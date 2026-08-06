"""Phase 1 — quality parity: does serving through Metronome change the output vs direct
inference? Three arms on the SAME samples through the SAME engine:

  A. direct      — one-shot offline prefill+greedy decode (generate_once)
  B. served-solo — periodic-session path (set_input + per-frame step_stream), 1 at a time
  C. served-bK   — K sessions served concurrently (batched step_stream) — the load condition

Reports each arm's benchmark score and paired token agreement (A vs B isolates the
streaming/framing; B vs C isolates batching-under-load). If A==B==C in score, serving is
quality-neutral; any gap is attributable and quantified.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

from bench.gpu_probe import wait_for_window
from experiments.bench_realtime import (load_task, vqa_match, strip_think, clean_asr,
                                         INSTR, wer)
from experiments.bench_spoken_qa import correct, OMNI


def score_one(task, pred, gold):
    if task == "asr":
        # same cleaning as the real ASR scorer: strip reasoning + "the content is:" preamble
        return 1.0 - min(1.0, wer(gold[0], clean_asr(strip_think(pred))))
    if task == "vqa":
        return float(vqa_match(pred, gold[0]))
    return float(correct(pred, gold))


def bootstrap_ci(deltas, iters=10000):
    """95% CI on the mean per-sample (served − direct) score delta, via paired bootstrap.
    Deterministic resampling (index hashing) since Math.random is unavailable; uses a fixed
    LCG so the CI is reproducible."""
    n = len(deltas)
    if n == 0:
        return (0.0, 0.0)
    means = []
    seed = 12345
    for _ in range(iters):
        s = 0.0
        for _ in range(n):
            seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
            s += deltas[seed % n]
        means.append(s / n)
    means.sort()
    lo = means[int(0.025 * iters)]
    hi = means[int(0.975 * iters)]
    return (round(lo, 4), round(hi, 4))


def agree(a, b):
    """token-list agreement: longest common prefix / max len."""
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n / max(1, max(len(a), len(b)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="spoken-qa")
    ap.add_argument("--dataset", default="llama-questions")
    ap.add_argument("--model", default="qwen-omni", choices=list(OMNI))
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--gpu-mem", type=float, default=0.30)
    ap.add_argument("--max-tokens", type=int, default=96)
    args = ap.parse_args()
    wait_for_window(need_free_gib=args.gpu_mem * 97 + 2, max_util_pct=100, timeout_s=36000)

    from metronome.backends.vllm_backend import VLLMBackend
    hf = OMNI[args.model][0]
    samples = load_task(args.task, args.dataset, args.n)
    be = VLLMBackend(hf, gpu_memory_utilization=args.gpu_mem, max_model_len=4096,
                     trust_remote_code=True, enforce_eager=True,
                     limit_mm_per_prompt={"audio": 1, "image": 1})
    instr = INSTR.get(args.task) or ""

    def mm(s):
        # VQA: the question is the real prompt. Audio tasks: the audio carries the
        # question/speech, so the text is the task instruction (NOT sample['question'],
        # which for ASR is the gold transcript and for spoken-QA duplicates the audio).
        text = s["question"] if s.get("image") else instr
        return dict(audio=s.get("audio"), images=[s["image"]] if s.get("image") else [],
                    text=text)

    # Arm A: direct one-shot
    A = [be.generate_once(max_tokens=args.max_tokens, **mm(s)) for s in samples]

    # Arm B: served solo (periodic-session, one at a time)
    B = []
    for i, s in enumerate(samples):
        sid = 10000 + i
        be.add_session(sid, 2048); be.set_input(sid, max_tokens=args.max_tokens, **mm(s))
        toks = []
        for _ in range(args.max_tokens + 5):
            be.step_stream([sid], 4)
            toks += be.last_outputs.get(sid, [])
            if be.is_finished(sid):
                break
        be.remove_session(sid); B.append(toks)

    # Arm C: served batched (K concurrent)
    C = [None] * len(samples)
    for start in range(0, len(samples), args.batch):
        grp = list(range(start, min(start + args.batch, len(samples))))
        for i in grp:
            sid = 20000 + i
            be.add_session(sid, 2048); be.set_input(sid, max_tokens=args.max_tokens, **mm(samples[i]))
        acc = {i: [] for i in grp}
        active = set(grp)
        for _ in range(args.max_tokens + 5):
            sids = [20000 + i for i in active]
            be.step_stream(sids, 4)
            for i in list(active):
                acc[i] += be.last_outputs.get(20000 + i, [])
                if be.is_finished(20000 + i):
                    active.discard(i)
            if not active:
                break
        for i in grp:
            C[i] = acc[i]; be.remove_session(20000 + i)

    # per-sample scores (so we can count correctness FLIPS, not just aggregate equality)
    N = len(samples)
    pA = [score_one(args.task, be.detokenize(A[i]), samples[i]["golds"]) for i in range(N)]
    pB = [score_one(args.task, be.detokenize(B[i]), samples[i]["golds"]) for i in range(N)]
    pC = [score_one(args.task, be.detokenize(C[i]), samples[i]["golds"]) for i in range(N)]
    sA, sB, sC = sum(pA) / N, sum(pB) / N, sum(pC) / N
    # a "flip" = the served arm changes this sample's score vs direct (threshold 1e-6 for WER)
    flips_solo = sum(1 for i in range(N) if abs(pA[i] - pB[i]) > 1e-6)
    flips_batch = sum(1 for i in range(N) if abs(pA[i] - pC[i]) > 1e-6)
    agAB = sum(agree(A[i], B[i]) for i in range(N)) / N
    agBC = sum(agree(B[i], C[i]) for i in range(N)) / N
    ci = bootstrap_ci([pC[i] - pA[i] for i in range(N)])     # CI on Δ(batched − direct)
    res = dict(model=args.model, task=args.task, dataset=args.dataset, n=N, batch=args.batch,
               score_direct=round(sA, 4), score_served_solo=round(sB, 4),
               score_served_batched=round(sC, 4),
               delta_batched_minus_direct=round(sC - sA, 4),
               delta_95ci=ci,
               flip_rate_solo=round(flips_solo / N, 4), flip_count_solo=flips_solo,
               flip_rate_batched=round(flips_batch / N, 4), flip_count_batched=flips_batch,
               token_agree_direct_vs_solo=round(agAB, 4),
               token_agree_solo_vs_batched=round(agBC, 4))
    os.makedirs("results/parity", exist_ok=True)
    json.dump(res, open(f"results/parity/{args.model}__{args.task}__{args.dataset}.json", "w"), indent=2)
    print("\n=== PARITY A/B ===")
    for k, v in res.items():
        print(f"  {k}: {v}")
    print(f"\n  Δ(served_solo − direct) = {sB - sA:+.4f}   "
          f"Δ(served_batched − direct) = {sC - sA:+.4f}")


if __name__ == "__main__":
    main()
