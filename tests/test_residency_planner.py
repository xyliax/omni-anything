from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engines/conveyor/worker/engine_patch'))
from residency_planner import AdmissionProfile, ResidencyPlanner, MaximumContextCosts, MaximumContextPlanner


def profile(**changes):
    return replace(AdmissionProfile(
        horizon_s=8, compute_s=.1, initial_blocks=20, growth_blocks_per_period=2,
        max_evict_blocks=20, h2d_blocks_per_s=1000, d2h_blocks_per_s=1000,
        transfer_overhead_s=.001, safety_s=.01, gpu_reserve_blocks=1,
        host_reserve_blocks=1, max_sessions=4), **changes)


def planner(p=None, **changes):
    args = dict(period_s=2, slots=4, epoch=0, restore_lead_s=.3,
                retained_prefix_blocks=2, gpu_blocks=200, host_blocks=500)
    args.update(changes)
    return ResidencyPlanner(p or profile(), **args)


class PlannerTests(unittest.TestCase):
    def test_twelve_sessions_share_four_group_windows(self):
        p = planner(profile(max_sessions=12), gpu_blocks=1000, host_blocks=2000)
        for i in range(12):
            result = p.try_admit(str(i), now=0, current_blocks={})
            self.assertTrue(result['admitted'], result)
            self.assertEqual(result['plan']['group'], i % 4)
        groups = result['forecast']['groups']
        self.assertEqual([len(g['members']) for g in groups], [3,3,3,3])
        self.assertTrue(all(g['assigned_ceiling_blocks'] <= g['window_capacity_blocks'] for g in groups))

    def test_future_ceiling_cannot_spend_temporarily_unused_group_bandwidth(self):
        p = planner(profile(initial_blocks=2, growth_blocks_per_period=0, max_evict_blocks=400))
        result = p.try_admit('small-now', now=0, current_blocks={})
        self.assertFalse(result['admitted'])
        self.assertIn('restore_window', result['reason'])

    def test_a_late_first_input_still_reserves_initial_backing(self):
        p = planner(profile(initial_blocks=200, growth_blocks_per_period=1), gpu_blocks=1000, host_blocks=2000)
        self.assertTrue(p.try_admit('a', now=0, current_blocks={})['admitted'])
        # No input has executed, even though several planned ticks passed.
        # A second session in this same slot would exceed the backing window.
        from dataclasses import replace
        plans = [p.plans['a'], replace(p.plans['a'], request_id='b', admitted_at=8, first_tick=8)]
        reason, _ = p.check(plans, now=8, current_blocks={})
        self.assertEqual(reason,'backing_window')

    def test_stable_slots_multiple_members_and_idempotent_admission(self):
        p = planner(profile(max_sessions=8))
        assigned = []
        for i in range(6):
            result = p.try_admit(str(i), now=0, current_blocks={})
            self.assertTrue(result['admitted'], result)
            assigned.append(result['plan']['slot'])
        self.assertEqual(assigned, [0, 1, 2, 3, 0, 1])
        before = dict(p.plans)
        self.assertEqual(p.try_admit('0', now=1, current_blocks={})['plan'], before['0'].wire())
        self.assertEqual(p.plans, before)

    def test_departure_reuses_slot_without_rephasing_others(self):
        p = planner()
        for i in range(4):
            self.assertTrue(p.try_admit(str(i), now=0, current_blocks={})['admitted'])
        old = dict(p.plans)
        p.release('1')
        result = p.try_admit('next', now=3.1, current_blocks={})
        self.assertTrue(result['admitted'], result)
        self.assertEqual(result['plan']['slot'], 1)
        self.assertEqual(result['plan']['first_tick'], 4.5)
        for key in ('0', '2', '3'):
            self.assertEqual(p.plans[key], old[key])

    def test_free_slot_is_insufficient_for_each_resource(self):
        cases = [
            (profile(compute_s=.6), {}, 'compute_window'),
            (profile(d2h_blocks_per_s=10), {}, 'backing_window'),
            (profile(h2d_blocks_per_s=10), {}, 'restore_window'),
            (profile(), {'gpu_blocks': 10}, 'gpu_capacity'),
            (profile(), {'host_blocks': 10}, 'host_capacity'),
        ]
        for pr, args, reason in cases:
            with self.subTest(reason=reason):
                p = planner(pr, **args)
                result = p.try_admit('new', now=0, current_blocks={})
                self.assertFalse(result['admitted'])
                self.assertIn(reason, result['reason'])
                self.assertEqual(p.plans, {})

    def test_growth_and_full_restore_allocation_are_charged(self):
        p = planner(gpu_blocks=25)
        result = p.try_admit('a', now=0, current_blocks={})
        self.assertFalse(result['admitted'])  # 20 now fits; 30 within H does not
        p = planner(gpu_blocks=31)
        result = p.try_admit('a', now=0, current_blocks={})
        self.assertTrue(result['admitted'])
        self.assertEqual(result['forecast']['gpu_peak_blocks'], 31)

    def test_staggering_can_fit_when_full_residency_does_not(self):
        p = planner(gpu_blocks=81)
        # Let the first session leave startup before the next one joins.
        for i, now in enumerate((0, 3, 6, 9)):
            result = p.try_admit(str(i), now=now, current_blocks={})
            self.assertTrue(result['admitted'], result)
        self.assertLessEqual(result['forecast']['gpu_peak_blocks'], 81)
        self.assertGreater(4 * 30, p.gpu_blocks)

    def test_current_physical_pressure_and_closing_reservations(self):
        p = planner(profile(max_sessions=1))
        self.assertFalse(p.try_admit('a', now=0, current_blocks={}, used_gpu_blocks=200)['admitted'])
        self.assertTrue(p.try_admit('a', now=0, current_blocks={})['admitted'])
        self.assertFalse(p.try_admit('b', now=1, current_blocks={})['admitted'])
        # Only explicit, confirmed release removes the reservation.
        p.release('a')
        self.assertTrue(p.try_admit('b', now=1, current_blocks={})['admitted'])

    def test_unconfirmed_eviction_cannot_supply_capacity_or_hide_restore_traffic(self):
        p = planner(gpu_blocks=81)
        for i, now in enumerate((0, 3)):
            self.assertTrue(p.try_admit(str(i), now=now, current_blocks={}, recoverable_blocks={})['admitted'])
        result = p.try_admit('2', now=6, current_blocks={}, recoverable_blocks={})
        self.assertFalse(result['admitted'])  # no backing: three full histories do not fit
        result = p.try_admit('2', now=6, current_blocks={}, recoverable_blocks={'0': 20, '1': 20})
        self.assertTrue(result['admitted'])
        p = planner(profile(h2d_blocks_per_s=10))
        result = p.try_admit('new', now=0, current_blocks={}, recoverable_blocks={})
        self.assertFalse(result['admitted'])
        self.assertIn('restore_window', result['reason'])  # future maximum transfer still reserved

    def test_ten_thousand_sequential_admissions_leave_no_reservations(self):
        p = planner(profile(max_sessions=1))
        for i in range(10_000):
            result = p.try_admit(str(i), now=i * 3, current_blocks={})
            self.assertTrue(result['admitted'])
            p.release(str(i))
        self.assertEqual(p.plans, {})

    def test_invalid_estimates_fail_closed(self):
        for change in ({'horizon_s': float('nan')}, {'compute_s': 0}, {'max_sessions': True}):
            with self.assertRaises(ValueError):
                profile(**change)
        with self.assertRaises(ValueError):
            planner(restore_lead_s=.6)
        with self.assertRaises(ValueError):
            planner(profile(horizon_s=1))


class MaximumContextPlannerTests(unittest.TestCase):
    def planner(self, **changes):
        costs = MaximumContextCosts(compute_s=.1, backup_s=.02, max_evict_blocks=40,
            h2d_blocks_per_s=1000, transfer_overhead_s=.001, safety_s=.01,
            gpu_reserve_blocks=1, host_reserve_blocks=1, max_sessions=8)
        args = dict(max_context_blocks=100, period_s=2, slots=4, epoch=0,
                    restore_lead_s=.2, retained_prefix_blocks=2, gpu_blocks=281, host_blocks=1000)
        args.update(changes)
        return MaximumContextPlanner(costs, **args)

    def test_maximum_histories_fit_cyclically_without_a_growth_forecast(self):
        p = self.planner()
        for i in range(4):
            result = p.try_admit(str(i), now=0, current_blocks={})
            self.assertTrue(result['admitted'], result)
            self.assertIsNone(result['plan']['forecast_until'])
        self.assertEqual(result['forecast']['gpu_peak_blocks'], 281)
        self.assertEqual(result['forecast']['host_blocks'], 401)
        self.assertGreater(4 * 100, p.gpu_blocks)
        # Short histories do not permit a fifth lifetime reservation.
        self.assertFalse(p.try_admit('fifth', now=0, current_blocks={})['admitted'])
        before = dict(p.plans)
        reason, full = p.check(list(p.plans.values()), now=20, current_blocks={str(i):100 for i in range(4)})
        self.assertIsNone(reason)
        self.assertEqual(full['gpu_peak_blocks'], result['forecast']['gpu_peak_blocks'])
        self.assertEqual(p.plans, before)

    def test_actual_pressure_and_context_limit_are_independent_checks(self):
        p = self.planner()
        self.assertTrue(p.try_admit('a', now=0, current_blocks={})['admitted'])
        self.assertEqual(p.check(list(p.plans.values()), now=0,
            current_blocks={'a':101})[0], 'maximum_context_exceeded')
        self.assertEqual(p.check(list(p.plans.values()), now=0,
            current_blocks={}, used_gpu_blocks=281)[0], 'current_gpu_pressure')

    def test_release_changes_version_without_moving_remaining_phases(self):
        p = self.planner()
        p.try_admit('a', now=0, current_blocks={})
        p.try_admit('b', now=0, current_blocks={})
        other = p.plans['b']
        version = p.generation
        p.release('a')
        self.assertGreater(p.generation, version)
        self.assertEqual(p.plans['b'], other)
        p.release('a')
        self.assertEqual(p.generation, version+1)

    def test_host_limit_uses_maximum_not_current_short_history(self):
        p = self.planner(host_blocks=100)
        result = p.try_admit('a', now=0, current_blocks={'a':1})
        self.assertFalse(result['admitted'])
        self.assertIn('host_capacity', result['reason'])

    def test_tie_break_reduces_alignment_without_changing_existing_phases(self):
        p = self.planner(gpu_blocks=1000)
        first = p.try_admit('a', now=.61, source_start=.61, current_blocks={})
        self.assertEqual(first['plan']['slot'], 2)  # earliest equally loaded future phase is 1s
        saved = p.plans['a']
        second = p.try_admit('b', now=.64, source_start=.64, current_blocks={})
        self.assertEqual(second['plan']['slot'], 3)
        self.assertEqual(p.plans['a'], saved)

    def test_calibrated_group_cost_is_shared_but_unknown_size_falls_back(self):
        from dataclasses import replace
        p = self.planner(gpu_blocks=1000)
        p.profile = replace(p.profile, compute_s=.3, compute_by_group={'2': .35})
        # Two members in a .5s interval fit only with the independently
        # calibrated group cost; no per-member multiplication of that cost.
        for i in range(8):
            self.assertTrue(p.try_admit(str(i), now=0, current_blocks={})['admitted'])
        p.profile = replace(p.profile, max_sessions=12)
        ninth = p.try_admit('ninth', now=0, current_blocks={})
        self.assertFalse(ninth['admitted'])
        self.assertIn('compute_window', ninth['reason'])
