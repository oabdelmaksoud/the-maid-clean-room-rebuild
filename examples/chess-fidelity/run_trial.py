#!/usr/bin/env python3
"""Success means the fidelity gate rejects the existing candidate for real gaps."""
import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
GAPS = {
    'board-3d', 'board-styles', 'variants', 'local-hint-undo',
    'game-center', 'speech-controls', 'native-document-commands',
}
UNKNOWNS = {'camera-gestures', 'speech-output', 'target-files-pgn', 'computer-strength'}


def gate(script, fixture, output):
    process = subprocess.run(
        [sys.executable, str(script), str(fixture), '--json'],
        text=True, capture_output=True, check=False,
    )
    output.write_text(process.stdout, encoding='utf-8')
    output.with_suffix('.stderr.txt').write_text(process.stderr, encoding='utf-8')
    result = json.loads(process.stdout)
    if process.returncode != 1 or result.get('exit_code') != 1 or result.get('ok') is not False:
        raise ValueError('Expected a valid BLOCKED fidelity assessment, not acceptance or schema failure')
    return result


def feature_ids(result, code):
    return {error['path'].rsplit('.', 1)[-1] for error in result['errors'] if error['code'] == code}


def run(args):
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()  # Refuse to overwrite previous evidence.
    fixture = HERE / 'fixture'
    script = Path(args.maid_script).resolve() if args.maid_script else HERE.parents[1] / 'skills/behavior-rebuild/scripts/fidelity.py'
    identities = json.loads((HERE / 'fixture-identities.json').read_text(encoding='utf-8'))
    candidate_checked = False
    if args.candidate_html:
        actual = hashlib.sha256(Path(args.candidate_html).read_bytes()).hexdigest()
        if actual != identities['candidate_html_sha256']:
            raise ValueError('Candidate HTML differs from the recorded existing candidate; reassess instead of rebinding silently')
        candidate_checked = True
    blocked = gate(script, fixture, output / 'gate-recorded.json')
    if feature_ids(blocked, 'FIDELITY_MISMATCH') != GAPS:
        raise ValueError('Gate did not identify exactly the seven recorded fidelity differences')
    if feature_ids(blocked, 'FIDELITY_UNKNOWN') != UNKNOWNS:
        raise ValueError('Gate did not retain the four explicit unknown feature families')
    codes = {error['code'] for error in blocked['errors']}
    if not {'ORIGINAL_VISUAL_BASELINE', 'INVENTORY_INCOMPLETE'}.issubset(codes):
        raise ValueError('Original-design baseline or incomplete-inventory safeguard missing')
    if feature_ids(blocked, 'ORIGINAL_VISUAL_BASELINE') != {'board-3d', 'board-styles'}:
        raise ValueError('Visual baseline evidence was not bound to the two recorded visual gaps')
    expected_counts = {'match': 4, 'mismatch': 7, 'unknown': 4, 'deviation': 0}
    if blocked.get('summary', {}).get('status_counts') != expected_counts:
        raise ValueError('Unexpected recorded feature summary')

    forged_dir = output / 'forged-pass-fixture'
    shutil.copytree(fixture, forged_dir)
    evaluation_path = forged_dir / 'fidelity.json'
    evaluation = json.loads(evaluation_path.read_text(encoding='utf-8'))
    for feature in evaluation['features']:
        if feature['id'] in GAPS:
            feature['status'] = 'match'
            if feature['baseline_origin'] == 'original_design':
                feature['baseline_origin'] = 'target'
    for case in evaluation['cases']:
        if any(feature_id in GAPS for feature_id in case['feature_ids']):
            case['status'] = 'pass'
    # Neither the frozen expected values nor hashed runtime/source-attested actual outcomes change.
    evaluation_path.write_text(json.dumps(evaluation, indent=2) + '\n', encoding='utf-8')
    forged = gate(script, forged_dir, output / 'gate-forged-pass.json')
    mismatch_paths = {error['path'] for error in forged['errors'] if error['code'] == 'ORACLE_MISMATCH'}
    if len(mismatch_paths) != len(GAPS) or not all(any(gap in path for path in mismatch_paths) for gap in GAPS):
        raise ValueError('Forged passing labels were not rejected by all seven frozen outcome comparisons')
    summary = {
        'trial_success': True,
        'started_at': started_at,
        'completed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'candidate_fidelity': 'BLOCKED',
        'assessment': 'Retrospective recorded evidence plus partial fresh parent native-menu observations; no new app build or exhaustive probe',
        'candidate_html_sha256': identities['candidate_html_sha256'],
        'candidate_html_locally_checked': candidate_checked,
        'recorded_feature_counts': expected_counts,
        'recorded_blocker_counts': dict(collections.Counter(error['code'] for error in blocked['errors'])),
        'forged_pass_oracle_mismatches': len(mismatch_paths),
        'gate_script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
        'contract_sha256': blocked['contract_sha256'],
        'old_bounded_scope': 'Parent freshly reran five-case acceptance and 476 rules successfully; this does not establish target fidelity',
    }
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New directory for retained gate evidence')
    parser.add_argument('--maid-script', help='Optional installed fidelity.py path')
    parser.add_argument('--candidate-html', help='Optionally verify the unchanged existing candidate HTML identity without launching it')
    args = parser.parse_args()
    try:
        run(args)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'Fidelity trial failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
