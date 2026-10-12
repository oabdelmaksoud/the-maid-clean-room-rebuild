#!/usr/bin/env python3
"""Report explicit scope denominators, recorded statuses, and ranked gaps."""
import argparse
from core import emit, validate_project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_dir')
    parser.add_argument('--run')
    parser.add_argument('--candidate')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    stage = 'acceptance' if args.run is not None or args.candidate is not None else 'discover'
    result = validate_project(args.project_dir, stage, args.run, args.candidate)
    emit(result, args.json)
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
