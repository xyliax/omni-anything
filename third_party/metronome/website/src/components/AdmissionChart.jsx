import React, { useMemo } from 'react'
import { Chart, nearestIdx } from '../chart/Chart.jsx'
import { linScale, linePath } from '../chart/util.js'
import { admissionTraces, C } from '../data.js'

// The payoff experiment: online AIMD admission discovers N* on the bounded-KV signal.
export function AdmissionChart() {
  const { admitted, cap, shed, latency } = useMemo(() => admissionTraces(), [])
  const W = 860
  const H1 = 300, H2 = 240
  const margin = { top: 20, right: 24, bottom: 40, left: 64 }
  const x = linScale(0, 170, margin.left, W - margin.right)
  const y1 = linScale(0, 330, H1 - margin.bottom, margin.top)
  const y2 = linScale(0, 2200, H2 - margin.bottom, margin.top)

  const hover1 = (dx) => {
    const i = nearestIdx(admitted, dx)
    const ic = cap.length ? nearestIdx(cap, dx) : -1
    const is = nearestIdx(shed, dx)
    return {
      title: `t = ${Math.round(dx)} s`, cx: x(admitted[i].t), py: y1(admitted[i].v),
      items: [
        { color: C.win, label: 'admitted', value: Math.round(admitted[i].v) },
        ic >= 0 && Math.abs(cap[ic].t - dx) < 3 && { color: C.ink, label: 'cap N★', value: Math.round(cap[ic].v) },
        { color: '#8A8171', label: 'shed (cum.)', value: Math.round(shed[is].v) },
      ].filter(Boolean),
    }
  }
  const hover2 = (dx) => {
    const i = nearestIdx(latency, dx)
    return {
      title: `t = ${Math.round(dx)} s`, cx: x(latency[i].t), py: y2(latency[i].v),
      items: [{ color: C.win, label: 'per-frame latency', value: `${Math.round(latency[i].v)} ms` }],
    }
  }

  return (
    <div className="panel panel-pad">
      <div className="fig-title">Admission discovers N★ ≈ 209 — online, from latency alone <span className="fig-tag blue">open-system overload</span></div>
      <div className="fig-sub">512 sessions offered at 8/s against the windowed worker · 600 ms admit target · 2 s deadline. No hand-set capacity number anywhere.</div>

      <Chart width={W} height={H1} margin={margin} x={x} y={y1}
        xTicks={[0, 40, 80, 120, 160]} yTicks={[0, 100, 209, 300]}
        xLabel="" yLabel="sessions" hover={hover1}
        ariaLabel="Admitted sessions climb with arrivals and settle at N star equals 209 while surplus arrivals are shed cleanly.">
        <line x1={x(0)} x2={x(170)} y1={y1(209)} y2={y1(209)} stroke={C.win} strokeWidth="1" strokeDasharray="2 4" />
        {/* shed */}
        <path d={linePath(shed, x, y1)} fill="none" stroke="#8A8171" strokeWidth="1.8" />
        {/* admitted area */}
        <path d={`${linePath(admitted, x, y1)} L${x(170)},${y1(0)} L${x(0)},${y1(0)} Z`} fill={C.win} opacity="0.1" />
        <path d={linePath(admitted, x, y1)} fill="none" stroke={C.win} strokeWidth="2.6" />
        {/* cap */}
        <path d={linePath(cap, x, y1)} fill="none" stroke={C.ink} strokeWidth="1.8" strokeDasharray="7 5" />
        <text x={x(112)} y={y1(232)} fontSize="12.5" fontWeight="600" fill={C.win} fontFamily="Spline Sans Mono">settles at N★ ≈ 209</text>
        <text x={x(112)} y={y1(272)} fontSize="11.5" fill="#8A8171" fontFamily="Spline Sans Mono">cumulative shed (303 rejected cleanly)</text>
        <text x={x(52)} y={y1(150)} fontSize="11.5" fill={C.ink} fontFamily="Spline Sans Mono">controller cap (dashed)</text>
      </Chart>

      <Chart width={W} height={H2} margin={{ ...margin, top: 8 }} x={x} y={y2}
        xTicks={[0, 40, 80, 120, 160]} yTicks={[0, 600, 2000]}
        yFmt={(v) => `${v} ms`}
        xLabel="elapsed time (s)" yLabel="latency" hover={hover2}
        ariaLabel="Per-frame latency probes the 600 millisecond target once during ramp-up then holds far under the 2 second deadline.">
        <line x1={x(0)} x2={x(170)} y1={y2(2000)} y2={y2(2000)} stroke={C.inkSoft} strokeWidth="1.2" strokeDasharray="6 5" />
        <text x={x(4)} y={y2(2000) - 7} fontSize="11" fill={C.inkSoft} fontFamily="Spline Sans Mono">frame deadline 2000 ms</text>
        <line x1={x(0)} x2={x(170)} y1={y2(600)} y2={y2(600)} stroke={C.amber} strokeWidth="1.4" strokeDasharray="7 4" />
        <text x={x(4)} y={y2(600) - 7} fontSize="11" fill={C.amber} fontFamily="Spline Sans Mono">admit target 600 ms</text>
        <path d={linePath(latency, x, y2)} fill="none" stroke={C.win} strokeWidth="2.2" />
        <text x={x(37)} y={y2(880)} fontSize="11.5" fill={C.win} fontFamily="Spline Sans Mono">probes the target once…</text>
        <text x={x(168)} y={y2(260)} textAnchor="end" fontSize="11.5" fill={C.win} fontFamily="Spline Sans Mono">…then steady p99 ≈ 12 ms for the rest of the run</text>
      </Chart>

      <div className="fig-caption">
        <b>And the counterfactual:</b> the <b>identical controller</b> against <b>unbounded</b> KV sees a flat signal
        as sessions pour in, reads it as pure headroom, and keeps admitting — past the concurrency the windowed system
        identified as the limit. By the time latency first grazes the target, the admitted sessions' resident KV is
        already filling the pool; the signal falls <i>back</i> to a few milliseconds, and the run ends pinned at the
        1.6 s wall. Shedding late cannot rescue sessions that are already resident. The dependency runs both ways:
        <b> bounded state makes latency faithful, and a faithful signal is what makes admission converge.</b>
      </div>
    </div>
  )
}
