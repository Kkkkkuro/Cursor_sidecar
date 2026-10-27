#!/usr/bin/env python3
"""Probe the installed skill wrapper with real tmux and a fixture named codex.

No agent CLI or GBrain is launched. All fixtures, the private tmux socket and
readbacks stay in a new or empty --run-dir. A tmux proxy reads the exit files
at the signal call, before forwarding that call to the real absolute binary.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wrapper", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("normal", "timeout"), required=True)
    args = parser.parse_args()
    root = args.run_dir.expanduser().absolute()
    wrapper = args.wrapper.expanduser().resolve(strict=True)
    real_tmux = shutil.which("tmux")
    if not real_tmux:
        parser.error("tmux not found")
    real_tmux = str(Path(real_tmux).resolve())
    if root.is_symlink() or (root.exists() and (not root.is_dir() or any(root.iterdir()))):
        parser.error("run-dir must be new or empty")
    socket = root / "tmux.sock"
    if len(os.fsencode(socket)) > 100:
        parser.error("run-dir is too long for a Unix tmux socket")
    root.mkdir(parents=True, exist_ok=True)
    before_hash = digest(wrapper)
    fixture = root / "codex"
    fixture.write_text(
        f"#!{sys.executable}\nimport sys, time\n"
        "if sys.argv[1] == 'timeout': time.sleep(60)\n"
        "sys.exit(7)\n", encoding="utf-8",
    )
    fixture.chmod(0o700)
    proxy = root / "tmux-proxy"
    proxy.write_text(
        f"#!{sys.executable}\n"
        "import hashlib, json, os, sys, time\nfrom pathlib import Path\n"
        f"root = Path({str(root)!r})\nreal = {real_tmux!r}\n"
        "argv = sys.argv[1:]\n"
        "with (root / 'tmux-calls.jsonl').open('a') as f:\n"
        "    f.write(json.dumps({'executable': str(Path(sys.argv[0]).absolute()), 'argv': argv}) + '\\n')\n"
        "if 'wait-for' in argv and '-S' in argv[argv.index('wait-for') + 1:]:\n"
        "    files = {}\n"
        "    for name in ('exit.txt', 'agent.exit', 'codex.exit'):\n"
        "        path = root / name\n"
        "        data = path.read_bytes()\n"
        "        files[name] = {'text': data.decode(), 'sha256': hashlib.sha256(data).hexdigest(), 'mtime_ns': path.stat().st_mtime_ns}\n"
        "    event = {'files': files, 'readback_ns': time.time_ns(), 'before_signal_forward': True, 'real_tmux': real, 'argv': argv}\n"
        "    (root / 'at-signal.json').write_text(json.dumps(event, indent=2) + '\\n')\n"
        "os.execv(real, [real, *argv])\n", encoding="utf-8",
    )
    proxy.chmod(0o700)
    env = os.environ.copy()
    # The controller never contacts the tmux server running this task.
    env.pop("TMUX", None)
    env.pop("TMUX_PANE", None)
    base = [real_tmux, "-S", str(socket)]
    session = "so19-" + args.mode
    signal_name = session + "-done"
    waiter = None
    server_started = False
    log = (root / "wrapper.log").open("w")
    try:
        # Keep this private server alive after the short-lived agent pane exits.
        subprocess.run(base + ["-f", "/dev/null", "new-session", "-d", "-s", "control",
                               "--", "/bin/sleep", "60"], env=env, check=True, timeout=10)
        server_started = True
        waiter = subprocess.Popen(base + ["wait-for", signal_name], env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        timeout = "0.25" if args.mode == "timeout" else "5"
        launch = base + ["new-session", "-d", "-s", session, "--", "env",
                         f"TMUX_BIN={proxy}", sys.executable, str(wrapper),
                         "--agent-cmd", shlex.join([str(fixture), args.mode]),
                         "--session", session, "--signal", signal_name,
                         "--run-dir", str(root), "--timeout-sec", timeout]
        (root / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
        subprocess.run(launch, env=env, stdout=log, stderr=log, check=True, timeout=10)
        stdout, stderr = waiter.communicate(timeout=20)
        if waiter.returncode:
            raise RuntimeError(f"waiter failed ({waiter.returncode}): {stderr}")
        event = json.loads((root / "at-signal.json").read_text())
        expected_status = "timeout" if args.mode == "timeout" else "exit"
        expected_code = 124 if args.mode == "timeout" else 7
        hashes = set()
        for name, item in event["files"].items():
            hashes.add(item["sha256"])
            if item["sha256"] != digest(root / name):
                raise RuntimeError(f"exit readback changed after signal: {name}")
            fields = dict(line.split(": ", 1) for line in item["text"].splitlines())
            if fields["status"] != expected_status or int(fields["code"]) != expected_code:
                raise RuntimeError(f"wrong result in {name}: {fields}")
            if fields["agent"] != "codex" or fields["signal"] != signal_name:
                raise RuntimeError(f"wrong agent/signal in {name}")
            if args.mode == "timeout" and "timeout-force" not in fields["reason"]:
                raise RuntimeError("missing timeout-force reason")
        if len(hashes) != 1 or not event["before_signal_forward"]:
            raise RuntimeError("exit files differ or were not read before signaling")
        if digest(wrapper) != before_hash:
            raise RuntimeError("wrapper changed during smoke")
        calls = [json.loads(line) for line in (root / "tmux-calls.jsonl").read_text().splitlines()]
        if any("send-keys" in call["argv"] for call in calls):
            raise RuntimeError("unexpected send-keys")
        summary = {
            "status": "PASS", "mode": args.mode, "evidence_kind": "real tmux / fixture codex",
            "wrapper": str(wrapper), "wrapper_sha256": before_hash,
            "tmux_bin": str(proxy), "real_tmux": real_tmux,
            "session": session, "signal": signal_name,
            "exit_code": expected_code, "waiter_exit_code": waiter.returncode,
            "all_exit_files_identical": True, "exit_readback_before_signal": True,
            "send_keys_calls": 0,
        }
        (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
    finally:
        log.close()
        if waiter is not None and waiter.poll() is None:
            waiter.terminate()
            waiter.communicate(timeout=5)
        if server_started:
            subprocess.run(base + ["kill-server"], env=env, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
