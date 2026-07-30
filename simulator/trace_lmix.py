"""Realistic tool-result length mixture vs the naive whole-splice engine.

The spec's L=8192 stress case guarantees a >480ms prefill step; real tool
results are mostly short. Mixture: 60% API-call sized (128-512), 30%
search/RAG sized (768-2048), 10% document tail (4096-8192). Contrast with the
same mixture minus the tail, across N = 8 / 24 / 48.
"""
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calib_model import load_default
from engine import Engine, Policy

cal = load_default(Path(__file__).parent.parent / "calibration" / "data",
                   "Qwen3-1.7B")

class MixEngine(Engine):
    def __init__(self, *a, lmix=None, **kw):
        self.lmix = lmix
        super().__init__(*a, **kw)

    def _fire(self, t, kind, payload):
        if kind == "tool" and self.lmix:
            r = self.rng.random(); cum = 0.0
            for p, lo, hi in self.lmix:
                cum += p
                if r < cum:
                    self.tool_L = self.rng.randrange(lo, hi + 1)
                    break
        super()._fire(t, kind, payload)

MIX_TAIL = [(0.6, 128, 512), (0.3, 768, 2048), (0.1, 4096, 8192)]
MIX_SHORT = [(0.6, 128, 512), (0.4, 768, 2048)]

def run(N, mix, label):
    out = []
    for sd in range(1, 6):
        e = MixEngine(cal, n_sessions=N, seed=sd, sim_ms=60000,
                      tool_rate_per_min=6.0, tool_L=1024, policy=Policy.WHOLE,
                      lmix=mix, kv_pool_tokens=44336)
        out.append(e.run())
    mr = statistics.fmean(r['miss_rate'] for r in out) * 100
    clean = statistics.fmean(sum(1 for v in r['per_session'].values()
            if v['beats'] and v['misses'] / v['beats'] <= 0.01) for r in out)
    ans = statistics.fmean(r['answer_p50_ms'] for r in out if r['answer_p50_ms'])
    dv = statistics.fmean(r['answers_delivered'] / max(1, r['total_tools'])
                          for r in out)
    cross = statistics.fmean(r['cross_session_misses'] for r in out)
    kvof = statistics.fmean(r['kv_overflow_steps'] / max(1, r['steps'])
                            for r in out)
    print(f"{label:>8} N={N:>2}: miss={mr:6.2f}%  clean={clean:4.1f}/{N}  "
          f"ans_p50={ans:6.0f}ms  deliv={dv:.2f}  cross={cross:6.1f}  "
          f"kv_overflow={kvof:.2f}")

if __name__ == "__main__":
    print("== naive whole-splice, realistic length mixture ==")
    for N in (8, 24, 48):
        run(N, MIX_TAIL, "带长尾")
    print("== same minus the 10% tail (all <=2048) ==")
    for N in (8, 24, 48):
        run(N, MIX_SHORT, "无长尾")
