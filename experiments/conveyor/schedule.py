"""Create the exogenous arrival schedule specified by the evaluation protocol.

This artifact deliberately contains no admission decisions or assigned phases.
It is not accepted by the legacy post-admission cohort player: a player must
preserve its source clock, rejection semantics and absolute input deadlines.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import wave
from pathlib import Path

from infra.run.artifacts import sha256_file


def audio_asset(path):
    path = Path(path).resolve()
    with wave.open(str(path), 'rb') as stream:
        if (stream.getnchannels(), stream.getsampwidth(), stream.getframerate(),
                stream.getcomptype()) != (1, 2, 16000, 'NONE'):
            raise ValueError(f'{path}: require uncompressed mono PCM16 WAV at 16 kHz')
        frames = stream.getnframes()
        # Verify data length rather than trusting a possibly truncated header.
        remaining = frames
        while remaining:
            block = stream.readframes(min(remaining, 65536))
            if not block or len(block) % 2:
                raise ValueError(f'{path}: truncated PCM data')
            remaining -= len(block) // 2
    if not frames:
        raise ValueError(f'{path}: empty audio')
    digest = sha256_file(path)
    return dict(input_stream_id=f'sha256:{digest}', sha256=digest,
                path=str(path), sample_rate=16000, samples=frames)


def generate_schedule(*, seed, arrival_rate, duration_s, arrival_window_s, period_s, assets):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    for name, value in (('arrival_rate', arrival_rate), ('duration_s', duration_s),
                        ('arrival_window_s', arrival_window_s), ('period_s', period_s)):
        if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
            raise ValueError(f'{name} must be finite and positive')
    if arrival_window_s < 2 * duration_s:
        raise ValueError('arrival window must span at least two session lifetimes')
    if duration_s < period_s:
        raise ValueError('session duration must cover a complete input period')
    if not assets:
        raise ValueError('at least one recorded audio asset is required')
    sources = sorted(assets, key=lambda asset: asset['input_stream_id'])
    if len({a['input_stream_id'] for a in sources}) != len(sources):
        raise ValueError('duplicate audio content in source manifest')
    samples = round(duration_s * 16000)
    if not math.isclose(samples / 16000, duration_s, rel_tol=0, abs_tol=1e-9):
        raise ValueError('session duration must represent a whole number of audio samples')
    if any(a['sample_rate'] != 16000 or a['samples'] < samples for a in sources):
        raise ValueError('each source must contain a complete session without looping')
    # The two RNG streams are independent. Source assignment cannot change
    # arrival times; changing the arrival rate preserves per-session inputs.
    arrivals = random.Random(seed)
    material_seed = int.from_bytes(hashlib.sha256(f'input:{seed}'.encode()).digest(), 'big')
    material = random.Random(material_seed)
    sessions = []
    start = 0.0
    while True:
        start += arrivals.expovariate(arrival_rate)
        if start >= arrival_window_s:
            break
        asset = sources[material.randrange(len(sources))]
        sessions.append(dict(session_id=f'session-{len(sessions)}', start_time_s=start,
            duration_s=duration_s, input_stream_id=asset['input_stream_id'],
            input_offset=material.randrange(asset['samples'] - samples + 1)))
    return dict(schema_version=1, kind='exogenous_session_schedule',
        configuration=dict(seed=seed, lambda_per_second=arrival_rate,
            session_duration_s=duration_s, arrival_window_s=arrival_window_s, period_s=period_s,
            input_offset_unit='samples', input_kind='recorded_audio',
            natural_first_tick='start_time_s + period_s'),
        assets=sources, sessions=sessions)


def read_schedule(path, *, verify_audio=True):
    """Validate before the run; never silently loop or replace input material."""
    data = json.loads(Path(path).read_text())
    if data.get('schema_version') != 1 or data.get('kind') != 'exogenous_session_schedule':
        raise ValueError('expected exogenous_session_schedule version 1')
    period = data['configuration']['period_s']
    if not math.isfinite(period) or period <= 0:
        raise ValueError('positive finite period required')
    assets = {asset['input_stream_id']: asset for asset in data['assets']}
    if len(assets) != len(data['assets']):
        raise ValueError('duplicate asset identity')
    for asset in assets.values():
        source = (Path(path).resolve().parent / asset['path']).resolve()
        if verify_audio:
            actual = audio_asset(source)
            if any(actual[key] != asset[key] for key in ('sha256', 'samples', 'sample_rate', 'input_stream_id')):
                raise ValueError('audio asset changed since schedule creation')
        asset['path'] = str(source)
    seen, rows = set(), []
    for row in data['sessions']:
        identity, arrival, duration = row['session_id'], row['start_time_s'], row['duration_s']
        if not isinstance(identity, str) or not identity or identity in seen:
            raise ValueError('unique nonempty session identities required')
        seen.add(identity)
        if not math.isfinite(arrival) or arrival < 0 or not math.isfinite(duration) or duration < period:
            raise ValueError('invalid source times')
        asset = assets[row['input_stream_id']]
        offset = row['input_offset']
        if type(offset) is not int or offset < 0 or offset + round(duration * 16000) > asset['samples']:
            raise ValueError('source segment exceeds recorded audio')
        rows.append(dict(id=identity, arrival_s=arrival, duration_s=duration,
                         audio_path=asset['path'], offset_samples=offset,
                         input_stream_id=row['input_stream_id']))
    if not rows:
        raise ValueError('evaluation needs at least one offered session')
    return data, rows


def generate_fixed_schedule(*, seed, sessions, duration_s, period_s, assets, measurement_start_s=0):
    """Common finite cohort; fractional phases are drawn before any execution."""
    if type(sessions) is not int or sessions < 1 or not 0 <= measurement_start_s < duration_s:
        raise ValueError('positive cohort and a valid shared measurement start required')
    # Reuse the dynamic generator's material validation and source ordering.
    template = generate_schedule(seed=seed, arrival_rate=1/duration_s, duration_s=duration_s,
        arrival_window_s=2*duration_s, period_s=period_s, assets=assets)
    sources = template['assets']
    phases = random.Random(seed)
    material = random.Random(int.from_bytes(hashlib.sha256(f'input:{seed}'.encode()).digest(), 'big'))
    samples = round(duration_s*16000)
    rows = []
    for index in range(sessions):
        asset = sources[material.randrange(len(sources))]
        rows.append(dict(session_id=f'session-{index}', start_time_s=phases.random()*period_s,
            duration_s=duration_s, input_stream_id=asset['input_stream_id'],
            input_offset=material.randrange(asset['samples']-samples+1)))
    return dict(schema_version=1, kind='exogenous_session_schedule', assets=sources,
        configuration=dict(seed=seed, arrival_process='fixed_cohort', period_s=period_s,
            session_duration_s=duration_s, measurement_start_s=measurement_start_s,
            input_kind='recorded_audio', input_offset_unit='samples', natural_first_tick='start_time_s + period_s'),
        sessions=sorted(rows, key=lambda row: row['start_time_s']))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', required=True, type=int)
    parser.add_argument('--arrival-rate', required=True, type=float)
    parser.add_argument('--session-duration', required=True, type=float)
    parser.add_argument('--arrival-window', required=True, type=float)
    parser.add_argument('--period', required=True, type=float)
    parser.add_argument('--audio', required=True, action='append', help='mono PCM16/16 kHz WAV; repeatable')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    schedule = generate_schedule(seed=args.seed, arrival_rate=args.arrival_rate,
        duration_s=args.session_duration, arrival_window_s=args.arrival_window,
        period_s=args.period, assets=[audio_asset(path) for path in args.audio])
    # Caller chooses the destination. Never replace an input schedule already
    # used by another system or trial.
    with args.output.open('x') as stream:
        json.dump(schedule, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(path=str(args.output), sha256=sha256_file(args.output),
                          offered_sessions=len(schedule['sessions']))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
