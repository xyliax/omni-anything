import React, { useRef, useState, useCallback } from 'react'

// Shared SVG chart frame with grid, axes and a crosshair-tooltip hover layer.
// Children render marks inside the plot area; hover items come from `hoverData`.
export function Chart({
  width = 720, height = 340,
  margin = { top: 18, right: 20, bottom: 42, left: 58 },
  x, y, // scale functions with .domain
  xTicks = [], yTicks = [],
  xLabel, yLabel,
  xFmt = (v) => v, yFmt = (v) => v,
  hover, // (dataX) => ({ items: [{color,label,value}], px, py })
  dark = false,
  children,
  ariaLabel,
}) {
  const hostRef = useRef(null)
  const [tt, setTt] = useState(null)
  const iw = width - margin.left - margin.right
  const ih = height - margin.top - margin.bottom
  const gridC = dark ? '#383226' : '#EAE2D2'
  const axisC = dark ? '#5A5240' : '#C9BFA9'
  const textC = dark ? '#B4AA95' : '#8A8171'
  const labC = dark ? '#D8CFBB' : '#55503F'

  const onMove = useCallback((e) => {
    if (!hover || !hostRef.current) return
    const rect = hostRef.current.getBoundingClientRect()
    const sx = width / rect.width
    const px = (e.clientX - rect.left) * sx
    if (px < margin.left || px > width - margin.right) { setTt(null); return }
    const [d0, d1] = x.domain
    const dataX = d0 + ((px - margin.left) / iw) * (d1 - d0)
    const h = hover(dataX)
    if (h) setTt({ ...h, screenX: (h.px ?? px) / sx, screenY: ((h.py ?? margin.top) / height) * rect.height })
    else setTt(null)
  }, [hover, width, height, margin.left, margin.right, iw, x])

  return (
    <div ref={hostRef} style={{ position: 'relative' }} onMouseMove={onMove} onMouseLeave={() => setTt(null)}>
      <svg className="chart-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={ariaLabel}>
        {/* grid */}
        {yTicks.map((v) => (
          <line key={`gy${v}`} x1={margin.left} x2={width - margin.right} y1={y(v)} y2={y(v)}
            stroke={gridC} strokeWidth="1" strokeDasharray="1 4" />
        ))}
        {/* axes */}
        <line x1={margin.left} x2={width - margin.right} y1={height - margin.bottom} y2={height - margin.bottom} stroke={axisC} strokeWidth="1.2" />
        <line x1={margin.left} x2={margin.left} y1={margin.top} y2={height - margin.bottom} stroke={axisC} strokeWidth="1.2" />
        {xTicks.map((v) => (
          <g key={`tx${v}`}>
            <line x1={x(v)} x2={x(v)} y1={height - margin.bottom} y2={height - margin.bottom + 5} stroke={axisC} strokeWidth="1.2" />
            <text x={x(v)} y={height - margin.bottom + 19} textAnchor="middle" fontSize="11.5" fill={textC}>{xFmt(v)}</text>
          </g>
        ))}
        {yTicks.map((v) => (
          <text key={`ty${v}`} x={margin.left - 9} y={y(v) + 3.6} textAnchor="end" fontSize="11.5" fill={textC}>{yFmt(v)}</text>
        ))}
        {xLabel && <text x={margin.left + iw / 2} y={height - 6} textAnchor="middle" fontSize="12" fill={labC}>{xLabel}</text>}
        {yLabel && (
          <text x={13} y={margin.top + ih / 2} textAnchor="middle" fontSize="12" fill={labC}
            transform={`rotate(-90 13 ${margin.top + ih / 2})`}>{yLabel}</text>
        )}
        {/* plot */}
        <g>{children}</g>
        {/* crosshair */}
        {tt && (
          <line x1={tt.cx} x2={tt.cx} y1={margin.top} y2={height - margin.bottom}
            stroke={dark ? '#6B624C' : '#B9AF98'} strokeWidth="1" strokeDasharray="3 3" />
        )}
      </svg>
      {tt && (
        <div className="tooltip" style={{ left: tt.screenX, top: tt.screenY }}>
          <span className="tt-dim">{tt.title}</span>
          {tt.items.map((it, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <span style={{ width: 8, height: 8, borderRadius: 2, background: it.color, flex: '0 0 auto' }} />
              <span className="tt-dim">{it.label}</span>
              <span style={{ marginLeft: 'auto', paddingLeft: 8 }}>{it.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function nearestIdx(arr, t) {
  let best = 0, bd = Infinity
  for (let i = 0; i < arr.length; i++) {
    const d = Math.abs(arr[i].t - t)
    if (d < bd) { bd = d; best = i }
  }
  return best
}
