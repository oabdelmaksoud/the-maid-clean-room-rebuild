import importlib.util
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
        (self.root / 'skills/behavior-rebuild').mkdir(parents=True)
        (self.root / 'VERSION').write_text('0.1.0\n')
        (self.root / 'skills/behavior-rebuild/SKILL.md').write_text('Original test fixture\n')
        self.entries = ['VERSION', 'release-files.txt', 'skills/behavior-rebuild/SKILL.md']
        (self.root / 'release-files.txt').write_text('\n'.join(self.entries) + '\n')

    def test_exact_archives_and_reproducibility(self):
        one, two = Path(self.temp.name) / 'one', Path(self.temp.name) / 'two'
        names = release.build(self.root, one)
        release.build(self.root, two)
        for name in names + ['SHA256SUMS']:
            self.assertEqual((one / name).read_bytes(), (two / name).read_bytes())
        with zipfile.ZipFile(one / names[0]) as archive:
            self.assertEqual(archive.namelist(), sorted(self.entries))
            for info in archive.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
        with zipfile.ZipFile(one / names[1]) as archive:
            self.assertEqual(archive.namelist(), ['behavior-rebuild/SKILL.md'])

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
        path = self.root / 'skills/behavior-rebuild/SKILL.md'
        path.unlink()
        try:
            path.symlink_to(self.root / 'VERSION')
        except OSError:
            path.mkdir()
        with self.assertRaises(ValueError):
            release.selected_files(self.root)


if __name__ == '__main__':
    unittest.main()
