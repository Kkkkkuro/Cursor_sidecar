# Codex adapter

CLI name: `codex`.

## Version check

`codex --version`. The version line is safe to print.

## Auth proof

Preflight requires `$CODEX_HOME/auth.json` when `CODEX_HOME` is set, otherwise `~/.codex/auth.json`. The file must exist and be non-empty. Preflight prints `auth: present bytes=<n>` and does not read the body out loud. This path is the Codex CLI credential file (inferred from the fleet preflight rule, not opened on this VM).

## Config

Requires Python 3.11+. Run `python3 "$SKILL_ROOT/scripts/agent_defaults.py" setup --model <choice> --effort <choice> --fast true|false` once. This writes `$SKILL_ROOT/defaults.toml` with a `[codex]` table containing `model` (CLI model identifier), `effort` (a level advertised by the chosen model/client), and `fast` (boolean). No model or effort is supplied implicitly. `setup --replace` requires all three choices again and preserves the previous bytes in a unique `defaults.toml.backup-*` file before atomic replacement. Defaults and backups are local and must not enter the public bundle.

Precedence: unindented BRIEF scalar keys `agent_model:`, `agent_effort:`, `agent_fast: true|false` override individual saved fields. Values are unquoted, one per line; duplicates, empty/invalid identifiers and non-boolean fast are refused. Missing or invalid saved defaults still require setup even if all BRIEF keys are present. Missing/unreadable BRIEF and malformed TOML fail closed. Model availability and supported effort levels remain the CLI/provider's responsibility; this resolver checks structure, not account entitlement.

Pass identical `--brief /absolute/BRIEF.md` and optional `--defaults-file /absolute/defaults.toml` to preflight and the shared wrapper. Without a path override, each uses the defaults beside its own loaded skill. A job-local skill copy needs its own explicit defaults file or the same `--defaults-file`. For `agents:`, these flat overrides apply to each selected Codex session; use separate BRIEFs for different choices.

Preflight parses `$CODEX_HOME/config.toml` (default `~/.codex/config.toml`) and validates the resolved launch settings with the shared resolver. Its model/effort need not match the base file: the wrapper passes root-level `-c model=...`, `-c model_reasoning_effort=...`, `-c service_tier="fast"|"default"` and `-c features.fast_mode=true|false` to the child. Thus fast=false also overrides an inherited fast setting. It never edits the user config and requires no config backup/sync.

Defaults, BRIEF and base config must be regular files. Auth must be regular, readable and non-empty. Setup flushes the backup before replacement. A failed post-publication readback is an error, with the backup retained; inspect both and restore manually if needed rather than automatically overwriting a concurrent change.

The per-process override behavior is measured in `codex exec --help` on CLI 0.164.0. See official [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) and [speed documentation](https://learn.chatgpt.com/docs/agent-configuration/speed). Fast requests can increase usage and depend on the account/model; local fixture tests do not prove remote speed or entitlement.

## agent-cmd

One line, e.g. `codex exec --color never -- 'job prompt'`. The first token's basename is `codex`, immediately followed by `exec`. Put the prompt after `--`. To keep resolved settings authoritative, the wrapper refuses `-c`/`--config`, `-m`/`--model`, `-p`/`--profile`, feature toggles, local-provider switches and `--ignore-user-config` before that delimiter. Use setup/BRIEF for these choices. Other exec flags keep their existing meaning. Do not embed a newline.

When that basename is `codex`, the shared shell also writes `codex.exit` with the same bytes as `exit.txt` and `agent.exit`.

## Launch

Run `adapters/codex/preflight.sh` first. On failure, stop with `STATUS: STUCK`. Do not start the shared shell, and do not do the Codex work in Cursor as a fallback.
