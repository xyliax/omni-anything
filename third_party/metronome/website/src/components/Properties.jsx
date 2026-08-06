import React, { useEffect, useRef, useState } from 'react'
import { wallRuns } from '../data.js'

// Three defining properties of the collapse: memory-triggered, metastable, silent.
export function Properties() {
  return (
    <div className="cards3" style={{ marginTop: 8 }}>
      <MemoryCard />
      <MetastableCard />
      <SilentCard />
    </div>
  )
}

function MemoryCard() {
  return (
    <div className="prop-card">
      <span className="prop-num">Property 01</span>
      <h3>It's memory, not compute</h3>
      <p>
        Over a 90 s burst the unbounded baseline is flawless past 160 concurrent sessions — there is no
        short-burst capacity problem. The wall is reached by <em>duration</em>: each frame appends KV until the
        block pool saturates. A 90 s test cannot see it.
      </p>
      <div className="prop-visual">
        <BurstVsDuration />
      </div>
    </div>
  )
}

function BurstVsDuration() {
  // tiny inline contrast: burst flat vs duration cliff
  return (
    <svg viewBox="0 0 280 92" width="100%" aria-label="A 90 second burst is flat; a 300 second run hits a cliff.">
      <text x="66" y="12" textAnchor="middle" fontSize="10" fill="#B4AA95" fontFamily="Spline Sans Mono">90 s burst</text>
      <line x1="10" x2="122" y1="76" y2="76" stroke="#5A5240" strokeWidth="1" />
      <path d="M14,62 L118,58" fill="none" stroke="#D55E00" strokeWidth="2" />
      <text x="66" y="90" textAnchor="middle" fontSize="9.5" fill="#7A7260" fontFamily="Spline Sans Mono">flat to N=160 ✓</text>
      <text x="214" y="12" textAnchor="middle" fontSize="10" fill="#B4AA95" fontFamily="Spline Sans Mono">300 s, same N</text>
      <line x1="158" x2="270" y1="76" y2="76" stroke="#5A5240" strokeWidth="1" />
      <path d="M162,62 L226,60 L228,24 L266,24" fill="none" stroke="#D55E00" strokeWidth="2" />
      <text x="214" y="90" textAnchor="middle" fontSize="9.5" fill="#D55E00" fontFamily="Spline Sans Mono">wall ✕</text>
    </svg>
  )
}

function MetastableCard() {
  const [revealed, setRevealed] = useState(0)
  const ref = useRef(null)
  useEffect(() => {
    const obs = new IntersectionObserver((es) => {
      if (es[0].isIntersecting) {
        let i = 0
        const iv = setInterval(() => {
          i++; setRevealed(i)
          if (i >= 40) clearInterval(iv)
        }, 70)
        obs.disconnect()
      }
    }, { threshold: 0.4 })
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [])

  const vanRuns = [...wallRuns.van, ...wallRuns.vanRand]
  const winRuns = [...wallRuns.win, ...wallRuns.winRand]
  return (
    <div className="prop-card" ref={ref}>
      <span className="prop-num">Property 02</span>
      <h3>It's metastable</h3>
      <p>
        Whether a run collapses is a race between two clocks: pool-fill time vs. session length. When they're
        comparable, identical five-minute runs are a coin flip — 4/10 one day, 10/10 in a randomized-order
        replication on another. The rate moves with the day's fill rate; the invariant is that windowed KV
        never tips.
      </p>
      <div className="prop-visual">
        <div className="run-dots" aria-label="Twenty unbounded runs across two batches: fourteen hit the wall. Twenty windowed runs: zero hit the wall.">
          {vanRuns.map((r, i) => (
            <span key={i} className={`run-dot ${i < revealed ? (r.wall ? 'wall' : 'ok') : ''}`}
              style={{
                marginLeft: i === 10 ? 12 : undefined,
                borderColor: i < revealed && !r.wall ? 'rgba(213,94,0,.5)' : undefined,
                background: i < revealed && !r.wall ? 'rgba(213,94,0,.12)' : undefined,
              }} />
          ))}
        </div>
        <div className="run-dots-label">unbounded KV — <b style={{ color: '#D55E00' }}>14/20 runs hit the wall</b> (4/10 fixed order · 10/10 randomized)</div>
        <div className="run-dots" style={{ marginTop: 10 }}>
          {winRuns.map((r, i) => (
            <span key={i} className={`run-dot ${i + 20 < revealed ? 'ok' : ''}`}
              style={{ marginLeft: i === 10 ? 12 : undefined }} />
          ))}
        </div>
        <div className="run-dots-label">Metronome windowed KV — <b style={{ color: '#4DA3D0' }}>0/20, flat in every run</b></div>
      </div>
    </div>
  )
}

function SilentCard() {
  return (
    <div className="prop-card">
      <span className="prop-num">Property 03</span>
      <h3>It's silent</h3>
      <p>
        The stalled engine doesn't miss deadlines — it returns <em>empty frames on time</em>. Latency reads green
        until the step; the deadline-miss counter reads zero <em>during</em> the collapse. The user doesn't hear a
        late response. The call simply goes quiet.
      </p>
      <div className="prop-visual">
        <div className="dash-mock" aria-label="A monitoring dashboard reading healthy while the call is dead.">
          <div className="dash-row"><span>ops dashboard · during collapse</span><span>live</span></div>
          <div className="dash-row"><span>per-frame latency p99</span><span className="dash-ok">under budget</span></div>
          <div className="dash-row"><span>deadline misses</span><span className="dash-ok">0</span></div>
          <div className="dash-row"><span>frames returned on time</span><span className="dash-ok">100%</span></div>
          <div className="dash-quiet">…tokens produced: 0 — the healthy system has stopped talking</div>
        </div>
      </div>
    </div>
  )
}
