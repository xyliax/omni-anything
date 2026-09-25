from __future__ import annotations

import asyncio
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

ROOT = Path(__file__).resolve().parents[1]


def worker_module():
    # Import the real worker without constructing its optional vLLM engine.
    for dependency in ('grpc', 'numpy', 'google.protobuf'):
        try:
            if importlib.util.find_spec(dependency) is None:
                raise unittest.SkipTest('worker CPU dependencies not installed')
        except ModuleNotFoundError:
            raise unittest.SkipTest('worker CPU dependencies not installed')
    spec = importlib.util.spec_from_file_location('admission_worker_under_test', ROOT / 'engines/conveyor/worker/stream_server.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkerLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.worker = worker_module()
        self.eng = self.worker.StreamingEngine.__new__(self.worker.StreamingEngine)
        self.eng.managed = True
        self.eng.engine = SimpleNamespace(abort=AsyncMock(), engine_core=SimpleNamespace(call_utility_async=AsyncMock()))
        self.eng.sessions = {}
        self.eng.closed_sessions = set()
        self.eng.close_futures = {}
        self.eng.output_token_cap = 25
        self.eng.initial_context_tokens = 0

    async def test_close_waits_for_backend_copy_drain_and_cancels_queued_input(self):
        st = self.worker.Session()
        st.closing = True
        finished = asyncio.Event()
        async def generation():
            try:
                await asyncio.Event().wait()
            finally:
                finished.set()
        st.runner_task = asyncio.create_task(generation())
        await asyncio.sleep(0)
        self.eng.engine.engine_core.call_utility_async.side_effect = [
            {'released': False}, {'released': False}, {'released': True}]
        await self.eng._close_session(3, st)
        self.assertTrue(finished.is_set())
        self.assertTrue(st.done)
        self.eng.engine.abort.assert_awaited_once_with('s3e1')
        self.assertEqual(self.eng.engine.engine_core.call_utility_async.await_count, 3)
        self.assertTrue(st.queue.empty())  # close must not enqueue a model flush

    async def test_drain_waits_for_final_frontend_output_then_capped_delivery(self):
        st = self.worker.Session()
        st.frame, st.tokens = 2, list(range(25))
        self.eng.sessions[1] = st
        self.eng.engine.engine_core.call_utility_async.return_value = {'drained': True}
        task = asyncio.create_task(self.eng._drain_input(1, st))
        await asyncio.sleep(.025)
        self.assertFalse(st.drained, 'EngineCore completion alone is not frontend output completion')
        st.tokens = list(range(50))
        await asyncio.wait_for(task, 1)
        self.assertFalse(self.eng.finished(1))
        self.assertEqual(len(self.eng.collect_output([1], 25)[1][0]), 25)
        self.assertFalse(self.eng.finished(1))
        self.assertEqual(len(self.eng.collect_output([1], 25)[1][0]), 25)
        self.assertTrue(self.eng.finished(1))

    async def test_late_step_cannot_recreate_closed_session(self):
        self.eng.closed_sessions.add(1)
        self.eng._ensure = Mock(side_effect=AssertionError('recreated closed session'))
        output, _ = self.eng.step({1: (None, 16000)}, 25)
        self.assertEqual(output, {})
        self.eng._ensure.assert_not_called()

    async def test_short_terminal_fragment_is_preserved_with_bounded_silence(self):
        import numpy as np
        tail = np.arange(160, dtype=np.float32)
        result = self.worker.terminal_audio(tail, 16000)
        self.assertEqual(len(result), 640)
        np.testing.assert_array_equal(result[:160], tail)
        self.assertTrue((result[160:] == 0).all())
        normal = np.ones(32000, dtype=np.float32)
        self.assertIs(self.worker.terminal_audio(normal, 16000), normal)
