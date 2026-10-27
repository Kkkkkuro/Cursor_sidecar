#!/bin/sh
set -eu

fail() {
  printf 'STATUS: STUCK\nitem: %s\n' "$1" >&2
  exit 1
}

if [ -z "${AGENT_BIN:-}" ]; then
  fail 'AGENT_BIN is unset'
fi

BIN=$(command -v "$AGENT_BIN" || true)
if [ -z "$BIN" ]; then
  fail "binary not on PATH ($AGENT_BIN)"
fi

version=$("$BIN" --version) || fail 'version check failed'
printf 'agent_version: %s\n' "$version"

if [ -z "${AGENT_AUTH_FILE:-}" ]; then
  fail 'AGENT_AUTH_FILE is unset'
fi
if [ ! -s "$AGENT_AUTH_FILE" ]; then
  fail "auth file missing or empty ($AGENT_AUTH_FILE)"
fi
bytes=$(wc -c < "$AGENT_AUTH_FILE" | tr -d ' ')
printf 'auth: present bytes=%s\n' "$bytes"
printf 'STATUS: ok\n'
