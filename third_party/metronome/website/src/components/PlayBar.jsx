import React from 'react'

export function PlayBar({ t, dur, playing, ctl, clock, note }) {
  return (
    <div className="playbar">
      <button className="play-btn" onClick={ctl.toggle} aria-label={playing ? 'Pause animation' : 'Play animation'}>
        {playing ? (
          <svg viewBox="0 0 16 16"><rect x="3" y="2.5" width="3.6" height="11" rx="1" /><rect x="9.4" y="2.5" width="3.6" height="11" rx="1" /></svg>
        ) : (
          <svg viewBox="0 0 16 16"><path d="M4 2.5 L13.5 8 L4 13.5 Z" /></svg>
        )}
      </button>
      <input
        className="scrub" type="range" min={0} max={dur} step={dur / 500} value={t}
        onChange={(e) => ctl.seek(parseFloat(e.target.value))}
        aria-label="Scrub animation timeline"
      />
      <span className="play-clock">{clock}</span>
      {note && <span className="replay-note">{note}</span>}
    </div>
  )
}
