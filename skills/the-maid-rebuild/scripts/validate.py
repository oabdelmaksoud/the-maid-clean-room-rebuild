#!/usr/bin/env python3
"""Validate one explicit evidence stage or print the raw manifest digest."""
import argparse
import json
from core import Invalid, emit, manifest_digest, validate_project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_dir')
    parser.add_argument('--stage', choices=['discover', 'handoff', 'acceptance'])
    parser.add_argument('--run')
    parser.add_argument('--candidate')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--digest', action='store_true')
    args = parser.parse_args()
    if args.digest:
        if args.stage or args.run or args.candidate:
            parser.error('--digest cannot be combined with stage, run, or candidate')
        try:
            digest = manifest_digest(args.project_dir)
            print(json.dumps({'manifest_sha256': digest}) if args.json else digest)
            return 0
        except (Invalid, OSError, ValueError, RecursionError, RuntimeError) as exc:
            issue = exc.issue if isinstance(exc, Invalid) else dict(code='INPUT_ERROR', path='project', message=str(exc))
            emit(dict(format_version=1, stage='digest', ok=False, exit_code=2, manifest_sha256=None, errors=[issue], warnings=[], summary={}), args.json)
            return 2
    result = validate_project(args.project_dir, args.stage or 'discover', args.run, args.candidate)
    emit(result, args.json)
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
