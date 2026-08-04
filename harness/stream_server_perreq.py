"""vLLM 0.23 STREAMING (append-to-resident-KV) gRPC worker — the GPU backend behind the Go gateway,
exposing the SAME proto (Step/Health) as worker/server.py so the identical gateway + clients drive it.

Unlike server.py (vLLM 0.19, fd_step: re-encode an 8 s window each frame), this holds ONE resident
*resumable* request per session (vLLM 0.23 StreamingInput / resumable requests) and APPENDS only the
new audio chunk each frame, reusing prior encoder output + KV -> flat per-frame ingest, minute-level
memory. The engine's continuous batching processes all N resident sessions together.

Run under the patched ~/vllm023-venv with the fix env (see experiments/run_stream_gateway.sh):
  FIX1 cu_seqlens · FIX2 capability gate · FIX3 NVCC cccl bypass · FIX4 mrope reconcile.

Bridge: gRPC Step (sync, gRPC threadpool) <-> a single asyncio loop thread that runs AsyncLLM and one
long-lived engine.generate() per session fed by a per-session asyncio.Queue. Step pushes each due
session's chunk and waits (bounded) for up to tpt new tokens, then returns them.

PERREQ variant (omni-anything, instrumented copy of metronome/worker/stream_server.py — the clone
stays untouched; upstream logic is byte-identical, only logging added). PERREQ_LOG=<path> appends
per-request event lines on one shared clock (seconds since process start):
  P <t> <sid>                          gateway tick pushed this session's 2s audio to its queue
  F <t> <sid> <frame>                  engine pulled that chunk into the request's input stream
  T <t> <sid> <ntok> <nprompt> <frame> request's output grew to ntok (nprompt = engine-side
                                       prompt token count if exposed, else 0)
METRONOME_STATLOG additionally gains pre=<cumulative preemption count> per line.
"""
import argparse, asyncio, logging, os, sys, threading, time
from concurrent import futures

_MET = os.environ.get(
    "METRONOME_ROOT",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "metronome"))
sys.path.insert(0, _MET)
sys.path.insert(0, os.path.join(_MET, "worker"))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "WARNING")

import grpc
import numpy as np
import inference_pb2 as pb
import inference_pb2_grpc as pb_grpc

logging.basicConfig(level=logging.INFO, format="%(asctime)s [stream-worker] %(message)s")
log = logging.getLogger("stream-worker")

_PT0 = time.perf_counter()
_PERREQ = open(os.environ["PERREQ_LOG"], "a", buffering=1) if os.environ.get("PERREQ_LOG") else None

def _pev(kind, *vals):
    if _PERREQ:
        _PERREQ.write(f"{kind} {time.perf_counter() - _PT0:.3f} " + " ".join(map(str, vals)) + "\n")

# Per-model prompt pieces. Frame 1 opens the assistant turn after an instruction so the model emits a
# REAL response (not chat-template filler); later frames append more audio. Trailing token after each
# audio placeholder avoids the mrope boundary (belt + FIX4).
def model_prompts(model: str):
    """Return (HEAD, APH, INSTR, ASST, TRAIL) for the model's audio chat template."""
    m = (model or "").lower()
    if "qwen3" in m and "omni" in m:
        aph = "<|audio_start|><|audio_pad|><|audio_end|>"
        head = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n"
        return head, aph, " Listen to the audio and answer any question in it.", \
            "<|im_end|>\n<|im_start|>assistant\n", "\n"
    if "omni" in m:  # Qwen2.5-Omni
        aph = "<|audio_bos|><|AUDIO|><|audio_eos|>"
        head = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n"
        return head, aph, " Listen to the audio and answer any question in it.", \
            "<|im_end|>\n<|im_start|>assistant\n", "\n"
    if "minicpm" in m:
        aph = "(<audio>./</audio>)\n"
        head = "<|im_start|>user\n"
        return head, aph, "Answer the question in the audio. /no_think", \
            "<|im_end|>\n<|im_start|>assistant\n", "\n"
    # generic fallback
    return "<|im_start|>user\n", "<|audio_start|><|audio_pad|><|audio_end|>", " Answer.", \
        "<|im_end|>\n<|im_start|>assistant\n", "\n"


class Session:
    __slots__ = ("queue", "tokens", "text", "base", "consumed", "consumed_text", "frame",
                 "epoch", "stop", "done", "error", "task")

    def __init__(self, loop):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.tokens: list = []      # cumulative output token ids (across epochs)
        self.text: str = ""         # cumulative detokenized text (current epoch)
        self.base: list = []        # tokens from completed epochs (windowed-KV resets)
        self.consumed = 0           # tokens already returned to the gateway
        self.consumed_text = 0      # chars of text already returned (current epoch)
        self.frame = 0
        self.epoch = 0
        self.stop = False
        self.done = False
        self.error = None
        self.task = None


class StreamingEngine:
    """AsyncLLM + per-session resident resumable requests, driven from a sync Step()."""

    def __init__(self, model, gpu_mem, max_model_len, max_num_seqs, tpt, wait_budget_s,
                 max_audio_chunks, window_frames=0, window_overlap=0, turn_eos=0):
        from vllm import SamplingParams
        from vllm.engine.arg_utils import AsyncEngineArgs
        from vllm.v1.engine.async_llm import AsyncLLM
        self.SamplingParams = SamplingParams
        self.tpt = tpt
        self.wait_budget = wait_budget_s
        self.window_frames = window_frames
        self.window_overlap = window_overlap
        self.turn_eos = turn_eos
        self.HEAD, self.APH, self.INSTR, self.ASST, self.TRAIL = model_prompts(model)
        self.sessions: dict[int, Session] = {}
        self.lock = threading.Lock()
        self.loop = asyncio.new_event_loop()
        self.thr = threading.Thread(target=self._loop_forever, daemon=True)
        self.thr.start()
        args = AsyncEngineArgs(
            model=model, trust_remote_code=True, gpu_memory_utilization=gpu_mem,
            max_model_len=max_model_len, enforce_eager=False, max_num_seqs=max_num_seqs,
            limit_mm_per_prompt={"audio": max_audio_chunks, "image": 0}, mm_processor_cache_gb=8)
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
                def record(self, scheduler_stats, iteration_stats, mm_cache_stats=None, engine_idx=0):
                    if iteration_stats is not None:
                        self._pre += getattr(iteration_stats, "num_preempted_reqs", 0)
                    if scheduler_stats is None:
                        return
                    now = _time.time()
                    if now - self._last < 1.0:   # throttle to ~1 Hz
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

    # ---- per-session resident resumable request (with optional SLIDING windowed-KV) ----
    async def _run_session(self, sid: int, st: Session):
        from vllm.engine.protocol import StreamingInput
        W = self.window_frames     # 0 = unbounded (vanilla vLLM-realtime); >0 = Metronome windowed-KV
        OV = self.window_overlap if self.window_overlap else (W // 2)  # carryover (sliding) frames
        base_sp = self.SamplingParams(temperature=0.0, max_tokens=self.tpt + 8, ignore_eos=True)

        # TURN-EOS mode (correctness eval): each turn = accumulate audio over `turn_eos` frames, then
        # generate ONE bounded answer terminated by EOS (no ignore_eos filler) -> clean per-frame
        # correctness. Repeats turns for the session duration; each turn re-encodes its window (bounded KV).
        if self.turn_eos:
            T = self.turn_eos
            textbase = ""                            # cumulative text across turns (monotonic for step())
            while not st.stop:
                st.epoch += 1
                buf = []

                async def gen():
                    for _ in range(T):
                        item = await st.queue.get()
                        if item is None:
                            st.stop = True
                            return
                        st.frame += 1
                        buf.append(item)
                    ph = self.APH * len(buf)
                    yield StreamingInput(
                        prompt={"prompt": self.HEAD + ph + self.INSTR + self.ASST,
                                "multi_modal_data": {"audio": list(buf)}},
                        sampling_params=self.SamplingParams(temperature=0.0, max_tokens=96,
                                                            ignore_eos=False))  # stop at EOS = clean answer
                try:
                    async for out in self.engine.generate(gen(), base_sp, f"s{sid}t{st.epoch}"):
                        st.tokens = st.base + list(out.outputs[0].token_ids)
                        st.text = textbase + out.outputs[0].text       # cumulative, never shrinks
                except Exception as e:  # noqa
                    st.error = f"{type(e).__name__}: {str(e)[:160]}"; break
                st.base = list(st.tokens)
                textbase = st.text + " | "           # turn separator; next turn appends
            st.done = True
            return

        carry: list = []           # recent (arr,sr) chunks carried into the next epoch (the slide)
        while not st.stop:
            st.epoch += 1
            st.text = ""; st.consumed_text = 0      # text stream restarts per epoch
            seed = list(carry)                      # window content to RE-ENCODE at epoch start
            recent = list(carry)                    # full window held this epoch (grows with new chunks)
            carry = []
            n = [len(seed)]

            async def gen():
                # 1) SLIDING re-seed: re-encode the carried-over recent window ONCE (one prefill of OV
                #    chunks; the mm-processor cache often reuses their encoder output) so context is
                #    preserved across the slide. Text after the audio (INSTR+ASST) avoids the mrope edge.
                if seed:
                    head = self.HEAD + (self.APH * len(seed)) + self.INSTR + self.ASST
                    yield StreamingInput(
                        prompt={"prompt": head, "multi_modal_data": {"audio": list(seed)}},
                        sampling_params=self.SamplingParams(
                            temperature=0.0, max_tokens=self.tpt * max(1, n[0]) + 8, ignore_eos=True))
                # 2) stream new chunks (append-to-resident-KV within the window)
                while True:
                    item = await st.queue.get()
                    if item is None:
                        st.stop = True
                        return
                    arr, sr = item
                    st.frame += 1; n[0] += 1
                    _pev("F", sid, st.frame)
                    recent.append((arr, sr))
                    prompt = (self.HEAD + self.APH + self.INSTR + self.ASST) \
                        if (n[0] == 1 and not seed) else (self.APH + self.TRAIL)
                    sp = self.SamplingParams(temperature=0.0, max_tokens=self.tpt * n[0] + 8,
                                             ignore_eos=True)
                    yield StreamingInput(
                        prompt={"prompt": prompt, "multi_modal_data": {"audio": (arr, sr)}},
                        sampling_params=sp)
                    if W and n[0] >= W:
                        # end epoch -> this resumable request's KV is freed (bounded to W frames);
                        # the next epoch re-seeds from the last OV frames (sliding window).
                        return

            try:
                async for out in self.engine.generate(gen(), base_sp, f"s{sid}e{st.epoch}"):
                    st.tokens = st.base + list(out.outputs[0].token_ids)
                    st.text = out.outputs[0].text
                    _pev("T", sid, len(st.tokens),
                         len(getattr(out, "prompt_token_ids", None) or []), st.frame)
            except Exception as e:  # noqa
                st.error = f"{type(e).__name__}: {str(e)[:160]}"
                log.warning("session %s ended: %s", sid, st.error)
                break
            st.base = list(st.tokens)                # carry completed-epoch tokens
            carry = recent[-OV:] if (W and OV) else []   # slide: keep the recent OV frames
        st.done = True

    def _ensure(self, sid: int) -> Session:
        st = self.sessions.get(sid)
        if st is None:
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic")
    ap.add_argument("--port", type=int, default=50051)
    ap.add_argument("--gpu-mem", type=float, default=0.85)
    ap.add_argument("--max-model-len", type=int, default=8192)
    ap.add_argument("--max-num-seqs", type=int, default=128)
    ap.add_argument("--tpt", type=int, default=25)
    ap.add_argument("--wait-budget-s", type=float, default=1.6)
    ap.add_argument("--max-audio-chunks", type=int, default=64)
    ap.add_argument("--window-frames", type=int, default=0,
                    help="Metronome windowed-KV: bound per-session resident context to this many "
                         "frames (free KV at window boundaries). 0 = vanilla vLLM-realtime (unbounded).")
    ap.add_argument("--window-overlap", type=int, default=0,
                    help="SLIDING window: carry over this many recent frames into the next window and "
                         "re-encode them once (preserves context across the slide). 0 = W//2.")
    ap.add_argument("--turn-eos", type=int, default=0,
                    help="correctness eval: per turn, accumulate this many audio frames then generate "
                         "ONE EOS-terminated answer (no ignore_eos filler). 0 = continuous streaming.")
    ap.add_argument("--ready-file", default=None)
    args = ap.parse_args()

    mode = (f"sliding windowed-KV W={args.window_frames}f overlap={args.window_overlap or args.window_frames//2}f"
            if args.window_frames else "unbounded (vanilla vLLM-realtime)")
    log.info("loading STREAMING worker: %s (vLLM 0.23 append-to-resident-KV, %s)", args.model, mode)
    eng = StreamingEngine(args.model, args.gpu_mem, args.max_model_len, args.max_num_seqs,
                          args.tpt, args.wait_budget_s, args.max_audio_chunks,
                          window_frames=args.window_frames, window_overlap=args.window_overlap,
                          turn_eos=args.turn_eos)
    # warm: one short session so JIT/CUDA-graph cost is paid before advertising ready.
    try:
        sil = (np.zeros(32000, dtype=np.float32), 16000)
        eng.step({10**9: sil}, args.tpt); eng.cancel(10**9)
        log.info("engine warm")
    except Exception:
        log.exception("warmup failed (continuing)")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8),
                         options=[("grpc.max_receive_message_length", 256 * 1024 * 1024),
                                  ("grpc.max_send_message_length", 256 * 1024 * 1024)])
    pb_grpc.add_InferenceServicer_to_server(Servicer(eng, args.model), server)
    server.add_insecure_port(f"0.0.0.0:{args.port}")
    server.start()
    log.info("STREAMING worker serving gRPC on :%d", args.port)
    if args.ready_file:
        open(args.ready_file, "w").write("ready")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=2.0)


if __name__ == "__main__":
    main()
