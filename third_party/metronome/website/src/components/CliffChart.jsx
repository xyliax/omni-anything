import React, { useMemo } from 'react'
import { Chart, nearestIdx } from '../chart/Chart.jsx'
import { linScale, logScale, linePath, usePlayback, fmtClock } from '../chart/util.js'
import { PlayBar } from './PlayBar.jsx'
import { headlineTraces, C, LABEL_VAN, LABEL_WIN } from '../data.js'

const DUR = 14 // s of animation for the 300 s call

// The headline figure, animated: one five-minute call at N=128, per-frame latency.
export function CliffChart() {
  const { van, win } = useMemo(() => headlineTraces(), [])
  const [tp, playing, ctl] = usePlayback(DUR, 1)
  const tCall = (tp / DUR) * 300

  const W = 860, H = 400
  const margin = { top: 26, right: 24, bottom: 46, left: 64 }
  const x = linScale(0, 300, margin.left, W - margin.right)
  const y = logScale(1, 3000, H - margin.bottom, margin.top)

  const vanVis = van.filter((p) => p.t <= tCall)
  const winVis = win.filter((p) => p.t <= tCall)
  const cliffHit = tCall >= 180

  const hover = (dx) => {
    const iv = nearestIdx(van, dx), iw = nearestIdx(win, dx)
    if (van[iv].t > tCall && win[iw].t > tCall) return null
    return {
      title: `t = ${Math.round(dx)} s`,
      cx: x(van[iv].t),
      px: x(van[iv].t), py: y(Math.max(van[iv].v, win[iw].v)),
      items: [
        van[iv].t <= tCall && { color: C.van, label: 'unbounded', value: van[iv].v >= 1000 ? `${(van[iv].v / 1000).toFixed(1)} s` : `${van[iv].v.toFixed(1)} ms` },
        win[iw].t <= tCall && { color: C.win, label: 'windowed', value: `${win[iw].v.toFixed(1)} ms` },
      ].filter(Boolean),
    }
  }

  return (
    <div className="panel panel-pad" ref={ctl.hostRef}>
      <div className="fig-title">One five-minute call, 128 concurrent sessions <span className="fig-tag">Qwen3-Omni-30B · live replay</span></div>
      <div className="fig-sub">Per-frame latency, log scale. Both policies serve the identical stack, model, and audio.</div>

      <Chart
        width={W} height={H} margin={margin} x={x} y={y} dark
        xTicks={[0, 50, 100, 150, 200, 250, 300]}
        yTicks={[1, 10, 100, 1000]}
        yFmt={(v) => (v >= 1000 ? `${v / 1000} s` : `${v} ms`)}
        xLabel="elapsed time in the call (s)" yLabel="per-frame latency"
        hover={hover}
        ariaLabel="Line chart: unbounded KV latency jumps from a few milliseconds to a 1.6 second wall at about 180 seconds; Metronome windowed KV stays flat for the whole call."
      >
        {/* 2 s deadline */}
        <line x1={x(0)} x2={x(300)} y1={y(2000)} y2={y(2000)} stroke="#8A8171" strokeWidth="1.3" strokeDasharray="6 5" />
        <text x={x(296)} y={y(2000) - 8} textAnchor="end" fontSize="11.5" fill="#B4AA95">2 s frame deadline — miss it and the call stutters</text>

        <path d={linePath(winVis, x, y)} fill="none" stroke={C.win} strokeWidth="2.4" strokeLinejoin="round" />
        <path d={linePath(vanVis, x, y)} fill="none" stroke={C.van} strokeWidth="2.4" strokeLinejoin="round" />

        {/* live cursor dots */}
        {vanVis.length > 0 && tCall < 300 && (
          <>
            <circle cx={x(vanVis[vanVis.length - 1].t)} cy={y(vanVis[vanVis.length - 1].v)} r="4.5" fill={C.van} stroke="#16130E" strokeWidth="1.5" />
            <circle cx={x(winVis[winVis.length - 1].t)} cy={y(winVis[winVis.length - 1].v)} r="4.5" fill={C.win} stroke="#16130E" strokeWidth="1.5" />
          </>
        )}

        {/* annotations */}
        {cliffHit && (
          <g style={{ opacity: 1 }}>
            <text x={x(176)} y={y(300)} textAnchor="end" fontSize="13" fontWeight="600" fill={C.van} fontFamily="Spline Sans, sans-serif">latency cliff: the call freezes</text>
            <path d={`M${x(178)},${y(260)} Q${x(184)},${y(140)} ${x(183)},${y(700)}`} fill="none" stroke={C.van} strokeWidth="1.3" markerEnd="url(#arrVan)" />
            <text x={x(246)} y={y(1600) + 20} textAnchor="middle" fontSize="12" fill={C.van}>frozen at the wall — engine stops producing tokens</text>
          </g>
        )}
        {tCall > 120 && (
          <text x={x(115)} y={y(18)} fontSize="13" fontWeight="600" fill="#4DA3D0" fontFamily="Spline Sans, sans-serif">flat, a few ms: stays on beat</text>
        )}
        <defs>
          <marker id="arrVan" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto">
            <path d="M0,0 L7,3.5 L0,7 Z" fill={C.van} />
          </marker>
        </defs>
      </Chart>

      <div className="legend-row">
        <span className="legend-item"><span className="legend-swatch" style={{ background: C.van }} />{LABEL_VAN}</span>
        <span className="legend-item"><span className="legend-swatch" style={{ background: C.win }} />{LABEL_WIN}</span>
      </div>
      <PlayBar t={tp} dur={DUR} playing={playing} ctl={ctl} clock={`${fmtClock(tCall)} / 5:00`} note="hover the chart to inspect any frame" />
      <div className="fig-caption">
        <b>No warning, no slope.</b> For three minutes the unbounded baseline is indistinguishable from Metronome —
        a few milliseconds per frame, hundreds of times under budget. Then, in a single step, it pins at a
        ~1.6 s wall where the stalled engine stops producing tokens. The windowed policy serves the same call flat
        to the end. (The wall sits at 0.8× the 2 s budget because the worker caps how long a tick waits for tokens.)
      </div>
    </div>
  )
}
