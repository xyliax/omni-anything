"""Exercise the real WebSocket client with delayed admission and rejection."""
import asyncio
import json
import time
import wave

import pytest

from experiments.conveyor.replay_client import serve_one


def test_delayed_admission_keeps_source_clock_and_rejection_sends_no_audio(tmp_path):
    websockets = pytest.importorskip('websockets')
    audio = tmp_path / 'source.wav'
    with wave.open(str(audio), 'wb') as stream:
        stream.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
        stream.writeframes(b'\1\0' * 3200)

    async def exercise(reject):
        messages, records = [], []
        start_ns, start = time.time_ns(), time.monotonic()
        async def handler(ws):
            await ws.send(json.dumps(dict(type='session.created', session=dict(id=1), admission_required=True)))
            messages.append(json.loads(await ws.recv()))
            await asyncio.sleep(.13)  # later than every source frame's availability
            if reject:
                await ws.send(json.dumps(dict(type='session.rejected', reason='session_limit')))
                return
            await ws.send(json.dumps(dict(type='session.admitted', slot=0, epoch_ns=start_ns,
                slots=1, first_release_ns=start_ns+40_000_000, phase_policy='natural')))
            while True:
                event = json.loads(await ws.recv())
                messages.append(event)
                if event['type'] == 'session.end':
                    await ws.send(json.dumps(dict(type='session.completed')))
                    return
        async with websockets.serve(handler, '127.0.0.1', 0) as server:
            port = server.sockets[0].getsockname()[1]
            row = dict(id='a', arrival_s=0, duration_s=.12, audio_path=str(audio), offset_samples=0)
            await asyncio.wait_for(serve_one(row, f'ws://127.0.0.1:{port}', start_ns, start, records, 40_000_000), 3)
        record = records[0]
        assert record['err'] == 0
        if reject:
            assert record['rejected'] and not record['admitted']
            assert [m['type'] for m in messages] == ['session.update']
        else:
            assert record['completed'] and len(record['sends']) == 3
            assert [r['planned_ns'] - start_ns for r in record['sends']] == [40_000_000, 80_000_000, 120_000_000]
            assert all(r['actual_ns'] > r['planned_ns'] for r in record['sends'])
            assert sum(len(m.get('audio', '')) for m in messages) > 0
    asyncio.run(exercise(False))
    asyncio.run(exercise(True))
