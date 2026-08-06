"""Transcribe Moshi's FD-Bench output.wav files into the output.json (word-level
timestamps) the Full-Duplex-Bench evaluators consume. Uses openai-whisper word
timestamps (the official harness uses NeMo parakeet/CrisperWhisper; whisper gives the
same {text, chunks:[{text,timestamp:[s,e]}]} structure the evaluators read)."""
import argparse
import glob
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--audio-name", default="output.wav")
    ap.add_argument("--out-name", default="output.json")
    ap.add_argument("--model", default="base.en")
    args = ap.parse_args()

    wavs = sorted(glob.glob(os.path.join(args.root, "*", args.audio_name)))
    # Prefer faster-whisper on GPU (CTranslate2, ~10-50x faster); fall back to CPU whisper.
    fw = None
    try:
        from faster_whisper import WhisperModel
        import torch
        dev, ct = ("cuda", "float16") if torch.cuda.is_available() else ("cpu", "int8")
        fw = WhisperModel(args.model, device=dev, compute_type=ct)
        print(f"[transcribe] {len(wavs)} files via faster-whisper {args.model} on {dev}", flush=True)
    except Exception as e:
        import whisper
        cw = whisper.load_model(args.model, device="cpu")
        print(f"[transcribe] {len(wavs)} files via openai-whisper(cpu) — faster-whisper unavailable ({e})", flush=True)

    for i, w in enumerate(wavs):
        chunks, text = [], ""
        try:
            if fw is not None:
                segs, _ = fw.transcribe(w, word_timestamps=True, language="en")
                for seg in segs:
                    text += seg.text
                    for word in (seg.words or []):
                        chunks.append({"text": word.word,
                                       "timestamp": [round(word.start, 3), round(word.end, 3)]})
            else:
                r = cw.transcribe(w, word_timestamps=True, language="en")
                text = r.get("text", "")
                for seg in r.get("segments", []):
                    for word in seg.get("words", []):
                        chunks.append({"text": word["word"],
                                       "timestamp": [round(word["start"], 3), round(word["end"], 3)]})
        except Exception as e:
            print(f"  [{i}] {w}: ERR {type(e).__name__}: {str(e)[:80]}", flush=True)
        json.dump({"text": text, "chunks": chunks},
                  open(os.path.join(os.path.dirname(w), args.out_name), "w"), indent=2)
        if i % 20 == 0:
            print(f"  [{i}/{len(wavs)}] {len(chunks)} words", flush=True)
    print("[transcribe] done — output.json written", flush=True)


if __name__ == "__main__":
    main()
