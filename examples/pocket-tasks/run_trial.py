#!/usr/bin/env python3
"""Run an original, controlled browser regression trial into a NEW directory."""
import argparse
from datetime import datetime, timezone
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import platform
import sys
from pathlib import Path
import shutil
import subprocess
import threading


SOURCE = Path(__file__).resolve().parent
VARIANTS = ('buggy', 'mobile', 'persistence', 'feedback', 'fixed')


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def ref(root, path):
    return {'path': path, 'sha256': hashlib.sha256((root / path).read_bytes()).hexdigest()}


def project(root, enhanced):
    saved = {'tasks': ['Read a chapter'], 'error': '', 'input': ''}
    add = {'id': 'add', 'action': 'Save Read a chapter', 'state': saved}
    specs = [('add-task', 'exact_json', {'steps': [add]}, 'baseline.json')]
    if enhanced:
        specs += [('blank-feedback', 'journey_trace', {'steps': [{'id': 'blank', 'action': 'Submit blank task', 'state': {'tasks': [], 'error': 'Enter a task.', 'input': ''}}]}, 'feedback.json'),
                  ('save-reload', 'journey_trace', {'steps': [add, {'id': 'reload', 'action': 'Reload page', 'state': saved}]}, 'persistence.json')]
        for viewport, width, height in [('desktop', 960, 640), ('mobile', 390, 700)]:
            specs.append((f'{viewport}-layout', 'visual_pixels', {'baseline': ref(root, f'baselines/{viewport}.ppm'), 'width': width, 'height': height, 'max_channel_delta': 0, 'max_changed_pixels': 0}, f'{viewport}.ppm'))
    cases = []
    for name, kind, expected, result in specs:
        cases.append({'id': name, 'title': name, 'origin': 'original_synthetic_design', 'source_ids': [], 'authorship': 'Original controlled Pocket Tasks example.', 'command_ids': ['save-task'], 'preconditions': ['Fresh browser context; fixed viewport and local original app.'], 'steps': [f'Observe {name} using the original browser recorder.'], 'expected': 'Match frozen original contract.', 'fixtures': [], 'oracle': {'kind': kind, 'description': 'Compare recorded runtime evidence against frozen original expectation.', 'expected': expected}, 'required': True, 'required_trials': 1})
    packet_files = [ref(root, 'packet/contract.md')]
    for item in packet_files:
        item.update(role='specification' if item['path'].endswith('.md') else 'fixture', provenance='Original teaching design frozen before candidate runs.', source_ids=[])
    manifest = {'format_version': 1, 'project_id': 'pocket-tasks', 'title': 'Pocket Tasks controlled browser trial', 'scope': 'Add, blank feedback, reload persistence, and two blank-state viewports.' if enhanced else 'Add a valid task without reload.', 'target': {'name': 'Original Pocket Tasks design', 'version': '1', 'mode': 'original-synthetic'}, 'sources': [], 'commands': [{'id': 'save-task', 'description': 'Save a task', 'parameters': 'Task text', 'preconditions': ['Fresh browser context'], 'effects': ['Append and persist valid text'], 'errors': ['Show Enter a task. for blank input'], 'recovery': 'Enter valid text and retry.', 'access': 'Original local browser app', 'events': [], 'design_rationale': 'Small original deterministic trial.'}], 'cases': cases, 'exclusions': [], 'exclusion_note': 'No exclusions approved.', 'handoff': {'directory': 'packet', 'files': packet_files, 'reviewer': 'original-example-author', 'approved': True, 'attestation': 'Original synthetic design; author attestation, not independent clean-room certification.', 'exposure_notes': ['All source is original; deliberately seeded faults are known to the trial author.']}, 'gaps': []}
    write(root / 'project.json', manifest)
    return specs


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--node', default='node')
    parser.add_argument('--playwright-module', required=True, type=Path)
    parser.add_argument('--browser-executable', type=Path)
    args = parser.parse_args()
    output = args.output.absolute()
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(SOURCE):
        parser.error('output must be a NEW directory outside the example')
    try:
        from PIL import Image, __version__ as pillow_version
    except ImportError:
        parser.error('install optional runner dependency Pillow; validators need only Python stdlib')
    output.mkdir(parents=True)
    snapshot = output / 'source'
    snapshot.mkdir()
    for name in ('app.html', 'record.cjs', 'run_trial.py', 'contract.md'):
        shutil.copyfile(SOURCE / name, snapshot / name)
    (snapshot / 'validation').mkdir()
    for name in ('core.py', 'ui_checks.py', 'validate.py'):
        shutil.copyfile(SOURCE.parents[1] / 'skills/behavior-rebuild/scripts' / name, snapshot / 'validation' / name)
    frozen_sources = {str(path.relative_to(snapshot)): hashlib.sha256(path.read_bytes()).hexdigest() for path in snapshot.rglob('*') if path.is_file()}
    write(output / 'source-hashes.json', frozen_sources)
    handler = functools.partial(QuietHandler, directory=str(snapshot))
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}'
    def record(variant, folder):
        folder.mkdir()
        command = [args.node, str(snapshot / 'record.cjs'), str(args.playwright_module.resolve()), url, variant, str(folder)]
        if args.browser_executable:
            command.append(str(args.browser_executable.resolve()))
        subprocess.run(command, check=True, timeout=60)
        environment = json.loads((folder / 'environment.json').read_text())
        environment.update(python=platform.python_version(), pillow=pillow_version, platform=platform.platform())
        write(folder / 'environment.json', environment)
        for viewport in ('desktop', 'mobile'):
            with Image.open(folder / f'{viewport}.png') as image:
                rgb = image.convert('RGB')
                width, height = rgb.size
                (folder / f'{viewport}.ppm').write_bytes(f'P6\n{width} {height}\n255\n'.encode('ascii') + rgb.tobytes())
    try:
        # Freeze original reference screenshots and BOTH manifests before any candidate run.
        reference = output / 'reference'
        record('fixed', reference)
        specifications = {}
        for mode in ('baseline', 'enhanced'):
            root = output / mode
            (root / 'packet').mkdir(parents=True)
            (root / 'baselines').mkdir()
            (root / 'runs').mkdir()
            (root / 'results').mkdir()
            shutil.copyfile(snapshot / 'contract.md', root / 'packet/contract.md')
            for viewport in ('desktop', 'mobile'):
                shutil.copyfile(reference / f'{viewport}.ppm', root / f'baselines/{viewport}.ppm')
            specifications[mode] = project(root, mode == 'enhanced')
        frozen_manifests = {mode: ref(output / mode, 'project.json')['sha256'] for mode in specifications}
        write(output / 'frozen-before-candidates.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'sources': frozen_sources, 'manifests': frozen_manifests, 'environment': json.loads((reference / 'environment.json').read_text()), 'reference_images': [ref(output, f'reference/{view}.{extension}') for view in ('desktop', 'mobile') for extension in ('png', 'ppm')]})
        summary = {}
        for variant in VARIANTS:
            observed = output / variant
            record(variant, observed)
            summary[variant] = {}
            for mode, specs in specifications.items():
                root = output / mode
                shutil.copytree(observed, root / 'results' / variant)
                evaluations = []
                for case, kind, expected, filename in specs:
                    actual_path = root / 'results' / variant / filename
                    if kind == 'visual_pixels':
                        passed = actual_path.read_bytes() == (root / expected['baseline']['path']).read_bytes()
                    else:
                        passed = json.loads(actual_path.read_text()) == expected
                    evaluations.append({'case_id': case, 'trial': 1, 'status': 'pass' if passed else 'failed', 'oracle_status': 'available', 'result': ref(root, f'results/{variant}/{filename}'), 'evidence': [ref(root, f'results/{variant}/environment.json')] + ([ref(root, f'results/{variant}/{Path(filename).stem}.png')] if kind == 'visual_pixels' else []), 'review': {'reviewer': 'deterministic-original-trial', 'decision': 'accepted' if passed else 'rejected', 'notes': 'Automated controlled fault trial, no independent product certification.'}, 'notes': 'Observed headless browser output; frozen reference and source hashes accompany trial.'})
                run = {'format_version': 1, 'run_id': variant, 'manifest_sha256': frozen_manifests[mode], 'candidate_id': f'pocket-{variant}', 'created_at': datetime.now(timezone.utc).isoformat(), 'runner': 'pocket-tasks-browser-recorder', 'environment': (observed / 'environment.json').read_text().strip(), 'evaluations': evaluations}
                write(root / 'runs' / f'{variant}.json', run)
                summary[variant][mode] = {e['case_id']: e['status'] for e in evaluations}
        if frozen_sources != {name: ref(snapshot, name)['sha256'] for name in frozen_sources} or frozen_manifests != {mode: ref(output / mode, 'project.json')['sha256'] for mode in specifications}:
            raise RuntimeError('Frozen source or manifest changed during trial')
        write(output / 'summary.json', summary)
        # Independently invoke the portable acceptance gate; unexpected outcomes fail CI.
        validator = snapshot / 'validation/validate.py'
        gates = {}
        expected_failures = {'buggy': {'blank-feedback', 'save-reload', 'mobile-layout'}, 'mobile': {'mobile-layout'}, 'persistence': {'save-reload'}, 'feedback': {'blank-feedback'}, 'fixed': set()}
        for variant in VARIANTS:
            failures = {case for case, status in summary[variant]['enhanced'].items() if status != 'pass'}
            if failures != expected_failures[variant] or any(status != 'pass' for status in summary[variant]['baseline'].values()):
                raise RuntimeError(f'Unexpected detection result for {variant}')
            for mode in specifications:
                result = subprocess.run([sys.executable, str(validator), str(output / mode), '--stage', 'acceptance', '--run', f'runs/{variant}.json', '--candidate', f'pocket-{variant}', '--json'], capture_output=True, text=True, timeout=30)
                expected_code = 1 if mode == 'enhanced' and variant != 'fixed' else 0
                gates[f'{mode}/{variant}'] = {'exit_code': result.returncode, 'expected_exit_code': expected_code, 'stdout': result.stdout, 'stderr': result.stderr}
                write(output / 'gate-results.json', gates)
                if result.returncode != expected_code:
                    raise RuntimeError(f'Acceptance gate disagrees for {mode}/{variant}: {result.stdout} {result.stderr}')
        if frozen_sources != {name: ref(snapshot, name)['sha256'] for name in frozen_sources}:
            raise RuntimeError('Frozen evaluator or app changed during validation')
        print(json.dumps(summary, indent=2))
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
