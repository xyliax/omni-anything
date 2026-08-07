from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from experiments.e2_kv_conveyor.core import (
    ComputeProfile,
    SimulationConfig,
    capacity_extension,
    load_compute_profile,
    phase_offsets,
    simulate,
)


class ConveyorModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.compute = ComputeProfile(
            source="fixture",
            busy_ms_by_batch={1: 700.0, 8: 900.0},
            decode_step_ms_by_batch={1: 20.0, 8: 25.0},
            steps_per_tick=34,
        )
        self.config = SimulationConfig(ticks=150, tail_tokens=4096, lead_ms=20)

    def test_tdma_offsets_follow_measured_group_service(self) -> None:
        offsets = phase_offsets(
            "tdma",
            8,
            2000,
            0,
            compute=self.compute,
            tdma_group_size=7,
            tdma_guard_ms=30,
        )
        self.assertEqual(offsets[:7], [0.0] * 7)
        self.assertEqual(offsets[7], 930.0)

    def test_conveyor_extends_capacity_when_staging_is_bounded(self) -> None:
        resident, _ = simulate(
            self.config,
            self.compute,
            [18.0, 18.0, 18.0, 40.0],
            conveyor=False,
            phase_policy="synchronized",
            seed=0,
        )
        conveyor, _ = simulate(
            self.config,
            self.compute,
            [18.0],
            conveyor=True,
            phase_policy="tdma",
            seed=0,
        )
        self.assertEqual(conveyor["transfer_deadline_misses"], 0)
        self.assertLess(conveyor["staging_peak_sessions"], self.config.sessions)
        self.assertGreater(capacity_extension(resident, conveyor), 1.0)

    def test_synchronized_transfers_miss_a_short_lead(self) -> None:
        short = SimulationConfig(ticks=10, tail_tokens=4096, lead_ms=5)
        summary, _ = simulate(
            short,
            self.compute,
            [18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 80.0],
            conveyor=True,
            phase_policy="synchronized",
            seed=0,
        )
        self.assertGreater(summary["transfer_deadline_misses"], 0)

    def test_content_cannot_move_before_previous_tick_finishes(self) -> None:
        config = SimulationConfig(ticks=2, tail_tokens=4096, lead_ms=1900)
        _, transfers = simulate(
            config,
            self.compute,
            [18.0],
            conveyor=True,
            phase_policy="tdma",
            seed=0,
        )
        second_tick = [row for row in transfers if row.tick == 1]
        self.assertTrue(second_tick)
        self.assertTrue(all(row.release_ms >= row.content_available_ms for row in second_tick))
        self.assertTrue(any(row.release_ms > row.planned_release_ms for row in second_tick))

    def test_staging_never_counts_two_tails_for_one_session(self) -> None:
        overloaded = ComputeProfile(
            source="fixture",
            busy_ms_by_batch={1: 2600.0, 8: 2600.0},
            decode_step_ms_by_batch={1: 20.0, 8: 25.0},
            steps_per_tick=34,
        )
        summary, _ = simulate(
            SimulationConfig(ticks=4, tail_tokens=4096),
            overloaded,
            [18.0],
            conveyor=True,
            phase_policy="synchronized",
            seed=0,
        )
        self.assertLessEqual(summary["staging_peak_sessions"], 8)

    def test_invalid_configuration_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "tdma_group_size"):
            SimulationConfig(sessions=4, tdma_group_size=5)

    def test_compute_profile_parses_scheduler_trace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "scheduler.log"
            path.write_text(
                "100.000 s1ea:53E s2eb:53E\n"
                "100.020 s1ea:1 s2eb:1\n"
                "100.040 s1ea:1 s2eb:1\n"
                "102.000 s1ea:53E s2eb:53E\n"
                "102.020 s1ea:1 s2eb:1\n"
                "102.040 s1ea:1 s2eb:1\n",
                encoding="utf-8",
            )
            profile = load_compute_profile(path)
        self.assertIn(2, profile.busy_ms_by_batch)
        self.assertAlmostEqual(profile.decode_step_ms_by_batch[2], 20.0, places=2)


if __name__ == "__main__":
    unittest.main()
