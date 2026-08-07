#!/usr/bin/env python3
"""Export any retained experiment run as a Perfetto-compatible timeline.

The exporter owns presentation only. Raw parsing lives in ``bundle.py`` and
E2/E3 replay delegates to the same simulation core that produced the result.
Open the generated ``derived/timeline.trace.json.gz`` at ui.perfetto.dev.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any, Iterable

from .bundle import build_bundle, resolve_run


TRACE_NAME = "timeline.trace.json.gz"
METADATA_NAME = "timeline.trace.metadata.json"


class MissingTimelineDataError(ValueError):
    """A run has no supported timed or measurement artifacts."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repository_path(path: Path) -> str:
    """Prefer a portable repository-relative path, retaining external paths."""
    resolved = path.resolve()
    repository = Path(__file__).resolve().parents[1]
    try:
        return str(resolved.relative_to(repository))
    except ValueError:
        return str(resolved)


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
        timestamps = [event["ts"] for event in self.events if "ts" in event]
        shift_us = max(0, -min(timestamps, default=0))
        if shift_us:
            for event in self.events:
                if "ts" in event:
                    event["ts"] += shift_us
        return shift_us / 1_000_000


def add_e1(
    builder: TraceBuilder,
    bundle: dict[str, Any],
    counts: dict[str, int],
    *,
    process_prefix: str = "",
) -> None:
    steps = bundle.get("steps") or []
    if not steps:
        return
    builder.process(1, f"{process_prefix}engine steps (per session)")
    sessions = sorted({entry[0] for _, entries in steps for entry in entries})
    for session in sessions:
        builder.thread(1, session, f"session {session}")
    for index, (start, entries) in enumerate(steps):
        duration = steps[index + 1][0] - start if index + 1 < len(steps) else 0.021
        if duration <= 0 or duration > 0.5:
            duration = 0.021
        for session, tokens, encoder in entries:
            builder.slice(
                1,
                session,
                start,
                duration,
                f"prefill+encoder ({tokens} tokens)" if tokens >= 40 else "decode",
                {
                    "tokens": tokens,
                    "encoder": bool(encoder),
                    "batch": len(entries),
                    "step_ms": round(duration * 1000, 3),
                },
            )
            counts["engine_slices"] += 1
        builder.counter(1, start, "batch (concurrent sessions)", {"sessions": len(entries)})
        next_start = steps[index + 1][0] if index + 1 < len(steps) else None
        if next_start is None or next_start - start > 0.5:
            builder.counter(1, start + 0.021, "batch (concurrent sessions)", {"sessions": 0})
    for session, time_s in (bundle.get("starve") or {}).items():
        builder.instant(1, int(session), time_s, "STARVED: last token growth", {"session": int(session)})

    builder.process(2, f"{process_prefix}gateway")
    builder.thread(2, 1, "audio ticks")
    for time_s in bundle.get("ticks") or []:
        builder.instant(2, 1, time_s, "tick")

    builder.process(3, f"{process_prefix}runtime counters")
    builder.thread(3, 1, "scheduler events")
    for index, time_s in enumerate(bundle.get("evictions") or [], 1):
        builder.instant(3, 1, time_s, f"eviction #{index}")
    for time_s, kv, _running, waiting, preemptions in bundle.get("kv") or []:
        builder.counter(3, time_s, "KV pool", {"percent": round(kv * 100, 1)})
        builder.counter(3, time_s, "wait queue (1 Hz)", {"requests": waiting})
        builder.counter(3, time_s, "cumulative evictions", {"count": preemptions})
    for time_s, utilization in bundle.get("smi") or []:
        if time_s >= 0:
            builder.counter(3, time_s, "GPU SM utilization", {"percent": utilization})


def _mechanism_replay(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Replay E2/E3 from the exact model inputs stored in the run."""
    from experiments.e2_kv_conveyor.core import ComputeProfile, SimulationConfig, simulate

    manifest = bundle.get("manifest") or {}
    run_dir = Path(bundle["run_dir"])
    link = json.loads((run_dir / "link_calibration.json").read_text(encoding="utf-8"))
    profile_raw = manifest["compute_profile"]
    profile = ComputeProfile(
        source=profile_raw["source"],
        busy_ms_by_batch={int(key): value for key, value in profile_raw["busy_ms_by_batch"].items()},
        decode_step_ms_by_batch={
            int(key): value for key, value in profile_raw["decode_step_ms_by_batch"].items()
        },
        steps_per_tick=profile_raw["steps_per_tick"],
    )
    allowed_config = {field.name for field in fields(SimulationConfig)}
    config = SimulationConfig(
        **{key: value for key, value in manifest["config"].items() if key in allowed_config}
    )
    transfers: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for arm in manifest["arms"]:
        arm_events: list[dict[str, Any]] = []
        _summary, rows = simulate(
            config,
            profile,
            link["samples_ms"],
            conveyor=arm["conveyor"],
            phase_policy=arm["phase_policy"],
            seed=arm["seed"],
            timeline=arm_events,
        )
        events.extend({"arm": arm["name"], **event} for event in arm_events)
        transfers.extend({"arm": arm["name"], **asdict(row)} for row in rows)
    return transfers, events


def mechanism_source_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """Resolve and verify the E1 run that supplies a mechanism run's compute trace."""
    manifest = bundle.get("manifest") or {}
    expected_hash = manifest.get("compute_trace_sha256")
    source_value = (manifest.get("compute_profile") or {}).get("source")
    candidates: list[Path] = []
    if source_value:
        source = Path(source_value).expanduser()
        if source.is_file():
            candidates.append(source)

    repository = Path(__file__).resolve().parents[1]
    candidates.extend(
        path
        for path in repository.glob("results/e1_capacity_bottleneck/runs/*/scheduler.log")
        if path.is_file() and path not in candidates
    )
    for scheduler in candidates:
        if expected_hash and sha256(scheduler) != expected_hash:
            continue
        source_bundle = build_bundle(scheduler.parent)
        if not source_bundle.get("steps"):
            continue
        source_bundle["source_scheduler_sha256"] = sha256(scheduler)
        return source_bundle
    raise FileNotFoundError(
        "cannot resolve the non-empty E1 source run for compute trace "
        f"SHA-256 {expected_hash!r}"
    )


def add_mechanism(
    builder: TraceBuilder, bundle: dict[str, Any], counts: dict[str, int]
) -> None:
    replay_transfers, replay_events = _mechanism_replay(bundle)
    retained = bundle.get("transfers") or []
    if retained and retained != replay_transfers:
        raise ValueError("stored transfers.jsonl differs from deterministic manifest replay")
    transfers = retained or replay_transfers

    manifest = bundle["manifest"]
    summaries = {
        row["arm"]: row
        for row in json.loads(
            (Path(bundle["run_dir"]) / "summary.json").read_text(encoding="utf-8")
        )["arms"]
    }
    arms = [arm["name"] for arm in manifest["arms"]]
    events_by_arm: dict[str, list[dict[str, Any]]] = {arm: [] for arm in arms}
    transfers_by_arm: dict[str, list[dict[str, Any]]] = {arm: [] for arm in arms}
    for event in replay_events:
        events_by_arm[event["arm"]].append(event)
    for transfer in transfers:
        transfers_by_arm[transfer["arm"]].append(transfer)

    for arm_index, arm in enumerate(arms):
        pid = 100 + arm_index
        summary = summaries[arm]
        builder.process(pid, f"{bundle['experiment']} modeled arm: {arm}")
        builder.thread(pid, 1, "compute batches")
        builder.thread(pid, 2, "capacity and deadlines")
        if transfers_by_arm[arm]:
            builder.thread(pid, 3, "serial H2D link")
        for event in events_by_arm[arm]:
            if event["type"] == "slice":
                builder.slice(
                    pid,
                    1,
                    event["start_ms"] / 1000,
                    (event["finish_ms"] - event["start_ms"]) / 1000,
                    f"compute batch x{event['batch']}",
                    {
                        "tick": event["tick"],
                        "sessions": event["sessions"],
                        "due_ms": event["due_ms"],
                        "late": event["finish_ms"] > event["due_ms"] + manifest["config"]["period_ms"],
                    },
                )
                counts["compute_slices"] += 1
            elif event["type"] == "instant":
                builder.instant(
                    pid,
                    2,
                    event["time_ms"] / 1000,
                    event["name"],
                    {
                        key: value
                        for key, value in event.items()
                        if key not in {"type", "track", "time_ms", "name", "arm"}
                    },
                )
        if summary.get("output_deadline_misses"):
            builder.instant(
                pid,
                2,
                0,
                "arm has output deadline misses",
                {"count": summary["output_deadline_misses"], "rate": summary["output_deadline_miss_rate"]},
            )
        for transfer in transfers_by_arm[arm]:
            late = transfer["finish_ms"] > transfer["due_ms"]
            builder.slice(
                pid,
                3,
                transfer["start_ms"] / 1000,
                (transfer["finish_ms"] - transfer["start_ms"]) / 1000,
                "H2D transfer (late)" if late else "H2D transfer",
                {
                    "tick": transfer["tick"],
                    "session": transfer["session"],
                    "due_ms": transfer["due_ms"],
                    "service_ms": transfer["service_ms"],
                    "queue_ms": transfer["start_ms"] - transfer["release_ms"],
                    "late": late,
                },
            )
            counts["transfer_slices"] += 1
            if late:
                builder.instant(pid, 3, transfer["due_ms"] / 1000, "transfer deadline missed")


def add_e0(builder: TraceBuilder, bundle: dict[str, Any], counts: dict[str, int]) -> None:
    path = Path(bundle["run_dir"]) / "measurements.csv"
    if not path.is_file():
        return
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    builder.process(10, "E0 measurement matrix (not wall-clock execution)")
    for index, row in enumerate(rows):
        tid = int(row["B"])
        builder.thread(10, tid, f"batch B={row['B']}")
        builder.slice(
            10,
            tid,
            float(index),
            0.8,
            f"ctx={row['ctx']}, H2D={float(row['rate']):g}x",
            {
                "batch": int(row["B"]),
                "context_tokens": int(row["ctx"]),
                "target_rate": float(row["rate"]),
                "decode_p50_ms": float(row["decode_p50_ms"]),
                "decode_p99_ms": float(row["decode_p99_ms"]),
                "kappa": float(row["kappa"]),
                "effective_bandwidth_gbps": float(row["bw_eff_gbs"]),
                "iterations": int(row["iters"]),
            },
        )
        builder.counter(10, float(index), "decode p50", {"ms": float(row["decode_p50_ms"])})
        builder.counter(10, float(index), "H2D bandwidth", {"GB/s": float(row["bw_eff_gbs"])})
        counts["measurement_segments"] += 1


def add_generic(builder: TraceBuilder, bundle: dict[str, Any], counts: dict[str, int]) -> None:
    events = bundle.get("events") or []
    if not events:
        return
    builder.process(20, "experiment events")
    tracks = {track: index + 1 for index, track in enumerate(sorted({row["track"] for row in events}))}
    for track, tid in tracks.items():
        builder.thread(20, tid, track)
    for row in events:
        tid = tracks[row["track"]]
        args = row.get("args") or {}
        if row["type"] == "slice":
            builder.slice(20, tid, row["t_s"], row["duration_s"], row["name"], args)
        elif row["type"] == "instant":
            builder.instant(20, tid, row["t_s"], row["name"], args)
        else:
            builder.counter(20, row["t_s"], row["name"], {"value": row["value"], **args})
        counts["generic_events"] += 1


def source_hashes(run_dir: Path) -> dict[str, dict[str, Any]]:
    names = (
        "manifest.json",
        "status.json",
        "summary.json",
        "measurements.csv",
        "scheduler.log",
        "per_request.log",
        "kv.log",
        "gpu.csv",
        "gpu.log",
        "transfers.jsonl",
        "events.jsonl",
        "link_calibration.json",
    )
    return {
        name: {"bytes": (run_dir / name).stat().st_size, "sha256": sha256(run_dir / name)}
        for name in names
        if (run_dir / name).is_file()
    }


def _visualization_kind(experiment: str) -> str:
    if experiment == "e0_dma_interference":
        return "measurement_matrix"
    if experiment == "e1_capacity_bottleneck":
        return "end_to_end_engine_timeline"
    if experiment in {"e2_kv_conveyor", "e3_phase_scheduling"}:
        return "deterministic_mechanism_replay"
    return "generic_event_timeline"


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
    counts = {
        "engine_slices": 0,
        "compute_slices": 0,
        "transfer_slices": 0,
        "measurement_segments": 0,
        "generic_events": 0,
    }
    referenced_bundles: list[dict[str, Any]] = []
    if files.experiment in {"e2_kv_conveyor", "e3_phase_scheduling"}:
        baseline = mechanism_source_bundle(bundle)
        referenced_bundles.append(baseline)
        # E2/E3 extend the actual E1 view. Label the source explicitly so the
        # reference evidence cannot be mistaken for an E2/E3 engine run.
        add_e1(builder, baseline, counts, process_prefix="E1 source (real): ")
    else:
        add_e1(builder, bundle, counts)
    if files.experiment in {"e2_kv_conveyor", "e3_phase_scheduling"}:
        add_mechanism(builder, bundle, counts)
    add_e0(builder, bundle, counts)
    add_generic(builder, bundle, counts)
    if not any(counts.values()):
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
            "schema_version": 2,
            "artifact": TRACE_NAME,
            "run_id": files.run_id,
            "experiment": files.experiment,
            "visualization_kind": _visualization_kind(files.experiment),
            "claim_boundary": (bundle.get("manifest") or {}).get("claim_boundary"),
            "source_artifacts": source_hashes(files.directory),
            "referenced_runs": {
                referenced["run_id"]: {
                    "experiment": referenced["experiment"],
                    "path": repository_path(Path(referenced["run_dir"])),
                    "source_scheduler_sha256": referenced["source_scheduler_sha256"],
                    "artifacts": source_hashes(Path(referenced["run_dir"])),
                }
                for referenced in referenced_bundles
            },
            "events": len(builder.events),
            **counts,
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
    root = Path(__file__).resolve().parents[1] / "results"
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
