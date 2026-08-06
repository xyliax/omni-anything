// Data for every chart on the site. Shapes and headline numbers follow the
// measurements reported in the paper (figures/headline, kvpool, cliff, predict,
// admission_trace, longhorizon, capacity); traces are reconstructed at the
// paper's reported resolution for the interactive recreations.

export const C = {
  van: '#D55E00', // unbounded KV / failure
  win: '#0072B2', // Metronome windowed KV / fix
  sink: '#009E73', // full bound: window + pinned attention sinks
  amber: '#B8860B',
  ink: '#1D1A16',
  inkSoft: '#5C554B',
  inkMute: '#928979',
}

export const LABEL_VAN = 'vLLM-realtime (unbounded KV)'
export const LABEL_WIN = 'Metronome (windowed KV)'

// Deterministic pseudo-random (mulberry32) so traces are stable across renders.
function rng(seed) {
  let a = seed >>> 0
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// ---- Headline: one 5-minute call at N=128, per-frame latency (ms), log scale ----
export function headlineTraces() {
  const rv = rng(41), rw = rng(97)
  const van = [], win = []
  for (let t = 0; t <= 300; t += 4) {
    // vanilla: cold-start spike, flat few-ms, one-step jump to the ~1.6 s wall at ~180 s
    let v
    if (t === 0) v = 150
    else if (t < 178) v = 2.2 + 2.6 * rv() + (t > 140 ? -0.8 * rv() : 0)
    else v = 1600 + 12 * rv()
    van.push({ t, v: Math.max(1, v) })
    // windowed: cold-start spike, flat 2–10 ms for the whole call
    let w
    if (t === 0) w = 150
    else if (t < 60) w = 2.2 + 2.4 * rw()
    else if (t < 270) w = 4.5 + 4.5 * rw()
    else w = 1.6 + 1.2 * rw()
    win.push({ t, v: Math.max(1, w) })
  }
  return { van, win }
}

// ---- KV pool occupancy + waiting requests (N=128, 300 s, in-engine stat logger) ----
export function kvPoolTraces() {
  const r = rng(7)
  const occVan = [], occWin = [], waitVan = [], waitWin = []
  for (let t = 0; t <= 285; t += 3) {
    const ov = t < 14 ? 0 : Math.min(1, (t - 14) / 134) // linear fill, saturates ~148 s
    occVan.push({ t, v: ov })
    const ow = t < 14 ? 0 : Math.min(0.255, (t - 14) / 134) + (t > 48 ? 0.004 * (r() - 0.5) : 0)
    occWin.push({ t, v: Math.max(0, ow) })
    waitVan.push({ t, v: t < 128 ? 0 : t < 148 ? (t < 136 ? 4 : 2) : 128 })
    let wv = 0
    if (t >= 201 && t <= 216) wv = 20 * Math.sin(((t - 201) / 15) * Math.PI)
    else if (t >= 228 && t <= 240) wv = 10 * Math.sin(((t - 228) / 12) * Math.PI)
    else if (t >= 249 && t <= 279) wv = 30 + 8 * r()
    waitWin.push({ t, v: Math.round(wv) })
  }
  return { occVan, occWin, waitVan, waitWin }
}

// ---- Cliff (a): fresh 90 s bursts are flat for both policies ----
export const burstData = {
  N: [64, 96, 128, 160],
  van: [2.0, 3.0, 3.0, 5.0],
  win: [2.1, 3.0, 3.1, 4.3],
}

// ---- Per-run wall outcomes behind Fig. cliff(b) ----
// batch 1: fixed interleaved order (4/10 vanilla walls); batch 2: seeded randomized order on a
// different day (10/10 vanilla walls). Windowed KV: 0/20 across both.
export const wallRuns = {
  van: [
    { n: 96, wall: true }, { n: 96, wall: true }, { n: 96, wall: false }, { n: 96, wall: false }, { n: 96, wall: false },
    { n: 128, wall: true }, { n: 128, wall: true }, { n: 128, wall: false }, { n: 128, wall: false }, { n: 128, wall: false },
  ],
  vanRand: Array.from({ length: 10 }, (_, i) => ({ n: i < 5 ? 96 : 128, wall: true })),
  win: Array.from({ length: 10 }, (_, i) => ({ n: i < 5 ? 96 : 128, wall: false })),
  winRand: Array.from({ length: 10 }, (_, i) => ({ n: i < 5 ? 96 : 128, wall: false })),
}

// ---- Predictability (a): pool fill + predicted/measured stall ----
export const predictFill = {
  van30b: { t0: 14, tSat: 148, predicted: 145 },   // Qwen3-Omni-30B, N=128
  vanMcpm: { t0: 10, tSat: 114, predicted: 99 },   // MiniCPM-o-4.5, N=96
  win30bPlateau: 0.255,
  winMcpmPlateau: 0.29,
}

// ---- Predictability (b): windowed plateau is linear in N ----
export const plateauVsN = {
  points: [ { n: 128, occ: 25 }, { n: 192, occ: 38.5 }, { n: 256, occ: 51 } ],
  slopePctPerSession: 0.2016, // ~0.2 % of pool per session at W=1024
  ceiling: 496,
  nStar: 209,
}

// ---- Admission trace (open system: 512 offered at 8/s, 600 ms target) ----
export function admissionTraces() {
  const r = rng(23)
  const admitted = [], cap = [], shed = [], latency = []
  for (let t = 0; t <= 170; t += 2) {
    // admitted climbs with arrivals, caps at ~209, sessions end near t=160
    let a
    if (t < 10) a = Math.max(0, t * 1.2)
    else if (t < 35) a = Math.min(209, 12 + (t - 10) * 8)
    else if (t < 160) a = 209 + 2 * Math.sin(t / 9)
    else a = Math.max(120, 209 - (t - 160) * 9)
    admitted.push({ t, v: a })
    // controller cap: appears once latency first probes the target, settles ≈209
    if (t >= 30) {
      const c = t < 40 ? 188 + (t - 30) * 1.2 : Math.min(212, 200 + (t - 40) * 0.09)
      cap.push({ t, v: c })
    }
    // cumulative shed: 512 offered − 209 admitted, done by ~75 s
    let s
    if (t < 36) s = 0
    else if (t < 75) s = ((t - 36) / 39) * 303
    else s = 303
    shed.push({ t, v: s })
    // per-frame latency: ramps to graze 600 ms target at ~35 s, then ~12 ms steady
    let l
    if (t < 10) l = 0
    else if (t < 35) l = 60 + (t - 10) * 21 + 60 * Math.sin(t / 4) * r()
    else if (t < 38) l = 640 - (t - 35) * 200
    else if (t >= 76 && t <= 82) l = 170 * Math.sin(((t - 76) / 6) * Math.PI) + 12
    else l = 10 + 6 * r()
    latency.push({ t, v: Math.max(0, l) })
  }
  return { admitted, cap, shed, latency }
}

// ---- Long-horizon quality (free-running decode, N=32, 300 s) ----
export const longHorizon = {
  ages: [15, 45, 75, 105, 135, 165, 195, 225],
  series: [
    { key: 'van', label: LABEL_VAN, values: [32, 26, 23, 27, 27, 27, 27, 23] },
    { key: 'w512', label: 'window only, W=512 (~20 s)', values: [22, 14, 10, 11, 11, 11, 4, 3.5] },
    { key: 'w1024', label: 'window only, W=1024 (~40 s)', values: [12.5, 5, 9.5, 19, 0, 4, 7.5, 3.5] },
    { key: 'w2048', label: 'window only, W=2048 (~80 s)', values: [26, 12.5, 9.5, 0, 0, 0, 0, 0] },
    { key: 'tri0', label: 'sink kernel, sinks ablated (control)', values: [40, 4.5, 27, 5, 13.5, 8.5, 4, 0] },
    { key: 'sink', label: 'full bound: W=1024 + 32 sinks', values: [69, 34.5, 44, 35, 45.5, 41, 41, 33.5] },
  ],
  probes: [
    { probe: 'fresh spoken question (240–270 s)', van: 26, w1024: 6, tri0: 0, sink: 21 },
    { probe: 'recall of session start (270–300 s)', van: 18, w1024: 0, tri0: 0, sink: 29 },
  ],
}

// ---- Four-model streaming capacity (fresh 90 s bursts) ----
export const capacity = [
  { model: 'Qwen3-Omni-30B-A3B (FP8)', n: 160, lowerBound: true, note: 'MoE, 3 B active · 2 s budget' },
  { model: 'MiniCPM-o-4.5', n: 96, lowerBound: false, note: 'dense ~9 B · 1 s budget' },
  { model: 'Moshi', n: 32, lowerBound: true, note: 'native Mimi, voice-out · 80 ms budget' },
  { model: 'Qwen2.5-Omni-7B', n: 16, nHigh: 24, lowerBound: false, note: 'encoder-bound · 2 s budget' },
]

// ---- Window-size ablation (appendix): a generous window is free ----
export const windowAblation = {
  W: [256, 512, 1024, 2048, 4096],
  p50: [5.0, 4.9, 5.1, 5.0, 5.2],
  p90: [6.5, 6.4, 6.6, 6.8, 9.5],
}

// ---- Re-encode comparison (appendix): in-engine vs app-level recycling ----
export function reencodeTraces() {
  const r = rng(11)
  const van = [], recycle = [], engine = []
  for (let t = 0; t <= 300; t += 6) {
    van.push({ t, v: t < 240 ? 3 + 2 * r() : 1600 })
    recycle.push({ t, v: 4 + (t / 300) * 12 + 2 * r() })
    engine.push({ t, v: 2.5 + 1.5 * r() })
  }
  return { van, recycle, engine }
}
