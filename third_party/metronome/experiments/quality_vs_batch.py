"""Tier-1 experiment 3: does serving quality hold as the BATCH grows? We proved parity at
K=8-16; this sweeps the served batch size K and measures the correctness-flip rate vs the
direct reference at each K. If flips stay ~0 up to large K, capacity AND quality hold
together (the strong combined claim); if they rise, that's the honest boundary."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

from bench.gpu_probe import wait_for_window
from experiments.bench_realtime import load_task, INSTR
from experiments.bench_spoken_qa import OMNI
from experiments.parity_ab import score_one


def served_batched(be, samples, mm, K, max_tokens):
    N = len(samples)
    out = [None] * N
    for start in range(0, N, K):
        grp = list(range(start, min(start + K, N)))
        for i in grp:
            be.add_session(30000 + i, 2048); be.set_input(30000 + i, max_tokens=max_tokens, **mm(samples[i]))
        acc = {i: [] for i in grp}; active = set(grp)
        for _ in range(max_tokens + 5):
            be.step_stream([30000 + i for i in active], 4)
            for i in list(active):
                acc[i] += be.last_outputs.get(30000 + i, [])
                if be.is_finished(30000 + i):
                    active.discard(i)
            if not active:
                break
        for i in grp:
            out[i] = acc[i]; be.remove_session(30000 + i)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="spoken-qa")
    ap.add_argument("--dataset", default="llama-questions")
    ap.add_argument("--model", default="qwen-omni", choices=list(OMNI))
    ap.add_argument("--n", type=int, default=128)
    ap.add_argument("--batches", nargs="*", type=int, default=[1, 4, 8, 16, 32, 64, 128])
    ap.add_argument("--gpu-mem", type=float, default=0.35)
    ap.add_argument("--max-tokens", type=int, default=96)
    args = ap.parse_args()
    wait_for_window(need_free_gib=args.gpu_mem * 97 + 2, max_util_pct=100, timeout_s=36000)
    from metronome.backends.vllm_backend import VLLMBackend
    hf = OMNI[args.model][0]
    samples = load_task(args.task, args.dataset, args.n)
    N = len(samples)
    be = VLLMBackend(hf, gpu_memory_utilization=args.gpu_mem, max_model_len=4096,
                     trust_remote_code=True, enforce_eager=True,
                     limit_mm_per_prompt={"audio": 1, "image": 1})
    instr = INSTR.get(args.task) or ""

    def mm(s):
        return dict(audio=s.get("audio"), images=[s["image"]] if s.get("image") else [],
                    text=(s["question"] if s.get("image") else instr))

    # direct reference (one batched pass)
    A = be.generate_batch([mm(s) for s in samples], max_tokens=args.max_tokens)
    pA = [score_one(args.task, be.detokenize(A[i]), samples[i]["golds"]) for i in range(N)]
    rows = []
    for K in args.batches:
        C = served_batched(be, samples, mm, K, args.max_tokens)
        pC = [score_one(args.task, be.detokenize(C[i]), samples[i]["golds"]) for i in range(N)]
        flips = sum(1 for i in range(N) if abs(pA[i] - pC[i]) > 1e-6)
        rows.append(dict(batch=K, score=round(sum(pC) / N, 4), flips=flips,
                         flip_rate=round(flips / N, 4)))
        print(f"  K={K:3d}: score={rows[-1]['score']:.3f}  flips={flips}/{N}  "
              f"flip_rate={rows[-1]['flip_rate']:.3f}", flush=True)
    res = dict(model=args.model, task=args.task, dataset=args.dataset, n=N,
               direct_score=round(sum(pA) / N, 4), by_batch=rows)
    os.makedirs("results/quality_batch", exist_ok=True)
    json.dump(res, open(f"results/quality_batch/{args.model}__{args.task}.json", "w"), indent=2)
    print(f"\n=== quality vs batch ({args.model}/{args.task}, n={N}, direct={res['direct_score']}) ===")
    print("  flip_rate by K:", {r["batch"]: r["flip_rate"] for r in rows})


if __name__ == "__main__":
    main()
