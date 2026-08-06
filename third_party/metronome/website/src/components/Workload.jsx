import React from 'react'
import { C } from '../data.js'

const W = 860

// Static illustration: a chatbot/agent request lives in turns with idle gaps —
// its KV is evicted or swapped out between turns and reactivated (recompute or
// swap-in) on the next one, growing as the conversation accumulates. An
// interaction session has no idle at all: small work against a recurring
// deadline every frame, resident KV growing monotonically, pinned.
export function WorkloadFigure() {
  const axA = 40, axW = 770
  const rowA = 112, rowB = 400
  const kvA = 40, kvB = 46
  const baseA = rowA + 90 // KV sawtooth baseline for row A

  // chatbot turns: [start, prefillW, decodeW] in axis units; gaps are idle
  const turns = [
    { x: 10, pre: 26, dec: 58 },
    { x: 260, pre: 40, dec: 66 },
    { x: 540, pre: 52, dec: 70 },
  ]
  // swap gaps between turns: x center region
  const gaps = [152, 424]

  return (
    <div className="panel panel-pad">
      <div className="fig-title">
        The workload engines were not built for
        <span className="fig-tag blue">figure 1</span>
      </div>
      <div className="fig-sub">Two shapes of work — and where each one's KV cache lives.</div>

      <svg className="chart-svg" viewBox={`0 0 ${W} 548`} style={{ marginTop: 14 }}
        aria-label="A chatbot or agent request works in turns with idle gaps; its KV cache is swapped out or evicted between turns and paid for again on reactivation, growing every turn. An interaction session works every frame with no idle; its resident KV grows monotonically and stays pinned.">

        {/* ================= row A: chatbot / agent request ================= */}
        <text x={14} y={24} fontSize="14" fontWeight="600" fill={C.ink} fontFamily="Spline Sans, sans-serif">A · chatbot / agent request</text>
        <text x={14} y={42} fontSize="11.5" fill={C.inkMute}>turn-based — idle gaps between turns</text>

        {/* prefill/decode legend, top right */}
        <g fontFamily="Spline Sans Mono, monospace">
          <rect x={620} y={16} width={13} height={11} rx={2} fill="#DDD5C4" stroke="#B9AF98" strokeWidth="0.8" />
          <text x={639} y={25.5} fontSize="10.5" fill={C.inkSoft}>prefill</text>
          <rect x={706} y={16} width={13} height={11} rx={2} fill={C.van} opacity="0.28" stroke={C.van} strokeWidth="0.8" />
          <text x={725} y={25.5} fontSize="10.5" fill={C.inkSoft}>decode</text>
        </g>

        <line x1={axA} x2={axA + axW} y1={rowA} y2={rowA} stroke="#C9BFA9" strokeWidth="1.2" />
        <text x={axA + axW + 6} y={rowA + 4} fontSize="11" fill={C.inkMute}>time</text>

        {turns.map((t, i) => (
          <g key={i}>
            <rect x={axA + t.x} y={rowA - 30} width={t.pre} height={24} rx={3} fill="#DDD5C4" stroke="#B9AF98" strokeWidth="0.9" />
            <rect x={axA + t.x + t.pre} y={rowA - 30} width={t.dec} height={24} rx={3} fill={C.van} opacity="0.22" stroke={C.van} strokeWidth="0.9" />
            <text x={axA + t.x + (t.pre + t.dec) / 2} y={rowA - 38} textAnchor="middle" fontSize="10.5" fill={C.inkSoft}>turn {i + 1}</text>
          </g>
        ))}
        {/* idle gap labels */}
        <text x={axA + 178} y={rowA - 12} textAnchor="middle" fontSize="10.5" fontStyle="italic" fill={C.inkMute}>idle: user thinks…</text>
        <text x={axA + 460} y={rowA - 12} textAnchor="middle" fontSize="10.5" fontStyle="italic" fill={C.inkMute}>idle: tool call runs…</text>

        {/* KV footprint A: sawtooth — grows each turn, parked elsewhere between turns */}
        <text x={14} y={baseA - 44} fontSize="11" fill={C.inkMute}>KV in GPU</text>
        <text x={14} y={baseA - 30} fontSize="11" fill={C.inkMute}>memory (HBM)</text>
        {(() => {
          const h = (i) => kvA * (0.45 + 0.275 * i) // context accumulates: taller every turn
          let d = `M${axA + turns[0].x},${baseA}`
          turns.forEach((t, i) => {
            const x0 = axA + t.x, x1 = axA + t.x + t.pre + t.dec
            d += ` L${x0},${baseA} L${x0 + t.pre * 0.8},${baseA - h(i) * 0.85} L${x1},${baseA - h(i)} L${x1},${baseA}`
          })
          d += ` L${axA + axW},${baseA}`
          return <path d={d} fill="none" stroke={C.inkSoft} strokeWidth="2" strokeLinejoin="round" />
        })()}

        {/* swap arrows: down to host band, back up before the next turn */}
        {gaps.map((x) => (
          <g key={x} fontFamily="Spline Sans Mono, monospace">
            <line x1={axA + x - 6} y1={baseA - 22} x2={axA + x - 6} y2={baseA + 44} stroke={C.amber} strokeWidth="1.4" />
            <path d={`M${axA + x - 10},${baseA + 42} L${axA + x - 6},${baseA + 50} L${axA + x - 2},${baseA + 42} Z`} fill={C.amber} />
            <line x1={axA + x + 46} y1={baseA + 50} x2={axA + x + 46} y2={baseA - 16} stroke={C.amber} strokeWidth="1.4" />
            <path d={`M${axA + x + 42},${baseA - 14} L${axA + x + 46},${baseA - 22} L${axA + x + 50},${baseA - 14} Z`} fill={C.amber} />
            <text x={axA + x - 14} y={baseA + 24} textAnchor="end" fontSize="10" fill={C.amber}>swap out</text>
            <text x={axA + x + 54} y={baseA + 24} fontSize="10" fill={C.amber}>swap in</text>
          </g>
        ))}
        <text x={axA + axW} y={baseA + 24} textAnchor="end" fontSize="11" fontStyle="italic" fill={C.inkSoft}>each reactivation costs more</text>

        {/* host memory band */}
        <line x1={axA} x2={axA + axW} y1={baseA + 56} y2={baseA + 56} stroke="#D8CFBB" strokeWidth="1" strokeDasharray="4 4" />
        <text x={axA} y={baseA + 71} fontSize="10.5" fill={C.inkMute}>host DRAM — parked state waits here, hidden in the idle gaps</text>

        {/* ================= row B: interaction session ================= */}
        <text x={14} y={rowB - 78} fontSize="14" fontWeight="600" fill={C.ink} fontFamily="Spline Sans, sans-serif">B · interaction session</text>
        <text x={14} y={rowB - 61} fontSize="11.5" fill={C.win}>periodic + persistent — no idle, ever</text>

        <line x1={axA} x2={axA + axW} y1={rowB} y2={rowB} stroke="#C9BFA9" strokeWidth="1.2" />
        <text x={axA + axW + 6} y={rowB + 4} fontSize="11" fill={C.inkMute}>time</text>

        {Array.from({ length: 9 }, (_, i) => {
          const x0 = axA + 10 + i * (axW / 9) * 0.94
          return (
            <g key={i}>
              <rect x={x0} y={rowB - 26} width={15} height={20} rx={2.5} fill="#DDD5C4" stroke="#B9AF98" strokeWidth="0.8" />
              <rect x={x0 + 15} y={rowB - 26} width={12} height={20} rx={2.5} fill={C.van} opacity="0.22" stroke={C.van} strokeWidth="0.8" />
              <line x1={x0 + 58} x2={x0 + 58} y1={rowB - 32} y2={rowB + 5} stroke={C.van} strokeWidth="1.3" />
            </g>
          )
        })}
        <path d={`M${axA + 78},${rowB - 38} q40,-14 80,0`} fill="none" stroke={C.van} strokeWidth="1.2" />
        <text x={axA + 172} y={rowB - 42} fontSize="11" fill={C.van}>recurring deadline — every 80 ms to 2 s</text>
        <text x={axA + 10} y={rowB + 22} fontSize="10.5" fontStyle="italic" fill={C.inkSoft}>audio in → tokens out, every frame</text>

        {/* KV footprint B: monotone staircase */}
        <text x={14} y={rowB + 50} fontSize="11" fill={C.inkMute}>KV in GPU</text>
        <text x={14} y={rowB + 64} fontSize="11" fill={C.inkMute}>memory (HBM)</text>
        {(() => {
          const base = rowB + 100
          let d = `M${axA + 10},${base}`
          for (let i = 0; i < 9; i++) {
            const x1 = axA + 10 + (i + 1) * (axW / 9) * 0.94
            d += ` L${x1 - 18},${base - (i / 9) * kvB} L${x1 - 6},${base - ((i + 1) / 9) * kvB}`
          }
          return <path d={d} fill="none" stroke={C.van} strokeWidth="2.4" strokeLinejoin="round" />
        })()}
        <text x={axA + axW} y={rowB + 122} textAnchor="end" fontSize="11" fontStyle="italic" fill={C.van}>resident KV grows every frame — no idle to swap it out</text>
      </svg>

      <div className="fig-caption">
        A chatbot (a) parks its growing KV out of GPU memory between turns and pays a <b>reactivation toll</b> —
        survivable, because idle gaps hide it. A session (b) is due <i>every</i> frame with no idle, so its KV must
        stay <b>resident</b> — and unbounded, it grows for the life of the call. <b>Periodic deadlines + unbounded
        pinned state</b> is the combination this paper studies.
      </div>
    </div>
  )
}

// Static illustration: the three places session state can live, their tolls,
// and the missing fourth option Metronome adds.
export function StateOptions() {
  const rows = [
    {
      k: '1',
      name: 'Recompute',
      how: 'evict the KV, re-encode recent context every frame',
      toll: 'compute toll, grows with context',
      why: 'Fine per-turn for chatbots — fatal per-frame.',
      verdict: 'breaks the deadline',
      ok: false,
      spark: 'grow',
    },
    {
      k: '2',
      name: 'Swap',
      how: 'offload KV to host DRAM, swap back over PCIe each frame',
      toll: 'bandwidth toll, grows with context × N',
      why: 'Tens of GB/s of thrash within minutes — every session is due every frame.',
      verdict: 'breaks the deadline',
      ok: false,
      spark: 'grow',
    },
    {
      k: '3',
      name: 'Stay resident, unbounded',
      how: "keep KV pinned in HBM — vLLM-realtime / SGLang streaming sessions (Thinking Machines Lab's upstream)",
      toll: 'memory toll, grows without bound',
      why: 'The right primitive — but the pool fills on a clock latency cannot see.',
      verdict: 'the silent cliff (§02)',
      ok: false,
      spark: 'cliff',
    },
    {
      k: '★',
      name: 'Metronome: resident + bounded',
      how: 'keep only the last W tokens resident, freeing blocks behind the window',
      toll: 'fixed ~0.2% of pool per session',
      why: 'No movement, no re-encode, no growth — and latency becomes an honest signal.',
      verdict: 'on beat, on budget',
      ok: true,
      spark: 'flat',
    },
  ]

  return (
    <div className="panel panel-pad" style={{ marginTop: 26 }}>
      <div className="fig-title">Where can a session's state live? <span className="fig-tag blue">figure 2 · the design space</span></div>
      <div className="fig-sub">Unbounded state taxes whichever resource you park it in — FLOPs, PCIe, or HBM. The fix is to bound it.</div>

      <div style={{ marginTop: 14 }}>
        {rows.map((r) => (
          <div key={r.k} style={{
            display: 'grid', gridTemplateColumns: '46px 1.15fr 78px 1.35fr 158px',
            gap: 16, alignItems: 'center', padding: '16px 4px',
            borderTop: '1px solid var(--line-soft)',
          }} className="state-row">
            <div style={{
              fontFamily: 'var(--serif)', fontStyle: 'italic', fontSize: 26,
              color: r.ok ? 'var(--win)' : 'var(--ink-3)', textAlign: 'center',
            }}>{r.k}</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 15.5, color: r.ok ? 'var(--win)' : 'var(--ink)' }}>{r.name}</div>
              <div style={{ fontSize: 13, color: 'var(--ink-3)', marginTop: 2 }}>{r.how}</div>
            </div>
            <TollSpark kind={r.spark} ok={r.ok} />
            <div style={{ fontSize: 13.5, color: 'var(--ink-2)' }}>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 11.5, color: r.ok ? 'var(--win)' : 'var(--van)', display: 'block', marginBottom: 2 }}>{r.toll}</span>
              {r.why}
            </div>
            <div style={{
              fontFamily: 'var(--mono)', fontSize: 11.5, letterSpacing: '.04em', textTransform: 'uppercase',
              textAlign: 'center', padding: '7px 8px', borderRadius: 8,
              color: r.ok ? 'var(--win)' : 'var(--van)',
              background: r.ok ? 'var(--win-soft)' : 'var(--van-soft)',
              border: `1px solid ${r.ok ? 'rgba(0,114,178,.3)' : 'rgba(213,94,0,.3)'}`,
            }}>{r.ok ? '✓ ' : '✕ '}{r.verdict}</div>
          </div>
        ))}
      </div>

      <div className="fig-caption">
        Chatbots can afford 1–2; a periodic session can't, so state-of-the-art serving stays resident (3) —
        correctly, but unbounded. Metronome is the missing quadrant: resident <i>and</i> bounded.
      </div>
    </div>
  )
}

function TollSpark({ kind, ok }) {
  const c = ok ? '#0072B2' : '#D55E00'
  return (
    <svg viewBox="0 0 78 44" width="78" height="44" aria-hidden="true">
      <line x1="4" x2="74" y1="38" y2="38" stroke="#C9BFA9" strokeWidth="1" />
      {kind === 'grow' && <path d="M6,34 L70,10" fill="none" stroke={c} strokeWidth="2.2" strokeLinecap="round" />}
      {kind === 'cliff' && <path d="M6,32 L44,30 L46,8 L70,8" fill="none" stroke={c} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" />}
      {kind === 'flat' && <path d="M6,24 L70,23" fill="none" stroke={c} strokeWidth="2.2" strokeLinecap="round" />}
      <text x="39" y="30" textAnchor="middle" fontSize="8.5" fill="#8A8171" fontFamily="Spline Sans Mono" dy={kind === 'flat' ? 12 : kind === 'cliff' ? 14 : 14}>
        {kind === 'flat' ? 'toll: flat' : 'toll: grows'}
      </text>
    </svg>
  )
}
