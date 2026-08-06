import React from 'react'

export function BeyondVoice() {
  const cases = [
    {
      tag: 'Agents',
      title: 'Long-running agents',
      body: 'A scratchpad and tool-call history that grow with every step of a long task, pinned while the agent lives, against a loop that must keep responding — the same cliff, manufactured in a different modality.',
    },
    {
      tag: 'Video',
      title: 'Streaming video assistants',
      body: 'Frame context accumulates per session against a recurring render/response deadline. The pool fills on a clock that per-request latency never sees.',
    },
    {
      tag: 'RAG',
      title: 'Stateful RAG caches',
      body: 'Per-interaction cache growth that is pinned for the conversation. Latency is a lagging — here, a non- — indicator of memory pressure; the leading indicator is state occupancy.',
    },
  ]
  return (
    <>
      <div className="beyond-grid">
        {cases.map((c) => (
          <div className="beyond-card" key={c.tag}>
            <span className="beyond-icon">{c.tag}</span>
            <h4>{c.title}</h4>
            <p>{c.body}</p>
          </div>
        ))}
      </div>
      <div className="panel panel-pad" style={{ marginTop: 24 }}>
        <div className="fig-title">The engine-design implication</div>
        <p className="prose" style={{ marginTop: 10, maxWidth: 'none' }}>
          A per-session state bound should be a <strong>first-class serving parameter</strong>, not an emergent
          property of <span style={{ fontFamily: 'var(--mono)', fontSize: 15 }}>max_model_len</span>. Today the
          model-length cap is the only backstop on a resident session — and it is a crash boundary, not a policy:
          in our engine, a streaming request that reaches it kills <em>every co-resident session at once</em>.
          An engine that exposes <em>"retain each session's first S and last W tokens, freeing everything
          between"</em> as an API — Metronome's sink-anchored bound, both halves validated by ablation — would give
          every real-time deployment the slope that control depends on.
        </p>
      </div>
    </>
  )
}

export function Takeaways() {
  const items = [
    {
      t: 'Characterization',
      p: 'Real-time interaction serving is periodic serving with unbounded per-session state — and on a real full-duplex stack, that combination fails by a memory-triggered, metastable, silent latency cliff, with a validated first-order model that predicts when it strikes.',
    },
    {
      t: 'Principle',
      p: "Bounding each session's resident KV removes the cliff and restores a monotone latency signal. One mechanism buys both stability and observability — and the second is what any overload control requires.",
    },
    {
      t: 'Demonstration',
      p: 'A minimal in-engine bound — sliding window plus pinned attention sinks — and an admission controller that demonstrably depends on it, measured end-to-end on real audio across four interaction models, each half of the bound validated by ablation.',
    },
  ]
  return (
    <div className="takeaways">
      {items.map((it, i) => (
        <div className="takeaway" key={i}>
          <span className="takeaway-num">{String(i + 1).padStart(2, '0')}</span>
          <div>
            <h4>{it.t}</h4>
            <p>{it.p}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

export function Footer() {
  const bibtex = `@article{metronome2026,
  title         = {Metronome: Bound the Cache, Keep the Beat
                   for Real-Time Interaction Model Serving},
  author        = {Meng, Jiaying and Li, Bojie},
  year          = {2026},
  eprint        = {2607.02640},
  archivePrefix = {arXiv},
  primaryClass  = {cs.SD},
  url           = {https://arxiv.org/abs/2607.02640}
}`
  return (
    <footer>
      <div className="wrap">
        <div className="foot-grid">
          <div>
            <div className="foot-title">Metronome</div>
            <p style={{ marginTop: 12, fontSize: 15, maxWidth: '46ch' }}>
              Bound the cache, keep the beat — for real-time interaction model serving.
              All results measured end-to-end on real audio, across four interaction models, on one GPU.
            </p>
            <div className="foot-links">
              <a href="https://github.com/19PINE-AI/metronome" target="_blank" rel="noreferrer">Code &amp; artifact ↗</a>
              <a href="https://arxiv.org/abs/2607.02640" target="_blank" rel="noreferrer">Paper (arXiv) ↗</a>
            </div>
          </div>
          <div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: '.1em', textTransform: 'uppercase', marginBottom: 10 }}>Cite</div>
            <div className="bibtex">{bibtex}</div>
          </div>
        </div>
        <div className="foot-note">
          <span>Jiaying Meng (Independent Researcher) · Bojie Li (Pine AI)</span>
          <span>Produced with Pine Copilot's voice-directed whisper-coding workflow</span>
        </div>
      </div>
    </footer>
  )
}
