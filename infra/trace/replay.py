"""Source-clock evaluation of actual model work, including rejected/unfinished work."""
from __future__ import annotations

import json
import math
from pathlib import Path


def distribution(values):
    values = sorted(values)
    def quantile(q):
        if not values:
            return None
        index = (len(values) - 1) * q
        lo, hi = math.floor(index), math.ceil(index)
        return values[lo] + (values[hi] - values[lo]) * (index - lo)
    return dict(count=len(values), p50=quantile(.5), p95=quantile(.95), p99=quantile(.99),
                maximum=max(values) if values else None)


def evaluate(config, client, gateway, worker):
    invalid, frames = [], []
    schedule = config['admission']['cohort']
    expected = {row['session_id']: row for row in schedule['sessions']}
    rows = client['sessions']
    if (client.get('kind') != 'open_loop_replay' or client.get('total') != len(expected)
            or len(rows) != len(expected) or {row['id'] for row in rows} != set(expected)):
        raise ValueError('offered session identities do not match the frozen schedule')
    admitted = [s for s in rows if s.get('admitted')]
    rejected = [s for s in rows if s.get('rejected')]
    if any(s.get('admitted') and s.get('rejected') for s in rows):
        invalid.append('session is both admitted and rejected')
    if len({s['sid'] for s in admitted}) != len(admitted):
        invalid.append('duplicate backend session identity')
    events = {name: {} for name in ('input_ready', 'input_release', 'input_received', 'preprocessing_complete', 'engine_input', 'compute_complete')}
    for row in [*gateway, *worker]:
        if row['event'] not in events or row.get('frame', 0) == 0:
            continue
        key = (row['session'], row['epoch'], row['frame'])
        if key in events[row['event']]:
            invalid.append(f'duplicate {row["event"]} for {key}')
        events[row['event']][key] = row
    period = round(schedule['configuration']['period_s'] * 1e9)
    warmup = round(schedule['configuration'].get('measurement_start_s', 0) * 1e9)
    cutoff = client['start_ns'] + warmup
    keys, latencies, input_latencies, send_lag, contexts = set(), [], [], [], []
    execution_ms, history_wait_ms = [], []
    for session in admitted:
        offered = expected[session['id']]
        source = client['start_ns'] + round(offered['start_time_s'] * 1e9)
        if session['source_start_ns'] != source or session['period_ns'] != period:
            invalid.append('source clock changed during replay')
        first = source + period
        if session['phase_policy'] == 'assigned':
            phase = session['epoch_ns'] + session['slot'] * (period // session['slots'])
            first = phase + ((first - phase + period - 1) // period) * period
        if session['first_release_ns'] != first:
            invalid.append('first release shifted from the source clock')
        sends = {row['frame']: row for row in session['sends']}
        if len(sends) != len(session['sends']):
            invalid.append('duplicate client send identity')
        for seq in range(1, math.ceil(offered['duration_s'] * 1e9 / period) + 1):
            key = (session['sid'], 1, seq)
            keys.add(key)
            release = first + (seq - 1) * period
            source_ready = source + min(seq * period, round(offered['duration_s'] * 1e9))
            complete = events['compute_complete'].get(key)
            release_event = events['input_release'].get(key)
            if release_event and (release_event['release_ns'] != release or release_event['deadline_ns'] != release + period):
                invalid.append(f'deadline changed for {key}')
            if complete:
                if any(key not in events[name] for name in ('input_ready', 'input_release', 'input_received', 'engine_input')):
                    invalid.append(f'missing execution stage for {key}')
                if complete['tokens'] != config['workload']['output_token_cap'] or complete['finish_reason'] != 'length':
                    invalid.append(f'incomplete declared model work for {key}')
                if complete.get('context_tokens', 0) > config['engine']['max_model_len']:
                    invalid.append('backend exceeded maximum context')
            if source_ready < cutoff:
                continue
            done = complete['time_ns'] if complete else None
            frames.append(dict(session=session['id'], frame=seq, source_ready_ns=source_ready,
                release_ns=release, deadline_ns=release + period, complete_ns=done,
                outcome='unfinished' if done is None else 'on_time' if done <= release + period else 'late'))
            if done is not None:
                latencies.append((done - release) / 1e6)
                input_latencies.append((done - source_ready) / 1e6)
                if 'context_tokens' in complete:
                    contexts.append(complete['context_tokens'])
                ingest = events['engine_input'].get(key)
                preprocessed = events['preprocessing_complete'].get(key)
                if ingest:
                    execution_ms.append((done - ingest['time_ns']) / 1e6)
                if ingest and preprocessed:
                    history_wait_ms.append((ingest['time_ns'] - preprocessed['time_ns']) / 1e6)
            if seq in sends:
                if sends[seq]['planned_ns'] != source_ready:
                    invalid.append('client send source time mismatch')
                send_lag.append((sends[seq]['actual_ns'] - source_ready) / 1e6)
    for name, mapping in events.items():
        if set(mapping) - keys:
            invalid.append(f'{name} contains unoffered model work')
    if client.get('err'):
        invalid.append('client execution error')
    counts = {outcome: sum(frame['outcome'] == outcome for frame in frames)
              for outcome in ('on_time', 'late', 'unfinished')}
    end = max((f['complete_ns'] or f['deadline_ns'] for f in frames), default=cutoff)
    allocations = [row for row in worker if row['event'] == 'gpu_allocation' and cutoff <= row['time_ns'] <= end]
    previous = [row for row in worker if row['event'] == 'gpu_allocation' and row['time_ns'] < cutoff]
    if previous:
        allocations.append(max(previous, key=lambda row: row['time_ns']))
    geometry = [row for row in worker if row['event']=='gpu_allocation' and row.get('bytes_per_block')]
    block_bytes = geometry[0]['bytes_per_block'] if geometry else None
    backing = [row for row in worker if row['event']=='host_backing' and row['time_ns'] <= end]
    offered_frames = sum(max(0, math.ceil(row['duration_s'] * 1e9 / period) - max(0, math.ceil(
        (cutoff - (client['start_ns'] + round(row['start_time_s'] * 1e9)))/period) - 1))
                         for row in expected.values())
    return dict(schema_version=1, measurement='engine_observed_fixed_budget_completion',
        invalid_reasons=sorted(set(invalid)), offered_sessions=len(expected), admitted_sessions=len(admitted),
        rejected_sessions=len(rejected), undecided_sessions=len(rows) - len(admitted) - len(rejected),
        completed_sessions=sum(bool(row.get('completed')) for row in rows),
        offered_frames=offered_frames, admitted_frames=len(frames), **counts,
        on_time_offered_fraction=counts['on_time'] / offered_frames if offered_frames else None,
        on_time_admitted_fraction=counts['on_time'] / len(frames) if frames else None,
        completion_from_release_ms=distribution(latencies), completion_from_source_ready_ms=distribution(input_latencies),
        client_send_lateness_ms=distribution(send_lag), observed_context_tokens=distribution(contexts),
        engine_enqueue_to_completion_ms=distribution(execution_ms),
        preprocessing_to_engine_enqueue_ms=distribution(history_wait_ms),
        initial_alignment_ms=distribution([(s['first_release_ns']-s['source_start_ns']-period)/1e6 for s in admitted]),
        peak_allocated_gpu_blocks=max((row['allocated_blocks'] for row in allocations), default=None),
        gpu_pool_blocks=max((row['capacity_blocks'] for row in allocations), default=None),
        bytes_per_gpu_block=block_bytes,
        peak_valid_host_backing_blocks=max((row['valid_blocks'] for row in backing), default=0),
        frames=frames)


def evaluate_run(path, config=None):
    path = Path(path)
    try:
        config = config or json.loads((path / 'manifest.json').read_text())['config']
        def read(name):
            target = path / name
            return [json.loads(line) for line in target.read_text().splitlines() if line.strip()] if target.exists() else []
        return evaluate(config, json.loads((path / 'client.json').read_text()),
                        read('gateway_frames.jsonl'), read('service_events.jsonl'))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return dict(schema_version=1, invalid_reasons=[str(exc)])
