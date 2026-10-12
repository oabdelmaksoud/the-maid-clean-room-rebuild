#!/usr/bin/env python3
"""Generate recorded fixture evidence in an explicitly selected new directory."""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import shutil


def import_rows(path):
    staged = []
    with path.open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['item', 'amount']:
            raise ValueError('Unexpected header')
        for row in reader:
            if set(row) != {'item', 'amount'} or not row['item'] or row['amount'] is None:
                raise ValueError('Malformed row')
            try:
                amount = Decimal(row['amount'])
            except InvalidOperation as exc:
                raise ValueError('Invalid amount') from exc
            if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
                raise ValueError('Invalid amount')
            staged.append((row['item'], amount))
    return staged


def export_rows(rows, path):
    with path.open('x', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['item', 'amount'])
        writer.writerows((item, format(amount, '.2f')) for item, amount in rows)


def inspect_export(path):
    # Separate parser and integer-cents sum do not reuse transformation arithmetic.
    with path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.reader(stream))
    if rows[0] != ['item', 'amount']:
        raise ValueError('Oracle: export header differs')
    cents = 0
    for row in rows[1:]:
        whole, fractional = row[1].split('.')
        if len(fractional) != 2 or not whole.isdigit() or not fractional.isdigit():
            raise ValueError('Oracle: malformed exported amount')
        cents += int(whole) * 100 + int(fractional)
    return {'rows': len(rows) - 1, 'total': f'{cents // 100}.{cents % 100:02d}',
            'items': [row[0] for row in rows[1:]], 'amounts': [row[1] for row in rows[1:]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    destination = args.output.absolute()
    source = Path(__file__).resolve().parent
    if destination.exists() or destination.is_symlink():
        parser.error('output must be a NEW directory')
    if destination.resolve().is_relative_to(source):
        parser.error('output must be outside the canonical example')
    destination.mkdir(parents=True)
    shutil.copyfile(source / 'project.json', destination / 'project.json')
    shutil.copytree(source / 'packet', destination / 'packet')
    (destination / 'results').mkdir()
    (destination / 'runs').mkdir()
    rows = import_rows(destination / 'packet/fixtures/valid.csv')
    total = sum((amount for _, amount in rows), Decimal('0'))
    export_rows(rows, destination / 'results/export.csv')
    valid_result = inspect_export(destination / 'results/export.csv')
    if format(total, '.2f') != valid_result['total']:
        raise ValueError('Calculated total differs from independent export oracle')
    state = [('Existing', Decimal('9.00'))]
    before = list(state)
    rejected = False
    try:
        state = import_rows(destination / 'packet/fixtures/invalid.csv')
        export_rows(state, destination / 'results/invalid-export.csv')
    except ValueError:
        rejected = True
    invalid_result = {'rejected': rejected, 'unchanged': state == before,
                      'output_created': (destination / 'results/invalid-export.csv').exists()}
    project = json.loads((destination / 'project.json').read_text(encoding='utf-8'))
    evaluations = []
    def reference(path):
        return {'path': path, 'sha256': hashlib.sha256((destination / path).read_bytes()).hexdigest()}
    for case, actual in zip(project['cases'], [valid_result, invalid_result]):
        path = f"results/{case['id']}.json"
        (destination / path).write_text(json.dumps(actual, indent=2) + '\n', encoding='utf-8')
        passed = actual == case['oracle']['expected']
        evaluations.append({'case_id': case['id'], 'trial': 1,
                            'status': 'pass' if passed else 'failed', 'oracle_status': 'available',
                            'result': reference(path),
                            'evidence': [reference('results/export.csv')] if case['id'] == 'valid-export' else [],
                            'review': {'reviewer': 'deterministic-demo-oracle',
                                       'decision': 'accepted' if passed else 'rejected',
                                       'notes': 'Automated synthetic fixture check; no human or product certification.'},
                            'notes': 'Original local demo execution; limited to this fixture outcome.'})
    run = {'format_version': 1, 'run_id': 'demo',
           'manifest_sha256': hashlib.sha256((destination / 'project.json').read_bytes()).hexdigest(),
           'candidate_id': 'demo-v1', 'created_at': datetime.now(timezone.utc).isoformat(),
           'runner': 'original-delimited-notebook-demo', 'environment': 'Python standard library, local synthetic files',
           'evaluations': evaluations}
    (destination / 'runs/demo.json').write_text(json.dumps(run, indent=2) + '\n', encoding='utf-8')
    print(f'Generated {destination}; run=runs/demo.json candidate=demo-v1')
    return 0 if all(e['status'] == 'pass' for e in evaluations) else 1


if __name__ == '__main__':
    raise SystemExit(main())
