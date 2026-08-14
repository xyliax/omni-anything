#!/usr/bin/env python3
"""Export any retained experiment run as a Perfetto-compatible timeline.

The exporter owns presentation only; parsing lives in :mod:`tracekit.bundle`.
``scheduler.log`` steps become per-session engine lanes with a batch counter,
gateway ticks, and KV/GPU runtime counters.

Open the generated ``derived/timeline.trace.json.gz`` at ui.perfetto.dev.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Iterable

from .bundle import ROOT, _config_value, build_bundle, resolve_run
from .parse import is_prefill


TRACE_NAME = "timeline.trace.json.gz"
METADATA_NAME = "timeline.trace.metadata.json"
METADATA_SCHEMA_VERSION = 7
# Fallback duration for the final or isolated engine step (median decode step).
DEFAULT_STEP_S = 0.021
SEGMENT_GAP_S = 0.5
# Prefills beyond this are not per-tick chunks: warm-start seeding or (after a
# park) suspect recompute of a region that should have reloaded from CPU.
LARGE_PREFILL_TOKENS = 400


class MissingTimelineDataError(ValueError):
    """A run has no supported timed artifacts."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class TraceBuilder:
    """Small Chrome-trace writer with stable process and thread metadata."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self._processes: set[int] = set()
        self._threads: set[tuple[int, int]] = set()

    @staticmethod
    def micros(seconds: float) -> int:
        return round(seconds * 1_000_000)

    def process(self, pid: int, name: str) -> None:
        if pid in self._processes:
            return
        self._processes.add(pid)
        self.events.append(
            {"ph": "M", "name": "process_name", "pid": pid, "tid": 0, "args": {"name": name}}
        )

    def thread(self, pid: int, tid: int, name: str) -> None:
        if (pid, tid) in self._threads:
            return
        self._threads.add((pid, tid))
        self.events.append(
            {"ph": "M", "name": "thread_name", "pid": pid, "tid": tid, "args": {"name": name}}
        )

    def slice(
        self,
        pid: int,
        tid: int,
        start_s: float,
        duration_s: float,
        name: str,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(
            {
                "ph": "X",
                "pid": pid,
                "tid": tid,
                "ts": self.micros(start_s),
                "dur": max(self.micros(duration_s), 1),
                "name": name,
                "args": args or {},
            }
        )

    def instant(
        self,
        pid: int,
        tid: int,
        time_s: float,
        name: str,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(
            {
                "ph": "i",
                "s": "t",
                "pid": pid,
                "tid": tid,
                "ts": self.micros(time_s),
                "name": name,
                "args": args or {},
            }
        )

    def counter(
        self,
        pid: int,
        time_s: float,
        name: str,
        args: dict[str, Any],
    ) -> None:
        self.events.append(
            {"ph": "C", "pid": pid, "ts": self.micros(time_s), "name": name, "args": args}
        )

    def shift_nonnegative(self) -> float:
        """Translate the whole trace so pre-zero timestamps display.

        Clock alignment can push early kv/tick rows slightly before zero.
        The amount is recorded in metadata as ``global_time_shift_s`` so a
        reader can undo it.
        """
        timestamps = [event["ts"] for event in self.events if "ts" in event]
        shift_us = max(0, -min(timestamps, default=0))
        if shift_us:
            for event in self.events:
                if "ts" in event:
                    event["ts"] += shift_us
        return shift_us / 1_000_000


def add_engine(builder: TraceBuilder, bundle: dict[str, Any]) -> int:
    """Render the engine run: per-session lanes, ticks, runtime counters.

    HONESTY BOUNDARY: the lanes render the SCHEDULING timeline — each slice
    spans consecutive schedule() calls and is labeled with the batch content.
    In steady state that width numerically equals the GPU execution time; at
    transitions (around prefills) it does not, and no execution timestamps
    exist in the evidence (FINDINGS F3: never draw beyond the instrument).
    """
    steps = bundle.get("steps") or []
    if not steps:
        return 0
    slices = 0
    builder.process(1, "engine schedule steps (per session)")
    sessions = sorted({entry[0] for _, entries in steps for entry in entries})
    for session in sessions:
        builder.thread(1, session, f"session {session}")
    for index, (start, entries) in enumerate(steps):
        duration = steps[index + 1][0] - start if index + 1 < len(steps) else DEFAULT_STEP_S
        if duration <= 0 or duration > SEGMENT_GAP_S:
            duration = DEFAULT_STEP_S
        for session, tokens, encoder in entries:
            if is_prefill(tokens, encoder):
                # Chunk-sized prefills (~50-200 tok) are the healthy per-tick
                # shape; anything larger is either warm-start seeding or a
                # parked/evicted region being RECOMPUTED instead of reloaded —
                # flag it so a broken reload path shows on the timeline.
                name = (
                    f"sched prefill LARGE ({tokens} tokens)"
                    if tokens > LARGE_PREFILL_TOKENS
                    else f"sched prefill+encoder ({tokens} tokens)"
                )
            else:
                name = "sched decode"
            builder.slice(
                1,
                session,
                start,
                duration,
                name,
                {
                    "tokens": tokens,
                    "encoder": bool(encoder),
                    "batch": len(entries),
                    "step_ms": round(duration * 1000, 3),
                    "recompute_suspect": tokens > LARGE_PREFILL_TOKENS,
                },
            )
            slices += 1
        builder.counter(1, start, "batch (concurrent sessions)", {"sessions": len(entries)})
        next_start = steps[index + 1][0] if index + 1 < len(steps) else None
        if next_start is None or next_start - start > SEGMENT_GAP_S:
            builder.counter(1, start + DEFAULT_STEP_S, "batch (concurrent sessions)", {"sessions": 0})
    for session, time_s in (bundle.get("starve") or {}).items():
        # honest label: this is simply the LAST time tokens grew — healthy
        # sessions get one at run end too; only an EARLY marker means starvation.
        builder.instant(1, int(session), time_s, "last token growth", {"session": int(session)})
    # Each session ticks on its own grid (staggered gateways spread the grids);
    # mark every push on its session's lane.
    for session, times in (bundle.get("pushes") or {}).items():
        for time_s in times:
            builder.instant(1, int(session), time_s, "tick")

    # Ingest pipeline (per_request.log I-stations): fills the tick->reload gap
    # with what actually happens there — thread-pool queueing, feature
    # extraction (the ~290ms per-chunk floor), and engine admission. The
    # optimization surface between a tick and its compute slice lives here.
    for session, records in (bundle.get("ingest") or {}).items():
        sid = int(session)
        for record in records:
            for start_key, end_key, name in (
                ("iq", "is", "ingest queue"),
                ("is", "ie", "feature extraction"),
                ("ie", "ir", "loop handoff"),
                ("ir", "ia", "admit"),
            ):
                start = record.get(start_key)
                end = record.get(end_key)
                if start is not None and end is not None and end > start:
                    builder.slice(
                        1, sid, start, end - start, name,
                        {"ms": round((end - start) * 1000, 1)},
                    )

    # KV management on the session lanes (park.log, exact epoch alignment):
    # a PARK instant releases the session's grip and destroys its tail; the
    # following "KV reload" slice is the CPU->GPU window on resume
    # (WAITING_FOR_REMOTE_KVS admission -> completion). A reload slice that
    # pushes into the compute slice — or a LARGE prefill instead of a reload —
    # is the mechanism failing on-screen.
    for park in bundle.get("parks") or []:
        builder.instant(
            1,
            park["session"],
            park["time"],
            f"PARK -{park['evicted']} blocks",
            {
                "held": park["held"],
                "evicted": park["evicted"],
                "cpu_covered": park["cpu_covered"],
                "pool_usage_drop": round(
                    park["usage_before"] - park["usage_after"], 4
                ),
            },
        )
    for reload_event in bundle.get("reloads") or []:
        if reload_event["end"] is not None:
            builder.slice(
                1,
                reload_event["session"],
                reload_event["time"],
                reload_event["end"] - reload_event["time"],
                f"KV reload ({reload_event['cpu_tok']} tok)",
                {"cpu_tok": reload_event["cpu_tok"], "gpu_tok": reload_event["gpu_tok"]},
            )
        else:
            builder.instant(
                1,
                reload_event["session"],
                reload_event["time"],
                "KV reload started (never completed)",
                {"cpu_tok": reload_event["cpu_tok"]},
            )
    for offload in bundle.get("offloads") or []:
        builder.instant(
            1,
            offload["session"],
            offload["time"],
            f"KV mirror ({offload['blocks']} blocks)",
            {"blocks": offload["blocks"]},
        )
    if bundle.get("parks"):
        # per-session residency sawtooth, three points per cycle: the grip just
        # before release (upper envelope = context growth), the pinned floor
        # just after (held - evicted), and the restoration at reload admission
        # (approximated by the preceding park's held).
        builder.process(4, "kv residency (blocks, sampled at parks)")
        events: list[tuple[float, int, int]] = []
        for park in bundle["parks"]:
            events.append((park["time"], park["session"], park["held"]))
            events.append(
                (park["time"] + 0.001, park["session"], park["held"] - park["evicted"])
            )
        for reload_event in bundle.get("reloads") or []:
            prior = [
                p for p in bundle["parks"]
                if p["session"] == reload_event["session"]
                and p["time"] < reload_event["time"]
            ]
            if prior:
                events.append(
                    (reload_event["time"], reload_event["session"], prior[-1]["held"])
                )
        for time_s, session, blocks in sorted(events):
            builder.counter(4, time_s, f"session {session}", {"blocks": blocks})

    builder.process(2, "gateway")
    firings = bundle.get("gateway_firings") or []
    if firings:
        # Real per-firing evidence (gateway_ticks.log, gateway's own epoch clock):
        # slice = walk+stage+gRPC of one slot firing; lateness is measured against
        # the wheel's absolute grid at the source, delivered token counts at the
        # delivery point. The worker-side push clusters stay on their own track —
        # the gap between the two tracks is the gRPC/lock segment.
        builder.thread(2, 1, "slot firings (gateway clock)")
        builder.thread(2, 2, "push clusters (worker-side)")
        tpt = int(_config_value(bundle.get("manifest"), "tokens_per_tick") or 0)
        # STARVED marks mirror the gateway's exemption: starvation counting
        # begins at a session's first FULL (>= tpt) delivery — everything
        # before that is take-from-stock pipeline ramp, not falling behind.
        seen_full: set = set()
        for row in firings:
            delivered = row.get("deliv") or {}
            starved = (
                sorted(
                    sid for sid, tok in delivered.items()
                    if tok < tpt and sid in seen_full
                )
                if tpt else []
            )
            seen_full.update(sid for sid, tok in delivered.items() if tok >= tpt)
            builder.slice(
                2,
                1,
                row["time"],
                (row.get("sample_ms", 0.0) + row.get("grpc_ms", 0.0)) / 1000.0,
                f"slot {row['slot']}" if row["n"] else f"slot {row['slot']} (empty)",
                {
                    "late_ms": row.get("late_ms"),
                    "sessions": row["n"],
                    "grpc_ms": row.get("grpc_ms"),
                    "gpu_ms": row.get("gpu_ms"),
                    "delivered": {str(sid): tok for sid, tok in sorted(delivered.items())},
                },
            )
            if starved:
                builder.instant(
                    2, 1, row["time"], f"STARVED delivery x{len(starved)}",
                    {"sessions": starved},
                )
            builder.counter(
                2, row["time"], "delivered tokens/firing",
                {"tokens": sum(delivered.values())},
            )
            builder.counter(2, row["time"], "firing lateness", {"ms": row.get("late_ms", 0.0)})
        for time_s in bundle.get("ticks") or []:
            builder.instant(2, 2, time_s, "push cluster")
    else:
        # Legacy runs without gateway_ticks.log: firing instants are INFERRED by
        # clustering worker-side pushes (downstream of gRPC + lock, not a source
        # measurement).
        builder.thread(2, 1, "firings (inferred from push clusters)")
        for time_s in bundle.get("ticks") or []:
            builder.instant(2, 1, time_s, "firing")

    builder.process(3, "runtime counters")
    builder.thread(3, 1, "scheduler events")
    for index, time_s in enumerate(bundle.get("preemptions") or [], 1):
        builder.instant(3, 1, time_s, f"preemption #{index}")
    for time_s, kv, _running, _waiting, _preemptions in bundle.get("kv") or []:
        builder.counter(3, time_s, "KV pool", {"percent": round(kv * 100, 1)})
    for time_s, utilization in bundle.get("smi") or []:
        if time_s >= 0:
            builder.counter(3, time_s, "GPU SM utilization", {"percent": utilization})
    return slices


def source_hashes(run_dir: Path) -> dict[str, dict[str, Any]]:
    """Byte size and SHA-256 of every evidence file the export was built from."""
    return {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in sorted(run_dir.iterdir())
        if path.is_file() and not path.name.startswith(".")
    }


def export(source: str | Path) -> str:
    files = resolve_run(source)
    bundle = build_bundle(files.directory)
    output_dir = files.directory / "derived"
    trace_path = output_dir / TRACE_NAME
    metadata_path = output_dir / METADATA_NAME
    collisions = [path for path in (trace_path, metadata_path) if path.exists()]
    if collisions:
        raise FileExistsError(f"derived artifact already exists: {collisions[0]}")

    builder = TraceBuilder()
    engine_slices = add_engine(builder, bundle)
    if not engine_slices:
        raise MissingTimelineDataError(f"run {files.run_id!r} has no supported timeline data")
    shift_s = builder.shift_nonnegative()

    output_dir.mkdir(exist_ok=True)
    try:
        with trace_path.open("xb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8") as text:
                    json.dump(
                        {"traceEvents": builder.events, "displayTimeUnit": "ms"},
                        text,
                        separators=(",", ":"),
                    )
        metadata = {
            "schema_version": METADATA_SCHEMA_VERSION,
            "artifact": TRACE_NAME,
            "run_id": files.run_id,
            "experiment": files.experiment,
            "source_artifacts": source_hashes(files.directory),
            "events": len(builder.events),
            "engine_slices": engine_slices,
            "clock_alignment": bundle.get("clock_alignment"),
            "global_time_shift_s": shift_s,
            "bytes": trace_path.stat().st_size,
            "sha256": sha256(trace_path),
        }
        with metadata_path.open("x", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except BaseException:
        trace_path.unlink(missing_ok=True)
        metadata_path.unlink(missing_ok=True)
        raise
    return str(trace_path)


def discover_runs() -> Iterable[Path]:
    root = ROOT / "results"
    return sorted(run for runs in root.glob("*/runs") for run in runs.iterdir() if run.is_dir())


def main() -> None:
    parser = argparse.ArgumentParser(description="Export experiment runs to Perfetto timelines.")
    parser.add_argument("runs", nargs="*", help="run path, experiment/run-id, or unique run ID")
    parser.add_argument("--all", action="store_true", help="export every retained run")
    args = parser.parse_args()
    if not args.runs and not args.all:
        parser.error("provide at least one run or --all")
    sources: Iterable[str | Path] = [*args.runs]
    if args.all:
        sources = [*sources, *discover_runs()]
    for source in sources:
        try:
            path = export(source)
        except (FileExistsError, FileNotFoundError, MissingTimelineDataError, ValueError) as error:
            parser.error(str(error))
        print(f"wrote {path} ({Path(path).stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
