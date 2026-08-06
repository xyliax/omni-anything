"""Full-dataset quality parity (C2 hardening): direct offline (ONE batched engine pass)
vs served-batched (periodic-session step_stream in groups of K), over the full/large test
set. Reports score per arm, per-sample correctness flips, and a paired bootstrap 95% CI on
the score delta — the publication-scale version of parity_ab."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

from bench.gpu_probe import wait_for_window
from experiments.bench_realtime import load_task, vqa_match, strip_think, clean_asr, INSTR, wer
from experiments.bench_spoken_qa import correct, OMNI
from experiments.parity_ab import bootstrap_ci, score_one


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="asr")
    ap.add_argument("--dataset", default="librispeech")
    ap.add_argument("--model", default="qwen-omni", choices=list(OMNI))
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--gpu-mem", type=float, default=0.30)
    ap.add_argument("--max-tokens", type=int, default=200)
    ap.add_argument("--max-len", type=int, default=4096)
    args = ap.parse_args()
    wait_for_window(need_free_gib=args.gpu_mem * 97 + 2, max_util_pct=100, timeout_s=36000)
    from metronome.backends.vllm_backend import VLLMBackend
    hf = OMNI[args.model][0]
    samples = load_task(args.task, args.dataset, args.n)
    N = len(samples)
    be = VLLMBackend(hf, gpu_memory_utilization=args.gpu_mem, max_model_len=args.max_len,
                     trust_remote_code=True, enforce_eager=True,
                     limit_mm_per_prompt={"audio": 1, "image": 1})
    instr = INSTR.get(args.task) or ""

    def mm(s):
        text = s["question"] if s.get("image") else instr
        return dict(audio=s.get("audio"), images=[s["image"]] if s.get("image") else [], text=text)

    print(f"[parity-full] {args.model} {args.task}/{args.dataset} N={N} batch={args.batch}", flush=True)
    # Arm A: direct offline, one batched pass
    A = be.generate_batch([mm(s) for s in samples], max_tokens=args.max_tokens)
    # Arm C: served-batched, groups of K
    C = [None] * N
    for start in range(0, N, args.batch):
        grp = list(range(start, min(start + args.batch, N)))
        for i in grp:
            be.add_session(20000 + i, 2048); be.set_input(20000 + i, max_tokens=args.max_tokens, **mm(samples[i]))
        acc = {i: [] for i in grp}; active = set(grp)
        for _ in range(args.max_tokens + 5):
            be.step_stream([20000 + i for i in active], 4)
            for i in list(active):
                acc[i] += be.last_outputs.get(20000 + i, [])
                if be.is_finished(20000 + i):
                    active.discard(i)
            if not active:
                break
        for i in grp:
            C[i] = acc[i]; be.remove_session(20000 + i)

    pA = [score_one(args.task, be.detokenize(A[i]), samples[i]["golds"]) for i in range(N)]
    pC = [score_one(args.task, be.detokenize(C[i]), samples[i]["golds"]) for i in range(N)]
    sA, sC = sum(pA) / N, sum(pC) / N
    flips = sum(1 for i in range(N) if abs(pA[i] - pC[i]) > 1e-6)
    ci = bootstrap_ci([pC[i] - pA[i] for i in range(N)])
    res = dict(model=args.model, task=args.task, dataset=args.dataset, n=N, batch=args.batch,
               score_direct=round(sA, 4), score_served_batched=round(sC, 4),
               delta=round(sC - sA, 4), delta_95ci=ci,
               flip_count=flips, flip_rate=round(flips / N, 4))
    os.makedirs("results/parity_full", exist_ok=True)
    json.dump(res, open(f"results/parity_full/{args.model}__{args.task}__{args.dataset}.json", "w"), indent=2)
    print(f"\n=== FULL PARITY {args.model}/{args.task}/{args.dataset} (N={N}) ===")
    for k, v in res.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
