import React from 'react'

// Animated metronome: pendulum swings once per "frame budget"; each extreme is a tick.
// Pure CSS animation (rotate about the pivot), with tick flashes at the beat.
export function Metronome({ size = 300, period = 2, broken = false }) {
  const dur = `${period * 2}s`
  return (
    <div style={{ width: size, maxWidth: '100%' }} aria-hidden="true">
      <style>{`
        @keyframes swing { 0% { transform: rotate(-24deg); } 50% { transform: rotate(24deg); } 100% { transform: rotate(-24deg); } }
        @keyframes tickL { 0%, 3% { opacity: 1; } 10%, 100% { opacity: 0; } }
        @keyframes tickR { 0%, 46% { opacity: 0; } 50%, 53% { opacity: 1; } 60%, 100% { opacity: 0; } }
        @keyframes brokenStall { 0% { transform: rotate(-24deg); } 30% { transform: rotate(18deg); } 42% { transform: rotate(14deg);} 100% { transform: rotate(15deg); } }
        .pendulum { transform-origin: 130px 236px; animation: swing ${dur} cubic-bezier(.37,0,.63,1) infinite; }
        .pendulum.stalled { animation: brokenStall 5s cubic-bezier(.2,.6,.4,1) forwards; }
        .tick-l { animation: tickL ${dur} infinite; }
        .tick-r { animation: tickR ${dur} infinite; }
      `}</style>
      <svg viewBox="0 0 260 300" width="100%">
        <defs>
          <linearGradient id="mBody" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#2A2620" />
            <stop offset="1" stopColor="#16130E" />
          </linearGradient>
        </defs>
        {/* base shadow */}
        <ellipse cx="130" cy="284" rx="86" ry="9" fill="rgba(29,26,22,.14)" />
        {/* body: truncated pyramid */}
        <path d="M96 34 L164 34 L206 278 L54 278 Z" fill="url(#mBody)" />
        <path d="M96 34 L164 34 L206 278 L54 278 Z" fill="none" stroke="#3B352A" strokeWidth="1.4" />
        {/* face slot */}
        <path d="M117 52 L143 52 L152 236 L108 236 Z" fill="#FAF6EF" opacity="0.94" />
        {/* beat scale marks */}
        {[70, 96, 122, 148, 174, 200].map((y, i) => (
          <line key={y} x1={126 - i * 0.9} x2={134 + i * 0.9} y1={y} y2={y} stroke="#B9AF98" strokeWidth="1.4" />
        ))}
        {/* tick flashes at the extremes */}
        <g className="tick-l">
          <circle cx="52" cy="60" r="4.5" fill="#D55E00" />
          <text x="52" y="44" textAnchor="middle" fontFamily="Spline Sans Mono, monospace" fontSize="11" fill="#D55E00">tick</text>
        </g>
        <g className="tick-r">
          <circle cx="208" cy="60" r="4.5" fill="#D55E00" />
          <text x="208" y="44" textAnchor="middle" fontFamily="Spline Sans Mono, monospace" fontSize="11" fill="#D55E00">tick</text>
        </g>
        {/* pendulum */}
        <g className={`pendulum${broken ? ' stalled' : ''}`}>
          <line x1="130" y1="236" x2="130" y2="58" stroke="#1D1A16" strokeWidth="4.5" strokeLinecap="round" />
          {/* weight */}
          <path d="M118 96 L142 96 L138 118 L122 118 Z" fill="#D55E00" stroke="#A34800" strokeWidth="1" />
        </g>
        {/* pivot */}
        <circle cx="130" cy="236" r="7" fill="#1D1A16" />
        <circle cx="130" cy="236" r="2.6" fill="#FAF6EF" />
        {/* base plinth */}
        <rect x="46" y="276" width="168" height="10" rx="3" fill="#16130E" />
      </svg>
    </div>
  )
}
