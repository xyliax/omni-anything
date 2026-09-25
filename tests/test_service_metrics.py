import unittest

from infra.trace.service import ServiceSLO, evaluate


class ServiceMetricsTests(unittest.TestCase):
    def test_capacity_summary_does_not_turn_invalid_or_untested_into_failure(self):
        from experiments.conveyor.capacity import summarize
        points = [dict(system='resident',concurrency=n,seed=s,verdict=v)
                  for n,v in [(4,'pass'),(8,'invalid'),(12,'fail')] for s in [11,22]]
        summary = summarize(points,[4,8,12],[11,22])['resident']
        self.assertEqual(summary['maximum_tested_stable'],4)
        self.assertEqual(summary['next_tested_failure'],12)
        self.assertEqual(summary['states'][8],'invalid')

    def fixture(self):
        slo = ServiceSLO(horizon_s=8, warmup_s=4, max_miss_ratio=0,
                         window_s=4, max_lag_periods=1, max_consecutive_late=2)
        client = dict(total=1, err=0, sessions=[dict(sid=1, completed=True, audio_start_ns=0,
            audio_end_ns=14_000_000_000, duration_s=14, period_ns=2_000_000_000,
            epoch_ns=0, slots=1, slot=0)])
        gateway, worker = [], []
        for seq in range(1, 8):
            ready = seq * 2_000_000_000
            key = dict(session=1, epoch=1, frame=seq)
            gateway.extend([dict(**key, event='input_ready', time_ns=ready),
                            dict(**key, event='input_release', time_ns=ready)])
            worker.extend([dict(**key, event='input_received', time_ns=ready),
                           dict(**key, event='engine_input', time_ns=ready),
                           dict(**key, event='compute_complete', time_ns=ready+100_000_000,
                                tokens=25, finish_reason='length')])
        return slo, client, gateway, worker

    def test_actual_completion_not_rpc_latency_controls_deadline(self):
        args = self.fixture()
        self.assertEqual(evaluate(*args, 25)['verdict'], 'pass')
        for row in args[3]:
            if row['event'] == 'compute_complete' and row['frame'] == 3:
                row['time_ns'] += 3_000_000_000
        report = evaluate(*args, 25)
        self.assertEqual(report['verdict'], 'fail')
        self.assertEqual(report['misses'], 1)

    def test_unreleased_or_uncompleted_frames_stay_in_denominator(self):
        slo, client, gateway, worker = self.fixture()
        gateway = [r for r in gateway if r['event'] != 'input_release' or r['frame'] not in (3,4)]
        worker = [r for r in worker if r['frame'] not in (3,4)]
        report = evaluate(slo, client, gateway, worker, 25)
        self.assertEqual(report['verdict'], 'fail')
        self.assertEqual(report['misses'], 2)
        self.assertEqual(report['per_session'][0]['maximum_lag_streak'], 2)

    def test_duplicate_completion_is_invalid_and_admission_queue_cannot_pass(self):
        args = self.fixture()
        args[3].append(args[3][-1])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            evaluate(*args, 25)
        slo, client, gateway, worker = self.fixture()
        del client['sessions'][0]['audio_start_ns']
        self.assertEqual(evaluate(slo, client, gateway, worker, 25)['verdict'], 'fail')

    def test_late_release_cannot_move_deadline(self):
        args = self.fixture()
        for row in args[2]:
            if row['event'] == 'input_release':
                row['time_ns'] += 10_000_000_000
        for row in args[3]:
            if row['event'] == 'compute_complete':
                row['time_ns'] += 10_000_000_000
        self.assertEqual(evaluate(*args, 25)['verdict'], 'fail')

    def test_late_input_arrival_cannot_move_the_offered_horizon(self):
        args = self.fixture()
        for row in args[2]:
            row['time_ns'] += 10_000_000_000
        for row in args[3]:
            row['time_ns'] += 10_000_000_000
        result = evaluate(*args, 25)
        self.assertEqual(result['verdict'], 'fail')
        self.assertEqual(result['frames'],4)
        self.assertEqual(result['misses'],4)
