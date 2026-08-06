"""Fig (replaces the four-model capacity table): fresh, single-N streaming capacity across the four
interaction models, one worker per point. ">=" bars were flat at the largest N tested (the offered load,
not the model, saturated); Qwen2.5-Omni-7B shows its measured 16-24 range (encoder-bound)."""
import numpy as np
from nstyle import apply, WIN, GREY, DARK
import matplotlib.pyplot as plt

apply()
fig, ax = plt.subplots(figsize=(5.4, 2.1))

# (model, solid bar, range extension, lower-bound?, note)
rows = [
    ("Qwen2.5-Omni-7B",          16, 24,   False, "16–24 $\\cdot$ encoder-bound $\\cdot$ 2 s budget"),
    ("Moshi",                    32, None, True,  "$\\geq$ 32 $\\cdot$ native Mimi, voice-out $\\cdot$ 80 ms budget"),
    ("MiniCPM-o-4.5",            96, None, False, "$\\sim$96 $\\cdot$ dense $\\sim$9 B $\\cdot$ 1 s budget"),
    ("Qwen3-Omni-30B-A3B (FP8)", 160, None, True, "$\\geq$ 160 $\\cdot$ MoE, 3 B active $\\cdot$ 2 s budget"),
]
y = np.arange(len(rows))
for i, (name, solid, hi, lb, note) in enumerate(rows):
    ax.barh(i, solid, 0.55, color=WIN, zorder=3)
    end = solid
    if hi is not None:
        ax.barh(i, hi - solid, 0.55, left=solid, color=WIN, alpha=0.35, zorder=3)
        end = hi
    if lb:  # flat at the largest N tested: capacity is a lower bound
        ax.annotate("", xy=(end + 13, i), xytext=(end + 1.5, i),
                    arrowprops=dict(arrowstyle="-|>", color=WIN, lw=1.6, alpha=0.65))
        end += 13
    ax.text(end + 4, i, note, va="center", fontsize=7.4, color=DARK)

ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=8)
ax.set_xlim(0, 320); ax.set_ylim(-0.55, len(rows) - 0.45)
ax.set_xticks([0, 32, 64, 96, 128, 160])
ax.set_xlabel("fresh streaming capacity (concurrent sessions, 90 s burst)")
ax.grid(axis="y", visible=False)

fig.savefig("capacity.pdf")
fig.savefig("capacity.png", dpi=140)
print("wrote capacity.pdf")
