"""Original synthetic readiness records; no target access, assets or network needed."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'skills/the-maid-rebuild/scripts'))
from readiness import validate_readiness


class Fixture:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.evidence = self.ref('synthetic-observation.txt', b'Original synthetic observation and review fixture; not Manus evidence.')
        expected = dict(visible_strings=['Continue'], control_states={'continue': 'disabled'},
                        navigation='', persisted_effect={}, error_recovery={'empty_input': 'stay'})
        capture = dict(browser='synthetic-browser', browser_version='1', os='synthetic-os',
                       css_viewport=dict(width=1280, height=720), dpr=1, fonts=['Synthetic Sans'],
                       theme='dark', locale='en-US', state='empty-login')
        self.contract = dict(format_version=1, target_id='manus', target_version='synthetic-1',
            sources=[dict(id='login-source', evidence=[self.evidence])],
            requirements=[dict(id='empty-continue', kind='visual', surface='login', state='empty',
                precondition='Email is empty', action='View login', controls=['continue'], expected=expected,
                source_ids=['login-source'], evidence=[self.evidence], confidence='observed',
                acceptance_ids=['empty-login-case'], slice_ids=['login-visual'], packet_id='login-packet')],
            slices=[dict(id='login-visual', kind='visual', required=True, requirement_ids=['empty-continue'], capability_ids=['identity'], capture=capture)],
            acceptance_cases=[dict(id='empty-login-case', requirement_ids=['empty-continue'], expected={'empty-continue': copy.deepcopy(expected)}, steps=['View empty login; assert disabled Continue'], evidence=[self.evidence])],
            capabilities=[dict(id='identity', description='Synthetic identity service')],
            inventory_review=self.review())
        packet = dict(id='login-packet', target_id='manus', approved=True, reviewer='packet-reviewer',
                      requirement_ids=['empty-continue'], expected={'empty-continue': copy.deepcopy(expected)},
                      evidence=[self.evidence], artifact={})
        continuity = dict(target_id='manus', name='Manus synthetic readiness', owner='builder', evidence=[self.evidence])
        self.run = dict(format_version=1, contract={}, target_id='manus', target_version='synthetic-1',
            candidate_id='candidate-one', requested_slice_ids=['login-visual'], status='ready', full_scope_readiness_claim=False,
            packets=[packet], slices=[dict(id='login-visual', status='ready',
                requirements=[dict(id='empty-continue', status='ready', reason='', evidence=[self.evidence])],
                capture=copy.deepcopy(capture), blocker=None, review=self.review())],
            capabilities=[dict(id='identity', availability='available', disposition='', evidence=[self.evidence])],
            task=copy.deepcopy(continuity), resume=copy.deepcopy(continuity), gaps=[])
        self.freeze()

    def ref(self, name, data):
        (self.root / name).write_bytes(data)
        return dict(path=name, sha256=hashlib.sha256(data).hexdigest())

    def review(self):
        return dict(approved=True, reviewer='independent-reviewer', evidence=[self.evidence])

    def freeze(self):
        self.run['contract'] = self.ref('readiness-contract.json', json.dumps(self.contract).encode())
        for packet in self.run['packets']:
            packet['artifact'] = self.ref(packet['id'] + '.json', json.dumps({k: packet[k] for k in ('target_id', 'requirement_ids', 'expected')}).encode())
        (self.root / 'readiness.json').write_text(json.dumps(self.run, indent=2))

    def backend_provisional(self):
        req = copy.deepcopy(self.contract['requirements'][0])
        req.update(id='task-store', kind='behavior', surface='task', state='new', precondition='Local task exists',
                   action='Save task', controls=[], slice_ids=['task-backend'], acceptance_ids=['save-task-case'], packet_id='backend-packet')
        req['expected'] = dict(visible_strings=[], control_states={}, navigation='',
                               persisted_effect={'saved': True}, error_recovery={})
        self.contract['requirements'].append(req)
        self.contract['acceptance_cases'].append(dict(id='save-task-case', requirement_ids=['task-store'], expected={'task-store': copy.deepcopy(req['expected'])}, steps=['Save and reopen task; assert saved state'], evidence=[self.evidence]))
        self.contract['slices'].append(dict(id='task-backend', kind='backend', required=True,
            requirement_ids=['task-store'], capability_ids=[], capture=None))
        self.run['packets'].append(dict(id='backend-packet', target_id='manus', approved=True, reviewer='packet-reviewer',
            requirement_ids=['task-store'], expected={'task-store': copy.deepcopy(req['expected'])}, evidence=[self.evidence], artifact={}))
        self.run['slices'][0].update(status='blocked', capture=None,
            blocker=dict(owner='observer', reason='Target capture unavailable', next_action='Capture permitted target login', evidence=[self.evidence]))
        self.run['slices'][0]['requirements'][0].update(status='blocked', reason='Matched capture unavailable')
        self.run['slices'].append(dict(id='task-backend', status='ready',
            requirements=[dict(id='task-store', status='ready', reason='', evidence=[self.evidence])],
            capture=None, blocker=None, review=self.review()))
        self.run.update(status='provisional', requested_slice_ids=['task-backend'])
        self.freeze()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Retain fixtures in a new output directory')
    args = parser.parse_args()
    if args.output is not None:
        if args.output.exists() or args.output.is_symlink():
            parser.error('--output must name a new directory')
        args.output.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as temporary:
        directory = str(args.output) if args.output is not None else temporary
        results = {}
        fixture = Fixture(Path(directory) / 'flawed')
        fixture.run['packets'][0]['expected']['empty-continue']['visible_strings'] = ['Flex setup']
        fixture.freeze()
        results['flawed_handoff'] = validate_readiness(fixture.root)
        fixture = Fixture(Path(directory) / 'corrected')
        results['corrected_reviewed_slice'] = validate_readiness(fixture.root)
        fixture = Fixture(Path(directory) / 'backend')
        fixture.backend_provisional()
        results['independent_backend'] = validate_readiness(fixture.root)
        fixture = Fixture(Path(directory) / 'full-scope')
        fixture.backend_provisional()
        fixture.run['full_scope_readiness_claim'] = True
        fixture.freeze()
        results['full_scope_readiness_claim'] = validate_readiness(fixture.root)
        payload = {name: dict(exit_code=r['exit_code'], errors=r['errors'], summary=r['summary']) for name, r in results.items()}
        rendered = json.dumps(payload, indent=2)
        print(rendered)
        if args.output is not None:
            (args.output / 'results.json').write_text(rendered + '\n')
        return 0 if [r['exit_code'] for r in results.values()] == [1, 0, 0, 1] else 1


if __name__ == '__main__':
    raise SystemExit(main())
