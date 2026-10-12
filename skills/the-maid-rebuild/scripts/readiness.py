"""Portable offline build-readiness gate; recorded declarations are not authentication."""
import argparse
import hashlib
import json

from core import (Invalid, MAX_JSON_BYTES, Reader, array, boolean, canonical, enum,
                  fail, ident, integer, shape, strict_json, strings, text)

CAPTURE_FIELDS = 'browser browser_version os css_viewport dpr fonts theme locale state'
EXPECTED_FIELDS = 'visible_strings control_states navigation persisted_effect error_recovery'


def validate_readiness(root):
    result = dict(format_version=1, stage='readiness', ok=False, exit_code=2,
                  contract_sha256=None, errors=[], warnings=[], summary={})

    def blocked(code, path, message):
        result['errors'].append(dict(code=code, path=path, message=message))

    try:
        reader = Reader(root)
        run = strict_json(reader.read('readiness.json', MAX_JSON_BYTES, False), 'readiness.json')
        shape(run, 'format_version contract target_id target_version candidate_id requested_slice_ids status full_scope_readiness_claim packets slices capabilities task resume gaps', 'readiness')
        integer(run['format_version'], 1, 1, 'readiness.format_version')
        shape(run['contract'], 'path sha256', 'readiness.contract')
        if run['contract']['path'] != 'readiness-contract.json':
            fail('CONTRACT_PATH', 'readiness.contract', 'Expected readiness-contract.json')
        raw = reader.ref(run['contract'], 'readiness.contract')
        contract = strict_json(raw, 'readiness-contract.json')
        result['contract_sha256'] = hashlib.sha256(raw).hexdigest()
        shape(contract, 'format_version target_id target_version sources requirements acceptance_cases slices capabilities inventory_review', 'contract')
        integer(contract['format_version'], 1, 1, 'contract.format_version')
        for value in (contract['target_id'], run['target_id'], run['candidate_id']):
            ident(value, 'identity')
        text(contract['target_version'], 'contract.target_version')
        text(run['target_version'], 'readiness.target_version')
        if contract['target_id'] != run['target_id'] or contract['target_version'] != run['target_version']:
            blocked('TARGET_MISMATCH', 'readiness.target_id', 'Target differs from frozen contract')
        strings(run['requested_slice_ids'], 'requested_slice_ids', ids=True, nonempty=True)
        enum(run['status'], 'ready provisional blocked', 'readiness.status')
        boolean(run['full_scope_readiness_claim'], 'full_scope_readiness_claim')

        def evidence(values, path, required=True):
            array(values, path)
            if required and not values:
                blocked('EVIDENCE_MISSING', path, 'Hashed evidence is required')
            for ref in values:
                reader.ref(ref, path)

        def records(values, fields, path):
            array(values, path)
            out = {}
            for item in values:
                shape(item, fields, path)
                ident(item['id'], path + '.id')
                if item['id'] in out:
                    fail('DUPLICATE_ID', path, item['id'])
                out[item['id']] = item
            return out

        def capture(value, path):
            shape(value, CAPTURE_FIELDS, path)
            for key in ('browser', 'browser_version', 'os', 'theme', 'locale', 'state'):
                text(value[key], path + '.' + key)
            shape(value['css_viewport'], 'width height', path + '.css_viewport')
            for key in ('width', 'height'):
                integer(value['css_viewport'][key], 1, 100000, path + '.css_viewport.' + key)
            from decimal import Decimal
            if type(value['dpr']) not in (int, Decimal) or not 0 < value['dpr'] <= 16:
                fail('DPR', path, 'DPR must be a positive JSON number at most 16')
            strings(value['fonts'], path + '.fonts', nonempty=True)

        review = contract['inventory_review']
        shape(review, 'approved reviewer evidence', 'inventory_review')
        boolean(review['approved'], 'inventory_review.approved')
        text(review['reviewer'], 'inventory_review.reviewer', empty=True)
        evidence(review['evidence'], 'inventory_review.evidence')
        if not review['approved'] or not review['reviewer'].strip():
            blocked('INVENTORY_NOT_APPROVED', 'inventory_review', 'Canonical inventory requires recorded review')
        sources = records(contract['sources'], 'id evidence', 'sources')
        for source in sources.values():
            evidence(source['evidence'], 'sources.' + source['id'])
        requirements = records(contract['requirements'], 'id kind surface state precondition action controls expected source_ids evidence confidence acceptance_ids slice_ids packet_id', 'requirements')
        slices = records(contract['slices'], 'id kind required requirement_ids capability_ids capture', 'slices')
        cases = records(contract['acceptance_cases'], 'id requirement_ids expected steps evidence', 'acceptance_cases')
        caps = records(contract['capabilities'], 'id description', 'capabilities')
        packets = records(run['packets'], 'id target_id approved reviewer requirement_ids expected evidence artifact', 'packets')
        evaluated = records(run['slices'], 'id status requirements capture blocker review', 'readiness.slices')
        available = records(run['capabilities'], 'id availability disposition evidence', 'readiness.capabilities')
        if not requirements or not slices:
            blocked('INVENTORY_EMPTY', 'contract', 'Requirements and slices must be nonempty')
        if set(requirements) & set(sources):
            blocked('SOURCE_AS_FEATURE', 'requirements', 'Source IDs and atomic requirement IDs must be separate')
        if set(evaluated) != set(slices) or set(available) != set(caps):
            blocked('INVENTORY_MAPPING', 'readiness', 'Slice and capability records must exactly cover the contract')
        if not set(run['requested_slice_ids']) <= set(slices):
            blocked('SLICE_MAPPING', 'requested_slice_ids', 'Requested slices must exist')
        for cap in caps.values():
            text(cap['description'], 'capabilities.' + cap['id'])
        for cap in available.values():
            enum(cap['availability'], 'available unavailable blocked', 'capabilities.availability')
            text(cap['disposition'], 'capabilities.disposition', empty=cap['availability'] == 'available')
            evidence(cap['evidence'], 'capabilities.evidence')
        for req in requirements.values():
            path = 'requirements.' + req['id']
            enum(req['kind'], 'behavior visual capability', path + '.kind')
            for key in ('surface', 'state', 'precondition', 'action'):
                text(req[key], path + '.' + key)
            enum(req['confidence'], 'observed documented unknown', path + '.confidence')
            ident(req['packet_id'], path + '.packet_id')
            strings(req['controls'], path + '.controls')
            if len(set(req['controls'])) != len(req['controls']):
                fail('DUPLICATE_REFERENCE', path + '.controls', 'Duplicate control name')
            for key in ('source_ids', 'acceptance_ids', 'slice_ids'):
                strings(req[key], path + '.' + key, ids=True, nonempty=True)
            if not set(req['source_ids']) <= set(sources) or not set(req['slice_ids']) <= set(slices):
                blocked('REQUIREMENT_MAPPING', path, 'Requirement must link existing sources and applicable slices')
            evidence(req['evidence'], path + '.evidence')
            shape(req['expected'], EXPECTED_FIELDS, path + '.expected')
            expected = req['expected']
            strings(expected['visible_strings'], path + '.visible_strings')
            if not isinstance(expected['control_states'], dict):
                fail('CONTROL_STATES', path, 'Expected a control state object')
            if set(expected['control_states']) != set(req['controls']):
                blocked('CONTROL_STATES', path, 'Every declared applicable control needs exactly one concrete state')
            for control, state in expected['control_states'].items():
                text(control, path + '.control')
                enum(state, 'enabled disabled hidden readonly', path + '.control_states')
            text(expected['navigation'], path + '.navigation', empty=True)
            for key in ('persisted_effect', 'error_recovery'):
                if not isinstance(expected[key], dict):
                    fail('EXPECTED_JSON', path + '.' + key, 'Expected a concrete JSON object')
                if expected[key] and set(expected[key]) <= {'description', 'source_id', 'source_ids', 'evidence', 'confidence', 'matches'}:
                    blocked('METADATA_ORACLE', path + '.' + key, 'Metadata or a generic match flag is not a concrete outcome')
            if not any(expected.values()):
                blocked('EXPECTED_EMPTY', path + '.expected', 'At least one concrete observable outcome is required')
            if not set(req['acceptance_ids']) <= set(cases):
                blocked('ACCEPTANCE_MAPPING', path, 'Acceptance IDs must reference concrete case definitions')
            if req['kind'] == 'visual' and any(slices.get(i, {}).get('kind') != 'visual' for i in req['slice_ids']):
                blocked('CAPTURE_APPLICABILITY', path, 'Visual requirements must belong to visual slices')
            packet = packets.get(req['packet_id'])
            mapped = {p['id'] for p in packets.values() if req['id'] in p['requirement_ids']}
            if packet is None or mapped != {req['packet_id']}:
                blocked('PACKET_MAPPING', path, 'Each requirement needs exactly its designated packet')
            elif req['id'] not in packet['expected'] or canonical(packet['expected'][req['id']]) != canonical(expected):
                blocked('PACKET_CONFLICT', path, 'Packet expected JSON differs from canonical requirement')
        for case in cases.values():
            path = 'acceptance_cases.' + case['id']
            strings(case['requirement_ids'], path + '.requirement_ids', ids=True, nonempty=True)
            strings(case['steps'], path + '.steps', nonempty=True)
            evidence(case['evidence'], path + '.evidence')
            linked = {r['id'] for r in requirements.values() if case['id'] in r['acceptance_ids']}
            frozen = {i: requirements[i]['expected'] for i in linked}
            if set(case['requirement_ids']) != linked or canonical(case['expected']) != canonical(frozen):
                blocked('ACCEPTANCE_MAPPING', path, 'Cases must retain exact reciprocal requirement mappings and canonical expectations')
        for packet in packets.values():
            path = 'packets.' + packet['id']
            ident(packet['target_id'], path + '.target_id')
            artifact = strict_json(reader.ref(packet['artifact'], path + '.artifact'), path + '.artifact')
            shape(artifact, 'target_id requirement_ids expected', path + '.artifact')
            if canonical(artifact) != canonical({k: packet[k] for k in ('target_id', 'requirement_ids', 'expected')}):
                blocked('PACKET_CONFLICT', path, 'Hashed author packet differs from declared canonical mapping')
            boolean(packet['approved'], path + '.approved')
            text(packet['reviewer'], path + '.reviewer', empty=True)
            strings(packet['requirement_ids'], path + '.requirement_ids', ids=True, nonempty=True)
            if not isinstance(packet['expected'], dict) or set(packet['expected']) != set(packet['requirement_ids']) or not set(packet['requirement_ids']) <= set(requirements):
                blocked('PACKET_MAPPING', path, 'Packet expectations must cover exactly its canonical requirement IDs')
            if packet['target_id'] != contract['target_id']:
                blocked('TARGET_MISMATCH', path, 'Packet targets another product')
            evidence(packet['evidence'], path + '.evidence')
            if not packet['approved'] or not packet['reviewer'].strip() or packet['reviewer'] == run['task'].get('owner'):
                blocked('PACKET_NOT_APPROVED', path, 'Packet needs recorded independent approval')
        ready = []
        nonready = []
        for sl in slices.values():
            path = 'slices.' + sl['id']
            enum(sl['kind'], 'behavior visual backend', path + '.kind')
            boolean(sl['required'], path + '.required')
            strings(sl['requirement_ids'], path + '.requirement_ids', ids=True, nonempty=True)
            strings(sl['capability_ids'], path + '.capability_ids', ids=True)
            expected_ids = {r['id'] for r in requirements.values() if sl['id'] in r['slice_ids']}
            if set(sl['requirement_ids']) != expected_ids or not set(sl['capability_ids']) <= set(caps):
                blocked('SLICE_MAPPING', path, 'Slice must retain exact applicable requirements and existing capabilities')
            if sl['kind'] == 'visual':
                capture(sl['capture'], path + '.capture')
            elif sl['capture'] is not None:
                fail('CAPTURE_APPLICABILITY', path, 'Only visual slices declare capture conditions')
            trial = evaluated.get(sl['id'])
            if trial is None:
                nonready.append(sl['id'])
                continue
            enum(trial['status'], 'ready provisional blocked', path + '.status')
            state_records = records(trial['requirements'], 'id status reason evidence', path + '.requirements')
            if set(state_records) != set(sl['requirement_ids']):
                blocked('REQUIREMENT_MAPPING', path, 'Every applicable requirement needs a readiness record')
            for state in state_records.values():
                enum(state['status'], 'ready blocked', path + '.requirements.status')
                text(state['reason'], path + '.reason', empty=state['status'] == 'ready')
                evidence(state['evidence'], path + '.requirements.evidence')
            independent = trial['review']
            shape(independent, 'approved reviewer evidence', path + '.review')
            boolean(independent['approved'], path + '.review.approved')
            text(independent['reviewer'], path + '.review.reviewer', empty=True)
            evidence(independent['evidence'], path + '.review.evidence', trial['status'] == 'ready')
            if trial['status'] == 'ready':
                ready.append(sl['id'])
                if trial['blocker'] is not None:
                    blocked('FALSE_READY', path, 'Ready slice cannot have a blocker')
                if not independent['approved'] or not independent['reviewer'].strip() or independent['reviewer'] == run['task'].get('owner'):
                    blocked('SLICE_NOT_APPROVED', path, 'Ready slice requires independent review')
                if any(s['status'] != 'ready' for s in state_records.values()) or any(requirements[i]['confidence'] == 'unknown' for i in expected_ids):
                    blocked('REQUIREMENT_NOT_READY', path, 'Ready requires all applicable known requirements ready')
                if any(available.get(i, {}).get('availability') != 'available' for i in sl['capability_ids']):
                    blocked('CAPABILITY_UNAVAILABLE', path, 'Ready slice requires available capabilities')
                if sl['kind'] == 'visual':
                    capture(trial['capture'], path + '.capture')
                    if canonical(sl['capture']) != canonical(trial['capture']):
                        blocked('CAPTURE_MISMATCH', path, 'Capture conditions differ from declared target conditions')
                elif trial['capture'] is not None:
                    fail('CAPTURE_APPLICABILITY', path, 'Only visual slices use captures')
            else:
                nonready.append(sl['id'])
                shape(trial['blocker'], 'owner reason next_action evidence', path + '.blocker')
                for key in ('owner', 'reason', 'next_action'):
                    text(trial['blocker'][key], path + '.blocker.' + key)
                evidence(trial['blocker']['evidence'], path + '.blocker.evidence')
                if trial['capture'] is not None:
                    capture(trial['capture'], path + '.capture')
        for key in ('task', 'resume'):
            record = run[key]
            shape(record, 'target_id name owner evidence', key)
            ident(record['target_id'], key + '.target_id')
            text(record['name'], key + '.name')
            text(record['owner'], key + '.owner')
            evidence(record['evidence'], key + '.evidence')
            if record['target_id'] != contract['target_id'] or contract['target_id'] not in record['name'].lower():
                blocked('TARGET_MISMATCH', key, 'Task and resume must identify the frozen target')
        gaps = records(run['gaps'], 'id cause status fixable owner reproduction requirement_ids acceptance next_action candidate_id closure', 'gaps')
        pending = []
        for gap in gaps.values():
            path = 'gaps.' + gap['id']
            enum(gap['cause'], 'specification implementation oracle capture access dependency', path + '.cause')
            enum(gap['status'], 'open closed', path + '.status')
            boolean(gap['fixable'], path + '.fixable')
            for key in ('owner', 'reproduction', 'acceptance', 'next_action'):
                text(gap[key], path + '.' + key)
            ident(gap['candidate_id'], path + '.candidate_id')
            strings(gap['requirement_ids'], path + '.requirement_ids', ids=True, nonempty=True)
            if not set(gap['requirement_ids']) <= set(requirements):
                blocked('REQUIREMENT_MAPPING', path, 'Gap must link canonical requirements')
            if gap['status'] == 'open':
                pending.append(gap['id'])
                if gap['closure'] is not None:
                    fail('GAP_CLOSURE', path, 'Open gap cannot carry closure')
            else:
                closure = gap['closure']
                shape(closure, 'candidate_id independent_reviewer rerun evidence', path + '.closure')
                ident(closure['candidate_id'], path + '.closure.candidate_id')
                text(closure['independent_reviewer'], path + '.closure.independent_reviewer')
                if closure['independent_reviewer'] == gap['owner'] or closure['candidate_id'] != run['candidate_id'] or closure['candidate_id'] == gap['candidate_id']:
                    blocked('GAP_CLOSURE', path, 'Closure needs a repaired candidate and a distinct reviewer')
                evidence(closure['evidence'], path + '.closure.evidence')
                rerun = strict_json(reader.ref(closure['rerun'], path + '.closure.rerun'), path + '.closure.rerun')
                shape(rerun, 'candidate_id requirement_ids expected actual', path + '.closure.rerun')
                frozen = {i: requirements[i]['expected'] for i in gap['requirement_ids'] if i in requirements}
                if rerun['candidate_id'] != run['candidate_id'] or canonical(rerun['requirement_ids']) != canonical(gap['requirement_ids']) or canonical(rerun['expected']) != canonical(frozen) or canonical(rerun['actual']) != canonical(frozen):
                    blocked('GAP_RERUN', path, 'Independent rerun must retain canonical expectations and repaired identity')
        required_pending = [s['id'] for s in slices.values() if s['required'] and s['id'] not in ready]
        for requested in run['requested_slice_ids']:
            if requested not in ready:
                blocked('REQUESTED_SLICE_NOT_READY', requested, 'Requested slice is not ready')
        if run['status'] == 'ready' and required_pending:
            blocked('FALSE_READY', 'readiness.status', 'Required scope remains nonready; use provisional or blocked')
        if run['full_scope_readiness_claim'] and (required_pending or pending or run['status'] != 'ready'):
            blocked('REPAIR_PENDING' if pending else 'FALSE_COMPLETE', 'full_scope_readiness_claim', 'Full scope readiness requires ready declared scope and no open recovery gaps')
        result['summary'] = dict(target_id=contract['target_id'], candidate_id=run['candidate_id'], status=run['status'],
            ready_slice_ids=ready, nonready_slice_ids=nonready, required_nonready_slice_ids=required_pending,
            open_gap_ids=pending, total_requirements=len(requirements), source_count=len(sources),
            declared_scope_ready=not required_pending and not pending and not result['errors'],
            limits=['Checks local records and hashes, not observation truth, authorization, omitted scope or actual service execution.'])
        result['exit_code'] = 1 if result['errors'] else 0
        result['ok'] = result['exit_code'] == 0
    except Invalid as exc:
        result['errors'].append(exc.issue)
    except (OSError, UnicodeError, RecursionError, ValueError, TypeError, RuntimeError, AttributeError, KeyError) as exc:
        result['errors'].append(dict(code='INPUT_ERROR', path='readiness', message=str(exc)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_dir')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    result = validate_readiness(args.project_dir)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print('readiness: ' + ('INVALID' if result['exit_code'] == 2 else 'BLOCKED' if not result['ok'] else 'PASS'))
        print(json.dumps(result['summary'], indent=2, ensure_ascii=True))
        for issue in result['errors']:
            print(json.dumps(issue, ensure_ascii=True))
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
