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

codex_home=${CODEX_HOME:-$HOME/.codex}
auth="$codex_home/auth.json"
if [ ! -s "$auth" ]; then
  fail "codex auth file missing or empty ($auth)"
fi
bytes=$(wc -c < "$auth" | tr -d ' ')
printf 'auth: present bytes=%s\n' "$bytes"

cfg="$codex_home/config.toml"
if [ ! -f "$cfg" ]; then
  fail "codex config missing ($cfg)"
fi

python3 - "$cfg" <<'PY'
import sys
from pathlib import Path
import tomllib

path = Path(sys.argv[1])
data = tomllib.loads(path.read_text(encoding="utf-8"))
model = data.get("model")
effort = data.get("model_reasoning_effort")
sys.stdout.write(f"config.model={model}\n")
sys.stdout.write(f"config.model_reasoning_effort={effort}\n")
if model != "gpt-6.1-sol":
    sys.stderr.write("STATUS: STUCK\nitem: config model is not gpt-6.1-sol\n")
    sys.exit(1)
if effort != "xhigh":
    sys.stderr.write("STATUS: STUCK\nitem: config model_reasoning_effort is not xhigh\n")
    sys.exit(1)
PY

printf 'STATUS: ok\n'
