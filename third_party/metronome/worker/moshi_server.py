"""Moshi continuous full-duplex gRPC worker (runs in the moshi venv, torch<2.10).

Moshi is the native streaming-codec full-duplex model: each 80 ms frame, Mimi encodes the
incoming audio and the LM emits a token — true per-frame, no turns, no re-prefill. We batch B
streams via `streaming(B)` and, per gRPC Step, feed each session's new audio frame and step the
batched LM once. Same gRPC contract as the vLLM worker, so the SAME Go gateway drives it.
"""
import argparse, logging, os, sys, threading, time
from concurrent import futures
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grpc
import numpy as np
import inference_pb2 as pb
import inference_pb2_grpc as pb_grpc

logging.basicConfig(level=logging.INFO, format="%(asctime)s [moshi-worker] %(message)s")
log = logging.getLogger("moshi")


class MoshiServicer(pb_grpc.InferenceServicer):
    def __init__(self, maxb):
        import torch
        from moshi.models import LMGen, loaders
        self.torch = torch
        ckpt = loaders.CheckpointInfo.from_hf_repo(loaders.DEFAULT_REPO)
        self.mimi = ckpt.get_mimi(device="cuda")
        self.lm = ckpt.get_moshi(device="cuda")
        self.tok = ckpt.get_text_tokenizer()
        self.lm_gen = LMGen(self.lm, use_sampling=True, temp=0.8, temp_text=0.7)
        self.sr = int(self.mimi.sample_rate)
        self.frame = int(self.mimi.sample_rate / self.mimi.frame_rate)   # samples per 80ms frame
        self.maxb = maxb
        # pinned host staging buffer + its resident GPU twin: assemble the batch on the host,
        # then a single non-blocking H2D copy/tick (vs one tiny copy per active slot).
        self._host_batch_pinned = torch.empty(maxb, 1, self.frame, dtype=torch.float32, pin_memory=True)
        self._host_batch = self._host_batch_pinned.numpy()        # numpy view of the pinned memory
        self._host_batch_t = torch.zeros(maxb, 1, self.frame, device="cuda")
        # enter batched streaming for the whole lifetime
        self.mimi.streaming_forever(maxb)
        self.lm_gen.streaming_forever(maxb)
        self.slots = {}              # sid -> slot index (0..maxb-1)
        self.free = list(range(maxb))
        self.carry = {}              # slot -> leftover PCM samples (np.float32)
        self.lock = threading.Lock()
        self.steps = 0
        log.info(f"Moshi ready: {self.sr}Hz, {self.frame} samples/frame, batch slots {maxb}")

    def _slot(self, sid):
        if sid in self.slots:
            return self.slots[sid]
        if not self.free:
            return None
        s = self.free.pop(); self.slots[sid] = s; self.carry[s] = np.zeros(0, "float32")
        return s

    def Step(self, request, context):
        torch = self.torch
        with self.lock:
            t0 = time.perf_counter()
            # Assemble the whole [maxb,1,frame] batch on the HOST first, then do ONE H2D copy.
            # (Was: a separate torch.from_numpy(..).to('cuda') per active slot — 128 tiny H2D
            #  launches per tick. One pinned async copy removes that per-slot launch overhead.)
            host = self._host_batch                      # numpy view of pinned [maxb,1,frame]
            host.fill(0.0)
            slot_sid = {}
            for s in request.sessions:
                if s.cancel:
                    sl = self.slots.pop(s.sid, None)
                    if sl is not None:
                        self.free.append(sl); self.carry.pop(sl, None)
                    continue
                sl = self._slot(s.sid)
                if sl is None:
                    continue
                slot_sid[sl] = s.sid
                pcm = s.audio_pcm16
                if pcm and len(pcm) % 2:        # int16 needs an even byte count
                    log.warning("sid %s: odd audio byte length %d, dropping last byte",
                                s.sid, len(pcm))
                    pcm = pcm[:-1]
                if pcm:
                    arr = (np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768.0)
                    buf = np.concatenate([self.carry.get(sl, np.zeros(0, "float32")), arr])
                else:
                    buf = self.carry.get(sl, np.zeros(0, "float32"))
                if len(buf) >= self.frame:
                    host[sl, 0, :] = buf[:self.frame]; self.carry[sl] = buf[self.frame:]
                else:
                    self.carry[sl] = buf   # not enough yet -> silence this frame
            # one batched full-duplex frame
            try:
                with torch.no_grad():
                    batch = self._host_batch_t.copy_(self._host_batch_pinned, non_blocking=True)  # single H2D
                    codes = self.mimi.encode(batch)         # [maxb, K, 1]
                    out = self.lm_gen.step(codes)           # [maxb, ...] one text token/slot
                torch.cuda.synchronize()                     # real GPU time, not just kernel launch
            except Exception as e:
                log.exception("Moshi GPU step failed")
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"moshi step failed: {e}")
                return pb.StepResponse(gpu_ms=0.0, in_flight=len(self.slots))
            # AUDIO OUTPUT: out is [B, dep_q+1, 1] — row 0 is the text token, rows 1: are the
            # Mimi audio codebooks. Decode them back to PCM for real spoken output. During the
            # first max_delay frames some codes are ungenerated (sentinel < 0); decode the batch
            # with negatives clamped and only emit audio for slots whose codes were all valid.
            pcm_np, valid = None, None
            if out is not None and out.shape[1] > 1:
                try:
                    acodes = out[:, 1:, :]                          # [B, dep_q, 1]
                    valid = (acodes >= 0).all(dim=1).squeeze(-1)    # [B] bool
                    with torch.no_grad():
                        pcm = self.mimi.decode(acodes.clamp(min=0))  # [B, 1, frame]
                    pcm_np = (pcm[:, 0].clamp(-1, 1) * 32767.0).to(torch.int16).cpu().numpy()
                except Exception:
                    log.exception("Mimi audio decode failed; emitting text only")
                    pcm_np = None
            lat = (time.perf_counter() - t0) * 1000.0
            resp = pb.StepResponse(gpu_ms=float(lat), in_flight=len(self.slots))
            for sl, sid in slot_sid.items():
                toks, text = [], ""
                if out is not None:
                    tid = int(out[sl, 0].item())
                    if tid not in (0, 3) and tid != self.tok.eos_id():
                        toks = [tid]
                        try:
                            text = self.tok.id_to_piece(tid).replace("▁", " ")
                        except Exception:
                            text = ""
                so = pb.SessionOutput(sid=sid, tokens=toks, text=text, finished=False)
                if pcm_np is not None and valid is not None and bool(valid[sl]):
                    so.audio_out = pcm_np[sl].tobytes()
                    so.audio_sr = self.sr
                resp.outputs.append(so)
            self.steps += 1
            if self.steps % 100 == 0:
                log.info(f"step {self.steps}: {len(slot_sid)} active, {lat:.0f}ms")
            return resp

    def Health(self, request, context):
        return pb.HealthResponse(ready=True, in_flight=len(self.slots), model="moshi")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=50051)
    ap.add_argument("--max-batch", type=int, default=64)
    ap.add_argument("--ready-file", default=None)
    args = ap.parse_args()
    log.info("loading Moshi ...")
    servicer = MoshiServicer(args.max_batch)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4),
                         options=[("grpc.max_receive_message_length", 256 * 1024 * 1024),
                                  ("grpc.max_send_message_length", 256 * 1024 * 1024)])
    pb_grpc.add_InferenceServicer_to_server(servicer, server)
    server.add_insecure_port(f"0.0.0.0:{args.port}")
    server.start()
    log.info(f"Moshi worker serving gRPC on :{args.port} (max batch {args.max_batch})")
    if args.ready_file:
        open(args.ready_file, "w").write("ready")
    server.wait_for_termination()


if __name__ == "__main__":
    main()
