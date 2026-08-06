import { useEffect, useRef, useState } from 'react'

export function linScale(d0, d1, r0, r1) {
  const s = (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0)
  s.domain = [d0, d1]
  return s
}

export function logScale(d0, d1, r0, r1) {
  const l0 = Math.log10(d0), l1 = Math.log10(d1)
  const s = (v) => r0 + ((Math.log10(Math.max(v, d0)) - l0) / (l1 - l0)) * (r1 - r0)
  s.domain = [d0, d1]
  return s
}

export function linePath(points, x, y) {
  return points.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(p.t).toFixed(2)},${y(p.v).toFixed(2)}`).join('')
}

export function fmtClock(s) {
  const m = Math.floor(s / 60), r = Math.floor(s % 60)
  return `${m}:${String(r).padStart(2, '0')}`
}

// rAF-driven playback clock: returns [t, playing, controls]
export function usePlayback(duration, speed = 1, autoStart = true) {
  const [t, setT] = useState(0)
  const [playing, setPlaying] = useState(false)
  const raf = useRef(null)
  const last = useRef(null)
  const tRef = useRef(0)
  const started = useRef(false)
  const hostRef = useRef(null)

  useEffect(() => { tRef.current = t }, [t])

  useEffect(() => {
    if (!autoStart || !hostRef.current) { return }
    const obs = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !started.current) {
        started.current = true
        setPlaying(true)
      }
    }, { threshold: 0.35 })
    obs.observe(hostRef.current)
    return () => obs.disconnect()
  }, [autoStart])

  useEffect(() => {
    if (!playing) { last.current = null; return }
    const step = (now) => {
      if (last.current == null) last.current = now
      const dt = ((now - last.current) / 1000) * speed
      last.current = now
      let next = tRef.current + dt
      if (next >= duration) { next = duration; setPlaying(false) }
      tRef.current = next
      setT(next)
      if (next < duration) raf.current = requestAnimationFrame(step)
    }
    raf.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf.current)
  }, [playing, duration, speed])

  const controls = {
    hostRef,
    toggle: () => {
      if (!playing && tRef.current >= duration) { tRef.current = 0; setT(0) }
      setPlaying((p) => !p)
    },
    seek: (v) => { tRef.current = v; setT(v) },
    reset: () => { tRef.current = 0; setT(0); setPlaying(true) },
  }
  return [t, playing, controls]
}

// scroll reveal
export function useReveal() {
  const ref = useRef(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver((es) => {
      es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); obs.unobserve(e.target) } })
    }, { threshold: 0.12 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])
  return ref
}
