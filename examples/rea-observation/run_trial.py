"""Original synthetic PNG and reviewed behavior records; no actual REA/target run."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'skills/the-maid-rebuild/scripts'))
from rea import validate_rea


def synthetic_png(width=2, height=2):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\x00' + b'\x20\x80\xc0' * width) * height)) + chunk(b'IEND', b''))


class Fixture:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        capture = self.ref('evaluator/capture.png', synthetic_png())
        behavior = self.ref('behavior/continue.json', json.dumps(dict(format_version=1,
            target_id='synthetic-form', observation_id='continue-state', kind='sanitized_behavior',
            behavior='Original synthetic form: Continue remains disabled while the input is empty.')).encode())
        self.record = dict(format_version=1,
            target=dict(id='synthetic-form', version='original-synthetic-1', origin='https://synthetic.example', allowed_origins=['https://synthetic.example']),
            tool=dict(name='rea', version='6.4.0', operation='capture_web_screenshot'),
            permission=dict(reviewer='scope-reviewer', observe='allowed', basis='Original authored synthetic fixture only.',
                scope='Synthetic rendered form with no account information.', source_boundary='rendered_ui_only'),
            captures=[dict(id='empty-form', target_id='synthetic-form', origin='https://synthetic.example', artifact=capture,
                width=2, height=2, disposition='evaluator_only')],
            observations=[dict(id='continue-state', target_id='synthetic-form', capture_ids=['empty-form'], artifact=behavior,
                review=dict(reviewer='behavior-reviewer', disposition='approved_behavior', sanitized=True,
                    basis='Reviewed original synthetic description; no image bytes, assets or source.'))],
            handoff=dict(approved=True, reviewer='handoff-reviewer', observation_ids=['continue-state'], files=[behavior]))
        self.freeze()

    def ref(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return dict(path=name, sha256=hashlib.sha256(data).hexdigest())

    def freeze(self):
        (self.root / 'rea-evidence.json').write_text(json.dumps(self.record, indent=2))

def run_trials(root):
    root = Path(root)
    results = {}
    for label in ('source-operation', 'capture-handoff', 'reviewed-behavior'):
        fixture = Fixture(root / label)
        if label == 'source-operation':
            fixture.record['tool']['operation'] = 'analyze_web_bundle'
        elif label == 'capture-handoff':
            fixture.record['handoff']['files'].append(fixture.record['captures'][0]['artifact'])
        fixture.freeze()
        result = validate_rea(fixture.root)
        results[label] = dict(exit_code=result['exit_code'], errors=[e['code'] for e in result['errors']])
    summary = dict(synthetic=True, actual_rea_execution=False, trials=results)
    (root / 'results.json').write_text(json.dumps(summary, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output')
    args = parser.parse_args()
    if args.output:
        destination = Path(args.output)
        try:
            destination.mkdir(parents=True, exist_ok=False)
        except OSError as exc:
            parser.error('Output must be a new directory: ' + str(exc))
        result = run_trials(destination)
    else:
        with tempfile.TemporaryDirectory() as root:
            result = run_trials(root)
    print(json.dumps(result, indent=2))
    codes = [result['trials'][k]['exit_code'] for k in ('source-operation', 'capture-handoff', 'reviewed-behavior')]
    return 0 if codes == [1, 1, 0] else 1


if __name__ == '__main__':
    raise SystemExit(main())
