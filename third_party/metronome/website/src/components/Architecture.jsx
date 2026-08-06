import React from 'react'
import { C } from '../data.js'

// Animated system diagram: clients -> AIMD admission gate -> GPU worker driven by
// the metronome beat (one tick per frame budget), with the latency feedback loop
// that the windowed KV makes trustworthy. SMIL animations, 4 s beat cycle.
export function Architecture() {
  const beat = '4s'
  return (
    <div className="panel arch-panel">
      <div className="panel-pad">
        <div className="fig-title">How Metronome keeps the beat <span className="fig-tag blue">one tick = one batch</span></div>
        <div className="fig-sub">Two mechanisms, one dependency: the window makes latency honest; admission acts on it.</div>

        <svg className="arch-svg" viewBox="0 0 880 470" style={{ marginTop: 10 }}
          aria-label="Architecture: N clients stream audio to an AIMD admission gate, which admits up to N-star sessions into a GPU worker. A metronome beat fires one tick per frame budget; each tick prefills the new audio chunk and decodes tokens under windowed KV. Per-frame latency feeds back to the gate; surplus sessions are shed.">
          <defs>
            <marker id="arrInk" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
              <path d="M0,0.6 L7,4 L0,7.4 Z" fill={C.ink} />
            </marker>
            <marker id="arrBlue" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
              <path d="M0,0.6 L7,4 L0,7.4 Z" fill={C.win} />
            </marker>
            <marker id="arrVan2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
              <path d="M0,0.6 L7,4 L0,7.4 Z" fill={C.van} />
            </marker>
          </defs>

          {/* ---------- metronome beat, top center ---------- */}
          <g transform="translate(475,30)">
            <path d="M-16,54 L-7,8 L7,8 L16,54 Z" fill={C.ink} />
            <g>
              <line x1="0" y1="50" x2="0" y2="14" stroke={C.van} strokeWidth="3" strokeLinecap="round">
                <animateTransform attributeName="transform" type="rotate" values="-26 0 50; 26 0 50; -26 0 50" dur={beat} repeatCount="indefinite" calcMode="spline" keySplines=".37 0 .63 1;.37 0 .63 1" />
              </line>
            </g>
            <circle cx="0" cy="50" r="4" fill={C.ink} />
            <text x="30" y="24" fontSize="12.5" fill={C.inkSoft} fontFamily="Spline Sans Mono">the beat: one tick per frame budget B</text>
            <text x="30" y="41" fontSize="11.5" fill={C.inkMute} fontFamily="Spline Sans Mono">(2 s for Qwen-Omni · 80 ms for Moshi)</text>
            {/* tick flash */}
            <circle cx="0" cy="-2" r="5" fill={C.van}>
              <animate attributeName="opacity" values="0;1;0;0;1;0" keyTimes="0;0.02;0.12;0.5;0.52;0.62" dur={beat} repeatCount="indefinite" />
            </circle>
          </g>
          {/* beat line down to worker */}
          <line x1="475" y1="92" x2="475" y2="128" stroke={C.inkMute} strokeWidth="1.3" strokeDasharray="3 4" />

          {/* ---------- clients ---------- */}
          <g transform="translate(30,150)">
            <rect width="130" height="110" rx="10" fill="#F5EFE3" stroke="#C9BFA9" strokeWidth="1.2" />
            <text x="65" y="30" textAnchor="middle" fontSize="14" fontWeight="600" fill={C.ink} fontFamily="Spline Sans">N clients</text>
            <text x="65" y="49" textAnchor="middle" fontSize="11" fill={C.inkSoft} fontFamily="Spline Sans Mono">streaming 20 ms</text>
            <text x="65" y="64" textAnchor="middle" fontSize="11" fill={C.inkSoft} fontFamily="Spline Sans Mono">audio chunks</text>
            {/* waveform */}
            <g transform="translate(24,82)" stroke={C.win} strokeWidth="2" strokeLinecap="round">
              {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                <line key={i} x1={i * 10} x2={i * 10} y1={-4 - (i % 3) * 4} y2={4 + ((i + 1) % 3) * 4}>
                  <animate attributeName="y1" values={`${-3 - (i % 3) * 4};${-9 - ((i + 2) % 3) * 3};${-3 - (i % 3) * 4}`} dur="1.1s" begin={`${i * 0.12}s`} repeatCount="indefinite" />
                  <animate attributeName="y2" values={`${3 + ((i + 1) % 3) * 4};${9 + (i % 3) * 3};${3 + ((i + 1) % 3) * 4}`} dur="1.1s" begin={`${i * 0.12}s`} repeatCount="indefinite" />
                </line>
              ))}
            </g>
          </g>

          {/* audio flow: clients -> gate */}
          <path id="p-audio" d="M160,205 L235,205" fill="none" stroke={C.inkMute} strokeWidth="1.4" markerEnd="url(#arrInk)" />
          <text x="197" y="192" textAnchor="middle" fontSize="11" fill={C.inkMute} fontFamily="Spline Sans Mono">audio</text>
          {[0, 1, 2].map((i) => (
            <circle key={i} r="3.2" fill={C.win}>
              <animateMotion dur="1.6s" begin={`${i * 0.53}s`} repeatCount="indefinite" path="M160,205 L232,205" />
            </circle>
          ))}

          {/* ---------- admission gate ---------- */}
          <g transform="translate(238,148)">
            <rect width="150" height="114" rx="10" fill="#FDF6EC" stroke={C.van} strokeWidth="1.6" />
            <text x="75" y="28" textAnchor="middle" fontSize="14" fontWeight="600" fill={C.van} fontFamily="Spline Sans">Admission gate</text>
            <text x="75" y="48" textAnchor="middle" fontSize="11" fill={C.inkSoft} fontFamily="Spline Sans Mono">AIMD on measured</text>
            <text x="75" y="63" textAnchor="middle" fontSize="11" fill={C.inkSoft} fontFamily="Spline Sans Mono">per-frame latency</text>
            <text x="75" y="88" textAnchor="middle" fontSize="12.5" fontWeight="600" fill={C.ink} fontFamily="Spline Sans Mono">admit ≤ N★, shed rest</text>
          </g>

          {/* admitted flow: gate -> worker */}
          <path d="M388,205 L448,205" fill="none" stroke={C.inkMute} strokeWidth="1.4" markerEnd="url(#arrInk)" />
          <text x="418" y="192" textAnchor="middle" fontSize="11" fill={C.inkMute} fontFamily="Spline Sans Mono">admitted</text>
          <circle r="3.2" fill={C.win}>
            <animateMotion dur="1.6s" begin="0.3s" repeatCount="indefinite" path="M388,205 L445,205" />
          </circle>

          {/* shed arrow */}
          <path d="M313,262 L313,330" fill="none" stroke={C.van} strokeWidth="1.6" markerEnd="url(#arrVan2)" />
          <text x="326" y="312" fontSize="11.5" fill={C.van} fontFamily="Spline Sans Mono">surplus shed cleanly</text>
          <text x="326" y="327" fontSize="11" fill={C.inkMute} fontFamily="Spline Sans Mono">(overload rejection, not degraded service)</text>
          <circle r="3" fill={C.van}>
            <animateMotion dur="2.2s" begin="1s" repeatCount="indefinite" path="M313,262 L313,326" />
            <animate attributeName="opacity" values="1;1;0" keyTimes="0;0.85;1" dur="2.2s" begin="1s" repeatCount="indefinite" />
          </circle>

          {/* ---------- GPU worker ---------- */}
          <g transform="translate(452,132)">
            <rect width="398" height="146" rx="12" fill="#F5EFE3" stroke="#B9AF98" strokeWidth="1.3" />
            <text x="199" y="24" textAnchor="middle" fontSize="13" fontWeight="600" fill={C.ink} fontFamily="Spline Sans">GPU worker — one tick = one batch of all due sessions</text>
            {/* prefill box */}
            <rect x="26" y="40" width="150" height="58" rx="7" fill="#FFFDF8" stroke="#B9AF98" strokeWidth="1" />
            <text x="101" y="63" textAnchor="middle" fontSize="12.5" fontWeight="600" fill={C.ink} fontFamily="Spline Sans">Prefill</text>
            <text x="101" y="81" textAnchor="middle" fontSize="10.5" fill={C.inkSoft} fontFamily="Spline Sans Mono">new audio chunk</text>
            <rect x="26" y="40" width="150" height="58" rx="7" fill={C.win} opacity="0">
              <animate attributeName="opacity" values="0;0.16;0;0;0.16;0" keyTimes="0;0.04;0.14;0.5;0.54;0.64" dur={beat} repeatCount="indefinite" />
            </rect>
            <path d="M176,69 L216,69" stroke={C.inkMute} strokeWidth="1.3" markerEnd="url(#arrInk)" />
            <text x="196" y="60" textAnchor="middle" fontSize="10" fill={C.inkMute} fontFamily="Spline Sans Mono">then</text>
            {/* decode box */}
            <rect x="218" y="40" width="150" height="58" rx="7" fill="#FFFDF8" stroke="#B9AF98" strokeWidth="1" />
            <text x="293" y="63" textAnchor="middle" fontSize="12.5" fontWeight="600" fill={C.ink} fontFamily="Spline Sans">Decode</text>
            <text x="293" y="81" textAnchor="middle" fontSize="10.5" fill={C.inkSoft} fontFamily="Spline Sans Mono">τ tokens / session</text>
            <rect x="218" y="40" width="150" height="58" rx="7" fill={C.van} opacity="0">
              <animate attributeName="opacity" values="0;0;0.16;0;0;0;0.16;0" keyTimes="0;0.13;0.18;0.3;0.5;0.63;0.68;0.8" dur={beat} repeatCount="indefinite" />
            </rect>
            {/* windowed KV strip */}
            <text x="199" y="126" textAnchor="middle" fontSize="12" fontWeight="600" fill={C.win} fontFamily="Spline Sans Mono">bounded KV: last W tokens + a few pinned sinks</text>
          </g>

          {/* tokens back: worker -> clients (top arc) */}
          <path d="M475,132 C420,96 220,96 100,146" fill="none" stroke={C.inkMute} strokeWidth="1.3" strokeDasharray="1 0" markerEnd="url(#arrInk)" />
          <text x="286" y="103" textAnchor="middle" fontSize="11" fill={C.inkMute} fontFamily="Spline Sans Mono">stream tokens back</text>
          <circle r="3" fill={C.ink}>
            <animateMotion dur="2s" begin="0.9s" repeatCount="indefinite" path="M475,132 C420,96 220,96 104,144" />
          </circle>

          {/* latency feedback: worker -> gate (bottom arc) */}
          <path d="M700,278 C700,400 440,400 335,272" fill="none" stroke={C.win} strokeWidth="1.6" strokeDasharray="6 5" markerEnd="url(#arrBlue)" />
          <text x="565" y="416" textAnchor="middle" fontSize="12" fill={C.win} fontFamily="Spline Sans Mono">per-frame latency feedback — trustworthy only because the KV is bounded</text>
          <circle r="3.4" fill={C.win}>
            <animateMotion dur="2.4s" begin="0.4s" repeatCount="indefinite" path="M700,278 C700,400 440,400 339,276" />
          </circle>

          {/* one-tick anatomy strip */}
          <g transform="translate(60,448)">
            <line x1="0" x2="770" y1="0" y2="0" stroke="#C9BFA9" strokeWidth="1.2" />
            <line x1="0" x2="0" y1="-9" y2="6" stroke={C.ink} strokeWidth="1.6" />
            <line x1="640" x2="640" y1="-9" y2="6" stroke={C.ink} strokeWidth="1.6" />
            <text x="0" y="20" textAnchor="middle" fontSize="10.5" fill={C.inkSoft} fontFamily="Spline Sans Mono">tick k</text>
            <text x="640" y="20" textAnchor="middle" fontSize="10.5" fill={C.inkSoft} fontFamily="Spline Sans Mono">tick k+1</text>
            <rect x="2" y="-8" width="110" height="14" fill="#DDD5C4" />
            <rect x="112" y="-8" width="80" height="14" fill={C.van} opacity="0.25" />
            <text x="56" y="-14" textAnchor="middle" fontSize="10" fill={C.inkSoft} fontFamily="Spline Sans Mono">prefill</text>
            <text x="152" y="-14" textAnchor="middle" fontSize="10" fill={C.inkSoft} fontFamily="Spline Sans Mono">decode</text>
            <text x="410" y="-6" textAnchor="middle" fontSize="10.5" fontStyle="italic" fill={C.inkMute} fontFamily="Spline Sans Mono">slack (headroom) — schedulable iff Tₖ(N) ≤ B, every k</text>
            {/* sweeping playhead */}
            <line x1="0" x2="0" y1="-12" y2="8" stroke={C.van} strokeWidth="2">
              <animate attributeName="x1" values="0;640;640;0" keyTimes="0;0.5;0.99;1" dur={beat} repeatCount="indefinite" />
              <animate attributeName="x2" values="0;640;640;0" keyTimes="0;0.5;0.99;1" dur={beat} repeatCount="indefinite" />
            </line>
          </g>
        </svg>

        <div className="fig-caption">
          <b>Deliberately minimal.</b> WebSocket clients stream 20 ms audio to a Go gateway; once per tick it issues a
          single batched <span style={{ fontFamily: 'var(--mono)' }}>Step</span> over gRPC for all due sessions; the GPU
          worker feeds each session's long-lived resumable request. Metronome adds exactly two things:
          (a) the <b>sink-anchored in-engine KV window</b> — activate the engine's dormant sliding-window path on the
          decoder, so each session attends over and <i>retains</i> only its last W tokens plus a few pinned
          attention-sink tokens, freeing everything between with no re-encoding — and (b) the <b>AIMD admission
          gate</b>, which discovers the schedulable concurrency N★ online from the latency signal the window makes
          trustworthy. The contribution is knowing <i>what</i> to bound and <i>why</i>, not machinery.
        </div>
      </div>
    </div>
  )
}
