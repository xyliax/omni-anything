"""Parsers for the raw log formats experiments emit.

These preserve hard-won format knowledge:

- ``KV_PATTERN``'s ``pre=`` group is optional so pre-``pre`` logs still parse
  (and ``evict=`` is deliberately NOT captured: row[4] is preemptions)
- scheduler rows starting with ``!`` are markers and skipped
- the warmup session sentinel (10**9) is excluded from every parse but its
  push time is retained: it is the bridge between the StatLogger clock and
  the worker-process clock
- the worker writes one ``C <perf_s> <epoch_s>`` clock-pairing line, making
  the perf-clock family exactly alignable (legacy runs fall back to a biased
  heuristic — see bundle.align_perf_family)
- GPU sample timestamps are centered in their own sampling interval, so the
  parser must be told the sampler period (see the platform profile)
- gateway_ticks.log and park.log are epoch-clock (no pairing needed);
  park.log carries four line kinds (park / S mirror / L reload-admit /
  R reload-done), see parse_park
- residency.log is epoch-clock too (written by the same EngineCore collector
  as scheduler.log): one row per sample, ``<epoch> <request_id>:<blocks> ...``
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


KV_PATTERN = re.compile(
    r"([\d.]+) kv=([\d.]+) run=(\d+) wait=(\d+) evict=\d+(?: pre=(\d+))?"
)
SESSION_PATTERN = re.compile(r"s(\d+)e")
WARMUP_SESSION = 10**9
PUSH_CLUSTER_GAP_S = 0.1


def is_prefill(tokens: int, encoder: int) -> bool:
    """Decode schedules exactly one token per step per request (autoregressive);
    any step scheduling more — or carrying encoder work — is a prefill. A fixed
    token threshold would misclassify short first slices under a staggered
    gateway (an 0.8s opening chunk prefills only ~37 tokens)."""
    return tokens > 1 or bool(encoder)


def percentile(values: Iterable[float], fraction: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    return ordered[round((len(ordered) - 1) * fraction)]


def parse_per_request(path: Path) -> dict[str, Any]:
    warm_push = None
    clock_offset = None
    push_times: list[float] = []
    pushes: dict[int, list[float]] = {}
    tokens: dict[int, list[tuple[float, int]]] = {}
    # ingest pipeline stations per session, in emission order (per-session
    # chunk order is preserved by the worker): IQ dispatch-to-executor,
    # IS FE starts (thread), IE FE done, IR back on the loop, IA admitted.
    stations: dict[int, dict[str, list[float]]] = {}
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) < 3:
                continue
            kind, raw_time, raw_session, *rest = parts
            timestamp = float(raw_time)
            if kind == "C":
                # clock fix: "C <perf_s> <epoch_s>", written once at worker start;
                # maps this log's perf clock onto scheduler.log's epoch clock exactly.
                clock_offset = float(raw_session) - timestamp
                continue
            session = int(raw_session)
            if session == WARMUP_SESSION:
                if kind == "P" and warm_push is None:
                    warm_push = timestamp
                continue
            if kind == "P":
                push_times.append(timestamp)
                pushes.setdefault(session, []).append(timestamp)
            elif kind == "T" and rest:
                tokens.setdefault(session, []).append((timestamp, int(rest[0])))
            elif kind in ("IQ", "IS", "IE", "IR", "IA"):
                stations.setdefault(session, {}).setdefault(kind, []).append(timestamp)
    first_push = push_times[0] if push_times else None
    result: dict[str, Any] = {
        "warm_push": warm_push,
        "first_push": first_push,
        "clock_offset": clock_offset,
    }
    if first_push is not None:
        # Each session ticks on its own grid (one P row per push); a staggered
        # gateway spreads sessions' grids across the period, so alignment and
        # display must key on per-session pushes, not one shared tick train.
        result["pushes"] = {
            session: [round(timestamp - first_push, 3) for timestamp in times]
            for session, times in pushes.items()
        }
        # Gateway firing instants: pushes within one firing land within
        # milliseconds; collapse that fan-out into one logical marker.
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
        # ingest records: zip the five stations per session in order (the
        # worker preserves per-session chunk order, so index i across the
        # five lists is chunk i). Sessions with mismatched counts (e.g. run
        # cut mid-chunk) zip to the shortest.
        result["ingest"] = {
            session: [
                {
                    key.lower(): round(value - first_push, 3)
                    for key, value in zip(("IQ", "IS", "IE", "IR", "IA"), row)
                }
                for row in zip(*(kinds.get(k, []) for k in ("IQ", "IS", "IE", "IR", "IA")))
            ]
            for session, kinds in stations.items()
        }
    return result


def parse_gateway_ticks(path: Path) -> list[dict[str, Any]]:
    """Per-firing rows from the conveyor gateway's GW_TICKLOG.

    Line: ``<wake_epoch> slot=N late_ms=F sample_ms=F grpc_ms=F gpu_ms=F n=K
    [deliv=<sid>:<tok>,...]``. Timestamps are epoch-clock (same family as
    scheduler.log), so alignment is exact — no clock pairing. ``deliv`` counts
    are measured at the delivery point (the take-from-stock deadline fact).
    """
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            parts = line.split()
            if not parts:
                continue
            try:
                row: dict[str, Any] = {"time": float(parts[0])}
                for item in parts[1:]:
                    key, value = item.split("=", 1)
                    if key == "deliv":
                        row[key] = {
                            int(sid): int(tok)
                            for sid, tok in (pair.split(":") for pair in value.split(","))
                        }
                    elif key in ("slot", "n"):
                        row[key] = int(value)
                    else:
                        row[key] = float(value)
            except (ValueError, IndexError) as exc:
                raise ValueError(f"invalid gateway tick row {path}:{line_number}") from exc
            rows.append(row)
    return rows


def parse_park(path: Path) -> dict[str, list[dict[str, Any]]]:
    """Park and reload events from the conveyor engine patch's park.log.

    Four line kinds, all epoch-clock (exact alignment, no pairing needed):

    - park:   ``<epoch> req=<id> held=N evicted=N cpu_covered=N usage_before=F
      usage_after=F`` — one per successful park.
    - load:   ``<epoch> L req=<id> cpu_tok=N gpu_tok=N [trigger=demand|prefetch]``
      — a CPU-supplied load was issued: demand = resume reload (request enters
      WAITING_FOR_REMOTE_KVS), prefetch = anonymous materialization at
      chunk-push time. Missing ``trigger`` (pre-prefetch logs) reads as
      demand.
    - loaded: ``<epoch> R req=<id> [trigger=...]`` — that load completed.
    - store:  ``<epoch> S req=<id> blocks=N`` — the eager mirror's frontier
      advanced N blocks for this session (offload activity; upper bound on
      copies, dedup-skips included).

    Returns ``{"parks": [...], "reloads": [...], "offloads": [...]}``; reloads
    carry a ``trigger`` field and are L/R pairs matched per (request, trigger)
    in order (an unmatched L keeps ``end=None``). The session id is parsed
    out of the request id (``s<sid>e1-...``).
    """
    parks: list[dict[str, Any]] = []
    reloads: list[dict[str, Any]] = []
    offloads: list[dict[str, Any]] = []
    open_loads: dict[tuple[str, str], list[dict[str, Any]]] = {}
    if not path.is_file():
        return {"parks": [], "reloads": [], "offloads": []}
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                timestamp = float(parts[0])
                kind = parts[1]
                if kind in ("L", "R", "S"):
                    fields = dict(item.split("=", 1) for item in parts[2:])
                else:
                    kind = "park"
                    fields = dict(item.split("=", 1) for item in parts[1:])
                match = SESSION_PATTERN.match(fields["req"])
                if not match or int(match.group(1)) == WARMUP_SESSION:
                    continue
                session = int(match.group(1))
                if kind == "park":
                    parks.append(
                        {
                            "time": timestamp,
                            "session": session,
                            "held": int(fields["held"]),
                            "evicted": int(fields["evicted"]),
                            "cpu_covered": int(fields["cpu_covered"]),
                            "usage_before": float(fields["usage_before"]),
                            "usage_after": float(fields["usage_after"]),
                        }
                    )
                elif kind == "S":
                    offloads.append(
                        {
                            "time": timestamp,
                            "session": session,
                            "blocks": int(fields["blocks"]),
                        }
                    )
                elif kind == "L":
                    trigger = fields.get("trigger", "demand")
                    event = {
                        "time": timestamp,
                        "session": session,
                        "cpu_tok": int(fields["cpu_tok"]),
                        "gpu_tok": int(fields["gpu_tok"]),
                        "trigger": trigger,
                        "end": None,
                    }
                    reloads.append(event)
                    open_loads.setdefault((fields["req"], trigger), []).append(event)
                else:  # R
                    trigger = fields.get("trigger", "demand")
                    pending = open_loads.get((fields["req"], trigger))
                    if pending:
                        pending.pop(0)["end"] = timestamp
            except (KeyError, ValueError, IndexError) as exc:
                raise ValueError(f"invalid park row {path}:{line_number}") from exc
    return {"parks": parks, "reloads": reloads, "offloads": offloads}


def parse_residency(path: Path) -> list[list[Any]]:
    """Per-session KV residency samples from the EngineCore collector.

    Line: ``<epoch_s> <request_id>:<blocks> ...`` — one row per sample
    (throttled at the source by ``OMNI_STATLOG_PERIOD_S``), one field per
    live request. ``blocks`` is the request's grip or, when parked, its
    still-GPU-cached prefix chain. Returns ``[[epoch_s, [[sid, blocks],
    ...]], ...]`` with the warmup sentinel excluded — epoch clock, so
    alignment against scheduler.log is exact.
    """
    rows: list[list[Any]] = []
    if not path.is_file():
        return rows
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            parts = line.split()
            if not parts:
                continue
            try:
                timestamp = float(parts[0])
                entries: list[list[int]] = []
                for item in parts[1:]:
                    request_id, blocks = item.rsplit(":", 1)
                    match = SESSION_PATTERN.match(request_id)
                    if match and int(match.group(1)) != WARMUP_SESSION:
                        entries.append([int(match.group(1)), int(blocks)])
            except (ValueError, IndexError) as exc:
                raise ValueError(f"invalid residency row {path}:{line_number}") from exc
            if entries:
                rows.append([timestamp, entries])
    return rows


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
        # kv.log counts seconds since the StatLogger's clock origin while
        # per_request.log counts seconds since worker start; the warmup push
        # appears in both and bridges them.
        offset = first_push - (warm_push - float(rows[0][0]))
        for row in rows:
            row[0] = round(float(row[0]) - offset, 2)
    return rows


def parse_scheduler(path: Path) -> tuple[float | None, list[list[Any]]]:
    """Real-session scheduler rows as ``(epoch_origin, [[t_rel_s, entries], ...])``.

    The origin (first row's epoch time) is the shared clock every other
    wall-clock series aligns to.
    """
    rows: list[tuple[float, list[list[int]]]] = []
    if not path.is_file():
        return None, []
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
    if not rows:
        return None, []
    origin = rows[0][0]
    return origin, [[round(timestamp - origin, 3), entries] for timestamp, entries in rows]


def parse_gpu(path: Path) -> list[list[float]]:
    """Parse nvidia-smi loop output into ``[epoch_s, util_pct]`` rows.

    Uses the sampler's own wall-clock timestamps (first CSV field), which
    share an epoch clock with scheduler.log — no synthetic time base.
    """
    rows: list[list[float]] = []
    if not path.is_file():
        return rows
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            fields = line.split(", ")
            if len(fields) < 5:
                continue
            try:
                stamp = datetime.strptime(fields[0].strip(), "%Y/%m/%d %H:%M:%S.%f")
                rows.append([stamp.timestamp(), int(float(fields[4]))])
            except ValueError:
                continue
    return rows
