"""Offline REA gate integrity, boundary and reviewed handoff regressions."""
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'skills/the-maid-rebuild/scripts/rea.py'
spec = importlib.util.spec_from_file_location('rea_trial', ROOT / 'examples/rea-observation/run_trial.py')
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)


class ReaTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.fixture = trial.Fixture(temp.name)
        self.record = self.fixture.record

    def check(self, code=0, error=None):
        self.fixture.freeze()
        proc = subprocess.run([sys.executable, str(CLI), str(self.fixture.root), '--json'], capture_output=True, text=True)
        payload = json.loads(proc.stdout)
        self.assertEqual(proc.returncode, code, payload)
        self.assertEqual(payload['exit_code'], code)
        self.assertEqual(payload['ok'], code == 0)
        if error:
            self.assertIn(error, [e['code'] for e in payload['errors']])
        return payload

    def test_reviewed_behavior(self):
        self.assertEqual(self.check()['summary']['approved_handoff_observation_ids'], ['continue-state'])

    def test_hash(self):
        self.record['captures'][0]['artifact']['sha256'] = '0' * 64
        self.check(2, 'HASH_MISMATCH')

    def test_traversal(self):
        self.record['captures'][0]['artifact']['path'] = '../capture.png'
        self.check(2, 'UNSAFE_PATH')

    def test_symlink(self):
        target = self.fixture.root / 'evaluator/capture.png'
        alias = self.fixture.root / 'alias.png'
        alias.symlink_to(target)
        self.record['captures'][0]['artifact']['path'] = 'alias.png'
        self.check(2, 'SYMLINK')

    def test_unreviewed(self):
        self.record['observations'][0]['review']['disposition'] = 'unreviewed'
        self.check(1, 'OBSERVATION_UNREVIEWED')

    def test_excluded_handoff(self):
        self.record['observations'][0]['review']['disposition'] = 'excluded'
        self.check(1, 'HANDOFF_DISPOSITION')

    def test_not_sanitized(self):
        self.record['observations'][0]['review']['sanitized'] = False
        self.check(1, 'NOT_SANITIZED')

    def test_wrong_target(self):
        self.record['captures'][0]['target_id'] = 'different'
        self.check(1, 'TARGET_MISMATCH')

    def test_wrong_behavior_identity(self):
        artifact = self.record['observations'][0]['artifact']
        data = json.loads((self.fixture.root / artifact['path']).read_text())
        data['target_id'] = 'different'
        new = self.fixture.ref(artifact['path'], json.dumps(data).encode())
        self.record['observations'][0]['artifact'] = new
        self.record['handoff']['files'] = [new]
        self.check(1, 'TARGET_MISMATCH')

    def test_unsafe_origins(self):
        for value in ('https://synthetic.example/', 'https://synthetic.example?token=x', 'https://u:p@synthetic.example',
                      'http://synthetic.example', 'https://synthetic.example#x', 'https://synthetic.example?', '\nhttps://synthetic.example'):
            with self.subTest(value=value):
                self.record['target']['origin'] = value
                self.check(2, 'UNSAFE_ORIGIN')

    def test_local_and_explicit_port_origins(self):
        for value in ('http://localhost:8123', 'http://127.0.0.1:8123', 'http://[::1]:8123',
                      'http://localhost', 'https://synthetic.example:443', 'https://synthetic.example:8443'):
            with self.subTest(value=value):
                self.record['target']['origin'] = value
                self.record['target']['allowed_origins'] = [value]
                self.record['captures'][0]['origin'] = value
                self.check()

    def test_ports_and_nonlocal_http_rejected(self):
        for value in ('http://example.com:8123', 'http://127.0.0.2:8123', 'https://synthetic.example:0',
                      'https://synthetic.example:65536', 'https://synthetic.example:',
                      'https://synthetic.example:0443', 'http://[::1]:0', 'http://LOCALHOST:8123'):
            with self.subTest(value=value):
                self.record['target']['origin'] = value
                self.check(2, 'UNSAFE_ORIGIN')

    def test_default_ports_preserved_without_normalization(self):
        self.record['target']['origin'] = 'https://synthetic.example:443'
        self.record['target']['allowed_origins'] = ['https://synthetic.example:443']
        self.record['captures'][0]['origin'] = 'https://synthetic.example:443'
        self.check()
        self.record['captures'][0]['origin'] = 'https://synthetic.example'
        self.check(1, 'TARGET_MISMATCH')
        self.record['target']['allowed_origins'] = ['https://synthetic.example']
        self.check(1, 'ORIGIN_NOT_ALLOWED')

    def test_allowlist(self):
        self.record['target']['allowed_origins'] = ['https://other.example']
        self.check(1, 'ORIGIN_NOT_ALLOWED')

    def test_source_operations(self):
        for value in ('inspect_web_page', 'analyze_web_bundle', 'compare_web_screenshots'):
            with self.subTest(value=value):
                self.record['tool']['operation'] = value
                self.check(1, 'TOOL_BOUNDARY')

    def test_unknown_operation_invalid(self):
        self.record['tool']['operation'] = 'fetch_credentials'
        self.check(2, 'ENUM')

    def test_version(self):
        self.record['tool']['version'] = '7.0.0'
        self.check(1, 'TOOL_BOUNDARY')

    def test_source_boundary(self):
        self.record['permission']['source_boundary'] = 'code'
        self.check(1, 'SOURCE_BOUNDARY')

    def test_no_permission(self):
        self.record['permission']['observe'] = 'unknown'
        self.check(1, 'OBSERVATION_PERMISSION')

    def test_screenshot_handoff(self):
        self.record['handoff']['files'].append(self.record['captures'][0]['artifact'])
        self.check(1, 'CAPTURE_HANDOFF')

    def test_renamed_screenshot_handoff(self):
        raw = (self.fixture.root / 'evaluator/capture.png').read_bytes()
        self.record['handoff']['files'].append(self.fixture.ref('behavior/renamed.txt', raw))
        self.check(1, 'CAPTURE_HANDOFF')

    def test_extra_raw_asset(self):
        self.record['handoff']['files'].append(self.fixture.ref('behavior/asset.txt', b'arbitrary copied asset'))
        self.check(1, 'HANDOFF_FILE_SET')

    def test_png_header(self):
        self.record['captures'][0]['artifact'] = self.fixture.ref('evaluator/capture.png', b'not PNG')
        self.check(2, 'PNG_HEADER')

    def test_png_bounds(self):
        raw = bytearray(trial.synthetic_png())
        raw[16:20] = struct.pack('>I', 8193)
        raw[29:33] = struct.pack('>I', zlib.crc32(raw[12:29]) & 0xffffffff)
        self.record['captures'][0]['artifact'] = self.fixture.ref('evaluator/capture.png', raw)
        self.check(2, 'PNG_BOUNDS')

    def test_png_dimensions(self):
        self.record['captures'][0]['width'] = 3
        self.check(2, 'PNG_DIMENSIONS')

    def test_strict_types(self):
        self.record['captures'][0]['width'] = True
        self.check(2, 'INTEGER')

    def test_exact_shape(self):
        self.record['tool']['credentials'] = 'not-real'
        self.check(2, 'SHAPE')

    def test_duplicate_json_key(self):
        self.fixture.freeze()
        path = self.fixture.root / 'rea-evidence.json'
        path.write_text(path.read_text().replace('"format_version": 1', '"format_version": 1, "format_version": 1', 1))
        result = trial.validate_rea(self.fixture.root)
        self.assertEqual(result['exit_code'], 2)
        self.assertEqual(result['errors'][0]['code'], 'DUPLICATE_KEY')

    def test_synthetic_demo(self):
        proc = subprocess.run([sys.executable, str(ROOT / 'examples/rea-observation/run_trial.py')], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertFalse(json.loads(proc.stdout)['actual_rea_execution'])

    def test_demo_preserves_trial_records(self):
        destination = self.fixture.root / 'new-demo'
        proc = subprocess.run([sys.executable, str(ROOT / 'examples/rea-observation/run_trial.py'),
                               '--output', str(destination)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads((destination / 'results.json').read_text()), json.loads(proc.stdout))
        for label, code in [('source-operation', 1), ('capture-handoff', 1), ('reviewed-behavior', 0)]:
            with self.subTest(label=label):
                self.assertTrue((destination / label / 'rea-evidence.json').is_file())
                self.assertEqual(trial.validate_rea(destination / label)['exit_code'], code)

    def test_demo_refuses_existing_output(self):
        marker = self.fixture.root / 'keep.txt'
        marker.write_text('Preserve existing evidence')
        proc = subprocess.run([sys.executable, str(ROOT / 'examples/rea-observation/run_trial.py'),
                               '--output', str(self.fixture.root)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(marker.read_text(), 'Preserve existing evidence')
        self.assertFalse((self.fixture.root / 'results.json').exists())

    def test_demo_refuses_symlink_output(self):
        alias = self.fixture.root / 'alias-output'
        alias.symlink_to(self.fixture.root, target_is_directory=True)
        proc = subprocess.run([sys.executable, str(ROOT / 'examples/rea-observation/run_trial.py'),
                               '--output', str(alias)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertFalse((self.fixture.root / 'results.json').exists())


if __name__ == '__main__':
    unittest.main()
