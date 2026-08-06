import React from 'react'
import { Metronome } from './Metronome.jsx'

export function Nav() {
  return (
    <nav className="nav">
      <div className="nav-inner">
        <a className="nav-brand" href="#top">
          <svg width="20" height="20" viewBox="0 0 32 32" aria-hidden="true">
            <path d="M10 28 L14 4 L18 4 L22 28 Z" fill="currentColor" />
            <line x1="16" y1="26" x2="24" y2="8" stroke="#D55E00" strokeWidth="2.5" strokeLinecap="round" />
            <circle cx="24" cy="8" r="2.5" fill="#D55E00" />
          </svg>
          Metronome
        </a>
        <div className="nav-links">
          <a href="#workload">Workload</a>
          <a href="#cliff">The cliff</a>
          <a href="#fix">The fix</a>
          <a href="#results">Results</a>
          <a href="#beyond">Beyond voice</a>
          <a className="nav-cta" href="https://github.com/19PINE-AI/metronome" target="_blank" rel="noreferrer">Code ↗</a>
        </div>
      </div>
    </nav>
  )
}

export function Hero() {
  return (
    <header className="hero" id="top">
      <div className="hero-grid">
        <div>
          <div className="hero-kicker">Real-time interaction model serving</div>
          <h1>
            Bound the cache,<br />
            <span className="accent">keep the beat.</span>
          </h1>
          <p className="hero-sub">
            Voice-native models like Moshi, MiniCPM&#8209;o, and Qwen&#8209;Omni — and frontier interaction
            models like Thinking Machines Lab's — turn LLM serving into a{' '}
            <strong>periodic real-time task</strong> — and under sustained load, that task doesn't slow down
            gracefully. It <strong>falls off a cliff</strong>: silently, unpredictably, mid-call.{' '}
            <strong>Metronome</strong> shows that one move fixes it — bound each session's resident KV cache —
            and latency starts telling the truth.
          </p>
          <div className="hero-meta">
            <span><b>Jiaying Meng</b> · Independent Researcher</span>
            <span><b>Bojie Li</b> · Pine AI</span>
          </div>
          <div className="hero-actions">
            <a className="btn primary" href="#cliff">See the collapse ↓</a>
            <a className="btn" href="https://arxiv.org/abs/2607.02640" target="_blank" rel="noreferrer">Paper (arXiv) ↗</a>
          </div>
        </div>
        <div className="hero-instrument">
          <Metronome size={290} period={2} />
        </div>
      </div>
    </header>
  )
}

export function StatBand() {
  const stats = [
    { v: <><span className="van">14/20</span> vs <span className="win">0/20</span></>, l: 'five-minute runs that collapse across two batches: unbounded KV vs Metronome, identical stack and load' },
    { v: <>2 ms <span style={{ fontWeight: 400 }}>→</span> <span className="van">1.6 s</span></>, l: 'the cliff: per-frame latency jumps in a single step when the KV pool saturates' },
    { v: <span className="win">N★ ≈ 209</span>, l: 'schedulable concurrency discovered online by AIMD admission — no hand-set capacity' },
    { v: <>±<span style={{ fontVariantNumeric: 'tabular-nums' }}>3%</span></>, l: 'a first-order model predicts the collapse time on Qwen3-Omni-30B (145 s predicted vs 148 s measured)' },
  ]
  return (
    <div className="stats">
      <div className="stats-inner">
        {stats.map((s, i) => (
          <div className="stat" key={i}>
            <div className="stat-value">{s.v}</div>
            <div className="stat-label">{s.l}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
