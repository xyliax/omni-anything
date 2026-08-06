import React, { useEffect, useRef, useState } from 'react'
import { C } from '../data.js'

// The sink-anchored bound, animated: tokens append every frame; the engine
// attends over — and retains — the last W tokens PLUS the first few pinned
// sink tokens. Blocks between sinks and window are freed.
export function WindowAnim() {
  const [tick, setTick] = useState(0)
  const hostRef = useRef(null)
  const [running, setRunning] = useState(false)

  useEffect(() => {
    const obs = new IntersectionObserver((es) => setRunning(es[0].isIntersecting), { threshold: 0.3 })
    if (hostRef.current) obs.observe(hostRef.current)
    return () => obs.disconnect()
  }, [])

  useEffect(() => {
    if (!running) return
    const iv = setInterval(() => setTick((t) => t + 1), 700)
    return () => clearInterval(iv)
  }, [running])

  const W = 12 // window size in cells
  const SINKS = 2 // pinned sink blocks
  const total = 30 // visible token slots
  const grown = Math.min(total + 200, 4 + tick) // tokens generated so far
  const winStart = Math.max(0, grown - W)

  // Strip layout: once the stream outgrows the strip, the first SINKS cells
  // stay pinned at the left, a gap slot marks the elided freed region, and
  // the rest of the strip shows the most recent tokens.
  const scrolled = grown > total
  const stripN = scrolled ? total - SINKS - 1 : total
  const first = scrolled ? grown - stripN : 0
  const xoff = scrolled ? (SINKS + 1) * 28 : 0

  const cellStyle = (idx) => {
    const inWin = idx >= winStart
    const isSink = idx < SINKS
    if (inWin) return { fill: C.win, opacity: idx === grown - 1 ? 1 : 0.82, stroke: C.win, freed: false }
    if (isSink) return { fill: C.sink, opacity: 0.9, stroke: C.sink, freed: false }
    return { fill: '#E8E0CF', opacity: 0.35, stroke: '#C9BFA9', freed: true }
  }

  const cell = (idx, xp, key) => {
    const st = cellStyle(idx)
    return (
      <g key={key}>
        <rect x={xp} y={48} width={24} height={34} rx={4}
          fill={st.fill} opacity={st.opacity}
          stroke={st.stroke} strokeWidth={idx === grown - 1 ? 2 : 0.8}
          style={{ transition: 'fill .4s, opacity .4s' }} />
        {st.freed && (
          <g stroke="#B0A68E" strokeWidth="1.2">
            <line x1={xp + 5} y1={53} x2={xp + 19} y2={77} />
            <line x1={xp + 5} y1={77} x2={xp + 19} y2={53} />
          </g>
        )}
      </g>
    )
  }

  return (
    <div className="panel panel-pad" ref={hostRef}>
      <div className="fig-title">The sink-anchored bound, frame by frame <span className="fig-tag blue">no re-encode, ever</span></div>
      <div className="fig-sub">Each cell is a KV block of the session's context. A new chunk arrives every frame.</div>

      <svg className="chart-svg" viewBox="0 0 860 190" style={{ marginTop: 14 }}
        aria-label="A token stream grows each frame. The engine retains the most recent W tokens plus the first few pinned sink tokens; blocks between them are freed.">
        {/* logical context ruler */}
        <text x="846" y="14" textAnchor="end" fontSize="11.5" fill={C.inkMute} fontFamily="Spline Sans Mono">logical context: grows without bound — token #{grown * 64}</text>

        {/* pinned sink cells + elision gap (once the strip scrolls) */}
        {scrolled && (
          <g>
            {Array.from({ length: SINKS }, (_, i) => cell(i, 14 + i * 28, `s${i}`))}
            <text x={14 + SINKS * 28 + 10} y={70} fontSize="14" fill={C.inkMute} fontFamily="Spline Sans Mono">⋯</text>
            <path d={`M${11},42 L${11},36 L${14 + SINKS * 28 - 4 + 3},36 L${14 + SINKS * 28 - 4 + 3},42`} fill="none" stroke={C.sink} strokeWidth="1.8" />
            <text x={14 + SINKS * 14 - 2} y={30} textAnchor="middle" fontSize="12" fontWeight="600" fill={C.sink} fontFamily="Spline Sans Mono">sinks</text>
          </g>
        )}

        {/* token cells */}
        {Array.from({ length: stripN }, (_, i) => {
          const idx = first + i
          if (idx >= grown) return null
          return cell(idx, 14 + xoff + i * 28, idx)
        })}

        {/* window bracket */}
        {(() => {
          const wi0 = Math.max(0, winStart - first)
          const x0 = 14 + xoff + wi0 * 28 - 3
          const x1 = 14 + xoff + Math.min(stripN, grown - first) * 28 - 4 + 3
          return (
            <g>
              <path d={`M${x0},42 L${x0},36 L${x1},36 L${x1},42`} fill="none" stroke={C.win} strokeWidth="1.8" />
              <text x={(x0 + x1) / 2} y={30} textAnchor="middle" fontSize="12" fontWeight="600" fill={C.win} fontFamily="Spline Sans Mono">resident window: last W tokens</text>
            </g>
          )
        })()}
        {/* freed label */}
        {winStart > SINKS && (
          <text x={14} y={104} fontSize="11.5" fill={C.inkMute} fontFamily="Spline Sans Mono">✕ freed KV blocks — returned to the pool the moment they fall between the sinks and the window</text>
        )}
        {/* incoming chunk */}
        <g transform={`translate(${14 + xoff + Math.min(stripN - 1, grown - 1 - first) * 28 + 34}, 52)`}>
          <text x="0" y="18" fontSize="11.5" fill={C.van} fontFamily="Spline Sans Mono">← new audio chunk, every frame</text>
        </g>

        {/* memory readout bars */}
        <g transform="translate(14,136)">
          <text x="0" y="0" fontSize="11.5" fill={C.inkSoft} fontFamily="Spline Sans Mono">resident KV memory:</text>
          <rect x="170" y="-10" width="380" height="13" rx="3" fill="#EDE6D8" />
          <rect x="170" y="-10" width={Math.min(380, (Math.min(grown, W) / total) * 380 * (total / W) * 0.4)} height="13" rx="3" fill={C.win} style={{ transition: 'width .4s' }} />
          <text x="562" y="0" fontSize="11.5" fill={C.win} fontFamily="Spline Sans Mono">{grown > W ? 'capped at W + sinks — flat forever' : 'filling…'}</text>
          <text x="0" y="26" fontSize="11.5" fill={C.inkSoft} fontFamily="Spline Sans Mono">without the bound:</text>
          <rect x="170" y="16" width="380" height="13" rx="3" fill="#EDE6D8" />
          <rect x="170" y="16" width={Math.min(380, grown * 4.2)} height="13" rx="3" fill={C.van} style={{ transition: 'width .4s' }} />
          {grown * 4.2 >= 380 && <text x="562" y="26" fontSize="11.5" fill={C.van} fontFamily="Spline Sans Mono">pool exhausted → stall</text>}
        </g>
      </svg>

      <div className="fig-caption">
        <b>Activating a dormant path — and completing it.</b> vLLM already ships sliding-window attention — windowed
        masks plus a KV spec that frees blocks behind the window — but only for models that <i>declare</i> a window,
        and interaction models don't. Metronome installs W on the decoder-attention layers at construction time and
        adds the sink half: the KV manager pins each session's first blocks and the attention mask admits
        [0,&thinsp;S)&thinsp;∪&thinsp;[t−W,&thinsp;t], keeping the tokens that full-attention backbones anchor their
        softmax on — two KV blocks per session, latency-neutral. The obvious alternative — recycling the request at
        window boundaries in the application — pays a periodic re-encode that grows over the call. The in-engine
        bound strictly dominates it, and a generous window is free: latency is unchanged up to ~80 s of context.
      </div>
    </div>
  )
}
