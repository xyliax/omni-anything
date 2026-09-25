"""Conveyor's vLLM 0.23 streaming gRPC worker.

Each session owns one long-lived ``engine.generate`` stream. The synchronous
``Step`` RPC enqueues the current input chunk and snapshots tokens already in
that session's undelivered-output buffer; it does not wait for the newly
enqueued chunk to finish. This is an implementation choice used to keep one
slow service call from delaying later release slots, not a paper mechanism.

The EngineCore patch incrementally copies completed KV blocks to host memory,
partially evicts idle-session KV tails, reloads missing host-backed blocks on
demand, and optionally prefetches them at input release. The retained-prefix
mode performs eviction at the scheduler's idle transition; a fixed-tail RPC is
kept for controlled experiments. Both use synchronous scheduling because an
in-flight speculative iteration could still write a block being evicted.

This measured Qwen2.5-Omni path returns Thinker text tokens only. It does not
run Talker/Code2Wav or produce PCM audio.
"""
import argparse, asyncio, json, logging, os, sys, threading, time
from concurrent import futures
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_MET = os.environ.get("METRONOME_ROOT", str(_ROOT / "third_party" / "metronome"))
sys.path.insert(0, str(_ROOT))   # for infra.trace.collectors.worker_obs (shared observation)
sys.path.insert(0, _MET)
sys.path.insert(0, os.path.join(_MET, "worker"))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "WARNING")

import grpc
import numpy as np
import inference_pb2 as pb
import inference_pb2_grpc as pb_grpc

from infra.trace.collectors.worker_obs import perreq_logger, stat_logger_classes
from infra.trace.collectors.service_events import emit as service_event
from engines.model_inputs import audio_adapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [stream-worker] %(message)s")
log = logging.getLogger("stream-worker")

# Warmup sentinel session id. Contract shared across process boundaries:
# infra/trace/parse.py excludes it from every statistic and the engine_patch
# never applies automatic KV eviction to it; a contract test
# pins the three declarations together.
WARMUP_SID = 10**9

# Shared observation producer (infra/trace): per-request events on one perf clock,
# with the clock-pairing C line written at open.
_pev = perreq_logger()


_INGEST_POOL = None
_INPUT_GATES = {}  # frontend event-loop only; exact (external request, frame)


def checked_context_size(retained, input_tokens, output_tokens, maximum):
    """Check the complete append before handing it to the resumable backend."""
    total = retained + input_tokens + output_tokens
    if total > maximum:
        raise ValueError(f'maximum context exceeded: {total} > {maximum}')
    # The pinned backend keeps computed output tokens, excluding the final
    # sampled-but-uncomputed token, when resuming the next segment.
    return total - 1


class InputGate:
    """Overlap restoration with CPU preprocessing, or trigger on actual demand.

    Submission, history readiness, and backend enqueue remain distinct events.
    The submitting coroutine keeps its session lock until enqueue is confirmed.
    """
    def __init__(self, prepare, policy):
        self.prepare = prepare
        self.task = asyncio.create_task(prepare()) if policy != 'on_demand' else None
        self.done = asyncio.get_running_loop().create_future()

    async def ready(self):
        if self.task is None:
            self.task = asyncio.create_task(self.prepare())
        await self.task

    def close(self):
        if self.task is not None and not self.task.done():
            self.task.cancel()

def _patch_parallel_ingest(workers=8, model_family="qwen25_omni"):
    """Replace AsyncLLM._add_streaming_input_request with a copy whose per-chunk
    process_inputs is offloaded to a thread pool (sole change vs upstream 0.23)."""
    global _INGEST_POOL
    import functools
    from concurrent.futures import ThreadPoolExecutor
    from vllm import TokensPrompt
    from vllm.renderers.inputs.preprocess import extract_prompt_components
    from vllm.v1.engine.async_llm import AsyncLLM, InputStreamError
    from vllm.v1.engine.output_processor import RequestOutputCollector
    from engines.audio_features import install_bounded_audio_padding

    if model_family == "qwen25_omni":
        install_bounded_audio_padding()
    elif model_family == "minicpm_o45":
        from engines.audio_features import install_minicpm_bounded_audio_padding
        install_minicpm_bounded_audio_padding()
    _INGEST_POOL = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="ingest")

    async def _add_streaming_input_request(self, request_id, input_stream, sampling_params,
                                           arrival_time=None, lora_request=None,
                                           tokenization_kwargs=None, trace_headers=None,
                                           priority=0, data_parallel_rank=None):
        self._validate_streaming_input_sampling_params(sampling_params)
        inputs = dict(
            supported_tasks=await self.get_supported_tasks(),
            arrival_time=arrival_time, lora_request=lora_request,
            tokenization_kwargs=tokenization_kwargs, trace_headers=trace_headers,
            priority=priority, data_parallel_rank=data_parallel_rank)
        if not sampling_params.skip_clone:
            sampling_params = sampling_params.clone()
            sampling_params.skip_clone = True
        final_req = self.input_processor.process_inputs(
            request_id=request_id, prompt=TokensPrompt(prompt_token_ids=[0]),
            params=sampling_params, **inputs)
        self.input_processor.assign_request_id(final_req)
        internal_req_id = final_req.request_id
        queue = RequestOutputCollector(sampling_params.output_kind, internal_req_id)

        async def handle_inputs():
            loop = asyncio.get_running_loop()
            # ingest-pipeline stations (sid extracted from "s<sid>e1" request ids so the
            # lines stay parse-compatible with P/F/T):
            #   IQ dispatch to executor · IS FE starts (thread) · IE FE done (thread)
            #   IR back on the loop · IA admitted to the engine
            sid = request_id[1:request_id.index("e")] if request_id.startswith("s") else request_id
            cancelled = False
            frame = -int(bool(os.environ.get('OMNI_SERVICE_PRELOAD')))
            retained = 0
            try:
                async for input_chunk in input_stream:
                    frame += 1
                    sp = input_chunk.sampling_params
                    if sp:
                        self._validate_streaming_input_sampling_params(sp)
                    else:
                        sp = sampling_params
                    _pev("IQ", sid)
                    fn = functools.partial(
                        self.input_processor.process_inputs,
                        request_id=internal_req_id, prompt=input_chunk.prompt,
                        params=sp, resumable=True, **inputs)

                    def _timed(fn=fn):
                        _pev("IS", sid)
                        result = fn()
                        _pev("IE", sid)
                        return result

                    req = await loop.run_in_executor(_INGEST_POOL, _timed)
                    _pev("IR", sid)
                    req.external_req_id = request_id
                    if os.environ.get('OMNI_INPUT_GATES'):
                        retained = checked_context_size(retained, len(req.prompt_token_ids or ()),
                                                        sp.max_tokens, self.model_config.max_model_len)
                    if req.prompt_embeds is not None:
                        raise ValueError("prompt_embeds not supported for streaming inputs")
                    prompt_text, _, _ = extract_prompt_components(
                        self.model_config, input_chunk.prompt)
                    gate = _INPUT_GATES.get((request_id, frame))
                    if gate is not None:
                        service_event('preprocessing_complete', sid, frame)
                        await gate.ready()
                    await self._add_request(req, prompt_text, None, 0, queue)
                    service_event('engine_input', sid, frame)
                    if gate is not None and not gate.done.done():
                        gate.done.set_result(None)
                    _pev("IA", sid)
            except (asyncio.CancelledError, GeneratorExit):
                cancelled = True
            except Exception as error:
                for (identity, _), gate in list(_INPUT_GATES.items()):
                    if identity == request_id and not gate.done.done():
                        gate.done.set_exception(error)
                queue.put(InputStreamError(error))
            finally:
                queue._input_stream_task = None
                if not cancelled:
                    await self._add_request(final_req, None, None, 0, queue)

        self._run_output_handler()
        queue._input_stream_task = asyncio.create_task(handle_inputs())
        return queue

    AsyncLLM._add_streaming_input_request = _add_streaming_input_request
    log.info("PARALLEL-INGEST patch applied: per-chunk process_inputs -> ThreadPoolExecutor(%d)",
             workers)


def terminal_audio(arr, sample_rate, minimum_ms=40):
    """Retain a tiny final fragment; Qwen needs enough frames for one embedding.

    This declared input adapter appends at most 40 ms of silence, never drops
    the tail and never reintroduces the old long feature-extraction window.
    """
    minimum = (sample_rate * minimum_ms + 999) // 1000
    return np.pad(arr, (0, minimum - len(arr))) if len(arr) < minimum else arr


class Session:
    __slots__ = ("queue", "tokens", "text", "consumed", "consumed_text", "frame",
                 "done", "error", "task", "runner_task", "closing", "pushes", "push_lock", "ending", "drained", "received")

    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.tokens: list = []      # cumulative output token ids
        self.text: str = ""         # cumulative detokenized text
        self.consumed = 0           # tokens already returned to the gateway
        self.consumed_text = 0      # chars of text already returned
        self.frame = 0
        self.done = False
        self.error = None
        self.task = None
        self.runner_task = None
        self.closing = False
        self.pushes = set()
        self.push_lock = asyncio.Lock()
        self.ending = False
        self.drained = False
        self.received = 0


class StreamingEngine:
    """AsyncLLM + per-session resident resumable requests, driven from a sync Step()."""

    def __init__(self, model, gpu_mem, max_model_len, max_num_seqs, output_token_cap,
                 max_audio_chunks, initial_context_tokens=0, kv_pool_gib=None, host_offload_gib=24.0,
                 evict_tail_blocks=0, eviction_delay_s=1.2, sync_scheduling=False,
                 prefetch="off", model_family='qwen25_omni', enforce_eager=False, max_num_batched_tokens=None):
        from vllm import SamplingParams
        from vllm.config import KVTransferConfig
        from vllm.engine.arg_utils import AsyncEngineArgs
        from vllm.v1.engine.async_llm import AsyncLLM
        self.SamplingParams = SamplingParams
        self.input_adapter = audio_adapter(model_family)
        self.output_token_cap = output_token_cap
        self.initial_context_tokens = initial_context_tokens
        self.evict_tail_blocks = evict_tail_blocks
        self.eviction_delay_s = eviction_delay_s
        self.eviction_refused_why: dict = {}
        self.eviction_error = 0
        # push-triggered prefetch (engine-side omni_prefetch, utility RPC at
        # each chunk push so the reload copy overlaps FE). Refusals are
        # normal per-cycle outcomes (resident / pool-pressure / in-flight).
        self.prefetch = prefetch == "push"
        self.prefetch_refused_why: dict = {}
        self.prefetch_error = 0
        self.managed = bool(os.environ.get("OMNI_SESSION_MANAGER") or os.environ.get('OMNI_RESIDENT_ONLY'))
        self.sessions: dict[int, Session] = {}
        self.closed_sessions = set()
        self.close_futures = {}
        self.loop = asyncio.new_event_loop()
        self.thr = threading.Thread(target=self._loop_forever, daemon=True)
        self.thr.start()
        # The connector incrementally backs completed KV blocks in host memory.
        # Prefix caching is required for later GPU/host prefix matching.
        kv_xfer = KVTransferConfig(
            kv_connector="SimpleCPUOffloadConnector", kv_role="kv_both",
            kv_connector_extra_config={"cpu_bytes_to_use": int(host_offload_gib * (1 << 30))})
        engine_kwargs = dict(
            model=model, trust_remote_code=True, gpu_memory_utilization=gpu_mem,
            max_model_len=max_model_len, enforce_eager=enforce_eager, max_num_seqs=max_num_seqs,
            dtype='bfloat16',
            limit_mm_per_prompt={"audio": max_audio_chunks, "image": 0},
            enable_prefix_caching=True,
            kv_transfer_config=kv_xfer,
            mm_processor_cache_gb=0)   # cache off: no cross-thread LRU mutation (hits ~absent anyway)
        if max_num_batched_tokens is not None:
            engine_kwargs['max_num_batched_tokens'] = max_num_batched_tokens
        if os.environ.get('OMNI_RESIDENT_ONLY'):
            engine_kwargs.pop('kv_transfer_config')
            engine_kwargs['async_scheduling'] = False
        if kv_pool_gib is not None:   # optional exact-byte pool cap (smoke test / pinned budget)
            engine_kwargs["kv_cache_memory_bytes"] = int(kv_pool_gib * (1 << 30))
        if sync_scheduling or evict_tail_blocks or os.environ.get("OMNI_KV_EVICTION"):
            # The KV eviction primitive frees a stopped request's blocks from a utility
            # call on the busy loop; that is provably serialized with schedule()
            # only when scheduling is synchronous. Async scheduling pipelines
            # step N+1 while N executes, so a just-stopped request may still
            # have an in-flight speculative step writing into its blocks — KV eviction
            # under that regime is a use-after-free window (the engine_patch
            # guard refuses it). Trade pipeline throughput for exactness here.
            engine_kwargs["async_scheduling"] = False
        args = AsyncEngineArgs(**engine_kwargs)
        _patch_parallel_ingest(workers=int(os.environ.get("INGEST_WORKERS", "8")), model_family=model_family)
        fut = asyncio.run_coroutine_threadsafe(self._make_engine(args), self.loop)
        self.engine = fut.result()
        log.info("AsyncLLM streaming engine ready (model=%s)", model)

    def _loop_forever(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _make_engine(self, args):
        from vllm.v1.engine.async_llm import AsyncLLM
        # shared stat logger (infra/trace worker_obs): kv.log + per_iteration.log
        loggers = stat_logger_classes()
        if loggers:
            return AsyncLLM.from_engine_args(args, stat_loggers=loggers)
        return AsyncLLM.from_engine_args(args)

    # ---- per-session resident resumable request (unbounded append-to-resident-KV) ----
    async def _run_session(self, sid: int, st: Session):
        if st.closing:
            return
        st.runner_task = asyncio.current_task()
        from vllm.engine.protocol import StreamingInput
        # base_sp only governs the stream-end flush request (never a live
        # segment; per-segment caps are set on each StreamingInput below).
        base_sp = self.SamplingParams(temperature=0.0, max_tokens=self.output_token_cap, ignore_eos=True)
        async def gen():
            # Initial-context preloading grows every session before measurement.
            # Per-session unique text prevents cross-session prefix deduplication.
            # defeats prefix-cache dedup, which would otherwise make capacity look optimistic.
            # max_tokens=1: prefill, one token, on.
            if self.initial_context_tokens:
                import random as _rnd
                _r = _rnd.Random(9973 * (sid + 1))
                _vocab = ("alpha","bravo","charlie","delta","echo","foxtrot","golf","hotel",
                          "india","juliet","kilo","lima","mike","november","oscar","papa")
                filler = " ".join(_r.choice(_vocab) for _ in range(int(self.initial_context_tokens / 1.6)))  # ~1.6 tok/word measured
                _pev("INITCTX", sid, self.initial_context_tokens)
                yield StreamingInput(
                    prompt={"prompt": self.input_adapter.preload(f"[context {sid}] " + filler)},
                    sampling_params=self.SamplingParams(temperature=0.0, max_tokens=1,
                                                        ignore_eos=True))
            # stream chunks (append-to-resident-KV, context grows unbounded)
            while True:
                item = await st.queue.get()
                if item is None:
                    return
                arr, sr = item
                st.frame += 1
                _pev("F", sid, st.frame)
                prompt = self.input_adapter.prompt(st.frame == 1 and not self.initial_context_tokens)
                # This harness sets max_tokens to the configured per-period
                # output cap. It is an upper bound, not a required delivery
                # amount or a measured audio playback rate.
                sp = self.SamplingParams(temperature=0.0, max_tokens=self.output_token_cap,
                                         ignore_eos=True)
                yield StreamingInput(
                    prompt={"prompt": prompt, "multi_modal_data": {"audio": (arr, sr)}},
                    sampling_params=sp)

        try:
            # request id keeps the upstream "s<sid>e<n>" shape: the trace parser's session pattern
            # (parse.SESSION_PATTERN) parses it out of the scheduler trace.
            async for out in self.engine.generate(gen(), base_sp, f"s{sid}e1"):
                st.tokens = list(out.outputs[0].token_ids)
                st.text = out.outputs[0].text
                _pev("T", sid, len(st.tokens),
                     len(getattr(out, "prompt_token_ids", None) or []), st.frame)
        except Exception as e:  # noqa
            st.error = f"{type(e).__name__}: {str(e)[:160]}"
            log.warning("session %s ended: %s", sid, st.error)
        st.done = True

    def _ensure(self, sid: int) -> Session:
        st = self.sessions.get(sid)
        if st is None:
            if getattr(self, "preloaded_n", 0) and sid < WARMUP_SID:
                log.warning(
                    "session s%d created after the initialization barrier "
                    "(preloaded 1..%d); preloading lazily",
                    sid,
                    self.preloaded_n,
                )
            st = Session()
            self.sessions[sid] = st
            st.task = asyncio.run_coroutine_threadsafe(self._run_session(sid, st), self.loop)
        return st

    # ---- sync Step bridge: push the new chunk, take whatever the previous slice produced ----
    def step(self, sid_audio: dict, output_token_cap: int, cadence=None, frame_ids=None) -> tuple[dict, float]:
        t0 = time.perf_counter()
        out = {}      # sid -> (tokens, text_delta)
        for sid, (arr, sr) in sid_audio.items():
            if sid in self.closed_sessions:
                continue  # late Step must never recreate an ended session
            st = self._ensure(sid)
            st.received += 1
            if frame_ids is not None and sid < WARMUP_SID:
                if frame_ids.get(str(sid)) != st.received:
                    raise ValueError(f'input identity gap for session {sid}')
                service_event('input_received', sid, st.received)
            if self.managed and sid < WARMUP_SID:
                if cadence is None:
                    raise ValueError("Session Manager requires planned next-tick metadata")
                asyncio.run_coroutine_threadsafe(self._managed_push(sid, st, arr, sr, cadence), self.loop)
            else:
                asyncio.run_coroutine_threadsafe(st.queue.put((arr, sr)), self.loop)
            _pev("P", sid)
            if self.prefetch and sid < WARMUP_SID:
                # Issue push prefetch alongside input processing. The shorter
                # bounded feature extraction is not guaranteed to hide H2D.
                asyncio.run_coroutine_threadsafe(self._prefetch_after_push(sid), self.loop)
            if self.evict_tail_blocks and sid < WARMUP_SID:   # warmup sentinel never evicts KV
                asyncio.run_coroutine_threadsafe(self._evict_after(sid), self.loop)
        return self.collect_output(sid_audio, output_token_cap), (time.perf_counter() - t0) * 1000.0

    def collect_output(self, session_ids, output_token_cap):
        out = {}
        for sid in session_ids:
            st = self.sessions.get(sid)
            if st is None:
                continue
            tokens, text = st.tokens, st.text
            if len(tokens) > st.consumed:
                new = tokens[st.consumed: st.consumed + output_token_cap]
                delta = text[st.consumed_text:]
                out[sid] = (new, delta)
                st.consumed += len(new)
                st.consumed_text += len(delta)
        return out

    def end_input(self, sid):
        st = self.sessions.get(sid)
        if st is None or st.ending:
            return
        st.ending = True
        asyncio.run_coroutine_threadsafe(self._drain_input(sid, st), self.loop)

    async def _drain_input(self, sid, st):
        while not st.closing:
            if not st.pushes and st.queue.empty():
                result = await self.engine.engine_core.call_utility_async('session_drained', f's{sid}e1')
                expected = st.frame * self.output_token_cap + int(bool(self.initial_context_tokens))
                # EngineCore completion can precede frontend output delivery.
                # This fixed-cap harness must observe the final output too.
                if result['drained'] and len(st.tokens) >= expected:
                    st.drained = True
                    return
            await asyncio.sleep(.01)

    async def _managed_push(self, sid, st, arr, sr, cadence):
        task = asyncio.current_task()
        st.pushes.add(task)
        gate, gate_key = None, None
        try:
            async with st.push_lock:
                if st.closing:
                    return
                period_s, next_tick = cadence
                await self.engine.engine_core.call_utility_async(
                    "session_plan", f"s{sid}e1", period_s, next_tick,
                    float(os.environ["OMNI_RESTORE_LEAD_S"]),
                    int(os.environ["OMNI_RETAINED_PREFIX_BLOCKS"]))
                if os.environ.get('OMNI_INPUT_GATES'):
                    async def prepare():
                        while not st.closing:
                            result = await self.engine.engine_core.call_utility_async(
                                'session_ready', f's{sid}e1', str(next_tick))
                            if result['ready']:
                                return
                            await asyncio.sleep(.001)
                        raise asyncio.CancelledError()
                    gate_key = (f's{sid}e1', st.frame + 1)
                    gate = InputGate(prepare, os.environ.get('OMNI_RESTORE_POLICY', 'pre_tick'))
                    _INPUT_GATES[gate_key] = gate
                    await st.queue.put((arr, sr))
                    await gate.done
                    return
                if os.environ.get('OMNI_ADMISSION_PROFILE') or os.environ.get('OMNI_RESIDENT_ONLY'):
                    while not st.closing:
                        result = await self.engine.engine_core.call_utility_async(
                            'session_ready', f's{sid}e1', str(next_tick))
                        if result['ready']:
                            break
                        await asyncio.sleep(.01)
                if not st.closing:
                    await st.queue.put((arr, sr))
        except Exception as exc:
            st.error = f"Session Manager input failed: {exc!r}"
            log.error("session %s ended: %s", sid, st.error)
            st.done = True
        finally:
            if gate is not None:
                gate.close()
                _INPUT_GATES.pop(gate_key, None)
            st.pushes.discard(task)

    async def _prefetch_after_push(self, sid: int):
        """Issue ``prefetch_kv`` without blocking the service RPC.

        No host-backed gap, capacity deferral, and an in-flight copy are
        normal outcomes. Only RPC transport errors are unexpected.
        """
        try:
            result = await self.engine.engine_core.call_utility_async(
                "prefetch_kv", f"s{sid}e1")
        except Exception as e:  # noqa
            self.prefetch_error += 1
            log.warning("prefetch s%d RPC failed: %s: %s", sid, type(e).__name__, str(e)[:120])
            return
        if not result.get("prefetched"):
            reason = result.get("reason", "?")
            self.prefetch_refused_why[reason] = self.prefetch_refused_why.get(reason, 0) + 1

    async def _evict_after(self, sid: int):
        """FIXED-TAIL MODE ONLY (retained-prefix limit mode auto-evicts KV engine-side via
        OMNI_RETAINED_PREFIX_BLOCKS and never enters this coroutine). eviction_delay_s after
        this session's chunk push, ask the engine to destroy its last
        evict_tail_blocks blocks. Refusals are NORMAL per-cycle outcomes and
        self-heal next cycle — not idle yet (slice still running), unknown
        request (first chunk not admitted within the delay under load, or
        session cancelled with this timer in flight). Only RPC transport
        errors are never expected. Engine-side evidence is ``kv_events.log``."""
        await asyncio.sleep(self.eviction_delay_s)
        try:
            result = await self.engine.engine_core.call_utility_async(
                "evict_tail_blocks", f"s{sid}e1", self.evict_tail_blocks)
        except Exception as e:  # noqa
            self.eviction_error += 1
            log.warning("KV eviction s%d RPC failed: %s: %s", sid, type(e).__name__, str(e)[:120])
            return
        if not result.get("kv_evicted"):
            reason = result.get("reason", "?")
            self.eviction_refused_why[reason] = self.eviction_refused_why.get(reason, 0) + 1

    def cancel(self, sid: int):
        self.begin_cancel(sid).result(timeout=8)
        self.finish_cancel(sid)

    def begin_cancel(self, sid: int):
        self.closed_sessions.add(sid)
        if sid not in self.close_futures:
            st = self.sessions.get(sid)
            if st is not None:
                st.closing = True
            self.close_futures[sid] = asyncio.run_coroutine_threadsafe(
                self._close_session(sid, st), self.loop)
        # The gateway retains its admission reservation until this succeeds.
        # A timeout leaves the same close task running for an idempotent retry.
        return self.close_futures[sid]

    def finish_cancel(self, sid):
        self.sessions.pop(sid, None)
        self.close_futures.pop(sid, None)

    async def _close_session(self, sid, st):
        if st is not None:
            for task in list(st.pushes):
                task.cancel()
            if st.pushes:
                await asyncio.gather(*list(st.pushes), return_exceptions=True)
            if st.runner_task is not None:
                st.runner_task.cancel()
                await asyncio.gather(st.runner_task, return_exceptions=True)
            elif st.task is not None:
                st.task.cancel()
        await self.engine.abort(f's{sid}e1')
        if self.managed:
            while True:
                result = await self.engine.engine_core.call_utility_async('session_release', f's{sid}e1')
                if result['released']:
                    break
                await asyncio.sleep(.01)
        if st is not None:
            st.done = True

    def admit(self, sid, period_s, slots, epoch, source_start=None):
        if sid in self.closed_sessions:
            raise ValueError('closed session identity')
        future = asyncio.run_coroutine_threadsafe(
            self.engine.engine_core.call_utility_async(
                'session_admit', f's{sid}e1', period_s, slots, epoch, source_start), self.loop)
        return future.result(timeout=8)

    def num_unfinished(self) -> int:
        return sum(1 for s in self.sessions.values() if not s.done)

    def finished(self, sid: int) -> bool:
        st = self.sessions.get(sid)
        return sid in self.closed_sessions or bool(st and (st.done or (st.drained and st.consumed >= len(st.tokens))))

    def total_tokens(self) -> int:
        return sum(len(s.tokens) for s in self.sessions.values())

    def sample_text(self) -> str:
        for s in self.sessions.values():
            t = s.text.strip()
            if t:
                return t[:80]
        return ""


class Servicer(pb_grpc.InferenceServicer):
    def __init__(self, eng: StreamingEngine, model):
        self.eng = eng
        self.model = model
        self.steps = 0
        self.lock = threading.Lock()

    def Step(self, request, context):
        metadata = dict(context.invocation_metadata())
        control = metadata.get('x-pilarius-control')
        if control in ('gpu_trace_start', 'gpu_trace_stop'):
            try:
                if not os.environ.get('OMNI_GPU_ACTIVITY') or request.sessions:
                    raise ValueError('capture control requires configured capture and no input')
                future = asyncio.run_coroutine_threadsafe(
                    self.eng.engine.engine_core.call_utility_async(control), self.eng.loop)
                future.result(timeout=280)
                return pb.StepResponse()
            except Exception as exc:
                context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        if control in ('admit', 'close'):
            try:
                if len(request.sessions) != 1:
                    raise ValueError('control operation requires one session')
                sid = request.sessions[0].sid
                if control == 'admit':
                    if not self.eng.managed:
                        raise ValueError('admission requires managed mode')
                    result = self.eng.admit(
                        sid,
                        int(metadata['x-pilarius-period-ns']) / 1e9,
                        int(metadata['x-pilarius-slots']),
                        int(metadata['x-pilarius-epoch-ns']) / 1e9,
                        int(metadata['x-pilarius-source-start-ns']) / 1e9 if 'x-pilarius-source-start-ns' in metadata else None)
                    context.send_initial_metadata((('x-pilarius-admission', json.dumps(result)),))
                    return pb.StepResponse()
                with self.lock:
                    close = self.eng.begin_cancel(sid)
                close.result(timeout=8)  # never hold the Step lock across DMA drain
                with self.lock:
                    self.eng.finish_cancel(sid)
                return pb.StepResponse(outputs=[pb.SessionOutput(sid=sid, finished=True)])
            except Exception as exc:
                context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        with self.lock:
            output_token_cap = int(request.tokens_per_tick or 1)
            ending_ids = {int(sid) for sid in metadata.get('x-pilarius-ending-sids', '').split(',') if sid}
            cont = {}
            all_sids = []
            for s in request.sessions:
                if s.cancel:
                    self.eng.cancel(s.sid); continue
                all_sids.append(s.sid)
                if s.audio_pcm16:
                    arr = np.frombuffer(s.audio_pcm16, dtype="<i2").astype("float32")
                    arr *= (1.0 / 32768.0)
                    sample_rate = int(s.sample_rate or 16000)
                    if s.sid in ending_ids:
                        arr = terminal_audio(arr, sample_rate, getattr(getattr(self.eng, "input_adapter", None), "min_audio_ms", 40))
                    cont[s.sid] = (arr.copy(), sample_rate)
            outs, lat = ({}, 0.0)
            if cont:
                cadence = None
                if self.eng.managed:
                    metadata = dict(context.invocation_metadata())
                    try:
                        cadence = (int(metadata["x-pilarius-period-ns"]) / 1e9,
                                   int(metadata["x-pilarius-next-tick-ns"]) / 1e9)
                    except (KeyError, ValueError):
                        context.abort(grpc.StatusCode.INVALID_ARGUMENT, "missing or invalid planned tick metadata")
                frame_ids = json.loads(metadata['x-pilarius-frame-ids']) if os.environ.get('OMNI_SERVICE_EVENTS') else None
                outs, lat = self.eng.step(cont, output_token_cap, cadence, frame_ids)
            # End follows the last staged input; an empty poll never creates
            # another model update. Delivery remains capped once per tick.
            for sid in ending_ids:
                self.eng.end_input(sid)
            outs.update(self.eng.collect_output([sid for sid in all_sids if sid not in cont], output_token_cap))
            resp = pb.StepResponse(gpu_ms=float(lat))
            for sid in all_sids:
                st = self.eng.sessions.get(sid)
                if st is not None and st.error:
                    context.abort(grpc.StatusCode.INTERNAL, st.error)
                tk, txt = outs.get(sid, ([], ""))
                toks = [int(t) for t in tk]
                resp.outputs.append(pb.SessionOutput(sid=sid, tokens=toks, text=txt,
                                                     finished=self.eng.finished(sid)))
            try:
                resp.in_flight = int(self.eng.num_unfinished())
            except Exception:
                resp.in_flight = 0
            self.steps += 1
            if self.steps % 8 == 0:
                mx = max((s.frame for s in self.eng.sessions.values()), default=0)
                output_backlog = max(
                    (len(s.tokens) - s.consumed for s in self.eng.sessions.values()),
                    default=0,
                )
                log.info("step %d: %d sessions, %.0fms, resident_frames=%d (~%ds ctx), "
                         "tot_tokens=%d, output_backlog=%d, "
                         "eviction_refused_why=%r, eviction_error=%d, "
                         "prefetch_refused_why=%r, prefetch_error=%d, "
                         "sample=%r", self.steps, len(all_sids), lat, mx, mx * 2,
                         self.eng.total_tokens(), output_backlog, self.eng.eviction_refused_why,
                         self.eng.eviction_error, self.eng.prefetch_refused_why,
                         self.eng.prefetch_error, self.eng.sample_text())
            return resp

    def Health(self, request, context):
        with self.lock:   # sessions dict mutates under this lock in Step
            return pb.HealthResponse(ready=True, in_flight=self.eng.num_unfinished(),
                                     model=self.model)


def main():
    # Engine geometry has NO defaults here on purpose: the runner translates
    # experiments/conveyor/config/ (the single declaration point) into argv,
    # and a manual launch must be equally explicit — a second set of defaults
    # is a second source of truth that silently drifts.
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument('--model-family', choices=('qwen25_omni', 'minicpm_o45'), default='qwen25_omni')
    ap.add_argument('--enforce-eager', action='store_true')
    ap.add_argument('--max-num-batched-tokens', type=int)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--gpu-mem", type=float, required=True)
    ap.add_argument("--max-model-len", type=int, required=True)
    ap.add_argument("--max-num-seqs", type=int, required=True)
    ap.add_argument("--output-token-cap", type=int, required=True)
    ap.add_argument("--max-audio-chunks", type=int, required=True)
    ap.add_argument("--host-offload-gib", type=float, required=True,
                    help="host-backed KV pool in GiB; size so it never LRU-evicts an "
                         "interior block of a live session")
    ap.add_argument("--initial-context-tokens", type=int, default=0,
                    help="initial context: prefill about this many unique filler text tokens per "
                         "session at start (0 = off) — compresses time-to-wall, makes ctx a "
                         "controlled variable")
    ap.add_argument("--kv-pool-gib", type=float, default=None,
                    help="OPTIONAL exact GPU KV pool cap in GiB; default None = use the full "
                         "pool from --gpu-mem (same as baseline). Set only to pin a byte budget "
                         "or force preemption at small N for a smoke test — the capacity claim "
                         "is made by sweeping sessions on the FULL pool, not by shrinking this")
    ap.add_argument("--evict-tail-blocks", type=int, default=0,
                    help="KV eviction primitive, fixed mode: after each session's slice, release its "
                         "KV grip and destroy this many tail blocks (0 = off; requires the "
                         "engine_patch sitecustomize on PYTHONPATH with OMNI_KV_EVICTION set)")
    ap.add_argument("--sync-scheduling", action="store_true",
                    help="pin synchronous scheduling without KV eviction for a matched control; "
                         "KV eviction runs force it regardless)")
    ap.add_argument("--prefetch", choices=("off", "push"), default="off",
                    help="KV prefetch: push = at each chunk push, prefetch the session's "
                         "KV-evicted tail back into the GPU prefix cache so the copy overlaps FE "
                         "(requires KV eviction + the engine_patch with OMNI_PREFETCH set)")
    ap.add_argument("--eviction-delay-s", type=float, default=None,
                    help="delay from a session's chunk push to its KV eviction call; must land "
                         "after the slice finishes and before the next push (required "
                         "with --evict-tail-blocks; the config declares the value)")
    ap.add_argument("--preload-sessions", type=int, default=0,
                    help="initialization barrier: pre-create this many sessions (sids 1..N), "
                         "finish all initial-context prefills, then advertise ready "
                         "(requires --initial-context-tokens)")
    ap.add_argument("--ready-file", default=None)
    args = ap.parse_args()
    if args.evict_tail_blocks and args.eviction_delay_s is None:
        ap.error("--evict-tail-blocks requires --eviction-delay-s")

    log.info("loading Conveyor worker: %s (GPU KV pool=%s, host backing=%.1fGiB)",
             args.model,
             "full" if args.kv_pool_gib is None else f"{args.kv_pool_gib:.1f}GiB",
             args.host_offload_gib)
    eng = StreamingEngine(args.model, args.gpu_mem, args.max_model_len, args.max_num_seqs,
                          args.output_token_cap, args.max_audio_chunks, initial_context_tokens=args.initial_context_tokens,
                          kv_pool_gib=args.kv_pool_gib, host_offload_gib=args.host_offload_gib,
                          evict_tail_blocks=args.evict_tail_blocks,
                          eviction_delay_s=args.eviction_delay_s,
                          sync_scheduling=args.sync_scheduling,
                          prefetch=args.prefetch, model_family=args.model_family,
                          enforce_eager=args.enforce_eager, max_num_batched_tokens=args.max_num_batched_tokens)
    # warm: one short session so JIT/CUDA-graph cost is paid before advertising ready.
    # Step no longer waits for tokens, so poll the sentinel session until it produced one.
    try:
        sil = (np.zeros(32000, dtype=np.float32), 16000)
        eng.step({WARMUP_SID: sil}, args.output_token_cap)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline and not eng.sessions[WARMUP_SID].tokens:
            time.sleep(0.5)
        eng.cancel(WARMUP_SID)
        log.info("engine warm")
    except Exception:
        log.exception("warmup failed (continuing)")

    # INITIALIZATION BARRIER: build every requested initial context before
    # advertising ready. A barrier timeout currently continues to
    # ready for diagnostic capture, but the shared worker-fatal scanner makes
    # that run fail validation. RELIES ON DETERMINISTIC SIDS: the gateway
    # assigns
    # 1..N in admission order and the client opens exactly N sessions; a
    # session beyond N (e.g. a reconnect) falls back to lazy preloading at its
    # first push, with a log line.
    if args.initial_context_tokens and args.preload_sessions:
        n = args.preload_sessions
        log.info(
            "initialization barrier: preloading %d sessions x %d tokens ...",
            n,
            args.initial_context_tokens,
        )
        t0 = time.monotonic()
        for sid in range(1, n + 1):
            eng._ensure(sid)
        while True:
            done = sum(1 for sid in range(1, n + 1) if eng.sessions[sid].tokens)
            if done == n:
                break
            if time.monotonic() - t0 > 300:
                log.error("initialization barrier timed out (%d/%d preloaded)", done, n)
                break
            time.sleep(0.5)
        # The one token generated by initial-context prefill is state setup,
        # not output for the client; advance the buffer cursor past it.
        for sid in range(1, n + 1):
            st = eng.sessions[sid]
            st.consumed = len(st.tokens)
            st.consumed_text = len(st.text)
        # Release the automatic-eviction hold without evicting at the barrier.
        if os.environ.get("OMNI_RETAINED_PREFIX_BLOCKS"):
            fut = asyncio.run_coroutine_threadsafe(
                eng.engine.engine_core.call_utility_async("initial_context_finalize"),
                eng.loop)
            log.info("initial-context finalize: %r", fut.result(timeout=60))
        log.info("initialization barrier done: %d sessions preloaded in %.1fs",
                 n, time.monotonic() - t0)
        eng.preloaded_n = n

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8),
                         options=[("grpc.max_receive_message_length", 256 * 1024 * 1024),
                                  ("grpc.max_send_message_length", 256 * 1024 * 1024)])
    pb_grpc.add_InferenceServicer_to_server(Servicer(eng, args.model), server)
    server.add_insecure_port(f"0.0.0.0:{args.port}")
    server.start()
    log.info("STREAMING worker serving gRPC on :%d", args.port)
    if args.ready_file:
        Path(args.ready_file).write_text("ready", encoding="utf-8")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=2.0)


if __name__ == "__main__":
    main()
