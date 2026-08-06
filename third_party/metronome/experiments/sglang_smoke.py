"""De-risk gate: can SGLang actually load + serve the 30B (Qwen3-Omni-MoE) WITH AUDIO on this GPU?
Also probes the streaming-session API. Run with ~/sglang-venv/bin/python. Polite to shared GPU."""
import os, sys, time
os.environ.setdefault("SGLANG_LOGGING_LEVEL", "warning")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from bench.gpu_probe import wait_for_window

MODEL = os.environ.get("SGL_MODEL", "sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic")


def main():
    import soundfile as sf
    from experiments.bench_spoken_qa import load_samples
    wait_for_window(need_free_gib=40, max_util_pct=80, timeout_s=7200)
    # real spoken question -> temp wav (SGLang load_audio takes a path/url/base64/bytes)
    s = load_samples("llama-questions", 1)[0]
    arr = np.asarray(s["audio"][0], dtype=np.float32); sr = int(s["audio"][1])
    wav = "/tmp/sgl_smoke.wav"; sf.write(wav, arr, sr)
    print(f"[smoke] question audio {len(arr)/sr:.1f}s @ {sr}Hz; ref Q={s.get('question','?')!r}", flush=True)

    from sglang import Engine
    t0 = time.time()
    eng = Engine(model_path=MODEL, trust_remote_code=True, attention_backend="fa3",
                 mem_fraction_static=0.80, enable_streaming_session=True,
                 disable_cuda_graph=False, log_level="warning")
    print(f"[smoke] SGLang Engine loaded in {time.time()-t0:.1f}s", flush=True)

    # Qwen3-Omni audio placeholders (same as vLLM path)
    ph = "<|audio_start|><|audio_pad|><|audio_end|>"
    prompt = ("<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
              f"<|im_start|>user\n{ph}<|im_end|>\n<|im_start|>assistant\n")
    sp = {"temperature": 0.0, "max_new_tokens": 40}

    # 1) plain audio generate (does SGLang serve qwen3-omni AUDIO at all?)
    t1 = time.time()
    out = eng.generate(prompt=prompt, audio_data=[wav], sampling_params=sp)
    txt = out["text"] if isinstance(out, dict) else out[0]["text"]
    print(f"[smoke] AUDIO generate {time.time()-t1:.2f}s -> {txt[:120]!r}", flush=True)

    # 2) streaming session: open, then two appended generates over resident KV
    try:
        sid = eng.open_session()
        print(f"[smoke] opened streaming session {sid}", flush=True)
        o1 = eng.generate(prompt=prompt, audio_data=[wav], sampling_params=sp,
                          session_params={"session_id": sid})
        print(f"[smoke] SESSION gen1 -> {(o1['text'] if isinstance(o1,dict) else o1[0]['text'])[:100]!r}", flush=True)
        print("[smoke] STREAMING SESSION OK", flush=True)
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"[smoke] streaming session FAILED: {e}", flush=True)
    print("[smoke] DONE", flush=True)


if __name__ == "__main__":
    main()
