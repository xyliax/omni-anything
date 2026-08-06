#!/usr/bin/env python3
"""Build a self-contained interactive HTML timeline viewer for one run.

Usage: python3 harness/viz/build_viewer.py <tag> [<tag2> ...]
       (tag = e.g. e1schtr_n8_d600; logs read from results/paper/baseline/<tag>_*)

Emits results/viz/<tag>.html — double-click to open, no server needed.
Clock alignment onto one experiment axis (t=0 = first real gateway tick) uses the
same warmup anchors as the plot scripts. Missing logs degrade gracefully
(runs without a scheduler trace simply have no lanes track).
"""
import json, os, re, sys

BASE = "results/paper/baseline"
OUT = "results/viz"
TMPL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timeline_template.html")


def build(tag: str) -> str:
    bundle = {"tag": tag}

    # ---- perreq: anchors + tick times + per-sid starve ----
    warm_P = None; t0 = None; ticks = set()
    T = {}
    pr = f"{BASE}/{tag}_perreq.log"
    if os.path.exists(pr):
        for ln in open(pr):
            k, t, sid, *r = ln.split()
            t, sid = float(t), int(sid)
            if sid == 10**9:
                if k == "P" and warm_P is None: warm_P = t
                continue
            if k == "P":
                if t0 is None: t0 = t
                ticks.add(round(t - t0, 2))
            elif k == "T":
                T.setdefault(sid, []).append((t, int(r[0])))
    if t0 is not None:
        bundle["ticks"] = sorted(ticks)
        starve = {}
        for sid, ts in T.items():
            last = ts[0][0]
            for a, b in zip(ts, ts[1:]):
                if b[1] > a[1]: last = b[0]
            starve[sid] = round(last - t0, 1)
        bundle["starve"] = starve

    # ---- kv.log: pool / run / wait / cumulative preemptions ----
    kvf = f"{BASE}/{tag}_kv.log"
    if os.path.exists(kvf):
        rows = []
        for ln in open(kvf):
            m = re.match(r"([\d.]+) kv=([\d.]+) run=(\d+) wait=(\d+) evict=\d+(?: pre=(\d+))?", ln)
            if m:
                rows.append([float(m.group(1)), float(m.group(2)), int(m.group(3)),
                             int(m.group(4)), int(m.group(5) or 0)])
        if rows and warm_P is not None and t0 is not None:
            off = t0 - (warm_P - rows[0][0])
            kv = [[round(r[0] - off, 2)] + r[1:] for r in rows]
            bundle["kv"] = kv
            bundle["evictions"] = [kv[i][0] for i in range(1, len(kv)) if kv[i][4] > kv[i-1][4]]

    # ---- scheduler trace: per-step per-request lanes ----
    sf = f"{BASE}/{tag}_sched.log"
    if os.path.exists(sf):
        steps = []; first_real = None
        for ln in open(sf):
            parts = ln.split(); tt = float(parts[0]); ents = []
            for p in parts[1:]:
                rid, ntok = p.rsplit(":", 1)
                enc = 1 if ntok.endswith("E") else 0
                n = int(ntok[:-1] if enc else ntok)
                sid = int(re.match(r"s(\d+)e", rid).group(1))
                if sid == 10**9: continue
                ents.append([sid, n, enc])
            if ents:
                if first_real is None: first_real = tt
                steps.append([tt, ents])
        if steps:
            bundle["steps"] = [[round(t - first_real, 3), e] for t, e in steps]

    # ---- smi ----
    sm = f"{BASE}/{tag}_smi.log"
    if os.path.exists(sm):
        u = [int(l.split()[0]) for l in open(sm) if "%" in l]
        bundle["smi"] = [[round(5*i - 2.5, 1), v] for i, v in enumerate(u)]

    # ---- cross-clock alignment: the P-family (ticks/kv/starve, perf clock) and the
    # scheduler steps (unix clock) have different origins. Anchor them with the physical
    # invariant "no chunk's first prefill precedes its own push by construction": shift the
    # P-family so min(prefill_start - nearest_preceding_tick) == +3ms.
    if bundle.get("ticks") and bundle.get("steps"):
        pf = [t for t, ents in bundle["steps"] if any(n >= 40 for _, n, _ in ents)]
        import bisect as _bi
        ds = []
        for st in pf:
            i = _bi.bisect_right(bundle["ticks"], st) - 1
            lo = max(0, i - 1)
            for j in range(lo, min(i + 2, len(bundle["ticks"]))):
                d = st - bundle["ticks"][j]
                if -1.0 < d < 1.0: ds.append(d)
        if ds:
            shift = round(min(ds) - 0.003, 3)
            bundle["ticks"] = [round(t + shift, 3) for t in bundle["ticks"]]
            if "kv" in bundle:
                bundle["kv"] = [[round(r[0] + shift, 2)] + r[1:] for r in bundle["kv"]]
                bundle["evictions"] = [round(t + shift, 2) for t in bundle.get("evictions", [])]
            if "starve" in bundle:
                bundle["starve"] = {k: round(v + shift, 1) for k, v in bundle["starve"].items()}
    tmax = 0
    for key, idx in (("kv", 0), ("steps", 0), ("smi", 0)):
        if key in bundle and bundle[key]:
            tmax = max(tmax, bundle[key][-1][0])
    bundle["t_end"] = round(tmax + 5, 1)

    os.makedirs(OUT, exist_ok=True)
    html = open(TMPL).read().replace("__DATA_JSON__", json.dumps(bundle, separators=(",", ":")))
    path = f"{OUT}/{tag}.html"
    open(path, "w").write(html)
    return path


if __name__ == "__main__":
    for tag in sys.argv[1:]:
        p = build(tag)
        print(f"wrote {p}  ({os.path.getsize(p)//1024} KiB)")
