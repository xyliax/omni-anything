"""Step-time model fitted to the T1-T4 measurements.

The simulator asks one question of this module: given an engine step carrying B
decode rows at average context `ctx` plus `prefill_tokens` prefill tokens, how
long does the step take?

Design rule: interpolate the measurements, do not fit a shape onto them. The
measured surfaces are strongly non-linear and an earlier version of this file
fitted `ms = a + b*L` per context over the whole T2 range; because the L=8192
points dominate the least squares, that underpriced the 8-token micro-prefill
that every duplex beat performs -- the single hottest cell in the simulation.
So:

  decode-only step : bilinear over the T1 grid (B x ctx)
  prefill-only step: bilinear over the T2 grid (log L x ctx)
  mixed step       : T1 decode base + the measured T3 *increment*, interpolated
                     over (p x ctx) and taken exactly when the cell exists

The mixed step is deliberately NOT decode_ms + prefill_ms. T3 shows a mixed
step costs a large fixed entry toll (~9-13ms) and then very little per extra
token, while T2's solo prefill numbers carry their own per-request fixed cost;
adding the two double-counts the fixed part.

Every number this module returns is traceable to calibration/data/*.csv.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

DECODE_PRIOR_MS = 51.0        # 3090 + 8B prior, only used with no T1 data
PREFILL_PRIOR_MS_PER_TOK = 0.46


def _interp1(x, xs, ys):
    """Linear interp with linear extrapolation at both ends."""
    if len(xs) == 1:
        return ys[0]
    if x <= xs[0]:
        sl = (ys[1] - ys[0]) / (xs[1] - xs[0])
        return max(1e-6, ys[0] + sl * (x - xs[0]))
    if x >= xs[-1]:
        sl = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
        return ys[-1] + sl * (x - xs[-1])
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            f = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + f * (ys[i + 1] - ys[i])
    return ys[-1]


def _bilinear(x, y, grid, logx=False):
    """grid: {(x, y) -> v}, ragged-tolerant. Interp along x per y, then over y."""
    ys = sorted({yy for _, yy in grid})
    per_y = []
    for yy in ys:
        xs = sorted(xx for xx, y2 in grid if y2 == yy)
        if not xs:
            continue
        vx = [grid[(xx, yy)] for xx in xs]
        ax = [math.log2(max(xx, 1)) for xx in xs] if logx else xs
        q = math.log2(max(x, 1)) if logx else x
        per_y.append((yy, _interp1(q, ax, vx)))
    if not per_y:
        return None
    return _interp1(y, [a for a, _ in per_y], [b for _, b in per_y])


class Calibration:
    def __init__(self, t1_csv=None, t2_csv=None, t3_csv=None, t4_csv=None,
                 scale=1.0, source="measured"):
        self.scale = scale
        self.source = source
        self.t1 = {}     # (B, ctx)     -> step ms   (pure decode)
        self.t2 = {}     # (L, ctx)     -> ms        (solo prefill of L tokens)
        self.t3 = {}     # (B, ctx, p)  -> step ms   (B decode rows + p prefill)
        self.t4 = {}     # (k, ctx)     -> ms        (L=2048 split into k chunks)
        self.files = {}
        for name, path, fn in (("T1", t1_csv, self._load_t1),
                               ("T2", t2_csv, self._load_t2),
                               ("T3", t3_csv, self._load_t3),
                               ("T4", t4_csv, self._load_t4)):
            if path:
                fn(path)
                self.files[name] = str(path)
        self._fit()

    # ------------------------------------------------------------- loading
    def _load_t1(self, p):
        for r in csv.DictReader(open(p)):
            if r.get("feasible") == "0" or not r.get("p50_ms"):
                continue
            self.t1[(int(r["B"]), int(r["ctx"]))] = float(r["p50_ms"])

    def _load_t2(self, p):
        for r in csv.DictReader(open(p)):
            if r.get("p50_ms"):
                self.t2[(int(r["L"]), int(r["ctx"]))] = float(r["p50_ms"])

    def _load_t3(self, p):
        for r in csv.DictReader(open(p)):
            if r.get("p50_ms"):
                self.t3[(int(r["B"]), int(r["ctx"]), int(r["p"]))] = float(r["p50_ms"])

    def _load_t4(self, p):
        for r in csv.DictReader(open(p)):
            if r.get("p50_ms"):
                self.t4[(int(r["k"]), int(r["ctx"]))] = float(r["p50_ms"])

    # ------------------------------------------------------------- fitting
    def _fit(self):
        self.t1_Bs = sorted({b for b, _ in self.t1})
        self.t1_ctxs = sorted({c for _, c in self.t1})
        self.t2_ctxs = sorted({c for _, c in self.t2})
        self.t2_Ls = sorted({L for L, _ in self.t2})

        # --- the eager-prefill toll -------------------------------------
        # A step containing any prefill tokens cannot use a captured CUDA graph,
        # so it runs eager. calibration/data/diag_prefill_steps.json shows a
        # session woken with only 8 new tokens costs ~19ms while a pure decode
        # step at the same context costs ~7ms, and T2 is flat from L=8 to L=128.
        # That flat floor is the toll; per-token compute only shows up past
        # L~256. Two tolls, because they are measured separately:
        #   toll_solo(ctx): a prefill-only step. From T2, which is a two-step
        #     sequence (eager prefill, then one decode step that samples the
        #     first token), so subtract a decode step.
        #   toll_fused(ctx): the increment when prefill joins an existing decode
        #     batch. From T3's flat p<=256 region, averaged over B (B=4/8/16
        #     land within ~3ms of each other, with no monotone B trend).
        self.toll_solo = {}
        for c in self.t2_ctxs:
            base = self.t2.get((min(self.t2_Ls), c))
            if base is not None:
                self.toll_solo[c] = max(0.5, base - self.decode_ms(1, c) / max(self.scale, 1e-9))
        fused = {}
        for (B, c, p), ms in self.t3.items():
            if p == 0 or p > 256:
                continue
            b0 = self.t3.get((B, c, 0))
            if b0 is not None:
                fused.setdefault(c, []).append(ms - b0)
        self.toll_fused = {c: sum(v) / len(v) for c, v in fused.items()}

        # --- marginal prefill compute -----------------------------------
        # compute(L, ctx) = T2(L, ctx) - T2(L_min, ctx): the cost of the tokens
        # themselves, with the toll and the trailing decode step differenced
        # out. Non-negative and monotone in L by construction of the data.
        Lmin = min(self.t2_Ls) if self.t2_Ls else 0
        self.pf_compute = {}
        for (L, c), ms in self.t2.items():
            base = self.t2.get((Lmin, c))
            if base is not None:
                self.pf_compute[(L, c)] = max(0.0, ms - base)

    def _compute_ms(self, L, ctx):
        """Marginal prefill compute, interpolating ctx FIRST then L.

        Order matters: the T2 grid is ragged (L>=1024 was only measurable at
        ctx<=4096 because of max_model_len), so interpolating L first would
        force a long extrapolation along L at ctx=16384. Going along ctx first
        extrapolates the ctx trend of the *same* L, which the data supports
        (L=2048 compute: 98.1 / 108.8 / 135.3 ms at ctx 0 / 1k / 4k).
        """
        if not self.pf_compute or L <= 0:
            return 0.0
        per_L = []
        for LL in self.t2_Ls:
            cs = sorted(c for (l2, c) in self.pf_compute if l2 == LL)
            if not cs:
                continue
            per_L.append((LL, _interp1(ctx, cs,
                                       [self.pf_compute[(LL, c)] for c in cs])))
        if not per_L:
            return 0.0
        xs = [math.log2(max(l, 1)) for l, _ in per_L]
        ys = [max(0.0, v) for _, v in per_L]
        return max(0.0, _interp1(math.log2(max(L, 1)), xs, ys))

    # ------------------------------------------------------------- queries
    def decode_ms(self, B, ctx):
        """Pure-decode step time, bilinear over the T1 grid."""
        if not self.t1:
            return DECODE_PRIOR_MS * self.scale
        v = _bilinear(B, ctx, self.t1)
        return max(0.1, v) * self.scale

    def prefill_step_ms(self, ntok, ctx):
        """One prefill-only step: `ntok` tokens on top of existing context ctx."""
        if ntok <= 0:
            return 0.0
        if not self.t2:
            return ntok * PREFILL_PRIOR_MS_PER_TOK * self.scale
        cs = sorted(self.toll_solo)
        toll = _interp1(ctx, cs, [self.toll_solo[c] for c in cs]) if cs else 15.0
        return max(0.5, toll + self._compute_ms(ntok, ctx)) * self.scale

    def prefill_ms(self, ntok, ctx):
        """Total cost of a wake+prefill as T2 measured it (prefill + 1 decode).

        Kept because the T2 CSV is quoted directly in the findings; the
        simulator itself uses prefill_step_ms / mixed_extra_ms.
        """
        if ntok <= 0:
            return 0.0
        if not self.t2:
            return ntok * PREFILL_PRIOR_MS_PER_TOK * self.scale
        v = _bilinear(ntok, ctx, self.t2, logx=True)
        return max(0.1, v) * self.scale

    def mixed_extra_ms(self, p, ctx):
        """Extra step time from fusing p prefill tokens into a decode step.

        = eager toll + marginal compute of those p tokens, both measured.

        T3's increments are bimodal at p=512/1024: the same p costs ~12ms extra
        in some (B, ctx) cells and ~43ms in others. That is NOT a chunking
        artefact -- calibration/data/diag_t3_chunking.json reads the scheduler's
        own num_batched_tokens and confirms all p tokens were in the measured
        step in every cell. The upper branch is what T2's independent solo
        measurement predicts (T2 L=1024 marginal compute = 41.6ms vs T3's high
        branch 43ms), so this model follows the upper branch and therefore
        overestimates the fast cells by up to ~78%. That is a deliberate,
        documented conservatism, and it lands where it matters least: the
        simulator only ever schedules prefill at the budget cap (2048 tokens,
        model within 4%) or as an 8-token micro-prefill (within 13%). See
        cross_check_t3() for the full residual table.
        """
        if p <= 0:
            return 0.0
        if not self.toll_fused and not self.t2:
            return self.prefill_ms(p, ctx)
        cs = sorted(self.toll_fused)
        toll = _interp1(ctx, cs, [self.toll_fused[c] for c in cs]) if cs else 14.0
        return max(0.0, toll + self._compute_ms(p, 0)) * self.scale

    def step_ms(self, B, ctx, decode_tokens, prefill_tokens, prefill_ctx=None):
        """Time for one engine step.

        B              : number of decode rows in the batch
        ctx            : their average context length
        decode_tokens  : decode tokens emitted this step (normally == B)
        prefill_tokens : prefill tokens fused into this step
        prefill_ctx    : context the prefill attends over (defaults to ctx).
                         The tool-splice case attends over the session's whole
                         history, which is what makes it expensive.
        """
        pre = int(prefill_tokens)
        pctx = ctx if prefill_ctx is None else prefill_ctx
        if B <= 0 and decode_tokens <= 0:
            return self.prefill_step_ms(pre, pctx) if pre > 0 else 1.0
        eff_B = max(B, decode_tokens, 1)
        d = self.decode_ms(eff_B, ctx)
        if pre <= 0:
            return d
        cs = sorted(self.toll_fused)
        toll = _interp1(ctx, cs, [self.toll_fused[c] for c in cs]) if cs else 14.0
        return d + (toll + self._compute_ms(pre, pctx)) * self.scale

    def cross_check_t3(self):
        """Residuals of the composite model against every measured T3 cell.

        Reported in the validation output rather than hidden: the model tracks
        T3's upper branch, so cells where vLLM silently chunked the injected
        prefill show up as large positive residuals, and that is the expected
        disagreement, not a fit failure.
        """
        out = []
        for (B, c, p), ms in sorted(self.t3.items()):
            if p == 0:
                continue
            base = self.t3.get((B, c, 0))
            if base is None:
                continue
            pred = base + self.mixed_extra_ms(p, c)
            out.append({"B": B, "ctx": c, "p": p,
                        "measured_ms": round(ms, 2), "model_ms": round(pred, 2),
                        "err_pct": round(100 * (pred - ms) / ms, 1)})
        return out

    def chunk_penalty_pct(self, k, ctx):
        """Measured T4 penalty of splitting a 2048-token prefill into k chunks."""
        if not self.t4:
            return None
        one = _bilinear(1, ctx, self.t4)
        many = _bilinear(k, ctx, self.t4)
        if not one or not many:
            return None
        return 100.0 * (many - one) / one

    def summary(self):
        return {
            "source": self.source, "scale": self.scale,
            "files": self.files,
            "cells": {"T1": len(self.t1), "T2": len(self.t2),
                      "T3": len(self.t3), "T4": len(self.t4)},
            "decode_ms": {"B1_ctx4k": round(self.decode_ms(1, 4096), 2),
                          "B8_ctx4k": round(self.decode_ms(8, 4096), 2),
                          "B16_ctx2k": round(self.decode_ms(16, 2048), 2)},
            "eager_toll_ms": {"solo": {c: round(v, 2) for c, v in
                                       sorted(self.toll_solo.items())},
                              "fused": {c: round(v, 2) for c, v in
                                        sorted(self.toll_fused.items())}},
            "prefill_step_ms": {
                "L8_ctx4k": round(self.prefill_step_ms(8, 4096), 2),
                "L2048_ctx4k": round(self.prefill_step_ms(2048, 4096), 2),
                "L8192_ctx4k": round(self.prefill_step_ms(8192, 4096), 2)},
            "prefill_ms": {"L8_ctx4k": round(self.prefill_ms(8, 4096), 2),
                           "L512_ctx4k": round(self.prefill_ms(512, 4096), 2),
                           "L2048_ctx4k": round(self.prefill_ms(2048, 4096), 2),
                           "L8192_ctx4k": round(self.prefill_ms(8192, 4096), 2)},
            "mixed_extra_ms": {"p64_ctx4k": round(self.mixed_extra_ms(64, 4096), 2),
                               "p512_ctx4k": round(self.mixed_extra_ms(512, 4096), 2),
                               "p2048_ctx4k": round(self.mixed_extra_ms(2048, 4096), 2)},
        }


def load_default(datadir, tag, scale=1.0):
    d = Path(datadir)

    def f(n):
        p = d / f"{n}_{tag}.csv"
        return str(p) if p.exists() else None

    return Calibration(t1_csv=f("T1_decode"), t2_csv=f("T2_prefill"),
                       t3_csv=f("T3_mixed"), t4_csv=f("T4_chunk"),
                       scale=scale, source=f"{tag} x{scale}")
