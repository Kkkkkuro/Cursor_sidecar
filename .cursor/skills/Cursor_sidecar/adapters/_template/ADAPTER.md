# Agent adapter template

Copy this directory to `adapters/<cli-name>/` only after the Owner names the agent. Replace every placeholder before the first launch.

CLI name: `AGENT_BIN` (the executable name, not a product this repo already rejected).

## Model / effort / fast defaults

`model`, `effort` and `fast` are all **N/A in this uninstantiated template** because no CLI or measured configuration mapping exists yet. A new adapter must use the shared `scripts/agent_defaults.py` surface with measured per-process mappings, or give an explicit N/A reason for each unsupported field. Never inherit Codex values or silently drop BRIEF overrides. The wrapper currently refuses `--brief`/`--defaults-file` for non-Codex commands. Keep preflight fail-closed until those decisions and the launch are measured.

## Version check

`"$AGENT_BIN" --version`. Print the version line only.

## Auth proof

Set `AGENT_AUTH_FILE` to the credential file the Owner named. Preflight checks that the file is non-empty and prints `auth: present bytes=<n>`. Do not print the file. If the CLI proves auth another way, replace that block with a command whose output has no secrets, and write the command here after you have run it.

## agent-cmd

One line. The first token is `AGENT_BIN`. Record the non-interactive subcommand only after you have seen it in `--help` or an Owner note. Until then, smoke stays TODO.

## Smoke

TODO until a version-only probe has been run on a machine that has the binary, with a note that the probe did not start a job.
