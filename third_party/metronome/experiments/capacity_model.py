"""Analytical capacity model for sustained continuous full-duplex serving.

Predicts sustained capacity N* from the per-frame latency law fitted to real measurements:

    T(N) = T_fixed + alpha * N            (per-frame wall time at batch N)
    N*(B) = (B - T_fixed) / alpha         (largest batch whose frame fits the budget B)

where, mechanistically, the marginal per-session cost decomposes into

    alpha = alpha_LLM + alpha_enc
    alpha_LLM ~ kappa_engine * P_active * (L_window + tpt)     # window-prefill + decode through the LLM
    alpha_enc ~ kappa_enc    * W_seconds * encoder_throughput  # re-encoding the audio window each frame

Findings the data forces:
  - For models whose LLM dominates (MoE 30B, dense MiniCPM) alpha tracks ACTIVE params: alpha/P_active
    is ~constant (~1.5) for a given engine (vLLM). MoE sparsity is exactly why the 30B (3B active)
    beats the dense 8B MiniCPM despite being "bigger".
  - The HF-eager engine inflates kappa_engine ~5x (the eager incremental 7B had alpha/P_active~8).
  - The Qwen2.5-Omni-7B is ENCODER-bound: its LLM is the smallest here (28 layers, 57 KB/token KV)
    yet alpha is the largest, because the heavy audio encoder re-encodes the 8 s window every frame.
    So alpha is NOT explained by LLM params alone — the encoder term can dominate.

Run: python3 experiments/capacity_model.py   (reads results/sustained_fd/*.json)
"""
import json, os, numpy as np

# model -> (file tag, budget_ms, [N grid], active_params_B, engine, note)
MODELS = [
    ("MiniCPM-o-4.5",  "svmcpm_dist",   1000, [8,16,32,48],        8.0, "vLLM, dense"),
    ("Qwen3-30B-A3B",  "sv30b_dist",    2000, [32,64,128,256],     3.0, "vLLM-FP8, MoE 3B-active"),
    ("Qwen2.5-7B",     "sv7bvllm_dist", 2000, [8,12,16],           7.0, "vLLM, dense, ENCODER-bound"),
]
EXTRA = {"Qwen3-30B-A3B": {320: "sv30b_distinct_n320"}}


def load_p99(tag, n, extra):
    f = extra.get(n)
    f = f"results/sustained_fd/{f}.json" if f else f"results/sustained_fd/{tag}_n{n}.json"
    if not os.path.exists(f):
        return None
    d = json.load(open(f)); ev = d.get("ev", [])
    if not ev:
        return None
    return float(np.percentile([l for (_, l, _) in ev], 99))


def main():
    print(f"{'model':16s} {'engine/arch':26s} {'T_fixed':>8} {'alpha':>7} {'a/P_act':>8} "
          f"{'N*pred':>7} {'budget':>7}")
    rows = []
    for name, tag, bud, ns, pa, note in MODELS:
        em = EXTRA.get(name, {})
        xs, ys = [], []
        for n in ns:
            p = load_p99(tag, n, em)
            if p is not None:
                xs.append(n); ys.append(p)
        if len(xs) < 2:
            print(f"{name:16s} insufficient data"); continue
        xs, ys = np.array(xs), np.array(ys)
        a, b = np.polyfit(xs, ys, 1)               # ys = b + a*xs
        nstar = (bud - b) / a
        rows.append((name, note, b, a, a/pa, nstar, bud))
        print(f"{name:16s} {note:26s} {b:7.0f}m {a:6.2f}m {a/pa:7.2f} {nstar:7.0f} {bud:6.0f}m")
    print("\nReading: N*(B) = (B - T_fixed)/alpha. alpha is the marginal ms/session.")
    print("alpha/P_active ~1.5 for vLLM when LLM-bound (30B, MiniCPM); the 7B's alpha is far higher")
    print("at the SAME engine because its audio encoder (not its tiny LLM) dominates -> encoder-bound.")
    # SLO capacities from the law
    print("\nCapacity by p99 SLO (from the fitted law, N*=(SLO-T_fixed)/alpha):")
    print(f"  {'model':16s} {'<=500ms':>8} {'<=1000ms':>9} {'<=1500ms':>9} {'<=2000ms':>9}")
    for (name, note, b, a, _, _, bud) in rows:
        caps = [max(0, int((slo - b) / a)) for slo in (500, 1000, 1500, 2000)]
        print(f"  {name:16s} {caps[0]:>8} {caps[1]:>9} {caps[2]:>9} {caps[3]:>9}")


if __name__ == "__main__":
    main()
