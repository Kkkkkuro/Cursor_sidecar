#!/bin/sh
set -eu

fail() {
  printf 'STATUS: STUCK\nitem: %s\n' "$1" >&2
  exit 1
}

HERMES_BIN=$(command -v hermes || true)
if [ -z "$HERMES_BIN" ]; then
  fail 'hermes binary not on PATH (Owner-stated Hermes Agent v0.22.5 was not measured here)'
fi

version=$("$HERMES_BIN" --version) || fail 'hermes --version failed'
printf 'hermes_version: %s\n' "$version"
fail 'non-interactive invocation not measured'
