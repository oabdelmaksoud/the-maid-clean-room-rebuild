"""Offline fidelity gate against a separately hashed request and feature contract."""
import argparse
import hashlib
import json

from core import (Invalid, MAX_JSON_BYTES, Reader, array, boolean, canonical, enum,
                  fail, ident, integer, shape, strict_json, strings, text)

OBJECTIVES = 'faithful_reimplementation original_redesign bounded_workflow'
DIMENSIONS = 'behavior visual journey interoperability platform'
RUNTIMES = 'native browser cli service'


def validate_fidelity(root):
    result = dict(format_version=1, stage='fidelity', ok=False, exit_code=2,
                  contract_sha256=None, errors=[], warnings=[], summary={})

    def blocked(code, path, message):
        result['errors'].append(dict(code=code, path=path, message=message))

    try:
        reader = Reader(root)
        evaluation = strict_json(reader.read('fidelity.json', MAX_JSON_BYTES, False), 'fidelity.json')
        shape(evaluation, 'format_version contract objective candidate cases features', 'fidelity')
        integer(evaluation['format_version'], 1, 1, 'fidelity.format_version')
        if evaluation['contract'].get('path') != 'fidelity-contract.json':
            fail('CONTRACT_PATH', 'fidelity.contract', 'Contract must reference fidelity-contract.json')
        raw = reader.ref(evaluation['contract'], 'fidelity.contract')
        contract = strict_json(raw, 'fidelity-contract.json')
        result['contract_sha256'] = hashlib.sha256(raw).hexdigest()
        shape(contract, 'format_version objective user_request request_evidence intent_review target surfaces completeness features cases', 'contract')
        integer(contract['format_version'], 1, 1, 'contract.format_version')
        enum(contract['objective'], OBJECTIVES, 'contract.objective')
        enum(evaluation['objective'], OBJECTIVES, 'fidelity.objective')
        if evaluation['objective'] != contract['objective']:
            blocked('OBJECTIVE_MISMATCH', 'fidelity.objective', 'Evaluation cannot change the frozen objective')
        objective = contract['objective']
        text(contract['user_request'], 'contract.user_request')
        request = reader.ref(contract['request_evidence'], 'contract.request_evidence').decode('utf-8')
        if contract['user_request'] not in request:
            fail('REQUEST_EVIDENCE', 'contract.user_request', 'Recorded request must occur in hashed request evidence')

        def files(values, path, required=True):
            array(values, path)
            if required and not values:
                blocked('EVIDENCE_MISSING', path, 'Hashed evidence is required')
            names = set()
            for ref in values:
                reader.ref(ref, path)
                if ref['path'] in names:
                    fail('DUPLICATE_REFERENCE', path, ref['path'])
                names.add(ref['path'])

        def records(values, path):
            array(values, path)
            out = {}
            for record in values:
                if not isinstance(record, dict) or 'id' not in record:
                    fail('SHAPE', path, 'Records require an id')
                ident(record['id'], path + '.id')
                if record['id'] in out:
                    fail('DUPLICATE_ID', path, record['id'])
                out[record['id']] = record
            return out

        for field, flag, code in [('intent_review', 'approved', 'INTENT_NOT_APPROVED'),
                                  ('completeness', 'reviewed', 'INVENTORY_INCOMPLETE')]:
            review = contract[field]
            shape(review, 'reviewer ' + flag + ' evidence', 'contract.' + field)
            text(review['reviewer'], 'contract.' + field + '.reviewer', empty=True)
            boolean(review[flag], 'contract.' + field + '.' + flag)
            files(review['evidence'], 'contract.' + field + '.evidence')
            if not review[flag] or not review['reviewer'].strip():
                blocked(code, 'contract.' + field, 'Distinct recorded review is required')
        target = contract['target']
        shape(target, 'name version platform runtime evidence', 'contract.target')
        for key in ('name', 'version', 'platform'):
            text(target[key], 'contract.target.' + key)
        enum(target['runtime'], RUNTIMES, 'contract.target.runtime')
        files(target['evidence'], 'contract.target.evidence')
        candidate = evaluation['candidate']
        shape(candidate, 'id platform runtime evidence', 'fidelity.candidate')
        ident(candidate['id'], 'fidelity.candidate.id')
        text(candidate['platform'], 'fidelity.candidate.platform')
        enum(candidate['runtime'], RUNTIMES, 'fidelity.candidate.runtime')
        files(candidate['evidence'], 'fidelity.candidate.evidence')
        if objective == 'faithful_reimplementation' and any(candidate[k] != target[k] for k in ('platform', 'runtime')):
            blocked('RUNTIME_MISMATCH', 'fidelity.candidate', 'Faithful fidelity requires the target platform and runtime')

        features = records(contract['features'], 'contract.features')
        surfaces = records(contract['surfaces'], 'contract.surfaces')
        cases = records(contract['cases'], 'contract.cases')
        evaluated = records(evaluation['features'], 'fidelity.features')
        trials = records(evaluation['cases'], 'fidelity.cases')
        if not features or not surfaces or not cases:
            blocked('INVENTORY_INCOMPLETE', 'contract', 'Nonempty surfaces, features and cases are required')
        if set(features) != set(evaluated):
            blocked('INVENTORY_MAPPING', 'fidelity.features', 'Evaluated feature IDs must equal the frozen inventory')
        if set(cases) != set(trials):
            blocked('FEATURE_CASE_LINK', 'fidelity.cases', 'Evaluated case IDs must equal the frozen cases')
        for feature in features.values():
            path = 'contract.features.' + feature['id']
            shape(feature, 'id dimension critical description surface_ids case_ids target_evidence', path)
            enum(feature['dimension'], DIMENSIONS, path + '.dimension')
            boolean(feature['critical'], path + '.critical')
            text(feature['description'], path + '.description')
            strings(feature['surface_ids'], path + '.surface_ids', ids=True, nonempty=True)
            strings(feature['case_ids'], path + '.case_ids', ids=True, nonempty=True)
            files(feature['target_evidence'], path + '.target_evidence')
            if not set(feature['surface_ids']) <= set(surfaces) or not set(feature['case_ids']) <= set(cases):
                blocked('FEATURE_CASE_LINK', path, 'Features must link existing frozen surfaces and cases')
        for surface in surfaces.values():
            path = 'contract.surfaces.' + surface['id']
            shape(surface, 'id description evidence feature_ids', path)
            text(surface['description'], path + '.description')
            strings(surface['feature_ids'], path + '.feature_ids', ids=True, nonempty=True)
            files(surface['evidence'], path + '.evidence')
            expected = {f['id'] for f in features.values() if surface['id'] in f['surface_ids']}
            if set(surface['feature_ids']) != expected:
                blocked('INVENTORY_MAPPING', path, 'Surface mapping must cover precisely its frozen features')
        for case in cases.values():
            path = 'contract.cases.' + case['id']
            shape(case, 'id feature_ids expected', path)
            strings(case['feature_ids'], path + '.feature_ids', ids=True, nonempty=True)
            if case['expected'] is None:
                fail('CASE_EXPECTED', path, 'Expected outcome must be non-null frozen JSON')
            expected = {f['id'] for f in features.values() if case['id'] in f['case_ids']}
            if set(case['feature_ids']) != expected:
                blocked('FEATURE_CASE_LINK', path, 'Case mapping must equal its linked frozen features')
        passed = set()
        for trial in trials.values():
            path = 'fidelity.cases.' + trial['id']
            shape(trial, 'id feature_ids candidate_id status evidence result', path)
            strings(trial['feature_ids'], path + '.feature_ids', ids=True, nonempty=True)
            ident(trial['candidate_id'], path + '.candidate_id')
            enum(trial['status'], 'pass failed blocked unknown', path + '.status')
            files(trial['evidence'], path + '.evidence', trial['status'] == 'pass')
            frozen = cases.get(trial['id'])
            if frozen is None or set(trial['feature_ids']) != set(frozen['feature_ids']):
                blocked('FEATURE_CASE_LINK', path, 'Test must identify its exact frozen features')
            if trial['candidate_id'] != candidate['id']:
                blocked('CANDIDATE_MISMATCH', path, 'Test belongs to a different candidate')
            actual = None
            if trial['result'] is not None:
                actual = strict_json(reader.ref(trial['result'], path + '.result'), path + '.result')
                shape(actual, 'case_id candidate_id actual', path + '.result')
                if actual['case_id'] != trial['id'] or actual['candidate_id'] != candidate['id']:
                    blocked('CANDIDATE_MISMATCH', path + '.result', 'Outcome identity does not match case and candidate')
            if trial['status'] == 'pass':
                if actual is None:
                    blocked('RESULT_MISSING', path, 'Pass requires a hashed actual outcome')
                elif frozen is not None and canonical(actual['actual']) != canonical(frozen['expected']):
                    blocked('ORACLE_MISMATCH', path, 'Actual differs from frozen expected outcome')
                elif trial['candidate_id'] == candidate['id'] and actual['candidate_id'] == candidate['id'] and actual['case_id'] == trial['id']:
                    passed.add(trial['id'])
        counts = {status: 0 for status in ('match', 'mismatch', 'unknown', 'deviation')}
        approved_deviations = []
        for feature in evaluated.values():
            path = 'fidelity.features.' + feature['id']
            shape(feature, 'id status candidate_id candidate_evidence case_ids baseline_origin deviation', path)
            enum(feature['status'], 'match mismatch unknown deviation', path + '.status')
            ident(feature['candidate_id'], path + '.candidate_id')
            strings(feature['case_ids'], path + '.case_ids', ids=True)
            enum(feature['baseline_origin'], 'target original_design not_applicable', path + '.baseline_origin')
            files(feature['candidate_evidence'], path + '.candidate_evidence', feature['status'] == 'match')
            frozen = features.get(feature['id'])
            if frozen is None:
                continue
            counts[feature['status']] += 1
            if feature['candidate_id'] != candidate['id']:
                blocked('CANDIDATE_MISMATCH', path, 'Feature evidence belongs to a different candidate')
            if set(feature['case_ids']) != set(frozen['case_ids']):
                blocked('FEATURE_CASE_LINK', path, 'Feature must retain all frozen case links')
            if frozen['dimension'] == 'visual':
                if objective == 'faithful_reimplementation' and feature['baseline_origin'] == 'original_design':
                    blocked('ORIGINAL_VISUAL_BASELINE', path, 'An original-design baseline cannot establish target visual fidelity')
                if feature['status'] == 'match' and feature['baseline_origin'] == 'not_applicable':
                    blocked('VISUAL_BASELINE_MISSING', path, 'Visual match requires a named baseline origin')
            elif feature['baseline_origin'] != 'not_applicable':
                fail('BASELINE_DIMENSION', path, 'Only visual features have visual baselines')
            deviation = feature['deviation']
            authorized = False
            if deviation is not None:
                shape(deviation, 'instruction evidence', path + '.deviation')
                text(deviation['instruction'], path + '.deviation.instruction')
                instruction = reader.ref(deviation['evidence'], path + '.deviation.evidence').decode('utf-8')
                authorized = deviation['instruction'] in instruction
            if feature['status'] == 'deviation':
                if authorized:
                    approved_deviations.append(feature['id'])
                else:
                    blocked('UNAPPROVED_DEVIATION', path, 'Deviation requires recorded user instruction in hashed evidence')
            elif deviation is not None:
                fail('DEVIATION_STATUS', path, 'Deviation evidence requires deviation status')
            elif feature['status'] == 'unknown':
                blocked('FIDELITY_UNKNOWN', path, 'Required fidelity remains unknown')
            elif feature['status'] == 'mismatch':
                blocked('FIDELITY_MISMATCH', path, 'Required fidelity differs from target')
            elif not set(frozen['case_ids']) <= passed:
                blocked('CASE_NOT_PASSED', path, 'Match requires every linked test outcome to pass')
        missing = sorted(set(features) - set(evaluated))
        by_dimension = {}
        for dimension in DIMENSIONS.split():
            members = [f['id'] for f in features.values() if f['dimension'] == dimension]
            dimension_counts = {status: sum(evaluated[i]['status'] == status for i in members if i in evaluated)
                                for status in counts}
            dimension_counts['missing'] = sum(i not in evaluated for i in members)
            by_dimension[dimension] = dict(total=len(members), **dimension_counts)
        result['summary'] = dict(objective=objective, target=target['name'], candidate_id=candidate['id'],
            total_features=len(features), critical_features=sum(f['critical'] for f in features.values()),
            status_counts=counts, missing_features=len(missing), by_dimension=by_dimension, missing_feature_ids=missing, approved_deviation_ids=approved_deviations,
            matched_features=counts['match'], full_match=False, qualified=False,
            evidence_gate='recorded target-fidelity evidence; not product certification',
            limits=['Hashes bind local bytes, not authorship, truth or user identity.',
                    'Intent and completeness reviews and user instructions are recorded declarations, not authentication.',
                    'Replacing the frozen contract and rebinding its hash requires external human review; this tool cannot authenticate the original freeze.',
                    'Recorded outcome comparison does not independently execute the candidate or discover omitted target features.'])
        result['exit_code'] = 1 if result['errors'] else 0
        result['ok'] = result['exit_code'] == 0
        result['summary']['full_match'] = result['ok'] and counts['match'] == len(features)
        result['summary']['qualified'] = result['ok'] and bool(approved_deviations)
    except Invalid as exc:
        result['errors'].append(exc.issue)
    except (OSError, UnicodeError, RecursionError, ValueError, TypeError, RuntimeError, AttributeError) as exc:
        result['errors'].append(dict(code='INPUT_ERROR', path='fidelity', message=str(exc)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_dir')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    result = validate_fidelity(args.project_dir)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        status = 'INVALID' if result['exit_code'] == 2 else 'BLOCKED' if not result['ok'] else 'QUALIFIED' if result['summary']['qualified'] else 'PASS'
        print(f'fidelity: {status} (recorded-evidence gate)')
        print(json.dumps(result['summary'], indent=2, ensure_ascii=True))
        for error in result['errors']:
            print(json.dumps(error, ensure_ascii=True))
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
