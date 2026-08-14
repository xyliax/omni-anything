"""vLLM 0.23 STREAMING (append-to-resident-KV) gRPC worker for the conveyor engine.

Bridge: gRPC Step (sync, gRPC threadpool) <-> a single asyncio loop thread that runs AsyncLLM and
one long-lived engine.generate() per session fed by a per-session asyncio.Queue. Step pushes each
due session's chunk and IMMEDIATELY returns that session's token inventory (generated during the
previous slice) — take-from-stock delivery, no wait budget.

ORIGIN: copied from experiments/baseline/worker/stream_server.py and permanently diverged.
Behavioral changes vs that origin:
  1. Step delivers from inventory instead of waiting up to a budget for fresh tokens. Required
     by the staggered gateway: its slot firings arrive serialized through the Servicer lock, so
     one blocking Step would re-synchronize every slot behind it. Delivery therefore lags
     generation by exactly one slice (pipeline semantics); the first slice returns nothing.
  2. Warmup polls for the sentinel session's first token before advertising ready (the blocking
     Step used to provide that wait implicitly).
  3. BANDWIDTH-FOR-VRAM KV rotation. The GPU KV pool stays FULL (same --gpu-mem as baseline).
     The expansion is in residency, achieved ACTIVELY (passive pool-pressure preemption cannot
     express it — vLLM only preempts RUNNING requests and its LRU is anti-Belady for cyclic
     loads, see FINDINGS H3): vLLM's stock SimpleCPUOffloadConnector keeps an incremental host
     mirror of every full block (--host-offload-gib pool), the park primitive (item 4) releases
     each session's tail beyond quota K the instant its slice stops, and the tail reloads by
     hash-match on the next chunk. Idle-time residency stays pinned at K while contexts grow;
     the capacity claim is made by sweeping N (sessions), NOT by shrinking the pool. Prefix
     caching is enabled (the connector and the park/resume path require it). Reload timing REALITY (measured, not the original overlap
     intent): the load is triggered by the chunk's arrival at the scheduler, i.e. AFTER the
     ~296ms feature extraction — serialized, adding ~one reload duration (70ms at 330MB tails,
     growing with tail size) to the slice's critical path. True overlap needs a prefetch
     primitive (open work). --kv-pool-gib is an optional exact-byte cap for a small-N smoke test, not the lever.
  4. PARK wiring, two modes. QUOTA MODE (the main path) lives entirely in the engine:
     the runner sets OMNI_PARK_KEEP=K and the engine_patch auto-parks each session the
     instant its slice stops — this worker plays no part beyond having the patch on
     PYTHONPATH. FIXED-TAIL MODE (experiments): --park-tail-blocks N schedules, at
     --park-delay-s after each chunk push, a call_utility RPC to the engine-side
     park_tail_blocks primitive (destroy exactly the last N blocks). Either mode forces
     synchronous scheduling (the gate is `park_tail_blocks or OMNI_PARK_PATCH in env` —
     note the env reaches this worker even in quota mode). Engine-side evidence lands in
     park.log; worker-side RPC failures log here.
No experiment may add another copy of this worker.

Instrumentation (this file is the producer; the line grammars live with the
consumers in tracekit/parse.py): PERREQ_LOG gets P/F/T/SEED plus the five
ingest stations IQ/IS/IE/IR/IA, all on one shared perf clock with a single
"C <perf> <epoch>" pairing line; METRONOME_STATLOG (kv.log) additionally
carries pre=<cumulative preemption count> per line.

PARINGEST: AsyncLLM._add_streaming_input_request is monkeypatched so each
chunk's process_inputs runs in a ThreadPoolExecutor instead of synchronously
on the event loop (vllm 0.23 handle_inputs blocks the loop ~265ms/chunk on
this host, serializing all sessions' ingest). mm processor cache is disabled
(mm_processor_cache_gb=0): no cross-thread LRU mutation, and hits are ~absent
under FD_PHASE_STAGGER anyway. Per-session chunk ORDER is preserved — only
different sessions overlap.
"""
import argparse, asyncio, logging, os, sys, threading, time
from concurrent import futures
from pathlib import Path

_MET = os.environ.get(
    "METRONOME_ROOT",
    str(Path(__file__).resolve().parents[3] / "third_party" / "metronome"),
)
sys.path.insert(0, _MET)
sys.path.insert(0, os.path.join(_MET, "worker"))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "WARNING")

import grpc
import numpy as np
import inference_pb2 as pb
import inference_pb2_grpc as pb_grpc

logging.basicConfig(level=logging.INFO, format="%(asctime)s [stream-worker] %(message)s")
log = logging.getLogger("stream-worker")

# Warmup sentinel session id. Contract shared across process boundaries:
# tracekit/parse.py excludes it from every statistic and the engine_patch
# never auto-parks it (as request-id prefix "s1000000000e"); a contract test
# pins the three declarations together.
WARMUP_SID = 10**9

_PT0 = time.perf_counter()
_PERREQ = open(os.environ["PERREQ_LOG"], "a", buffering=1) if os.environ.get("PERREQ_LOG") else None

def _pev(kind, *vals):
    if _PERREQ:
        _PERREQ.write(f"{kind} {time.perf_counter() - _PT0:.3f} " + " ".join(map(str, vals)) + "\n")

# Clock fix: one line pairing this log's perf clock with the epoch clock that
# scheduler.log uses, so trace alignment is exact instead of heuristic.
_pev("C", f"{time.time():.6f}")


_INGEST_POOL = None

def _patch_parallel_ingest(workers=8):
    """Replace AsyncLLM._add_streaming_input_request with a copy whose per-chunk
    process_inputs is offloaded to a thread pool (sole change vs upstream 0.23)."""
    global _INGEST_POOL
    import functools
    from concurrent.futures import ThreadPoolExecutor
    from vllm import TokensPrompt
    from vllm.renderers.inputs.preprocess import extract_prompt_components
    from vllm.v1.engine.async_llm import AsyncLLM, InputStreamError
    from vllm.v1.engine.output_processor import RequestOutputCollector

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
            try:
                async for input_chunk in input_stream:
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
                    if req.prompt_embeds is not None:
                        raise ValueError("prompt_embeds not supported for streaming inputs")
                    prompt_text, _, _ = extract_prompt_components(
                        self.model_config, input_chunk.prompt)
                    await self._add_request(req, prompt_text, None, 0, queue)
                    _pev("IA", sid)
            except (asyncio.CancelledError, GeneratorExit):
                cancelled = True
            except Exception as error:
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

# Qwen2.5-Omni audio chat template. Frame 1 opens the assistant turn after an instruction so the
# model emits a REAL response (not chat-template filler); later frames append more audio. The
# trailing newline after each audio placeholder avoids the mrope boundary (belt + FIX4).
HEAD = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n"
APH = "<|audio_bos|><|AUDIO|><|audio_eos|>"
INSTR = " Listen to the audio and answer any question in it."
ASST = "<|im_end|>\n<|im_start|>assistant\n"
TRAIL = "\n"


class Session:
    __slots__ = ("queue", "tokens", "text", "consumed", "consumed_text", "frame",
                 "done", "error", "task")

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


class StreamingEngine:
    """AsyncLLM + per-session resident resumable requests, driven from a sync Step()."""

    def __init__(self, model, gpu_mem, max_model_len, max_num_seqs, tpt,
                 max_audio_chunks, seed_tokens=0, kv_pool_gib=None, host_offload_gib=24.0,
                 park_tail_blocks=0, park_delay_s=1.2, sync_scheduling=False):
        from vllm import SamplingParams
        from vllm.config import KVTransferConfig
        from vllm.engine.arg_utils import AsyncEngineArgs
        from vllm.v1.engine.async_llm import AsyncLLM
        self.SamplingParams = SamplingParams
        self.tpt = tpt
        self.seed_tokens = seed_tokens   # warm-start: prefill ~K filler tokens per session at start
        self.park_tail_blocks = park_tail_blocks  # >0: park this many tail blocks after each slice
                                                  # (quota mode is engine-side: OMNI_PARK_KEEP)
        self.park_delay_s = park_delay_s          # push -> park delay; slice must be done by then
        self.park_refused_why: dict = {}          # reason -> count, shown in the periodic step log
        self.park_error = 0                       # RPC transport failure (never expected)
        self.sessions: dict[int, Session] = {}
        self.loop = asyncio.new_event_loop()
        self.thr = threading.Thread(target=self._loop_forever, daemon=True)
        self.thr.start()
        # bandwidth-for-VRAM: the GPU KV pool stays at its FULL size (same
        # gpu_memory_utilization as baseline — NOT shrunk). The expansion comes
        # from residency, not from a smaller pool: under the staggered schedule
        # only the ~B computing sessions need KV resident at once, so the
        # scheduler preempts idle sessions when real demand (N x L) exceeds the
        # pool, and SimpleCPUOffloadConnector mirrors their full blocks to a host
        # pool during decode and reloads on resume (hash-match) instead of
        # recomputing. The same full pool therefore holds ~2x more sessions than
        # baseline. Sweep N (sessions), not the pool. kv_pool_gib is an OPTIONAL
        # override (kv_cache_memory_bytes ignores gpu_memory_utilization) only for
        # pinning an exact byte budget or a small-N smoke test — default None
        # means "match baseline's full pool". Prefix caching is REQUIRED (the
        # connector no-ops without it); copies are deferred to get_finished on a
        # low-priority stream so cudagraph stays on (enforce_eager=False). Reload
        # timing is measured in the header's item 3: it does NOT overlap feature
        # extraction (it is triggered by chunk arrival, after FE).
        kv_xfer = KVTransferConfig(
            kv_connector="SimpleCPUOffloadConnector", kv_role="kv_both",
            kv_connector_extra_config={"cpu_bytes_to_use": int(host_offload_gib * (1 << 30))})
        engine_kwargs = dict(
            model=model, trust_remote_code=True, gpu_memory_utilization=gpu_mem,
            max_model_len=max_model_len, enforce_eager=False, max_num_seqs=max_num_seqs,
            limit_mm_per_prompt={"audio": max_audio_chunks, "image": 0},
            enable_prefix_caching=True,
            kv_transfer_config=kv_xfer,
            mm_processor_cache_gb=0)   # cache off: no cross-thread LRU mutation (hits ~absent anyway)
        if kv_pool_gib is not None:   # optional exact-byte pool cap (smoke test / pinned budget)
            engine_kwargs["kv_cache_memory_bytes"] = int(kv_pool_gib * (1 << 30))
        if sync_scheduling or park_tail_blocks or os.environ.get("OMNI_PARK_PATCH"):
            # The park primitive frees a stopped request's blocks from a utility
            # call on the busy loop; that is provably serialized with schedule()
            # only when scheduling is synchronous. Async scheduling pipelines
            # step N+1 while N executes, so a just-stopped request may still
            # have an in-flight speculative step writing into its blocks — park
            # under that regime is a use-after-free window (the engine_patch
            # guard refuses it). Trade pipeline throughput for exactness here.
            engine_kwargs["async_scheduling"] = False
        args = AsyncEngineArgs(**engine_kwargs)
        _patch_parallel_ingest(workers=int(os.environ.get("INGEST_WORKERS", "8")))
        fut = asyncio.run_coroutine_threadsafe(self._make_engine(args), self.loop)
        self.engine = fut.result()
        log.info("AsyncLLM streaming engine ready (model=%s)", model)

    def _loop_forever(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _make_engine(self, args):
        from vllm.v1.engine.async_llm import AsyncLLM
        sl = os.environ.get("METRONOME_STATLOG")
        if sl:   # diagnostic: per-iteration scheduler stats (kv usage, running/waiting, evictions)
            from vllm.v1.metrics.loggers import StatLoggerBase
            import time as _time

            class _StatLog(StatLoggerBase):
                def __init__(self, vllm_config, engine_index=0):
                    self._f = open(sl, "a"); self._t0 = _time.time(); self._last = 0.0
                    self._pre = 0     # cumulative preemptions (must accumulate across throttled calls)
                    # kv.log sampling period; the runner sets this from config
                    # (0.2s = 10 samples/tick, matching the GPU sampler's
                    # rationale) — 1 Hz was too coarse for park sawtooth reading.
                    self._period = float(os.environ.get("OMNI_STATLOG_PERIOD_S", "1.0"))
                    pi = os.environ.get("PERITER_LOG")
                    self._it = open(pi, "a", buffering=1) if pi else None
                def record(self, scheduler_stats, iteration_stats, mm_cache_stats=None, engine_idx=0):
                    if iteration_stats is not None:
                        self._pre += getattr(iteration_stats, "num_preempted_reqs", 0)
                    if scheduler_stats is None:
                        return
                    now = _time.time()
                    if self._it is not None and iteration_stats is not None:
                        # per-iteration: engine-step composition (no throttle)
                        self._it.write(f"{now - self._t0:.3f} run={scheduler_stats.num_running_reqs} "
                                       f"wait={scheduler_stats.num_waiting_reqs} "
                                       f"gen={iteration_stats.num_generation_tokens} "
                                       f"ptok={getattr(iteration_stats, 'num_prompt_tokens', 0)}\n")
                    if now - self._last < self._period:   # throttled sampling
                        return
                    self._last = now
                    ev = len(getattr(scheduler_stats, "kv_cache_eviction_events", []) or [])
                    self._f.write(f"{now - self._t0:.1f} kv={scheduler_stats.kv_cache_usage:.3f} "
                                  f"run={scheduler_stats.num_running_reqs} "
                                  f"wait={scheduler_stats.num_waiting_reqs} evict={ev} "
                                  f"pre={self._pre}\n")
                    self._f.flush()
                def log(self): pass
                def log_engine_initialized(self): pass

            return AsyncLLM.from_engine_args(args, stat_loggers=[_StatLog])
        return AsyncLLM.from_engine_args(args)

    # ---- per-session resident resumable request (unbounded append-to-resident-KV) ----
    async def _run_session(self, sid: int, st: Session):
        from vllm.engine.protocol import StreamingInput
        # base_sp only governs the stream-end flush request (never a live
        # segment; per-segment caps are set on each StreamingInput below).
        base_sp = self.SamplingParams(temperature=0.0, max_tokens=self.tpt + 8, ignore_eos=True)
        async def gen():
            # WARM-START: one-shot prefill of approximately seed_tokens filler text so sessions
            # begin with pre-grown context (KV bytes are modality-agnostic). Per-sid unique prefix
            # defeats prefix-cache dedup, which would otherwise make capacity look optimistic.
            # max_tokens=1: prefill, one token, on.
            if self.seed_tokens:
                import random as _rnd
                _r = _rnd.Random(9973 * (sid + 1))
                _vocab = ("alpha","bravo","charlie","delta","echo","foxtrot","golf","hotel",
                          "india","juliet","kilo","lima","mike","november","oscar","papa")
                filler = " ".join(_r.choice(_vocab) for _ in range(int(self.seed_tokens / 1.6)))  # ~1.6 tok/word measured
                _pev("SEED", sid, self.seed_tokens)
                yield StreamingInput(
                    prompt={"prompt": HEAD + f"[context {sid}] " + filler + INSTR + ASST},
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
                prompt = (HEAD + APH + INSTR + ASST) \
                    if (st.frame == 1 and not self.seed_tokens) else (APH + TRAIL)
                # max_tokens is PER-SEGMENT and must equal tpt EXACTLY: each
                # chunk's update folds prior output into the prompt and clears
                # the output count, so any slack (the old +8) is generated
                # EVERY segment and accumulates in the take-from-stock
                # inventory — delivered tokens drift ever further behind the
                # audio that prompted them (duplex semantics silently break
                # while delivery metrics stay green). The stop check reads a
                # field frozen at construction; ONLY the engine_patch (park
                # runs) refreshes it per chunk — without the patch the frozen
                # value happens to equal tpt when seed is off, and seed runs
                # are refused by config validation (1-token-per-segment trap).
                sp = self.SamplingParams(temperature=0.0, max_tokens=self.tpt,
                                         ignore_eos=True)
                yield StreamingInput(
                    prompt={"prompt": prompt, "multi_modal_data": {"audio": (arr, sr)}},
                    sampling_params=sp)

        try:
            # request id keeps the upstream "s<sid>e<n>" shape: tracekit's session pattern
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
            if getattr(self, "pre_seeded_n", 0) and sid < WARMUP_SID:
                # a session beyond the pre-seed set (reconnect / sid drift):
                # it seeds lazily at this first push — functional but outside
                # the warm-start barrier's semantics, so make it visible.
                log.warning("session s%d created after the warm-start barrier "
                            "(pre-seeded 1..%d); seeding lazily", sid, self.pre_seeded_n)
            st = Session()
            self.sessions[sid] = st
            st.task = asyncio.run_coroutine_threadsafe(self._run_session(sid, st), self.loop)
        return st

    # ---- sync Step bridge: push the new chunk, take whatever the previous slice produced ----
    def step(self, sid_audio: dict, tpt: int) -> tuple[dict, float]:
        t0 = time.perf_counter()
        out = {}      # sid -> (tokens, text_delta)
        for sid, (arr, sr) in sid_audio.items():
            st = self._ensure(sid)
            asyncio.run_coroutine_threadsafe(st.queue.put((arr, sr)), self.loop)
            _pev("P", sid)
            if self.park_tail_blocks and sid < WARMUP_SID:   # warmup sentinel never parks
                asyncio.run_coroutine_threadsafe(self._park_after(sid), self.loop)
            # One snapshot per field: the loop thread REBINDS st.tokens/st.text
            # (never mutates), so each read below is a consistent list/str.
            # Cursors advance by exactly what this delivery took — re-reading
            # the live fields here would let a concurrent update mark tokens
            # or text as consumed that were never delivered.
            tokens, text = st.tokens, st.text
            if len(tokens) > st.consumed:
                new = tokens[st.consumed: st.consumed + tpt]
                delta = text[st.consumed_text:]
                out[sid] = (new, delta)
                st.consumed += len(new)
                st.consumed_text += len(delta)
        return out, (time.perf_counter() - t0) * 1000.0

    async def _park_after(self, sid: int):
        """FIXED-TAIL MODE ONLY (quota mode auto-parks engine-side via
        OMNI_PARK_KEEP and never enters this coroutine). park_delay_s after
        this session's chunk push, ask the engine to destroy its last
        park_tail_blocks blocks. Refusals are NORMAL per-cycle outcomes and
        self-heal next cycle — not idle yet (slice still running), unknown
        request (first chunk not admitted within the delay under load, or
        session cancelled with this timer in flight). Only RPC transport
        errors are never expected. Engine-side evidence is park.log."""
        await asyncio.sleep(self.park_delay_s)
        try:
            result = await self.engine.engine_core.call_utility_async(
                "park_tail_blocks", f"s{sid}e1", self.park_tail_blocks)
        except Exception as e:  # noqa
            self.park_error += 1
            log.warning("park s%d RPC failed: %s: %s", sid, type(e).__name__, str(e)[:120])
            return
        if not result.get("parked"):
            reason = result.get("reason", "?")
            self.park_refused_why[reason] = self.park_refused_why.get(reason, 0) + 1

    def cancel(self, sid: int):
        st = self.sessions.pop(sid, None)
        if st is not None:
            asyncio.run_coroutine_threadsafe(st.queue.put(None), self.loop)

    def num_unfinished(self) -> int:
        return sum(1 for s in self.sessions.values() if not s.done)

    def finished(self, sid: int) -> bool:
        st = self.sessions.get(sid)
        return bool(st and st.done)

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
        with self.lock:
            tpt = int(request.tokens_per_tick or 1)
            cont = {}
            all_sids = []
            for s in request.sessions:
                if s.cancel:
                    self.eng.cancel(s.sid); continue
                all_sids.append(s.sid)
                if s.audio_pcm16:
                    arr = np.frombuffer(s.audio_pcm16, dtype="<i2").astype("float32")
                    arr *= (1.0 / 32768.0)
                    cont[s.sid] = (arr.copy(), int(s.sample_rate or 16000))
            outs, lat = ({}, 0.0)
            if cont:
                outs, lat = self.eng.step(cont, tpt)
            resp = pb.StepResponse(gpu_ms=float(lat))
            for sid in all_sids:
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
                # inventory backlog: tokens generated but not yet delivered.
                # Healthy take-from-stock = one slice (~tpt) steady; growth =
                # generation outpacing delivery = duplex drift (see gen()'s
                # max_tokens comment).
                inv = max((len(s.tokens) - s.consumed
                           for s in self.eng.sessions.values()), default=0)
                log.info("step %d: %d sessions, %.0fms, resident_frames=%d (~%ds ctx), "
                         "tot_tokens=%d, inv_backlog=%d, park_refused_why=%r, park_error=%d, "
                         "sample=%r", self.steps, len(all_sids), lat, mx, mx * 2,
                         self.eng.total_tokens(), inv, self.eng.park_refused_why,
                         self.eng.park_error, self.eng.sample_text())
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
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--gpu-mem", type=float, required=True)
    ap.add_argument("--max-model-len", type=int, required=True)
    ap.add_argument("--max-num-seqs", type=int, required=True)
    ap.add_argument("--tpt", type=int, required=True)
    ap.add_argument("--max-audio-chunks", type=int, required=True)
    ap.add_argument("--host-offload-gib", type=float, required=True,
                    help="host KV mirror pool in GiB; size so it never LRU-evicts an "
                         "interior block of a live session")
    ap.add_argument("--seed-tokens", type=int, default=0,
                    help="warm-start: prefill about this many unique filler text tokens per "
                         "session at start (0 = off) — compresses time-to-wall, makes ctx a "
                         "controlled variable")
    ap.add_argument("--kv-pool-gib", type=float, default=None,
                    help="OPTIONAL exact GPU KV pool cap in GiB; default None = use the full "
                         "pool from --gpu-mem (same as baseline). Set only to pin a byte budget "
                         "or force preemption at small N for a smoke test — the capacity claim "
                         "is made by sweeping sessions on the FULL pool, not by shrinking this")
    ap.add_argument("--park-tail-blocks", type=int, default=0,
                    help="park primitive, fixed mode: after each session's slice, release its "
                         "KV grip and destroy this many tail blocks (0 = off; requires the "
                         "engine_patch sitecustomize on PYTHONPATH with OMNI_PARK_PATCH set)")
    ap.add_argument("--sync-scheduling", action="store_true",
                    help="pin synchronous scheduling without park (control-arm knob; "
                         "park runs force it regardless)")
    ap.add_argument("--park-delay-s", type=float, default=None,
                    help="delay from a session's chunk push to its park call; must land "
                         "after the slice finishes and before the next push (required "
                         "with --park-tail-blocks; the config declares the value)")
    ap.add_argument("--pre-seed-sessions", type=int, default=0,
                    help="warm-start barrier: pre-create this many sessions (sids 1..N) and "
                         "finish ALL their seed prefills before advertising ready — ticks "
                         "then start against fully-seeded sessions (requires --seed-tokens)")
    ap.add_argument("--ready-file", default=None)
    args = ap.parse_args()
    if args.park_tail_blocks and args.park_delay_s is None:
        ap.error("--park-tail-blocks requires --park-delay-s")

    log.info("loading STREAMING worker: %s (vLLM 0.23 append-to-resident-KV, take-from-stock, "
             "bandwidth-for-VRAM KV rotation: pool=%s host=%.1fGiB)",
             args.model,
             "full" if args.kv_pool_gib is None else f"{args.kv_pool_gib:.1f}GiB",
             args.host_offload_gib)
    eng = StreamingEngine(args.model, args.gpu_mem, args.max_model_len, args.max_num_seqs,
                          args.tpt, args.max_audio_chunks, seed_tokens=args.seed_tokens,
                          kv_pool_gib=args.kv_pool_gib, host_offload_gib=args.host_offload_gib,
                          park_tail_blocks=args.park_tail_blocks,
                          park_delay_s=args.park_delay_s,
                          sync_scheduling=args.sync_scheduling)
    # warm: one short session so JIT/CUDA-graph cost is paid before advertising ready.
    # Step no longer waits for tokens, so poll the sentinel session until it produced one.
    try:
        sil = (np.zeros(32000, dtype=np.float32), 16000)
        eng.step({WARMUP_SID: sil}, args.tpt)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline and not eng.sessions[WARMUP_SID].tokens:
            time.sleep(0.5)
        eng.cancel(WARMUP_SID)
        log.info("engine warm")
    except Exception:
        log.exception("warmup failed (continuing)")

    # WARM-START BARRIER: pre-create every session and run ALL seed prefills to
    # completion BEFORE advertising ready. Warm start models "each request
    # already has context"; the correct semantics is that the engine only
    # starts taking tick input once that context exists — not seeds and ticks
    # racing (the seed-flood transient: startup batch sync, early misses, a
    # permanent inventory scar). The barrier is structural: gateway and client
    # only start after the ready file, so the first tick physically cannot
    # precede the last seed. RELIES ON DETERMINISTIC SIDS: the gateway assigns
    # 1..N in admission order and the client opens exactly N sessions; a
    # session beyond N (e.g. a reconnect) falls back to lazy seeding at its
    # first push, with a log line.
    if args.seed_tokens and args.pre_seed_sessions:
        n = args.pre_seed_sessions
        log.info("warm-start barrier: seeding %d sessions x %d tokens ...", n, args.seed_tokens)
        t0 = time.monotonic()
        for sid in range(1, n + 1):
            eng._ensure(sid)   # gen() yields the seed input immediately, no audio needed
        while True:
            done = sum(1 for sid in range(1, n + 1) if eng.sessions[sid].tokens)
            if done == n:
                break
            if time.monotonic() - t0 > 300:
                log.error("warm-start barrier timed out (%d/%d seeded)", done, n)
                break
            time.sleep(0.5)
        # the seed's output token is CONTEXT, not response: skip it in the
        # take-from-stock inventory, or every session's first tick delivers a
        # junk token that burns the gateway's first-delivery exemption (fake
        # 3ms TTFA + tick-2 partials miscounted as starvation).
        for sid in range(1, n + 1):
            st = eng.sessions[sid]
            st.consumed = len(st.tokens)
            st.consumed_text = len(st.text)
        # barrier tail (quota mode): release the auto-park hold. NO park
        # here — the mirror cannot be complete at seed-end (see the finalize
        # utility's docstring); cycle 1 runs fully resident and the first
        # auto-park at slice-1's stop lands everyone in steady posture.
        if os.environ.get("OMNI_PARK_KEEP"):
            fut = asyncio.run_coroutine_threadsafe(
                eng.engine.engine_core.call_utility_async("warm_start_finalize"),
                eng.loop)
            log.info("warm-start finalize: %r", fut.result(timeout=60))
        log.info("warm-start barrier done: %d sessions seeded in %.1fs",
                 n, time.monotonic() - t0)
        eng.pre_seeded_n = n

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
