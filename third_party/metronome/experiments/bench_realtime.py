"""Unified END-TO-END benchmark driven entirely through the Realtime API.

Stands up the Metronome OpenAI-Realtime server in-process on a real vLLM omni backend,
then connects as a WebSocket client and runs the real benchmarks through the API surface
— audio in (spoken QA / ASR), image in (VQA), or audio+image together. Nothing talks to
the engine directly; this is exactly the path a production developer would use.

Tasks (same client code, same scorer, swappable across the omni models):
  * spoken-qa : fixie-ai/llama-questions | fixie-ai/spoken-web-questions  -> inclusion acc
  * asr       : openslr/librispeech_asr (clean/test)                      -> WER
  * vqa       : lmms-lab/* (image + question)                            -> inclusion acc
  * av        : real audio + real image in one turn                       -> coherence

Reports accuracy/WER, real-time factor, and the Realtime server's own per-frame deadline
stats (metronome.tick), plus example traces so the output is auditable.
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

from bench.gpu_probe import wait_for_window
from bench.realtime_client import RealtimeClient
from experiments.bench_spoken_qa import normalize, correct, OMNI

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "realtime_bench")
INSTR = {"spoken-qa": "Answer the question spoken in the audio in a few words.",
         "asr": "Repeat the spoken words verbatim. Output ONLY the transcription itself — "
                "no preamble, no quotation marks, no commentary.",
         "vqa": None, "av": "What do you see and hear? Answer in one sentence."}


def vqa_match(pred: str, gold: str) -> bool:
    """Multiple-choice (MMStar): does the model's chosen letter match the gold letter?"""
    p = strip_think(pred).upper()
    g = (gold or "").strip().upper()
    m = _re.search(r"\b([A-D])\b", p)
    return bool(m and g and m.group(1) == g)

import re as _re
_ASR_PREAMBLE = _re.compile(
    r"^\s*(the\s+(original\s+)?(content|transcription|words|text)\s+(of\s+this\s+audio\s+)?"
    r"(is|are|says?)\s*[:\-]?\s*|here\s+is\s+the\s+transcription\s*[:\-]?\s*|"
    r"sure[,!]?\s*|transcription\s*[:\-]?\s*)", _re.I)


def strip_think(text: str) -> str:
    """Remove Qwen3-style <think>...</think> reasoning, keeping the final answer.
    Handles matched pairs, stray/mangled tags, and the '/no_think' empty-think prefix."""
    t = _re.sub(r"<think>.*?</think>", " ", text or "", flags=_re.S)   # matched pairs
    t = _re.sub(r"</?think>", " ", t)                                  # stray open/close
    t = _re.sub(r"^\s*p>\s*", "", t)                                   # mangled </think> remnant
    return t.strip()


def clean_asr(text: str) -> str:
    """Strip instruction-following preamble/quotes so verbatim ASR isn't penalized."""
    t = (text or "").strip()
    prev = None
    while prev != t:                       # peel nested preambles
        prev = t
        t = _ASR_PREAMBLE.sub("", t).strip()
    return t.strip().strip("'\"`").strip()


def wer(ref: str, hyp: str) -> float:
    r, h = normalize(ref).split(), normalize(hyp).split()
    if not r:
        return 0.0 if not h else 1.0
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev = cur
    return d[len(h)] / len(r)


def load_task(task, dataset, n):
    """Return list of dicts: {audio?, image?, question, golds, dur}."""
    from datasets import load_dataset, Audio
    import soundfile as sf
    rows = []
    if task in ("spoken-qa", "asr"):
        if task == "asr":
            ds = load_dataset("openslr/librispeech_asr", "clean", split="test",
                              streaming=True, trust_remote_code=True)
            af, txt = "audio", "text"
        else:
            repo = {"llama-questions": "fixie-ai/llama-questions",
                    "spoken-web-questions": "fixie-ai/spoken-web-questions"}[dataset]
            ds = load_dataset(repo, split="test", streaming=True)
            af, txt = "audio", ("answer" if dataset == "llama-questions" else "answers")
        ds = ds.cast_column("audio", Audio(decode=False))
        for row in ds:
            b = row["audio"]["bytes"]
            try:
                arr, sr = sf.read(io.BytesIO(b))
            except Exception:
                import librosa; arr, sr = librosa.load(io.BytesIO(b), sr=16000)
            if getattr(arr, "ndim", 1) > 1:
                arr = arr.mean(axis=1)
            g = row[txt]; golds = g if isinstance(g, list) else [g]
            rows.append(dict(audio=(arr.astype("float32"), int(sr)),
                             question=row.get("question", row.get("text", "")),
                             golds=golds, dur=len(arr) / float(sr)))
            if len(rows) >= n:
                break
    elif task == "vqa":
        ds = load_dataset("Lin-Chen/MMStar", split="val", streaming=True)
        for row in ds:
            rows.append(dict(image=row["image"].convert("RGB"),
                             question=row["question"] + "\nAnswer with the letter of the "
                             "correct option only (A, B, C, or D).",
                             golds=[row["answer"]], dur=0))
            if len(rows) >= n:
                break
    elif task == "av":
        from vllm.assets.audio import AudioAsset
        from vllm.assets.image import ImageAsset
        a, sr = AudioAsset("mary_had_lamb").audio_and_sample_rate
        rows.append(dict(audio=(a.astype("float32"), int(sr)),
                         image=ImageAsset("stop_sign").pil_image,
                         question="", golds=["stop", "lamb", "mary"],
                         dur=len(a) / float(sr)))
    return rows


async def run_one(uri, sample, task, modalities, sr_hint):
    cli = await RealtimeClient.connect(uri)
    try:
        await cli.configure(modalities=modalities,
                            input_sample_rate=(sample["audio"][1] if sample.get("audio") else sr_hint),
                            instructions=INSTR.get(task) or "")
        if sample.get("image") is not None:
            await cli.attach_image(sample["image"], text=sample.get("question") or INSTR.get(task))
        if sample.get("audio") is not None:
            await cli.append_audio(sample["audio"][0], sample["audio"][1])
            if INSTR.get(task):
                await cli.add_text(INSTR[task])
        r = await cli.respond(modalities=modalities)
        return r
    finally:
        await cli.close()


async def main_async(args):
    from metronome.backends.vllm_backend import VLLMBackend
    from metronome.realtime import RealtimeServer
    import websockets

    hf, _, default_mem = OMNI[args.model]
    gpu_mem = args.gpu_mem or default_mem
    print(f"[load] {hf} (gpu_mem={gpu_mem}) ...", flush=True)
    backend = VLLMBackend(hf, gpu_memory_utilization=gpu_mem, max_model_len=args.max_len,
                          trust_remote_code=True, enforce_eager=True,
                          limit_mm_per_prompt={"audio": 1, "image": 1})
    # ASR sentences run long; give responses room so they aren't truncated (short answers
    # still stop early on EOS).
    resp_max = 256 if args.task == "asr" else 96
    srv = RealtimeServer(backend, frame_budget_s=args.frame_budget, kv_budget_tokens=2048,
                         tokens_per_tick=args.tokens_per_tick, port=args.port,
                         capacity=max(8, args.concurrency * 2), response_max_tokens=resp_max)
    samples = load_task(args.task, args.dataset, args.n)
    print(f"[bench] task={args.task} dataset={args.dataset} n={len(samples)} "
          f"concurrency={args.concurrency}", flush=True)
    uri = f"ws://127.0.0.1:{args.port}"
    rows = []
    async with websockets.serve(srv.handle, "127.0.0.1", args.port,
                                ping_interval=None, max_size=64 * 2**20):
        floop = asyncio.create_task(srv.frame_loop())
        t_all = time.time()
        sem = asyncio.Semaphore(args.concurrency)

        async def worker(i, s):
            async with sem:
                try:
                    r = await run_one(uri, s, args.task, ["text"], 16000)
                except Exception as e:
                    return i, {"text": "", "latency_s": 0.0, "ticks": 0, "missed": 0,
                               "error": f"{type(e).__name__}: {str(e)[:120]}"}
                return i, r

        done = await asyncio.gather(*[worker(i, s) for i, s in enumerate(samples)])
        wall = time.time() - t_all
        floop.cancel()
    backend.shutdown()

    # score
    n_ok, wsum = 0, 0.0
    for i, r in done:
        s = samples[i]
        pred = r.get("text", "")
        if args.task == "asr":
            # ASR wants the verbatim transcript: drop reasoning + boilerplate.
            pred = clean_asr(strip_think(pred))
            w = wer(s["golds"][0], pred); wsum += w
            ok = w < 0.5
        elif args.task == "vqa":
            ok = vqa_match(pred, s["golds"][0])
        else:
            # spoken-QA: inclusion match on the FULL output (answer may be in reasoning)
            ok = correct(pred, s["golds"])
        n_ok += bool(ok)
        rtf = s["dur"] / max(r.get("latency_s", 1e-9), 1e-9) if s.get("dur") else None
        rows.append(dict(question=s.get("question", "")[:80], gold=s["golds"][:3],
                         pred=pred, ok=bool(ok),
                         audio_s=round(s.get("dur", 0), 1),
                         latency_s=round(r.get("latency_s", 0), 2),
                         rtf=round(rtf, 2) if rtf else None,
                         ticks=r.get("ticks", 0), missed=r.get("missed", 0),
                         error=r.get("error")))
    metric = (round(wsum / max(1, len(rows)), 3) if args.task == "asr"
              else round(n_ok / max(1, len(rows)), 3))
    res = dict(task=args.task, dataset=args.dataset, model=args.model, served_hf=hf,
               n=len(rows), via="realtime-api", concurrency=args.concurrency,
               metric=("WER" if args.task == "asr" else "accuracy"), score=metric,
               wall_s=round(wall, 1), traces=rows)
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, f"{args.model}__{args.task}__{args.dataset}.json")
    json.dump(res, open(fn, "w"), indent=2)
    print(f"\n=== {args.model} / {args.task} / {args.dataset} via Realtime API ===")
    print(f"  {res['metric']} = {metric}  (n={res['n']}, concurrency={args.concurrency}, "
          f"wall={res['wall_s']}s)")
    for r in rows[:6]:
        tag = "OK" if r["ok"] else "x"
        print(f"   [{tag}] gold={r['gold']} -> {r['pred'][:70]!r}"
              + (f"  ERR {r['error']}" if r.get("error") else ""))
    print(f"  saved {fn}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["spoken-qa", "asr", "vqa", "av"], default="spoken-qa")
    ap.add_argument("--dataset", default="llama-questions")
    ap.add_argument("--model", choices=list(OMNI), default="qwen-omni")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--gpu-mem", type=float, default=0.0)
    ap.add_argument("--need-free-gib", type=float, default=26.0)
    ap.add_argument("--max-util", type=int, default=98)
    ap.add_argument("--max-len", type=int, default=4096)
    ap.add_argument("--frame-budget", type=float, default=0.2)
    ap.add_argument("--tokens-per-tick", type=int, default=4)
    ap.add_argument("--port", type=int, default=8799)
    args = ap.parse_args()
    # The window guard must require at least what vLLM will actually request
    # (gpu_memory_utilization x total), or init fails after the guard passes.
    from bench.gpu_probe import query
    eff_mem = args.gpu_mem or OMNI[args.model][2]
    total_gib = query().mem_total_mib / 1024.0
    need = max(args.need_free_gib, eff_mem * total_gib + 1.5)
    print(f"=== Realtime-API benchmark: waiting for GPU window (>= {need:.0f} GiB) ===",
          flush=True)
    wait_for_window(need_free_gib=need, max_util_pct=args.max_util, timeout_s=36000)
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
