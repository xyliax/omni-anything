"""Task H (efficiency) — deadline-aware DVFS energy lever.

Every tick must finish within the frame budget F, but a batch with current cost
C ≤ F has *slack*. Scaling the GPU clock to φ = C/F (just meeting the deadline)
trades that slack for energy: per-tick latency ≈ C/φ, dynamic power ∝ φ³, so per-tick
energy ∝ φ³·(C/φ)/C = φ² — i.e. **energy ∝ (C/F)²** vs running at φ=1 and idling.

This couples to §1.5: because typical sessions live on the *rising ramp* (life ≪
fill-time), their per-tick cost C(L) is well below the plateau most of the time, so
C/F < 1 and there is real DVFS headroom. We compute the energy saving vs an
always-max-clock baseline, integrated over the session-age distribution, as a
function of load and mean session length. (Analytical — grounded in the measured
C(L) cost model and the standard energy∝φ² model; no on-device power measurement.)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments._common import load_cost, all_models
from metronome import models

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "dvfs")
PHI_MIN = 0.3      # GPUs cannot scale arbitrarily low; floor the clock fraction
STATIC_FRAC = 0.3  # fraction of power that is static (DVFS only cuts dynamic power)


def batch_ms(cost, N, L):
    return (cost.batch_base + cost.batch_per_session * N + cost.batch_alpha * N * L) * cost.tail_factor


def run(name):
    facts = models.get(name)
    cost = load_cost(name)
    window = max(512, facts.context_ceiling_tokens // 4)
    budget = facts.period_s * 1000.0 * 0.9
    rate = facts.tokens_per_tick / facts.period_s
    fill_budget_s = window / rate
    # operating concurrency: near worst-case capacity at the plateau
    denom = cost.batch_per_session + cost.batch_alpha * window
    Ncap = max(2, int((budget - cost.batch_base) / max(denom, 1e-9)))

    # energy saving vs mean session length (fraction of fill-to-budget time).
    # age distribution: exponential with the given mean, clamped to [0, fill].
    rng = np.random.default_rng(0)
    life_fracs = np.linspace(0.1, 3.0, 20)
    rows = []
    for N in (max(2, Ncap // 2), Ncap):
        saves = []
        for lf in life_fracs:
            mean_life = lf * fill_budget_s
            ages = rng.exponential(mean_life, 20000)
            Ls = np.minimum(rate * ages, window)
            # per-tick cost at each session's age, batched at concurrency N
            C = cost.batch_base*cost.tail_factor + cost.batch_per_session*N*cost.tail_factor \
                + cost.batch_alpha * cost.tail_factor * N * Ls   # ms, batch cost scales with mean L
            # actually batch cost depends on the *mean* resident length across the N sessions:
            meanL = np.mean(Ls)
            C_batch = batch_ms(cost, N, meanL)
            phi = max(PHI_MIN, min(1.0, C_batch / budget))
            # total energy over the frame = static (∝ time = budget, constant) +
            # dynamic (∝ φ²). DVFS only cuts the dynamic part.
            energy_dvfs = STATIC_FRAC + (1 - STATIC_FRAC) * phi ** 2
            saves.append(1.0 - energy_dvfs)   # vs φ=1 baseline (energy 1.0)
        rows.append(dict(N=N, life_fracs=life_fracs.tolist(), savings=saves))

    os.makedirs(OUT, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for r in rows:
        ax.plot(r["life_fracs"], [s*100 for s in r["savings"]], "o-",
                label=f"N={r['N']} sessions")
    ax.set_xlabel("mean session life / fill-to-budget time")
    ax.set_ylabel("energy saving vs max-clock (%)")
    ax.set_title(f"{name}: deadline-aware DVFS saves energy on the ramp (§1.5)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_dvfs.png"), dpi=120)
    plt.close(fig)

    # headline: saving at a short-session operating point (life = 0.5x fill)
    idx = int(np.argmin(np.abs(life_fracs - 0.5)))
    res = dict(model=name, Ncap=Ncap, fill_budget_s=fill_budget_s,
               saving_short_life_halfN=round(rows[0]["savings"][idx]*100, 1),
               saving_short_life_fullN=round(rows[1]["savings"][idx]*100, 1),
               life_fracs=life_fracs.tolist(),
               savings_fullN=[round(s*100, 1) for s in rows[1]["savings"]])
    with open(os.path.join(OUT, f"{name}_dvfs.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"[{name}] DVFS energy saving at life=0.5x fill: "
          f"{res['saving_short_life_halfN']}% (N={rows[0]['N']}), "
          f"{res['saving_short_life_fullN']}% (N={Ncap}, near capacity)")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = args.models or all_models()
    out = {n: run(n) for n in names}
    with open(os.path.join(OUT, "dvfs_summary.json"), "w") as fh:
        json.dump(out, fh, indent=2)


if __name__ == "__main__":
    main()
