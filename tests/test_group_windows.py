import unittest
from infra.trace.groups import analyze


class GroupWindowTests(unittest.TestCase):
    def test_volume_cap_and_time_overrun_are_independent(self):
        events = []
        for sid in (1, 2):
            rid = f's{sid}e1'
            events.extend([
                dict(event='admitted', request=rid, plan={'slot':0}),
                dict(event='evicted', request=rid+'-internal', time=1,
                     logical_blocks=[1,2], ceiling_blocks=2, group=0,
                     restore_start_epoch=1.9, restore_end_epoch=2),
                dict(event='queued', direction='H2D', transfer_id=sid,
                     requests=[rid+'-internal'], time=1.91, blocks=2),
                dict(event='published', transfer_id=sid, time=2.01),
            ])
        report = analyze(events)
        self.assertEqual(report['maximum_group_members'], {0:2})
        self.assertEqual(report['cap_violations'], [])
        self.assertEqual(report['late_windows'], 1)
        self.assertEqual(report['windows'][0]['blocks'], 4)
        self.assertTrue(report['windows'][0]['all_members_at_ceiling'])
        self.assertAlmostEqual(report['windows'][0]['publication_lateness_ms'], 10)

    def test_unmatched_and_unpublished_transfers_stay_explicit(self):
        events = [dict(event='queued', direction='H2D',transfer_id=1,requests=['s1e1'],time=1,blocks=3),
                  dict(event='evicted',request='s2e1',time=1,logical_blocks=[1,2,3],ceiling_blocks=2,group=0,
                       restore_start_epoch=1.9,restore_end_epoch=2),
                  dict(event='queued',direction='H2D',transfer_id=2,requests=['s2e1'],time=1.9,blocks=3)]
        report=analyze(events)
        self.assertEqual(report['unmatched_h2d'],[1])
        self.assertEqual(report['unpublished_h2d'],[2])
        self.assertEqual(len(report['cap_violations']),1)
