"""S9: emit the benchmark leaderboard (markdown) from results/ JSON artifacts."""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from metronome import models


def load(p):
    with open(os.path.join(ROOT, "results", p)) as fh:
        return json.load(fh)


def main():
    core = {s["model"]: s for s in load("core/core_summary.json")}
    adm = load("admission/admission_summary.json")
    kv = {s["model"]: s for s in load("kv/kv_summary.json")}
    pvm = {p["model"]: p for p in adm["predicted_vs_measured"]}

    lines = ["# Metronome-Bench Leaderboard", "",
             "MSCS = max sustainable concurrent sessions @ 0.1% deadline-miss SLO. "
             "Hardware: RTX PRO 6000 Blackwell.", "",
             "| Model | Tick | B0 | B1 | B2 | **M** | M/B1 | $/sess-hr (M) | "
             "pred=meas (G5) | KV gain | class |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m, s in core.items():
        v = s["mscs"]
        d = s["dollars"]
        g5 = pvm.get(m, {})
        kvm = kv.get(m, {})
        tick = f"{models.get(m).period_s*1000:.0f} ms"
        lines.append(
            f"| {m} | {tick} | {v['B0']} | {v['B1']} | {v['B2']} | **{v['M']}** | "
            f"{s['gain']:.1f}× | ${d['M']:.4f} | "
            f"{g5.get('predicted_worst_case','?')}={g5.get('measured','?')} | "
            f"{kvm.get('kv_budget_gain', float('nan')):.1f}× | "
            f"{kvm.get('classification','?')} |")
    out = "\n".join(lines) + "\n"
    with open(os.path.join(ROOT, "results", "LEADERBOARD.md"), "w") as fh:
        fh.write(out)
    print(out)


if __name__ == "__main__":
    main()
