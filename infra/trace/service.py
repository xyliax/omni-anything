"""Stable concurrency from input identities and observed model completion.

All offered frames remain in the denominator, including never released or
never completed work. No RPC latency or sampling of resident KV is used as a
substitute for model progress. This first protocol measures periodic compute
completion; it does not claim native speech playback quality.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServiceSLO:
    horizon_s: float
    warmup_s: float
    max_miss_ratio: float
    window_s: float
    max_lag_periods: float
    max_consecutive_late: int

    def __post_init__(self):
        for name in ('horizon_s', 'warmup_s', 'window_s', 'max_lag_periods'):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f'{name} must be finite and positive')
        if not 0 <= self.max_miss_ratio < 1 or self.window_s > self.horizon_s:
            raise ValueError('invalid miss ratio or window')
        if type(self.max_consecutive_late) is not int or self.max_consecutive_late < 1:
            raise ValueError('positive consecutive-lag count required')

    @classmethod
    def read(cls, path):
        return cls(**json.loads(Path(path).read_text()))


def read_events(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    if not rows:
        raise ValueError(f'empty event log: {Path(path).name}')
    return rows


def evaluate_run(path, config=None):
    path = Path(path)
    try:
        config = config or json.loads((path / 'manifest.json').read_text())['config']
        slo = ServiceSLO(**config['service_slo'])
        client = json.loads((path / 'client.json').read_text())
        if any('audio_start_ns' not in s for s in client['sessions']):
            return evaluate(slo, client, [], [], config['workload']['output_token_cap'])
        gateway = read_events(path / 'gateway_frames.jsonl')
        worker = read_events(path / 'service_events.jsonl')
        return evaluate(slo, client, gateway, worker, config['workload']['output_token_cap'])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return dict(schema_version=1, verdict='invalid', reasons=[str(exc)])


def evaluate(slo, client, gateway, worker, output_cap):
    sessions = client['sessions']
    reasons, invalid = [], []
    if len(sessions) != client['total'] or len({s.get('sid') for s in sessions}) != len(sessions):
        raise ValueError('offered session identity mismatch')
    if client.get('err') or any(not s.get('completed') for s in sessions):
        reasons.append('offered sessions failed, timed out, or did not drain')
    if any('audio_start_ns' not in s for s in sessions):
        return dict(schema_version=1, verdict='fail', reasons=reasons + ['all-session admission barrier not reached'])
    start = max(s['audio_start_ns'] for s in sessions) + round(slo.warmup_s * 1e9)
    end = start + round(slo.horizon_s * 1e9)
    if any(s.get('audio_end_ns', 0) < end for s in sessions):
        reasons.append('target concurrency did not span the full observation horizon')

    maps = {event: {} for event in ('input_ready', 'input_release', 'input_received', 'engine_input', 'compute_complete')}
    for row in [*gateway, *worker]:
        if row['event'] not in maps or row['frame'] == 0:
            continue
        key = (row['session'], row['epoch'], row['frame'])
        target = maps[row['event']]
        if key in target:
            raise ValueError(f'duplicate {row["event"]} for {key}')
        target[key] = row
    offered = set(maps['input_ready'])
    for event in ('input_release', 'input_received', 'engine_input', 'compute_complete'):
        if set(maps[event]) - offered:
            invalid.append(f'{event} contains an unoffered input identity')
    per_session, samples = [], []
    for session in sessions:
        sid = session['sid']
        period = session['period_ns']
        if period <= 0 or slo.warmup_s * 1e9 < 2 * period:
            raise ValueError('warmup must cover at least two input periods')
        phase = session['epoch_ns'] + session['slot'] * (period // session['slots'])
        selected = []
        all_ready = sorted((key, row) for key, row in maps['input_ready'].items() if key[0] == sid)
        expected_frames = math.ceil(session['duration_s'] * 1e9 / period)
        if [key[2] for key, _ in all_ready] != list(range(1, expected_frames + 1)):
            reasons.append(f'session {sid}: missing offered audio frames')
        for sequence in range(1, expected_frames + 1):
            key = (sid, 1, sequence)
            ready = maps['input_ready'].get(key)
            # Offered availability is frozen by source sample time. Delayed
            # network reception or a missing frame cannot shift its deadline
            # or remove it from the observation horizon.
            when = session['audio_start_ns'] + min(sequence * period, round(session['duration_s'] * 1e9))
            if not start <= when < end:
                continue
            # Earliest eligible absolute slot, independent of a late loop or
            # missing RPC. Never move deadlines to actual submission time.
            release = phase + ((when - phase + period - 1) // period) * period
            deadline = release + period
            done = maps['compute_complete'].get(key)
            completion = done['time_ns'] if done else None
            missed = completion is None or completion > deadline
            lag = math.inf if completion is None else (completion - deadline) / period
            for event in ('input_release', 'input_received', 'engine_input'):
                if done and key not in maps[event]:
                    invalid.append(f'{event} missing for completed input {key}')
            if done and (done['tokens'] != output_cap or done['finish_reason'] != 'length'):
                reasons.append(f'session {sid}: model stopped without the declared per-frame work')
            selected.append(dict(frame=key[2], ready_ns=when, deadline_ns=deadline,
                                 received_ready_ns=ready.get('ready_ns', ready['time_ns']) if ready else None,
                                 completion_ns=completion, missed=missed, lag_periods=lag if math.isfinite(lag) else None))
        if len(selected) < max(1, math.floor(slo.horizon_s * 1e9 / period) - 1):
            invalid.append(f'session {sid}: insufficient offered inputs during the horizon')
        count = len(selected)
        misses = sum(s['missed'] for s in selected)
        if count and misses / count > slo.max_miss_ratio:
            reasons.append(f'session {sid}: overall deadline miss ratio exceeded')
        # Windows begin at each offered frame; only full observation windows
        # are tested. Session-wide ratio still includes both boundary tails.
        window_ns = round(slo.window_s * 1e9)
        for frame in selected:
            left = frame['ready_ns']
            if left + window_ns > end:
                break
            window = [s for s in selected if left <= s['ready_ns'] < left + window_ns]
            if window and sum(s['missed'] for s in window) / len(window) > slo.max_miss_ratio:
                reasons.append(f'session {sid}: window deadline miss ratio exceeded')
                break
        streak = maximum = 0
        for frame in selected:
            lag = frame['lag_periods']
            streak = streak + 1 if lag is None or lag > slo.max_lag_periods else 0
            maximum = max(maximum, streak)
        if maximum >= slo.max_consecutive_late:
            reasons.append(f'session {sid}: persistent model lag')
        per_session.append(dict(session=sid, frames=count, misses=misses,
                                miss_ratio=misses / count if count else None,
                                maximum_lag_streak=maximum))
        samples.extend(dict(session=sid, **row) for row in selected)
    total, misses = len(samples), sum(row['missed'] for row in samples)
    if total and misses / total > slo.max_miss_ratio:
        reasons.append('aggregate deadline miss ratio exceeded')
    # Failed/missing completion samples remain explicit misses. Quantiles
    # below describe completed samples only and report that denominator.
    period_by_sid = {s['sid']: s['period_ns'] for s in sessions}
    latency = sorted((r['completion_ns'] - r['deadline_ns'] + period_by_sid[r['session']]) / 1e6
                     for r in samples if r['completion_ns'] is not None)
    latency_summary = {'completed_samples': len(latency)}
    for name, q in (('p50_ms', .5), ('p95_ms', .95), ('p99_ms', .99)):
        latency_summary[name] = latency[max(0, math.ceil(q * len(latency)) - 1)] if latency else None
    return dict(schema_version=1, verdict='invalid' if invalid else ('fail' if reasons else 'pass'),
                reasons=invalid + reasons, target_concurrency=len(sessions),
                observation_start_ns=start, observation_end_ns=end, horizon_s=slo.horizon_s,
                frames=total, misses=misses, miss_ratio=misses / total if total else None,
                per_session=per_session, frames_detail=samples,
                completion_latency=latency_summary,
                first_missed_deadline_ns=min((r['deadline_ns'] for r in samples if r['missed']), default=None),
                metric='engine-observed compute completion by next planned release')
