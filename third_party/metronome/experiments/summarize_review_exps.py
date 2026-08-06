"""Summarize the review follow-up experiments (run_review_exps.sh) once they complete."""
import json, os, re, sys

R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def statlog(path):
    """-> (t, kv, run, wait) arrays from a METRONOME_STATLOG file."""
    T, K, RU, W = [], [], [], []
    if not os.path.exists(path):
        return T, K, RU, W
    for ln in open(path):
        m = re.match(r"([\d.]+) kv=([\d.]+) run=(\d+) wait=(\d+)", ln)
        if m:
            T.append(float(m.group(1))); K.append(float(m.group(2)))
            RU.append(int(m.group(3))); W.append(int(m.group(4)))
    return T, K, RU, W


def kv_summary(tag, path, n):
    T, K, RU, W = statlog(path)
    if not T:
        print(f"  {tag}: no stat log"); return
    kmax = max(K)
    stall = next((t for t, r, w in zip(T, RU, W) if r == 0 and w >= n * 0.9), None)
    # plateau = median of last third; growth = slope of middle third (per 100s)
    third = len(K) // 3
    last = sorted(K[-third:])[third // 2] if third else K[-1]
    if third and (T[2 * third] - T[third]) > 1:
        slope = (K[2 * third] - K[third]) / (T[2 * third] - T[third]) * 100
    else:
        slope = float("nan")
    print(f"  {tag}: kv_max={kmax:.3f} last-third-median={last:.3f} "
          f"mid-slope={slope:+.3f}/100s stall={'%.0fs' % stall if stall else 'none'}")


print("=== EXP1 long-horizon quality ===")
for swa in [0, 512, 1024, 2048]:
    p = os.path.join(R, "sustained_fd", f"lh_swa{swa}.json")
    if not os.path.exists(p):
        print(f"  swa={swa}: missing"); continue
    d = json.load(open(p))
    sh = d["seg_hits"]
    rot = " ".join(f"{h}/{t}" for h, t in sh[:8])
    print(f"  swa={swa}: rot[{rot}] espeak-known={sh[8][0]}/{sh[8][1]} "
          f"recall={sh[9][0]}/{sh[9][1]} rep_late={d['rep_late']:.2f} "
          f"lat p50={d['lat_p50']:.0f} p99={d['lat_p99']:.0f} errs={d['errs']}")

print("=== EXP2 MiniCPM-o-4.5 600s wall pair (N=96, 1s frames) ===")
for cond in ["van", "win"]:
    out = os.path.join(R, f"mcpm600_{cond}.out")
    if os.path.exists(out):
        for ln in open(out):
            if "DEGRADATION" in ln or "OVERALL" in ln:
                print(f"  {cond}: {ln.strip()}")
    kv_summary(f"mcpm {cond}", os.path.join(R, f"mcpm_stats_{cond}.log"), 96)

print("=== EXP3 windowed ceiling (SWA=1024) ===")
base_n, base_plat = 128, 0.258   # measured plateau from preempt_stats_win.log
print(f"  reference: N={base_n} plateau={base_plat}")
for n in [192, 256]:
    kv_summary(f"N={n}", os.path.join(R, f"ceil_stats_n{n}.log"), n)
    T, K, _, _ = statlog(os.path.join(R, f"ceil_stats_n{n}.log"))
    if K:
        third = len(K) // 3
        plat = sorted(K[-third:])[third // 2] if third else K[-1]
        print(f"    linearity: predicted {base_plat * n / base_n:.3f}, measured {plat:.3f}; "
              f"implied ceiling ~{n / plat:.0f} sessions" if plat > 0 else "")

print("=== EXP4 randomized-order variance (20 x 300s) ===")
order = []
op = os.path.join(R, "rvar_order.txt")
if os.path.exists(op):
    order = [ln.split()[0] for ln in open(op) if ln.strip()]
out = os.path.join(R, "rvar_run.out")
verdicts = {}
if os.path.exists(out):
    tag = None
    for ln in open(out):
        m = re.match(r"#### (rvar_\S+) \(try", ln)
        if m:
            tag = m.group(1)
        if "DEGRADING" in ln and tag:
            verdicts[tag] = "WALL"
        elif "STABLE" in ln and tag:
            verdicts[tag] = "flat"
van = [t for t in order if "van" in t]
win = [t for t in order if "ineng" in t]
vw = sum(1 for t in van if verdicts.get(t) == "WALL")
ww = sum(1 for t in win if verdicts.get(t) == "WALL")
done = sum(1 for t in order if t in verdicts)
print(f"  progress {done}/20; vanilla walls {vw}/{sum(1 for t in van if t in verdicts)}, "
      f"windowed walls {ww}/{sum(1 for t in win if t in verdicts)}")
for i, t in enumerate(order):
    if t in verdicts:
        print(f"   {i+1:>2}. {t:<18} {verdicts[t]}")
