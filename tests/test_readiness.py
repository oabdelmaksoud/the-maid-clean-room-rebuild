"""Synthetic defect fixtures exercise the public offline readiness gate."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'skills/the-maid-rebuild/scripts/readiness.py'
spec = importlib.util.spec_from_file_location('readiness_fixture', ROOT / 'examples/manus-readiness/run_trial.py')
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixture = fixture_module.Fixture(self.temp.name)
        self.run = self.fixture.run
        self.contract = self.fixture.contract

    def check(self, code=0, issue=None):
        self.fixture.freeze()
        proc = subprocess.run([sys.executable, str(CLI), self.temp.name, '--json'], capture_output=True, text=True)
        result = json.loads(proc.stdout)
        self.assertEqual(proc.returncode, code, result)
        if issue:
            self.assertIn(issue, [item['code'] for item in result['errors']])
        return result

    def test_corrected_reviewed_slice(self):
        self.assertTrue(self.check()['summary']['declared_scope_ready'])

    def test_missing_disabled_state(self):
        del self.contract['requirements'][0]['expected']['control_states']
        self.check(2, 'SHAPE')

    def test_conflicting_expected(self):
        self.run['packets'][0]['expected']['empty-continue']['visible_strings'] = ['Flex setup']
        self.check(1, 'PACKET_CONFLICT')

    def test_mismatched_dpr_and_viewport(self):
        for field, value in [('dpr', 2), ('css_viewport', {'width': 800, 'height': 600})]:
            with self.subTest(field=field):
                old = self.run['slices'][0]['capture'][field]
                self.run['slices'][0]['capture'][field] = value
                self.check(1, 'CAPTURE_MISMATCH')
                self.run['slices'][0]['capture'][field] = old

    def test_unavailable_capability(self):
        self.run['capabilities'][0].update(availability='unavailable', disposition='Access blocked; obtain permitted service access')
        self.check(1, 'CAPABILITY_UNAVAILABLE')

    def test_source_as_feature(self):
        self.contract['sources'][0]['id'] = 'empty-continue'
        self.contract['requirements'][0]['source_ids'] = ['empty-continue']
        self.check(1, 'SOURCE_AS_FEATURE')

    def test_wrong_target_at_resume(self):
        self.run['resume']['target_id'] = 'chess'
        self.check(1, 'TARGET_MISMATCH')

    def test_wrong_target_version(self):
        self.run['target_version'] = 'other-1'
        self.check(1, 'TARGET_MISMATCH')

    def gap(self):
        return dict(id='continue-repair', cause='implementation', status='open', fixable=True,
                    owner='builder', reproduction='View empty login', requirement_ids=['empty-continue'],
                    acceptance='Continue is disabled', next_action='Disable empty Continue',
                    candidate_id='candidate-one', closure=None)

    def test_repair_pending(self):
        self.run['gaps'] = [self.gap()]
        self.run['full_scope_readiness_claim'] = True
        self.check(1, 'REPAIR_PENDING')

    def test_repaired_candidate_independent_rerun(self):
        gap = self.gap()
        self.run['candidate_id'] = 'candidate-two'
        expected = {'empty-continue': copy.deepcopy(self.contract['requirements'][0]['expected'])}
        rerun = self.fixture.ref('rerun.json', json.dumps(dict(candidate_id='candidate-two', requirement_ids=['empty-continue'], expected=expected, actual=expected)).encode())
        gap.update(status='closed', closure=dict(candidate_id='candidate-two', independent_reviewer='verifier', rerun=rerun, evidence=[self.fixture.evidence]))
        self.run.update(gaps=[gap], full_scope_readiness_claim=True)
        self.check()
        gap['closure']['independent_reviewer'] = 'builder'
        self.check(1, 'GAP_CLOSURE')

    def test_backend_provisional_visual_blocked(self):
        self.fixture.backend_provisional()
        summary = self.check()['summary']
        self.assertFalse(summary['declared_scope_ready'])
        self.assertEqual(summary['required_nonready_slice_ids'], ['login-visual'])
        self.run['full_scope_readiness_claim'] = True
        self.check(1, 'FALSE_COMPLETE')

    def test_prose_metadata_oracle_rejected(self):
        self.contract['requirements'][0]['expected'] = {'description': 'Looks like target', 'matches': True}
        self.check(2, 'SHAPE')

    def test_no_fake_ready_requirement(self):
        self.run['slices'][0]['requirements'][0].update(status='blocked', reason='Missing source observation')
        self.check(1, 'REQUIREMENT_NOT_READY')

    def test_missing_required_requirement(self):
        self.run['slices'][0]['requirements'] = []
        self.check(1, 'REQUIREMENT_MAPPING')

    def test_hash_tamper(self):
        self.fixture.freeze()
        (Path(self.temp.name) / 'synthetic-observation.txt').write_text('changed')
        result = fixture_module.validate_readiness(self.temp.name)
        self.assertEqual(result['exit_code'], 2)
        self.assertEqual(result['errors'][0]['code'], 'HASH_MISMATCH')

    def test_visual_requirement_cannot_hide_in_backend(self):
        self.contract['slices'][0].update(kind='backend', capture=None)
        self.run['slices'][0]['capture'] = None
        self.check(1, 'CAPTURE_APPLICABILITY')

    def test_declared_control_missing_state(self):
        self.contract['requirements'][0]['expected']['control_states'] = {}
        self.check(1, 'CONTROL_STATES')

    def test_nonexistent_acceptance_case(self):
        self.contract['requirements'][0]['acceptance_ids'] = ['missing-case']
        self.check(1, 'ACCEPTANCE_MAPPING')

    def test_conflicting_acceptance_definition(self):
        self.contract['acceptance_cases'][0]['expected']['empty-continue']['visible_strings'] = ['Other']
        self.check(1, 'ACCEPTANCE_MAPPING')

    def test_builder_cannot_approve_own_slice(self):
        self.run['slices'][0]['review']['reviewer'] = self.run['task']['owner']
        self.check(1, 'SLICE_NOT_APPROVED')

    def test_metadata_effect_oracle_rejected(self):
        self.contract['requirements'][0]['expected']['persisted_effect'] = {'description': 'Looks good'}
        self.check(1, 'METADATA_ORACLE')

    def test_retained_demo_and_unknown_argument(self):
        demo = ROOT / 'examples/manus-readiness/run_trial.py'
        output = Path(self.temp.name) / 'demo'
        proc = subprocess.run([sys.executable, str(demo), '--output', str(output)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        results = json.loads((output / 'results.json').read_text())
        self.assertEqual([r['exit_code'] for r in results.values()], [1, 0, 0, 1])
        for name in ('flawed', 'corrected', 'backend', 'full-scope'):
            self.assertTrue((output / name / 'readiness.json').is_file())
        proc = subprocess.run([sys.executable, str(demo), '--unknown'], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        proc = subprocess.run([sys.executable, str(demo), '--output', str(output)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)

    def test_unknown_fields_rejected(self):
        self.contract['requirements'][0]['implementation_note'] = 'shortcut'
        self.check(2, 'SHAPE')

    def test_duplicate_packet_mapping(self):
        duplicate = copy.deepcopy(self.run['packets'][0])
        duplicate['id'] = 'other-packet'
        self.run['packets'].append(duplicate)
        self.check(1, 'PACKET_MAPPING')

    def test_blocked_slice_needs_concrete_blocker(self):
        self.fixture.backend_provisional()
        self.run['slices'][0]['blocker']['next_action'] = ''
        self.check(2, 'TEXT')


if __name__ == '__main__':
    unittest.main()
