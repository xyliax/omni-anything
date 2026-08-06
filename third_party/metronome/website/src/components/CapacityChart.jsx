import React from 'react'
import { linScale } from '../chart/util.js'
import { capacity, C } from '../data.js'

// Fresh single-N streaming capacity across four interaction models (90 s bursts).
export function CapacityChart() {
  const W = 860, H = 320
  const margin = { top: 18, right: 40, bottom: 46, left: 230 }
  const x = linScale(0, 176, margin.left, W - margin.right)
  const rowH = (H - margin.top - margin.bottom) / capacity.length

  return (
    <div className="panel panel-pad">
      <div className="fig-title">Fresh streaming capacity across four models <span className="fig-tag blue">one GPU · 90 s bursts</span></div>
      <div className="fig-sub">Concurrent sessions sustained on one RTX PRO 6000 Blackwell, freshly started worker per point. A ▸ means still flat at the largest N tested (lower bound).</div>
      <svg className="chart-svg" viewBox={`0 0 ${W} ${H}`} role="img"
        aria-label="Bar chart of streaming capacity: Qwen3-Omni-30B at least 160 sessions, MiniCPM-o-4.5 about 96, Moshi at least 32, Qwen2.5-Omni-7B 16 to 24.">
        {[0, 32, 64, 96, 128, 160].map((v) => (
          <g key={v}>
            <line x1={x(v)} x2={x(v)} y1={margin.top} y2={H - margin.bottom} stroke="#EAE2D2" strokeDasharray="1 4" />
            <text x={x(v)} y={H - margin.bottom + 20} textAnchor="middle" fontSize="11.5" fill="#8A8171">{v}</text>
          </g>
        ))}
        <line x1={x(0)} x2={x(0)} y1={margin.top} y2={H - margin.bottom} stroke="#C9BFA9" strokeWidth="1.2" />
        {capacity.map((m, i) => {
          const cy = margin.top + rowH * i + rowH / 2
          const bh = 30
          return (
            <g key={m.model}>
              <text x={margin.left - 14} y={cy + 1} textAnchor="end" fontSize="13" fontWeight="600" fill={C.ink} fontFamily="Spline Sans, sans-serif">{m.model}</text>
              <rect x={x(0)} y={cy - bh / 2} width={x(m.n) - x(0)} height={bh} rx="4" fill={C.win} />
              {m.nHigh && (
                <rect x={x(m.n)} y={cy - bh / 2} width={x(m.nHigh) - x(m.n)} height={bh} rx="4" fill={C.win} opacity="0.35" />
              )}
              {m.lowerBound && (
                <path d={`M${x(m.n) + 7},${cy - 7} L${x(m.n) + 17},${cy} L${x(m.n) + 7},${cy + 7} Z`} fill={C.win} />
              )}
              {x(m.n) - x(0) > 400 ? (
                <>
                  <text x={x(m.n) - 12} y={cy + 4} textAnchor="end" fontSize="12" fill="#FFFDF8" fontFamily="Spline Sans Mono">{m.note}</text>
                  <text x={x(m.n) + 26} y={cy + 4} fontSize="12" fill="#55503F" fontFamily="Spline Sans Mono">≥{m.n}</text>
                </>
              ) : (
                <text x={x(m.nHigh || m.n) + (m.lowerBound ? 26 : 10)} y={cy + 4} fontSize="12" fill="#55503F" fontFamily="Spline Sans Mono">
                  {m.lowerBound ? '≥' : m.nHigh ? '' : '~'}{m.n}{m.nHigh ? `–${m.nHigh}` : ''} · {m.note}
                </text>
              )}
            </g>
          )
        })}
        <text x={margin.left + (W - margin.left - margin.right) / 2} y={H - 8} textAnchor="middle" fontSize="12" fill="#55503F">fresh streaming capacity (concurrent sessions, 90 s burst)</text>
      </svg>
      <div className="fig-caption">
        <b>Capacity is set by architecture; the cliff travels with the mechanism.</b> Short-burst capacity tracks
        audio-encoder weight, MoE sparsity, and frame budget — Qwen2.5-Omni-7B is bound by its heavyweight audio
        encoder while the MoE 30B sustains an order of magnitude more sessions. The collapse, by contrast, follows
        the serving path: it reproduces on MiniCPM-o-4.5 exactly as the first-order model predicts — a dense
        backbone with 1 s frames fills its pool in under two minutes, a fifth of the ten-minute session, so the
        collapse is <b>deterministic: the run hard-stalls on schedule</b>, deadline-miss counter at zero throughout.
        Windowed KV on the same load holds single-digit-millisecond medians for the full ten minutes.
      </div>
    </div>
  )
}
