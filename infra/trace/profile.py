"""Create a standalone interactive profile from an existing Perfetto export.

The source trace is immutable. This presentation layer neither reconstructs
GPU execution from scheduler intervals nor fills uncaptured device activity.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .bundle import resolve_run
from .perfetto import TRACE_NAME, METADATA_NAME, sha256, derived_directory


PROFILE_NAME = "profile.html"
PROFILE_METADATA = "profile.metadata.json"
TEMPLATE = Path(__file__).with_name("profile_view.html")


def build_profile(trace: dict, manifest: dict, status: dict, client: dict | None = None) -> dict:
    events = trace["traceEvents"]
    ticks = [e["ts"] for e in events if e.get("pid") == 1 and e.get("name") == "tick"]
    timed = [e for e in events if "ts" in e and e.get("ph") in ("X", "i", "C")]
    if not timed:
        raise ValueError("trace contains no timed events")
    origin = min(ticks) if ticks else min(e["ts"] for e in timed)
    names = {(e["pid"], e.get("tid")): e["args"]["name"] for e in events
             if e.get("ph") == "M" and e["name"] == "thread_name"}
    tracks = {}
    copies = defaultdict(dict)
    gpu_times = []
    gpu_count = 0

    def track(key, label, scope, session=0):
        if key not in tracks:
            tracks[key] = dict(label=label, scope=scope, session=session, events=[])
        return tracks[key]

    for event in timed:
        pid, name, args = event["pid"], event["name"], event.get("args", {})
        start = (event["ts"] - origin) / 1e6
        duration = event.get("dur", 0) / 1e6
        row = [start, duration, name, args, event["ph"]]
        lane = None
        if pid == 100 and event["ph"] == "X":
            tid = event["tid"]
            lane = track((0, tid), names.get((pid, tid), f"GPU stream {tid}"), "gpu")
            gpu_times.extend((start, start + duration))
            gpu_count += 1
            if "transfer_id" in args:
                copies[str(args["transfer_id"])].setdefault("gpu", []).append(row)
        elif pid == 101:
            if args.get("direction") in ("H2D", "D2H"):
                direction = args["direction"]
                lane = track((1, direction), f"CopyService · {direction}", "host")
            if "transfer_id" in args:
                copies[str(args["transfer_id"])][args["event"]] = row
        elif pid == 1 and event["ph"] in ("X", "i"):
            sid = event.get("tid", 0)
            if not 0 < sid < 10**9:
                continue
            if args.get("timing_scope") == "CPU scheduler observation":
                part, label = 1, "scheduler"
            elif name in ("ingest queue", "feature extraction", "loop handoff", "admit", "tick"):
                part, label = 0, "input"
            else:
                part, label = 2, "KV / lifecycle"
            lane = track((3, sid, part), f"S{sid} · {label}", label, sid)
        elif pid == 2 and event["ph"] == "X":
            lane = track((2, 0), "Gateway · releases", "host")
        elif pid == 3 and event["ph"] == "C" and name == "KV pool":
            lane = track((4, 0), "GPU KV pool · %", "counter")
        if lane is not None:
            lane["events"].append(row)

    lanes = [tracks[k] for k in sorted(tracks)]
    for lane in lanes:
        lane["events"].sort(key=lambda r: r[0])
    bounds = [(e["ts"] - origin) / 1e6 for e in timed]
    ends = [(e["ts"] + e.get("dur", 0) - origin) / 1e6 for e in timed]
    gpu_extent = [min(gpu_times), max(gpu_times)] if gpu_times else None
    config = manifest.get("config", {})
    sessions = sorted({lane["session"] for lane in lanes if lane["session"]})
    attributed = [value for value in copies.values() if value.get("gpu")]
    schedule_times = sorted({(e["ts"] - origin) / 1e6 for e in timed
                             if e["pid"] == 1
                             and e.get("args", {}).get("timing_scope") == "CPU scheduler observation"
                             and e["ts"] >= origin})
    # These are gaps between CPU observations, not measured GPU idle spans.
    gaps = [[a, b] for a, b in zip(schedule_times, schedule_times[1:]) if b - a > .5]
    return {
        "run_id": manifest.get("run_id", "unknown"), "status": status.get("state", "unknown"),
        "sessions": sessions, "config": config, "tracks": lanes, "transfers": copies,
        "cohort_makespan_s": (client or {}).get("makespan_s")
            if (client or {}).get("kind") == "finite_cohort" else None,
        "bounds": [min(bounds), max(ends)], "business": [0, max(ends)],
        "gpu_extent": gpu_extent, "gpu_count": gpu_count,
        "captured_kv_transfers": len(attributed),
        "origin": "first periodic input" if ticks else "first recorded event",
        "perfetto_offset_s": origin / 1e6, "schedule_gaps": gaps,
    }


def export(source: str | Path, *, variant: str | None = None) -> str:
    directory = resolve_run(source).directory
    derived = derived_directory(directory, variant)
    trace_path, trace_meta_path = derived / TRACE_NAME, derived / METADATA_NAME
    target, metadata_path = derived / PROFILE_NAME, derived / PROFILE_METADATA
    if target.exists() or metadata_path.exists():
        raise FileExistsError("profile already exists; retained exports are never overwritten")
    trace_meta = json.loads(trace_meta_path.read_text())
    if sha256(trace_path) != trace_meta["sha256"]:
        raise ValueError("Perfetto trace hash does not match its metadata")
    for name, info in trace_meta["source_artifacts"].items():
        if sha256(directory / name) != info["sha256"]:
            raise ValueError(f"source artifact changed after trace export: {name}")
    with gzip.open(trace_path, "rt", encoding="utf-8") as handle:
        trace = json.load(handle)
    manifest = json.loads((directory / "manifest.json").read_text())
    status = json.loads((directory / "status.json").read_text())
    client_path = directory / "client.json"
    client = json.loads(client_path.read_text()) if client_path.is_file() else {}
    data = build_profile(trace, manifest, status, client)
    encoded = base64.b64encode(gzip.compress(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(), mtime=0)).decode()
    html = TEMPLATE.read_text().replace("__PROFILE_DATA__", encoded)
    metadata = {
        "schema_version": 2, "run_id": directory.name,
        "source_trace_sha256": sha256(trace_path),
        "source_trace_metadata_sha256": sha256(trace_meta_path),
        "source_client_sha256": sha256(client_path) if client_path.is_file() else None,
        "generator_sha256": sha256(Path(__file__)), "template_sha256": sha256(TEMPLATE),
        "profile_sha256": hashlib.sha256(html.encode()).hexdigest(),
        "gpu_extent_basis": "first to last observed GPU activity; not a whole-run coverage guarantee",
        "time_origin": data["origin"],
    }
    created = []
    try:
        with target.open("x", encoding="utf-8") as handle:
            created.append(target)
            handle.write(html)
        with metadata_path.open("x", encoding="utf-8") as handle:
            created.append(metadata_path)
            json.dump(metadata, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return str(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="run directory or run ID with an existing Perfetto export")
    parser.add_argument("--variant", help="read/write a named subdirectory under derived/")
    args = parser.parse_args()
    print(f"wrote {export(args.source, variant=args.variant)}")


if __name__ == "__main__":
    main()
