---
name: verify-cursor-sidecar
description: >-
  Verify Cursor_sidecar's CLI skill installation, adapter preflight, and tmux
  completion bell when checking a change or closing a stage. Preserve local
  proof artifacts and maintain the feature map with /maintain-verification-skill.
---

# Verify Cursor_sidecar

This is a checkout-local verification harness. Read [features/README.md](features/README.md)
and the feature being checked. The surface is CLI and on-disk files; no server or
browser is needed. The default journey proves the installed wrapper with real tmux
and a fixture named `codex`. It starts no live agent and contacts no GBrain service.
Fixture success does not certify a live login, model response, or fleet rollout.

Use one **Bash** session for the sections below, from this repository. Python 3.11+
and tmux are required. Keep the fleet skill, adapters, shared wrapper and KM-owned
wrapper unchanged. Never inspect credential contents or dump configuration/environment.
The optional Codex preflight prints only version, auth byte length and the two
allowlisted model/effort identifiers. A failed real preflight means STUCK; do not
launch an agent as a fallback.

## Launch

Launch means preparing isolated local directories, not starting a persistent app.
The default RUN_DIR is the Owner t667u job on the local home disk. For a later job,
set RUN_DIR to that job's directory under `$HOME/cursor-runs` before these commands.
Each attempt gets a fresh short `i.*` directory; keep the printed proof paths.

```bash
set -euo pipefail
umask 077
cd "$(git rev-parse --show-toplevel)"
export REPO_ROOT="$PWD"
export RUN_DIR="${RUN_DIR:-$HOME/cursor-runs/t667u-verify-cursor-sidecar}"
python3 -E - <<'PY'
import os
from pathlib import Path
root = Path(os.environ['RUN_DIR'])
assert root.is_absolute() and root == root.resolve(), 'RUN_DIR must not use symlinks'
assert root.is_relative_to(Path.home().resolve() / 'cursor-runs'), 'use the local home disk'
for path in (root, root / 'evidence', root / 'proof'):
    assert not path.is_symlink(), path
    path.mkdir(parents=True, exist_ok=True)
PY
export INSTANCE="$(mktemp -d "$RUN_DIR/i.XXXXXX")"
export RUN_ID="$(basename "$INSTANCE")"
export PROOF_DIR="$RUN_DIR/proof/$RUN_ID"
export EVIDENCE_DIR="$RUN_DIR/evidence/wrapper-so19-dual-path/$RUN_ID"
mkdir "$PROOF_DIR"
printf '%s\n' "$RUN_ID" > "$INSTANCE/.verify-owner"
run() {
  local rc=0 output
  output="$(mktemp "$PROOF_DIR/command.XXXXXX")" || return
  { printf '\n$'; printf ' %q' "$@"; printf '\noutput_file: %s\n' "$output"; } | tee -a "$PROOF_DIR/commands.log" || return
  "$@" > "$output" 2>&1 || rc=$?
  tee -a "$PROOF_DIR/commands.log" < "$output" || return
  printf 'exit_code: %s\n' "$rc" | tee -a "$PROOF_DIR/commands.log" || return
  return "$rc"
}
printf 'INSTANCE=%s\nPROOF_DIR=%s\nEVIDENCE_DIR=%s\n' "$INSTANCE" "$PROOF_DIR" "$EVIDENCE_DIR" | tee -a "$PROOF_DIR/commands.log"
run git rev-parse HEAD
run python3 scripts/install-skill.py --check
```

## Doctor

All commands must exit 0 before the default Drive. An unavailable tool, invalid
bundle or overlong socket is STUCK; keep its transcript instead of changing gates.
The fixture journey needs no agent authentication. To verify a real adapter,
use its mapped feature separately; do not make that a hidden prerequisite here.

```bash
run python3 --version
run python3 -E -c 'import sys, tomllib; assert sys.version_info >= (3, 11)'
export TMUX_BIN="$(command -v tmux)"
run "$TMUX_BIN" -V
run python3 -E - <<'PY'
import ast, os
from pathlib import Path
for name in ('scripts/install-skill.py', 'scripts/run-agent-with-tmux-signal.py', 'smoke/check-so19.py'):
    ast.parse(Path(name).read_text())
for case in ('n', 't'):
    socket = Path(os.environ['INSTANCE']) / case / 'tmux.sock'
    assert len(os.fsencode(socket)) <= 100, 'shorten RUN_DIR; Unix socket limit is 100 bytes'
print('doctor: PASS (Python, syntax, private socket paths)')
PY
run python3 scripts/install-skill.py --check
```

## Drive

Default mapped feature: [wrapper-so19-dual-path](features/wrapper-so19-dual-path.md).
The installer destination and both smoke directories are new. These are the
existing repository entrypoints, not a second agent launch path.

```bash
run python3 scripts/install-skill.py --dest "$INSTANCE/skill"
run python3 smoke/check-so19.py --wrapper "$INSTANCE/skill/scripts/run-agent-with-tmux-signal.py" --run-dir "$INSTANCE/n" --mode normal
run python3 smoke/check-so19.py --wrapper "$INSTANCE/skill/scripts/run-agent-with-tmux-signal.py" --run-dir "$INSTANCE/t" --mode timeout
```

Both smoke commands exit **0** for success. Their fixture result codes are **7**
(normal nonzero propagation) and **124** (forced timeout), respectively. The smoke
owns a private tmux socket, bounds its waiter, reads exit files before forwarding
`wait-for -S`, and stops only its own server in `finally`. Never drive the worker's
shared tmux session, run a live agent, or use unscoped `tmux kill-server` for proof.

## Evidence

For the default job, the durable evidence parent is
`/Users/kurochen_macmini/cursor-runs/t667u-verify-cursor-sidecar/evidence/wrapper-so19-dual-path/`.
The exact attempt path is `$EVIDENCE_DIR`, outside `$INSTANCE`. Preserve the
summaries, pre-signal readbacks, exit files, launch argv, tmux calls, logs and the
exact installed wrapper. Record hashes under `$PROOF_DIR` before cleanup.

```bash
run python3 -E - <<'PY'
import hashlib, json, os, shutil
from pathlib import Path
instance = Path(os.environ['INSTANCE'])
evidence = Path(os.environ['EVIDENCE_DIR'])
evidence.mkdir(parents=True, exist_ok=False)
wrapper = instance / 'skill/scripts/run-agent-with-tmux-signal.py'
wrapper_hash = hashlib.sha256(wrapper.read_bytes()).hexdigest()
for case, mode, code in (('n', 'normal', 7), ('t', 'timeout', 124)):
    source = instance / case
    summary = json.loads((source / 'summary.json').read_text())
    assert (summary['status'], summary['mode'], summary['exit_code']) == ('PASS', mode, code)
    assert summary['waiter_exit_code'] == 0 and summary['send_keys_calls'] == 0
    assert summary['all_exit_files_identical'] and summary['exit_readback_before_signal']
    assert summary['wrapper_sha256'] == wrapper_hash
    target = evidence / mode
    target.mkdir()
    for name in ('summary.json', 'at-signal.json', 'exit.txt', 'agent.exit', 'codex.exit',
                 'launch.json', 'tmux-calls.jsonl', 'wrapper.log'):
        shutil.copy2(source / name, target / name)
shutil.copy2(wrapper, evidence / 'installed-wrapper.py')
manifest = {p.relative_to(evidence).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(evidence.rglob('*')) if p.is_file()}
encoded = json.dumps(manifest, indent=2) + '\n'
(evidence / 'sha256.json').write_text(encoded)
(Path(os.environ['PROOF_DIR']) / 'artifact-sha256.json').write_text(encoded)
print(f'evidence: {evidence}\nartifacts: {len(manifest)}')
PY
```

Keep `$PROOF_DIR/commands.log` with command exit codes. Save any additional probes
there, never credentials or raw environment/configuration dumps. Summaries describe
fixture/replay evidence; label any live or untested claim separately. Local paths
are local proofs, not publicly accessible PR attachments.

## Cleanup

Run only after Evidence passes. Check archived hashes, then remove this attempt's
marked instance, including install and fixtures. Preserve all `proof/` and
`evidence/` content and the waiter's other files in RUN_DIR. On a failed journey,
retain scratch for diagnosis; do not run this successful-close cleanup.

```bash
run python3 -E - <<'PY'
import hashlib, json, os, shutil, subprocess
from pathlib import Path
root = Path(os.environ['RUN_DIR']).resolve()
instance = Path(os.environ['INSTANCE'])
evidence = Path(os.environ['EVIDENCE_DIR'])
assert instance == instance.resolve() and instance.parent == root
assert instance.name == os.environ['RUN_ID'] and instance.name.startswith('i.')
assert (instance / '.verify-owner').read_text().strip() == instance.name
assert evidence.is_relative_to(root / 'evidence') and not evidence.is_relative_to(instance)
manifest = json.loads((evidence / 'sha256.json').read_text())
assert manifest, 'no archived proof'
for name, expected in manifest.items():
    assert hashlib.sha256((evidence / name).read_bytes()).hexdigest() == expected, name
for case in ('n', 't'):
    probe = subprocess.run([os.environ['TMUX_BIN'], '-S', str(instance / case / 'tmux.sock'),
                            'list-sessions'], capture_output=True, text=True, timeout=5)
    assert probe.returncode != 0, 'private server still running; retain scratch and investigate'
shutil.rmtree(instance)
assert not instance.exists() and (evidence / 'sha256.json').is_file()
record = {'instance_removed': True, 'evidence_path': str(evidence),
          'post_cleanup_exists': evidence.is_dir(), 'artifacts_verified': len(manifest)}
(Path(os.environ['PROOF_DIR']) / 'post-cleanup.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
PY
```

## Helpers

No new executable helpers are needed. The commands above call maintained sources:

Internal Python checks use `-E` so inherited `PYTHONOPTIMIZE` cannot remove assertions.
Keep that flag. The `run` function drains output synchronously into per-command files
and the transcript; a process guard must not race a background logging process.

- `scripts/install-skill.py`: validate the complete bundle; install into a new/empty directory; refuse overwrite.
- `smoke/check-so19.py`: real private tmux plus a fixture, normal and timeout paths.
- `adapters/codex/preflight.sh`: version, auth presence/length and exact configured model/effort gate.
- `adapters/hermes/preflight.sh`: fails closed for missing CLI and currently for unmeasured non-interactive invocation.
- `tests/test_skill_install.py`: install regression suite. Optional checkout regression:

```bash
mkdir -p "$PROOF_DIR/test-tmp"
run env SIDECAR_TEST_TMP="$PROOF_DIR/test-tmp" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

For `/maintain-verification-skill`, compare the changed sources with the map, update
only affected journeys/gotchas, and rerun affected paths with fresh instances.
Keep feature headings and links intact. Do not mark a newly mapped feature proven
from documentation or syntax alone; cite its transcript, revision/hash and surviving
evidence, and report anything unverified. Check in map/instructions only, not job proofs.
