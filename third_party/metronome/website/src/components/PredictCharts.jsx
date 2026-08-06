import React from 'react'
import { Chart } from '../chart/Chart.jsx'
import { linScale, linePath } from '../chart/util.js'
import { C, predictFill, plateauVsN } from '../data.js'

// (a) linear pool fill => saturation time is predictable
export function PredictFill() {
  const W = 560, H = 340
  const margin = { top: 24, right: 18, bottom: 46, left: 58 }
  const x = linScale(0, 300, margin.left, W - margin.right)
  const y = linScale(0, 1.08, H - margin.bottom, margin.top)

  const { van30b, vanMcpm, win30bPlateau, winMcpmPlateau } = predictFill
  const fillPath = (t0, tSat) => {
    const pts = [{ t: 0, v: 0 }, { t: t0, v: 0 }, { t: tSat, v: 1 }, { t: 300, v: 1 }]
    return linePath(pts, x, y)
  }
  const plateauPath = (t0, tSat, plat) => {
    const tKnee = t0 + plat * (tSat - t0)
    const pts = [{ t: 0, v: 0 }, { t: t0, v: 0 }, { t: tKnee, v: plat }, { t: 300, v: plat }]
    return linePath(pts, x, y)
  }

  return (
    <div className="panel panel-pad">
      <div className="fig-title">Linear fill ⇒ the stall time is predictable <span className="fig-tag blue">first-order model</span></div>
      <div className="fig-sub">ρ(t) = ρ₀ + N·r·t — fit r on the early trace, predict the crash.</div>
      <Chart width={W} height={H} margin={margin} x={x} y={y}
        xTicks={[0, 100, 200, 300]} yTicks={[0, 0.25, 0.5, 0.75, 1]}
        yFmt={(v) => v.toFixed(2)}
        xLabel="elapsed session time (s)" yLabel="KV-pool occupancy"
        ariaLabel="Pool occupancy rises linearly to capacity for unbounded KV; a straight-line fit predicts the stall within a few percent. Windowed occupancy plateaus far below capacity.">
        <line x1={x(0)} x2={x(300)} y1={y(1)} y2={y(1)} stroke="#8A8171" strokeWidth="1.2" strokeDasharray="6 5" />
        <text x={x(296)} y={y(1) - 7} textAnchor="end" fontSize="11" fill={C.inkMute}>pool capacity</text>

        {/* unbounded fills */}
        <path d={fillPath(van30b.t0, van30b.tSat)} fill="none" stroke={C.van} strokeWidth="2.4" />
        <path d={fillPath(vanMcpm.t0, vanMcpm.tSat)} fill="none" stroke={C.van} strokeWidth="2" strokeDasharray="7 5" />
        {/* windowed plateaus */}
        <path d={plateauPath(van30b.t0, van30b.tSat, win30bPlateau)} fill="none" stroke={C.win} strokeWidth="2.4" />
        <path d={plateauPath(vanMcpm.t0, vanMcpm.tSat, winMcpmPlateau)} fill="none" stroke={C.win} strokeWidth="2" strokeDasharray="7 5" />

        {/* predicted (o) vs measured (x) stalls */}
        <PredMark x={x(van30b.predicted)} y={y(1)} type="o" />
        <PredMark x={x(van30b.tSat)} y={y(1)} type="x" />
        <PredMark x={x(vanMcpm.predicted)} y={y(1)} type="o" />
        <PredMark x={x(vanMcpm.tSat)} y={y(1)} type="x" />
        <text x={x(152)} y={y(0.62)} fontSize="11.5" fill={C.van} fontFamily="Spline Sans Mono">30B: predicted 145 s,</text>
        <text x={x(152)} y={y(0.55)} fontSize="11.5" fill={C.van} fontFamily="Spline Sans Mono">measured 148 s</text>
        <text x={x(118)} y={y(0.88)} fontSize="11.5" fill={C.van} fontFamily="Spline Sans Mono" textAnchor="end">MiniCPM-o: 99 s vs 114 s</text>
        <text x={x(295)} y={y(win30bPlateau) + 16} textAnchor="end" fontSize="11.5" fill={C.win} fontFamily="Spline Sans Mono">windowed: plateau, never saturates</text>
      </Chart>
      <div className="legend-row">
        <span className="legend-item"><span className="legend-swatch" style={{ background: C.van }} />unbounded (solid 30B N=128, dashed MiniCPM N=96)</span>
        <span className="legend-item"><span className="legend-swatch" style={{ background: C.win }} />windowed</span>
        <span className="legend-item">○ predicted · ✕ measured stall</span>
      </div>
      <div className="fig-caption">
        <b>The coin flip, explained.</b> A run collapses iff t<sub>sat</sub> = (1−ρ₀)/(N·r) is shorter than the
        session. Where the two clocks are comparable, the day's fill rate r decides the race — 4/10 in one
        batch, 10/10 in a randomized-order replication. A faster-filling configuration (MiniCPM-o: dense
        backbone, 1 s frames) sits far below the boundary and collapses <b>every</b> run.
      </div>
    </div>
  )
}

function PredMark({ x, y, type }) {
  return type === 'o'
    ? <circle cx={x} cy={y} r="5" fill="none" stroke={C.ink} strokeWidth="1.6" />
    : <g stroke={C.ink} strokeWidth="1.8"><line x1={x - 4.5} y1={y - 4.5} x2={x + 4.5} y2={y + 4.5} /><line x1={x - 4.5} y1={y + 4.5} x2={x + 4.5} y2={y - 4.5} /></g>
}

// (b) bounded state: memory becomes a provisionable linear budget
export function PredictPlateau() {
  const W = 560, H = 340
  const margin = { top: 24, right: 20, bottom: 46, left: 58 }
  const x = linScale(0, 560, margin.left, W - margin.right)
  const y = linScale(0, 108, H - margin.bottom, margin.top)
  const { points, slopePctPerSession, ceiling, nStar } = plateauVsN

  return (
    <div className="panel panel-pad">
      <div className="fig-title">Bounded state: memory becomes a budget <span className="fig-tag blue">provisionable</span></div>
      <div className="fig-sub">Windowed plateau occupancy vs. concurrency N (W = 1024).</div>
      <Chart width={W} height={H} margin={margin} x={x} y={y}
        xTicks={[0, 128, 256, 384, 496]} yTicks={[0, 25, 50, 75, 100]}
        yFmt={(v) => `${v}%`}
        xLabel="concurrent sessions N" yLabel="plateau occupancy"
        ariaLabel="Windowed plateau occupancy is linear in N, extrapolating to a memory ceiling of about 500 sessions, well above the deadline-schedulable 209.">
        <line x1={x(0)} x2={x(560)} y1={y(100)} y2={y(100)} stroke="#8A8171" strokeWidth="1.2" strokeDasharray="6 5" />
        {/* extrapolation line */}
        <line x1={x(0)} y1={y(0)} x2={x(ceiling)} y2={y(100)} stroke={C.inkMute} strokeWidth="1.3" strokeDasharray="2 5" />
        {/* N* deadline line */}
        <line x1={x(nStar)} x2={x(nStar)} y1={y(0)} y2={y(88)} stroke={C.amber} strokeWidth="1.6" strokeDasharray="7 4" />
        <text x={x(nStar) - 8} y={y(76)} textAnchor="end" fontSize="11.5" fill={C.amber} fontFamily="Spline Sans Mono">deadline binds first:</text>
        <text x={x(nStar) - 8} y={y(69)} textAnchor="end" fontSize="11.5" fill={C.amber} fontFamily="Spline Sans Mono">admission N★ ≈ 209</text>
        {/* measured points */}
        {points.map((p) => (
          <circle key={p.n} cx={x(p.n)} cy={y(p.occ)} r="6.5" fill={C.win} stroke="#FFFDF8" strokeWidth="2" />
        ))}
        {/* ceiling marker */}
        <circle cx={x(ceiling)} cy={y(100)} r="6" fill="none" stroke={C.ink} strokeWidth="1.6" />
        <text x={x(ceiling) - 10} y={y(100) + 22} textAnchor="end" fontSize="11.5" fill={C.inkSoft} fontFamily="Spline Sans Mono">memory ceiling ≈ 496 sessions</text>
        <text x={x(150)} y={y(14)} fontSize="11.5" fill={C.win} fontFamily="Spline Sans Mono">~0.2% of pool per session</text>
      </Chart>
      <div className="fig-caption">
        <b>The regime flips.</b> With bounded state, occupancy is linear in N and extrapolates to a hard ceiling of
        ≈500 resident sessions — more than double the deadline-schedulable N★≈209. Bounded-KV serving is
        <b> compute-limited</b>: the deadline binds long before memory. The exact reverse of the vanilla failure,
        where memory kills sessions whose compute the GPU could easily carry.
      </div>
    </div>
  )
}
