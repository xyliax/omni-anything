"""Summarize the apple-to-apple sweep: WINDOWED (a2a_win) vs STREAMING (a2a_str) per N.

Reads results/sustained_fd/{a2a_win,a2a_str}_n{N}.json (written by sustained_fd.py) and prints a
side-by-side table: p50/p90/p99 latency, deadline-miss, frame-delivery cadence, drift, real-time
verdict. Same clients/gateway/model/N -> the only difference is the worker compute path."""
import json, os, sys

GRID = (sys.argv[1] if len(sys.argv) > 1 else "1 4 8 16 32 64").split()
D = "results/sustained_fd"


def load(tag, n):
    p = f"{D}/{tag}_n{n}.json"
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except Exception:
        return None


def fmt(d):
    if d is None:
        return f"{'(no data)':>40}"
    if d.get("starved"):
        return f"{'STARVED (no ticks)':>40}"
    p50, p90, p99 = d.get("p50", 0), d.get("p90", 0), d.get("p99", 0)
    miss = d.get("miss", 0) * 100
    deliv = d.get("deliv_pct", 0) * 100
    rt = "RT" if d.get("realtime") else "SLIP"
    return f"p50={p50:>5.0f} p90={p90:>5.0f} p99={p99:>5.0f}ms miss={miss:>4.1f}% deliv={deliv:>3.0f}% {rt:>4}"


print("\n================= APPLE-TO-APPLE: windowed (previous) vs streaming (resident-context) =================")
print("same clients (distinct phase-staggered) + same gateway + same model + same N; only worker path differs\n")
print(f"{'N':>4} | {'WINDOWED (fd_step 8s)':^52} | {'STREAMING (fd_step_stream)':^52}")
print("-" * 116)
for n in GRID:
    w = load("a2a_win", n)
    s = load("a2a_str", n)
    print(f"{n:>4} | {fmt(w):<52} | {fmt(s):<52}")
print("\nLegend: deliv = frame-delivery cadence completeness (>=90% + miss<2% => real-time RT).")
print("Capacity = largest N that stays RT. p99 is the production SLO; a 2s frame is a deadline, not good UX.")
