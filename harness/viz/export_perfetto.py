#!/usr/bin/env python3
"""Export a run's aligned timeline bundle as a Perfetto-compatible Chrome trace.

Usage: python3 harness/viz/export_perfetto.py <tag> [...]
Emits results/viz/<tag>.trace.json.gz — open at https://ui.perfetto.dev
(“Open trace file”; processing is local WASM, the trace never leaves the browser).

Mapping:
  process "engine steps"   one thread per session; every scheduler step this session
                           participated in = one slice ("prefill+enc"/"decode",
                           args: tokens, batch, step_ms). Starvation = instant marker.
  process "gateway"        audio tick boundaries as instants.
  process "scheduler"      evictions as instants.
  counters                 KV pool %, run, wait, cumulative evictions, SM util %.
Clock alignment is inherited from bundle.build_bundle() (single source of truth).
"""
import gzip, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bundle import build_bundle, OUT  # noqa: E402


def export(tag: str) -> str:
    bundle = build_bundle(tag)
    os.makedirs(OUT, exist_ok=True)
    ev = []
    us = lambda t: int(t * 1e6)

    def meta(pid, tid, pname=None, tname=None):
        if pname is not None:
            ev.append(dict(ph="M", name="process_name", pid=pid, tid=0,
                           args=dict(name=pname)))
        if tname is not None:
            ev.append(dict(ph="M", name="thread_name", pid=pid, tid=tid,
                           args=dict(name=tname)))

    steps = bundle.get("steps") or []
    sids = sorted({e[0] for _, ents in steps for e in ents})
    meta(1, 0, pname="engine steps (per session)")
    for sid in sids:
        meta(1, sid, tname=f"sid {sid}")
    for i, (t, ents) in enumerate(steps):
        dur = (steps[i+1][0] - t) if i + 1 < len(steps) else 0.021
        if dur > 0.5: dur = 0.021
        for sid, n, enc in ents:
            ev.append(dict(ph="X", pid=1, tid=sid, ts=us(t), dur=max(us(dur), 1),
                           name=(f"prefill+enc {n}tok" if n >= 40 else "decode"),
                           args=dict(tokens=n, batch=len(ents),
                                     step_ms=round(dur * 1000, 1))))
    for sid, st in (bundle.get("starve") or {}).items():
        ev.append(dict(ph="i", s="t", pid=1, tid=int(sid), ts=us(st),
                       name=f"STARVED (last token, sid {sid})"))

    meta(2, 1, pname="gateway", tname="audio ticks")
    for t in bundle.get("ticks") or []:
        ev.append(dict(ph="i", s="t", pid=2, tid=1, ts=us(t), name="tick"))

    meta(3, 1, pname="scheduler", tname="evictions")
    for k, t in enumerate(bundle.get("evictions") or []):
        ev.append(dict(ph="i", s="p", pid=3, tid=1, ts=us(t), name=f"EVICTION #{k+1}"))

    for t, kv, run, wait, pre in bundle.get("kv") or []:
        ev.append(dict(ph="C", pid=3, ts=us(t), name="KV pool %",
                       args=dict(pct=round(kv * 100, 1))))
        ev.append(dict(ph="C", pid=3, ts=us(t), name="requests",
                       args=dict(run=run, wait=wait)))
        ev.append(dict(ph="C", pid=3, ts=us(t), name="evictions (cum)",
                       args=dict(n=pre)))
    for t, u in bundle.get("smi") or []:
        if t >= 0:
            ev.append(dict(ph="C", pid=3, ts=us(t), name="GPU SM util %",
                           args=dict(pct=u)))

    path = f"{OUT}/{tag}.trace.json.gz"
    with gzip.open(path, "wt") as f:
        json.dump(dict(traceEvents=ev, displayTimeUnit="ms"), f,
                  separators=(",", ":"))
    return path


if __name__ == "__main__":
    for tag in sys.argv[1:]:
        p = export(tag)
        print(f"wrote {p} ({os.path.getsize(p)//1024} KiB)")
