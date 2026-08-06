"""Production-grade Python/vLLM inference worker — the GPU backend behind the Go gateway.

A gRPC server wrapping VLLMBackend. The gateway calls Step() once per tick with the batch of
sessions needing compute; the worker runs ONE batched prefill+decode on the real engine and
returns each session's new tokens. The engine owns the GPU; Step calls are serialized (the
engine is not reentrant). Health/readiness, graceful shutdown, and structured logging included.

Input modalities: audio (PCM16), VISION (SessionInput.images, decoded to PIL), and text.
Output: text tokens + transcript. NOTE on AUDIO OUTPUT: vLLM serves the omni model's *thinker*
(text) only — the talker / code2wav speech-synthesis stack is not part of the vLLM forward, so
this worker returns transcript text, not synthesized PCM. Real spoken audio output is produced
by the Moshi worker (worker/moshi_server.py, native Mimi codec); for the omni models the served
output is the transcript (which is also what the quality benchmarks score).
"""
import argparse
import logging
import os
import sys
import threading
import time
from concurrent import futures

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

import grpc
import numpy as np
import inference_pb2 as pb
import inference_pb2_grpc as pb_grpc

logging.basicConfig(level=logging.INFO, format="%(asctime)s [worker] %(message)s")
log = logging.getLogger("worker")


def _decode_images(raw_list):
    """Decode encoded image bytes (PNG/JPEG) -> list[PIL.Image]. Skips any that fail."""
    if not raw_list:
        return None
    import io
    from PIL import Image
    out = []
    for raw in raw_list:
        try:
            out.append(Image.open(io.BytesIO(raw)).convert("RGB"))
        except Exception:
            log.exception("failed to decode an input image (%d bytes)", len(raw))
    return out or None


class AudioRing:
    """Preallocated sliding-window ring for continuous full-duplex ingest.

    Replaces the per-frame `np.concatenate([buf, new])[-W:]` (two O(window) copies per session
    per tick — measured ~10-13 ms at N=128) with an O(new-samples) write and a zero-copy
    contiguous view over the last W samples. Backing array is 2*W (history half + work half);
    we compact only when the write head reaches the end (~once every W/k frames)."""
    __slots__ = ("W", "b", "pos")

    def __init__(self, window_samples):
        self.W = int(window_samples)
        self.b = np.zeros(2 * self.W, dtype="float32")
        self.pos = self.W                       # primed with W samples of leading silence

    def push(self, arr):
        k = len(arr)
        if k >= self.W:                         # frame >= window: keep only the tail
            self.b[:self.W] = arr[-self.W:]
            self.pos = self.W
            return self.b[:self.W]
        if self.pos + k > 2 * self.W:           # compact: slide last W to front (rare)
            self.b[:self.W] = self.b[self.pos - self.W:self.pos].copy()
            self.pos = self.W
        self.b[self.pos:self.pos + k] = arr
        self.pos += k
        return self.b[self.pos - self.W:self.pos]   # zero-copy contiguous window


class InferenceServicer(pb_grpc.InferenceServicer):
    def __init__(self, backend, model_name, window_s=8.0, streaming_sessions=False,
                 max_ctx_chunks=0):
        self.be = backend
        self.model = model_name
        self.lock = threading.Lock()        # engine is single-threaded; serialize Step
        self.steps = 0
        self.audio_bufs = {}                # sid -> np.float32 (windowed recent audio)
        self.window_s = window_s            # continuous full-duplex: recent-audio window
        # STREAMING SESSIONS: incremental resident KV (append new chunk each frame, no re-encode
        # window) -> minute-level context + flat per-frame cost. carry = per-sid leftover audio
        # until a full chunk (block_s) accumulates, so each appended chunk is a clean block.
        self.streaming = streaming_sessions
        self.max_ctx_chunks = max_ctx_chunks
        self.chunk_carry = {}               # sid -> np.float32 leftover audio < one block

    def Step(self, request, context):
        with self.lock:
            _dbg = os.environ.get("WK_DEBUG")
            _t = time.perf_counter() if _dbg else 0.0
            tpt = int(request.tokens_per_tick or 1)
            turn_sids, cont_audio, all_sids = [], {}, []
            # 1) ingest
            for s in request.sessions:
                if s.cancel:
                    self.audio_bufs.pop(s.sid, None)
                    try:
                        self.be.remove_session(s.sid)
                    except Exception:
                        pass
                    continue
                all_sids.append(s.sid)
                if s.new_turn:                                   # turn-based path
                    audio = None
                    if s.audio_pcm16:
                        arr = (np.frombuffer(s.audio_pcm16, dtype="<i2").astype("float32") / 32768.0)
                        audio = (arr, int(s.sample_rate or 16000))
                    images = _decode_images(list(s.images))      # VISION
                    self.be.set_input(s.sid, audio=audio, images=images,
                                      text=s.text or "", max_tokens=int(s.max_tokens or 64))
                    turn_sids.append(s.sid)
                elif s.images:                                   # VISION in full-duplex: an image
                    # frame is a prefill-heavy turn (re-encoding an image every frame is wrong),
                    # so route audio+image through the turn path with one bounded response.
                    audio = None
                    if s.audio_pcm16:
                        arr = (np.frombuffer(s.audio_pcm16, dtype="<i2").astype("float32") / 32768.0)
                        audio = (arr, int(s.sample_rate or 16000))
                    self.be.set_input(s.sid, audio=audio, images=_decode_images(list(s.images)),
                                      text=s.text or "", max_tokens=int(s.max_tokens or 64))
                    turn_sids.append(s.sid)
                elif s.audio_pcm16:                              # CONTINUOUS full-duplex frame
                    sr = int(s.sample_rate or 16000)
                    arr = np.frombuffer(s.audio_pcm16, dtype="<i2").astype("float32")
                    arr *= (1.0 / 32768.0)                        # in-place; no extra alloc
                    if self.streaming:
                        # STREAMING SESSION: the new audio IS the next chunk to append to the
                        # resident growing context (no window). The gateway delivers ~one block
                        # per tick (period == block_s), so pass it straight through.
                        cont_audio[s.sid] = (arr.copy(), sr)
                    else:
                        ring = self.audio_bufs.get(s.sid)
                        if ring is None:
                            ring = self.audio_bufs[s.sid] = AudioRing(self.window_s * sr)
                        cont_audio[s.sid] = (ring.push(arr), sr)   # O(new) write, zero-copy window
            if _dbg:
                _ingest_ms = (time.perf_counter() - _t) * 1000.0; _t = time.perf_counter()
            # 2) batched compute: continuous frame (fd_step) and/or turn-based (step_stream)
            lat, outs = 0.0, {}
            if cont_audio:
                lat = (self.be.fd_step_stream(cont_audio, tpt, self.max_ctx_chunks)
                       if self.streaming else self.be.fd_step(cont_audio, tpt))
                outs.update(self.be.last_outputs or {})
            # Drive step_stream when a new turn arrives OR there are still in-flight responses
            # to decode. A response longer than `tpt` tokens spans multiple ticks; without the
            # in-flight check those requests would enqueue once and never finish decoding.
            if turn_sids or getattr(self.be, "inflight", None):
                lat = max(lat, self.be.step_stream(turn_sids, tpt))
                outs.update(getattr(self.be, "last_outputs", {}) or {})
            if _dbg:
                _t = time.perf_counter()
            # 3) build response
            resp = pb.StepResponse(gpu_ms=float(lat))
            sids = all_sids
            for sid in sids:
                toks = [int(t) for t in outs.get(sid, [])]
                text = ""
                if toks:
                    try:
                        text = self.be.detokenize(toks)
                    except Exception:
                        text = ""
                fin = bool(getattr(self.be, "is_finished", lambda x: False)(sid))
                resp.outputs.append(pb.SessionOutput(sid=sid, tokens=toks, text=text, finished=fin))
                if fin:
                    try:
                        self.be.remove_session(sid)
                    except Exception:
                        pass
            try:
                resp.in_flight = int(self.be.num_unfinished())
            except Exception:
                resp.in_flight = 0
            self.steps += 1
            if _dbg:
                _detok_ms = (time.perf_counter() - _t) * 1000.0
                log.info(f"[wkdbg] N={len(sids)} ingest={_ingest_ms:.2f}ms gpu={lat:.1f}ms "
                         f"detok+build={_detok_ms:.2f}ms")
            elif self.steps % 25 == 0:
                extra = ""
                if self.streaming and getattr(self.be, "stream_chunks", None):
                    mx = max((len(v) for v in self.be.stream_chunks.values()), default=0)
                    extra = f", resident_chunks={mx} (~{mx*2}s ctx)"
                log.info(f"step {self.steps}: {len(sids)} sessions, gpu {lat:.0f}ms, "
                         f"in_flight {resp.in_flight}{extra}")
            return resp

    def Health(self, request, context):
        try:
            inf = int(self.be.num_unfinished())
        except Exception:
            inf = 0
        return pb.HealthResponse(ready=True, in_flight=inf, model=self.model)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="openbmb/MiniCPM-o-2_6")
    ap.add_argument("--port", type=int, default=50051)
    ap.add_argument("--gpu-mem", type=float, default=0.6)
    ap.add_argument("--max-model-len", type=int, default=4096)
    ap.add_argument("--max-num-seqs", type=int, default=640)
    ap.add_argument("--max-num-batched-tokens", type=int, default=16384)
    ap.add_argument("--quantization", default=None)
    ap.add_argument("--ready-file", default=None)
    ap.add_argument("--window-s", type=float, default=8.0)   # continuous full-duplex audio window
    ap.add_argument("--streaming-sessions", action="store_true",
                    help="incremental resident KV (append new chunk/frame, no re-encode window) "
                         "-> minute-level context + flat per-frame cost")
    ap.add_argument("--max-ctx-chunks", type=int, default=0,
                    help="cap resident chunks (0=grow to max_model_len) to bound KV memory")
    ap.add_argument("--sliding-window-tokens", type=int, default=0,
                    help="force sliding-window attention of this many tokens on the LLM (>=30s of "
                         "context) -> bounds per-frame attention compute (flat latency) while "
                         "append-only growth keeps the KV/prefix cache intact (no re-encode)")
    ap.add_argument("--kv-fp8", action="store_true",
                    help="fp8 KV cache (kv_cache_dtype=fp8) — ~halves KV memory + KV bandwidth; "
                         "lifts the KV-bound streaming capacity and reduces growing-context drift")
    ap.add_argument("--batch-invariant", action="store_true",
                    help="enable vLLM batch-invariant kernels (TML 'defeating nondeterminism': "
                         "batch-invariant matmul/attention + IEEE fp32) so a session's output is "
                         "independent of batch composition -> bitwise-deterministic under load")
    args = ap.parse_args()

    if args.batch_invariant:
        # must be set before the engine (and its csrc/env overrides) initialize
        os.environ["VLLM_BATCH_INVARIANT"] = "1"
        log.info("BATCH-INVARIANT kernels enabled (deterministic output under load; FLASH_ATTN)")

    log.info(f"loading {args.model} on vLLM ...")
    from metronome.backends.vllm_backend import VLLMBackend
    extra = dict(enable_chunked_prefill=True, max_num_seqs=args.max_num_seqs,
                 max_num_batched_tokens=args.max_num_batched_tokens,
                 limit_mm_per_prompt={"audio": 1, "image": 1})
    if args.streaming_sessions:
        # streaming sessions hold many resident audio chunks per request; raise the mm limit and
        # enable the mm-processor cache (encoder-output reuse by chunk hash) so only the NEW chunk
        # is encoded each frame. Cap = max-ctx-chunks (or a generous default for grow-unbounded).
        n_aud = args.max_ctx_chunks if args.max_ctx_chunks else 256
        extra["limit_mm_per_prompt"] = {"audio": n_aud, "image": 1}
        extra["mm_processor_cache_gb"] = 8
    if args.batch_invariant:
        extra["attention_backend"] = "FLASH_ATTN"   # required by batch-invariant mode (engine arg)
    if args.sliding_window_tokens > 0:
        W = int(args.sliding_window_tokens)
        # The model is built in the EngineCore SUBPROCESS, so a parent monkeypatch doesn't reach it.
        # Set the env var read by the installed vLLM general-plugin (metronome_vllm_plugin), which
        # vLLM's load_general_plugins() executes INSIDE EngineCore -> it injects
        # per_layer_sliding_window into the Qwen3-MoE text attention, so vLLM builds a
        # SlidingWindowSpec that bounds BOTH attention compute AND stored KV (frees old blocks).
        os.environ["METRONOME_SWA_TOKENS"] = str(W)
        log.info("SLIDING-WINDOW streaming: W=%d tokens (via EngineCore plugin; bounded KV+attn)", W)
    if args.kv_fp8:
        extra["kv_cache_dtype"] = "fp8"             # ~2x KV headroom + less KV bandwidth
        # flashinfer (default backend) JIT-compiles the fp8-KV kernel and resolves nvcc via
        # CUDA_HOME (torch cpp_extension). The system nvcc is 11.5 (no sm_120); point it at the
        # 12.8 toolkit IN os.environ so the spawned EngineCore subprocess inherits it.
        cuda12 = "/usr/local/cuda-12.8"
        if os.path.isdir(cuda12):
            os.environ["CUDA_HOME"] = cuda12
            os.environ["PATH"] = cuda12 + "/bin:" + os.environ.get("PATH", "")
            log.info("FP8 KV cache enabled (kv_cache_dtype=fp8); CUDA_HOME=%s for flashinfer JIT",
                     cuda12)
        else:
            log.warning("FP8 KV enabled but %s not found; flashinfer JIT may use system nvcc", cuda12)
    if args.quantization:
        extra["quantization"] = args.quantization
    be = VLLMBackend(args.model, gpu_memory_utilization=args.gpu_mem,
                     max_model_len=args.max_model_len, trust_remote_code=True,
                     enforce_eager=False, in_frac=0.0, **extra)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8),
                         options=[("grpc.max_receive_message_length", 256 * 1024 * 1024),
                                  ("grpc.max_send_message_length", 256 * 1024 * 1024)])
    pb_grpc.add_InferenceServicer_to_server(
        InferenceServicer(be, args.model, window_s=args.window_s,
                          streaming_sessions=args.streaming_sessions,
                          max_ctx_chunks=args.max_ctx_chunks), server)
    if args.streaming_sessions:
        log.info("STREAMING SESSIONS enabled: incremental resident KV, no %ss window", args.window_s)
    # Warm the engine BEFORE advertising ready: the first multimodal prefill triggers
    # flashinfer autotuning + CUDA-graph capture, which can take tens of seconds and would
    # otherwise blow the gateway's per-Step gRPC deadline on the first real request (observed
    # to desync gateway/worker and hang sessions). A few dummy generates pay that cost here.
    if hasattr(be, "generate_once"):
        try:
            sil = (np.zeros(16000, dtype=np.float32), 16000)
            from PIL import Image
            img = Image.new("RGB", (448, 448))
            log.info("warming engine (audio + audio+image prefill/decode)...")
            be.generate_once(audio=sil, text="hello", max_tokens=8)
            be.generate_once(audio=sil, images=[img], text="describe", max_tokens=8)
            log.info("engine warm")
        except Exception:
            log.exception("engine warmup failed (continuing; first request may be slow)")
    server.add_insecure_port(f"0.0.0.0:{args.port}")
    server.start()
    log.info(f"vLLM worker serving gRPC on :{args.port}")
    if args.ready_file:
        open(args.ready_file, "w").write("ready")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=2.0)


if __name__ == "__main__":
    main()
