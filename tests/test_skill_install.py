"""Install regression checks; all scratch files stay under SIDECAR_TEST_TMP."""

import os
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".cursor/skills/Cursor_sidecar"
INSTALL = ROOT / "scripts/install-skill.py"


class SkillInstallTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(dir=os.environ["SIDECAR_TEST_TMP"])
        self.addCleanup(self.scratch.cleanup)
        self.work = Path(self.scratch.name)

    def install(self, *args, script=INSTALL):
        return subprocess.run(
            [sys.executable, str(script), *map(str, args)],
            capture_output=True, text=True, check=False,
        )

    def test_tree_runs_without_repo(self):
        # A plain directory copy must carry both the launcher and preflights.
        isolated = self.work / "standalone"
        shutil.copytree(SKILL, isolated)
        for name in ("scripts/run-agent-with-tmux-signal.py",
                     "adapters/codex/preflight.sh", "adapters/hermes/preflight.sh",
                     "adapters/_template/preflight.sh", "docs/architecture.md"):
            self.assertTrue((isolated / name).is_file(), name)
        proc = subprocess.run(
            [sys.executable, str(isolated / "scripts/run-agent-with-tmux-signal.py"), "--help"],
            cwd=self.work, capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_install_complete_and_identical(self):
        dest = self.work / "installed skill"
        proc = self.install("--dest", dest)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        source_files = {p.relative_to(SKILL) for p in SKILL.rglob("*") if p.is_file()}
        installed_files = {p.relative_to(dest) for p in dest.rglob("*") if p.is_file()}
        self.assertEqual(source_files, installed_files)
        for name in source_files:
            self.assertEqual((SKILL / name).read_bytes(), (dest / name).read_bytes())
            self.assertEqual((SKILL / name).stat().st_mode & 0o777,
                             (dest / name).stat().st_mode & 0o777)
        self.assertTrue(os.access(dest / "adapters/codex/preflight.sh", os.X_OK))

    def test_refuses_nonempty_destination(self):
        dest = self.work / "existing"
        dest.mkdir()
        (dest / "SKILL.md").write_text("owner content\n")
        proc = self.install("--dest", dest)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("existing installs are never overwritten", proc.stderr)
        self.assertEqual((dest / "SKILL.md").read_text(), "owner content\n")
        self.assertEqual(list(dest.iterdir()), [dest / "SKILL.md"])

    def test_stale_bundle_fails_before_creating_destination(self):
        # Mutate a private fixture, never the checkout under review.
        repo = self.work / "repo"
        for name in ("scripts", "adapters", ".cursor/skills/Cursor_sidecar"):
            shutil.copytree(ROOT / name, repo / name)
        (repo / "docs").mkdir()
        shutil.copy2(ROOT / "docs/architecture.md", repo / "docs/architecture.md")
        (repo / ".cursor/skills/Cursor_sidecar/scripts/run-agent-with-tmux-signal.py").write_text("stale\n")
        dest = self.work / "must-not-exist"
        proc = self.install("--dest", dest, script=repo / "scripts/install-skill.py")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("bundle differs", proc.stderr)
        self.assertFalse(dest.exists())

    def test_collision_after_empty_check_preserves_file(self):
        spec = importlib.util.spec_from_file_location("sidecar_install", INSTALL)
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        dest = self.work / "race"
        dest.mkdir()
        original_iterdir = Path.iterdir

        def create_after_listing(path):
            entries = list(original_iterdir(path))
            if path == dest:
                (dest / "SKILL.md").write_text("concurrent owner content\n")
            return iter(entries)

        with patch.object(Path, "iterdir", create_after_listing), patch.object(
            sys, "argv", [str(INSTALL), "--dest", str(dest)]
        ):
            self.assertEqual(installer.main(), 1)
        self.assertEqual((dest / "SKILL.md").read_text(), "concurrent owner content\n")


if __name__ == "__main__":
    unittest.main()
