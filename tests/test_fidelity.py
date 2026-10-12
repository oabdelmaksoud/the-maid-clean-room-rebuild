"""Request, inventory, runtime and outcome binding via the public fidelity CLI."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'skills/the-maid-rebuild/scripts/fidelity.py'


class FidelityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.evidence = self.ref('observed.txt', b'Target synthetic observation')
        self.candidate = self.ref('candidate.txt', b'Candidate v1 native execution trace')
        request = 'Reimplement the target faithfully on its native platform.'
        self.contract = dict(format_version=1, objective='faithful_reimplementation',
            user_request=request, request_evidence=self.ref('request.txt', request.encode()),
            intent_review=dict(reviewer='intent-reviewer', approved=True, evidence=[self.evidence]),
            target=dict(name='Synthetic target', version='1.0', platform='macos', runtime='native', evidence=[self.evidence]),
            surfaces=[dict(id='main-window', description='Window controls', evidence=[self.evidence], feature_ids=['add-item', 'window-layout'])],
            completeness=dict(reviewer='inventory-reviewer', reviewed=True, evidence=[self.evidence]),
            features=[self.feature('add-item', 'behavior'), self.feature('window-layout', 'visual')],
            cases=[dict(id='case-' + name, feature_ids=[name], expected={'matches': True}) for name in ['add-item', 'window-layout']])
        self.evaluation = dict(format_version=1, contract={}, objective='faithful_reimplementation',
            candidate=dict(id='candidate-v1', platform='macos', runtime='native', evidence=[self.candidate]),
            cases=[dict(id=c['id'], feature_ids=c['feature_ids'], candidate_id='candidate-v1', status='pass', evidence=[self.candidate], result=self.outcome(c['id'], {'matches': True})) for c in self.contract['cases']],
            features=[dict(id=f['id'], status='match', candidate_id='candidate-v1', candidate_evidence=[self.candidate], case_ids=f['case_ids'], baseline_origin='target' if f['dimension'] == 'visual' else 'not_applicable', deviation=None) for f in self.contract['features']])
        self.freeze()

    def feature(self, name, dimension):
        return dict(id=name, dimension=dimension, critical=True, description='Frozen ' + name,
                    surface_ids=['main-window'], case_ids=['case-' + name], target_evidence=[self.evidence])

    def ref(self, name, data):
        (self.root / name).write_bytes(data)
        return dict(path=name, sha256=hashlib.sha256(data).hexdigest())

    def outcome(self, case, actual, candidate='candidate-v1'):
        return self.ref(case + '.json', json.dumps(dict(case_id=case, candidate_id=candidate, actual=actual)).encode())

    def freeze(self):
        self.evaluation['contract'] = self.ref('fidelity-contract.json', json.dumps(self.contract).encode())

    def check(self, code=0, error=None):
        (self.root / 'fidelity.json').write_text(json.dumps(self.evaluation))
        proc = subprocess.run([sys.executable, str(CLI), str(self.root), '--json'], text=True, capture_output=True)
        payload = json.loads(proc.stdout)
        self.assertEqual(proc.returncode, code, payload)
        self.assertEqual(payload['exit_code'], code)
        self.assertEqual(payload['ok'], code == 0)
        if error:
            self.assertIn(error, [i['code'] for i in payload['errors']])
        return payload

    def test_valid_paired_native(self):
        result = self.check()['summary']
        self.assertTrue(result['full_match'])
        self.assertFalse(result['qualified'])
        self.assertEqual(result['total_features'], 2)

    def test_cannot_shrink_inventory(self):
        self.evaluation['features'].pop()
        result = self.check(1, 'INVENTORY_MAPPING')['summary']
        self.assertEqual(result['total_features'], 2)
        self.assertEqual(result['missing_feature_ids'], ['window-layout'])
        self.assertEqual(result['by_dimension']['visual']['missing'], 1)

    def test_frozen_contract_hash(self):
        (self.root / 'fidelity-contract.json').write_text('{}')
        self.check(2, 'HASH_MISMATCH')

    def test_wrong_objective_cannot_weaken_visual_gate(self):
        self.evaluation['objective'] = 'original_redesign'
        self.evaluation['features'][1]['baseline_origin'] = 'original_design'
        result = self.check(1, 'OBJECTIVE_MISMATCH')
        self.assertIn('ORIGINAL_VISUAL_BASELINE', [i['code'] for i in result['errors']])
        self.assertEqual(result['summary']['objective'], 'faithful_reimplementation')

    def test_original_visual_is_not_target_visual(self):
        self.evaluation['features'][1]['baseline_origin'] = 'original_design'
        self.check(1, 'ORIGINAL_VISUAL_BASELINE')

    def test_browser_or_wrong_platform_cannot_pass_as_native(self):
        for key, value in [('runtime', 'browser'), ('platform', 'linux')]:
            with self.subTest(key=key):
                original = self.evaluation['candidate'][key]
                self.evaluation['candidate'][key] = value
                self.check(1, 'RUNTIME_MISMATCH')
                self.evaluation['candidate'][key] = original

    def test_redesign_can_use_browser_and_original_visual(self):
        self.contract['objective'] = self.evaluation['objective'] = 'original_redesign'
        self.evaluation['candidate']['runtime'] = 'browser'
        self.evaluation['features'][1]['baseline_origin'] = 'original_design'
        self.freeze()
        self.check()

    def test_unknown_and_mismatch_block(self):
        for status, code in [('unknown', 'FIDELITY_UNKNOWN'), ('mismatch', 'FIDELITY_MISMATCH')]:
            with self.subTest(status=status):
                self.evaluation['features'][0]['status'] = status
                self.check(1, code)

    def test_deviation_needs_recorded_instruction_not_name(self):
        feature = self.evaluation['features'][0]
        feature['status'] = 'deviation'
        self.check(1, 'UNAPPROVED_DEVIATION')
        feature['deviation'] = dict(instruction='Reviewer approves omission', evidence=self.evidence)
        self.check(1, 'UNAPPROVED_DEVIATION')

    def test_user_instruction_qualifies_with_full_denominator(self):
        feature = self.evaluation['features'][0]
        instruction = 'User instruction: omit add-item.'
        feature['status'] = 'deviation'
        feature['deviation'] = dict(instruction=instruction, evidence=self.ref('instruction.txt', instruction.encode()))
        self.evaluation['cases'][0].update(status='blocked', result=None)
        summary = self.check()['summary']
        self.assertTrue(summary['qualified'])
        self.assertFalse(summary['full_match'])
        self.assertEqual(summary['total_features'], 2)
        self.assertEqual(summary['status_counts']['deviation'], 1)
        self.assertEqual(summary['matched_features'], 1)

    def test_separate_intent_and_completeness_reviews(self):
        for field, flag, code in [('intent_review', 'approved', 'INTENT_NOT_APPROVED'), ('completeness', 'reviewed', 'INVENTORY_INCOMPLETE')]:
            with self.subTest(field=field):
                self.contract[field][flag] = False
                self.freeze()
                self.check(1, code)
                self.contract[field][flag] = True

    def test_request_must_occur_in_evidence(self):
        self.contract['user_request'] = 'Unrelated task'
        self.freeze()
        self.check(2, 'REQUEST_EVIDENCE')

    def test_case_links_and_surface_mapping(self):
        self.evaluation['features'][0]['case_ids'] = []
        self.check(1, 'FEATURE_CASE_LINK')
        self.evaluation['features'][0]['case_ids'] = ['case-add-item']
        self.contract['surfaces'][0]['feature_ids'] = ['window-layout']
        self.freeze()
        self.check(1, 'INVENTORY_MAPPING')

    def test_omitted_case_and_unrelated_feature(self):
        self.evaluation['cases'][0]['feature_ids'] = ['window-layout']
        self.check(1, 'FEATURE_CASE_LINK')
        self.evaluation['cases'].pop()
        self.check(1, 'FEATURE_CASE_LINK')

    def test_false_pass_compares_outcome(self):
        self.evaluation['cases'][0]['result'] = self.outcome('case-add-item', {'matches': False})
        result = self.check(1, 'ORACLE_MISMATCH')
        self.assertIn('CASE_NOT_PASSED', [i['code'] for i in result['errors']])

    def test_boolean_is_not_integer(self):
        self.evaluation['cases'][0]['result'] = self.outcome('case-add-item', {'matches': 1})
        self.check(1, 'ORACLE_MISMATCH')

    def test_pass_needs_outcome_and_paired_evidence(self):
        self.evaluation['cases'][0]['result'] = None
        self.check(1, 'RESULT_MISSING')
        self.evaluation['cases'][0]['result'] = self.outcome('case-add-item', {'matches': True})
        self.evaluation['features'][0]['candidate_evidence'] = []
        self.check(1, 'EVIDENCE_MISSING')
        self.evaluation['features'][0]['candidate_evidence'] = [self.candidate]
        self.contract['features'][0]['target_evidence'] = []
        self.freeze()
        self.check(1, 'EVIDENCE_MISSING')

    def test_candidate_identity_all_layers(self):
        for part in ['feature', 'trial', 'actual']:
            with self.subTest(part=part):
                snapshot = copy.deepcopy(self.evaluation)
                if part == 'feature':
                    self.evaluation['features'][0]['candidate_id'] = 'wrong-build'
                elif part == 'trial':
                    self.evaluation['cases'][0]['candidate_id'] = 'wrong-build'
                else:
                    self.evaluation['cases'][0]['result'] = self.outcome('case-add-item', {'matches': True}, 'wrong-build')
                self.check(1, 'CANDIDATE_MISMATCH')
                self.evaluation = snapshot
                self.evaluation['cases'][0]['result'] = self.outcome('case-add-item', {'matches': True})

    def test_tampered_evidence(self):
        (self.root / 'candidate.txt').write_text('Changed build')
        self.check(2, 'HASH_MISMATCH')

    def test_paths_and_nonregular_evidence(self):
        self.evaluation['candidate']['evidence'][0] = dict(self.candidate, path='../candidate.txt')
        self.check(2, 'UNSAFE_PATH')
        try:
            (self.root / 'link.txt').symlink_to('candidate.txt')
            expected_error = 'SYMLINK'
        except OSError:
            # On hosts without symlink privileges, test a real directory-as-file
            # attack instead; this branch does not establish symlink coverage.
            (self.root / 'link.txt').mkdir()
            expected_error = 'NOT_REGULAR'
        self.evaluation['candidate']['evidence'][0] = dict(self.candidate, path='link.txt')
        self.check(2, expected_error)

    def test_duplicate_json_keys(self):
        (self.root / 'fidelity.json').write_text('{"format_version":1,"format_version":1}')
        proc = subprocess.run([sys.executable, str(CLI), str(self.root), '--json'], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(json.loads(proc.stdout)['errors'][0]['code'], 'DUPLICATE_KEY')

    def test_plain_cli_escapes_terminal_controls(self):
        self.evaluation['candidate']['evidence'][0]['path'] = 'bad\n\x1b[31m.txt'
        (self.root / 'fidelity.json').write_text(json.dumps(self.evaluation))
        proc = subprocess.run([sys.executable, str(CLI), str(self.root)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn('\x1b', proc.stdout)
        self.assertIn('\\x1b', proc.stdout)
        self.assertNotIn('bad\n', proc.stdout)

    def test_strict_fields_and_nonnull_oracle(self):
        self.evaluation['features'][0]['approved_by'] = 'reviewer'
        self.check(2, 'SHAPE')
        del self.evaluation['features'][0]['approved_by']
        self.contract['cases'][0]['expected'] = None
        self.freeze()
        self.check(2, 'CASE_EXPECTED')


if __name__ == '__main__':
    unittest.main()
