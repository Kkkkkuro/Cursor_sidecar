# Codex adapter preflight

Before a real launch, the Codex adapter checks CLI version, nonempty auth file and
the resolved model, reasoning effort and fast choices. This is a readiness check, not a model
request or proof that the credentials are valid with the service.

## Sub-features

- Missing `codex` on PATH, failed version probe or missing/empty auth returns STUCK.
- Reads `${CODEX_HOME:-$HOME/.codex}/config.toml` with Python `tomllib`.
- Resolves the skill's explicit first-run `defaults.toml` and optional unindented BRIEF `agent_model` / `agent_effort` / `agent_fast` overrides using `scripts/agent_defaults.py`.
- Prints version, auth byte length and the three resolved choices without dumping base config.
- Missing/malformed defaults or BRIEF, non-regular inputs or unusable auth exit 1; successful readiness prints `STATUS: ok`. No fixed model/effort pair is required in the base config, because the wrapper supplies per-process CLI overrides.

## How to get to it (user POV)

Read [Launch/Doctor](../SKILL.md), then inspect the selected adapter path.
Use the preflight as a separate read-only check when a real Codex launch is intended.
The default wrapper fixture journey does not require a real account or this check.

## Driving it with Bash and Python

From the repository root, in the initialized Bash session:

```bash
run adapters/codex/preflight.sh
```

First complete the explicit setup documented in the fleet skill; do not pick a model automatically for this check. Pass identical `--brief "$BRIEF"` and optional `--defaults-file <absolute-path>` to preflight and wrapper when used. This read-only journey must not run setup or modify saved defaults itself.

Success requires exit 0 and `STATUS: ok` with the expected resolved model/effort/fast. Preserve
the curated output and exit code in `$PROOF_DIR/commands.log`. A failure is the
observed readiness result: record the failing item, retain scratch and stop the real
launch. Do not edit auth/configuration, change the session model or run `codex exec`
to turn this check green. This feature alone does not use the wrapper Evidence or
successful-close Cleanup blocks; those require the full default journey.

For the missing-CLI failure path without touching a real account:

```bash
run python3 -E - <<'PY'
import subprocess
cmd = ['/bin/sh', 'adapters/codex/preflight.sh']
proc = subprocess.run(cmd, env={'PATH': '/usr/bin:/bin'}, capture_output=True, text=True, timeout=30)
print('command:', cmd, 'PATH=/usr/bin:/bin')
print(proc.stdout, proc.stderr, f'exit_code: {proc.returncode}')
assert proc.returncode == 1 and 'codex binary not on PATH' in proc.stderr
PY
```

## Gotchas

The check resolves `codex` from the current PATH; a fixture or shim there changes
what version is being measured. Python must support `tomllib` (3.11+). Malformed TOML
returns a sanitized STUCK result; do not launch. Pass the same defaults/BRIEF inputs to the wrapper and keep them unchanged until launch. Provider model/effort support and fast entitlement are not proven by this local check. Never print auth contents, complete config, tokens or environment.
Hermes is separate: its current adapter fails closed even when its version succeeds,
because non-interactive invocation remains unmeasured.
