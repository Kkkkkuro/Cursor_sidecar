# Launch-path smoke

## Installed skill SO19 smoke (writes only to the named RUN_DIR)

This explicit mode creates a private real tmux server and a fixture executable named `codex`. It starts no actual Codex/Hermes CLI and touches no GBrain data. Run the adapter preflight separately for a real launch; fixture success does not prove model, auth or production acceptance.

```sh
python3 scripts/install-skill.py --check
python3 scripts/install-skill.py --dest "$RUN_DIR/skill-install-dst"
python3 smoke/check-so19.py --wrapper "$RUN_DIR/skill-install-dst/scripts/run-agent-with-tmux-signal.py" --run-dir "$RUN_DIR/smoke-normal" --mode normal
python3 smoke/check-so19.py --wrapper "$RUN_DIR/skill-install-dst/scripts/run-agent-with-tmux-signal.py" --run-dir "$RUN_DIR/smoke-timeout" --mode timeout
```

Each destination must be new or empty. Keep RUN_DIR short enough for a Unix socket (the script checks). Normal returns code 7 to test nonzero propagation; timeout kills the hung fixture and records code 124. Each case launches the installed wrapper with `new-session -d` and an absolute `TMUX_BIN` proxy that delegates to absolute real tmux. The proxy reads all three exit files **before** forwarding `wait-for -S`. `at-signal.json` contains the contents, SHA256 values and call arguments; `launch.json`, `tmux-calls.jsonl` and `summary.json` prove the start, bounded waiter and no `send-keys`. Only the private test server is stopped afterward.

The keep-exception for the KM-owned GBrain wrapper does not authorize its use without the skill's current-hash SO19 evidence. Do not rewrite its body. Missing/failed evidence is STUCK; redirect the plan to the installed skill wrapper and repeat preflight/smoke. These fixture results cannot certify a different wrapper or authorize a live cutover.

Install regressions (keep scratch files local to the job):

```sh
mkdir -p "$RUN_DIR/test-tmp"
SIDECAR_TEST_TMP="$RUN_DIR/test-tmp" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

## Version-only read-only smoke

Mini smoke of this repo is read-only (`mutation=0`). It checks the launch path. It does not start a Codex job or a Hermes job.

On a Mini checkout:

1. Confirm the tree contains `scripts/run-agent-with-tmux-signal.py`, `adapters/codex/`, `adapters/hermes/`, and `adapters/_template/`.
2. Check syntax without writing bytecode into the repo: `python3 -c 'import ast, pathlib; ast.parse(pathlib.Path("scripts/run-agent-with-tmux-signal.py").read_text())'`.
3. For the selected adapter, run only a version probe when that binary is on `PATH`. Record the command and that it did not start a job.
4. Do not run `codex exec`. Do not run a Hermes job command. Hermes non-interactive flags are still TODO in `adapters/hermes/ADAPTER.md`.
5. Do not `send-keys` a multi-line command. Do not create a tmux session in the read-only smoke.

## What this cloud VM ran

Measured while preparing the launcher pull request. None of these commands started a Codex job or a Hermes job. This list is not a Mini read-only smoke.

- `command -v hermes` failed. `hermes --version` was not run. `hermes --help` was not run. No Hermes flags were recorded.
- `command -v codex` failed. `~/.codex` was absent.
- The shared shell was started under tmux with `/bin/true`, with `/bin/sleep 30` and `--timeout-sec 1`, with a copy of `/bin/true` whose file name is `codex`, and with a two-line command. The two-line command was rejected. Each waiter returned. `codex.exit` was written only for the copy named `codex`.
- `adapters/codex/preflight.sh` was run against a temporary fixture binary and config. It was not run against a live Codex login. The fixture secret did not appear in the output.
