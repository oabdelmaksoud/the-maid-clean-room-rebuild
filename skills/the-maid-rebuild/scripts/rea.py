"""Offline REA observation record gate; never invokes REA or accesses a target."""
import argparse
import hashlib
import ipaddress
import json
import re
import struct
from urllib.parse import urlsplit
import zlib

from core import (Invalid, MAX_JSON_BYTES, Reader, array, boolean, enum, fail,
                  ident, integer, shape, strict_json, strings, text)

MAX_PNG_DIMENSION = 8192
MAX_PNG_PIXELS = 16 * 1024 * 1024


def origin(value, path):
    text(value, path)
    try:
        parsed = urlsplit(value)
        hostname, port = parsed.hostname, parsed.port
        host = hostname
        if hostname and ':' in hostname:
            host = '[' + str(ipaddress.IPv6Address(hostname)) + ']'
        valid_host = hostname and (':' in hostname or re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)*', hostname))
        authority = host + (':' + str(port) if port is not None else '') if host else ''
        # Explicit default ports are preserved, never normalized to absent ports.
        canonical = parsed.scheme + '://' + authority
        valid_scheme = parsed.scheme == 'https' or (parsed.scheme == 'http' and hostname in ('localhost', '127.0.0.1', '::1'))
        if (not valid_scheme or not valid_host or (port is not None and not 1 <= port <= 65535)
                or parsed.username is not None or parsed.password is not None
                or parsed.path or parsed.query or parsed.fragment
                or any(c.isspace() for c in value) or value != canonical):
            raise ValueError('Origin does not match canonical permitted form')
    except ValueError:
        fail('UNSAFE_ORIGIN', path, 'Expected canonical HTTPS origin or HTTP loopback origin; optional port 1..65535, no userinfo, path, query, fragment or whitespace')



def png_header(raw, width, height, path):
    # Identity/header validation only: no image decoding or decompression.
    if len(raw) < 33 or raw[:8] != b'\x89PNG\r\n\x1a\n' or raw[8:16] != b'\x00\x00\x00\rIHDR':
        fail('PNG_HEADER', path, 'Expected PNG signature and first 13-byte IHDR')
    if zlib.crc32(raw[12:29]) & 0xffffffff != struct.unpack('>I', raw[29:33])[0]:
        fail('PNG_HEADER', path, 'IHDR checksum differs')
    w, h, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', raw[16:29])
    if not (1 <= w <= MAX_PNG_DIMENSION and 1 <= h <= MAX_PNG_DIMENSION and w * h <= MAX_PNG_PIXELS):
        fail('PNG_BOUNDS', path, 'PNG dimensions exceed bounded header policy')
    valid_depths = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
    if depth not in valid_depths.get(color, ()) or compression != 0 or filtering != 0 or interlace not in (0, 1):
        fail('PNG_HEADER', path, 'Invalid PNG IHDR fields')
    if (w, h) != (width, height):
        fail('PNG_DIMENSIONS', path, 'Recorded dimensions differ from PNG header')


def validate_rea(root):
    result = dict(format_version=1, stage='rea', ok=False, exit_code=2,
                  manifest_sha256=None, errors=[], warnings=[], summary={})

    def blocked(code, path, message):
        result['errors'].append(dict(code=code, path=path, message=message))

    try:
        reader = Reader(root)
        raw = reader.read('rea-evidence.json', MAX_JSON_BYTES, False)
        record = strict_json(raw, 'rea-evidence.json')
        result['manifest_sha256'] = hashlib.sha256(raw).hexdigest()
        shape(record, 'format_version target tool permission captures observations handoff', 'rea')
        integer(record['format_version'], 1, 1, 'format_version')
        target = record['target']
        shape(target, 'id version origin allowed_origins', 'target')
        ident(target['id'], 'target.id')
        text(target['version'], 'target.version')
        origin(target['origin'], 'target.origin')
        strings(target['allowed_origins'], 'target.allowed_origins', nonempty=True)
        if len(set(target['allowed_origins'])) != len(target['allowed_origins']):
            fail('DUPLICATE_REFERENCE', 'target.allowed_origins', 'Duplicate origin')
        for item in target['allowed_origins']:
            origin(item, 'target.allowed_origins')
        if target['origin'] not in target['allowed_origins']:
            blocked('ORIGIN_NOT_ALLOWED', 'target.origin', 'Target origin absent from recorded allowlist')
        tool = record['tool']
        shape(tool, 'name version operation', 'tool')
        enum(tool['name'], 'rea', 'tool.name')
        text(tool['version'], 'tool.version')
        enum(tool['operation'], 'capture_web_screenshot compare_web_screenshots inspect_web_page analyze_web_bundle', 'tool.operation')
        if tool['version'] != '6.4.0' or tool['operation'] != 'capture_web_screenshot':
            blocked('TOOL_BOUNDARY', 'tool', 'This gate supports only recorded REA 6.4.0 capture_web_screenshot')
        permission = record['permission']
        shape(permission, 'reviewer observe basis scope source_boundary', 'permission')
        for key in ('basis', 'scope'):
            text(permission[key], 'permission.' + key)
        text(permission['reviewer'], 'permission.reviewer', empty=True)
        enum(permission['observe'], 'allowed denied unknown', 'permission.observe')
        enum(permission['source_boundary'], 'rendered_ui_only proprietary_source network code credentials', 'permission.source_boundary')
        if permission['observe'] != 'allowed' or not permission['reviewer'].strip():
            blocked('OBSERVATION_PERMISSION', 'permission', 'Explicit reviewer and permitted observation required')
        if permission['source_boundary'] != 'rendered_ui_only':
            blocked('SOURCE_BOUNDARY', 'permission.source_boundary', 'Source, network, code and credential inspection are excluded')

        def records(values, path):
            array(values, path)
            out = {}
            for item in values:
                if not isinstance(item, dict) or 'id' not in item:
                    fail('SHAPE', path, 'Record requires id')
                ident(item['id'], path + '.id')
                if item['id'] in out:
                    fail('DUPLICATE_ID', path, item['id'])
                out[item['id']] = item
            return out

        captures = records(record['captures'], 'captures')
        observations = records(record['observations'], 'observations')
        capture_paths, capture_hashes = set(), set()
        for capture in captures.values():
            path = 'captures.' + capture['id']
            shape(capture, 'id target_id origin artifact width height disposition', path)
            ident(capture['target_id'], path + '.target_id')
            origin(capture['origin'], path + '.origin')
            if capture['target_id'] != target['id'] or capture['origin'] != target['origin']:
                blocked('TARGET_MISMATCH', path, 'Capture must identify the exact target and origin')
            enum(capture['disposition'], 'evaluator_only', path + '.disposition')
            integer(capture['width'], 1, MAX_PNG_DIMENSION, path + '.width')
            integer(capture['height'], 1, MAX_PNG_DIMENSION, path + '.height')
            data = reader.ref(capture['artifact'], path + '.artifact')
            if not capture['artifact']['path'].endswith('.png'):
                fail('PNG_EXTENSION', path, 'Capture must use .png extension')
            png_header(data, capture['width'], capture['height'], path)
            if capture['artifact']['path'] in capture_paths:
                fail('DUPLICATE_REFERENCE', path, 'Duplicate capture file')
            capture_paths.add(capture['artifact']['path'])
            capture_hashes.add(capture['artifact']['sha256'])
        if not captures or not observations:
            blocked('EVIDENCE_MISSING', 'rea', 'Capture and behavioral observation required')
        artifacts = {}
        for observation in observations.values():
            path = 'observations.' + observation['id']
            shape(observation, 'id target_id capture_ids artifact review', path)
            ident(observation['target_id'], path + '.target_id')
            strings(observation['capture_ids'], path + '.capture_ids', ids=True, nonempty=True)
            if not set(observation['capture_ids']) <= set(captures):
                fail('UNKNOWN_REFERENCE', path, 'Unknown capture ID')
            if observation['target_id'] != target['id']:
                blocked('TARGET_MISMATCH', path, 'Observation belongs to another target')
            artifact = observation['artifact']
            data = reader.ref(artifact, path + '.artifact')
            if artifact['path'] in capture_paths or artifact['sha256'] in capture_hashes:
                blocked('RAW_ASSET', path, 'Capture bytes cannot be a behavioral record')
            body = strict_json(data, artifact['path'])
            shape(body, 'format_version target_id observation_id kind behavior', artifact['path'])
            integer(body['format_version'], 1, 1, artifact['path'])
            enum(body['kind'], 'sanitized_behavior', artifact['path'] + '.kind')
            text(body['behavior'], artifact['path'] + '.behavior')
            if body['target_id'] != target['id'] or body['observation_id'] != observation['id']:
                blocked('TARGET_MISMATCH', path + '.artifact', 'Behavior record target and observation identity must agree')
            review = observation['review']
            shape(review, 'reviewer disposition sanitized basis', path + '.review')
            text(review['reviewer'], path + '.review.reviewer', empty=True)
            text(review['basis'], path + '.review.basis')
            boolean(review['sanitized'], path + '.review.sanitized')
            enum(review['disposition'], 'approved_behavior excluded unreviewed', path + '.review.disposition')
            if review['disposition'] == 'unreviewed' or not review['reviewer'].strip():
                blocked('OBSERVATION_UNREVIEWED', path, 'Each observation requires an explicit review disposition')
            if review['disposition'] == 'approved_behavior' and not review['sanitized']:
                blocked('NOT_SANITIZED', path, 'Approved behavior requires recorded sanitization review')
            if artifact['path'] in artifacts:
                fail('DUPLICATE_REFERENCE', path, 'Behavior records require separate artifacts')
            artifacts[artifact['path']] = artifact
        handoff = record['handoff']
        shape(handoff, 'approved reviewer observation_ids files', 'handoff')
        boolean(handoff['approved'], 'handoff.approved')
        text(handoff['reviewer'], 'handoff.reviewer', empty=True)
        strings(handoff['observation_ids'], 'handoff.observation_ids', ids=True, nonempty=True)
        if not handoff['approved'] or not handoff['reviewer'].strip():
            blocked('HANDOFF_APPROVAL', 'handoff', 'Explicit approved behavior handoff and reviewer required')
        expected = {}
        for item in handoff['observation_ids']:
            if item not in observations:
                fail('UNKNOWN_REFERENCE', 'handoff.observation_ids', item)
            observation = observations[item]
            if observation['review']['disposition'] != 'approved_behavior' or not observation['review']['sanitized']:
                blocked('HANDOFF_DISPOSITION', item, 'Only approved sanitized behavior observations may enter handoff')
            expected[observation['artifact']['path']] = observation['artifact']
        array(handoff['files'], 'handoff.files')
        actual = {}
        for artifact in handoff['files']:
            reader.ref(artifact, 'handoff.files')
            if artifact['path'] in actual:
                fail('DUPLICATE_REFERENCE', 'handoff.files', artifact['path'])
            actual[artifact['path']] = artifact
            if artifact['path'] in capture_paths or artifact['sha256'] in capture_hashes:
                blocked('CAPTURE_HANDOFF', 'handoff.files', 'Evaluator-only captures cannot be handed off, including renamed copies')
        if actual != expected:
            blocked('HANDOFF_FILE_SET', 'handoff.files', 'Files must equal the exact approved behavior records; no additional assets')
        result['summary'] = dict(target_id=target['id'], captures=len(captures), observations=len(observations),
            approved_handoff_observation_ids=handoff['observation_ids'], evidence_gate='record agreement only',
            limits=['No network, target execution, REA invocation or SDK dependency.',
                    'Hashes bind local bytes; records do not prove captures came from REA or the actual target.',
                    'Review and permission declarations are not authenticated.',
                    'No semantic secret scanning, copied-content detection or full PNG decoding.'])
        result['exit_code'] = 1 if result['errors'] else 0
        result['ok'] = result['exit_code'] == 0
    except Invalid as exc:
        result['errors'].append(exc.issue)
    except (OSError, UnicodeError, RecursionError, ValueError, TypeError, RuntimeError, AttributeError) as exc:
        result['errors'].append(dict(code='INPUT_ERROR', path='rea', message=str(exc)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_dir')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    result = validate_rea(args.project_dir)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print('rea: ' + ('PASS' if result['ok'] else 'INVALID' if result['exit_code'] == 2 else 'BLOCKED') + ' (record agreement only)')
        print(json.dumps(result, indent=2, ensure_ascii=True))
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
