#!/usr/bin/env python3
"""Sidecar-owned first-run choices and per-job overrides (Python 3.11+)."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import tomllib


DEFAULTS_FILE = Path(__file__).resolve().parents[1] / "defaults.toml"
FIELDS = ("model", "effort", "fast")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/+-]{0,127}\Z")


class ConfigError(ValueError):
    pass


def normalize_path(path: Path) -> Path:
    try:
        return path.expanduser()
    except (OSError, ValueError, RuntimeError):
        raise ConfigError("configuration path cannot be normalized") from None


def validate(values: dict) -> dict:
    if set(values) != set(FIELDS):
        raise ConfigError("defaults require exactly model, effort and fast")
    for key in ("model", "effort"):
        if not isinstance(values[key], str) or not TOKEN.fullmatch(values[key]):
            raise ConfigError(f"{key} must be a non-empty CLI identifier")
    if type(values["fast"]) is not bool:
        raise ConfigError("fast must be true or false")
    return dict(values)


def read_toml(path: Path) -> dict:
    try:
        if not path.is_file():
            raise ConfigError("configuration must be a regular file")
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # TOML diagnostics can contain arbitrary file contents, including secrets.
        raise ConfigError("configuration missing, unreadable or invalid TOML") from None


def brief_overrides(path: Path | None) -> dict:
    if path is None:
        return {}
    path = normalize_path(path)
    try:
        if not path.is_file():
            raise ConfigError("BRIEF must be a regular file")
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, ValueError):
        raise ConfigError("BRIEF unreadable") from None
    result = {}
    for line in lines:
        match = re.match(r"^agent_(model|effort|fast)\s*:(.*)$", line)
        if not match:
            if re.match(r"^[\s\ufeff]*agent_(model|effort|fast)\b", line):
                raise ConfigError("BRIEF override requires an unindented agent_<field>: value line")
            continue
        key, raw = match.group(1), match.group(2).strip()
        if key in result:
            raise ConfigError(f"duplicate agent_{key} in BRIEF")
        if key == "fast":
            if raw not in ("true", "false"):
                raise ConfigError("agent_fast must be literal true or false")
            result[key] = raw == "true"
        else:
            result[key] = raw
    return result


def resolve(path: Path | None = None, brief: Path | None = None) -> dict:
    path = normalize_path(path if path is not None else DEFAULTS_FILE)
    try:
        exists = path.exists()
    except (OSError, ValueError):
        raise ConfigError("defaults path cannot be inspected") from None
    if not exists:
        raise ConfigError("first-run setup required: run scripts/agent_defaults.py setup "
                          "--model <choice> --effort <choice> --fast true|false; "
                          "repeat any --defaults-file <same-path> before setup")
    data = read_toml(path)
    if set(data) != {"codex"} or not isinstance(data["codex"], dict):
        raise ConfigError("defaults file must contain one [codex] table")
    values = validate(data["codex"])
    values.update(brief_overrides(brief))
    return validate(values)


def setup(path: Path, values: dict, replace: bool = False) -> None:
    values = validate(values)
    path = normalize_path(path)
    if not path.name:
        raise ConfigError("defaults path must include a file name")
    body = ("[codex]\n" + "".join(
        f"{key} = {json.dumps(values[key])}\n" for key in FIELDS
    )).encode()
    if path.is_symlink():
        raise ConfigError("refusing a symlink defaults file")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Serialize setup writers. A leftover lock requires inspection, never deletion here.
    lock = path.with_name(path.name + ".lock")
    try:
        lock.mkdir()
    except FileExistsError:
        raise ConfigError("defaults setup already locked; inspect the existing writer") from None
    temporary = None
    try:
        exists = path.exists()
        if path.is_symlink() or (exists and not path.is_file()):
            raise ConfigError("defaults must be a regular file")
        if exists and not replace:
            raise ConfigError("defaults already exist; use --replace to back up and change them")
        if exists:
            # Exclusive creation preserves previous backups and the previous file bytes.
            with tempfile.NamedTemporaryFile(prefix=path.name + ".backup-", dir=path.parent,
                                             delete=False) as backup:
                backup.write(path.read_bytes())
                backup.flush()
                os.fsync(backup.fileno())
            sync_directory(path.parent)
        fd, name = tempfile.mkstemp(prefix=path.name + ".tmp-", dir=path.parent)
        temporary = Path(name)
        with os.fdopen(fd, "wb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        if exists:
            os.replace(temporary, path)
        else:
            # Atomic first publication; a concurrent non-setup writer is never truncated.
            os.link(temporary, path)
        sync_directory(path.parent)
        if resolve(path) != values:
            raise ConfigError("defaults published but readback differs; inspect file and backup before retry")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        lock.rmdir()


def sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def codex_settings(values: dict) -> dict:
    return {"model": values["model"], "model_reasoning_effort": values["effort"],
            "service_tier": "fast" if values["fast"] else "default",
            "features.fast_mode": values["fast"]}


def codex_command(argv: list[str], values: dict) -> list[str]:
    # These are root-level CLI overrides, taking precedence over file/profile defaults.
    # Refuse a second configuration channel in agent-cmd, before the prompt delimiter.
    if len(argv) < 2 or argv[1] != "exec":
        raise ConfigError("configured Codex jobs require codex exec")
    for item in argv[2:]:
        if item == "--":
            break
        if (item.startswith(("-c", "-m", "-p")) or
                item.split("=", 1)[0] in ("--config", "--model", "--profile", "--enable",
                                           "--disable", "--oss", "--local-provider",
                                           "--ignore-user-config")):
            raise ConfigError("use defaults/BRIEF for Codex settings; put prompt after --")
    flags = []
    for key, value in codex_settings(values).items():
        flags.extend(["-c", f"{key}={json.dumps(value)}"])
    return [argv[0], *flags, *argv[1:]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--defaults-file", type=Path, default=DEFAULTS_FILE)
    sub = parser.add_subparsers(dest="command", required=True)
    writer = sub.add_parser("setup", help="explicit first-run setup; no model fallback")
    writer.add_argument("--model", required=True)
    writer.add_argument("--effort", required=True)
    writer.add_argument("--fast", required=True, choices=("true", "false"))
    writer.add_argument("--replace", action="store_true")
    reader = sub.add_parser("resolve")
    reader.add_argument("--brief", type=Path)
    reader.add_argument("--codex-config", type=Path,
                        help="validate base TOML without requiring matching file defaults")
    args = parser.parse_args()
    try:
        if args.command == "setup":
            setup(args.defaults_file,
                  {"model": args.model, "effort": args.effort, "fast": args.fast == "true"},
                  args.replace)
            print("defaults: saved and read back (model, effort, fast)")
        else:
            values = resolve(args.defaults_file, args.brief)
            if args.codex_config is not None:
                read_toml(args.codex_config)
                # Validate exactly the command shape the wrapper will use.
                codex_command(["codex", "exec", "--", "prompt"], values)
            print(json.dumps(values, sort_keys=True))
        return 0
    except (ConfigError, OSError) as exc:
        # Keep raw OS paths/errors and user config contents out of logs.
        detail = str(exc) if isinstance(exc, ConfigError) else "defaults file operation failed"
        print(f"STATUS: STUCK\nitem: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
