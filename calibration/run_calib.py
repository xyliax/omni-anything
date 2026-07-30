"""Driver: sweep T1-T4 grids, write CSVs + environment record."""
import argparse
import csv
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).parent))
from bench import Bench, stats, free_gib  # noqa: E402

OUT = Path(__file__).parent / "data"

T1_B = [1, 2, 4, 8, 16, 32]
T1_CTX = [1024, 4096, 8192, 16384]
T2_L = [64, 128, 256, 512, 1024, 2048, 4096, 8192]
T2_CTX = [0, 1024, 4096, 16384]
T3_P = [0, 64, 128, 256, 512, 1024, 2048]
T3_B = [4, 8, 16]
T3_CTX = [4096]
T4_K = [1, 2, 4, 8, 16, 32]
T4_CTX = [4096, 16384]
T4_L = 2048


def env_record(model, dev, dtype):
    def sh(c):
        try:
            return subprocess.run(c, shell=True, capture_output=True,
                                  text=True, timeout=20).stdout.strip()
        except Exception:
            return "n/a"
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "gpu_name": torch.cuda.get_device_name(dev),
        "gpu_index": dev,
        "gpu_count": torch.cuda.device_count(),
        "driver": sh("nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1"),
        "cuda_runtime": torch.version.cuda,
        "torch": torch.__version__,
        "transformers": __import__("transformers").__version__,
        "model": model,
        "dtype": str(dtype),
        "attn_impl": "sdpa",
        "python": platform.python_version(),
        "free_GiB_at_start": round(free_gib(dev), 2),
        "note": "SHARED GPU: other tenants present; GPU chosen for lowest contention. "
                "No CUDA graphs (HF eager loop) -> per-step Python overhead included.",
    }


def write_rows(name, rows):
    if not rows:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{name}.csv"
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[write] {p} ({len(rows)} rows)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--gpu", type=int, default=3)
    ap.add_argument("--iters", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=8)
    ap.add_argument("--tests", default="T1,T2,T3,T4")
    ap.add_argument("--tag", default="")
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    if args.quick:
        args.iters, args.warmup = 10, 3

    b = Bench(args.model, args.gpu)
    tag = args.tag or Path(args.model).name
    tests = args.tests.split(",")

    env = env_record(args.model, args.gpu, b.dtype)
    env["kv_KB_per_token"] = round(b.kv_kb_tok, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"env_{tag}.json").write_text(json.dumps(env, indent=2))
    print(json.dumps(env, indent=2), flush=True)

    # ---------------- T1
    if "T1" in tests:
        rows = []
        for ctx in T1_CTX:
            for B in T1_B:
                need = B * (ctx + args.iters + args.warmup + 8)
                if not b.fits(B, need):
                    print(f"[T1] SKIP B={B} ctx={ctx}: KV {need*b.kv_kb_tok/1024**2:.1f}GiB "
                          f"> free {free_gib(args.gpu):.1f}GiB", flush=True)
                    rows.append({"test": "T1", "model": tag, "B": B, "ctx": ctx,
                                 "feasible": 0, "kv_GiB_needed":
                                 round(need * b.kv_kb_tok / 1024**2, 2)})
                    continue
                try:
                    s = b.t1_decode(B, ctx, args.iters, args.warmup)
                except torch.cuda.OutOfMemoryError:
                    b.cleanup()
                    print(f"[T1] OOM B={B} ctx={ctx}", flush=True)
                    rows.append({"test": "T1", "model": tag, "B": B, "ctx": ctx,
                                 "feasible": 0, "kv_GiB_needed":
                                 round(need * b.kv_kb_tok / 1024**2, 2)})
                    continue
                r = {"test": "T1", "model": tag, "B": B, "ctx": ctx, "feasible": 1,
                     "kv_GiB_needed": round(need * b.kv_kb_tok / 1024**2, 2), **stats(s)}
                r["ms_per_token"] = round(r["p50_ms"] / B, 4)
                rows.append(r)
                print(f"[T1] B={B:>2} ctx={ctx:>5} p50={r['p50_ms']:.2f}ms "
                      f"({r['ms_per_token']:.2f}ms/tok)", flush=True)
        write_rows(f"T1_decode_{tag}", rows)

    # ---------------- T2
    if "T2" in tests:
        rows = []
        for ctx in T2_CTX:
            for L in T2_L:
                if not b.fits(1, ctx + L + 8):
                    continue
                try:
                    s = b.t2_prefill(L, ctx, max(10, args.iters // 2), args.warmup)
                except torch.cuda.OutOfMemoryError:
                    b.cleanup()
                    print(f"[T2] OOM L={L} ctx={ctx}", flush=True)
                    continue
                r = {"test": "T2", "model": tag, "L": L, "ctx": ctx, **stats(s)}
                r["ms_per_token"] = round(r["p50_ms"] / L, 4)
                r["tokens_per_s"] = round(L / (r["p50_ms"] / 1e3))
                rows.append(r)
                print(f"[T2] L={L:>5} ctx={ctx:>5} p50={r['p50_ms']:.2f}ms "
                      f"({r['ms_per_token']:.3f}ms/tok, {r['tokens_per_s']:,}tok/s)", flush=True)
        write_rows(f"T2_prefill_{tag}", rows)

    # ---------------- T3
    if "T3" in tests:
        rows = []
        for ctx in T3_CTX:
            for B in T3_B:
                base = None
                for p in T3_P:
                    rowsN = B + (1 if p else 0)
                    if not b.fits(rowsN, rowsN * (ctx + p + 8)):
                        continue
                    try:
                        s = b.t3_mixed(B, ctx, p, max(10, args.iters // 2), args.warmup)
                    except torch.cuda.OutOfMemoryError:
                        b.cleanup()
                        print(f"[T3] OOM B={B} p={p}", flush=True)
                        continue
                    st = stats(s)
                    if p == 0:
                        base = st["p50_ms"]
                    r = {"test": "T3", "model": tag, "B": B, "ctx": ctx, "p": p, **st}
                    r["base_ms"] = round(base, 4) if base else ""
                    r["overhead_ms"] = round(st["p50_ms"] - base, 4) if base else ""
                    r["overhead_pct"] = round(100 * (st["p50_ms"] / base - 1), 2) if base else ""
                    rows.append(r)
                    print(f"[T3] B={B:>2} p={p:>5} p50={st['p50_ms']:.2f}ms "
                          f"(+{r['overhead_pct']}%)", flush=True)
        write_rows(f"T3_mixed_{tag}", rows)

    # ---------------- T4
    if "T4" in tests:
        rows = []
        for ctx in T4_CTX:
            if not b.fits(1, ctx + T4_L + 8):
                continue
            base = None
            for k in T4_K:
                try:
                    s = b.t4_chunked(T4_L, k, ctx, max(10, args.iters // 3), max(3, args.warmup // 2))
                except torch.cuda.OutOfMemoryError:
                    b.cleanup()
                    continue
                st = stats(s)
                if k == 1:
                    base = st["p50_ms"]
                r = {"test": "T4", "model": tag, "L": T4_L, "k": k, "ctx": ctx,
                     "chunk": T4_L // k, **st}
                r["base_k1_ms"] = round(base, 4) if base else ""
                r["penalty_pct"] = round(100 * (st["p50_ms"] / base - 1), 2) if base else ""
                rows.append(r)
                print(f"[T4] ctx={ctx:>5} k={k:>2} (chunk={T4_L//k:>4}) "
                      f"p50={st['p50_ms']:.2f}ms penalty={r['penalty_pct']}%", flush=True)
        write_rows(f"T4_chunk_{tag}", rows)

    print("[done]", flush=True)


if __name__ == "__main__":
    main()
