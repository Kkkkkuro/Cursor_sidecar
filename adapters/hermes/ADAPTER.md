# Hermes adapter

CLI name: `hermes`.

## Model / effort / fast defaults

All three fields are **N/A for launch in this adapter**: its non-interactive invocation and configuration flags have not been measured, so mapping Codex model identifiers, reasoning levels or fast tiers would invent a contract. Do not create a `[hermes]` defaults table or silently ignore BRIEF overrides. Preflight remains `STATUS: STUCK` until the invocation is measured; the wrapper refuses `--brief`/`--defaults-file` for non-Codex commands. When this adapter becomes runnable, implement the shared model/effort/fast surface with measured mappings or document each remaining N/A. The existing version-only check does not prove configuration support.

## Version

Owner-stated: Hermes Agent v0.22.5 on Mini. This cloud VM did not measure that version. `command -v hermes` failed, so `hermes --version` and `hermes --help` were not run. No flags are recorded here, because none were seen.

## Version check

When `hermes` is on `PATH`, preflight runs `hermes --version`, prints that line, and then exits `STATUS: STUCK` with item `non-interactive invocation not measured`. A version line is not a launch. The script does not start a job.

## Auth proof

TODO. The auth check is not discoverable until `hermes` is present and its help (or an Owner-named auth file) is read. Preflight must not print secrets. It does not guess a credential path.

## agent-cmd

TODO. The non-interactive flag was not visible on this VM. Do not invent one. Until a measured flag exists, do not build a live `agent-cmd` and do not treat this adapter as smoke-clean.

## Smoke

TODO. A future smoke may run `hermes --version` only, and must say that the probe did not start a job. A job command waits until the non-interactive flag is measured.
