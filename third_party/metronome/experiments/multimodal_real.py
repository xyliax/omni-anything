"""Real audio/vision benchmark — feed the actual multimodal interaction models REAL
audio and images and check they produce COHERENT output (not random) in real time.

Uses vLLM's bundled real test assets (an audio clip and an image) through the real
models, then reports: the model's actual output text, the processing latency, and the
real-time factor (audio duration / processing time). This validates correctness (the
serving stack produces sensible multimodal responses) and real-time capability.

  * audio  — Qwen2.5-Omni-7B: "what is said in this audio?" over a real speech clip.
  * vision — MiniCPM-o 4.5: "describe this image" over a real image.

Run after the GPU has room; each model loads, runs, and unloads in turn.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

from bench.gpu_probe import wait_for_window

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "multimodal")


def coherent(text: str) -> bool:
    """A crude coherence check: non-empty, has real words, not degenerate repetition."""
    t = (text or "").strip()
    if len(t) < 3:
        return False
    words = t.split()
    if len(words) >= 4 and len(set(words)) <= 2:   # degenerate repetition
        return False
    return any(c.isalpha() for c in t)


def run_audio(gpu_mem, max_len):
    from vllm import LLM, SamplingParams
    from vllm.assets.audio import AudioAsset
    arr, sr = AudioAsset("mary_had_lamb").audio_and_sample_rate
    dur = len(arr) / sr
    llm = LLM(model="Qwen/Qwen2.5-Omni-7B", trust_remote_code=True,
              max_model_len=max_len, gpu_memory_utilization=gpu_mem,
              enforce_eager=True, limit_mm_per_prompt={"audio": 1})
    prompt = ("<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
              "<|im_start|>user\n<|audio_bos|><|AUDIO|><|audio_eos|>"
              "What is said in this audio? Answer in one sentence.<|im_end|>\n"
              "<|im_start|>assistant\n")
    t0 = time.time()
    out = llm.generate({"prompt": prompt, "multi_modal_data": {"audio": [(arr, sr)]}},
                       SamplingParams(max_tokens=64, temperature=0.0))
    dt = time.time() - t0
    text = out[0].outputs[0].text.strip()
    del llm
    import torch; torch.cuda.empty_cache()
    return dict(modality="audio", model="Qwen/Qwen2.5-Omni-7B", input="mary_had_lamb (real speech)",
                audio_seconds=round(dur, 1), latency_s=round(dt, 2),
                realtime_factor=round(dur / max(dt, 1e-6), 2), output=text,
                coherent=coherent(text))


def run_vision(gpu_mem, max_len):
    from vllm import LLM, SamplingParams
    from vllm.assets.image import ImageAsset
    img = ImageAsset("stop_sign").pil_image
    llm = LLM(model="openbmb/MiniCPM-o-4_5", trust_remote_code=True,
              max_model_len=max_len, gpu_memory_utilization=gpu_mem,
              enforce_eager=True, limit_mm_per_prompt={"image": 1})
    prompt = ("<|im_start|>user\n(<image>./</image>)\nDescribe this image in one "
              "sentence.<|im_end|>\n<|im_start|>assistant\n")
    t0 = time.time()
    out = llm.generate({"prompt": prompt, "multi_modal_data": {"image": img}},
                       SamplingParams(max_tokens=64, temperature=0.0))
    dt = time.time() - t0
    text = out[0].outputs[0].text.strip()
    del llm
    import torch; torch.cuda.empty_cache()
    return dict(modality="vision", model="openbmb/MiniCPM-o-4_5", input="stop_sign (real image)",
                latency_s=round(dt, 2), output=text, coherent=coherent(text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", nargs="*", default=["audio", "vision"])
    ap.add_argument("--gpu-mem", type=float, default=0.30)
    ap.add_argument("--need-free-gib", type=float, default=24.0)
    ap.add_argument("--max-util", type=int, default=92)
    ap.add_argument("--max-len", type=int, default=4096)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    results = {}
    for which in args.which:
        print(f"\n=== REAL {which} benchmark (waiting for >= {args.need_free_gib} GiB) ===", flush=True)
        wait_for_window(need_free_gib=args.need_free_gib, max_util_pct=args.max_util, timeout_s=36000)
        try:
            r = run_audio(args.gpu_mem, args.max_len) if which == "audio" else \
                run_vision(args.gpu_mem, args.max_len)
            results[which] = r
            print(f"  model: {r['model']}", flush=True)
            print(f"  input: {r['input']}")
            if "realtime_factor" in r:
                print(f"  latency: {r['latency_s']}s for {r['audio_seconds']}s audio "
                      f"(real-time factor {r['realtime_factor']}x)")
            else:
                print(f"  latency: {r['latency_s']}s")
            print(f"  OUTPUT: {r['output']!r}")
            print(f"  coherent (not random): {r['coherent']}")
        except Exception as e:
            import traceback; traceback.print_exc()
            results[which] = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
        with open(os.path.join(OUT, "multimodal_real.json"), "w") as fh:
            json.dump(results, fh, indent=2)
    print("\n=== REAL MULTIMODAL SUMMARY ===")
    for k, r in results.items():
        if "output" in r:
            print(f"  {k}: coherent={r['coherent']}  output={r['output'][:80]!r}")
        else:
            print(f"  {k}: {r.get('error')}")


if __name__ == "__main__":
    main()
