"""Shared NeurIPS-ish matplotlib style: serif to match LaTeX body, muted palette,
clean spines, tight PDF output. Import and call apply() at the top of each figure script.

Palette: Okabe-Ito vermillion/blue pair (CVD-validated: worst adjacent-pair deltaE 91.9
protan / 65.7 tritan, all >= 3:1 contrast on white). Vermillion = the failure (vanilla,
unbounded KV); blue = the fix (Metronome, windowed KV). Amber is the accent for
percentile/target series. Series labels are shared here so every figure names the two
policies identically."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

VAN   = "#D55E00"   # vermillion -- vanilla / unbounded KV (the failure)
WIN   = "#0072B2"   # blue       -- Metronome / windowed KV (the fix)
AMBER = "#B8860B"   # accent     -- p90 / targets
GREY  = "#7f8c8d"
DARK  = "#2c3e50"

# back-compat aliases (older scripts import RED/GREEN/BLUE)
RED, GREEN, BLUE = VAN, WIN, WIN

LABEL_VAN = "vLLM-realtime (unbounded KV)"
LABEL_WIN = "Metronome (windowed KV)"

def apply():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "cm",
        "font.size": 9,
        "axes.titlesize": 9.5,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.linestyle": ":",
        "grid.alpha": 0.45,
        "grid.linewidth": 0.6,
        "legend.frameon": True,
        "legend.framealpha": 0.92,
        "legend.edgecolor": "0.8",
        "lines.linewidth": 1.8,
        "figure.dpi": 140,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    })
