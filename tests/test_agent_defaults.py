"""Defaults and launch regressions; no live agent, user config or credentials."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import agent_defaults as defaults

spec = importlib.util.spec_from_file_location("sidecar_wrapper", ROOT / "scripts/run-agent-with-tmux-signal.py")
wrapper = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = wrapper
spec.loader.exec_module(wrapper)


class AgentDefaultsTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory(dir=os.environ["SIDECAR_TEST_TMP"])
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.file = self.root / "defaults.toml"
        self.values = {"model": "chosen-model", "effort": "medium", "fast": False}
        self.brief = self.root / "BRIEF.md"

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/agent_defaults.py"),
                               "--defaults-file", str(self.file), *args],
                              capture_output=True, text=True)

    def test_missing_requires_setup_even_with_all_overrides(self):
        self.brief.write_text("agent_model: other\nagent_effort: high\nagent_fast: true\n")
        proc = self.cli("resolve", "--brief", str(self.brief))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("first-run setup required", proc.stderr)
        self.assertIn("--defaults-file <same-path> before setup", proc.stderr)
        self.assertFalse(self.file.exists())

    def test_first_run_writes_all_choices_and_replace_backs_up(self):
        proc = self.cli("setup", "--model", "chosen-model", "--effort", "medium", "--fast", "false")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(defaults.resolve(self.file), self.values)
        self.assertEqual(self.file.stat().st_mode & 0o777, 0o600)
        before = self.file.read_bytes()
        refused = self.cli("setup", "--model", "other", "--effort", "high", "--fast", "true")
        self.assertEqual(refused.returncode, 1)
        self.assertEqual(self.file.read_bytes(), before)
        proc = self.cli("setup", "--model", "other", "--effort", "high", "--fast", "true", "--replace")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        backups = list(self.root.glob("defaults.toml.backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), before)
        self.assertEqual(defaults.resolve(self.file), {"model": "other", "effort": "high", "fast": True})

    def test_setup_requires_explicit_three_choices(self):
        proc = self.cli("setup", "--model", "chosen-model", "--effort", "medium")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(self.file.exists())

    def test_override_all_and_partial_without_mutation(self):
        defaults.setup(self.file, self.values)
        before = self.file.read_bytes()
        self.brief.write_text("agent_model: other\nagent_effort: ultra\nagent_fast: true\n")
        proc = self.cli("resolve", "--brief", str(self.brief))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), {"model": "other", "effort": "ultra", "fast": True})
        self.brief.write_text("agent_fast: true\n")
        self.assertEqual(defaults.resolve(self.file, self.brief), {**self.values, "fast": True})
        self.assertEqual(self.file.read_bytes(), before)

    def test_invalid_brief_and_defaults_fail_closed_without_secret_output(self):
        defaults.setup(self.file, self.values)
        for body in ("agent_fast: yes\n", "agent_model:\n", "agent_fast: true\nagent_fast: false\n",
                     "agent_model = other\n", " agent_model: other\n", "\ufeffagent_fast: false\n",
                     "\u00a0agent_model: other\n", "\u2003agent_fast: false\n", "\u3000agent_effort: high\n",
                     "agent_effort: high;secret-marker\n"):
            with self.subTest(body=body):
                self.brief.write_text(body)
                proc = self.cli("resolve", "--brief", str(self.brief))
                self.assertEqual(proc.returncode, 1)
                self.assertNotIn("secret-marker", proc.stdout + proc.stderr)
        for body in ('[codex]\nmodel="secret-marker"\neffort="high"\nfast="false"\n',
                     '[codex]\nmodel="x"\n', 'secret-marker invalid TOML'):
            self.file.write_text(body)
            proc = self.cli("resolve")
            self.assertEqual(proc.returncode, 1)
            self.assertNotIn("secret-marker", proc.stdout + proc.stderr)

    def test_setup_refuses_empty_basename_without_traceback_or_writes(self):
        for name in ("", ".", "/"):
            with self.subTest(name=name):
                proc = subprocess.run([sys.executable, str(ROOT / "scripts/agent_defaults.py"),
                    "--defaults-file", name, "setup", "--model", "chosen-model", "--effort", "medium", "--fast", "false"],
                    cwd=self.root, capture_output=True, text=True)
                self.assertEqual(proc.returncode, 1)
                self.assertIn("STATUS: STUCK", proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_shared_path_normalization_includes_wrapper_and_brief(self):
        defaults.setup(self.file, self.values)
        self.brief.write_text("agent_model: job-choice\n")
        args = ["--agent-cmd", "codex exec -- prompt", "--session", "test", "--signal", "done",
                "--run-dir", str(self.root), "--timeout-sec", "5", "--defaults-file", "~/defaults.toml",
                "--brief", "~/BRIEF.md"]
        with patch.dict(os.environ, {"HOME": str(self.root)}), patch.object(wrapper, "resolve_tmux", return_value="/fixture/tmux"), patch.object(wrapper, "current_session", return_value="test"), patch.object(wrapper, "run_agent") as run:
            self.assertEqual(defaults.resolve(Path("~/defaults.toml"), Path("~/BRIEF.md"))["model"], "job-choice")
            wrapper.launch(args)
        self.assertIn('model="job-choice"', run.call_args.args[0])
        with patch.object(Path, "expanduser", side_effect=RuntimeError("secret-marker")):
            with self.assertRaisesRegex(defaults.ConfigError, "cannot be normalized"):
                defaults.resolve(self.file)

    def test_symlink_and_existing_setup_lock_refused(self):
        target = self.root / "owner"
        target.write_text("owner content")
        self.file.symlink_to(target)
        proc = self.cli("setup", "--model", "other", "--effort", "low", "--fast", "true", "--replace")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(target.read_text(), "owner content")
        self.file.unlink()
        lock = self.root / "defaults.toml.lock"
        lock.mkdir()
        with self.assertRaises(defaults.ConfigError):
            defaults.setup(self.file, self.values)
        self.assertTrue(lock.exists())
        self.assertFalse(self.file.exists())

    def test_preflight_uses_overrides_and_preserves_base_config(self):
        defaults.setup(self.file, self.values)
        executable = self.root / "codex"
        executable.write_text("#!/bin/sh\nprintf 'codex fixture\\n'\n")
        executable.chmod(0o700)
        auth = self.root / "auth.json"
        auth.write_text("secret-marker")
        config = self.root / "config.toml"
        original = 'model="machine-choice"\nmodel_reasoning_effort="low"\nsecret="secret-marker"\n'
        config.write_text(original)
        env = {**os.environ, "CODEX_HOME": str(self.root), "PATH": str(self.root) + os.pathsep + os.environ["PATH"]}
        self.brief.write_text("agent_model: job-choice\nagent_effort: high\nagent_fast: true\n")
        def preflight(*options):
            return subprocess.run([str(ROOT / "adapters/codex/preflight.sh"), "--defaults-file", str(self.file),
                                   "--brief", str(self.brief), *options], env=env, capture_output=True, text=True)
        proc = preflight()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('"model": "job-choice"', proc.stdout)
        self.assertIn('"fast": true', proc.stdout)
        self.assertNotIn("secret-marker", proc.stdout + proc.stderr)
        self.assertEqual(config.read_text(), original)
        self.assertEqual(preflight("--brief", "").returncode, 1)
        self.assertEqual(preflight("--defaults-file", "").returncode, 1)
        config.write_text("invalid secret-marker")
        proc = preflight()
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn("secret-marker", proc.stdout + proc.stderr)
        config.write_text(original)
        auth.unlink()
        self.assertEqual(preflight().returncode, 1)
        auth.mkdir()
        self.assertEqual(preflight().returncode, 1)

    def test_nonregular_inputs_refused_without_reading(self):
        defaults.setup(self.file, self.values)
        fifo = self.root / "pipe"
        os.mkfifo(fifo)
        with patch.object(Path, "read_text", side_effect=AssertionError("must not read FIFO")):
            for reader in (defaults.read_toml, defaults.brief_overrides, defaults.resolve):
                with self.subTest(reader=reader.__name__), self.assertRaises(defaults.ConfigError):
                    reader(fifo)

    def test_readback_failure_preserves_backup_and_reports_published_state(self):
        defaults.setup(self.file, self.values)
        original = self.file.read_bytes()
        with patch.object(defaults, "resolve", return_value={}):
            with self.assertRaisesRegex(defaults.ConfigError, "published but readback differs"):
                defaults.setup(self.file, {**self.values, "model": "other"}, replace=True)
        self.assertEqual(list(self.root.glob("defaults.toml.backup-*"))[0].read_bytes(), original)
        self.assertFalse((self.root / "defaults.toml.lock").exists())

    def test_wrapper_passes_resolved_settings_to_child(self):
        defaults.setup(self.file, self.values)
        self.brief.write_text("agent_model: job-choice\nagent_effort: high\nagent_fast: true\n")
        args = ["--agent-cmd", "codex exec --color never -- prompt", "--session", "test", "--signal", "done",
                "--run-dir", str(self.root), "--timeout-sec", "5", "--defaults-file", str(self.file),
                "--brief", str(self.brief)]
        with patch.object(wrapper, "resolve_tmux", return_value="/fixture/tmux"), patch.object(
                wrapper, "current_session", return_value="test"), patch.object(wrapper, "run_agent") as run:
            wrapper.launch(args)
        self.assertEqual(run.call_args.args[0], ["codex", "-c", 'model="job-choice"', "-c",
            'model_reasoning_effort="high"', "-c", 'service_tier="fast"', "-c", "features.fast_mode=true",
            "exec", "--color", "never", "--", "prompt"])
        off = defaults.codex_command(["codex", "exec", "--", "prompt"], self.values)
        self.assertIn('service_tier="default"', off)
        self.assertIn('features.fast_mode=false', off)

    def test_conflicting_flags_refused_before_prompt_delimiter(self):
        for flag in ("--model=other", "-mother", "--config", "-pother", "--enable=fast_mode", "--ignore-user-config"):
            with self.subTest(flag=flag), self.assertRaises(defaults.ConfigError):
                defaults.codex_command(["codex", "exec", flag, "prompt"], self.values)
        argv = defaults.codex_command(["codex", "exec", "--", "--model=prompt-text"], self.values)
        self.assertEqual(argv[-1], "--model=prompt-text")

    def test_refused_wrapper_still_writes_exits_and_bells_without_launch(self):
        args = ["--agent-cmd", "codex exec -- prompt", "--session", "test", "--signal", "done",
                "--run-dir", str(self.root), "--timeout-sec", "5", "--defaults-file", str(self.file)]
        with patch.object(wrapper, "notify") as bell, patch.object(wrapper, "run_agent") as run:
            self.assertEqual(wrapper.main(args), 2)
        run.assert_not_called()
        bell.assert_called_once()
        bodies = [(self.root / name).read_bytes() for name in ("exit.txt", "agent.exit", "codex.exit")]
        self.assertEqual(len(set(bodies)), 1)
        self.assertIn(b"first-run setup required", bodies[0])

    def test_uninspectable_defaults_path_still_writes_exits_before_bell(self):
        args = ["--agent-cmd", "codex exec -- prompt", "--session", "test", "--signal", "done",
                "--run-dir", str(self.root), "--timeout-sec", "5", "--defaults-file", str(self.file)]
        original = Path.exists
        def fail_selected(path):
            if path == self.file:
                raise OSError("secret-marker")
            return original(path)
        def check_before_bell(*unused):
            for name in ("exit.txt", "agent.exit", "codex.exit"):
                body = (self.root / name).read_text()
                self.assertIn("defaults path cannot be inspected", body)
                self.assertNotIn("secret-marker", body)
        with patch.object(Path, "exists", fail_selected), patch.object(wrapper, "notify", side_effect=check_before_bell) as bell, patch.object(wrapper, "run_agent") as run:
            self.assertEqual(wrapper.main(args), 2)
        run.assert_not_called()
        bell.assert_called_once()

    def test_non_codex_config_arguments_refused(self):
        args = ["--agent-cmd", "hermes run", "--session", "test", "--signal", "done",
                "--run-dir", str(self.root), "--timeout-sec", "5", "--defaults-file", str(self.file)]
        with self.assertRaisesRegex(wrapper.UsageError, "N/A"), patch.object(wrapper, "run_agent") as run:
            wrapper.launch(args)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
