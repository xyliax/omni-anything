from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from experiments.conveyor.cohort_client import read_manifest, pcm_source, run


class CohortTests(unittest.TestCase):
    def test_manifest_and_reproducible_distinct_inputs(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'cohort.json'
            row = {'id': 'a', 'arrival_s': 0, 'duration_s': 1, 'seed': 17}
            path.write_text(json.dumps([row]))
            self.assertEqual(read_manifest(path), [row])
            self.assertEqual(pcm_source(row)(640), pcm_source(row)(640))
            self.assertNotEqual(pcm_source(row)(640), pcm_source({**row, 'seed': 18})(640))
            path.write_text(json.dumps([row, row]))
            with self.assertRaises(ValueError):
                read_manifest(path)


class CohortProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_waits_for_admission_and_requires_completion(self):
        try:
            from websockets.asyncio.server import serve
        except ImportError:
            self.skipTest('websockets client dependency not installed')
        received = []
        async def handler(ws):
            await ws.send(json.dumps({'type': 'session.created', 'session': {'id': 1}, 'admission_required': True}))
            received.append(json.loads(await ws.recv())['type'])
            with self.assertRaises(asyncio.TimeoutError):
                await asyncio.wait_for(ws.recv(), .02)
            await ws.send(json.dumps({'type': 'session.admitted', 'slot': 2}))
            while True:
                event = json.loads(await ws.recv())
                received.append(event['type'])
                if event['type'] == 'session.end':
                    await ws.send(json.dumps({'type': 'metronome.tick'}))
                    await ws.send(json.dumps({'type': 'session.completed'}))
                    return
        async with serve(handler, '127.0.0.1', 0) as server:
            port = server.sockets[0].getsockname()[1]
            result = await run([{'id': 'a', 'arrival_s': 0, 'duration_s': .1, 'seed': 1}],
                               f'ws://127.0.0.1:{port}', 2)
        self.assertEqual(result['completed'], 1)
        self.assertEqual(result['err'], 0)
        self.assertEqual(received[0], 'session.update')
        self.assertEqual(received[-1], 'session.end')

    async def test_no_completed_event_is_not_success(self):
        try:
            from websockets.asyncio.server import serve
        except ImportError:
            self.skipTest('websockets client dependency not installed')
        async def handler(ws):
            await ws.send(json.dumps({'type': 'session.created', 'session': {'id': 1}, 'admission_required': True}))
            await ws.send(json.dumps({'type': 'session.admitted', 'slot': 0}))
            async for message in ws:
                if json.loads(message)['type'] == 'session.end':
                    return  # disconnect is not completion
        async with serve(handler, '127.0.0.1', 0) as server:
            port = server.sockets[0].getsockname()[1]
            result = await run([{'id': 'a', 'arrival_s': 0, 'duration_s': .1, 'seed': 1}],
                               f'ws://127.0.0.1:{port}', 2)
        self.assertEqual(result['completed'], 0)
        self.assertEqual(result['err'], 1)
