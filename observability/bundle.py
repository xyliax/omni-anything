"""Resolve and parse timed artifacts from any experiment run.

The shared bundle is the boundary between raw logs and visualization code.
Experiments may emit the established scheduler/request/KV/GPU logs, the
generic ``events.jsonl`` schema, or experiment-specific adapters supported
here such as E2's ``transfers.jsonl``.
"""

from __future__ import annotations

import bisect
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = ROOT / "results"
KV_PATTERN = re.compile(
    r"([\d.]+) kv=([\d.]+) run=(\d+) wait=(\d+) evict=\d+(?: pre=(\d+))?"
)
SESSION_PATTERN = re.compile(r"s(\d+)e")
WARMUP_SESSION = 10**9
PUSH_CLUSTER_GAP_S = 0.1


@dataclass(frozen=True)
class RunFiles:
    """Known timed artifacts resolved from one run directory."""

    experiment: str
    run_id: str
    directory: Path
    manifest: Path | None
    status: Path | None
    per_request: Path
    kv: Path
    scheduler: Path
    gpu: Path
    transfers: Path
    events: Path


def _run_files(directory: Path) -> RunFiles:
    gpu = directory / "gpu.csv"
    if not gpu.is_file():
        gpu = directory / "gpu.log"
    experiment = directory.parent.parent.name if directory.parent.name == "runs" else "external"
    return RunFiles(
        experiment=experiment,
        run_id=directory.name,
        directory=directory,
        manifest=(directory / "manifest.json") if (directory / "manifest.json").is_file() else None,
        status=(directory / "status.json") if (directory / "status.json").is_file() else None,
        per_request=directory / "per_request.log",
        kv=directory / "kv.log",
        scheduler=directory / "scheduler.log",
        gpu=gpu,
        transfers=directory / "transfers.jsonl",
        events=directory / "events.jsonl",
    )


def resolve_run(source: str | Path) -> RunFiles:
    """Resolve a directory, ``experiment/run-id``, or globally unique run ID."""
    direct = Path(source).expanduser()
    candidates: list[Path] = []
    if direct.is_dir():
        candidates.append(direct.resolve())
    else:
        repository_relative = ROOT / direct
        if repository_relative.is_dir():
            candidates.append(repository_relative.resolve())
        parts = direct.parts
        if len(parts) == 2:
            scoped = RESULTS_ROOT / parts[0] / "runs" / parts[1]
            if scoped.is_dir():
                candidates.append(scoped.resolve())
        candidates.extend(
            path.resolve()
            for path in RESULTS_ROOT.glob(f"*/runs/{str(source)}")
            if path.is_dir()
        )
    unique = sorted(set(candidates))
    if len(unique) == 1:
        return _run_files(unique[0])
    if len(unique) > 1:
        rendered = ", ".join(str(path) for path in unique)
        raise ValueError(f"run ID is ambiguous; use experiment/run-id: {rendered}")
    raise FileNotFoundError(f"run not found: {source}")


def read_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_per_request(path: Path) -> dict[str, Any]:
    warm_push = None
    push_times: list[float] = []
    tokens: dict[int, list[tuple[float, int]]] = {}
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) < 3:
                continue
            kind, raw_time, raw_session, *rest = parts
            timestamp, session = float(raw_time), int(raw_session)
            if session == WARMUP_SESSION:
                if kind == "P" and warm_push is None:
                    warm_push = timestamp
                continue
            if kind == "P":
                push_times.append(timestamp)
            elif kind == "T" and rest:
                tokens.setdefault(session, []).append((timestamp, int(rest[0])))
    first_push = push_times[0] if push_times else None
    result: dict[str, Any] = {"warm_push": warm_push, "first_push": first_push}
    if first_push is not None:
        # One synchronous gateway step writes one P row per session. Collapse
        # that short fan-out into one logical tick instead of displaying
        # several near-identical gateway markers.
        logical_ticks = [push_times[0]]
        for timestamp in push_times[1:]:
            if timestamp - logical_ticks[-1] > PUSH_CLUSTER_GAP_S:
                logical_ticks.append(timestamp)
        result["ticks"] = [
            round(timestamp - first_push, 3) for timestamp in logical_ticks
        ]
        result["starve"] = {
            session: round(last_token_growth(rows) - first_push, 1)
            for session, rows in tokens.items()
            if rows
        }
    return result


def last_token_growth(rows: list[tuple[float, int]]) -> float:
    last = rows[0][0]
    for previous, current in zip(rows, rows[1:]):
        if current[1] > previous[1]:
            last = current[0]
    return last


def parse_kv(
    path: Path, warm_push: float | None, first_push: float | None
) -> list[list[float | int]]:
    rows: list[list[float | int]] = []
    if not path.is_file():
        return rows
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = KV_PATTERN.match(line)
            if match:
                rows.append(
                    [
                        float(match.group(1)),
                        float(match.group(2)),
                        int(match.group(3)),
                        int(match.group(4)),
                        int(match.group(5) or 0),
                    ]
                )
    if rows and warm_push is not None and first_push is not None:
        offset = first_push - (warm_push - float(rows[0][0]))
        for row in rows:
            row[0] = round(float(row[0]) - offset, 2)
    return rows


def parse_scheduler_absolute(path: Path) -> list[tuple[float, list[list[int]]]]:
    """Return real-session scheduler rows as ``(unix_s, [sid, tokens, encoder])``."""
    rows: list[tuple[float, list[list[int]]]] = []
    if not path.is_file():
        return rows
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            parts = line.split()
            if not parts or parts[0].startswith("!"):
                continue
            try:
                timestamp = float(parts[0])
                entries: list[list[int]] = []
                for item in parts[1:]:
                    request_id, token_field = item.rsplit(":", 1)
                    encoder = int(token_field.endswith("E"))
                    token_count = int(token_field[:-1] if encoder else token_field)
                    match = SESSION_PATTERN.match(request_id)
                    if match and int(match.group(1)) != WARMUP_SESSION:
                        entries.append([int(match.group(1)), token_count, encoder])
            except (ValueError, IndexError) as exc:
                raise ValueError(f"invalid scheduler row {path}:{line_number}") from exc
            if entries:
                rows.append((timestamp, entries))
    return rows


def parse_scheduler(path: Path) -> list[list[Any]]:
    rows = parse_scheduler_absolute(path)
    if not rows:
        return []
    origin = rows[0][0]
    return [[round(timestamp - origin, 3), entries] for timestamp, entries in rows]


def parse_gpu(path: Path) -> list[list[float | int]]:
    values: list[int] = []
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                if "," in line:
                    values.append(int(float(line.split(",")[4].strip())))
                elif "%" in line:
                    values.append(int(line.split()[0]))
            except (ValueError, IndexError):
                continue
    return [[round(5 * index - 2.5, 1), value] for index, value in enumerate(values)]


def parse_transfers(path: Path) -> list[dict[str, Any]]:
    rows = parse_jsonl(path)
    required = {"arm", "tick", "session", "start_ms", "finish_ms", "due_ms"}
    for line_number, row in enumerate(rows, 1):
        missing = required - row.keys()
        if missing:
            raise ValueError(f"missing transfer fields {sorted(missing)} at {path}:{line_number}")
    return rows


def parse_events(path: Path) -> list[dict[str, Any]]:
    """Parse the public generic timeline schema used by future experiments."""
    rows = parse_jsonl(path)
    for line_number, row in enumerate(rows, 1):
        event_type = row.get("type")
        required = {"type", "track", "t_s", "name"}
        if event_type == "slice":
            required.add("duration_s")
        elif event_type == "counter":
            required.add("value")
        elif event_type != "instant":
            raise ValueError(f"unknown event type at {path}:{line_number}: {event_type!r}")
        missing = required - row.keys()
        if missing:
            raise ValueError(f"missing event fields {sorted(missing)} at {path}:{line_number}")
    return rows


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"JSONL row is not an object at {path}:{line_number}")
            rows.append(row)
    return rows


def percentile(values: Iterable[float], fraction: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    return ordered[round((len(ordered) - 1) * fraction)]


def align_perf_family(bundle: dict[str, Any]) -> None:
    ticks = bundle.get("ticks")
    steps = bundle.get("steps")
    if not ticks or not steps:
        return
    prefill_starts = [
        time for time, entries in steps if any(tokens >= 40 for _, tokens, _ in entries)
    ]
    deltas: list[float] = []
    for start in prefill_starts:
        index = bisect.bisect_right(ticks, start) - 1
        for candidate in range(max(0, index - 1), min(index + 2, len(ticks))):
            delta = start - ticks[candidate]
            if -1.0 < delta < 1.0:
                deltas.append(delta)
    if not deltas:
        return
    minimum = min(deltas)
    shift = round(minimum - 0.003, 3)
    bundle["clock_alignment"] = {
        "method": "min_prefill_after_tick",
        "shift_s": shift,
        "anchors": len(deltas),
        "anchor_spread_p95_ms": round(
            (percentile((abs(value - minimum) for value in deltas), 0.95) or 0) * 1000,
            3,
        ),
    }
    bundle["ticks"] = [round(time + shift, 3) for time in ticks]
    if "kv" in bundle:
        bundle["kv"] = [
            [round(float(row[0]) + shift, 2), *row[1:]] for row in bundle["kv"]
        ]
    if "starve" in bundle:
        bundle["starve"] = {
            session: round(time + shift, 1) for session, time in bundle["starve"].items()
        }


def add_periodic_ticks(bundle: dict[str, Any]) -> None:
    if bundle.get("ticks") or not bundle.get("steps"):
        return
    manifest = bundle.get("manifest") or {}
    period_ms = (manifest.get("config") or {}).get("period_ms")
    if not period_ms:
        return
    period_s = float(period_ms) / 1000.0
    end = float(bundle["steps"][-1][0]) + period_s
    bundle["ticks"] = [
        round(index * period_s, 3) for index in range(int(end / period_s) + 1)
    ]
    bundle["tick_source"] = "periodic_from_manifest"


def build_bundle(source: str | Path) -> dict[str, Any]:
    files = resolve_run(source)
    bundle: dict[str, Any] = {
        "experiment": files.experiment,
        "run_id": files.run_id,
        "run_dir": str(files.directory),
        "manifest": read_json(files.manifest),
        "status": read_json(files.status),
        "artifact_paths": {
            name: str(path)
            for name, path in {
                "scheduler": files.scheduler,
                "transfers": files.transfers,
                "events": files.events,
            }.items()
            if path.is_file()
        },
    }
    per_request = parse_per_request(files.per_request)
    for key in ("ticks", "starve"):
        if key in per_request:
            bundle[key] = per_request[key]
    kv = parse_kv(files.kv, per_request.get("warm_push"), per_request.get("first_push"))
    if kv:
        bundle["kv"] = kv
    steps = parse_scheduler(files.scheduler)
    if steps:
        bundle["steps"] = steps
        add_periodic_ticks(bundle)
    gpu = parse_gpu(files.gpu)
    if gpu:
        bundle["smi"] = gpu
    transfers = parse_transfers(files.transfers)
    if transfers:
        bundle["transfers"] = transfers
    events = parse_events(files.events)
    if events:
        bundle["events"] = events

    align_perf_family(bundle)
    if "kv" in bundle:
        bundle["evictions"] = [
            bundle["kv"][index][0]
            for index in range(1, len(bundle["kv"]))
            if bundle["kv"][index][4] > bundle["kv"][index - 1][4]
        ]
    endpoints = [
        rows[-1][0] for key in ("kv", "steps", "smi") if (rows := bundle.get(key))
    ]
    endpoints.extend(float(row["finish_ms"]) / 1000 for row in transfers)
    endpoints.extend(float(row["t_s"]) for row in events)
    bundle["t_end"] = round(max(endpoints, default=0) + 5, 1)
    return bundle
