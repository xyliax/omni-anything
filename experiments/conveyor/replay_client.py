"""Replay an immutable input schedule against a fresh admission-enabled worker."""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import math
import time
import urllib.request
import wave
from pathlib import Path


async def serve_one(row, uri, start_ns, monotonic_start, records, period_ns):
    import websockets
    source_start = start_ns + round(row['arrival_s'] * 1e9)
    record = dict(row, source_start_ns=source_start, admitted=False, rejected=False,
                  completed=False, err=0, ticks=0, sends=[])
    records.append(record)
    sender = None
    try:
        # Decode/read material before arrival. No file I/O in the timed sender.
        with wave.open(row['audio_path'], 'rb') as stream:
            stream.setpos(row['offset_samples'])
            audio = stream.readframes(round(row['duration_s'] * 16000))
        await asyncio.sleep(max(0, monotonic_start + row['arrival_s'] - time.monotonic()))
        record['connect_ns'] = time.time_ns()
        async with websockets.connect(uri + f'?source_start_ns={source_start}',
                                      max_size=8 << 20, open_timeout=30, ping_timeout=60) as ws:
            async def send(kind, **fields):
                await ws.send(json.dumps(dict(type=kind, **fields)))
            await send('session.update', session=dict(input_sample_rate=16000, turn_detection=dict(type='full_duplex')))
            while True:
                event = json.loads(await ws.recv())
                kind = event.get('type')
                if kind == 'error':
                    raise RuntimeError(event['error'])
                if kind == 'session.created':
                    if not event.get('admission_required'):
                        raise ValueError('replay requires admission')
                    record['sid'] = event['session']['id']
                elif kind == 'session.rejected':
                    record.update(rejected=True, rejection_reason=event['reason'], rejected_ns=time.time_ns())
                    return
                elif kind == 'session.admitted':
                    record.update(admitted=True, admitted_ns=time.time_ns(), period_ns=period_ns)
                    for key in ('slot', 'epoch_ns', 'slots', 'first_release_ns', 'phase_policy'):
                        record[key] = event[key]
                    break

            async def send_audio():
                samples = len(audio) // 2
                # Use fixed 20ms transport chunks; input identity is one period.
                frame_samples = period_ns * 16000 // 10**9
                for end in range(320, samples + 320, 320):
                    end = min(end, samples)
                    begin = max(0, end - (320 if end % 320 == 0 else end % 320))
                    due_s = row['arrival_s'] + end / 16000
                    await asyncio.sleep(max(0, monotonic_start + due_s - time.monotonic()))
                    await send('input_audio_buffer.append', audio=base64.b64encode(audio[begin*2:end*2]).decode())
                    if end % frame_samples == 0 or end == samples:
                        record['sends'].append(dict(frame=math.ceil(end / frame_samples),
                            planned_ns=source_start + round(end / 16000 * 1e9), actual_ns=time.time_ns()))
                await send('session.end')
                record['audio_end_ns'] = time.time_ns()
            sender = asyncio.create_task(send_audio())
            while True:
                event = json.loads(await ws.recv())
                if event.get('type') == 'error':
                    raise RuntimeError(event['error'])
                if event.get('type') == 'metronome.tick':
                    record['ticks'] += 1
                if event.get('type') == 'session.completed':
                    await sender
                    record.update(completed=True, completed_ns=time.time_ns())
                    return
    except asyncio.CancelledError:
        record.update(unfinished=True, timeout=True)
        raise
    except Exception as exc:
        record.update(err=1, error=f'{type(exc).__name__}: {exc}')
    finally:
        if sender is not None and not sender.done():
            sender.cancel()
            await asyncio.gather(sender, return_exceptions=True)


async def run(rows, uri, timeout, *, epoch_ns, period_ns):
    # Same relative alignment to the serving grid in every fresh-worker run.
    now_ns, mono = time.time_ns(), time.monotonic()
    start_ns = epoch_ns + math.ceil((now_ns + 10**9 - epoch_ns) / period_ns) * period_ns
    start = mono + (start_ns - now_ns) / 1e9
    records = []
    try:
        await asyncio.wait_for(asyncio.gather(*(serve_one(row, uri, start_ns, start, records, period_ns)
                                              for row in rows)), timeout)
    except asyncio.TimeoutError:
        pass
    return dict(schema_version=1, kind='open_loop_replay', total=len(rows), start_ns=start_ns,
        admitted=sum(row['admitted'] for row in records), rejected=sum(row['rejected'] for row in records),
        completed=sum(row['completed'] for row in records), err=sum(row['err'] for row in records),
        unfinished=sum(not row['completed'] and not row['rejected'] for row in records),
        starved=False, sessions=records)


def main():
    # This file is also invoked by absolute path from the pinned client cwd.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.conveyor.schedule import read_schedule
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('manifest', 'uri', 'output'):
        parser.add_argument('--' + key, required=True)
    parser.add_argument('--timeout', required=True, type=float)
    args = parser.parse_args()
    data, rows = read_schedule(args.manifest)
    with urllib.request.urlopen(args.uri.replace('ws://', 'http://') + '/clock', timeout=10) as response:
        grid = json.load(response)
    if grid['period_ns'] != round(data['configuration']['period_s'] * 1e9):
        raise ValueError('input and gateway periods differ')
    result = asyncio.run(run(rows, args.uri, args.timeout, **grid))
    with Path(args.output).open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'sessions'}), flush=True)
    return int(bool(result['err']))


if __name__ == '__main__':
    raise SystemExit(main())
