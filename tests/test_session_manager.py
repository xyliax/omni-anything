"""Independent control/copy progress, with no vLLM installation or GPU required."""
from __future__ import annotations

import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch
from types import SimpleNamespace

PATCH = Path(__file__).resolve().parents[1] / "engines/conveyor/worker/engine_patch"
sys.path.insert(0, str(PATCH))
from session_manager import SessionManager, SessionPlan
from copy_service import CopyService
from manager_adapter import VllmKVMemoryManager
from session_manager import ManagedSession


class Block:
    def __init__(self, block_id):
        self.block_id, self.ref_cnt = block_id, 0
        self._block_hash = f'hash{block_id}'

    @property
    def block_hash(self):
        return self._block_hash


class Pool:
    """Reference-counting test pool; detects premature releases and reuse."""
    def __init__(self, count):
        self.blocks = [Block(i) for i in range(count)]
        self.valid = {}
        self.cached_block_hash_to_block = SimpleNamespace(insert=self.insert)

    def insert(self, key, block):
        self.valid[key] = block

    def touch(self, blocks):
        for block in blocks:
            block.ref_cnt += 1

    def free_blocks(self, blocks):
        for block in blocks:
            assert block.ref_cnt > 0, "releasing an unowned block"
            block.ref_cnt -= 1

    def get_cached_block(self, key, groups):
        return [self.valid[key]] if key in self.valid else None

    def get_num_free_blocks(self):
        return sum(b.ref_cnt == 0 for b in self.blocks)

    def get_new_blocks(self, count):
        selected = [b for b in self.blocks if b.ref_cnt == 0][:count]
        assert len(selected) == count
        self.touch(selected)
        return selected


class PhysicalReferenceTests(unittest.TestCase):
    def setUp(self):
        self.adapter = VllmKVMemoryManager.__new__(VllmKVMemoryManager)
        a = self.adapter
        a.lock = threading.RLock()
        a.gpu, a.cpu = Pool(10), Pool(10)
        a.native = SimpleNamespace(fa_gidx=0)
        a.block_size, a.hold, a.min_free = 16, False, 0
        a.observer, a.copies, a.manager = Mock(), Mock(), Mock()
        a.manager.restoration_paused = False
        a.manager.restore_policy = 'pre_tick'
        a.closed_sessions = set()
        a.planner = None
        self.request = SimpleNamespace(request_id="s1e1", status="idle",
                                       num_computed_tokens=96,
                                       block_hashes=[f"hash{i}" for i in range(6)])
        a.gpu.touch(a.gpu.blocks[:6])
        # Block 2 lacks a completed host copy, 3 is shared / in-flight.
        for i in (0, 1, 3, 4, 5):
            a.cpu.insert(f"hash{i}", a.cpu.blocks[i])
        a.gpu.touch([a.gpu.blocks[3]])
        self.owned = list(range(6))
        self.kvm = Mock()
        self.native_table = SimpleNamespace(req_to_blocks={'s1e1': list(a.gpu.blocks[:6])},
                                            num_cached_block={'s1e1': 6})
        self.kvm.coordinator.single_type_managers = [self.native_table]
        self.kvm.usage = .6
        self.kvm.get_block_ids.side_effect = lambda _: (self.owned[:],)
        def free(_):
            a.gpu.free_blocks([a.gpu.blocks[i] for i in self.owned])
            self.owned.clear()
            self.native_table.req_to_blocks.pop('s1e1', None)
            self.native_table.num_cached_block.pop('s1e1', None)
        self.kvm.free.side_effect = free
        def evict_hashes(ids):
            for bid in ids:
                a.gpu.blocks[bid]._block_hash = None
        self.kvm.evict_blocks.side_effect = evict_hashes
        a.scheduler = SimpleNamespace(requests={"s1e1": self.request}, kv_cache_manager=self.kvm)
        self.session = ManagedSession("s1e1", SessionPlan(2, 12, .2, 2), activity="idle")
        a.manager.sessions = {'s1e1': self.session}
        # Only the status enum is needed; the adapter's pure reference logic
        # is exercised without loading the optional GPU dependency.
        fake = SimpleNamespace(RequestStatus=SimpleNamespace(WAITING_FOR_STREAMING_REQ="idle"))
        self.enterContext(patch.dict(sys.modules, {"vllm.v1.request": fake}))

    def test_evict_requires_confirmed_host_copy_and_exclusive_gpu_reference(self):
        self.assertTrue(self.adapter.evict(self.session))
        self.kvm.evict_blocks.assert_called_once_with({4, 5})
        self.assertEqual([i for i, _ in self.session.host_pins], [4, 5])
        self.assertEqual([b.block_id for b in self.session.resident_pins], [0, 1, 2, 3])
        self.assertEqual([b.ref_cnt for b in self.adapter.gpu.blocks[:6]], [1, 1, 1, 2, 0, 0])
        self.assertTrue(self.request._omni_kv_evicted)

    def test_plan_transition_defers_allocation_without_losing_host_pins(self):
        self.adapter.evict(self.session)
        before = list(self.session.host_pins)
        self.adapter.manager.restoration_paused = True
        self.assertFalse(self.adapter.restore(self.session))
        self.assertEqual(self.session.host_pins, before)
        self.adapter.copies.submit.assert_not_called()
        self.adapter.manager.restoration_paused = False
        self.assertTrue(self.adapter.restore(self.session))

    def test_late_input_plan_does_not_move_the_missing_history_deadline(self):
        from dataclasses import replace
        self.adapter.evict(self.session)
        self.session.plan = replace(self.session.plan, next_tick=14)
        self.assertEqual(self.session.restoration_tick, 12)
        self.adapter.restore(self.session)
        self.adapter.copies.submit.call_args.args[-1]()
        self.assertEqual(self.session.restoration_tick, 14)

    def test_demand_cannot_bypass_earlier_requested_complete_destination(self):
        self.adapter.evict(self.session)
        self.session.restoration_requested = True
        other = ManagedSession('s2e1', SessionPlan(2, 14, .2, 1), activity='idle',
                               host_pins=[(6, self.adapter.cpu.blocks[6])], restoration_requested=True)
        self.adapter.manager.sessions['s2e1'] = other
        self.adapter.manager.restore_policy = 'on_demand'
        self.assertFalse(self.adapter.restore(other))
        self.adapter.copies.submit.assert_not_called()

    def test_range_budget_and_unfinished_block_boundary(self):
        self.request.num_computed_tokens = 95  # block 5 is not complete
        self.session.plan = SessionPlan(2, 12, .2, 1, ((3, 6),), 1)
        self.assertTrue(self.adapter.evict(self.session))
        self.kvm.evict_blocks.assert_called_once_with({4})

    def test_restore_publishes_only_after_completion_and_pins_until_resume(self):
        self.adapter.evict(self.session)
        self.assertTrue(self.adapter.restore(self.session))
        args = self.adapter.copies.submit.call_args.args
        self.assertTrue(self.session.restore_inflight)
        self.assertEqual(self.adapter.gpu.valid, {})
        self.assertEqual([self.adapter.cpu.blocks[i].ref_cnt for i in (4, 5)], [1, 1])
        args[-1]()  # physical completion
        self.assertFalse(self.session.restore_inflight)
        self.assertEqual(len(self.adapter.gpu.valid), 2)
        self.assertEqual(len(self.session.resident_pins), 6)
        self.adapter.release_idle_pins(self.session)
        self.assertEqual([b.ref_cnt for b in self.adapter.gpu.blocks[:6]], [0, 0, 0, 1, 0, 0])

    def test_reversed_free_queue_does_not_reverse_physical_copy_mapping(self):
        self.adapter.evict(self.session)
        # Force the allocator's actual descending-free-order case and a host
        # pin list whose logical order differs from physical backing order.
        self.session.host_pins.reverse()
        def allocate(n):
            blocks = self.adapter.gpu.blocks[8:8+n]
            self.adapter.gpu.touch(blocks)
            return list(reversed(blocks))
        self.adapter.gpu.get_new_blocks = allocate
        self.adapter.restore(self.session)
        _, source, target, _, done = self.adapter.copies.submit.call_args.args
        self.assertEqual(list(zip(source,target)),[(4,8),(5,9)])
        self.assertFalse(self.adapter.gpu.valid)
        done()
        for sid, tid in zip(source,target):
            self.assertIs(self.adapter.gpu.valid[self.adapter.cpu.blocks[sid].block_hash],
                          self.adapter.gpu.blocks[tid])

    def test_cancel_retains_inflight_references_and_never_publishes_cancelled_targets(self):
        self.adapter.evict(self.session)
        self.adapter.restore(self.session)
        self.session.cancelled = True
        self.adapter.release_idle_pins(self.session)
        self.assertEqual([self.adapter.gpu.blocks[i].ref_cnt for i in (4, 5)], [1, 1])
        self.assertEqual([self.adapter.cpu.blocks[i].ref_cnt for i in (4, 5)], [1, 1])
        self.adapter.copies.submit.call_args.args[-1]()
        self.assertEqual(self.adapter.gpu.valid, {})
        self.assertEqual([self.adapter.gpu.blocks[i].ref_cnt for i in (4, 5)], [0, 0])
        self.assertEqual([self.adapter.cpu.blocks[i].ref_cnt for i in (4, 5)], [0, 0])

    def test_capacity_deferral_keeps_host_sources_and_does_not_allocate(self):
        self.adapter.evict(self.session)
        self.adapter.min_free = .9
        self.assertFalse(self.adapter.restore(self.session))
        self.adapter.copies.submit.assert_not_called()
        self.assertEqual(len(self.session.host_pins), 2)

    def test_input_readiness_waits_for_publication_and_reserves_until_backend_allocates(self):
        self.adapter.evict(self.session)
        result = self.adapter.prepare_input('s1e1', 'frame-1')
        self.assertFalse(result['ready'])
        self.assertFalse(self.adapter.prepare_input('s1e1', 'frame-1')['ready'])
        self.assertEqual(self.adapter.copies.submit.call_count, 1)
        self.adapter.copies.submit.call_args.args[-1]()
        # The real pool already indexes the retained complete blocks.
        for block in self.session.resident_pins:
            self.adapter.gpu.insert(block.block_hash, block)
        self.assertTrue(self.adapter.prepare_input('s1e1', 'frame-1')['ready'])
        self.assertTrue(self.adapter.prepare_input('s1e1', 'frame-1')['ready'])
        self.assertFalse(self.adapter.prepare_input('s1e1', 'frame-2')['ready'])
        manager = SessionManager(self.adapter)
        manager.sessions['s1e1'] = self.session
        manager.on_resume('s1e1')
        self.assertFalse(self.session.resident_pins)
        self.assertEqual(len(self.native_table.req_to_blocks['s1e1']), 6)
        self.assertTrue(all(block.ref_cnt >= 1 for block in self.native_table.req_to_blocks['s1e1']))
        self.assertEqual(self.request.num_computed_tokens, 96)
        self.assertFalse(self.request._omni_kv_evicted)

    def test_unfinished_tail_is_retained_and_rebound_without_recomputation(self):
        self.request.num_computed_tokens = 95
        self.native_table.num_cached_block['s1e1'] = 5
        self.adapter.gpu.blocks[5]._block_hash = None
        self.adapter.evict(self.session)
        self.assertIs(self.session.retained_table[5], self.adapter.gpu.blocks[5])
        self.assertEqual(self.adapter.gpu.blocks[5].ref_cnt, 1)
        self.adapter.prepare_input('s1e1', 'frame-1')
        self.adapter.copies.submit.call_args.args[-1]()
        self.assertTrue(self.adapter.prepare_input('s1e1', 'frame-1')['ready'])
        self.assertIs(self.native_table.req_to_blocks['s1e1'][5], self.adapter.gpu.blocks[5])
        self.assertEqual(self.native_table.num_cached_block['s1e1'], 5)
        self.assertEqual(self.request.num_computed_tokens, 95)

    def test_restored_bytes_in_wrong_logical_position_are_rejected(self):
        self.adapter.evict(self.session)
        self.adapter.prepare_input('s1e1', 'frame-1')
        self.adapter.copies.submit.call_args.args[-1]()
        table = self.session.retained_table
        table[4], table[5] = table[5], table[4]
        with self.assertRaisesRegex(RuntimeError, 'logical KV history changed'):
            self.adapter.prepare_input('s1e1', 'frame-1')
        self.assertNotIn('s1e1', self.native_table.req_to_blocks)

    def test_closing_reservation_waits_for_copy_callback_and_rejects_late_input(self):
        self.adapter.planner = Mock()
        self.adapter.scheduler.requests = {}
        self.adapter.copies.pending_requests.return_value = {'s1e1-deadbeef'}
        self.assertFalse(self.adapter.release_session('s1e1')['released'])
        self.adapter.planner.release.assert_not_called()
        with self.assertRaises(ValueError):
            self.adapter.prepare_input('s1e1', 'late-frame')
        self.adapter.copies.pending_requests.return_value = set()
        self.assertTrue(self.adapter.release_session('s1e1')['released'])
        self.adapter.planner.release.assert_called_once_with('s1e1')

    def test_forecast_credit_excludes_missing_host_coverage_and_shared_blocks(self):
        a = self.adapter
        a.planner = SimpleNamespace(plans={'s1e1': self.session.plan})
        for block in a.gpu.blocks[:6]:
            a.gpu.insert(block.block_hash, block)
        with a.lock:
            self.assertEqual(a.recoverable_snapshot(), {'s1e1': 2})
            # Already missing GPU contents are backed, but a competing GPU
            # reference must never be counted as reclaimable capacity.
            del a.gpu.valid['hash4']
            a.gpu.touch([a.gpu.blocks[5]])
            self.assertEqual(a.recoverable_snapshot(), {'s1e1': 1})

    def test_admission_cannot_spend_the_copy_allocator_reserve(self):
        from tests.test_residency_planner import profile
        a = self.adapter
        a.admission_profile = profile()
        a.scheduler.requests = {}
        a.min_free = .5
        with patch.dict('os.environ', {'OMNI_RESTORE_LEAD_S': '.2', 'OMNI_RETAINED_PREFIX_BLOCKS': '1'}):
            a.admit('new', 2, 4, 0)
        self.assertEqual(a.planner.profile.gpu_reserve_blocks, 5)

    def test_simultaneous_load_and_store_callbacks_keep_their_own_request_ids(self):
        a = self.adapter
        a.native._store_event_to_reqs = {5: ["store-session"]}
        a.native._process_store_event = Mock()
        a.scheduler._update_from_kv_xfer_finished = Mock()
        meta = SimpleNamespace(load_cpu_blocks=[1], load_gpu_blocks=[2], load_event=4,
                               load_event_to_reqs={4: ["load-session"]},
                               store_gpu_blocks=[3], store_cpu_blocks=[4], store_event=5,
                               need_flush=True)
        a.dispatch(meta)
        load, store = a.copies.submit.call_args_list
        # Complete in reverse order, after both callbacks have been created.
        store.args[-1]()
        fake_outputs = SimpleNamespace(KVConnectorOutput=lambda **kwargs: SimpleNamespace(**kwargs))
        with patch.dict(sys.modules, {"vllm.v1.outputs": fake_outputs}):
            load.args[-1]()
        done = a.scheduler._update_from_kv_xfer_finished.call_args.args[0]
        self.assertEqual(done.finished_recving, {"load-session"})
        a.native._process_store_event.assert_called_once_with(5)
        self.assertEqual(meta.load_cpu_blocks, [])
        self.assertEqual(meta.store_gpu_blocks, [])
        self.assertFalse(meta.need_flush)


class SessionManagerTests(unittest.TestCase):
    def setUp(self):
        self.now = 10.0
        self.adapter = Mock()
        self.adapter.lock = threading.RLock()
        self.manager = SessionManager(self.adapter, clock=lambda: self.now)
        self.plan = SessionPlan(2, 12, .2, 2)
        self.manager.set_plan("s1e1", self.plan)

    def test_idle_eviction_and_restore_follow_timer_without_steps(self):
        state = self.manager.sessions["s1e1"]
        def evict(session):
            session.host_pins = [(2, "host block")]
            return True
        self.adapter.evict.side_effect = evict
        self.manager.on_idle("s1e1")
        self.manager.advance()
        self.adapter.evict.assert_called_once_with(state)
        self.adapter.restore.assert_not_called()
        self.now = 11.81
        self.manager.advance()
        self.adapter.restore.assert_called_once_with(state)
        self.assertEqual(self.adapter.evict.call_count, 1)

    def test_no_eviction_after_restore_window_or_during_active_use(self):
        self.manager.advance()
        self.adapter.evict.assert_not_called()
        self.manager.on_idle("s1e1")
        self.now = 11.9
        self.manager.advance()
        self.adapter.evict.assert_not_called()

    def test_queued_plan_can_be_replaced_and_capacity_refusal_retried(self):
        self.manager.on_idle("s1e1")
        state = self.manager.sessions["s1e1"]
        state.evicted_generation = state.idle_generation
        state.host_pins = [(2, "host block")]
        self.adapter.restore.return_value = False
        self.manager.set_plan("s1e1", SessionPlan(2, 11, .2, 3, ((3, 5),)))
        self.now = 10.9
        self.manager.advance()
        self.manager.advance()
        self.assertEqual(self.adapter.restore.call_count, 2)
        self.assertEqual(state.plan.candidates(8), [3, 4])

    def test_blocked_oldest_restore_does_not_block_later_idle_eviction(self):
        self.manager.on_idle('s1e1')
        oldest = self.manager.sessions['s1e1']
        oldest.host_pins = [(2, 'host block')]
        oldest.evicted_generation = oldest.idle_generation
        self.manager.set_plan('s2e1', SessionPlan(2, 14, .2, 2))
        self.manager.on_idle('s2e1')
        self.now = 11.9
        calls = []
        self.adapter.evict.side_effect = lambda session: calls.append(('evict', session.request_id)) or True
        self.adapter.restore.side_effect = lambda session: calls.append(('restore', session.request_id)) or False
        self.manager.advance()
        self.assertEqual(calls, [('evict', 's2e1'), ('restore', 's1e1')])

    def test_overtaking_input_and_cancel_do_not_issue_another_copy(self):
        state = self.manager.sessions["s1e1"]
        self.manager.on_idle("s1e1")
        state.restore_inflight = True
        self.manager.on_resume("s1e1")
        self.manager.advance()
        self.adapter.restore.assert_not_called()
        self.manager.cancel("s1e1")
        self.assertTrue(state.cancelled)
        self.assertTrue(state.restore_inflight)  # completion owns transfer pins
        self.assertNotIn("s1e1", self.manager.sessions)

    def test_bad_ranges_and_nonfinite_times_are_rejected(self):
        for ranges in (((0, 2),), ((3, 5), (4, 6)), ((3, 3),)):
            with self.subTest(ranges=ranges), self.assertRaises(ValueError):
                SessionPlan(2, 12, .2, 2, ranges)
        with self.assertRaises(ValueError):
            SessionPlan(2, float("nan"), .2, 2)


class CopyServiceTests(unittest.TestCase):
    def test_integrity_failure_retains_pins_and_never_publishes(self):
        backend = Mock(verify_copies=True)
        backend.last_submit = {}
        backend.launch.return_value = (object(), 4096)
        backend.finished.return_value = True
        backend.elapsed_ms.return_value = .2
        backend.verify.side_effect = RuntimeError('physical KV bytes differ')
        callback, observer = Mock(), Mock()
        service = CopyService(backend, observer)
        service.submit('H2D', [1], [4], ['session'], callback)
        with self.assertRaisesRegex(RuntimeError, 'copy service failed'):
            service.close()
        callback.assert_not_called()
        self.assertEqual(service.pending_requests(), {'session'})
        self.assertNotIn('published', [call.args[0] for call in observer.call_args_list])

    def test_completes_while_no_model_step_is_called(self):
        device_done = threading.Event()
        published = threading.Event()
        backend = Mock()
        backend.last_submit = {}
        backend.launch.return_value = (device_done, 4096)
        backend.finished.side_effect = lambda handle: handle.is_set()
        backend.elapsed_ms.return_value = .2
        observer = Mock()
        service = CopyService(backend, observer)
        self.addCleanup(service.close)
        service.submit("H2D", [1], [4], ["s1e1"], published.set)
        self.assertFalse(published.wait(.02))
        device_done.set()
        self.assertTrue(published.wait(1), "completion must progress without a scheduler iteration")
        service.close()
        self.assertEqual([call.args[0] for call in observer.call_args_list],
                         ["queued", "submitted", "device_complete_observed", "published"])

    def test_copy_failure_is_visible_and_never_publishes(self):
        backend = Mock()
        backend.launch.side_effect = RuntimeError("device failed")
        callback = Mock()
        service = CopyService(backend, Mock())
        service.submit("H2D", [1], [2], ["s1e1"], callback)
        with self.assertRaisesRegex(RuntimeError, "copy service failed"):
            service.close()
        callback.assert_not_called()
