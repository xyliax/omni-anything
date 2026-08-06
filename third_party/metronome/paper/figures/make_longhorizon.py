"""Long-horizon quality: correctness vs session age (rotating spoken questions), plus the
espeak comprehension/recall probes. Data: results/sustained_fd/lh_swa{0,512,1024,2048}.json
(fd_longhorizon_probe.py) + lh_sink32.json / lh_tri0.json (run_sink_exps.sh). (a) shows the
post-hoc window degrading generation after the window slides (attention-sink effect) and sink
retention recovering it; lh_tri0 is the same-kernel no-sink control. (b) shows the espeak-known
sanity segment and the beyond-horizon recall probe."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import nstyle
nstyle.apply()

D = "../../results/sustained_fd"
SINK = "#009E73"   # Okabe-Ito bluish green -- windowed + sink retention (the mitigation)
CONDS = [  # (tag, label, color, linestyle)
    ("lh_swa0",    nstyle.LABEL_VAN,          nstyle.VAN,  "-"),
    ("lh_swa512",  "windowed $W{=}512$ (~20s)",  "#7CB9DC", "--"),
    ("lh_swa1024", "windowed $W{=}1024$ (~40s)", nstyle.WIN, "-"),
    ("lh_swa2048", "windowed $W{=}2048$ (~80s)", "#054F7D", ":"),
    ("lh_tri0",    "$W{=}1024$, sink kernel, 0 sinks", nstyle.GREY, "--"),
    ("lh_sink32",  "$W{=}1024$ + 32 sink tokens", SINK, "-"),
]

data = {}
for tag, *_ in CONDS:
    p = os.path.join(D, f"{tag}.json")
    if os.path.exists(p):
        data[tag] = json.load(open(p))
if not data:
    raise SystemExit("no lh_swa*.json yet")

N_ROT = 8
fig, (ax, axb) = plt.subplots(1, 2, figsize=(7.4, 2.6), gridspec_kw={"width_ratios": [3, 2]})

for tag, label, color, ls in CONDS:
    if tag not in data:
        continue
    sh = data[tag]["seg_hits"]
    xs = [k * 30 + 15 for k in range(N_ROT)]
    ys = [sh[k][0] / sh[k][1] * 100 if sh[k][1] else np.nan for k in range(N_ROT)]
    hero = tag in ("lh_sink32", "lh_swa0")
    ax.plot(xs, ys, ls, color=color, marker="o", ms=3.5 if hero else 2.8,
            lw=1.7 if hero else 1.1, label=label)
ax.set_xlabel("session age when the question plays (s)")
ax.set_ylabel("sessions answering correctly (%)")
ax.set_ylim(0, 74)
ax.set_xlim(0, 245)
ax.set_title("(a) correctness vs session age (rotating questions)", fontsize=9)
ax.legend(loc="upper right", fontsize=6.2, handlelength=1.8, ncol=2, columnspacing=0.9)

# (b) espeak-known (comprehension sanity) and espeak-recall (beyond-horizon memory);
# only the W=1024 family + vanilla to keep the groups readable
BARS = ["lh_swa0", "lh_swa1024", "lh_tri0", "lh_sink32"]
labels = ["espeak question\n(240–270 s)", "recall of first question\n(270–300 s)"]
w = 0.19
present = [(t, l, c) for (t, l, c, _) in CONDS if t in data and t in BARS]
for j, (tag, label, color) in enumerate(present):
    sh = data[tag]["seg_hits"]
    vals = [sh[N_ROT][0] / sh[N_ROT][1] * 100 if sh[N_ROT][1] else 0,
            sh[N_ROT + 1][0] / sh[N_ROT + 1][1] * 100 if sh[N_ROT + 1][1] else 0]
    xs = [x + (j - (len(present) - 1) / 2) * w for x in range(2)]
    axb.bar(xs, vals, w, color=color, label=label)
    for x, v in zip(xs, vals):  # label every bar so 0% is visibly 0, not missing
        axb.text(x, v + 1.0, f"{v:.0f}", ha="center", va="bottom",
                 fontsize=6.4, color=nstyle.DARK)
axb.set_xticks(range(2)); axb.set_xticklabels(labels, fontsize=7.5)
axb.set_ylim(0, 45)
axb.set_ylabel("sessions (%)")
axb.set_title("(b) synthetic-voice probes", fontsize=9)

fig.tight_layout()
fig.savefig("longhorizon.pdf"); fig.savefig("longhorizon.png", dpi=160)
print("wrote longhorizon.pdf/png")
