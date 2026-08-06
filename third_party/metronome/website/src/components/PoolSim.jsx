import React, { useMemo } from 'react'
import { usePlayback, fmtClock } from '../chart/util.js'
import { PlayBar } from './PlayBar.jsx'
import { rngOrder } from './rng.js'

const COLS = 24, ROWS = 9, N_BLOCKS = COLS * ROWS
const DUR = 16 // s of animation for a 300 s call
const T_SAT = 148 // s: measured pool saturation (N=128, Qwen3-Omni-30B)
const WIN_PLATEAU = 0.255

// The mechanism, animated: two identical KV block pools under the same load.
// Unbounded resident KV fills the pool linearly until the scheduler stalls;
// the in-engine window frees blocks behind it and plateaus at ~25 %.
export function PoolSim() {
  const [tp, playing, ctl] = usePlayback(DUR, 1)
  const tCall = (tp / DUR) * 300

  // deterministic fill order so blocks light up in a stable scatter
  const order = useMemo(() => rngOrder(N_BLOCKS, 13), [])

  const vanOcc = Math.min(1, Math.max(0, (tCall - 14) / (T_SAT - 14)))
  const winOcc = Math.min(WIN_PLATEAU, Math.max(0, (tCall - 14) / (T_SAT - 14)))
  const stalled = tCall >= T_SAT
  const vanFull = Math.round(vanOcc * N_BLOCKS)
  const winFull = Math.round(winOcc * N_BLOCKS)
  // windowed churn: after plateau, blocks recycle — shift which blocks are lit
  const churn = winOcc >= WIN_PLATEAU - 0.001 ? Math.floor((tCall - 60) / 6) : 0

  const winLit = useMemo(() => {
    const s = new Set()
    for (let i = 0; i < winFull; i++) s.add(order[(i + churn) % N_BLOCKS])
    return s
  }, [winFull, churn, order])

  return (
    <div className="panel panel-pad" ref={ctl.hostRef}>
      <div className="fig-title">Inside the engine: the KV block pool <span className="fig-tag">the trigger, caught in the act</span></div>
      <div className="fig-sub">Each cell is a KV block. Same call as above — N=128 sessions, every frame appends KV to every session.</div>

      <div className="pool-duo" style={{ marginTop: 16 }}>
        <div className="pool-cell">
          <div className="pool-cell-head">
            <span className="pool-name van">unbounded resident KV</span>
            <span className="pool-occ">pool {Math.round(vanOcc * 100)}%</span>
          </div>
          <div className="pool-grid" role="img" aria-label={`Unbounded KV pool at ${Math.round(vanOcc * 100)} percent occupancy${stalled ? ', saturated and stalled' : ''}`}>
            {Array.from({ length: N_BLOCKS }, (_, i) => {
              const lit = order.indexOf(i) < vanFull
              return <div key={i} className={`pool-block${lit ? (stalled ? ' stalled' : ' van-full') : ''}`} />
            })}
          </div>
          <div className="pool-status">
            <span>running <b className={stalled ? 'bad' : ''}>{stalled ? 0 : 128}</b></span>
            <span>waiting <b className={stalled ? 'bad' : ''}>{stalled ? 128 : 0}</b></span>
            <span className={stalled ? 'bad' : ''}>{stalled ? '■ SCHEDULER STALLED — never recovers' : 'occupancy climbing…'}</span>
          </div>
        </div>

        <div className="pool-cell">
          <div className="pool-cell-head">
            <span className="pool-name win">Metronome: windowed KV (W tokens)</span>
            <span className="pool-occ">pool {Math.round(winOcc * 100)}%</span>
          </div>
          <div className="pool-grid" role="img" aria-label={`Windowed KV pool plateaus at about 25 percent occupancy`}>
            {Array.from({ length: N_BLOCKS }, (_, i) => (
              <div key={i} className={`pool-block${winLit.has(i) ? ' win-full' : ''}`} />
            ))}
          </div>
          <div className="pool-status">
            <span>running <b className="good">128</b></span>
            <span>waiting <b className="good">0</b></span>
            <span className="good">{winOcc >= WIN_PLATEAU - 0.001 ? 'plateau ≈ 25% — blocks behind the window freed' : 'occupancy climbing…'}</span>
          </div>
        </div>
      </div>

      <PlayBar t={tp} dur={DUR} playing={playing} ctl={ctl} clock={`${fmtClock(tCall)} / 5:00`} />
      <div className="fig-caption">
        <b>The failure is a memory cliff, not a compute drift.</b> Per-frame compute stays cheap to the last tick;
        what kills the run is that N sessions steadily consume a fixed block pool. When it saturates (~148 s here),
        the scheduler can no longer allocate blocks and moves <b>all N sessions to the waiting queue at once</b> —
        a hard stall that never recovers, because audio keeps arriving open-loop and stalled sessions can never
        catch up. The windowed pool frees blocks behind each session's window and settles at roughly a quarter of
        capacity, with only transient, self-healing preemption late in the run.
      </div>
    </div>
  )
}
