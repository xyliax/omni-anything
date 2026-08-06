"""Attribution: run MMStar on the HF REFERENCE Qwen2.5-Omni (transformers, the impl that
produced the paper's 64.0) with the SAME official prompt + can_infer extraction. If this
≈64% while vLLM gave ~40%, the remaining gap is vLLM's omni-vision serving path, not our
harness or Metronome's scheduling."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

from experiments.mmstar_official import parse_choices, can_infer


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    args = ap.parse_args()
    from bench.gpu_probe import wait_for_window
    wait_for_window(need_free_gib=28, max_util_pct=100, timeout_s=36000)

    import torch
    from datasets import load_dataset
    from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor

    model_id = "Qwen/Qwen2.5-Omni-7B"
    proc = Qwen2_5OmniProcessor.from_pretrained(model_id)
    model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
        model_id, torch_dtype=torch.bfloat16, device_map="cuda",
        attn_implementation="flash_attention_2").eval()

    ds = load_dataset("Lin-Chen/MMStar", split="val", streaming=True)
    rows = []
    for r in ds:
        rows.append((r["image"].convert("RGB"), r["question"], r["answer"].strip().upper()))
        if len(rows) >= args.n:
            break
    ok = miss = 0
    for img, q, gold in rows:
        choices, _ = parse_choices(q)
        conv = [{"role": "user", "content": [
            {"type": "image", "image": img},
            {"type": "text", "text": q + "\nPlease select the correct answer from the "
             "options above. "}]}]
        text = proc.apply_chat_template(conv, add_generation_prompt=True, tokenize=False)
        inputs = proc(text=text, images=[img], return_tensors="pt").to("cuda")
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=512, do_sample=False,
                                 return_audio=False)
        resp = proc.batch_decode(out[:, inputs["input_ids"].shape[1]:],
                                 skip_special_tokens=True)[0]
        ext = can_infer(resp, choices) if choices else False
        miss += (ext is False)
        ok += (ext == gold)
    print(f"\n=== MMStar HF-REFERENCE Qwen2.5-Omni (n={len(rows)}) ===")
    print(f"  accuracy (official prompt + can_infer): {ok/len(rows):.3f}")
    print(f"  unparseable: {miss}/{len(rows)}")
    print(f"  [vLLM-served gave 0.400; paper = 0.640]")


if __name__ == "__main__":
    main()
