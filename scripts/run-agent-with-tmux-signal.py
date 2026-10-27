#!/usr/bin/env python3
"""Run one agent command and ring the tmux completion bell from finally."""

from __future__ import annotations

import argparse
import math
import os
import shlex
import shutil
import signal
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

CODEX_AGENT_NAME = "codex"
EXIT_FILE_NAMES = ("exit.txt", "agent.exit")
CODEX_EXIT_ALIAS = "codex.exit"
TMUX_CANDIDATES = ("/opt/homebrew/bin/tmux", "/usr/local/bin/tmux")


class RunStatus(Enum):
    EXIT = "exit"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class RunResult:
    status: RunStatus
    code: int
    reason: str


class UsageError(Exception):
    pass


def peek_option(argv: list[str], name: str) -> str | None:
    prefix = name + "="
    for index, item in enumerate(argv):
        if item == name and index + 1 < len(argv):
            return argv[index + 1]
        if item.startswith(prefix):
            return item[len(prefix) :]
    return None


def resolve_tmux() -> str | None:
    configured = os.environ.get("TMUX_BIN")
    if configured:
        if (
            os.path.isabs(configured)
            and os.path.isfile(configured)
            and os.access(configured, os.X_OK)
        ):
            return configured
        return None
    for candidate in TMUX_CANDIDATES:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    found = shutil.which("tmux")
    if found is None:
        return None
    if not os.path.isabs(found):
        found = os.path.realpath(found)
    if os.path.isabs(found) and os.path.isfile(found) and os.access(found, os.X_OK):
        return found
    return None


def tmux_argv(binary: str) -> list[str]:
    argv = [binary]
    raw = os.environ.get("TMUX", "")
    socket = raw.split(",", 1)[0]
    if socket.startswith("/"):
        argv.extend(["-S", socket])
    return argv


def current_session(binary: str) -> str | None:
    if not os.environ.get("TMUX"):
        return None
    try:
        proc = subprocess.run(
            tmux_argv(binary) + ["display-message", "-p", "#S"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    name = proc.stdout.strip()
    return name or None


def parse_agent_cmd(raw: str) -> list[str]:
    if "\n" in raw or "\r" in raw:
        raise UsageError("agent-cmd must be a single line")
    try:
        argv = shlex.split(raw, posix=True)
    except ValueError as exc:
        raise UsageError(f"agent-cmd could not be parsed: {exc}") from exc
    if not argv:
        raise UsageError("agent-cmd is empty")
    return argv


def agent_basename(argv: list[str]) -> str:
    return os.path.basename(argv[0])


def kill_process_group(proc: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=2)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        return


def run_agent(argv: list[str], timeout_sec: float) -> RunResult:
    try:
        proc = subprocess.Popen(argv, start_new_session=True)
    except OSError as exc:
        detail = exc.strerror or str(exc)
        return RunResult(RunStatus.ERROR, 127, f"failed to start agent: {detail}")
    try:
        code = proc.wait(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        kill_process_group(proc)
        return RunResult(
            RunStatus.TIMEOUT,
            124,
            f"timeout-force after {timeout_sec:g}s",
        )
    return RunResult(RunStatus.EXIT, int(code), f"agent exited {int(code)}")


def render_exit(
    result: RunResult,
    agent: str,
    session: str,
    signal_name: str,
    timeout_sec: str,
) -> str:
    reason = result.reason.replace("\n", " ").replace("\r", " ")
    lines = (
        f"status: {result.status.value}",
        f"code: {result.code}",
        f"reason: {reason}",
        f"agent: {agent}",
        f"session: {session}",
        f"signal: {signal_name}",
        f"timeout_sec: {timeout_sec}",
    )
    return "\n".join(lines) + "\n"


def write_exits(run_dir: Path, body: str, agent: str) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    names = list(EXIT_FILE_NAMES)
    if agent == CODEX_AGENT_NAME:
        names.append(CODEX_EXIT_ALIAS)
    data = body.encode("utf-8")
    for name in names:
        target = run_dir / name
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, target)


def notify(binary: str | None, signal_name: str) -> None:
    if not signal_name or binary is None:
        print("completion bell skipped", file=sys.stderr)
        return
    try:
        subprocess.run(
            tmux_argv(binary) + ["wait-for", "-S", signal_name],
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        print("completion bell failed", file=sys.stderr)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="run-agent-with-tmux-signal",
        exit_on_error=False,
    )
    parser.add_argument("--agent-cmd", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--signal", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--timeout-sec", required=True)
    try:
        return parser.parse_args(argv)
    except argparse.ArgumentError as exc:
        raise UsageError(str(exc)) from exc


def require_token(value: str, label: str) -> str:
    if value.strip() == "" or "\n" in value or "\r" in value:
        raise UsageError(f"{label} must be a single non-empty token")
    return value


def require_timeout(raw: str) -> float:
    try:
        timeout_sec = float(raw)
    except ValueError as exc:
        raise UsageError("timeout-sec must be a positive number") from exc
    if not math.isfinite(timeout_sec) or timeout_sec <= 0:
        raise UsageError("timeout-sec must be a positive number")
    return timeout_sec


def launch(argv: list[str]) -> RunResult:
    ns = parse_args(argv)
    session = require_token(ns.session, "session")
    require_token(ns.signal, "signal")
    require_timeout(ns.timeout_sec)
    agent_argv = parse_agent_cmd(ns.agent_cmd)
    tmux_bin = resolve_tmux()
    if tmux_bin is None:
        return RunResult(RunStatus.ERROR, 127, "tmux binary not found")
    here = current_session(tmux_bin)
    if here != session:
        return RunResult(
            RunStatus.ERROR,
            2,
            f"wrapper session is {here or 'unset'}, expected {session}",
        )
    return run_agent(agent_argv, float(ns.timeout_sec))


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    signal_name = peek_option(args_list, "--signal") or ""
    run_dir_raw = peek_option(args_list, "--run-dir")
    timeout_raw = peek_option(args_list, "--timeout-sec") or ""
    session = peek_option(args_list, "--session") or ""
    agent = "unknown"
    tmux_bin = resolve_tmux()
    result = RunResult(RunStatus.ERROR, 1, "launch failed before a result was recorded")
    rc = 1
    try:
        try:
            agent_cmd = peek_option(args_list, "--agent-cmd")
            if agent_cmd:
                try:
                    agent = agent_basename(parse_agent_cmd(agent_cmd))
                except UsageError:
                    agent = "unknown"
            result = launch(args_list)
            rc = result.code
        except UsageError as exc:
            result = RunResult(RunStatus.ERROR, 2, str(exc))
            rc = 2
        body = render_exit(result, agent, session, signal_name, timeout_raw)
        if run_dir_raw:
            write_exits(Path(run_dir_raw).expanduser().resolve(), body, agent)
        else:
            print("exit files skipped: run-dir missing", file=sys.stderr)
    finally:
        notify(tmux_bin, signal_name)
    return rc


if __name__ == "__main__":
    sys.exit(main())
