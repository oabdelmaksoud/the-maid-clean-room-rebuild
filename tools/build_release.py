#!/usr/bin/env python3
"""Build deterministic release archives from the explicit reviewed file manifest."""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def selected_files(root):
    root = Path(root).resolve()
    manifest = root / 'release-files.txt'
    if manifest.is_symlink():
        raise ValueError('release manifest cannot be a symlink')
    entries = manifest.read_text(encoding='utf-8').splitlines()
    if not entries or len(entries) != len(set(entries)):
        raise ValueError('release manifest must be nonempty and unique')
    for entry in entries:
        parts = entry.split('/')
        if not entry or '\\' in entry or ':' in entry or '\x00' in entry or any(p in ('', '.', '..', '.git', '__pycache__') for p in parts) or PurePosixPath(entry).is_absolute():
            raise ValueError(f'unsafe release path: {entry!r}')
        path = root
        for part in parts:
            path = path / part
            if path.is_symlink():
                raise ValueError(f'symlink release path: {entry}')
        if not path.is_file():
            raise ValueError(f'not a regular release file: {entry}')
    actual = set()
    def walk(directory):
        for path in directory.iterdir():
            if path.name in ('.git', '__pycache__'):
                continue
            if path.is_symlink():
                raise ValueError(f'symlink in release tree: {path.relative_to(root)}')
            if path.is_dir():
                walk(path)
            elif path.is_file():
                actual.add(path.relative_to(root).as_posix())
            else:
                raise ValueError(f'nonregular release entry: {path.relative_to(root)}')
    walk(root)
    if actual != set(entries):
        raise ValueError(f'release manifest mismatch; unlisted={sorted(actual-set(entries))}; absent={sorted(set(entries)-actual)}')
    return sorted(entries)


def portable_skill_files(root, entries):
    """Select native command skills and enforce their shared-core dependency."""
    skill_entries = [p for p in entries if len(p.split('/')) >= 3
                     and p.split('/')[0] == 'skills'
                     and p.split('/')[1].startswith('the-maid-')]
    core = 'skills/the-maid-rebuild/SKILL.md'
    if core not in skill_entries:
        raise ValueError('portable skills require skills/the-maid-rebuild/SKILL.md')
    names = {p.split('/')[1] for p in skill_entries}
    for name in sorted(names):
        entry = f'skills/{name}/SKILL.md'
        if entry not in skill_entries:
            raise ValueError(f'missing skill entrypoint: {entry}')
        text = (root / entry).read_text(encoding='utf-8')
        frontmatter = re.match(r'\A---\n(.*?)\n---(?:\n|$)', text, re.DOTALL)
        if not frontmatter or not re.search(r'^name: ' + re.escape(name) + r'$', frontmatter[1], re.MULTILINE):
            raise ValueError(f'skill frontmatter name must match folder: {name}')
        if name != 'the-maid-rebuild':
            for link in ('../the-maid-rebuild/SKILL.md', '../the-maid-rebuild/references/commands.md'):
                if f']({link})' not in text:
                    raise ValueError(f'missing relative core link in {name}: {link}')
            if f'skills/{name}/agents/openai.yaml' not in skill_entries:
                raise ValueError(f'missing native command UI metadata: {name}')
    wrappers = names - {'the-maid-rebuild'}
    if wrappers:
        catalog_path = 'skills/the-maid-rebuild/references/commands.json'
        if catalog_path not in skill_entries or 'skills/the-maid-rebuild/references/commands.md' not in skill_entries:
            raise ValueError('native command wrappers require the shared command reference and catalog')
        catalog = json.loads((root / catalog_path).read_text(encoding='utf-8'))
        if not isinstance(catalog, dict) or catalog.get('schema_version') != 1 or catalog.get('core_skill') != 'the-maid-rebuild':
            raise ValueError('invalid native command catalog')
        commands = catalog.get('commands')
        if not isinstance(commands, list) or not all(isinstance(c, dict) for c in commands):
            raise ValueError('invalid native command catalog entries')
        catalog_names = [c.get('skill') for c in commands]
        if not all(isinstance(n, str) for n in catalog_names) or len(catalog_names) != len(set(catalog_names)) or set(catalog_names) != wrappers:
            raise ValueError('native command catalog must match the selected wrappers')
        for command in commands:
            if command.get('skill') != 'the-maid-' + str(command.get('mode')):
                raise ValueError('native command catalog mode must match its skill name')
    return skill_entries


def build(root, output):
    root = Path(root).resolve()
    output = Path(output).absolute()
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(root):
        raise ValueError('output must be a NEW directory outside the repository')
    entries = selected_files(root)
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    if len(version) > 32 or not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('VERSION must be a stable semantic version: MAJOR.MINOR.PATCH without leading zeroes')
    skill_entries = portable_skill_files(root, entries)
    output.mkdir(parents=True)
    archives = [(f'behavior-rebuild-kit-{version}.zip', entries, ''),
                (f'behavior-rebuild-skill-{version}.zip', skill_entries, 'skills/')]
    sums = []
    for name, files, strip in archives:
        with zipfile.ZipFile(output / name, 'w', compression=zipfile.ZIP_STORED) as archive:
            for entry in files:
                info = zipfile.ZipInfo(entry[len(strip):], date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, (root / entry).read_bytes())
        sums.append(f"{hashlib.sha256((output / name).read_bytes()).hexdigest()}  {name}")
    (output / 'SHA256SUMS').write_text('\n'.join(sums) + '\n', encoding='ascii')
    return [name for name, _, _ in archives]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        archives = build(ROOT, args.output)
    except (ValueError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    print('\n'.join(archives + ['SHA256SUMS']))


if __name__ == '__main__':
    main()
