#!/usr/bin/env python3
"""Export any retained experiment run as a Perfetto-compatible timeline.

The exporter owns presentation only; parsing lives in :mod:`infra.trace.bundle`.
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
import re
from pathlib import Path
from typing import Any, Iterable

from .bundle import ROOT, build_bundle, resolve_run
from .parse import is_prefill
from .gpu_activity import stream_labels


TRACE_NAME = "timeline.trace.json.gz"
METADATA_NAME = "timeline.trace.metadata.json"
METADATA_SCHEMA_VERSION = 10
# Fallback duration for the final or isolated engine step (median decode step).
DEFAULT_STEP_S = 0.021
SEGMENT_GAP_S = 0.5
# Prefills beyond this are not normal periodic chunks: initial-context preloading or (after a
# eviction) suspect recompute of a region that should have reloaded from CPU.
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
        *,
        precise: bool = False,
    ) -> None:
        self.events.append(
            {
                "ph": "X",
                "pid": pid,
                "tid": tid,
                "ts": start_s * 1_000_000 if precise else self.micros(start_s),
                "dur": duration_s * 1_000_000 if precise else max(self.micros(duration_s), 1),
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
    This interval can contain CPU work and waits, including in steady state.
    Device execution is rendered separately when CUPTI evidence is present.
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
                # shape; anything larger is either initial-context preloading or a
                # partially evicted/evicted region being RECOMPUTED instead of reloaded —
                # flag it so a broken reload path shows on the timeline.
                phase = "prefill+encoder" if encoder else "prefill"
                size = " LARGE" if tokens > LARGE_PREFILL_TOKENS else ""
                name = f"{phase}{size} ({tokens} tokens)"
            else:
                name = "decode"
            builder.slice(
                1,
                session,
                start,
                duration,
                name,
                {
                    "timing_scope": "CPU scheduler observation",
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
    for session, time_s in (bundle.get("last_token_growth") or {}).items():
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

    # L/R delimit scheduler-observed windows, not DMA execution. Demand R is
    # emitted when the scheduler promotes the waiting request; prefetch R is
    # emitted when it handles the copy completion and publishes cached blocks.
    # Both windows can include dispatch, copy submission, and completion delay.
    for eviction in bundle.get("kv_evictions") or []:
        builder.instant(
            1,
            eviction["session"],
            eviction["time"],
            f"KV EVICT -{eviction['evicted']} blocks",
            {
                "owned_before": eviction["owned_before"],
                "evicted": eviction["evicted"],
                "host_backed": eviction["host_backed"],
                "pool_usage_drop": round(
                    eviction["usage_before"] - eviction["usage_after"], 4
                ),
            },
        )
    geometry = (
        ((bundle.get("manifest") or {}).get("config") or {}).get("model") or {}
    ).get("kv_geometry") or {}
    bytes_per_token = geometry.get("bytes_per_token")
    for reload_event in bundle.get("reloads") or []:
        trigger = reload_event.get("trigger", "demand")
        kind = "KV prefetch window" if trigger == "prefetch" else "KV reload window"
        args = {
            "cpu_tok": reload_event["cpu_tok"],
            "gpu_tok": reload_event["gpu_tok"],
            "trigger": trigger,
            "timing_scope": "scheduler-observed L-to-R window; not DMA duration",
            "start_event": "prefetch queued" if trigger == "prefetch" else "load allocation",
            "end_event": (
                "prefetch completion handled" if trigger == "prefetch" else "request promotion"
            ),
        }
        if type(bytes_per_token) is int and bytes_per_token > 0:
            # Logical payload from this run's model, not measured PCIe traffic:
            # batching, duplicate copies, padding, and layout require copy events.
            args["logical_kv_bytes"] = reload_event["cpu_tok"] * bytes_per_token
            args["bytes_basis"] = "cpu_tok * manifest.config.model.kv_geometry.bytes_per_token"
        if reload_event["end"] is not None:
            builder.slice(
                1,
                reload_event["session"],
                reload_event["time"],
                reload_event["end"] - reload_event["time"],
                f"{kind} ({reload_event['cpu_tok']} tok)",
                args,
            )
        else:
            builder.instant(
                1,
                reload_event["session"],
                reload_event["time"],
                f"{kind} (completion unobserved)",
                args,
            )
    for backing in bundle.get("host_backing") or []:
        builder.instant(
            1,
            backing["session"],
            backing["time"],
            f"KV host backing (+{backing['blocks']} blocks)",
            {"blocks": backing["blocks"]},
        )
    if bundle.get("residency"):
        # per-session residency counters from the uniform sampler
        # (residency.log, both evaluated systems): baseline shows the context-growth
        # staircase, conveyor the eviction sawtooth — same track, same source.
        builder.process(4, "kv residency (blocks, sampled)")
        for time_s, entries in bundle["residency"]:
            for session, blocks in entries:
                builder.counter(4, time_s, f"session {session}", {"blocks": blocks})
    elif bundle.get("kv_evictions"):
        # LEGACY fallback (runs predating residency.log): sawtooth sampled at
        # eviction instants, three points per cycle: the grip just before release
        # (upper envelope = context growth), the pinned floor just after
        # (held - evicted), and the restoration at reload admission
        # (approximated by the preceding eviction's held).
        builder.process(4, "kv residency (blocks, sampled at evictions)")
        events: list[tuple[float, int, int]] = []
        for eviction in bundle["kv_evictions"]:
            events.append(
                (eviction["time"], eviction["session"], eviction["owned_before"])
            )
            events.append(
                (
                    eviction["time"] + 0.001,
                    eviction["session"],
                    eviction["owned_before"] - eviction["evicted"],
                )
            )
        for reload_event in bundle.get("reloads") or []:
            prior = [
                p for p in bundle["kv_evictions"]
                if p["session"] == reload_event["session"]
                and p["time"] < reload_event["time"]
            ]
            if prior:
                events.append(
                    (
                        reload_event["time"],
                        reload_event["session"],
                        prior[-1]["owned_before"],
                    )
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
        for row in firings:
            delivered = row.get("deliv") or {}
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


def add_gpu_activity(builder: TraceBuilder, bundle: dict[str, Any]) -> int:
    activities = bundle.get("gpu_activities") or []
    labels = stream_labels(activities)
    lanes = {}
    for row in activities:
        key = (row["device"], row["context"], row["stream"])
        if key not in lanes:
            lanes[key] = len(lanes) + 1
        lane = lanes[key]
        builder.process(100, "GPU execution (CUPTI)")
        builder.thread(100, lane, labels[key])
        args = {**row["args"], "device": key[0], "context": key[1], "stream": key[2],
                "activity_kind": row["category"], "stream_role": labels[key]}
        builder.slice(100, lane, row["time"], row["duration"], row["name"], args, precise=True)
    rows = bundle.get("transfer_events") or []
    if rows:
        builder.process(101, "Session Manager transfers (CPU control)")
    for row in rows:
        transfer = row.get("transfer_id", 0)
        lane = {"H2D": 1, "D2H": 2}.get(row.get("direction"), 0)
        builder.thread(101, lane, f"{row.get('direction', 'session')} control")
        args = {k: v for k, v in row.items() if k not in ("time", "submit_start", "submit_end")}
        if row["event"] == "submitted":
            builder.slice(101, lane, row["submit_start"], row["submit_end"] - row["submit_start"],
                          f"submit {row['direction']} #{transfer}", args)
        else:
            builder.instant(101, lane, row["time"], f"{row['event']} #{transfer}", args)
    return len(activities)


def derived_directory(run: Path, variant: str | None = None) -> Path:
    """Keep revised presentations beside, without replacing, earlier exports."""
    if variant is not None and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", variant):
        raise ValueError("variant must be a simple name containing letters, digits, _ or -")
    return run / "derived" / variant if variant is not None else run / "derived"


def export(source: str | Path, *, variant: str | None = None) -> str:
    files = resolve_run(source)
    output_dir = derived_directory(files.directory, variant)
    bundle = build_bundle(files.directory)
    trace_path = output_dir / TRACE_NAME
    metadata_path = output_dir / METADATA_NAME
    collisions = [path for path in (trace_path, metadata_path) if path.exists()]
    if collisions:
        raise FileExistsError(f"derived artifact already exists: {collisions[0]}")

    builder = TraceBuilder()
    engine_slices = add_engine(builder, bundle)
    gpu_activities = add_gpu_activity(builder, bundle)
    if not engine_slices and not gpu_activities:
        raise MissingTimelineDataError(f"run {files.run_id!r} has no supported timeline data")
    shift_s = builder.shift_nonnegative()

    output_dir.mkdir(exist_ok=True, parents=True)
    created = []
    try:
        with trace_path.open("xb") as raw:
            created.append(trace_path)
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
            "gpu_activities": gpu_activities,
            "clock_alignment": bundle.get("clock_alignment"),
            "global_time_shift_s": shift_s,
            "bytes": trace_path.stat().st_size,
            "sha256": sha256(trace_path),
            "generator_sources": {
                name: sha256(Path(__file__).with_name(name))
                for name in ("perfetto.py", "gpu_activity.py", "bundle.py", "parse.py")
            },
        }
        with metadata_path.open("x", encoding="utf-8") as handle:
            created.append(metadata_path)
            json.dump(metadata, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return str(trace_path)


def discover_runs() -> Iterable[Path]:
    root = ROOT / "results"
    return sorted(
        run
        for experiment in root.iterdir()
        if experiment.is_dir()
        for run in experiment.iterdir()
        if run.is_dir() and run.name != "aggregates"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export experiment runs to Perfetto timelines.")
    parser.add_argument("runs", nargs="*", help="run path, experiment/run-id, or unique run ID")
    parser.add_argument("--all", action="store_true", help="export every retained run")
    parser.add_argument("--variant", help="write a fresh named subdirectory under derived/")
    args = parser.parse_args()
    if not args.runs and not args.all:
        parser.error("provide at least one run or --all")
    sources: Iterable[str | Path] = [*args.runs]
    if args.all:
        sources = [*sources, *discover_runs()]
    for source in sources:
        try:
            path = export(source, variant=args.variant)
        except (FileExistsError, FileNotFoundError, MissingTimelineDataError, ValueError) as error:
            parser.error(str(error))
        print(f"wrote {path} ({Path(path).stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
