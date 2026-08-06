"""Official MMStar answer-extraction completion: when the rule-based can_infer fails (30%
of responses, concentrated in long-reasoning items), VLMEvalKit falls back to an LLM judge
to map the free-form answer to a choice. We do the same with a small LOCAL model (Qwen3),
recovering the unparseable cases. Final accuracy = rule-based hits + judge-recovered hits.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-model", default="Qwen/Qwen3-1.7B")
    ap.add_argument("--gpu-mem", type=float, default=0.12)
    args = ap.parse_args()
    from bench.gpu_probe import wait_for_window
    data = json.load(open("results/mmstar/mmstar_outputs.json"))
    rule_correct = sum(1 for d in data if d["rule_ext"] == d["gold"])
    unparsed = [d for d in data if d["rule_ext"] is None]
    print(f"[judge] {len(data)} total, rule-correct {rule_correct}, unparseable {len(unparsed)}",
          flush=True)
    def mkprompt(d):
        opts = "\n".join(f"{k}: {v}" for k, v in d["choices"].items())
        return ("A model answered a multiple-choice question. The model's answer was:\n"
                f"\"{d['response'][:900]}\"\n\nThe options were:\n{opts}\n\n"
                "Which option (A, B, C, or D) does the model's answer select? If the answer "
                "describes one option's content, choose that one. Reply with ONLY the single "
                "letter.")

    remote = "/" in args.judge_model      # e.g. openai/gpt-4o-mini via OpenRouter
    if remote:
        import concurrent.futures as cf
        from openai import OpenAI
        client = OpenAI(base_url="https://openrouter.ai/api/v1",
                        api_key=os.environ["OPENROUTER_API_KEY"])

        def judge_one(d):
            try:
                r = client.chat.completions.create(
                    model=args.judge_model, max_tokens=4, temperature=0,
                    messages=[{"role": "user", "content": mkprompt(d)}])
                return r.choices[0].message.content or ""
            except Exception:
                return ""
        with cf.ThreadPoolExecutor(max_workers=16) as ex:
            texts = list(ex.map(judge_one, unparsed))
    else:
        wait_for_window(need_free_gib=args.gpu_mem*97+2, max_util_pct=100, timeout_s=36000)
        from vllm import LLM, SamplingParams
        llm = LLM(args.judge_model, gpu_memory_utilization=args.gpu_mem, max_model_len=4096,
                  enforce_eager=True)
        outs = llm.generate([mkprompt(d) + " /no_think" for d in unparsed],
                            SamplingParams(max_tokens=8, temperature=0.0))
        texts = [o.outputs[0].text for o in outs]
    recovered = still_unparsed = 0
    for d, t in zip(unparsed, texts):
        m = re.search(r"[ABCD]", t.upper())
        judged = m.group(0) if m else None
        if judged is None:
            still_unparsed += 1
        if judged == d["gold"]:
            recovered += 1
    final = (rule_correct + recovered) / len(data)
    res = dict(n=len(data), rule_correct=rule_correct, unparseable=len(unparsed),
               judge_recovered=recovered, still_unparseable=still_unparsed,
               final_accuracy=round(final, 4), paper=0.640)
    json.dump(res, open("results/mmstar/mmstar_official_judged.json", "w"), indent=2)
    print(f"\n=== MMStar OFFICIAL (rule + LLM-judge), n={len(data)} ===")
    print(f"  rule-based correct : {rule_correct}/{len(data)} = {rule_correct/len(data):.3f}")
    print(f"  judge recovered    : {recovered}/{len(unparsed)} unparseable")
    print(f"  FINAL accuracy     : {final:.3f}   [paper = 0.640]")


if __name__ == "__main__":
    main()
