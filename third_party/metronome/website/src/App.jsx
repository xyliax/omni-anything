import React from 'react'
import { Nav, Hero, StatBand } from './components/Hero.jsx'
import { WorkloadFigure, StateOptions } from './components/Workload.jsx'
import { CliffChart } from './components/CliffChart.jsx'
import { PoolSim } from './components/PoolSim.jsx'
import { Properties } from './components/Properties.jsx'
import { PredictFill, PredictPlateau } from './components/PredictCharts.jsx'
import { Architecture } from './components/Architecture.jsx'
import { WindowAnim } from './components/WindowAnim.jsx'
import { AdmissionChart } from './components/AdmissionChart.jsx'
import { QualityRegimes, LongHorizonChart, ProbeChart, SinkSweepTable } from './components/QualityChart.jsx'
import { CapacityChart } from './components/CapacityChart.jsx'
import { BeyondVoice, Takeaways, Footer } from './components/Beyond.jsx'
import { useReveal } from './chart/util.js'

function Reveal({ children, style }) {
  const ref = useReveal()
  return <div ref={ref} className="reveal" style={style}>{children}</div>
}

function SectionHead({ num, title, children }) {
  return (
    <div className="sec-head">
      <div className="sec-num">{num}</div>
      <h2>{title}</h2>
      {children}
    </div>
  )
}

export default function App() {
  return (
    <>
      <Nav />
      <Hero />
      <StatBand />

      {/* 01 — the workload */}
      <section className="band" id="workload">
        <SectionHead num="01 · The new serving regime" title={<>A session is not a request. It's a <span className="accent">periodic real-time task</span>.</>}>
          <p className="sec-lede">
            A chatbot works in <em>turns</em>; between them, its growing KV cache is swapped out of GPU memory or
            recomputed, and the idle gap hides the cost. An interaction session gets an audio chunk <em>every
            frame</em> — every 80 ms to 2 s, for minutes — with no idle, ever. Its KV must stay <em>resident</em>,
            and resident, it grows without bound. LLM serving assumes ephemeral requests; real-time scheduling
            assumes bounded state. A session violates both.
          </p>
        </SectionHead>
        <div className="wrap">
          <Reveal><WorkloadFigure /></Reveal>
          <Reveal><StateOptions /></Reveal>
        </div>
      </section>

      {/* 02 — the cliff (dark) */}
      <section className="band dark" id="cliff">
        <SectionHead num="02 · The failure" title={<>Under sustained load, serving doesn't degrade. It <span className="accent">falls off a cliff</span>.</>}>
          <p className="sec-lede">
            Drive the unmodified resumable-KV path through a real full-duplex stack — WebSocket audio clients, a Go
            gateway, a GPU worker, real audio — and per-frame latency holds at a few milliseconds… then jumps, in a
            single step, to a wall where the stalled engine stops producing tokens.
          </p>
        </SectionHead>
        <div className="wrap">
          <Reveal><CliffChart /></Reveal>
          <Reveal style={{ marginTop: 26 }}><PoolSim /></Reveal>
          <Reveal style={{ marginTop: 46 }}>
            <Properties />
          </Reveal>
        </div>
      </section>

      {/* 03 — predictable */}
      <section className="band deep" id="model">
        <SectionHead num="03 · The physics" title={<>The collapse isn't random. It obeys a <span className="accent-win">first-order model</span>.</>}>
          <p className="sec-lede">
            Pool occupancy under unbounded KV rises <em>linearly</em>: N sessions each append KV at a steady rate r,
            so saturation strikes at t<sub>sat</sub> = (1−ρ₀)/(N·r). Fit r on the early trace and you predict the
            crash within a few percent — and the "coin flip" dissolves into a race between two clocks.
          </p>
        </SectionHead>
        <div className="wrap">
          <div className="duo">
            <Reveal><PredictFill /></Reveal>
            <Reveal><PredictPlateau /></Reveal>
          </div>
        </div>
      </section>

      {/* 04 — the fix */}
      <section className="band" id="fix">
        <SectionHead num="04 · Metronome" title={<>One move fixes both: <span className="accent-win">bound each session's resident state</span> — and latency starts telling the truth.</>}>
          <p className="sec-lede">
            Capping the resident context turns the cliff into a slope: per-frame latency rises smoothly and
            monotonically with load. That keeps every session on beat <em>and</em> gives a feedback controller a signal
            it can trust — and graceful degradation is the precondition for every overload defense you'd want to build.
          </p>
        </SectionHead>
        <div className="wrap">
          <Reveal><Architecture /></Reveal>
          <Reveal style={{ marginTop: 26 }}><WindowAnim /></Reveal>
        </div>
      </section>

      {/* pull quote */}
      <section className="band deep" style={{ padding: '76px 0' }}>
        <div className="wrap">
          <Reveal>
            <p className="pull-quote">
              "A signal that is flat until the instant of collapse carries no information to act on.
              <span className="accent-win"> Graceful degradation is what makes a metric trustworthy.</span>"
            </p>
          </Reveal>
        </div>
      </section>

      {/* 05 — results */}
      <section className="band" id="results">
        <SectionHead num="05 · The payoff" title={<>Admission converges <span className="accent-win">only</span> with bounded state.</>}>
          <p className="sec-lede">
            The controller makes a falsifiable claim: an AIMD loop on per-frame latency works only if latency is a
            monotone signal of load. Both arms ran. <strong>With the bound, the controller converges</strong> —
            N★≈209 discovered online, no hand-set capacity anywhere. <strong>Without it, the identical controller
            over-admits into the wall</strong>: the flat signal reads as headroom while resident KV silently fills
            the pool, and shedding late cannot rescue sessions that are already resident.
          </p>
        </SectionHead>
        <div className="wrap"><Reveal><AdmissionChart /></Reveal></div>
      </section>

      {/* 06 — quality */}
      <section className="band deep" id="quality">
        <SectionHead num="06 · The honest map" title={<>The bound's two halves — <span className="accent">validated by ablation</span>.</>}>
          <p className="sec-lede">
            Metronome's bound is a sliding window <em>plus a few pinned attention-sink tokens</em>. These backbones
            were trained with full attention and park softmax mass on their earliest positions — evict those and
            free-running generation corrupts. Rather than assert safety, the paper ablates each half of the bound
            in both decoding regimes.
          </p>
        </SectionHead>
        <div className="wrap">
          <Reveal><QualityRegimes /></Reveal>
          <div className="duo">
            <Reveal><LongHorizonChart /></Reveal>
            <Reveal><ProbeChart /></Reveal>
          </div>
          <Reveal><SinkSweepTable /></Reveal>
        </div>
      </section>

      {/* 07 — generality */}
      <section className="band" id="generality">
        <SectionHead num="07 · Generality" title={<>Capacity is architectural. <span className="accent">The cliff is not.</span></>}>
          <p className="sec-lede">
            Fresh capacity spans an order of magnitude across four models — set by audio-encoder weight, MoE
            sparsity, and frame budget. The cliff travels with the serving path: on MiniCPM-o-4.5, whose dense
            backbone fills the pool in under two minutes, the coin flip becomes certainty — every ten-minute run
            hard-stalls on schedule, deadline-miss counter at zero. Everything is measured end-to-end on real
            audio, every data point on a freshly started worker.
          </p>
        </SectionHead>
        <div className="wrap"><Reveal><CapacityChart /></Reveal></div>
      </section>

      {/* 08 — beyond voice */}
      <section className="band deep" id="beyond">
        <SectionHead num="08 · Beyond voice" title={<>Nothing here is specific to audio.</>}>
          <p className="sec-lede">
            Any serving loop that holds unbounded per-session state against a recurring deadline manufactures the
            same cliff — equally silent, because latency is a lagging (here, a non-) indicator of memory pressure.
            The principled fix is the same: bound the resident state per session, and size the bound to the task.
          </p>
        </SectionHead>
        <div className="wrap"><Reveal><BeyondVoice /></Reveal></div>
      </section>

      {/* 09 — takeaways */}
      <section className="band" id="takeaways">
        <SectionHead num="09 · Contributions" title={<>What the paper shows.</>} />
        <div className="wrap">
          <Reveal><Takeaways /></Reveal>
        </div>
      </section>

      <Footer />
    </>
  )
}
