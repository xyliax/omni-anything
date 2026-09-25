import json
from pathlib import Path
import tempfile
import unittest
import wave

from experiments.conveyor.schedule import audio_asset, generate_schedule, main


class ArrivalScheduleTests(unittest.TestCase):
    def configuration(self, **changes):
        return dict(seed=31, arrival_rate=2, duration_s=4, arrival_window_s=12,
                    period_s=1, assets=[dict(input_stream_id='sha256:a', sha256='a',
                        path='/input.wav', sample_rate=16000, samples=160000)], **changes)

    def test_paired_schedule_preserves_fractional_clock_and_material(self):
        config = self.configuration()
        first = generate_schedule(**config)
        self.assertEqual(first, generate_schedule(**config))
        rows = first['sessions']
        self.assertGreater(len(rows), 2)
        starts = [row['start_time_s'] for row in rows]
        self.assertEqual(starts, sorted(set(starts)))
        self.assertTrue(all(0 < value < 12 for value in starts))
        self.assertTrue(any(value % 1 for value in starts))
        self.assertTrue(all('phase' not in row and 'admitted' not in row for row in rows))
        self.assertGreater(len({row['input_offset'] for row in rows}), 1)
        self.assertTrue(all(row['input_offset'] + 64000 <= 160000 for row in rows))
        higher = generate_schedule(**{**config, 'arrival_rate': 4})
        for a, b in zip(rows, higher['sessions']):
            self.assertEqual((a['input_stream_id'], a['input_offset']),
                             (b['input_stream_id'], b['input_offset']))

    def test_material_selection_does_not_move_arrivals(self):
        config = self.configuration()
        initial = generate_schedule(**config)
        more = generate_schedule(**{**config, 'assets': [*config['assets'],
            dict(input_stream_id='sha256:b', sha256='b', path='/second.wav',
                 sample_rate=16000, samples=320000)]})
        self.assertEqual([s['start_time_s'] for s in initial['sessions']],
                         [s['start_time_s'] for s in more['sessions']])
        self.assertEqual(more, generate_schedule(**{**config, 'assets': list(reversed(more['assets']))}))

    def test_invalid_protocol_and_short_sources_are_rejected(self):
        config = self.configuration()
        for changes in ({'arrival_rate': float('nan')}, {'period_s': 0},
                        {'arrival_window_s': 7}, {'duration_s': 4.000001},
                        {'assets': []}, {'assets': config['assets'] * 2},
                        {'assets': [{**config['assets'][0], 'samples': 10}]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                generate_schedule(**{**config, **changes})

    def test_cli_locks_source_identity_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / 'input.wav'
            with wave.open(str(audio), 'wb') as stream:
                stream.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                stream.writeframes(b'\x01\x00' * 64000)
            asset = audio_asset(audio)
            output = Path(directory) / 'schedule.json'
            args = ['--seed', '17', '--arrival-rate', '2', '--session-duration', '1',
                    '--arrival-window', '3', '--period', '1', '--audio', str(audio),
                    '--output', str(output)]
            self.assertEqual(main(args), 0)
            self.assertEqual(json.loads(output.read_text())['assets'], [asset])
            original = output.read_bytes()
            with self.assertRaises(FileExistsError):
                main(args)
            self.assertEqual(output.read_bytes(), original)
            audio.write_bytes(audio.read_bytes()[:-2])
            with self.assertRaisesRegex(ValueError, 'truncated'):
                audio_asset(audio)
