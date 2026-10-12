"""Exercise visual and journey evidence through the public acceptance CLI."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UIOracleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        subprocess.run([sys.executable, str(ROOT / 'examples/delimited-notebook/run_demo.py'),
                        '--output', str(self.root)], check=True, capture_output=True)
        self.project = json.loads((self.root / 'project.json').read_text())
        self.run = json.loads((self.root / 'runs/demo.json').read_text())
        self.case = self.project['cases'][0]
        self.ev = next(e for e in self.run['evaluations'] if e['case_id'] == self.case['id'])

    def reference(self, name, raw):
        (self.root / name).write_bytes(raw)
        return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}

    def check(self, code=0, error=None, stage='acceptance'):
        manifest = json.dumps(self.project).encode()
        (self.root / 'project.json').write_bytes(manifest)
        self.run['manifest_sha256'] = hashlib.sha256(manifest).hexdigest()
        (self.root / 'runs/demo.json').write_text(json.dumps(self.run))
        result = subprocess.run([sys.executable, str(ROOT / 'skills/behavior-rebuild/scripts/validate.py'),
                                 str(self.root), '--stage', stage, '--run', 'runs/demo.json',
                                 '--candidate', 'demo-v1', '--json'], capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, code, payload)
        if error:
            self.assertIn(error, [e['code'] for e in payload['errors']])

    def journey(self):
        expected = {'steps': [
            {'id': 'open', 'action': 'Open list', 'state': {'count': 0, 'ready': True}},
            {'id': 'add', 'action': 'Add item', 'state': {'count': 1, 'ready': True}},
        ]}
        self.case['oracle'] = {'kind': 'journey_trace', 'description': 'Observed state after each action', 'expected': expected}
        self.trace(expected)
        return expected

    def trace(self, value):
        self.ev['result'] = self.reference('results/journey.json', json.dumps(value).encode())

    def visual(self):
        raw = b'P6\n2 1\n255\n' + bytes([0, 10, 20, 30, 40, 50])
        self.case['oracle'] = {'kind': 'visual_pixels', 'description': 'Frozen RGB region', 'expected': {
            'baseline': self.reference('results/baseline.ppm', raw), 'width': 2, 'height': 1,
            'max_channel_delta': 0, 'max_changed_pixels': 0}}
        self.ev['result'] = self.reference('results/actual.ppm', raw)
        return raw

    def test_journey_matches(self):
        self.journey()
        self.check()

    def test_journey_missing_reordered_extra_wrong_action(self):
        expected = self.journey()
        variants = [expected['steps'][:1], expected['steps'][::-1], expected['steps'] + [
            {'id': 'extra', 'action': 'Extra action', 'state': {'count': 1}}],
            [dict(expected['steps'][0], action='Different action'), expected['steps'][1]]]
        for steps in variants:
            with self.subTest(steps=steps):
                self.trace({'steps': steps})
                self.check(1, 'ORACLE_MISMATCH')

    def test_journey_boolean_integer_decimal_are_distinct(self):
        expected = self.journey()
        for value in (1, 1.0):
            with self.subTest(value=value):
                altered = json.loads(json.dumps(expected))
                altered['steps'][0]['state']['ready'] = value
                self.trace(altered)
                self.check(1, 'ORACLE_MISMATCH')

    def test_journey_rejects_claimed_pass_empty_duplicate_and_empty_state(self):
        expected = self.journey()
        for value, error in [({'pass': True}, 'SHAPE'), ({'steps': []}, 'JOURNEY_EMPTY'),
                             ({'steps': [expected['steps'][0]] * 2}, 'JOURNEY_DUPLICATE'),
                             ({'steps': [{'id': 'open', 'action': 'Open', 'state': {}}]}, 'JOURNEY_STATE')]:
            with self.subTest(error=error):
                self.trace(value)
                self.check(2, error)

    def test_journey_expected_validated_before_acceptance(self):
        self.journey()['steps'] = []
        self.check(2, 'JOURNEY_EMPTY', 'discover')

    def test_visual_matches_and_channel_and_pixel_thresholds(self):
        raw = self.visual()
        self.check()
        self.ev['result'] = self.reference('results/actual.ppm', raw[:-1] + bytes([53]))
        self.check(1, 'ORACLE_MISMATCH')
        self.case['oracle']['expected']['max_channel_delta'] = 3
        self.check()
        self.case['oracle']['expected']['max_channel_delta'] = 2
        self.check(1, 'ORACLE_MISMATCH')
        self.case['oracle']['expected']['max_changed_pixels'] = 1
        self.check()
        self.ev['result'] = self.reference('results/actual.ppm', raw[:-6] + bytes([3, 10, 20, 30, 40, 53]))
        self.check(1, 'ORACLE_MISMATCH')

    def test_visual_actual_dimensions_mismatch(self):
        raw = self.visual()
        self.ev['result'] = self.reference('results/actual.ppm', raw.replace(b'2 1', b'1 2'))
        self.check(1, 'ORACLE_MISMATCH')

    def test_visual_bad_format_and_raster_are_rejected(self):
        raw = self.visual()
        for altered, error in [(b'{"pass":true}', 'VISUAL_FORMAT'), (raw[:-1], 'VISUAL_RASTER'),
                               (raw + b'\x00', 'VISUAL_RASTER'), (raw.replace(b'255', b'256'), 'VISUAL_FORMAT'),
                               (b'P6\n# comment\n2 1\n255\n' + raw[-6:], 'VISUAL_FORMAT')]:
            with self.subTest(error=error, altered=altered):
                self.ev['result'] = self.reference('results/actual.ppm', altered)
                self.check(2, error)

    def test_visual_preserves_whitespace_raster_bytes(self):
        self.visual()
        raw = b'P6\n2 1\n255\n' + b'\n\r\t \x00\xff'
        self.case['oracle']['expected']['baseline'] = self.reference('results/baseline.ppm', raw)
        self.ev['result'] = self.reference('results/actual.ppm', raw)
        self.check()

    def test_visual_bounds_and_nonvacuous_thresholds(self):
        self.visual()
        expected = self.case['oracle']['expected']
        for key, value, error in [('width', 4097, 'INTEGER'), ('width', True, 'INTEGER'),
                                  ('max_channel_delta', 255, 'INTEGER'), ('max_channel_delta', -1, 'INTEGER'),
                                  ('max_changed_pixels', 2, 'INTEGER'), ('max_changed_pixels', True, 'INTEGER')]:
            with self.subTest(key=key, value=value):
                original = expected[key]
                expected[key] = value
                self.check(2, error)
                expected[key] = original
        self.ev['result'] = self.reference('results/actual.ppm', b'P6\n4096 4096\n255\n')
        self.check(2, 'VISUAL_SIZE')

    def test_visual_baseline_shape_and_hash_checked_early(self):
        raw = self.visual()
        self.case['oracle']['expected']['width'] = 3
        self.check(2, 'VISUAL_DIMENSIONS', 'discover')
        self.case['oracle']['expected']['width'] = 2
        (self.root / 'results/baseline.ppm').write_bytes(raw[:-1] + b'\x00')
        self.check(2, 'HASH_MISMATCH', 'discover')

    def test_visual_baseline_symlink_rejected(self):
        self.visual()
        link = self.root / 'results/link.ppm'
        try:
            link.symlink_to('baseline.ppm')
        except OSError:
            self.skipTest('Symlink creation unavailable on this platform')
        self.case['oracle']['expected']['baseline']['path'] = 'results/link.ppm'
        self.check(2, 'SYMLINK')

    def test_optional_claimed_pass_still_recomputed(self):
        for kind in ('journey', 'visual'):
            with self.subTest(kind=kind):
                if kind == 'journey':
                    expected = self.journey()
                    self.trace({'steps': expected['steps'][:1]})
                else:
                    raw = self.visual()
                    self.ev['result'] = self.reference('results/actual.ppm', raw[:-1] + b'\x00')
                self.case['required'] = False
                self.check(1, 'ORACLE_MISMATCH')

    def test_visual_reused_images_still_consume_comparison_budget(self):
        self.visual()
        raw = b'P6\n1000 1000\n255\n' + bytes(3_000_000)
        self.case['oracle']['expected'].update(width=1000, height=1000,
            baseline=self.reference('results/baseline.ppm', raw))
        self.ev['result'] = self.reference('results/actual.ppm', raw[:21] + b'\xff' + raw[22:])
        for i in range(16):
            case, ev = copy.deepcopy(self.case), copy.deepcopy(self.ev)
            case['id'] = ev['case_id'] = f'visual-{i}'
            self.project['cases'].append(case)
            self.run['evaluations'].append(ev)
        self.check(2, 'VISUAL_BUDGET')

    def test_actual_hash_and_missing_evidence(self):
        self.visual()
        (self.root / 'results/actual.ppm').write_bytes(b'altered')
        self.check(2, 'HASH_MISMATCH')
        self.ev['result'] = None
        self.check(1, 'RESULT_MISSING')


if __name__ == '__main__':
    unittest.main()
