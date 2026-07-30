"""Probe GPU timing stability under neighbour contention.

We need to know whether microbenchmark timings on a *shared* GPU are
trustworthy before spending hours on T1-T4. Runs a fixed-size matmul many
times and reports the spread. Low coefficient-of-variation => usable.
"""
import argparse
import json
import statistics
import time

import torch


def probe(dev: int, iters: int = 200, n: int = 4096) -> dict:
    torch.cuda.set_device(dev)
    a = torch.randn(n, n, device=f"cuda:{dev}", dtype=torch.float16)
    b = torch.randn(n, n, device=f"cuda:{dev}", dtype=torch.float16)

    for _ in range(30):  # warmup
        a @ b
    torch.cuda.synchronize(dev)

    samples = []
    for _ in range(iters):
        t0 = time.perf_counter()
        a @ b
        torch.cuda.synchronize(dev)
        samples.append((time.perf_counter() - t0) * 1e3)

    samples.sort()
    med = statistics.median(samples)
    free, total = torch.cuda.mem_get_info(dev)
    return {
        "gpu": dev,
        "name": torch.cuda.get_device_name(dev),
        "free_GiB": round(free / 2**30, 2),
        "total_GiB": round(total / 2**30, 2),
        "p50_ms": round(med, 3),
        "p90_ms": round(samples[int(0.90 * len(samples))], 3),
        "p99_ms": round(samples[int(0.99 * len(samples))], 3),
        "min_ms": round(samples[0], 3),
        "max_ms": round(samples[-1], 3),
        "cv_pct": round(100 * statistics.pstdev(samples) / med, 2),
        "p99_over_p50": round(samples[int(0.99 * len(samples))] / med, 3),
        # 4096^3 matmul = 2*n^3 FLOPs
        "tflops_at_p50": round(2 * n**3 / (med * 1e-3) / 1e12, 1),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpus", default="0,1,2,3")
    ap.add_argument("--iters", type=int, default=200)
    args = ap.parse_args()

    out = []
    for d in [int(x) for x in args.gpus.split(",")]:
        try:
            r = probe(d, args.iters)
        except Exception as e:  # OOM on a full card is informative, not fatal
            r = {"gpu": d, "error": repr(e)[:200]}
        out.append(r)
        print(json.dumps(r))
    print("\nSUMMARY (3090 clean fp16 peak ~ 71 TFLOPS dense, ~35 realistic):")
    for r in out:
        if "error" in r:
            print(f"  gpu{r['gpu']}: ERROR {r['error']}")
        else:
            print(
                f"  gpu{r['gpu']}: free={r['free_GiB']:.1f}GiB p50={r['p50_ms']:.2f}ms "
                f"cv={r['cv_pct']:.1f}% p99/p50={r['p99_over_p50']:.2f} "
                f"{r['tflops_at_p50']:.0f}TFLOPS"
            )
