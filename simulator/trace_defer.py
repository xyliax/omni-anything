"""The user's proposed policy: beats-first + per-chunk admission test
("will this chunk finish before the next beat arrives?" with a 15% calibration
margin) + deferred chunks get head-of-line among tools (reservation).

DeferEngine = IDLE_ONLY (beats-first) + fit-check on every tool chunk +
deferred-to-front ordering. Big tools amortise across successive gaps
(installments), so completion beats are deterministic.
"""
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calib_model import load_default
from engine import Engine, Policy
from trace_lmix import MixEngine, MIX_TAIL

cal = load_default(Path(__file__).parent.parent / "calibration" / "data",
                   "Qwen3-1.7B")

class DeferEngine(MixEngine):
    MARGIN = 1.15

    def _admit(self, force_idle=False):
        # gap = time until the next BEAT arrival (other timer kinds — tool
        # returns, interrupts — do not claim the engine and must not shrink
        # the admission window).
        nb = min((t for (t, _, kind, _p) in self.timers if kind == "beat"),
                 default=float("inf"))
        gap = nb - self.now
        hidden_w, hidden_r = [], []
        for src, hid in ((self.waiting, hidden_w), (self.running, hidden_r)):
            keep = []
            for s in src:
                if s.is_tool and s.in_prefill:
                    take = min(s.prefill_total - s.prefill_done, self.budget)
                    pred = self.cal.prefill_step_ms(
                        take, self.sessions[s.sid].ctx) * self.MARGIN
                    if pred > gap:
                        hid.append(s)
                        continue
                keep.append(s)
            src[:] = keep
        out = super()._admit(force_idle)
        # deferred tools re-enter at the FRONT: they hold the reservation for
        # the next gap and outrank newly arrived tools.
        self.waiting[:0] = hidden_w
        self.running[:0] = hidden_r
        return out

def run(N, phase, mk, label):
    rs = []
    for sd in range(1, 6):
        e = mk(cal, n_sessions=N, seed=sd, sim_ms=60000, tool_rate_per_min=6.0,
               tool_L=1024, lmix=MIX_TAIL, kv_pool_tokens=44336, phase=phase)
        rs.append(e.run())
    m = statistics.fmean(r['miss_rate'] for r in rs) * 100
    clean = statistics.fmean(sum(1 for v in r['per_session'].values()
            if v['beats'] and v['misses'] / v['beats'] <= 0.01) for r in rs)
    ansl = [a for r in rs if r['answer_p50_ms'] for a in [r['answer_p50_ms']]]
    ans = statistics.fmean(ansl) if ansl else float('nan')
    p99 = statistics.fmean(r['answer_p99_ms'] or 0 for r in rs)
    dv = statistics.fmean(r['answers_delivered'] / max(1, r['total_tools'])
                          for r in rs)
    print(f"  N={N:>2} {phase:>7} {label:>14}: miss={m:6.2f}%  clean={clean:5.1f}/{N}  "
          f"ans_p50={ans:6.0f}ms  ans_p99={p99:6.0f}ms  deliv={dv:.2f}")

W = lambda *a, **kw: MixEngine(*a, policy=Policy.WHOLE, **kw)
I = lambda *a, **kw: MixEngine(*a, policy=Policy.IDLE_ONLY, **kw)
D = lambda *a, **kw: DeferEngine(*a, policy=Policy.IDLE_ONLY, **kw)

if __name__ == "__main__":
    print("带长尾混合注入(4-8k 占 10%):")
    for N in (24, 48):
        run(N, "aligned", W, "naive(FCFS整段)")
        run(N, "aligned", I, "拍优先(idle)")
        run(N, "aligned", D, "defer+预定(你的)")
    print("同策略在随机相位下(空隙碎片化的照妖镜):")
    run(48, "random", D, "defer+预定(你的)")
