"""No-op transport server for the Metronome transport ablation.

Isolates PURE transport + dispatch cost (no GPU, no model): each request carries
N sessions' per-frame audio; the server returns 1 token/session. Four wire mechanisms:
  grpc : the production stack (gRPC/HTTP-2 + protobuf), no-op Step
  zmq  : ZeroMQ REP, raw length-framed binary
  uds  : raw AF_UNIX stream socket, length-prefixed binary
  shm  : /dev/shm mmap data-plane (zero-copy) + AF_UNIX tiny control message

Request frame (zmq/uds): u32 N, u32 chunk_bytes, then N*chunk_bytes audio (sids implicit 0..N-1).
Response frame:          u32 N, then N*(u32 sid, u32 token).
shm control (uds):       u32 N, u32 chunk_bytes  (audio already in the ring at offset 0).
"""
import argparse, mmap, os, socket, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "worker"))

SHM_PATH = "/dev/shm/mtb_ring"
SHM_SIZE = 64 * 1024 * 1024


def _resp(n):
    # u32 N, then N*(u32 sid, u32 token)  -- token=1 for all
    return struct.pack("<I", n) + b"".join(struct.pack("<II", i, 1) for i in range(n))


def run_grpc(port):
    import grpc
    from concurrent import futures
    import inference_pb2 as pb
    import inference_pb2_grpc as pbg
    import numpy as np

    class S(pbg.InferenceServicer):
        def Step(self, req, ctx):
            # touch the audio as the real worker does (numpy view) to be fair
            for s in req.sessions:
                if s.audio_pcm16:
                    _ = np.frombuffer(s.audio_pcm16, dtype="<i2")
            out = pb.StepResponse(gpu_ms=0.0, in_flight=len(req.sessions))
            for s in req.sessions:
                out.outputs.append(pb.SessionOutput(sid=s.sid, tokens=[1], text="x", finished=False))
            return out

        def Health(self, req, ctx):
            return pb.HealthResponse(ready=True, in_flight=0, model="noop")

    srv = grpc.server(futures.ThreadPoolExecutor(max_workers=4),
                      options=[("grpc.max_receive_message_length", 256 << 20),
                               ("grpc.max_send_message_length", 256 << 20)])
    pbg.add_InferenceServicer_to_server(S(), srv)
    srv.add_insecure_port(f"127.0.0.1:{port}")
    srv.start()
    print(f"[noop-grpc] :{port}", flush=True)
    srv.wait_for_termination()


def run_zmq(endpoint):
    import zmq, numpy as np
    ctx = zmq.Context(io_threads=1)
    sock = ctx.socket(zmq.REP)
    sock.bind(endpoint)
    print(f"[noop-zmq] {endpoint}", flush=True)
    while True:
        msg = sock.recv()
        n, cb = struct.unpack_from("<II", msg, 0)
        base = 8
        for i in range(n):
            _ = np.frombuffer(msg, dtype="<i2", count=cb // 2, offset=base + i * cb)
        sock.send(_resp(n))


def _recvn(c, n):
    b = bytearray()
    while len(b) < n:
        chunk = c.recv(n - len(b))
        if not chunk:
            raise EOFError
        b += chunk
    return bytes(b)


def run_uds(path):
    import numpy as np
    if os.path.exists(path):
        os.unlink(path)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(path); srv.listen(1)
    print(f"[noop-uds] {path}", flush=True)
    c, _ = srv.accept()
    c.setsockopt(socket.IPPROTO_TCP if False else socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
    while True:
        try:
            hdr = _recvn(c, 8)
        except EOFError:
            c, _ = srv.accept(); continue
        n, cb = struct.unpack("<II", hdr)
        payload = _recvn(c, n * cb)
        for i in range(n):
            _ = np.frombuffer(payload, dtype="<i2", count=cb // 2, offset=i * cb)
        c.sendall(_resp(n))


def run_shm(path):
    import numpy as np
    # pre-size the ring
    fd = os.open(SHM_PATH, os.O_CREAT | os.O_RDWR, 0o600)
    os.ftruncate(fd, SHM_SIZE)
    ring = mmap.mmap(fd, SHM_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
    if os.path.exists(path):
        os.unlink(path)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(path); srv.listen(1)
    print(f"[noop-shm] ctrl={path} ring={SHM_PATH}", flush=True)
    c, _ = srv.accept()
    while True:
        try:
            hdr = _recvn(c, 8)              # u32 N, u32 chunk_bytes  (data already in ring)
        except EOFError:
            c, _ = srv.accept(); continue
        n, cb = struct.unpack("<II", hdr)
        mv = memoryview(ring)
        for i in range(n):                  # zero-copy views straight over the shared pages
            _ = np.frombuffer(mv, dtype="<i2", count=cb // 2, offset=i * cb)
        c.sendall(_resp(n))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["grpc", "zmq", "uds", "shm"])
    ap.add_argument("--port", type=int, default=50071)
    ap.add_argument("--endpoint", default="ipc:///tmp/mtb_zmq")
    ap.add_argument("--uds", default="/tmp/mtb_uds.sock")
    args = ap.parse_args()
    if args.mode == "grpc":
        run_grpc(args.port)
    elif args.mode == "zmq":
        run_zmq(args.endpoint)
    elif args.mode == "uds":
        run_uds(args.uds)
    else:
        run_shm(args.uds)
