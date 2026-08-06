import React from 'react'
import { Chart } from '../chart/Chart.jsx'
import { linScale, linePath } from '../chart/util.js'
import { longHorizon, C, LABEL_VAN } from '../data.js'

const SERIES_STYLE = {
  van: { color: C.van, width: 2.6, dash: null },
  w512: { color: '#7FB4D6', width: 1.6, dash: '7 5' },
  w1024: { color: C.win, width: 1.8, dash: null },
  w2048: { color: '#134A6B', width: 1.6, dash: '2 5' },
  tri0: { color: '#928979', width: 1.6, dash: '9 4' },
  sink: { color: C.sink, width: 2.8, dash: null },
}

export function QualityRegimes() {
  return (
    <div className="duo" style={{ marginBottom: 24 }}>
      <div className="regime free">
        <h4>Turn-based decoding: the window alone is quality-free</h4>
        <p>
          The regime a spoken-QA deployment actually runs: each response is an EOS-terminated turn over recent
          context. Under load, <strong>96/96 sessions state the correct answer under both policies</strong>; per-frame
          correctness is statistically indistinguishable (~70% vs ~68%). Each turn's relevant context lies inside
          the window — the sink half isn't even exercised.
        </p>
        <span className="verdict">✓ quality-free — the window suffices</span>
      </div>
      <div className="regime free">
        <h4>Free-running decode: the sinks are load-bearing</h4>
        <p>
          Continuous forced decoding on one resident request. Ablate the sinks and every windowed variant decays
          toward zero with session age — the attention-sink effect: full-attention backbones park softmax mass on
          the first tokens, and a bound that evicts them corrupts generation. <strong>The full bound — window plus
          32 pinned sink tokens (two KV blocks) — holds an age-independent profile at or above the unbounded
          baseline</strong>, at unchanged flat latency.
        </p>
        <span className="verdict">✓ quality-free — with the bound's sink half in place</span>
      </div>
    </div>
  )
}

export function LongHorizonChart() {
  const W = 560, H = 350
  const margin = { top: 22, right: 18, bottom: 46, left: 54 }
  const x = linScale(0, 240, margin.left, W - margin.right)
  const y = linScale(0, 72, H - margin.bottom, margin.top)

  return (
    <div className="panel panel-pad">
      <div className="fig-title">Correctness vs. session age <span className="fig-tag">sink ablation</span></div>
      <div className="fig-sub">Rotating spoken questions, N=32, 300 s, Qwen3-Omni-30B, free-running decode.</div>
      <Chart width={W} height={H} margin={margin} x={x} y={y}
        xTicks={[0, 60, 120, 180, 240]} yTicks={[0, 20, 40, 60]}
        yFmt={(v) => `${v}%`}
        xLabel="session age when the question plays (s)" yLabel="sessions answering correctly"
        ariaLabel="With sinks ablated, every windowed variant declines toward zero as the window slides past the session start; the full bound of window plus 32 pinned sink tokens holds an age-independent profile at or above the unbounded baseline.">
        {longHorizon.series.map((s) => {
          const st = SERIES_STYLE[s.key]
          const hero = s.key === 'sink' || s.key === 'van'
          const pts = longHorizon.ages.map((a, i) => ({ t: a, v: s.values[i] }))
          return (
            <g key={s.key} opacity={hero ? 1 : 0.75}>
              <path d={linePath(pts, x, y)} fill="none" stroke={st.color} strokeWidth={st.width} strokeDasharray={st.dash || undefined} />
              {pts.map((p) => <circle key={p.t} cx={x(p.t)} cy={y(p.v)} r={hero ? 3.4 : 2.6} fill={st.color} stroke="#FFFDF8" strokeWidth="1.4" />)}
            </g>
          )
        })}
        <text x={x(238)} y={y(51)} textAnchor="end" fontSize="11.5" fill={C.sink} fontFamily="Spline Sans Mono">full bound: age-independent</text>
        <text x={x(238)} y={y(17)} textAnchor="end" fontSize="11.5" fill={C.van} fontFamily="Spline Sans Mono">unbounded: steady plateau</text>
      </Chart>
      <div className="legend-row">
        <span className="legend-item"><span className="legend-swatch" style={{ background: C.sink }} />W=1024 + 32 sinks (full bound)</span>
        <span className="legend-item"><span className="legend-swatch" style={{ background: C.van }} />{LABEL_VAN}</span>
        <span className="legend-item"><span className="legend-swatch" style={{ background: C.win }} />W=1024, sinks ablated</span>
        <span className="legend-item"><span className="legend-swatch" style={{ background: '#928979' }} />sink kernel, 0 sinks (control)</span>
        <span className="legend-item"><span className="legend-swatch" style={{ background: '#7FB4D6' }} />W=512</span>
        <span className="legend-item"><span className="legend-swatch" style={{ background: '#134A6B' }} />W=2048</span>
      </div>
    </div>
  )
}

export function ProbeChart() {
  const W = 560, H = 350
  const margin = { top: 22, right: 18, bottom: 64, left: 54 }
  const y = linScale(0, 42, H - margin.bottom, margin.top)
  const groups = longHorizon.probes
  const iw = W - margin.left - margin.right
  const gw = iw / groups.length
  const bw = 30

  return (
    <div className="panel panel-pad">
      <div className="fig-title">What sinks don't buy: memory <span className="fig-tag">late-session probes</span></div>
      <div className="fig-sub">A fresh synthesized-voice question late in the call, and recall of the session's start.</div>
      <svg className="chart-svg" viewBox={`0 0 ${W} ${H}`} role="img"
        aria-label="Bar chart: the full bound answers the late fresh question like the unbounded baseline; sink-ablated windows fail it. The full bound's recall score reflects coherent in-window answers, not beyond-horizon memory.">
        {[0, 10, 20, 30, 40].map((v) => (
          <g key={v}>
            <line x1={margin.left} x2={W - margin.right} y1={y(v)} y2={y(v)} stroke="#EAE2D2" strokeDasharray="1 4" />
            <text x={margin.left - 8} y={y(v) + 3.5} textAnchor="end" fontSize="11.5" fill="#8A8171">{v}%</text>
          </g>
        ))}
        <line x1={margin.left} x2={W - margin.right} y1={y(0)} y2={y(0)} stroke="#C9BFA9" strokeWidth="1.2" />
        {groups.map((g, gi) => {
          const cx = margin.left + gw * gi + gw / 2
          const bars = [
            { v: g.van, c: C.van, l: 'unbounded' },
            { v: g.w1024, c: C.win, l: 'sinks ablated' },
            { v: g.tri0, c: '#928979', l: 'kernel control' },
            { v: g.sink, c: C.sink, l: 'full bound' },
          ]
          return (
            <g key={gi}>
              {bars.map((b, bi) => {
                const bx = cx + (bi - 1.5) * (bw + 6) - bw / 2
                return (
                  <g key={bi}>
                    <rect x={bx} y={y(b.v)} width={bw} height={Math.max(0, y(0) - y(b.v))} rx="4" fill={b.c} />
                    <text x={bx + bw / 2} y={y(b.v) - 6} textAnchor="middle" fontSize="11" fill="#55503F">{b.v > 0 ? `${Math.round(b.v)}%` : '0'}</text>
                  </g>
                )
              })}
              <text x={cx} y={y(0) + 22} textAnchor="middle" fontSize="11" fill="#55503F">{g.probe.split('(')[0].trim()}</text>
              <text x={cx} y={y(0) + 38} textAnchor="middle" fontSize="10.5" fill="#8A8171">({g.probe.split('(')[1]}</text>
            </g>
          )
        })}
      </svg>
      <div className="legend-row">
        <span className="legend-item"><span className="legend-swatch" style={{ background: C.van }} />unbounded</span>
        <span className="legend-item"><span className="legend-swatch" style={{ background: C.win }} />W=1024, sinks ablated</span>
        <span className="legend-item"><span className="legend-swatch" style={{ background: '#928979' }} />sink kernel, 0 sinks</span>
        <span className="legend-item"><span className="legend-swatch" style={{ background: C.sink }} />W=1024 + 32 sinks</span>
      </div>
      <div className="fig-caption">
        The full bound answers the fresh question; the zero-sink control on the identical kernel fails it, so the
        recovery is the sinks, not the kernel change. One honest footnote: the full bound's <b>recall</b> score is
        the lenient keyword scorer crediting coherent in-window answers — probed directly, the model names the most
        recent question as "the first" — because <b>no fixed bound can recall beyond its horizon</b>. That is a task
        for retrieval, not residency.
      </div>
    </div>
  )
}

const SWEEP_ROWS = [
  { ws: '(1024, 0)', pin: '— (sink kernel, 0-sink control)', mid: '→ 0%', fresh: '0%', out: 'decays as the window slides', k: 'bad' },
  { ws: '(1024, 16)', pin: 'chat header', mid: '38–57%', fresh: '45%', out: 'recovers — best', k: 'best' },
  { ws: '(1024, 32)', pin: '+ ~2/3 of first audio', mid: '33–45%', fresh: '21%', out: 'recovers', k: 'good' },
  { ws: '(1024, 42)', pin: '+ complete first audio', mid: '20–32%', fresh: '21%', out: 'degraded: answers the pinned clip', k: 'mid' },
  { ws: '(1024, 58)', pin: '+ instruction, assistant-open', mid: '25–37%', fresh: '18%', out: 'degraded: quotes the pinned clip', k: 'mid' },
  { ws: '(1024, 64)', pin: '+ first 6 generated tokens', mid: '→ 7%', fresh: '8%', out: 'collapses: template echo', k: 'bad' },
  { ws: '(512, 32)', pin: 'as (1024, 32)', mid: '→ 0%', fresh: '0%', out: 'too-small window; sinks no rescue', k: 'bad' },
  { ws: '(2048, 32)', pin: 'as (1024, 32)', mid: '40–57%', fresh: '42%', out: 'recovers; matches W=1024', k: 'good' },
]
const OUT_COLOR = { best: C.sink, good: C.sink, mid: C.amber, bad: C.van }

export function SinkSweepTable() {
  return (
    <div className="panel panel-pad" style={{ marginTop: 24 }}>
      <div className="fig-title">Sizing the bound: the operating region has edges <span className="fig-tag">boundary controls</span></div>
      <div className="fig-sub">
        Sweep of the bound's two sizes (W, S), with controls at the exact token-layout edges — session layout:
        chat header [0, 14) · first audio [14, 42) · instruction [42, 53) · assistant-open [53, 58) · generated ≥ 58.
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table className="sweep-table">
          <thead>
            <tr><th>(W, S)</th><th>pin covers</th><th>mid-call</th><th>fresh Q</th><th>outcome</th></tr>
          </thead>
          <tbody>
            {SWEEP_ROWS.map((r) => (
              <tr key={r.ws + r.pin}>
                <td className="mono">{r.ws}</td>
                <td>{r.pin}</td>
                <td className="mono">{r.mid}</td>
                <td className="mono">{r.fresh}</td>
                <td style={{ color: OUT_COLOR[r.k], fontWeight: r.k === 'best' ? 650 : 480 }}>{r.out}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="fig-caption">
        The controls overturned our first guess. A pin that <i>truncates</i> the first audio block is harmless
        (S=32) — the malformed-block hypothesis is refuted. Instead, <b>pinned content stays semantically
        live</b>: from the complete-audio pin onward, sessions answer the pinned first question minutes after it
        played, and pinning the model's own first output tokens collapses generation into template echo. Engine
        metrics are identical in every row (KV plateau tracks block arithmetic; latency flat) — the differences
        are pure model behavior. The rule: <b>pin structure, not content, and keep the window generous.</b>
      </div>
    </div>
  )
}
