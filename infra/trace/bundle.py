"""Resolve one run directory and assemble its parsed, clock-aligned bundle.

The bundle is the boundary between raw logs and any downstream consumer
(Perfetto export, ad-hoc analysis). Which keys appear depends only on which
artifacts the run directory contains.
"""

from __future__ import annotations

import bisect
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .parse import (
    is_prefill,
    parse_gateway_ticks,
    parse_gpu,
    parse_kv,
    parse_park,
    parse_per_request,
    parse_residency,
    parse_scheduler,
    percentile,
)


ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = ROOT / "results"


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
    residency: Path
    gpu: Path
    gateway_ticks: Path
    park: Path


def _run_files(directory: Path) -> RunFiles:
    experiment = directory.parent.name if directory.parent.parent == RESULTS_ROOT else "external"
    return RunFiles(
        experiment=experiment,
        run_id=directory.name,
        directory=directory,
        manifest=(directory / "manifest.json") if (directory / "manifest.json").is_file() else None,
        status=(directory / "status.json") if (directory / "status.json").is_file() else None,
        per_request=directory / "per_request.log",
        kv=directory / "kv.log",
        scheduler=directory / "scheduler.log",
        residency=directory / "residency.log",
        gpu=directory / "gpu.csv",
        gateway_ticks=directory / "gateway_ticks.log",
        park=directory / "park.log",
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
            scoped = RESULTS_ROOT / parts[0] / parts[1]
            if scoped.is_dir():
                candidates.append(scoped.resolve())
        candidates.extend(
            path.resolve()
            for path in RESULTS_ROOT.glob(f"*/{str(source)}")
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


def _config_value(manifest: dict[str, Any] | None, *keys: str) -> Any:
    """Look one key up in manifest config, tolerating flat and sectioned layouts."""
    config = (manifest or {}).get("config") or {}
    for key in keys:
        if key in config:
            return config[key]
        for section in config.values():
            if isinstance(section, dict) and key in section:
                return section[key]
    return None


def align_exact(bundle: dict[str, Any], per_request: dict[str, Any], steps_origin: float) -> bool:
    """Shift the perf-clock family onto the scheduler's epoch clock exactly,
    using the worker's clock-fix line ("C <perf_s> <epoch_s>"). Returns False
    when the run predates the clock fix (legacy runs fall back to the
    heuristic anchoring)."""
    offset = per_request.get("clock_offset")
    first_push = per_request.get("first_push")
    if offset is None or first_push is None:
        return False
    shift = round(first_push + offset - steps_origin, 3)
    bundle["clock_alignment"] = {"method": "worker_clock_fix", "shift_s": shift}
    _shift_perf_family(bundle, shift)
    return True


def _shift_perf_family(bundle: dict[str, Any], shift: float) -> None:
    bundle["ticks"] = [round(time + shift, 3) for time in bundle.get("ticks") or []]
    bundle["pushes"] = {
        session: [round(time + shift, 3) for time in times]
        for session, times in (bundle.get("pushes") or {}).items()
    }
    if "kv" in bundle:
        bundle["kv"] = [
            [round(float(row[0]) + shift, 2), *row[1:]] for row in bundle["kv"]
        ]
    if "starve" in bundle:
        bundle["starve"] = {
            session: round(time + shift, 1) for session, time in bundle["starve"].items()
        }
    if "ingest" in bundle:
        bundle["ingest"] = {
            session: [
                {key: round(value + shift, 3) for key, value in record.items()}
                for record in records
            ]
            for session, records in bundle["ingest"].items()
        }


def align_perf_family(bundle: dict[str, Any]) -> None:
    """LEGACY heuristic for runs without a clock-fix line: shift the perf
    family so the smallest prefill-after-push delay lands at +3 ms.

    Known bias: the true minimum delay is the ingest floor (~240 ms on this
    stack), which this method folds into the clock shift — displayed
    push-to-prefill gaps are relative to the fastest observed, not absolute.
    Anchors pair each session's prefills with that session's own pushes."""
    pushes = bundle.get("pushes")
    steps = bundle.get("steps")
    if not pushes or not steps:
        return
    deltas: list[float] = []
    for start, entries in steps:
        for session, tokens, encoder in entries:
            if not is_prefill(tokens, encoder):
                continue
            own = pushes.get(session)
            if not own:
                continue
            index = bisect.bisect_right(own, start) - 1
            for candidate in range(max(0, index - 1), min(index + 2, len(own))):
                delta = start - own[candidate]
                if -1.0 < delta < 1.0:
                    deltas.append(delta)
    if not deltas:
        return
    minimum = min(deltas)
    shift = round(minimum - 0.003, 3)
    bundle["clock_alignment"] = {
        "method": "min_prefill_after_push",
        "shift_s": shift,
        "anchors": len(deltas),
        "anchor_spread_p95_ms": round(
            (percentile((abs(value - minimum) for value in deltas), 0.95) or 0) * 1000,
            3,
        ),
    }
    _shift_perf_family(bundle, shift)


def add_periodic_ticks(bundle: dict[str, Any]) -> None:
    if bundle.get("ticks") or not bundle.get("steps"):
        return
    period_ms = _config_value(bundle.get("manifest"), "period_ms")
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
    manifest = read_json(files.manifest)
    bundle: dict[str, Any] = {
        "experiment": files.experiment,
        "run_id": files.run_id,
        "run_dir": str(files.directory),
        "manifest": manifest,
        "status": read_json(files.status),
    }
    per_request = parse_per_request(files.per_request)
    for key in ("ticks", "pushes", "starve", "ingest"):
        if key in per_request:
            bundle[key] = per_request[key]
    kv = parse_kv(files.kv, per_request.get("warm_push"), per_request.get("first_push"))
    if kv:
        bundle["kv"] = kv
    steps_origin, steps = parse_scheduler(files.scheduler)
    if steps:
        bundle["steps"] = steps
        add_periodic_ticks(bundle)
    residency = parse_residency(files.residency)
    if residency:
        # residency.log is epoch-clock (same EngineCore collector as
        # scheduler.log): exact alignment, same base rule as gpu/gateway.
        base = steps_origin if steps_origin is not None else residency[0][0]
        bundle["residency"] = [
            [round(timestamp - base, 3), entries] for timestamp, entries in residency
        ]
    gpu = parse_gpu(files.gpu)
    if gpu:
        # nvidia-smi stamps share the scheduler's epoch clock: exact alignment.
        base = steps_origin if steps_origin is not None else gpu[0][0]
        bundle["smi"] = [[round(stamp - base, 2), util] for stamp, util in gpu]
    firings = parse_gateway_ticks(files.gateway_ticks)
    if firings:
        # gateway stamps are epoch-clock too: exact alignment, same base rule.
        base = steps_origin if steps_origin is not None else firings[0]["time"]
        bundle["gateway_firings"] = [
            {**row, "time": round(row["time"] - base, 3)} for row in firings
        ]
    park = parse_park(files.park)
    if park["parks"] or park["reloads"] or park["offloads"]:
        # park.log is epoch-clock (engine patch): exact alignment. Without a
        # scheduler.log the fallback base is per-family (park events anchor to
        # their own first event, gpu to its own) — flag it so ad-hoc consumers
        # don't cross-read misaligned series.
        first = (park["parks"] or park["offloads"] or park["reloads"])[0]["time"]
        base = steps_origin if steps_origin is not None else first
        if steps_origin is None:
            bundle["alignment_warning"] = "per-family zero points (no scheduler.log)"
        bundle["parks"] = [
            {**row, "time": round(row["time"] - base, 3)} for row in park["parks"]
        ]
        bundle["offloads"] = [
            {**row, "time": round(row["time"] - base, 3)} for row in park["offloads"]
        ]
        bundle["reloads"] = [
            {
                **row,
                "time": round(row["time"] - base, 3),
                "end": None if row["end"] is None else round(row["end"] - base, 3),
            }
            for row in park["reloads"]
        ]

    if steps_origin is None or not align_exact(bundle, per_request, steps_origin):
        align_perf_family(bundle)
    if "kv" in bundle:
        # row[4] is the pre= field (cumulative PREEMPTIONS; KV_PATTERN does
        # not capture evict=). Naming this "evictions" once mislabeled the
        # timeline — the two are deliberately distinct concepts here.
        bundle["preemptions"] = [
            bundle["kv"][index][0]
            for index in range(1, len(bundle["kv"]))
            if bundle["kv"][index][4] > bundle["kv"][index - 1][4]
        ]
    endpoints = [
        rows[-1][0] for key in ("kv", "steps", "smi", "residency") if (rows := bundle.get(key))
    ]
    bundle["t_end"] = round(max(endpoints, default=0) + 5, 1)
    return bundle
