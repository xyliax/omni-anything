"""Derive N* (the schedulable capacity) from measured per-frame latency sweeps, instead of hand-setting
it. For each config, N* = the largest swept N whose steady-state per-frame latency stays under the SLO.
This is the value the online AIMD controller converges to; here we derive it offline from the capacity
probe (the sweep) to show the cap is measured, not an oracle constant.
"""
import json, os, sys

D = "results/sustained_fd"


def p50(tag, n):
    f = f"{D}/{tag}_n{n}.json"
    if not os.path.exists(f):
        return None
    try:
        return json.load(open(f)).get("p50")
    except Exception:
        return None


# config -> (tag, swept Ns, budget_ms)
CONFIGS = [
    ("vanilla vLLM-realtime", "hl_vanilla", [64, 96, 128, 160], 2000),
    ("in-engine SWA (W=1024)", "ineng_cap", [128, 160], 2000),
    ("MiniCPM-o-4.5", "bench_mcpm", [16, 32, 64, 96], 1000),
    ("Qwen2.5-Omni-7B", "bench_q7b", [16, 32, 64, 96], 2000),
]
SLOS = [0.05, 0.25, 0.5]   # SLO as a fraction of budget (e.g., 0.05 = 100ms @ 2s budget)


def main():
    print(f"{'config':28s} {'budget':>7} " + " ".join(f"N*@{int(s*100)}%budget".rjust(14) for s in SLOS))
    for name, tag, ns, budget in CONFIGS:
        cells = []
        for s in SLOS:
            slo = s * budget
            nstar = 0
            for n in sorted(ns):
                v = p50(tag, n)
                if v is None:
                    continue
                if v <= slo:
                    nstar = n
                else:
                    break  # latency crossed the SLO -> knee found
            # if all swept Ns are under the SLO, N* is >= the largest swept N
            allunder = all((p50(tag, n) or 1e9) <= slo for n in ns if p50(tag, n) is not None)
            cells.append((f">={max(ns)}" if allunder and nstar == max(ns) else str(nstar)))
        print(f"{name:28s} {budget:>7} " + " ".join(c.rjust(14) for c in cells))
    print("\nN* = largest swept N with steady p50 <= SLO. The online AIMD admission controller "
          "(--online-admit) converges to this knee from latency feedback; this table derives the same "
          "from the capacity-probe sweep (measured, not hand-set).")


if __name__ == "__main__":
    main()
