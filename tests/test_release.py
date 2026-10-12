import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_release', ROOT / 'tools/build_release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        (self.root / 'skills/the-maid-rebuild').mkdir(parents=True)
        (self.root / 'VERSION').write_text('0.2.0\n')
        (self.root / 'skills/the-maid-rebuild/SKILL.md').write_text('---\nname: the-maid-rebuild\ndescription: Test shared core.\n---\nOriginal test fixture\n')
        self.entries = ['VERSION', 'release-files.txt', 'skills/the-maid-rebuild/SKILL.md']
        (self.root / 'release-files.txt').write_text('\n'.join(self.entries) + '\n')

    def test_exact_archives_and_reproducibility(self):
        one, two = Path(self.temp.name) / 'one', Path(self.temp.name) / 'two'
        names = release.build(self.root, one)
        release.build(self.root, two)
        self.assertEqual(names, ['behavior-rebuild-kit-0.2.0.zip', 'behavior-rebuild-skill-0.2.0.zip'])
        for name in names + ['SHA256SUMS']:
            self.assertEqual((one / name).read_bytes(), (two / name).read_bytes())
        with zipfile.ZipFile(one / names[0]) as archive:
            self.assertEqual(archive.namelist(), sorted(self.entries))
            for info in archive.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
        with zipfile.ZipFile(one / names[1]) as archive:
            self.assertEqual(archive.namelist(), ['the-maid-rebuild/SKILL.md'])

    def add_wrapper(self):
        wrapper = self.root / 'skills/the-maid-status'
        (wrapper / 'agents').mkdir(parents=True)
        (wrapper / 'SKILL.md').write_text('---\nname: the-maid-status\ndescription: Read status.\n---\n[Core](../the-maid-rebuild/SKILL.md)\n[Modes](../the-maid-rebuild/references/commands.md)\n')
        (wrapper / 'agents/openai.yaml').write_text('interface:\n  display_name: "The Maid - Status"\n')
        refs = self.root / 'skills/the-maid-rebuild/references'
        refs.mkdir()
        (refs / 'commands.md').write_text('## status\nRead only.\n')
        (refs / 'commands.json').write_text(json.dumps({'schema_version': 1, 'core_skill': 'the-maid-rebuild', 'commands': [{'skill': 'the-maid-status', 'mode': 'status'}]}))
        self.entries += ['skills/the-maid-status/SKILL.md', 'skills/the-maid-status/agents/openai.yaml', 'skills/the-maid-rebuild/references/commands.md', 'skills/the-maid-rebuild/references/commands.json']
        (self.root / 'release-files.txt').write_text('\n'.join(self.entries) + '\n')
        return wrapper

    def test_wrapper_archive_includes_shared_dependency_reproducibly(self):
        self.add_wrapper()
        one, two = Path(self.temp.name) / 'one', Path(self.temp.name) / 'two'
        names = release.build(self.root, one)
        release.build(self.root, two)
        for name in names + ['SHA256SUMS']:
            self.assertEqual((one / name).read_bytes(), (two / name).read_bytes())
        with zipfile.ZipFile(one / names[1]) as archive:
            self.assertEqual(archive.namelist(), sorted(p[len('skills/'):] for p in self.entries if p.startswith('skills/')))
            self.assertIn('the-maid-rebuild/SKILL.md', archive.namelist())
            self.assertIn('the-maid-status/SKILL.md', archive.namelist())

    def test_wrapper_without_core_rejected_before_output(self):
        self.add_wrapper()
        core = 'skills/the-maid-rebuild/SKILL.md'
        (self.root / core).unlink()
        self.entries.remove(core)
        (self.root / 'release-files.txt').write_text('\n'.join(self.entries) + '\n')
        output = Path(self.temp.name) / 'out'
        with self.assertRaisesRegex(ValueError, 'require skills/the-maid-rebuild/SKILL.md'):
            release.build(self.root, output)
        self.assertFalse(output.exists())

    def test_wrapper_name_and_core_link_required(self):
        wrapper = self.add_wrapper()
        path = wrapper / 'SKILL.md'
        original = path.read_text()
        for contents, message in [(original.replace('name: the-maid-status', 'name: other'), 'frontmatter'), (original.replace('../the-maid-rebuild/SKILL.md', '../wrong/SKILL.md'), 'relative core link')]:
            with self.subTest(message=message):
                path.write_text(contents)
                with self.assertRaisesRegex(ValueError, message):
                    release.build(self.root, Path(self.temp.name) / 'out')

    def test_catalog_cannot_omit_a_packaged_wrapper(self):
        self.add_wrapper()
        catalog = self.root / 'skills/the-maid-rebuild/references/commands.json'
        data = json.loads(catalog.read_text())
        data['commands'] = []
        catalog.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'catalog must match'):
            release.build(self.root, Path(self.temp.name) / 'out')

    def test_repository_command_entrypoints_and_links(self):
        entries = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / 'skills').rglob('*') if path.is_file() and '__pycache__' not in path.parts)
        selected = release.portable_skill_files(ROOT, entries)
        catalog = json.loads((ROOT / 'skills/the-maid-rebuild/references/commands.json').read_text())
        self.assertEqual({c['mode'] for c in catalog['commands']}, {'discover', 'rea', 'spec', 'ready', 'build', 'validate', 'repair', 'status', 'all'})
        for command in catalog['commands']:
            self.assertIn(f"skills/{command['skill']}/SKILL.md", selected)

    def test_reject_unsafe_or_malformed_version(self):
        for version in ['../0.2.0', '/0.2.0', '0.2.0/other', '01.2.0', '0.2', 'v0.2.0', '0.2.0\nextra', '0.2.0-beta', '9' * 33 + '.0.0']:
            with self.subTest(version=version):
                (self.root / 'VERSION').write_text(version)
                output = Path(self.temp.name) / 'out'
                with self.assertRaises(ValueError):
                    release.build(self.root, output)
                self.assertFalse(output.exists())

    def test_reject_unlisted(self):
        (self.root / 'unreviewed.txt').write_text('not selected')
        with self.assertRaises(ValueError):
            release.build(self.root, Path(self.temp.name) / 'out')

    def test_reject_unsafe_manifest(self):
        for entry in ['../x', '/x', 'a\\b', '.git/config', 'a//b', 'C:/x']:
            with self.subTest(entry=entry):
                (self.root / 'release-files.txt').write_text(entry + '\n')
                with self.assertRaises(ValueError):
                    release.selected_files(self.root)

    def test_reject_existing_or_inside_output(self):
        for path in [self.root, self.root / 'dist']:
            with self.assertRaises(ValueError):
                release.build(self.root, path)

    def test_reject_symlink_or_nonfile(self):
        path = self.root / 'skills/the-maid-rebuild/SKILL.md'
        path.unlink()
        try:
            path.symlink_to(self.root / 'VERSION')
        except OSError:
            path.mkdir()
        with self.assertRaises(ValueError):
            release.selected_files(self.root)


if __name__ == '__main__':
    unittest.main()
