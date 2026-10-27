# Codex adapter

CLI name: `codex`.

## Version check

`codex --version`. The version line is safe to print.

## Auth proof

Preflight requires `$CODEX_HOME/auth.json` when `CODEX_HOME` is set, otherwise `~/.codex/auth.json`. The file must exist and be non-empty. Preflight prints `auth: present bytes=<n>` and does not read the body out loud. This path is the Codex CLI credential file (inferred from the fleet preflight rule, not opened on this VM).

## Config

Preflight reads only two top-level keys in `$CODEX_HOME/config.toml` (default `~/.codex/config.toml`).

- `model` must be `gpt-6.1-sol`.
- `model_reasoning_effort` must be `xhigh`.

Those key names are the Codex CLI config keys from the public example config (`model`, `model_reasoning_effort`). The required values come from the fleet preflight rule. This VM has no `~/.codex` directory, so the file was not read here. Preflight prints those two values and no other keys.

## agent-cmd

One line. The first token's basename is `codex`. A non-interactive job uses the `exec` subcommand. Pass the prompt as arguments the installed `codex` already accepts. Do not embed a newline.

When that basename is `codex`, the shared shell also writes `codex.exit` with the same bytes as `exit.txt` and `agent.exit`.

## Launch

Run `adapters/codex/preflight.sh` first. On failure, stop with `STATUS: STUCK`. Do not start the shared shell, and do not do the Codex work in Cursor as a fallback.
