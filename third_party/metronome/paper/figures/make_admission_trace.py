"""Fig: AIMD admission CONVERGENCE over time (open-system ramp, offered 512, 600 ms target).
The gateway logs one line per tick (results/admit_trace_*.log): elapsed, live sessions, effCap (the
online N* estimate), per-frame gpu ms, cumulative admitted/rejected. TOP: live (admitted) concurrency,
the controller's N* estimate, and the cumulative shed count, all in session units on ONE axis -- they
climb as sessions arrive, then settle at the schedulable knee. BOTTOM: per-frame latency tracks the
target and stays under the deadline throughout -- the controller discovers N* from this signal alone."""
import numpy as np
from nstyle import apply, WIN, GREY, DARK, AMBER
import matplotlib.pyplot as plt

LOG = "../../results/admit_trace_ramp_admit_win_trace.log"
TARGET_MS, BUDGET_MS, OFFERED = 600.0, 2000.0, 512

t, live, cap, gpu, adm, rej = [], [], [], [], [], []
for line in open(LOG):
    p = line.split()
    if len(p) < 6:
        continue
    d = {kv.split("=")[0]: kv.split("=")[1] for kv in p[1:] if "=" in kv}
    t.append(float(p[0])); live.append(int(d["live"])); cap.append(int(d["cap"]))
    gpu.append(float(d["gpu"])); adm.append(int(d["adm"])); rej.append(int(d["rej"]))
t, live, cap, gpu, rej = map(np.array, (t, live, cap, gpu, rej))

# steady plateau is between the first cap-set and the start of the session drain (sessions reaching
# their fixed lifetime at the end). Settled N* = the held admitted count over that window.
cap_on = t[cap > 0]
t_cap = cap_on.min() if len(cap_on) else t[0]
plateau = int(np.median(live[(cap > 0)]))
# drain begins where live falls and stays below 0.9*plateau near the end
drain = next((t[i] for i in range(len(t) - 1, 0, -1)
              if live[i] >= 0.9 * plateau), t.max())
nstar = plateau
xmax = min(t.max(), drain + 8)

apply()
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.6, 4.1), sharex=True,
                               gridspec_kw={"height_ratios": [1.15, 0.85], "hspace": 0.12})

# ---- TOP: concurrency, N* estimate, and cumulative shed -- one shared axis (all sessions) ----
ax1.fill_between(t, 0, live, color=WIN, alpha=0.14)
ax1.plot(t, live, color=WIN, label="admitted (live) sessions")
capm = np.where(cap > 0, cap, np.nan)
ax1.plot(t, capm, color=DARK, ls="--", lw=1.3, label="controller $N^\\star$ estimate (cap)")
ax1.plot(t, rej, color=GREY, lw=1.4, label="cumulative shed (rejected)")
ax1.axhline(nstar, color=WIN, ls=":", lw=1.0)
ax1.text(118, nstar - 12, f"settles at $N^\\star\\!\\approx\\!{nstar}$", color=WIN,
         fontsize=8, ha="center", va="top")
ax1.set_ylabel("sessions")
ax1.set_ylim(0, max(rej.max(), live.max()) * 1.14)
ax1.legend(loc="center right", bbox_to_anchor=(0.975, 0.28), fontsize=7.6)

# ---- BOTTOM: per-frame latency vs target/deadline (single series: no legend, lines labeled) ----
ax2.axhline(BUDGET_MS, color=DARK, ls="--", lw=1.0)
ax2.text(2, BUDGET_MS - 40, "frame deadline 2000 ms", color=DARK, fontsize=7.3, va="top")
ax2.axhline(TARGET_MS, color=AMBER, ls="--", lw=1.0)
ax2.text(2, TARGET_MS + 40, f"admit target {int(TARGET_MS)} ms", color=AMBER, fontsize=7.3, va="bottom")
ax2.plot(t, gpu, color=WIN)
ax2.text(xmax - 3, 130, "per-frame latency", color=WIN, fontsize=7.6, ha="right")
ax2.set_ylabel("per-frame latency (ms)")
ax2.set_xlabel("elapsed time (s)")
ax2.set_xlim(0, xmax)
ax2.set_ylim(0, max(BUDGET_MS * 1.1, np.percentile(gpu, 99) * 1.2))

fig.savefig("admission_trace.pdf")
fig.savefig("admission_trace.png", dpi=140)
print(f"wrote admission_trace.pdf  (ticks={len(t)}, settled N*={nstar}, "
      f"final shed={rej[-1]}, latency p50={np.median(gpu):.0f}ms)")
