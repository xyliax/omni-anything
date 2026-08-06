"""Fig (for the evaluation): a generous window is essentially free. At N=128, p50/p90 stay ~5 ms up to a
2048-token (~80 s) window; only a very large 4096-token window lets the attention tail reappear
(p90 jumps to ~160 ms). One can pick a comfortably long memory horizon at no capacity cost."""
import numpy as np
from nstyle import apply, WIN, AMBER
import matplotlib.pyplot as plt

apply()
fig, ax = plt.subplots(figsize=(4.3, 2.8))

W = [512, 1024, 2048, 4096]
p50 = [2.5, 2.6, 2.4, 3.5]
p90 = [5.3, 4.7, 5.0, 161.1]
x = np.arange(len(W)); bw = 0.38
ax.bar(x - bw/2, p50, bw, color=WIN, label="$p_{50}$")
ax.bar(x + bw/2, p90, bw, color=AMBER, label="$p_{90}$")
ax.set_yscale("log"); ax.set_ylim(1, 400)
secs = {512: 20, 1024: 40, 2048: 80, 4096: 160}
ax.set_xticks(x); ax.set_xticklabels([f"{w}\n({secs[w]} s)" for w in W])
ax.set_xlabel("window $W$ (tokens, $\\approx$context)")
ax.set_ylabel("per-frame latency (ms)")
ax.annotate("attention tail\nreappears", xy=(3 + bw/2 - 0.08, 130), xytext=(1.75, 45),
            color=AMBER, fontsize=7.6, ha="center",
            arrowprops=dict(arrowstyle="->", color=AMBER, lw=1.0))
ax.axvspan(-0.5, 2.5, color=WIN, alpha=0.06)
ax.text(1.0, 300, "$\\leq$80 s context: free", color=WIN, fontsize=7.6,
        ha="center", va="top", fontweight="bold")
ax.legend(loc="upper left")

fig.savefig("window_ablation.pdf")
fig.savefig("window_ablation.png", dpi=140)
print("wrote window_ablation.pdf")
