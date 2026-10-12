"""Offline, read-only validation of Behavior Rebuild Kit version 1 records."""
import hashlib
import json
import re
import stat
import ui_checks
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

MAX_JSON_BYTES = 1024 * 1024
MAX_DEPTH = 40
MAX_COLLECTION = 1000
MAX_FILES = 256
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


class Invalid(ValueError):
    def __init__(self, code, path, message):
        self.issue = dict(code=code, path=str(path), message=message)
        super().__init__(message)


def fail(code, path, message):
    raise Invalid(code, path, message)


def shape(value, keys, path):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        fail('SHAPE', path, 'Expected exactly these fields: ' + keys)


def text(value, path, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()):
        fail('TEXT', path, 'Expected a nonblank string' if not empty else 'Expected a string')


def ident(value, path):
    if not isinstance(value, str) or not ID.fullmatch(value):
        fail('ID', path, 'Expected a lowercase hyphenated identifier, maximum 64 characters')


def enum(value, choices, path):
    if not isinstance(value, str) or value not in choices.split():
        fail('ENUM', path, 'Expected one of: ' + choices)


def integer(value, low, high, path):
    if type(value) is not int or not low <= value <= high:
        fail('INTEGER', path, f'Expected integer in {low}..{high}')


def boolean(value, path):
    if type(value) is not bool:
        fail('BOOLEAN', path, 'Expected boolean')


def array(value, path):
    if not isinstance(value, list) or len(value) > MAX_COLLECTION:
        fail('COLLECTION', path, f'Expected array with at most {MAX_COLLECTION} items')


def strings(value, path, ids=False, nonempty=False):
    array(value, path)
    if nonempty and not value:
        fail('EMPTY_COLLECTION', path, 'At least one item required')
    for i, item in enumerate(value):
        (ident if ids else text)(item, f'{path}[{i}]')
    if ids and len(set(value)) != len(value):
        fail('DUPLICATE_REFERENCE', path, 'Duplicate reference')


def path_parts(value):
    text(value, 'path')
    parts = value.split('/')
    if any(x in value for x in ('\\', ':', '\x00')) or any(p in ('', '.', '..') for p in parts):
        fail('UNSAFE_PATH', value, 'Expected a relative POSIX path without traversal or special components')
    return parts


def strict_json(raw, path):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                fail('DUPLICATE_KEY', path, 'Duplicate JSON key: ' + key)
            out[key] = value
        return out

    def constant(value):
        fail('NONFINITE_JSON', path, 'Nonfinite JSON number: ' + value)

    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant, parse_float=Decimal)
        def walk(item, depth=0):
            if depth > MAX_DEPTH:
                fail('JSON_DEPTH', path, 'JSON nesting exceeds limit')
            if isinstance(item, (list, dict)):
                if len(item) > MAX_COLLECTION:
                    fail('COLLECTION', path, 'JSON collection exceeds limit')
                for child in (item.values() if isinstance(item, dict) else item):
                    walk(child, depth + 1)
            elif isinstance(item, Decimal):
                if not item.is_finite():
                    fail('NONFINITE_JSON', path, 'JSON number is not finite')
        walk(value)
        return value
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError, InvalidOperation) as exc:
        if isinstance(exc, Invalid):
            raise
        fail('INVALID_JSON', path, str(exc))


class Reader:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        if not self.root.is_dir():
            fail('ROOT', root, 'Project root must be a directory')
        self.cache = {}
        self.total = 0
        self.visual_pixels_checked = 0

    def local(self, name):
        current = self.root
        for component in path_parts(name):
            current = current / component
            if current.is_symlink():
                fail('SYMLINK', name, 'Symlink components are prohibited')
        return current

    def read(self, name, limit=None, referenced=True):
        limit = MAX_FILE_BYTES if limit is None else limit
        path = self.local(name)
        if name not in self.cache:
            if referenced and sum(v[1] for v in self.cache.values()) >= MAX_FILES:
                fail('FILE_LIMIT', name, 'Too many referenced files')
            size = path.stat().st_size
            if not stat.S_ISREG(path.stat().st_mode):
                fail('NOT_REGULAR', name, 'Expected regular file')
            if size > limit:
                fail('FILE_SIZE', name, 'File exceeds size limit')
            if self.total + size > MAX_TOTAL_BYTES:
                fail('TOTAL_SIZE', name, 'Total read budget exceeded')
            with path.open('rb') as stream:
                raw = stream.read(min(limit, MAX_TOTAL_BYTES - self.total) + 1)
            if len(raw) > limit or self.total + len(raw) > MAX_TOTAL_BYTES:
                fail('FILE_SIZE', name, 'File grew beyond read budget')
            self.total += len(raw)
            self.cache[name] = (raw, referenced)
        raw, was_ref = self.cache[name]
        if referenced and not was_ref:
            if sum(v[1] for v in self.cache.values()) >= MAX_FILES:
                fail('FILE_LIMIT', name, 'Too many referenced files')
            self.cache[name] = (raw, True)
        if len(raw) > limit:
            fail('FILE_SIZE', name, 'File exceeds size limit')
        return raw

    def ref(self, value, path, extra=False):
        shape(value, 'path sha256 role provenance source_ids' if extra else 'path sha256', path)
        if not isinstance(value['sha256'], str) or not SHA.fullmatch(value['sha256']):
            fail('SHA256', path, 'Expected lowercase SHA256 digest')
        raw = self.read(value['path'])
        if hashlib.sha256(raw).hexdigest() != value['sha256']:
            fail('HASH_MISMATCH', value['path'], 'File does not match recorded SHA256')
        return raw


def canonical(value):
    """Typed structure with exact decimal values; never expand exponent notation."""
    if isinstance(value, dict):
        return ('object', tuple((key, canonical(item)) for key, item in sorted(value.items())))
    if isinstance(value, list):
        return ('array', tuple(canonical(item) for item in value))
    if isinstance(value, Decimal):
        return ('decimal', value)
    if type(value) is int:
        return ('integer', value)
    if type(value) is bool:
        return ('boolean', value)
    if value is None:
        return ('null',)
    return ('string', value)


def validate_project(root, stage='discover', run=None, candidate=None):
    result = dict(format_version=1, stage=stage, ok=False, exit_code=2,
                  manifest_sha256=None, errors=[], warnings=[], summary={})
    def issue(code, path, message, warning=False):
        result['warnings' if warning else 'errors'].append(dict(code=code, path=path, message=message))
    try:
        if stage not in ('discover', 'handoff', 'acceptance'):
            fail('USAGE', 'stage', 'Unknown validation stage')
        if (run is None) != (candidate is None):
            fail('USAGE', 'run', 'Supply both run and candidate')
        if stage == 'acceptance' and run is None:
            fail('USAGE', 'run', 'Acceptance requires explicit run and candidate')
        reader = Reader(root)
        raw = reader.read('project.json', MAX_JSON_BYTES, False)
        project = strict_json(raw, 'project.json')
        result['manifest_sha256'] = hashlib.sha256(raw).hexdigest()
        shape(project, 'format_version project_id title scope target sources commands cases exclusions exclusion_note handoff gaps', 'project')
        integer(project['format_version'], 1, 1, 'format_version')
        ident(project['project_id'], 'project_id')
        for key in ('title', 'scope', 'exclusion_note'):
            text(project[key], key)
        shape(project['target'], 'name version mode', 'target')
        for key, value in project['target'].items():
            text(value, 'target.' + key)
        indexes = {}
        for key in ('sources', 'commands', 'cases', 'gaps'):
            array(project[key], key)
            index = {}
            for i, record in enumerate(project[key]):
                if not isinstance(record, dict) or 'id' not in record:
                    fail('SHAPE', f'{key}[{i}]', 'Record needs id')
                ident(record['id'], f'{key}[{i}].id')
                if record['id'] in index:
                    fail('DUPLICATE_ID', key, record['id'])
                index[record['id']] = record
            indexes[key] = index
        def refs(values, kind, path, nonempty=False):
            strings(values, path, ids=True, nonempty=nonempty)
            for value in values:
                if value not in indexes[kind]:
                    fail('UNKNOWN_REFERENCE', path, value)
        def files(values, path):
            array(values, path)
            names = set()
            for value in values:
                reader.ref(value, path)
                if value['path'] in names:
                    fail('DUPLICATE_REFERENCE', path, value['path'])
                names.add(value['path'])
        for source in project['sources']:
            p = 'sources.' + source['id']
            shape(source, 'id kind locator captured_on description permission evidence', p)
            enum(source['kind'], 'D O R U', p + '.kind')
            for key in ('locator', 'description'):
                text(source[key], p + '.' + key)
            if not isinstance(source['captured_on'], str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', source['captured_on']):
                fail('DATE', p, 'Expected YYYY-MM-DD')
            try:
                date.fromisoformat(source['captured_on'])
            except ValueError:
                fail('DATE', p, 'Invalid date')
            permission = source['permission']
            shape(permission, 'observe handoff publish basis reviewer', p + '.permission')
            text(permission['basis'], p + '.permission.basis')
            text(permission['reviewer'], p + '.permission.reviewer', empty=True)
            for use in ('observe', 'handoff', 'publish'):
                enum(permission[use], 'allowed denied unknown', p + '.permission.' + use)
                if permission[use] == 'allowed' and not permission['reviewer'].strip():
                    fail('PERMISSION_REVIEWER', p, 'Allowed permissions require reviewer')
                if permission[use] == 'unknown':
                    issue('UNKNOWN_PERMISSION', p + '.permission.' + use, 'Permission remains unresolved', True)
            if source['kind'] == 'U':
                issue('UNKNOWN_SOURCE', p, 'Source is unverified', True)
            files(source['evidence'], p + '.evidence')
            if source['kind'] == 'O' and not source['evidence']:
                fail('OBSERVATION_EVIDENCE', p, 'Observed sources require evidence')
        for command in project['commands']:
            p = 'commands.' + command['id']
            shape(command, 'id description parameters preconditions effects errors recovery access events design_rationale', p)
            for key in ('description', 'parameters', 'recovery', 'access', 'design_rationale'):
                text(command[key], p + '.' + key)
            for key in ('preconditions', 'effects', 'errors', 'events'):
                strings(command[key], p + '.' + key, nonempty=key in ('effects', 'errors'))
        for case in project['cases']:
            p = 'cases.' + case['id']
            shape(case, 'id title origin source_ids authorship command_ids preconditions steps expected fixtures oracle required required_trials', p)
            enum(case['origin'], 'documented observed reported unknown original_synthetic_design', p + '.origin')
            for key in ('title', 'expected'):
                text(case[key], p + '.' + key)
            text(case['authorship'], p + '.authorship', empty=case['origin'] != 'original_synthetic_design')
            refs(case['source_ids'], 'sources', p + '.source_ids', case['origin'] in ('documented', 'observed', 'reported'))
            refs(case['command_ids'], 'commands', p + '.command_ids', True)
            strings(case['preconditions'], p + '.preconditions')
            strings(case['steps'], p + '.steps', nonempty=True)
            boolean(case['required'], p + '.required')
            integer(case['required_trials'], 1, 20, p + '.required_trials')
            files(case['fixtures'], p + '.fixtures')
            shape(case['oracle'], 'kind description expected', p + '.oracle')
            enum(case['oracle']['kind'], 'exact_json manual_review journey_trace visual_pixels', p + '.oracle.kind')
            text(case['oracle']['description'], p + '.oracle.description')
            if (case['oracle']['kind'] == 'manual_review') != (case['oracle']['expected'] is None):
                fail('ORACLE_EXPECTED', p, 'Manual review requires null; automated oracles require non-null expected')
            if case['oracle']['kind'] == 'journey_trace':
                ui_checks.journey(case['oracle']['expected'], p + '.oracle.expected')
            elif case['oracle']['kind'] == 'visual_pixels':
                ui_checks.visual_expected(case['oracle']['expected'], p + '.oracle.expected', reader)
            kinds = {indexes['sources'][s]['kind'] for s in case['source_ids']}
            required_kind = {'documented': 'D', 'observed': 'O', 'reported': 'R'}.get(case['origin'])
            if required_kind and (required_kind not in kinds or 'U' in kinds):
                fail('SOURCE_KIND', p, 'Evidence source kinds do not substantiate case origin')
            if case['origin'] == 'unknown':
                issue('UNKNOWN_CASE', p, 'Behavior provenance remains unknown', True)
        excluded = set()
        array(project['exclusions'], 'exclusions')
        for record in project['exclusions']:
            shape(record, 'case_id reason approved_by', 'exclusions')
            refs([record['case_id']], 'cases', 'exclusions.case_id')
            for key in ('reason', 'approved_by'):
                text(record[key], 'exclusions.' + key)
            if record['case_id'] in excluded:
                fail('DUPLICATE_REFERENCE', 'exclusions', record['case_id'])
            excluded.add(record['case_id'])
        handoff = project['handoff']
        shape(handoff, 'directory files reviewer approved attestation exposure_notes', 'handoff')
        directory = handoff['directory']
        path_parts(directory)
        boolean(handoff['approved'], 'handoff.approved')
        for key in ('reviewer', 'attestation'):
            text(handoff[key], 'handoff.' + key, empty=True)
        strings(handoff['exposure_notes'], 'handoff.exposure_notes')
        array(handoff['files'], 'handoff.files')
        packet_names = set()
        for record in handoff['files']:
            reader.ref(record, 'handoff.files', True)
            name = record['path']
            if not name.startswith(directory + '/'):
                fail('PACKET_PATH', name, 'Handoff file must be below handoff directory')
            if name in packet_names:
                fail('DUPLICATE_REFERENCE', 'handoff.files', name)
            packet_names.add(name)
            if Path(name).suffix.lower() not in ('.md', '.txt', '.json', '.csv'):
                fail('PACKET_EXTENSION', name, 'Unsupported handoff file extension')
            enum(record['role'], 'specification fixture', name)
            text(record['provenance'], name)
            refs(record['source_ids'], 'sources', name + '.source_ids')
        packet = reader.local(directory)
        if packet.exists():
            if not packet.is_dir():
                fail('PACKET_DIRECTORY', directory, 'Expected directory')
            actual = set()
            pending = [packet]
            entries_seen = 0
            while pending:
                current = pending.pop()
                for child in current.iterdir():
                    entries_seen += 1
                    if entries_seen > MAX_COLLECTION:
                        fail('PACKET_LIMIT', directory, 'Packet scan entry limit exceeded')
                    name = child.relative_to(reader.root).as_posix()
                    if child.is_symlink():
                        fail('SYMLINK', name, 'Symlink in packet')
                    if child.is_dir():
                        pending.append(child)
                    elif child.is_file():
                        actual.add(name)
                    else:
                        fail('NOT_REGULAR', name, 'Nonregular entry in packet')
            if actual != packet_names:
                fail('PACKET_FILE_SET', directory, 'Packet files differ from manifest; extra=' + str(sorted(actual - packet_names)) + ', missing=' + str(sorted(packet_names - actual)))
        elif handoff['files'] or stage != 'discover':
            fail('PACKET_MISSING', directory, 'Handoff directory missing')
        for gap in project['gaps']:
            p = 'gaps.' + gap['id']
            shape(gap, 'id case_ids severity impact recovery_action status', p)
            refs(gap['case_ids'], 'cases', p + '.case_ids')
            enum(gap['severity'], 'blocker high medium low', p + '.severity')
            enum(gap['status'], 'open closed', p + '.status')
            integer(gap['impact'], 1, 5, p + '.impact')
            text(gap['recovery_action'], p + '.recovery_action')
        active = [c for c in project['cases'] if c['id'] not in excluded]
        required = [c for c in active if c['required']]
        result['summary'] = dict(project_id=project['project_id'], total_cases=len(project['cases']), active_cases=len(active), required_active_cases=len(required), optional_active_cases=sum(not c['required'] for c in active), excluded_case_ids=sorted(excluded), required_trials=sum(c['required_trials'] for c in required), acceptance_evaluated=stage == 'acceptance', evidence_gate='recorded-evidence gate; not product certification', publication_permission='not evaluated; local handoff never grants publication approval', limits=['File integrity and recorded approvals cannot establish provenance truth or detect concealed copied content.', 'Manual review records are declarations; this tool cannot independently evaluate their correctness.'], raw_source_files_handed_off=any(f['path'] in packet_names for s in project['sources'] for f in s['evidence']), gaps=sorted(project['gaps'], key=lambda g: (['blocker', 'high', 'medium', 'low'].index(g['severity']), -g['impact'], g['id'])))
        if not project['cases']:
            issue('EMPTY_SCOPE', 'cases', 'No behavior cases defined')
        if stage in ('handoff', 'acceptance'):
            if not (handoff['approved'] and handoff['reviewer'].strip() and handoff['attestation'].strip() and handoff['exposure_notes'] and any(f['role'] == 'specification' for f in handoff['files'])):
                issue('HANDOFF_APPROVAL', 'handoff', 'Reviewed specification, attestation and exposure notes required')
            for record in handoff['files']:
                for sid in record['source_ids']:
                    if indexes['sources'][sid]['permission']['handoff'] != 'allowed':
                        issue('HANDOFF_PERMISSION', record['path'], 'Source handoff permission not allowed: ' + sid)
            for case in active:
                if case['origin'] == 'unknown':
                    issue('UNKNOWN_CASE', case['id'], 'Unknown cases cannot enter implementation handoff')
                for sid in case['source_ids']:
                    perm = indexes['sources'][sid]['permission']
                    if perm['observe'] != 'allowed' or perm['handoff'] != 'allowed':
                        issue('CASE_PERMISSION', case['id'], 'Observe and handoff permission required: ' + sid)
                for fixture in case['fixtures']:
                    if fixture['path'] not in packet_names:
                        issue('FIXTURE_NOT_HANDED_OFF', case['id'], fixture['path'])
        evaluations = {}
        if run is not None:
            text(candidate, 'candidate')
            record = strict_json(reader.read(run, MAX_JSON_BYTES, False), run)
            shape(record, 'format_version run_id manifest_sha256 candidate_id created_at runner environment evaluations', 'run')
            integer(record['format_version'], 1, 1, 'run.format_version')
            ident(record['run_id'], 'run.run_id')
            for key in ('candidate_id', 'created_at', 'runner', 'environment'):
                text(record[key], 'run.' + key)
            if not isinstance(record['manifest_sha256'], str) or not SHA.fullmatch(record['manifest_sha256']):
                fail('SHA256', 'run.manifest_sha256', 'Expected lowercase SHA256')
            if record['manifest_sha256'] != result['manifest_sha256']:
                fail('MANIFEST_MISMATCH', run, 'Run is bound to different raw project bytes')
            if record['candidate_id'] != candidate:
                fail('CANDIDATE_MISMATCH', run, 'Explicit candidate differs from run')
            try:
                stamp = datetime.fromisoformat(record['created_at'])
                if stamp.tzinfo is None or stamp.utcoffset() is None or 'T' not in record['created_at']:
                    raise ValueError('Timezone ISO8601 timestamp required')
            except ValueError:
                fail('TIMESTAMP', run, 'Timezone ISO8601 timestamp required')
            array(record['evaluations'], 'run.evaluations')
            for evaluation in record['evaluations']:
                p = 'run.evaluations'
                shape(evaluation, 'case_id trial status oracle_status result evidence review notes', p)
                refs([evaluation['case_id']], 'cases', p + '.case_id')
                case = indexes['cases'][evaluation['case_id']]
                integer(evaluation['trial'], 1, case['required_trials'], p + '.trial')
                slot = (case['id'], evaluation['trial'])
                if slot in evaluations:
                    fail('DUPLICATE_TRIAL', p, str(slot))
                evaluations[slot] = evaluation
                enum(evaluation['status'], 'pass failed blocked unknown skip', p + '.status')
                enum(evaluation['oracle_status'], 'available missing', p + '.oracle_status')
                text(evaluation['notes'], p + '.notes', empty=evaluation['status'] in ('pass', 'skip'))
                review = evaluation['review']
                shape(review, 'reviewer decision notes', p + '.review')
                enum(review['decision'], 'accepted rejected pending', p + '.review.decision')
                for key in ('reviewer', 'notes'):
                    text(review[key], p + '.review.' + key, empty=True)
                files(evaluation['evidence'], p + '.evidence')
                actual = None
                if evaluation['result'] is not None:
                    actual = reader.ref(evaluation['result'], p + '.result')
                if evaluation['oracle_status'] == 'missing' and evaluation['status'] not in ('blocked', 'unknown'):
                    fail('MISSING_ORACLE_STATUS', p, 'Missing oracle permits only blocked or unknown status')
                if evaluation['status'] == 'skip' and case['id'] not in excluded:
                    fail('UNAPPROVED_SKIP', p, 'Skip requires approved case exclusion')
                if evaluation['status'] == 'pass':
                    if not review['reviewer'].strip() or review['decision'] != 'accepted' or not review['notes'].strip():
                        issue('PASS_REVIEW', case['id'], 'Pass requires recorded accepted review with reviewer and notes')
                    if case['oracle']['kind'] in ('exact_json', 'journey_trace', 'visual_pixels'):
                        if actual is None:
                            issue('RESULT_MISSING', case['id'], 'Automated oracle pass requires result file')
                        else:
                            if case['oracle']['kind'] == 'visual_pixels':
                                matches = ui_checks.visual_matches(case['oracle']['expected'], actual, evaluation['result']['path'], reader)
                            else:
                                parsed = strict_json(actual, evaluation['result']['path'])
                                if case['oracle']['kind'] == 'journey_trace':
                                    ui_checks.journey(parsed, evaluation['result']['path'])
                                matches = canonical(parsed) == canonical(case['oracle']['expected'])
                            if not matches:
                                issue('ORACLE_MISMATCH', case['id'], 'Actual result differs from frozen oracle expectations')
                    elif actual is not None or not evaluation['evidence']:
                        issue('MANUAL_EVIDENCE', case['id'], 'Manual pass requires null result and evidence file')
            result['summary'].update(run_id=record['run_id'], candidate_id=candidate)
        counts = {s: sum(e['status'] == s for e in evaluations.values()) for s in ('pass', 'failed', 'blocked', 'unknown', 'skip')}
        untested = [dict(case_id=c['id'], trial=t, required=c['required']) for c in active for t in range(1, c['required_trials'] + 1) if (c['id'], t) not in evaluations]
        result['summary'].update(recorded_status_counts=counts, untested_trials=untested, evaluations=[dict(case_id=k[0], trial=k[1], status=v['status'], required=indexes['cases'][k[0]]['required'], excluded=k[0] in excluded) for k, v in sorted(evaluations.items())])
        if stage == 'acceptance':
            if not required:
                issue('NO_REQUIRED_CASES', 'cases', 'At least one active required case required')
            for case in required:
                for trial in range(1, case['required_trials'] + 1):
                    ev = evaluations.get((case['id'], trial))
                    if ev is None or ev['status'] != 'pass':
                        issue('REQUIRED_TRIAL', case['id'], f'Trial {trial} is ' + ('untested' if ev is None else ev['status']))
            for gap in project['gaps']:
                if gap['severity'] == 'blocker' and gap['status'] == 'open':
                    issue('OPEN_BLOCKER', gap['id'], gap['recovery_action'])
        result['exit_code'] = 1 if result['errors'] else 0
        result['ok'] = result['exit_code'] == 0
    except Invalid as exc:
        result['errors'].append(exc.issue)
    except (OSError, UnicodeError, RecursionError, ValueError, TypeError, RuntimeError) as exc:
        result['errors'].append(dict(code='INPUT_ERROR', path='project', message=str(exc)))
    return result


def manifest_digest(root):
    reader = Reader(root)
    raw = reader.read('project.json', MAX_JSON_BYTES, False)
    strict_json(raw, 'project.json')
    return hashlib.sha256(raw).hexdigest()


def emit(result, as_json=False):
    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print(f"{result['stage']}: {'PASS' if result['ok'] else 'INVALID' if result['exit_code'] == 2 else 'BLOCKED'} (recorded-evidence gate)")
        for key, value in result['summary'].items():
            print(f'{key}: {json.dumps(value, ensure_ascii=True)}')
        for kind in ('errors', 'warnings'):
            for issue in result[kind]:
                print(f"{kind}: {json.dumps(issue, ensure_ascii=True)}")
