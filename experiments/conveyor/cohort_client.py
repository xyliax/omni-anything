"""Finite, open-loop arrivals; real-time audio starts only after admission.

This controls offered work, not model answers. Synthetic PCM is explicitly
labelled; it is a systems stress input, not a conversational-quality dataset.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import math
import random
import struct
import time
import wave
from pathlib import Path


def read_manifest(path):
    rows = json.loads(Path(path).read_text())
    if not isinstance(rows, list) or not rows:
        raise ValueError('cohort manifest must be a nonempty list')
    ids = set()
    for row in rows:
        if not isinstance(row.get('id'), str) or not row['id'] or row['id'] in ids:
            raise ValueError('cohort ids must be unique nonempty strings')
        ids.add(row['id'])
        if not math.isfinite(row['arrival_s']) or row['arrival_s'] < 0:
            raise ValueError('arrival_s must be finite and nonnegative')
        if not math.isfinite(row['duration_s']) or row['duration_s'] < .1:
            raise ValueError('duration_s must be at least 100 ms')
        if type(row['seed']) is not int:
            raise ValueError('seed must be an integer')
        if 'audio_path' in row:
            row['audio_path'] = str((Path(path).resolve().parent / row['audio_path']).resolve())
    return rows


def pcm_source(row):
    if row.get('audio_path'):
        with wave.open(row['audio_path'], 'rb') as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 16000):
                raise ValueError('audio must be mono PCM16 WAV at 16 kHz')
            pcm = wav.readframes(wav.getnframes())
        if not pcm:
            raise ValueError('empty audio source')
        offset = (row.get('offset_samples', row['seed'] * 7919) * 2) % len(pcm)
        def chunk(samples):
            nonlocal offset
            count = samples * 2
            output = (pcm * (math.ceil((offset + count) / len(pcm))))[offset:offset + count]
            offset = (offset + count) % len(pcm)
            return output
        return chunk
    rng = random.Random(row['seed'])
    return lambda samples: struct.pack('<' + 'h' * samples, *(rng.randint(-2000, 2000) for _ in range(samples)))


async def serve_one(row, uri, start, records, barrier=None):
    import websockets
    record = {'id': row['id'], 'arrival_s': row['arrival_s'], 'duration_s': row['duration_s'],
              'input_kind': 'recorded_audio' if row.get('audio_path') else 'synthetic_pcm',
              'completed': False, 'err': 0, 'ticks': 0}
    records.append(record)
    sender_task = None
    try:
        await asyncio.sleep(max(0, start + row['arrival_s'] - time.monotonic()))
        record['connect_s'] = time.monotonic() - start
        async with websockets.connect(uri, max_size=8 << 20, open_timeout=30, ping_timeout=60) as ws:
            async def send(kind, **fields):
                await ws.send(json.dumps({'type': kind, **fields}))
            await send('session.update', session={'input_sample_rate': 16000,
                       'turn_detection': {'type': 'full_duplex'}})
            admitted = False
            while not admitted:
                event = json.loads(await ws.recv())
                if event.get('type') == 'error':
                    raise RuntimeError(event['error'])
                if event.get('type') == 'session.created':
                    if not event.get('admission_required'):
                        raise RuntimeError('cohort client requires admission-enabled gateway')
                    record['sid'] = event['session']['id']
                if event.get('type') == 'session.admitted':
                    admitted = True
                    record['slot'] = event['slot']
                    record['admitted_s'] = time.monotonic() - start
                    record['admission_wait_s'] = record['admitted_s'] - record['arrival_s']
                    for name in ('epoch_ns', 'period_ns', 'slots'):
                        if name in event:
                            record[name] = event[name]
            source = pcm_source(row)
            if barrier is not None:
                await barrier.wait()
            async def sender():
                sent = 0
                total = round(row['duration_s'] * 16000)
                audio_start = time.monotonic()
                record['audio_start_ns'] = time.time_ns()
                while sent < total:
                    count = min(320, total - sent)
                    # A chunk becomes available after its samples have played,
                    # not one chunk early. Source time stays independent of
                    # gateway/worker delay and defines the offered schedule.
                    await asyncio.sleep(max(0, audio_start + (sent + count) / 16000 - time.monotonic()))
                    await send('input_audio_buffer.append', audio=base64.b64encode(source(count)).decode())
                    sent += count
                await send('session.end')
                record['audio_end_ns'] = time.time_ns()
            sender_task = asyncio.create_task(sender())
            while True:
                event = json.loads(await ws.recv())
                if event.get('type') == 'error':
                    raise RuntimeError(event['error'])
                if event.get('type') == 'metronome.tick':
                    record['ticks'] += 1
                if event.get('type') == 'session.completed':
                    await sender_task
                    record.update(completed=True, completed_s=time.monotonic() - start)
                    return
    except asyncio.CancelledError:
        record.update(err=1, error='cohort timeout', failed_s=time.monotonic() - start)
        raise
    except Exception as exc:
        record.update(err=1, error=f'{type(exc).__name__}: {exc}', failed_s=time.monotonic() - start)
    finally:
        if sender_task is not None and not sender_task.done():
            sender_task.cancel()
            await asyncio.gather(sender_task, return_exceptions=True)


async def run(rows, uri, timeout, barrier=0):
    if barrier and (barrier != len(rows) or any(row['arrival_s'] != 0 for row in rows)):
        raise ValueError('capacity barrier requires all offered sessions to arrive together')
    start = time.monotonic()
    records = []
    try:
        gate = asyncio.Barrier(barrier) if barrier else None
        await asyncio.wait_for(asyncio.gather(*(serve_one(row, uri, start, records, gate) for row in rows)), timeout)
    except asyncio.TimeoutError:
        pass
    completed = sum(row['completed'] for row in records)
    return {'schema_version': 1, 'kind': 'finite_cohort', 'total': len(rows),
            'completed': completed, 'err': len(rows) - completed,
            'makespan_s': time.monotonic() - start, 'sessions': records,
            'starved': not any(row['ticks'] for row in records)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--uri', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--timeout', type=float, required=True)
    parser.add_argument('--barrier', type=int, default=0)
    args = parser.parse_args()
    result = asyncio.run(run(read_manifest(args.manifest), args.uri, args.timeout, args.barrier))
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'sessions'}), flush=True)
    return int(bool(result['err']))


if __name__ == '__main__':
    raise SystemExit(main())
