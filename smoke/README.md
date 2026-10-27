# Launch-path smoke

Mini smoke of this repo is read-only (`mutation=0`). It checks the launch path. It does not start a Codex job or a Hermes job.

On a Mini checkout:

1. Confirm the tree contains `scripts/run-agent-with-tmux-signal.py`, `adapters/codex/`, `adapters/hermes/`, and `adapters/_template/`.
2. Compile the shell without writing bytecode into the repo: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/run-agent-with-tmux-signal.py`.
3. For the selected adapter, run only a version probe when that binary is on `PATH`. Record the command and that it did not start a job.
4. Do not run `codex exec`. Do not run a Hermes job command. Hermes non-interactive flags are still TODO in `adapters/hermes/ADAPTER.md`.
5. Do not `send-keys` a multi-line command. Do not create a tmux session in the read-only smoke.

## What this cloud VM ran

Measured while preparing the launcher pull request. None of these commands started a Codex job or a Hermes job. This list is not a Mini read-only smoke.

- `command -v hermes` failed. `hermes --version` was not run. `hermes --help` was not run. No Hermes flags were recorded.
- `command -v codex` failed. `~/.codex` was absent.
- The shared shell was started under tmux with `/bin/true`, with `/bin/sleep 30` and `--timeout-sec 1`, with a copy of `/bin/true` whose file name is `codex`, and with a two-line command. The two-line command was rejected. Each waiter returned. `codex.exit` was written only for the copy named `codex`.
- `adapters/codex/preflight.sh` was run against a temporary fixture binary and config. It was not run against a live Codex login. The fixture secret did not appear in the output.
