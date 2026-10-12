"""Contract tests exercise evidence gates through the public offline CLI."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/behavior-rebuild/scripts/validate.py'
REPORT = ROOT / 'skills/behavior-rebuild/scripts/report.py'
DEMO = ROOT / 'examples/delimited-notebook/run_demo.py'


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'generated'
        subprocess.run([sys.executable, str(DEMO), '--output', str(self.root)], check=True, capture_output=True)
        self.project = json.loads((self.root / 'project.json').read_text())
        self.run = json.loads((self.root / 'runs/demo.json').read_text())

    def save(self, bind=True):
        (self.root / 'project.json').write_text(json.dumps(self.project))
        if bind:
            self.run['manifest_sha256'] = hashlib.sha256((self.root / 'project.json').read_bytes()).hexdigest()
        (self.root / 'runs/demo.json').write_text(json.dumps(self.run))

    def invoke(self, stage='acceptance', script=SCRIPT, explicit=True):
        args = [sys.executable, str(script), str(self.root), '--json']
        if script == SCRIPT:
            args += ['--stage', stage]
        if explicit:
            args += ['--run', 'runs/demo.json', '--candidate', 'demo-v1']
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertNotIn('Traceback', result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, payload['exit_code'])
        self.assertEqual(payload['ok'], result.returncode == 0)
        return result.returncode, payload

    def test_demo_and_read_only(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(self.invoke()[0], 0)
        self.assertEqual(self.invoke(script=REPORT)[0], 0)
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_relocated_skill_install(self):
        installed = Path(self.temp.name) / 'portable skill'
        shutil.copytree(ROOT / 'skills/behavior-rebuild', installed, ignore=shutil.ignore_patterns('__pycache__'))
        command = [sys.executable, str(installed / 'scripts/validate.py'), str(self.root),
                   '--stage', 'acceptance', '--run', 'runs/demo.json', '--candidate', 'demo-v1', '--json']
        result = subprocess.run(command, cwd=self.temp.name, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(json.loads(result.stdout)['ok'])

    def test_empty_template_blocks(self):
        shutil.rmtree(self.root)
        self.root.mkdir()
        shutil.copyfile(ROOT / 'skills/behavior-rebuild/assets/templates/project.json', self.root / 'project.json')
        code, payload = self.invoke('discover', explicit=False)
        self.assertEqual(code, 1)
        self.assertIn('EMPTY_SCOPE', [e['code'] for e in payload['errors']])

    def test_requires_explicit_run(self):
        self.assertNotEqual(self.invoke(explicit=False)[0], 0)

    def test_stale_manifest(self):
        self.project['title'] += ' changed'
        self.save(bind=False)
        self.assertNotEqual(self.invoke()[0], 0)

    def test_wrong_candidate(self):
        self.run['candidate_id'] = 'another-version'
        self.save()
        self.assertNotEqual(self.invoke()[0], 0)

    def test_missing_trial(self):
        self.run['evaluations'].pop()
        self.save()
        self.assertEqual(self.invoke()[0], 1)

    def test_missing_oracle(self):
        self.run['evaluations'][0]['oracle_status'] = 'missing'
        self.save()
        self.assertNotEqual(self.invoke()[0], 0)

    def test_tampered_result(self):
        (self.root / 'results/valid-export.json').write_text('{}')
        self.assertEqual(self.invoke()[0], 2)

    def test_exact_type_distinction(self):
        self.project['cases'][1]['oracle']['expected']['rejected'] = 1
        self.save()
        self.assertEqual(self.invoke()[0], 1)

    def test_missing_fixture(self):
        (self.root / 'packet/fixtures/valid.csv').unlink()
        self.assertEqual(self.invoke()[0], 2)

    def test_hidden_extra_packet_file(self):
        (self.root / 'packet/.unlisted').write_text('unreviewed')
        self.assertNotEqual(self.invoke()[0], 0)

    def test_duplicate_case(self):
        self.project['cases'].append(self.project['cases'][0])
        self.save()
        self.assertEqual(self.invoke()[0], 2)

    def test_duplicate_trial(self):
        self.run['evaluations'].append(self.run['evaluations'][0])
        self.save()
        self.assertEqual(self.invoke()[0], 2)

    def test_unknown_field_and_boolean_integer(self):
        for mutate in [lambda p: p.update(unexpected='x'), lambda p: p['cases'][0].update(required_trials=True)]:
            with self.subTest(mutation=mutate):
                original = json.loads(json.dumps(self.project))
                mutate(self.project)
                self.save()
                self.assertEqual(self.invoke()[0], 2)
                self.project = original

    def test_strict_json(self):
        for content in ['{"format_version":1,"format_version":1}', '{"x":NaN}', '[' * 50 + '0' + ']' * 50, '{"x":"' + 'a' * (1024 * 1024) + '"}']:
            with self.subTest(length=len(content)):
                (self.root / 'project.json').write_text(content)
                self.assertEqual(self.invoke()[0], 2)

    def test_path_traversal(self):
        for path in ['../outside.csv', '/absolute.csv', 'packet\\file.csv', 'packet//file.csv', 'packet/./file.csv', 'C:/file.csv']:
            with self.subTest(path=path):
                self.project['cases'][0]['fixtures'][0]['path'] = path
                self.save()
                self.assertEqual(self.invoke()[0], 2)

    def test_symlink(self):
        fixture = self.root / 'packet/fixtures/valid.csv'
        outside = Path(self.temp.name) / 'outside.csv'
        shutil.copyfile(fixture, outside)
        fixture.unlink()
        try:
            fixture.symlink_to(outside)
        except OSError:
            # Windows CI without symlink privilege still exercises a directory-as-file attack.
            fixture.mkdir()
        self.assertEqual(self.invoke()[0], 2)

    def test_exclusion_not_vacuous(self):
        self.project['exclusions'] = [{'case_id': c['id'], 'reason': 'Explicit teaching exclusion', 'approved_by': 'test-reviewer'} for c in self.project['cases']]
        self.run['evaluations'] = []
        self.save()
        self.assertEqual(self.invoke()[0], 1)

    def test_optional_skip_not_approved(self):
        self.project['cases'][0]['required'] = False
        self.run['evaluations'][0]['status'] = 'skip'
        self.save()
        self.assertNotEqual(self.invoke()[0], 0)

    def test_open_blocker(self):
        self.project['gaps'] = [{'id': 'blocker', 'case_ids': [], 'severity': 'blocker', 'impact': 5, 'recovery_action': 'Resolve before acceptance.', 'status': 'open'}]
        self.save()
        self.assertEqual(self.invoke()[0], 1)
        self.project['gaps'][0]['status'] = 'closed'
        self.save()
        self.assertEqual(self.invoke()[0], 0)

    def test_manual_review_requires_evidence(self):
        self.project['cases'][0]['oracle'] = {'kind': 'manual_review', 'description': 'Review actual export', 'expected': None}
        self.run['evaluations'][0]['result'] = None
        self.save()
        self.assertEqual(self.invoke()[0], 0)
        self.run['evaluations'][0]['evidence'] = []
        self.save()
        self.assertNotEqual(self.invoke()[0], 0)

    def test_permission_unknown_blocks_handoff(self):
        self.project['sources'] = [{'id': 'public-note', 'kind': 'D', 'locator': 'https://example.invalid/synthetic',
            'captured_on': '2026-10-11', 'description': 'Synthetic permission test metadata; never fetched.',
            'permission': {'observe': 'unknown', 'handoff': 'unknown', 'publish': 'unknown',
                           'basis': 'Permission not reviewed.', 'reviewer': ''}, 'evidence': []}]
        self.project['cases'][0].update(origin='documented', source_ids=['public-note'])
        self.save()
        code, result = self.invoke('discover', explicit=False)
        self.assertEqual(code, 0)
        self.assertTrue(result['warnings'])
        self.assertEqual(self.invoke('handoff', explicit=False)[0], 1)

    def test_report_counts_and_gap_order(self):
        self.project['gaps'] = [{'id': name, 'case_ids': [], 'severity': severity, 'impact': impact,
            'recovery_action': 'Original fixture exercise.', 'status': 'closed'}
            for name, severity, impact in [('minor', 'low', 5), ('high-small', 'high', 1),
                                            ('high-large', 'high', 5), ('urgent', 'blocker', 1)]]
        self.save()
        code, report = self.invoke(script=REPORT)
        self.assertEqual(code, 0)
        summary = report['summary']
        self.assertEqual(summary['total_cases'], 2)
        self.assertEqual(summary['required_active_cases'], 2)
        self.assertEqual(summary['required_trials'], 2)
        self.assertEqual(summary['recorded_status_counts']['pass'], 2)
        self.assertEqual(summary['untested_trials'], [])
        self.assertEqual([g['id'] for g in summary['gaps']], ['urgent', 'high-large', 'high-small', 'minor'])

    def test_optional_and_excluded_passes_need_valid_evidence(self):
        baseline_project = json.loads(json.dumps(self.project))
        baseline_run = json.loads(json.dumps(self.run))
        for scope in ['optional', 'excluded']:
            for defect in ['missing-result', 'empty-reviewer', 'pending-review', 'empty-review-notes', 'mismatch', 'manual-no-evidence']:
                with self.subTest(scope=scope, defect=defect):
                    self.project = json.loads(json.dumps(baseline_project))
                    self.run = json.loads(json.dumps(baseline_run))
                    case, evaluation = self.project['cases'][0], self.run['evaluations'][0]
                    if scope == 'optional':
                        case['required'] = False
                    else:
                        self.project['exclusions'] = [{'case_id': case['id'], 'reason': 'Explicit test scope', 'approved_by': 'fixture-reviewer'}]
                    if defect == 'missing-result':
                        evaluation['result'] = None
                    elif defect == 'empty-reviewer':
                        evaluation['review']['reviewer'] = ''
                    elif defect == 'pending-review':
                        evaluation['review']['decision'] = 'pending'
                    elif defect == 'empty-review-notes':
                        evaluation['review']['notes'] = ''
                    elif defect == 'mismatch':
                        case['oracle']['expected'] = {'different': 'outcome'}
                    elif defect == 'manual-no-evidence':
                        case['oracle'] = {'kind': 'manual_review', 'description': 'Review output', 'expected': None}
                        evaluation['result'] = None
                        evaluation['evidence'] = []
                    self.save()
                    self.assertNotEqual(self.invoke()[0], 0)

    def test_honest_optional_failure_does_not_block(self):
        self.project['cases'][0]['required'] = False
        self.run['evaluations'][0].update(status='failed', result=None, evidence=[],
            review={'reviewer': '', 'decision': 'pending', 'notes': ''}, notes='Optional feature failed during an honest trial.')
        self.save()
        self.assertEqual(self.invoke()[0], 0)

    def test_exact_decimal_precision_and_type(self):
        for expected, actual, passes in [
            ('9007199254740992.0', '9007199254740993.0', False),
            ('1e-9999', '2e-9999', False),
            ('0.0', '1e-9999', False),
            ('1.00', '1e0', True),
            ('1', '1.0', False),
            ('true', '1.0', False),
        ]:
            with self.subTest(expected=expected, actual=actual):
                self.project['cases'][0]['oracle']['expected'] = 'RAW-NUMBER-SENTINEL'
                raw_project = json.dumps(self.project).replace('"RAW-NUMBER-SENTINEL"', expected)
                (self.root / 'project.json').write_text(raw_project)
                result_path = self.root / 'results/valid-export.json'
                result_path.write_text(actual)
                self.run['evaluations'][0]['result']['sha256'] = hashlib.sha256(result_path.read_bytes()).hexdigest()
                self.run['manifest_sha256'] = hashlib.sha256((self.root / 'project.json').read_bytes()).hexdigest()
                (self.root / 'runs/demo.json').write_text(json.dumps(self.run))
                self.assertEqual(self.invoke()[0], 0 if passes else 1)

    def test_digest_symlink_loop_is_structured_error(self):
        loop = Path(self.temp.name) / 'loop'
        try:
            loop.symlink_to(loop, target_is_directory=True)
        except OSError:
            # Still test a malformed root on hosts without symlink permission.
            loop.write_text('not a project directory')
        result = subprocess.run([sys.executable, str(SCRIPT), str(loop), '--digest', '--json'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(json.loads(result.stdout)['exit_code'], 2)

    def test_human_output_escapes_hostile_path(self):
        self.project['cases'][0]['fixtures'][0]['path'] = 'packet/hostile-' + chr(27) + '[2J.csv'
        self.save()
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.root), '--stage', 'discover'],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(chr(27), result.stdout + result.stderr)

    def test_review_pending(self):
        self.run['evaluations'][0]['review']['decision'] = 'pending'
        self.save()
        self.assertNotEqual(self.invoke()[0], 0)

    def test_recorded_commands_never_executed(self):
        sentinel = Path(self.temp.name) / 'must-not-exist'
        self.project['cases'][0]['steps'] = [f'python -c "open({str(sentinel)!r}, chr(119)).write(chr(120))"']
        self.save()
        self.assertEqual(self.invoke()[0], 0)
        self.assertFalse(sentinel.exists())


if __name__ == '__main__':
    unittest.main()
