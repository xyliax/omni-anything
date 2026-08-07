"""Trace-driven capacity and transfer model shared by E2 and E3.

The compute service times come from an E1 scheduler trace produced by the
real Qwen2.5-Omni/vLLM stack. Transfer service times come from fresh pinned
H2D measurements. This module combines those measured inputs; it contains no
CUDA code and is therefore deterministic and unit-testable.
"""

from __future__ import annotations

import math
import random
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from observability.bundle import parse_scheduler_absolute



def percentile(values: Iterable[float], fraction: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    return ordered[round((len(ordered) - 1) * fraction)]


@dataclass(frozen=True)
class ComputeProfile:
    """Measured duration of one full tick burst for each batch size."""

    source: str
    busy_ms_by_batch: dict[int, float]
    decode_step_ms_by_batch: dict[int, float]
    steps_per_tick: int

    def busy_ms(self, batch: int) -> float:
        if batch in self.busy_ms_by_batch:
            return self.busy_ms_by_batch[batch]
        known = sorted(self.busy_ms_by_batch)
        if not known:
            raise ValueError("compute profile is empty")
        nearest = min(known, key=lambda value: abs(value - batch))
        return self.busy_ms_by_batch[nearest]

    def as_manifest(self) -> dict:
        result = asdict(self)
        result["busy_ms_by_batch"] = {
            str(key): value for key, value in self.busy_ms_by_batch.items()
        }
        result["decode_step_ms_by_batch"] = {
            str(key): value for key, value in self.decode_step_ms_by_batch.items()
        }
        return result


def load_compute_profile(path: Path) -> ComputeProfile:
    """Derive batch service times from one non-empty E1 scheduler trace."""
    rows = [
        (timestamp, [(session, tokens) for session, tokens, _ in entries])
        for timestamp, entries in parse_scheduler_absolute(path)
    ]
    if len(rows) < 2:
        raise ValueError(f"scheduler trace has no usable steps: {path}")

    decode_steps: dict[int, list[float]] = defaultdict(list)
    for (timestamp, entries), (next_timestamp, _) in zip(rows, rows[1:]):
        duration_ms = (next_timestamp - timestamp) * 1000
        if 0 < duration_ms < 500 and all(tokens < 40 for _, tokens in entries):
            decode_steps[len(entries)].append(duration_ms)

    segments: list[list[tuple[float, list[tuple[int, int]]]]] = []
    current: list[tuple[float, list[tuple[int, int]]]] = []
    for row in rows:
        if current and row[0] - current[-1][0] > 0.5:
            segments.append(current)
            current = []
        current.append(row)
    if current:
        segments.append(current)

    bursts: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for segment in segments:
        counts = Counter(
            len(entries)
            for _, entries in segment
            if all(tokens < 40 for _, tokens in entries)
        )
        if not counts:
            continue
        batch = counts.most_common(1)[0][0]
        duration_ms = (segment[-1][0] - segment[0][0]) * 1000
        bursts[batch].append((len(segment), duration_ms))

    step_medians = {
        batch: statistics.median(samples)
        for batch, samples in decode_steps.items()
        if samples
    }
    observed_steps = [count for samples in bursts.values() for count, _ in samples]
    steps_per_tick = round(statistics.median(observed_steps)) if observed_steps else 34
    busy_ms = {
        batch: statistics.median(duration for _, duration in samples)
        for batch, samples in bursts.items()
        if samples
    }
    for batch, duration in step_medians.items():
        busy_ms.setdefault(batch, duration * steps_per_tick)
    if not busy_ms:
        raise ValueError(f"scheduler trace has no usable bursts: {path}")
    return ComputeProfile(str(path), busy_ms, step_medians, steps_per_tick)


def phase_offsets(
    policy: str,
    sessions: int,
    period_ms: float,
    seed: int,
    *,
    compute: ComputeProfile | None = None,
    tdma_group_size: int = 7,
    tdma_guard_ms: float = 30.0,
) -> list[float]:
    if policy == "synchronized":
        return [0.0] * sessions
    if policy == "tdma":
        if compute is None:
            raise ValueError("TDMA phase assignment requires a compute profile")
        if not 1 <= tdma_group_size <= sessions:
            raise ValueError("tdma_group_size must be between one and sessions")
        phases: list[float] = []
        due = 0.0
        for start in range(0, sessions, tdma_group_size):
            group_size = min(tdma_group_size, sessions - start)
            phases.extend([due] * group_size)
            due += compute.busy_ms(group_size) + tdma_guard_ms
        return phases
    if policy == "random":
        rng = random.Random(seed)
        return [rng.random() * period_ms for _ in range(sessions)]
    raise ValueError(f"unknown phase policy: {policy}")


@dataclass(frozen=True)
class SimulationConfig:
    sessions: int = 8
    ticks: int = 300
    period_ms: float = 2000.0
    growth_tokens_per_tick: int = 78
    initial_context_tokens: int = 0
    tail_tokens: int = 4096
    pool_tokens: int = 73728
    lead_ms: float = 20.0
    tdma_group_size: int = 7
    tdma_guard_ms: float = 30.0

    def __post_init__(self) -> None:
        positive = {
            "sessions": self.sessions,
            "ticks": self.ticks,
            "period_ms": self.period_ms,
            "growth_tokens_per_tick": self.growth_tokens_per_tick,
            "tail_tokens": self.tail_tokens,
            "pool_tokens": self.pool_tokens,
        }
        for name, value in positive.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.initial_context_tokens < 0:
            raise ValueError("initial_context_tokens must be non-negative")
        if self.lead_ms < 0 or self.tdma_guard_ms < 0:
            raise ValueError("lead_ms and tdma_guard_ms must be non-negative")
        if not 1 <= self.tdma_group_size <= self.sessions:
            raise ValueError("tdma_group_size must be between one and sessions")


@dataclass(frozen=True)
class TransferResult:
    tick: int
    session: int
    planned_release_ms: float
    content_available_ms: float
    release_ms: float
    due_ms: float
    start_ms: float
    finish_ms: float
    service_ms: float

    @property
    def queue_ms(self) -> float:
        return self.start_ms - self.release_ms

    @property
    def late(self) -> bool:
        return self.finish_ms > self.due_ms


def _peak_staging_tokens(
    intervals: Sequence[tuple[int, float, float]], tail_tokens: int
) -> int:
    # A session owns at most one staging tail. When compute falls behind, the
    # next tick extends that residency interval instead of allocating a second
    # copy for the same session.
    by_session: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for session, start, finish in intervals:
        by_session[session].append((start, finish))
    merged: list[tuple[float, float]] = []
    for rows in by_session.values():
        session_intervals: list[tuple[float, float]] = []
        for start, finish in sorted(rows):
            if session_intervals and start <= session_intervals[-1][1]:
                previous_start, previous_finish = session_intervals[-1]
                session_intervals[-1] = (previous_start, max(previous_finish, finish))
            else:
                session_intervals.append((start, finish))
        merged.extend(session_intervals)

    events: list[tuple[float, int]] = []
    for start, finish in merged:
        events.append((start, tail_tokens))
        events.append((finish, -tail_tokens))
    current = peak = 0
    for _, delta in sorted(events, key=lambda event: (event[0], event[1])):
        current += delta
        peak = max(peak, current)
    return peak


def _capacity_wall_ms(
    config: SimulationConfig, conveyor: bool, staging_peak_tokens: int
) -> float | None:
    for tick in range(config.ticks):
        context = config.initial_context_tokens + (tick + 1) * config.growth_tokens_per_tick
        if conveyor:
            resident = config.sessions * max(0, context - config.tail_tokens)
            used = resident + staging_peak_tokens
        else:
            used = config.sessions * context
        if used > config.pool_tokens:
            return tick * config.period_ms
    return None


def _phase_plan_summary(
    phases: Sequence[float], compute: ComputeProfile, period_ms: float
) -> dict:
    groups = Counter(phases)
    demand_ms = sum(compute.busy_ms(size) for size in groups.values())
    last_finish_ms = max(
        phase + compute.busy_ms(size) for phase, size in groups.items()
    )
    return {
        "nominal_groups": [
            {"phase_ms": phase, "sessions": size, "busy_ms": compute.busy_ms(size)}
            for phase, size in sorted(groups.items())
        ],
        "nominal_compute_demand_ms": demand_ms,
        "nominal_compute_utilization": demand_ms / period_ms,
        "nominal_last_finish_ms": last_finish_ms,
        "nominal_slot_aligned": last_finish_ms <= period_ms,
        "nominal_schedulable": demand_ms <= period_ms,
    }


def _schedule_compute_tick(
    jobs: Sequence[tuple[int, float, float]],
    compute: ComputeProfile,
    gpu_free: float,
) -> tuple[float, dict[int, float], list[tuple[int, float, float, float, list[int]]]]:
    """Batch every job ready when the GPU chooses its next engine step burst."""
    pending = sorted(jobs, key=lambda job: (job[2], job[1], job[0]))
    completion: dict[int, float] = {}
    batches: list[tuple[int, float, float, float, list[int]]] = []
    while pending:
        start = max(gpu_free, pending[0][2])
        ready = [job for job in pending if job[2] <= start + 1e-9]
        ready_ids = {job[0] for job in ready}
        pending = [job for job in pending if job[0] not in ready_ids]
        finish = start + compute.busy_ms(len(ready))
        for session, _, _ in ready:
            completion[session] = finish
        batches.append(
            (len(ready), start, finish, min(job[1] for job in ready), sorted(ready_ids))
        )
        gpu_free = finish
    return gpu_free, completion, batches


def simulate(
    config: SimulationConfig,
    compute: ComputeProfile,
    transfer_samples_ms: Sequence[float],
    *,
    conveyor: bool,
    phase_policy: str,
    seed: int,
    timeline: list[dict] | None = None,
) -> tuple[dict, list[TransferResult]]:
    """Simulate the measured link and GPU, optionally collecting compute events.

    ``timeline`` is an observability sink. Supplying it does not alter the
    model or returned summaries; it exposes the exact compute batches chosen
    by the simulator so old runs can be visualized by deterministic replay.
    """
    if conveyor and not transfer_samples_ms:
        raise ValueError("conveyor simulation requires transfer samples")
    phases = phase_offsets(
        phase_policy,
        config.sessions,
        config.period_ms,
        seed,
        compute=compute,
        tdma_group_size=config.tdma_group_size,
        tdma_guard_ms=config.tdma_guard_ms,
    )
    plan = _phase_plan_summary(phases, compute, config.period_ms)
    transfer_results: list[TransferResult] = []
    # The first prefetch is legitimately released before the first t=0 due
    # point. Starting the virtual link at zero would create a synthetic miss.
    link_free = -math.inf

    gpu_free = 0.0
    previous_completion: dict[int, float] = {}
    staging_intervals: list[tuple[int, float, float]] = []
    compute_latencies: list[float] = []
    compute_batches: Counter[int] = Counter()
    compute_busy_ms = 0.0
    output_misses = 0
    sample_index = 0
    expected_service = statistics.median(transfer_samples_ms) if conveyor else 0.0
    for tick in range(config.ticks):
        tick_groups: dict[float, list[int]] = defaultdict(list)
        for session, phase in enumerate(phases):
            tick_groups[round(tick * config.period_ms + phase, 6)].append(session)

        transfer_completion: dict[int, float] = {}
        if conveyor:
            for compute_due, sessions in sorted(tick_groups.items()):
                services = [
                    float(transfer_samples_ms[(sample_index + offset) % len(transfer_samples_ms)])
                    for offset in range(len(sessions))
                ]
                sample_index += len(sessions)
                planned_release = (
                    compute_due - config.lead_ms - expected_service * len(sessions)
                )
                cursor = link_free
                for session, service in zip(sessions, services):
                    # Tick zero starts with a host-resident tail. Every later
                    # transfer waits for the preceding tick to freeze content.
                    content_available = previous_completion.get(session, planned_release)
                    release = max(planned_release, content_available)
                    start = max(release, cursor)
                    finish = start + service
                    result = TransferResult(
                        tick=tick,
                        session=session,
                        planned_release_ms=planned_release,
                        content_available_ms=content_available,
                        release_ms=release,
                        due_ms=compute_due,
                        start_ms=start,
                        finish_ms=finish,
                        service_ms=service,
                    )
                    transfer_results.append(result)
                    transfer_completion[session] = finish
                    cursor = finish
                link_free = cursor

        jobs = []
        due_by_session: dict[int, float] = {}
        for due, sessions in tick_groups.items():
            for session in sessions:
                ready = max(due, transfer_completion.get(session, due))
                jobs.append((session, due, ready))
                due_by_session[session] = due
        gpu_free, tick_completion, batches = _schedule_compute_tick(
            jobs, compute, gpu_free
        )
        previous_completion = tick_completion
        for batch_size, start, finish, due, sessions in batches:
            compute_batches[batch_size] += 1
            compute_busy_ms += finish - start
            if timeline is not None:
                timeline.append(
                    {
                        "type": "slice",
                        "track": "compute",
                        "tick": tick,
                        "start_ms": start,
                        "finish_ms": finish,
                        "due_ms": due,
                        "batch": batch_size,
                        "sessions": sessions,
                    }
                )
        for session, finish in tick_completion.items():
            due = due_by_session[session]
            compute_latencies.append(finish - due)
            if finish > due + config.period_ms:
                output_misses += 1
            if conveyor:
                staging_intervals.append(
                    (session, transfer_completion[session], finish)
                )

    staging_peak = (
        _peak_staging_tokens(staging_intervals, config.tail_tokens) if conveyor else 0
    )
    queues = [result.queue_ms for result in transfer_results]
    services = [result.service_ms for result in transfer_results]
    horizon_ms = config.ticks * config.period_ms
    capacity_wall = _capacity_wall_ms(config, conveyor, staging_peak)
    if timeline is not None and capacity_wall is not None:
        timeline.append(
            {
                "type": "instant",
                "track": "capacity",
                "time_ms": capacity_wall,
                "name": "capacity wall",
                "used_model": "resident KV plus peak staging",
            }
        )
    transfer_misses = sum(result.late for result in transfer_results)
    compute_busy_fraction = compute_busy_ms / horizon_ms if horizon_ms else 0.0
    end_overrun_ms = max(0.0, gpu_free - horizon_ms)
    mechanism_valid = (
        transfer_misses == 0
        and output_misses == 0
        and compute_busy_fraction <= 1.0 + 1e-9
    )
    summary = {
        "conveyor": conveyor,
        "phase_policy": phase_policy,
        "seed": seed,
        "lead_ms": config.lead_ms,
        "sessions": config.sessions,
        "ticks": config.ticks,
        "phase_plan": plan,
        "transfer_jobs": len(transfer_results),
        "transfer_service_p50_ms": percentile(services, 0.50),
        "transfer_service_p99_ms": percentile(services, 0.99),
        "transfer_queue_p99_ms": percentile(queues, 0.99),
        "transfer_deadline_misses": transfer_misses,
        "transfer_deadline_miss_rate": (
            transfer_misses / len(transfer_results)
            if transfer_results else 0.0
        ),
        "link_busy_fraction": sum(services) / horizon_ms if horizon_ms else 0.0,
        "content_release_delays": sum(
            result.release_ms > result.planned_release_ms + 1e-9
            for result in transfer_results
        ),
        "compute_batches": {str(size): count for size, count in sorted(compute_batches.items())},
        "compute_busy_fraction": compute_busy_fraction,
        "compute_end_overrun_ms": end_overrun_ms,
        "compute_latency_p50_ms": percentile(compute_latencies, 0.50),
        "compute_latency_p99_ms": percentile(compute_latencies, 0.99),
        "output_deadline_misses": output_misses,
        "output_deadline_miss_rate": output_misses / (config.sessions * config.ticks),
        "staging_peak_tokens": staging_peak,
        "staging_peak_sessions": staging_peak / config.tail_tokens if config.tail_tokens else 0,
        "mechanism_valid": mechanism_valid,
        "capacity_wall_ms": capacity_wall,
        "validated_capacity_wall_ms": capacity_wall if mechanism_valid else None,
    }
    return summary, transfer_results


def capacity_extension(baseline: dict, conveyor: dict) -> float | None:
    baseline_wall = baseline.get("validated_capacity_wall_ms")
    conveyor_wall = conveyor.get("validated_capacity_wall_ms")
    if baseline_wall in (None, 0) or conveyor_wall is None:
        return None
    return conveyor_wall / baseline_wall
