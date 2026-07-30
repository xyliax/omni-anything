"""Fitted-curve figures for T1-T4."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

D = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "figures"
OUT.mkdir(exist_ok=True)
TAG = "Qwen3-1.7B"
BEAT = 480.0


def load(name):
    p = D / name
    return list(csv.DictReader(open(p))) if p.exists() else []


def f(r, k):
    try:
        return float(r[k])
    except (KeyError, ValueError, TypeError):
        return None


# ------------------------------------------------------------------ T1
rows = [r for r in load(f"T1_decode_{TAG}.csv") if r.get("feasible") == "1"]
if rows:
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    ctxs = sorted({int(r["ctx"]) for r in rows})
    for c in ctxs:
        pts = sorted((int(r["B"]), f(r, "p50_ms")) for r in rows if int(r["ctx"]) == c)
        ax[0].plot([p[0] for p in pts], [p[1] for p in pts], "o-", label=f"ctx={c//1024}k")
    ax[0].set_xlabel("decode batch size B")
    ax[0].set_ylabel("step time (ms, p50)")
    ax[0].set_title(f"T1 decode step time — {TAG}\n(vLLM V0, CUDA graphs, fp16)")
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3)
    for c in ctxs:
        pts = sorted((int(r["B"]), f(r, "ms_per_token")) for r in rows if int(r["ctx"]) == c)
        ax[1].plot([p[0] for p in pts], [p[1] for p in pts], "s-", label=f"ctx={c//1024}k")
    ax[1].set_xlabel("decode batch size B")
    ax[1].set_ylabel("ms per output token")
    ax[1].set_title("T1 per-token cost: batching pays off\n(but KV pool caps B x ctx)")
    ax[1].set_yscale("log")
    ax[1].legend(fontsize=8)
    ax[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / "T1_decode.png", dpi=130)
    plt.close()

    # feasibility frontier
    allr = load(f"T1_decode_{TAG}.csv")
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    okB = [int(r["B"]) for r in allr if r["feasible"] == "1"]
    okC = [int(r["ctx"]) for r in allr if r["feasible"] == "1"]
    noB = [int(r["B"]) for r in allr if r["feasible"] == "0"]
    noC = [int(r["ctx"]) for r in allr if r["feasible"] == "0"]
    ax.scatter(okB, okC, c="tab:green", s=70, label="measurable")
    ax.scatter(noB, noC, c="tab:red", marker="x", s=70, label="KV pool exceeded")
    kv = 44336
    bs = list(range(1, 33))
    ax.plot(bs, [kv / b for b in bs], "k--", label=f"B x ctx = {kv//1000}k tokens")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("sessions / batch size B")
    ax.set_ylabel("context length (tokens)")
    ax.set_title("Session density is KV-capacity bound\n(1.7B model, 8.5GiB budget on a shared 3090)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, which="both")
    plt.tight_layout()
    plt.savefig(OUT / "T1_feasibility.png", dpi=130)
    plt.close()

# ------------------------------------------------------------------ T2
rows = load(f"T2_prefill_{TAG}.csv")
if rows:
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for c in sorted({int(r["ctx"]) for r in rows}):
        pts = sorted((int(r["L"]), f(r, "p50_ms")) for r in rows if int(r["ctx"]) == c)
        ax[0].plot([p[0] for p in pts], [p[1] for p in pts], "o-", label=f"ctx={c}")
    ax[0].axhline(BEAT, color="r", ls="--", label="480ms beat deadline")
    ax[0].set_xscale("log")
    ax[0].set_yscale("log")
    ax[0].set_xlabel("prefill length L (tokens)")
    ax[0].set_ylabel("prefill time (ms)")
    ax[0].set_title("T2 prefill cost vs L\nL>=4096 alone exceeds one beat")
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3, which="both")
    for c in sorted({int(r["ctx"]) for r in rows}):
        pts = sorted((int(r["L"]), f(r, "ms_per_token")) for r in rows if int(r["ctx"]) == c)
        ax[1].plot([p[0] for p in pts], [p[1] for p in pts], "s-", label=f"ctx={c}")
    ax[1].set_xscale("log")
    ax[1].set_xlabel("prefill length L")
    ax[1].set_ylabel("ms per prefill token")
    ax[1].set_title("Per-token prefill cost rises with existing context\n(prefix re-read)")
    ax[1].legend(fontsize=8)
    ax[1].grid(alpha=0.3, which="both")
    plt.tight_layout()
    plt.savefig(OUT / "T2_prefill.png", dpi=130)
    plt.close()

# ------------------------------------------------------------------ T3
rows = load(f"T3_mixed_{TAG}.csv")
if rows:
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for (B, c) in sorted({(int(r["B"]), int(r["ctx"])) for r in rows}):
        pts = sorted((int(r["p"]), f(r, "p50_ms")) for r in rows
                     if int(r["B"]) == B and int(r["ctx"]) == c)
        ax[0].plot([p[0] for p in pts], [p[1] for p in pts], "o-",
                   label=f"B={B} ctx={c}")
    ax[0].set_xlabel("prefill tokens p fused into the decode step")
    ax[0].set_ylabel("step time (ms)")
    ax[0].set_title("T3 mixed-batch step time\nflat 64->512 = entry toll, not a ramp")
    ax[0].legend(fontsize=7)
    ax[0].grid(alpha=0.3)
    for (B, c) in sorted({(int(r["B"]), int(r["ctx"])) for r in rows}):
        pts = sorted((int(r["p"]), f(r, "overhead_pct")) for r in rows
                     if int(r["B"]) == B and int(r["ctx"]) == c and f(r, "overhead_pct") is not None)
        if pts:
            ax[1].plot([p[0] for p in pts], [p[1] for p in pts], "s-",
                       label=f"B={B} ctx={c}")
    ax[1].set_xlabel("prefill tokens p")
    ax[1].set_ylabel("step-time overhead vs pure decode (%)")
    ax[1].set_title("There is no free ride: p=64 already costs +70-160%")
    ax[1].legend(fontsize=7)
    ax[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / "T3_mixed.png", dpi=130)
    plt.close()

# ------------------------------------------------------------------ T4
rows = load(f"T4_chunk_{TAG}.csv") + load(f"T4_chunk_{TAG}-ctx16k.csv")
if rows:
    seen = {}
    for r in rows:
        seen[(int(r["ctx"]), int(r["k"]))] = r
    rows = list(seen.values())
    fig, ax = plt.subplots(1, 3, figsize=(17, 4.5))
    for c in sorted({int(r["ctx"]) for r in rows}):
        pts = sorted((int(r["k"]), f(r, "p50_ms")) for r in rows if int(r["ctx"]) == c)
        ax[0].plot([p[0] for p in pts], [p[1] for p in pts], "o-", label=f"ctx={c}")
    ax[0].axhline(BEAT, color="r", ls="--", label="480ms beat")
    ax[0].set_xscale("log", base=2)
    ax[0].set_xlabel("number of chunks k (L=2048 total)")
    ax[0].set_ylabel("total prefill time (ms)")
    ax[0].set_title("T4 chunking penalty (L=2048)")
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3)
    for c in sorted({int(r["ctx"]) for r in rows}):
        pts = sorted((int(r["k"]), f(r, "penalty_pct")) for r in rows
                     if int(r["ctx"]) == c and f(r, "penalty_pct") is not None)
        ax[1].plot([p[0] for p in pts], [p[1] for p in pts], "s-", label=f"ctx={c}")
    ax[1].set_xscale("log", base=2)
    ax[1].set_xlabel("number of chunks k")
    ax[1].set_ylabel("penalty vs k=1 (%)")
    # The relative curve is the misleading view: it looks flat/better at 16k
    # only because the k=1 baseline is larger there (270ms vs 158ms). The
    # marginal cost per extra step is what actually grows with context --
    # 13.1 ms/step at ctx=4k vs 20.9 ms/step at ctx=16k (+59%).
    ax[1].set_title("Relative penalty is the misleading view\n"
                    "(flat at ctx=16k only because its k=1 baseline is larger)")
    ax[1].legend(fontsize=8)
    ax[1].grid(alpha=0.3)

    # Panel 3: the honest answer to "does chunking get worse with context".
    # Marginal ms per extra step, fitted over all k by least squares on
    # (steps_observed, mean_ms) so it does not hinge on the k=32 endpoint.
    marg = {}
    for c in sorted({int(r["ctx"]) for r in rows}):
        pts = [(f(r, "steps_observed"), f(r, "mean_ms")) for r in rows
               if int(r["ctx"]) == c]
        pts = [(x, y) for x, y in pts if x and y]
        if len(pts) < 2:
            continue
        n = len(pts)
        mx = sum(p[0] for p in pts) / n
        my = sum(p[1] for p in pts) / n
        den = sum((p[0] - mx) ** 2 for p in pts)
        if den:
            marg[c] = sum((p[0] - mx) * (p[1] - my) for p in pts) / den
    if marg:
        cs = sorted(marg)
        ax[2].bar([str(c) for c in cs], [marg[c] for c in cs],
                  color=["#4c72b0", "#dd8452"][:len(cs)])
        for i, c in enumerate(cs):
            ax[2].text(i, marg[c], f"{marg[c]:.1f}", ha="center",
                       va="bottom", fontsize=9)
        if len(cs) == 2:
            g = 100 * (marg[cs[1]] / marg[cs[0]] - 1)
            ax[2].set_title(f"Marginal cost per extra chunk grows +{g:.0f}%\n"
                            f"with context -- prefix re-read is real")
        ax[2].set_xlabel("context length (tokens)")
        ax[2].set_ylabel("ms per additional step (OLS over all k)")
        ax[2].grid(alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(OUT / "T4_chunking.png", dpi=130)
    plt.close()

# --------------------------------------------- CUDA graph cliff (side finding)
d = load(f"T1_decode_{TAG}_defaultcapture.csv")
n = load(f"T1_decode_{TAG}.csv")
if d and n:
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for src, lab, st in ((d, "default max_seq_len_to_capture=8192", "x--"),
                         (n, "capture covers full 17k range", "o-")):
        pts = sorted((int(r["ctx"]), f(r, "p50_ms")) for r in src
                     if r.get("feasible") == "1" and int(r["B"]) == 1)
        ax.plot([p[0] for p in pts], [p[1] for p in pts], st, label=lab)
    ax.set_xscale("log", base=2)
    ax.set_xlabel("context length (tokens)")
    ax.set_ylabel("decode step time B=1 (ms)")
    ax.set_title("vLLM default config: 2.3x decode cliff past ctx=8192\n(sessions drift over it as they accumulate context)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / "T1_cudagraph_cliff.png", dpi=130)
    plt.close()

print("figures written to", OUT)
for p in sorted(OUT.glob("*.png")):
    print(" ", p.name)
