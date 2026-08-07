"""E0: DMA-decode interference microbenchmark (docs/experiments.md E0, go/no-go).

The conveyor moves tail KV over PCIe H2D *while* decode steps run. The one
parameter no existing calibration can predict: does a sustained pinned-H2D
copy on a side CUDA stream inflate decode step time (copy engine stealing
HBM bandwidth), and does compute in turn degrade achieved copy bandwidth?

Method
  - Decode steps exactly as T1 (StaticCache, chunked KV fill, B x ctx cells).
  - Copier thread: dedicated cuda.Stream, pinned host buffer -> device buffer,
    paced to a fraction r of the unloaded link bandwidth (copy one chunk,
    sleep (1-r)/r * t_chunk). Counts bytes actually moved per window.
  - Decode timing uses CUDA events on the compute stream, NOT device-wide
    synchronize: device sync would wait for in-flight copy chunks and book
    copy-drain time as decode time (false interference).

Outputs
  kappa(r)  = decode p50 with copier at rate r / decode p50 at r=0
  bw_eff(r) = bytes moved / window during concurrent decode
  -> calibration/data/E0_dma_interference.{csv,json}

Go/no-go (docs/experiments.md E0): conveyor needs ~0.5-0.7 of link; if kappa
at that rate > 1.15, recompute net gain with measured kappa before building.
"""
import argparse
import csv
import json
import threading
import time
from pathlib import Path

import torch
from transformers import AutoConfig, AutoModelForCausalLM
from transformers.cache_utils import StaticCache

FILL_CHUNK = 2048
COPY_CHUNK_MB = 64  # pcie_h2d_bench: 64MB-1GB flat, 64MB = ~5ms pacing grain


class Copier:
    """Paced H2D copier on its own stream. rate=fraction of unloaded BW."""

    def __init__(self, dev, chunk_mb=COPY_CHUNK_MB):
        self.dev = dev
        self.stream = torch.cuda.Stream(device=dev)
        n = chunk_mb * 2**20
        self.host = torch.empty(n, dtype=torch.uint8, pin_memory=True)
        self.dst = torch.empty(n, dtype=torch.uint8, device=f"cuda:{dev}")
        self.bytes_moved = 0
        self._stop = threading.Event()
        self._thr = None

    def unloaded_bw(self, iters=20):
        """GB/s of the bare link (no compute running)."""
        with torch.cuda.stream(self.stream):
            for _ in range(3):
                self.dst.copy_(self.host, non_blocking=True)
        self.stream.synchronize()
        t0 = time.perf_counter()
        with torch.cuda.stream(self.stream):
            for _ in range(iters):
                self.dst.copy_(self.host, non_blocking=True)
        self.stream.synchronize()
        dt = time.perf_counter() - t0
        return self.host.numel() * iters / dt / 1e9

    def _run(self, t_chunk_s, rate):
        idle = t_chunk_s * (1.0 - rate) / rate if rate < 1.0 else 0.0
        while not self._stop.is_set():
            with torch.cuda.stream(self.stream):
                self.dst.copy_(self.host, non_blocking=True)
            self.stream.synchronize()   # releases GIL; paces by real copy time
            self.bytes_moved += self.host.numel()
            if idle:
                time.sleep(idle)

    def start(self, rate, bw0_gbs):
        self.bytes_moved = 0
        self._stop.clear()
        t_chunk = self.host.numel() / (bw0_gbs * 1e9)
        self._thr = threading.Thread(target=self._run, args=(t_chunk, rate), daemon=True)
        self._thr.start()

    def stop(self):
        self._stop.set()
        if self._thr:
            self._thr.join()
        self.stream.synchronize()


def event_timed_decode(model, cache, cfg, dev, ctx_start, iters, warmup):
    """Per-iter decode latency via CUDA events on the compute stream."""
    ids = torch.randint(0, cfg.vocab_size, (cache.max_batch_size, 1), device=f"cuda:{dev}")
    i = ctx_start
    out = []
    for k in range(warmup + iters):
        pos = torch.tensor([i], device=f"cuda:{dev}")
        e0 = torch.cuda.Event(enable_timing=True)
        e1 = torch.cuda.Event(enable_timing=True)
        e0.record()
        with torch.inference_mode():
            model(input_ids=ids, past_key_values=cache, cache_position=pos, use_cache=True)
        e1.record()
        e1.synchronize()
        if k >= warmup:
            out.append(e0.elapsed_time(e1))
        i += 1
    return out, i


def p50(xs):
    s = sorted(xs)
    return s[len(s) // 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3-1.7B")
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--iters", type=int, default=50)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--cells", default="1x4096,8x4096,8x16384,16x8192")
    ap.add_argument("--rates", default="0,0.25,0.5,0.75,1.0")
    ap.add_argument("--out", default=str(Path(__file__).parent / "data" / "E0_dma_interference"))
    args = ap.parse_args()

    dev = args.device
    torch.cuda.set_device(dev)
    cfg = AutoConfig.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.float16, attn_implementation="sdpa",
    ).to(f"cuda:{dev}").eval()

    copier = Copier(dev)
    bw0 = copier.unloaded_bw()
    print(f"[link] unloaded pinned H2D = {bw0:.2f} GB/s", flush=True)

    rows = []
    for cell in args.cells.split(","):
        B, ctx = (int(x) for x in cell.split("x"))
        need_iters = args.warmup + args.iters
        cache = StaticCache(config=cfg, max_batch_size=B,
                            max_cache_len=ctx + need_iters * len(args.rates.split(",")) + 8,
                            device=f"cuda:{dev}", dtype=torch.float16)
        done = 0
        while done < ctx:  # chunked prefill to populate KV (timing-exact, see bench.py)
            n = min(FILL_CHUNK, ctx - done)
            ids = torch.randint(0, cfg.vocab_size, (B, n), device=f"cuda:{dev}")
            pos = torch.arange(done, done + n, device=f"cuda:{dev}")
            with torch.inference_mode():
                model(input_ids=ids, past_key_values=cache, cache_position=pos,
                      use_cache=True, logits_to_keep=1)
            done += n
        torch.cuda.synchronize(dev)

        pos_cursor = ctx
        base_p50 = None
        for r in (float(x) for x in args.rates.split(",")):
            if r > 0:
                copier.start(r, bw0)
            t0 = time.perf_counter()
            lats, pos_cursor = event_timed_decode(
                model, cache, cfg, dev, pos_cursor, args.iters, args.warmup)
            window = time.perf_counter() - t0
            if r > 0:
                copier.stop()
                bw_eff = copier.bytes_moved / window / 1e9
            else:
                bw_eff = 0.0
            m = p50(lats)
            if r == 0:
                base_p50 = m
            kappa = m / base_p50 if base_p50 else float("nan")
            rows.append({"B": B, "ctx": ctx, "rate": r, "decode_p50_ms": round(m, 4),
                         "decode_p99_ms": round(sorted(lats)[int(0.99 * (len(lats) - 1))], 4),
                         "kappa": round(kappa, 4), "bw_eff_gbs": round(bw_eff, 3),
                         "bw_target_gbs": round(r * bw0, 3), "iters": len(lats)})
            print(f"[cell B={B} ctx={ctx}] r={r:.2f} decode p50={m:.3f}ms "
                  f"kappa={kappa:.3f} bw_eff={bw_eff:.2f}/{r * bw0:.2f} GB/s", flush=True)
        del cache
        torch.cuda.empty_cache()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    mid = [x["kappa"] for x in rows if 0 < x["rate"] <= 0.75]
    summary = {"model": args.model, "device": torch.cuda.get_device_name(dev),
               "unloaded_h2d_gbs": round(bw0, 3),
               "max_kappa_at_r<=0.75": max(mid) if mid else None,
               "max_kappa_any": max((x["kappa"] for x in rows if x["rate"] > 0), default=None),
               "rows": len(rows)}
    with open(f"{out}.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
