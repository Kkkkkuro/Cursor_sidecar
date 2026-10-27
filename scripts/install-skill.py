#!/usr/bin/env python3
"""Validate and install the complete on-disk Cursor_sidecar skill tree."""

import argparse
import hashlib
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / ".cursor/skills/Cursor_sidecar"
# The top-level sources stay authoritative. The bundled copies allow a plain
# directory install; this check prevents shipping stale or partial copies.
MIRRORS = (
    "scripts/run-agent-with-tmux-signal.py",
    "adapters/README.md",
    "adapters/codex/ADAPTER.md",
    "adapters/codex/preflight.sh",
    "adapters/hermes/ADAPTER.md",
    "adapters/hermes/preflight.sh",
    "adapters/_template/ADAPTER.md",
    "adapters/_template/preflight.sh",
    "docs/architecture.md",
)
PAYLOAD = ("SKILL.md", *MIRRORS)


def validate_bundle():
    actual = {p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob("*") if p.is_file()}
    if actual != set(PAYLOAD):
        raise ValueError("bundle file list differs; ship SKILL.md and every payload file")
    for name in PAYLOAD:
        bundled = BUNDLE / name
        if bundled.is_symlink():
            raise ValueError(f"bundle must contain real files: {name}")
        if name in MIRRORS:
            source = ROOT / name
            if bundled.read_bytes() != source.read_bytes():
                raise ValueError(f"bundle differs from {name}; refresh the bundled copy")
            if bundled.stat().st_mode & 0o777 != source.stat().st_mode & 0o777:
                raise ValueError(f"bundle permissions differ from {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="verify the checked-in bundle only")
    mode.add_argument("--dest", type=Path, help="exact skill directory; must be new or empty")
    args = parser.parse_args()
    try:
        validate_bundle()
        if args.dest is not None:
            dest = args.dest.expanduser().absolute()
            if dest.is_symlink() or (dest.exists() and (not dest.is_dir() or any(dest.iterdir()))):
                raise ValueError("destination must be a new or empty directory; existing installs are never overwritten")
            # Copy only the validated payload. No repository, config or credentials.
            for name in PAYLOAD:
                target = dest / name
                target.parent.mkdir(parents=True, exist_ok=True)
                # A concurrent installer may populate an initially empty target.
                # Exclusive creation fails closed instead of truncating its file.
                with (BUNDLE / name).open("rb") as source, target.open("xb") as installed:
                    shutil.copyfileobj(source, installed)
                shutil.copymode(BUNDLE / name, target)
                if target.read_bytes() != (BUNDLE / name).read_bytes():
                    raise ValueError(f"installed readback differs: {name}")
            print(f"installed: {dest}")
        else:
            print(f"bundle verified: {BUNDLE}")
        wrapper = (args.dest.expanduser().absolute() if args.dest else BUNDLE) / MIRRORS[0]
        print(f"wrapper_sha256: {hashlib.sha256(wrapper.read_bytes()).hexdigest()}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"STATUS: STUCK\nitem: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
