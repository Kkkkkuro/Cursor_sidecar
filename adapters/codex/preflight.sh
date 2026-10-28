#!/bin/sh
set -eu

fail() {
  printf 'STATUS: STUCK\nitem: %s\n' "$1" >&2
  exit 1
}

CODEX_BIN=$(command -v codex || true)
if [ -z "$CODEX_BIN" ]; then
  fail 'codex binary not on PATH'
fi

version=$("$CODEX_BIN" --version) || fail 'codex --version failed'
printf 'codex_version: %s\n' "$version"

skill_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
codex_home=${CODEX_HOME:-$HOME/.codex}
auth="$codex_home/auth.json"
if [ ! -f "$auth" ] || [ ! -r "$auth" ] || [ ! -s "$auth" ]; then
  fail 'codex auth file missing, unreadable or empty'
fi
bytes=$(wc -c < "$auth") || fail 'codex auth file size check failed'
bytes=$(printf '%s' "$bytes" | tr -d '[:space:]')
printf 'auth: present bytes=%s\n' "$bytes"

cfg="$codex_home/config.toml"
if [ ! -f "$cfg" ]; then
  fail "codex config missing ($cfg)"
fi

# Both preflight and the wrapper use the same resolver. File defaults need not
# match: the wrapper supplies model, effort and fast as per-process CLI overrides.
defaults_file="$skill_root/defaults.toml"
brief=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --defaults-file) [ "$#" -ge 2 ] && [ -n "$2" ] || fail 'missing defaults-file'; defaults_file=$2; shift 2 ;;
    --brief) [ "$#" -ge 2 ] && [ -n "$2" ] || fail 'missing brief'; brief=$2; shift 2 ;;
    *) fail 'unknown preflight option' ;;
  esac
done
if [ -n "$brief" ]; then
  python3 "$skill_root/scripts/agent_defaults.py" --defaults-file "$defaults_file" resolve --codex-config "$cfg" --brief "$brief" || fail 'resolved Codex config invalid; complete first-run setup'
else
  python3 "$skill_root/scripts/agent_defaults.py" --defaults-file "$defaults_file" resolve --codex-config "$cfg" || fail 'resolved Codex config invalid; complete first-run setup'
fi

printf 'STATUS: ok\n'
