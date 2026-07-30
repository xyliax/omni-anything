"""Drive T1-T4 against a real vLLM V0 engine and write CSVs."""
import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bench_vllm import VEngine, stats  # noqa: E402

OUT = Path(__file__).parent / "data"

T1_B = [1, 2, 4, 8, 16, 24, 32]
# ctx=2048 added: the KV pool caps B*ctx, so the larger batches the duplex
# workload needs are only reachable at moderate context.
T1_CTX = [1024, 2048, 4096, 8192, 16384]
# L=8..32 added: every duplex beat does an ~8-token micro-prefill, so that is
# the single most frequently evaluated cell in the simulation. Extrapolating it
# down from L=64 would put the error in the hottest path.
T2_L = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
T2_CTX = [0, 1024, 4096, 16384]
T3_P = [0, 64, 128, 256, 512, 1024, 2048]
T3_B = [4, 8, 16]
# ctx=2048 lets B=16 fit in the KV pool; ctx=4096 covers the larger-context
# case at B=4,8. Infeasible combinations are skipped by the KV guard.
# ctx=8192 added (feasible at B=4 only): duplex sessions accumulate context, so
# the simulator otherwise has to extrapolate the mixed-step toll past its data.
T3_CTX = [2048, 4096, 8192]
T4_K = [1, 2, 4, 8, 16, 32]
T4_CTX = [4096, 16384]
T4_L = 2048


def write_rows(name, rows):
    if not rows:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    p = OUT / f"{name}.csv"
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"[write] {p} ({len(rows)} rows)", flush=True)


def env_record(model, tag, ve):
    import torch

    def sh(c):
        try:
            return subprocess.run(c, shell=True, capture_output=True,
                                  text=True, timeout=20).stdout.strip()
        except Exception:
            return "n/a"
    import vllm
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "gpu_name": torch.cuda.get_device_name(0),
        "visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", "all"),
        "driver": sh("nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1"),
        "cuda_runtime": torch.version.cuda,
        "torch": torch.__version__,
        "vllm": vllm.__version__,
        "engine": "V0 LLMEngine (VLLM_USE_V1=0), CUDA graphs ON, paged attn",
        "transformers": __import__("transformers").__version__,
        "model": model,
        "tag": tag,
        "dtype": "float16",
        "python": platform.python_version(),
        "kv_tokens_available": ve.kv_tokens,
        "kv_KB_per_token": round(ve.kv_kb_tok, 1),
        "block_size": ve.block,
        "max_num_batched_tokens": ve.args["max_batched"],
        "gpu_memory_utilization": ve.args["util"],
        "note": "SHARED GPU (other tenants resident); GPU chosen for lowest "
                "contention. Decode steps are CUDA-graph replays, matching a "
                "production serving path.",
    }


# --------------------------------------------------------------------- T1
def t1(ve, iters, warmup, guard):
    rows = []
    # Global warmup: the first cell of a fresh engine reads high (measured
    # 12.29ms vs a stable 6.54ms for B=1/ctx=1k) because allocator and kernel
    # caches are still cold. Burn one throwaway cell before the grid.
    ve.drain()
    _wids = [ve.add(1024, 60, token_offset=12345) for _ in range(2)]
    for _ in range(40):
        if not ve.has_work():
            break
        ve.step_timed()
    ve.drain()

    for ctx in T1_CTX:
        for B in T1_B:
            need = B * (ctx + iters + warmup + 16)
            if need > ve.kv_tokens * guard or ctx > ve.args["max_len"]:
                rows.append({"test": "T1", "B": B, "ctx": ctx, "feasible": 0,
                             "kv_tokens_needed": need,
                             "kv_tokens_available": ve.kv_tokens,
                             "kv_GiB_needed": round(need * ve.kv_kb_tok / 1024**2, 2)})
                print(f"[T1] SKIP B={B} ctx={ctx}: needs {need} KV tokens "
                      f"> {ve.kv_tokens} available", flush=True)
                continue
            ve.drain()
            # generous max_tokens: if requests retire mid-window the batch
            # silently shrinks and the "B" label stops being true.
            ids = [ve.add(ctx, iters + warmup + 200, token_offset=90000 * (i + 1))
                   for i in range(B)]
            # run prefills out; a step is pure-decode once every request has
            # produced at least one token
            gen = {r: 0 for r in ids}
            steps = 0
            while steps < 2000:
                dt, outs = ve.step_timed()
                steps += 1
                for o in outs:
                    if o.outputs:
                        gen[o.request_id] = len(o.outputs[0].token_ids)
                if all(v >= 1 for v in gen.values()):
                    break
            # warmup decode steps
            for _ in range(warmup):
                ve.step_timed()
            samples = []
            for _ in range(iters):
                dt, outs = ve.step_timed()
                if not ve.has_work():
                    break
                samples.append(dt)
            ve.drain()
            if not samples:
                continue
            st = stats(samples)
            r = {"test": "T1", "B": B, "ctx": ctx, "feasible": 1,
                 "kv_tokens_needed": need, "kv_tokens_available": ve.kv_tokens,
                 "kv_GiB_needed": round(need * ve.kv_kb_tok / 1024**2, 2), **st}
            r["ms_per_token"] = round(st["p50_ms"] / B, 4)
            r["tokens_per_s"] = round(B / (st["p50_ms"] / 1e3), 1)
            rows.append(r)
            print(f"[T1] B={B:>2} ctx={ctx:>5} p50={st['p50_ms']:>7.2f}ms "
                  f"({r['ms_per_token']:>6.2f}ms/tok, {r['tokens_per_s']:>7.0f}tok/s)",
                  flush=True)
    write_rows(f"T1_decode_{ve.tag}", rows)
    return rows


# --------------------------------------------------------------------- T2
def t2(ve, iters, warmup, guard):
    """Prefill of L tokens on top of an existing ctx (prefix-cached)."""
    rows = []
    for ctx in T2_CTX:
        for L in T2_L:
            if ctx + L + 8 > ve.args["max_len"] or (ctx + L) > ve.kv_tokens * guard:
                continue
            ve.drain()
            prefix = []
            if ctx:
                # establish the prefix in the cache
                prefix = [(700000 + i) % 100000 + 1000 for i in range(ctx)]
                ve.add_shared_prefix(prefix, 0, 1)
                ve.drain()
            samples = []
            for it in range(warmup + iters):
                ve.add_shared_prefix(prefix, L, 1)
                # time only the steps that absorb this prefill
                tot = 0.0
                nsteps = 0
                while ve.has_work():
                    dt, outs = ve.step_timed()
                    nsteps += 1
                    done = any(o.finished for o in outs)
                    got = any(o.outputs and len(o.outputs[0].token_ids) >= 1
                              for o in outs)
                    tot += dt
                    if got or done:
                        break
                ve.drain()
                if it >= warmup:
                    samples.append(tot)
            if not samples:
                continue
            st = stats(samples)
            r = {"test": "T2", "L": L, "ctx": ctx, **st}
            r["ms_per_token"] = round(st["p50_ms"] / L, 4)
            r["tokens_per_s"] = round(L / (st["p50_ms"] / 1e3))
            rows.append(r)
            print(f"[T2] L={L:>5} ctx={ctx:>5} p50={st['p50_ms']:>8.2f}ms "
                  f"({r['ms_per_token']:.4f}ms/tok, {r['tokens_per_s']:,}tok/s)",
                  flush=True)
    write_rows(f"T2_prefill_{ve.tag}", rows)
    return rows


# --------------------------------------------------------------------- T3
def t3(ve, iters, warmup, guard):
    """B decode rows + p prefill tokens fused into ONE step.

    Finds the 'free ride' region: how many prefill tokens can share a decode
    step before the step time visibly grows.
    """
    rows = []
    for ctx in T3_CTX:
        for B in T3_B:
            need = B * (ctx + 64) + 2048
            if need > ve.kv_tokens * guard:
                print(f"[T3] SKIP B={B} ctx={ctx}: KV", flush=True)
                continue
            base = None
            for p in T3_P:
                ve.drain()
                ids = [ve.add(ctx, 400, token_offset=90000 * (i + 1))
                       for i in range(B)]
                gen = {r: 0 for r in ids}
                while True:
                    dt, outs = ve.step_timed()
                    for o in outs:
                        if o.outputs:
                            gen[o.request_id] = len(o.outputs[0].token_ids)
                    if all(v >= 1 for v in gen.values()):
                        break
                for _ in range(3):
                    ve.step_timed()
                samples = []
                for it in range(warmup + iters):
                    if p:
                        # inject a fresh prefill; next step fuses it with decode
                        ve.add(p, 1, token_offset=310000 + it * 977)
                        dt, outs = ve.step_timed()
                        if it >= warmup:
                            samples.append(dt)
                        # let the injected request finish so the next iteration
                        # measures a clean fused step again
                        for _ in range(3):
                            if ve.has_work():
                                ve.step_timed()
                    else:
                        dt, outs = ve.step_timed()
                        if it >= warmup:
                            samples.append(dt)
                ve.drain()
                if not samples:
                    continue
                st = stats(samples)
                if p == 0:
                    base = st["p50_ms"]
                r = {"test": "T3", "B": B, "ctx": ctx, "p": p, **st}
                r["base_ms"] = round(base, 4) if base else ""
                r["overhead_ms"] = round(st["p50_ms"] - base, 4) if base else ""
                r["overhead_pct"] = round(100 * (st["p50_ms"] / base - 1), 2) if base else ""
                r["ms_per_prefill_token"] = round(
                    (st["p50_ms"] - base) / p, 5) if (base and p) else ""
                rows.append(r)
                print(f"[T3] B={B:>2} ctx={ctx} p={p:>5} p50={st['p50_ms']:>7.2f}ms "
                      f"(+{r['overhead_pct']}%)", flush=True)
    write_rows(f"T3_mixed_{ve.tag}", rows)
    return rows


# --------------------------------------------------------------------- T4
def t4_one(model, tag, k, ctx, L, iters, warmup, util, max_len):
    """Separate engine per k: chunk size is set by max_num_batched_tokens."""
    chunk = max(1, L // k)
    ve = VEngine(model, max_batched=max(chunk, 1), max_len=max_len, util=util)
    ve.tag = tag
    prefix = [(700000 + i) % 100000 + 1000 for i in range(ctx)] if ctx else []
    if ctx:
        ve.add_shared_prefix(prefix, 0, 1)
        ve.drain()
    samples = []
    nsteps_seen = []
    for it in range(warmup + iters):
        ve.add_shared_prefix(prefix, L, 1)
        tot, nst = 0.0, 0
        while ve.has_work():
            dt, outs = ve.step_timed()
            tot += dt
            nst += 1
            if any(o.outputs and len(o.outputs[0].token_ids) >= 1 for o in outs):
                break
        ve.drain()
        if it >= warmup:
            samples.append(tot)
            nsteps_seen.append(nst)
    st = stats(samples)
    kv = ve.kv_tokens
    ve.shutdown()
    return st, (statistics_mean(nsteps_seen) if nsteps_seen else 0), kv


def statistics_mean(xs):
    return round(sum(xs) / len(xs), 2) if xs else 0


def t4(model, tag, iters, warmup, util, max_len):
    rows = []
    for ctx in T4_CTX:
        if ctx + T4_L + 8 > max_len:
            print(f"[T4] SKIP ctx={ctx}: exceeds max_model_len={max_len}", flush=True)
            continue
        base = None
        for k in T4_K:
            try:
                st, nst, kv = t4_one(model, tag, k, ctx, T4_L, iters, warmup,
                                     util, max_len)
            except Exception as e:
                print(f"[T4] ERR ctx={ctx} k={k}: {type(e).__name__} {str(e)[:120]}",
                      flush=True)
                continue
            if not st:
                continue
            if k == 1:
                base = st["p50_ms"]
            r = {"test": "T4", "L": T4_L, "k": k, "ctx": ctx,
                 "chunk": T4_L // k, "steps_observed": nst, **st}
            r["base_k1_ms"] = round(base, 4) if base else ""
            r["penalty_pct"] = round(100 * (st["p50_ms"] / base - 1), 2) if base else ""
            r["penalty_ms"] = round(st["p50_ms"] - base, 3) if base else ""
            rows.append(r)
            print(f"[T4] ctx={ctx:>5} k={k:>2} chunk={T4_L//k:>4} "
                  f"p50={st['p50_ms']:>8.2f}ms steps={nst:>5} "
                  f"penalty={r['penalty_pct']}%", flush=True)
    write_rows(f"T4_chunk_{tag}", rows)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", default="")
    ap.add_argument("--iters", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=8)
    ap.add_argument("--tests", default="T1,T2,T3,T4")
    ap.add_argument("--util", type=float, default=0.34)
    ap.add_argument("--max-len", type=int, default=8192)
    ap.add_argument("--max-batched", type=int, default=2048)
    ap.add_argument("--kv-guard", type=float, default=0.85,
                    help="fraction of KV pool we allow a cell to request")
    args = ap.parse_args()
    tag = args.tag or Path(args.model.rstrip("/")).name
    tests = args.tests.split(",")

    need_engine = any(t in tests for t in ("T1", "T2", "T3"))
    if need_engine:
        ve = VEngine(args.model, max_batched=args.max_batched,
                     max_len=args.max_len, util=args.util)
        ve.tag = tag
        OUT.mkdir(parents=True, exist_ok=True)
        env = env_record(args.model, tag, ve)
        (OUT / f"env_{tag}.json").write_text(json.dumps(env, indent=2))
        print(json.dumps(env, indent=2), flush=True)
        if "T1" in tests:
            t1(ve, args.iters, args.warmup, args.kv_guard)
        if "T2" in tests:
            t2(ve, max(10, args.iters // 2), max(3, args.warmup // 2), args.kv_guard)
        if "T3" in tests:
            t3(ve, max(10, args.iters // 2), max(3, args.warmup // 2), args.kv_guard)
        ve.shutdown()
    if "T4" in tests:
        t4(args.model, tag, max(8, args.iters // 4), 2, args.util, args.max_len)
    print("[done]", flush=True)


if __name__ == "__main__":
    main()
