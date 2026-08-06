"""Validate (c): MiniCPM-o's NATIVE streaming encoder gives incremental (flat) per-frame encode
cost, vs re-encoding the growing window. Uses the model's own get_audio_embedding_streaming (apm
encoder KV cache, bs=1) — the path streaming_prefill uses internally."""
import os, sys, time, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, soundfile as sf, torch


def load_audio(seconds, sr=16000):
    fs = sorted(glob.glob(os.path.expanduser("~/data/LibriSpeech/test-clean/*/*/*.flac")))
    arrs, i = [], 0
    while sum(len(x) for x in arrs) < seconds * sr:
        a, sr = sf.read(fs[i % len(fs)]); arrs.append(a.astype("float32")); i += 1
    return np.concatenate(arrs)[: int(seconds * sr)], sr


def main():
    # MiniCPM-o-2.6's remote code was written for transformers ~4.44; bridge the removed
    # WHISPER_ATTENTION_CLASSES symbol to the unified WhisperAttention in 4.57.
    import transformers.models.whisper.modeling_whisper as _w
    if not hasattr(_w, "WHISPER_ATTENTION_CLASSES"):
        _w.WHISPER_ATTENTION_CLASSES = {"eager": _w.WhisperAttention, "sdpa": _w.WhisperAttention,
                                        "flash_attention_2": _w.WhisperAttention}
    from transformers import DynamicCache as _DC
    if not hasattr(_DC, "get_usable_length"):
        _DC.get_usable_length = lambda self, new_len=0, layer_idx=0: self.get_seq_length(layer_idx)
    from transformers import AutoModel, AutoProcessor
    mid = os.environ.get("MCPM_MODEL", "openbmb/MiniCPM-o-4_5")
    print(f"loading {mid} ...", flush=True)
    proc = AutoProcessor.from_pretrained(mid, trust_remote_code=True)
    model = AutoModel.from_pretrained(mid, trust_remote_code=True, attn_implementation="sdpa",
                                      torch_dtype=torch.bfloat16, init_vision=False, init_tts=False)
    model = model.eval().cuda()
    dt = next(model.apm.parameters()).dtype

    audio, sr = load_audio(16)
    blk = int(2.0 * sr); nblk = len(audio) // blk

    def feats(a):
        # the model's own audio feature path -> ([1,80,frames], [tensor([len])], parts)
        af, lens, _ = proc.audio_feature_extract(a.astype("float32"), sampling_rate=sr)
        return af.to("cuda", dt), [l.to("cuda") for l in lens]

    # ---- INCREMENTAL: streaming encoder KV cache, encode only the new 2s block each frame ----
    model.audio_past_key_values = None
    inc = []
    with torch.no_grad():
        for b in range(nblk):
            f, lens = feats(audio[b * blk:(b + 1) * blk])
            torch.cuda.synchronize(); t0 = time.perf_counter()
            _ = model.get_audio_embedding_streaming({"audio_features": f, "audio_feature_lens": lens})
            torch.cuda.synchronize(); inc.append((time.perf_counter() - t0) * 1000)

    # ---- RE-ENCODE: full encode of the growing window each frame (the old fd_step cost) ----
    re = []
    with torch.no_grad():
        for b in range(1, nblk + 1):
            f, lens = feats(audio[: b * blk])
            model.audio_past_key_values = None
            torch.cuda.synchronize(); t0 = time.perf_counter()
            _ = model.get_audio_embedding_streaming({"audio_features": f, "audio_feature_lens": lens})
            torch.cuda.synchronize(); re.append((time.perf_counter() - t0) * 1000)

    print(f"\nMiniCPM-o incremental encode (KV cache, per 2s block): {[f'{x:.1f}' for x in inc]} ms  (FLAT)")
    print(f"MiniCPM-o re-encode whole window each frame:          {[f'{x:.1f}' for x in re]} ms  (GROWS)")
    print(f"\nSUMMARY: incremental flat ~{np.median(inc):.1f}ms vs re-encode {re[0]:.1f}ms@2s -> "
          f"{re[-1]:.1f}ms@{nblk*2}s  (speedup {re[-1]/np.median(inc):.1f}x at {nblk*2}s context)")


if __name__ == "__main__":
    main()
