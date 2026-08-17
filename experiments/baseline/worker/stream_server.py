"""vLLM 0.23 STREAMING (append-to-resident-KV) gRPC worker — the GPU backend behind the Go gateway,
exposing the SAME proto (Step/Health) as worker/server.py so the identical gateway + clients drive it.

Unlike server.py (vLLM 0.19, fd_step: re-encode an 8 s window each frame), this holds ONE resident
*resumable* request per session (vLLM 0.23 StreamingInput / resumable requests) and APPENDS only the
new audio chunk each frame, reusing prior encoder output + KV -> flat per-frame ingest, minute-level
memory. The engine's continuous batching processes all N resident sessions together.

Run through experiments/baseline with the environment built by environment/setup.sh:
  FIX1 cu_seqlens · FIX2 capability gate · FIX3 NVCC cccl bypass · FIX4 mrope reconcile.

Bridge: gRPC Step (sync, gRPC threadpool) <-> a single asyncio loop thread that runs AsyncLLM and one
long-lived engine.generate() per session fed by a per-session asyncio.Queue. Step pushes each due
session's chunk and waits (bounded) for up to tpt new tokens, then returns them.

ORIGIN: copied from third_party/metronome/worker/stream_server.py (the pin stays untouched and
is still run verbatim by --mode vanilla) and permanently diverged; upstream updates are not
tracked. Behavioral changes vs that origin:
  1. mm_processor_cache_gb 8 -> 0 (avoid cross-thread mutation of the LRU under parallel ingest)
  2. AsyncLLM._add_streaming_input_request is monkeypatched with a hand-copied vLLM 0.23 internal
     (second-order fork of a private API; any vLLM upgrade must re-audit it)
  3. warm-start prefill via --seed-tokens is added (the seed prompt predicate checks it),
     with the same warm-start barrier as the conveyor worker (--pre-seed-sessions: ALL
     seed prefills complete before ready — state construction precedes the tick cadence).
     Seed runs REQUIRE the engine_fix sitecustomize (worker/engine_fix/, injected by the
     runner when seed_tokens > 0): upstream freezes session.max_tokens at the first
     input's params — the seed's max_tokens=1 would cap every segment at 1 token.
  4. upstream features this repo never runs were removed: windowed/sliding KV, turn-eos eval
     mode, non-Qwen2.5-Omni prompt templates
No experiment may add another copy of this worker.

Instrumentation (the writers live in tracekit/collectors/worker_obs.py — the
one producer shared with conveyor; line grammars live with the consumers in
tracekit/parse.py): PERREQ_LOG appends per-request event lines on one shared
perf clock (seconds since process start), with a single "C <perf> <epoch>"
clock-pairing line at open:
  P <t> <sid>                          gateway tick pushed this session's 2s audio to its queue
  F <t> <sid> <frame>                  engine pulled that chunk into the request's input stream
  T <t> <sid> <ntok> <nprompt> <frame> request's output grew to ntok (nprompt = engine-side
                                       prompt token count if exposed, else 0)
plus the five ingest stations IQ/IS/IE/IR/IA (dispatch, FE start, FE done,
loop handoff, admitted). METRONOME_STATLOG additionally gains
pre=<cumulative preemption count> per line.

PARINGEST variant: additionally monkeypatches AsyncLLM._add_streaming_input_request so each
chunk's input_processor.process_inputs runs in a ThreadPoolExecutor instead of synchronously on
the event loop (vllm 0.23 async_llm.py handle_inputs blocks the loop ~265ms/chunk on this host,
serializing all sessions' ingest). mm processor cache is disabled (mm_processor_cache_gb=0) to
avoid cross-thread mutation of its LRU state; hits are ~absent under FD_PHASE_STAGGER anyway.
Per-session chunk ORDER is preserved: each session's handle_inputs task still awaits its own
chunks sequentially — only different sessions overlap.
"""
import argparse, asyncio, logging, os, sys, threading, time
from concurrent import futures
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_MET = os.environ.get("METRONOME_ROOT", str(_ROOT / "third_party" / "metronome"))
sys.path.insert(0, str(_ROOT))   # for tracekit.collectors.worker_obs (shared observation)
sys.path.insert(0, _MET)
sys.path.insert(0, os.path.join(_MET, "worker"))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "WARNING")

import grpc
import numpy as np
import inference_pb2 as pb
import inference_pb2_grpc as pb_grpc

from tracekit.collectors.worker_obs import perreq_logger, stat_logger_classes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [stream-worker] %(message)s")
log = logging.getLogger("stream-worker")

# Warmup sentinel session id. Contract shared across process boundaries
# (tracekit/parse.py excludes it from every statistic); a contract test pins
# the declarations together.
WARMUP_SID = 10**9

# Shared observation producer (tracekit): per-request events on one perf clock,
# with the clock-pairing C line written at open.
_pev = perreq_logger()


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

    def __init__(self, loop):
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

    def __init__(self, model, gpu_mem, max_model_len, max_num_seqs, tpt, wait_budget_s,
                 max_audio_chunks, seed_tokens=0):
        from vllm import SamplingParams
        from vllm.engine.arg_utils import AsyncEngineArgs
        from vllm.v1.engine.async_llm import AsyncLLM
        self.SamplingParams = SamplingParams
        self.tpt = tpt
        self.wait_budget = wait_budget_s
        self.seed_tokens = seed_tokens   # warm-start: prefill ~K filler tokens per session at start
        self.sessions: dict[int, Session] = {}
        self.lock = threading.Lock()
        self.loop = asyncio.new_event_loop()
        self.thr = threading.Thread(target=self._loop_forever, daemon=True)
        self.thr.start()
        args = AsyncEngineArgs(
            model=model, trust_remote_code=True, gpu_memory_utilization=gpu_mem,
            max_model_len=max_model_len, enforce_eager=False, max_num_seqs=max_num_seqs,
            limit_mm_per_prompt={"audio": max_audio_chunks, "image": 0},
            mm_processor_cache_gb=0)   # cache off: no cross-thread LRU mutation (hits ~absent anyway)
        _patch_parallel_ingest(workers=int(os.environ.get("INGEST_WORKERS", "8")))
        fut = asyncio.run_coroutine_threadsafe(self._make_engine(args), self.loop)
        self.engine = fut.result()
        log.info("AsyncLLM streaming engine ready (model=%s)", model)

    def _loop_forever(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _make_engine(self, args):
        from vllm.v1.engine.async_llm import AsyncLLM
        # shared stat logger (tracekit worker_obs): kv.log + per_iteration.log
        loggers = stat_logger_classes()
        if loggers:
            return AsyncLLM.from_engine_args(args, stat_loggers=loggers)
        return AsyncLLM.from_engine_args(args)

    # ---- per-session resident resumable request (unbounded append-to-resident-KV) ----
    async def _run_session(self, sid: int, st: Session):
        from vllm.engine.protocol import StreamingInput
        base_sp = self.SamplingParams(temperature=0.0, max_tokens=self.tpt + 8, ignore_eos=True)
        n = [0]

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
                st.frame += 1; n[0] += 1
                _pev("F", sid, st.frame)
                prompt = (HEAD + APH + INSTR + ASST) \
                    if (n[0] == 1 and not self.seed_tokens) else (APH + TRAIL)
                # max_tokens is PER-SEGMENT (each chunk's update folds prior
                # output into the prompt and clears the output count). The
                # engine's stop check reads a value frozen at the FIRST input
                # (upstream bug), so every formal run effectively capped each
                # segment at tpt+8 regardless of what was sent; declare that
                # cap explicitly so behavior is IDENTICAL whether the frozen
                # regime or the seed-run refresh fix (engine_fix, injected
                # only when --seed-tokens > 0) is in effect.
                sp = self.SamplingParams(temperature=0.0, max_tokens=self.tpt + 8,
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
            st = Session(self.loop)
            self.sessions[sid] = st
            st.task = asyncio.run_coroutine_threadsafe(self._run_session(sid, st), self.loop)
        return st

    # ---- sync Step bridge ----
    def step(self, sid_audio: dict, tpt: int) -> dict:
        t0 = time.perf_counter()
        pending = []
        for sid, (arr, sr) in sid_audio.items():
            st = self._ensure(sid)
            asyncio.run_coroutine_threadsafe(st.queue.put((arr, sr)), self.loop)
            pending.append(sid)
            _pev("P", sid)
        out = {}      # sid -> (tokens, text_delta)
        deadline = t0 + self.wait_budget
        remaining = set(pending)
        while remaining and time.perf_counter() < deadline:
            for sid in list(remaining):
                st = self.sessions[sid]
                if len(st.tokens) > st.consumed:
                    new = st.tokens[st.consumed: st.consumed + tpt]
                    txt = st.text[st.consumed_text:]
                    out[sid] = (new, txt)
                    st.consumed += len(new)
                    st.consumed_text = len(st.text)
                    remaining.discard(sid)
                elif st.error or st.done:           # nothing new and finished -> don't stall the tick
                    remaining.discard(sid)
            if remaining:
                time.sleep(0.003)
        return out, (time.perf_counter() - t0) * 1000.0

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
                log.info("step %d: %d sessions, %.0fms, resident_frames=%d (~%ds ctx), "
                         "tot_tokens=%d, sample=%r", self.steps, len(all_sids), lat, mx, mx * 2,
                         self.eng.total_tokens(), self.eng.sample_text())
            return resp

    def Health(self, request, context):
        return pb.HealthResponse(ready=True, in_flight=self.eng.num_unfinished(), model=self.model)


def main():
    # Engine geometry has NO defaults here on purpose: the runner translates
    # experiments/baseline/config/ (the single declaration point) into argv,
    # and a manual launch must be equally explicit — a second set of defaults
    # is a second source of truth that silently drifts.
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--gpu-mem", type=float, required=True)
    ap.add_argument("--max-model-len", type=int, required=True)
    ap.add_argument("--max-num-seqs", type=int, required=True)
    ap.add_argument("--tpt", type=int, required=True)
    ap.add_argument("--wait-budget-s", type=float, required=True)
    ap.add_argument("--max-audio-chunks", type=int, required=True)
    ap.add_argument("--seed-tokens", type=int, default=0,
                    help="warm-start: prefill about this many unique filler text tokens per "
                         "session at start (0 = off) — compresses time-to-wall, makes ctx a "
                         "controlled variable")
    ap.add_argument("--pre-seed-sessions", type=int, default=0,
                    help="warm-start barrier: pre-create this many sessions (sids 1..N) and "
                         "finish ALL their seed prefills before advertising ready — ticks "
                         "then start against fully-seeded sessions (requires --seed-tokens)")
    ap.add_argument("--ready-file", default=None)
    args = ap.parse_args()

    log.info("loading STREAMING worker: %s (vLLM 0.23 append-to-resident-KV, unbounded)", args.model)
    eng = StreamingEngine(args.model, args.gpu_mem, args.max_model_len, args.max_num_seqs,
                          args.tpt, args.wait_budget_s, args.max_audio_chunks,
                          seed_tokens=args.seed_tokens)
    # warm: one short session so JIT/CUDA-graph cost is paid before advertising ready.
    try:
        sil = (np.zeros(32000, dtype=np.float32), 16000)
        eng.step({WARMUP_SID: sil}, args.tpt); eng.cancel(WARMUP_SID)
        log.info("engine warm")
    except Exception:
        log.exception("warmup failed (continuing)")

    # WARM-START BARRIER (same semantics as the conveyor worker, minus the
    # park finalize — baseline runs no mechanism): warm start is a one-shot
    # STATE CONSTRUCTION ("each session already has context"), so the engine
    # only starts taking tick input once that context exists — seeds and
    # ticks must not race (lazy seeding would mix seed LARGE prefills into
    # the first ticks' cadence). Structural: gateway and client only start
    # after the ready file, so the first tick physically cannot precede the
    # last seed. RELIES ON DETERMINISTIC SIDS: the gateway assigns 1..N in
    # admission order and the client opens exactly N sessions; a session
    # beyond N falls back to lazy seeding at its first push, with a log line.
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
        # the seed's output token is CONTEXT, not response: skip it in
        # delivery, or every session's first tick returns a junk token.
        for sid in range(1, n + 1):
            st = eng.sessions[sid]
            st.consumed = len(st.tokens)
            st.consumed_text = len(st.text)
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
