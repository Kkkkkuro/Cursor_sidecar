---
name: Cursor_sidecar
description: >-
  Lets Cursor call any agent CLI installed on the current device through one
  shared launch path: Codex, Hermes, and (once you add an adapter) Claude, Kimi,
  and similar tools. Use when Cursor (including a Project Shell) needs an agent
  to do the work: pick it in the BRIEF, run preflight, start it in a tmux shell,
  and wait on a completion bell. A BRIEF that omits agent selection defaults to
  codex. Includes the required business-only BRIEF cite; never plugin get_skill.
  Formerly cursor-codex-launch.
---

# Cursor_sidecar (fleet skill)

**Cursor_sidecar** lets Cursor call any agent CLI installed on the current device, including Codex, Hermes, and (once you add an adapter) Claude, Kimi, and similar tools, through one shared launch path. When Cursor (including a Project Shell) needs an agent to do the work, pick it in the BRIEF, run preflight, start it in a tmux shell, and wait on a completion bell so the worker knows when to exit.

Authority is the Shared completion bell, then machine `grokbot-cursor-standing-orders` **#19** and **#23** (and the matching hard rules in the Cursor dispatch template). This skill does not restate Shared. If wording conflicts, Shared wins, then SO #19 and SO #23.

**Shape:** a complete fleet on-disk skill directory at `~/.cursor/skills/Cursor_sidecar/`, or a complete copy under the job `RUN_DIR`. `SKILL.md` alone is an incomplete install. It is not a GBrain or plugin catalog name. Briefs and workers must not call `plugin get_skill` or `get_skill` for `Cursor_sidecar` or the retired name `cursor-codex-launch`.

## Install and resolve paths

From the home repo, run `python3 scripts/install-skill.py --dest <absolute-skill-directory>` into a new or empty directory. It verifies the bundled files against their repo sources before copying, preserves executable preflights, and prints the installed wrapper SHA256. It refuses to overwrite an existing install. For an upgrade, stage into a new directory, verify it, then let the install owner replace the old directory. Copying the entire `.cursor/skills/Cursor_sidecar/` directory also works; never copy only `SKILL.md`.

Set `SKILL_ROOT` to the absolute directory containing the loaded `SKILL.md`. All `scripts/`, `adapters/`, and `docs/` paths below are relative to **that skill root**, never the business repository or the caller's working directory. The complete tree includes:

```text
Cursor_sidecar/
  SKILL.md
  scripts/run-agent-with-tmux-signal.py
  scripts/agent_defaults.py
  adapters/README.md
  adapters/{codex,hermes,_template}/{ADAPTER.md,preflight.sh}
  docs/architecture.md
```

Before launch, require `SKILL_ROOT/scripts/run-agent-with-tmux-signal.py` and the selected adapter's executable `preflight.sh` and `ADAPTER.md`. If absent, stop with `STATUS: STUCK`, item `incomplete Cursor_sidecar install`, and reinstall the complete tree. Do not search another project for a replacement script.

**Home repo / Project:** [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar) (public). Owning bot: Engineering Lead · 工程师.

Evidence for the launch hard rule: t1895u-r1 STUCK RECEIPT `e147a4c8` (tmux `send-keys` multi-line mangled `python3 '/Users/...`; wrapper and Codex never started). Mini smoke t2869u FIXED (RECEIPT sha256 `5a3b22e2…`).

## When to load

Load this skill before any Cursor (or Project Shell) step that will invoke a device agent CLI through an adapter. That includes Codex, Hermes, and any later adapter, whether or not the job touches GBrain. Skip only when the job never starts an agent CLI.

## Caller selection

The BRIEF selects the adapter for this job.

- `agent:` names one adapter directory under `adapters/`.
- `agents:` names a list. Each entry is one session.
- If both keys are set, stop with `STATUS: STUCK`.
- If `agents:` is present and empty, stop with `STATUS: STUCK`.
- If the BRIEF omits both keys, use `codex`.

Several agents use several tmux sessions. Each agent gets its own session name, its own signal, and its own subdirectory of `RUN_DIR`. Each session has one completion bell. Do not put unrelated CLIs in one pane.

Sequential: start the next session only after the previous signal arrives. Parallel: start the sessions together and wait on each signal with its own waiter. See `docs/architecture.md`.

## First-run defaults and job overrides

Python 3.11+ is required. Before the first Codex launch, ask the user to choose a model, reasoning effort and whether fast is enabled, then perform the documented setup:

```sh
python3 "$SKILL_ROOT/scripts/agent_defaults.py" setup --model <chosen-model> --effort <chosen-effort> --fast false
```

Set `--fast true` only when chosen. This writes `[codex]` with `model`, `effort`, `fast` to `$SKILL_ROOT/defaults.toml` (normally `~/.cursor/skills/Cursor_sidecar/defaults.toml`). There is no forced product-model or effort fallback. Missing defaults return `STATUS: STUCK` with setup instructions; even a complete job override cannot skip first-run. Change all three later with the same command plus `--replace`; the helper backs up existing bytes as `defaults.toml.backup-*` before atomic replacement. Preserve local choices/backups separately when staging an upgrade; never bundle or commit them. An unexplained setup lock must be inspected, not deleted automatically.

The BRIEF may contain unquoted, unindented scalar keys, one per line:

```text
agent_model: chosen-model
agent_effort: high
agent_fast: true
```

Each present field overrides its saved default; omitted fields retain saved values. Duplicate keys, invalid/empty identifiers, fast other than literal `true`/`false`, unreadable BRIEF and malformed defaults fail closed. Model/effort identifiers must be supported by the installed CLI/account; the resolver validates structure, not provider entitlement. For `agents:`, flat overrides apply to every selected Codex session; use separate BRIEFs for different choices.

Configuration and BRIEF must be regular files; empty paths are refused. Setup flushes backups before replacement. A failed readback after publication reports an error and retains the backup: inspect before retrying or restoring manually, rather than automatically overwriting a concurrent change.

Pass the same `--brief /absolute/BRIEF.md` and optional `--defaults-file /absolute/defaults.toml` to both the Codex preflight and shared wrapper, and keep these inputs unchanged between checks and launch. A job-local skill copy otherwise uses the defaults beside its own SKILL.md. On the setup/resolve helper, `--defaults-file` goes before the subcommand. Example preflight: `"$SKILL_ROOT/adapters/codex/preflight.sh" --brief "$BRIEF"`; append `--brief "$BRIEF"` to the existing tmux wrapper argv as well.

Codex preflight parses the base config and validates resolved settings. The wrapper uses per-process `-c` overrides for `model`, `model_reasoning_effort`, `service_tier` and `features.fast_mode`, so it never rewrites `~/.codex/config.toml` or demands a fixed model/effort in it. Fast=true maps to `"fast"` and true; false explicitly uses `"default"` and false. Fast availability depends on the account/model and may increase usage; see [official speed documentation](https://learn.chatgpt.com/docs/agent-configuration/speed). Use `codex exec -- 'prompt'`; settings flags in `agent-cmd` are refused before `--` to prevent a second override channel. See `adapters/codex/ADAPTER.md` for details.

Hermes and `_template` explicitly mark model/effort/fast all N/A in `ADAPTER.md`, with the reason that their CLI mappings are unmeasured. Hermes still fails preflight. The wrapper refuses these new config arguments for non-Codex commands; do not guess flags or silently ignore choices.

## Preflight (fail means STUCK, do not launch)

1. Check the complete install above, including `scripts/agent_defaults.py`, then run `"$SKILL_ROOT/adapters/<name>/preflight.sh"` with the same config arguments used for launch. Codex checks version, auth file present with byte length only, base config TOML and resolved defaults plus BRIEF overrides. Hermes checks live in `adapters/hermes/preflight.sh`. Do not print secrets. Apply the GBrain pin gate below before selecting any alternate wrapper.
2. Prove a writable local `RUN_DIR` (default local disk, not an external volume). External volumes need FDA/TCC for the CLI identity first (SO #20 and #21; setup before test).
3. Resolve `tmux` to an absolute path (`TMUX_BIN`, else `/opt/homebrew/bin/tmux`, then `/usr/local/bin/tmux`, then `command -v tmux`). Pass that path as `TMUX_BIN` into the session. Bare `tmux` under a narrowed PATH has failed measured jobs.
4. Prefer `wait-for -L <signal>` before start so the waiter is armed. Use one waiter per session.
5. Any preflight fail: stop, write `STATUS: STUCK` with the failing item, exit. Cursor must not do the agent work itself as a fallback.

## Launch hard steps

1. **Forbidden:** `tmux send-keys` for multi-line text or for pasting a full wrapper or python command line. That path mangled argv (e147a4c8) so the agent never ran.
2. **Required start:** one of these.
   - `"$TMUX_BIN" new-session -d -s <session> -- env TMUX_BIN="$TMUX_BIN" python3 "$SKILL_ROOT/scripts/run-agent-with-tmux-signal.py" --agent-cmd '<one line>' --session <session> --signal <signal> --run-dir <dir> --timeout-sec <n>`
   - or write a one-line launcher script to disk, then `send-keys` only that script path (single line, no embedded newlines).
3. Shared shell: `"$SKILL_ROOT/scripts/run-agent-with-tmux-signal.py"` from the complete installed tree. One agent command per session. The script does not call `send-keys`.
4. GBrain jobs that already pin in-repo `templates/run-codex-with-tmux-signal.py` keep that KM-owned file intact. The keep-exception preserves ownership, not permission to launch it. Apply the SO19 conformance gate below. Do not rewrite the KM wrapper body from this skill or from EL.
5. Pass `RUN_DIR`, the signal name, and `agent-cmd` as arguments to the shell. Do not pass them through multi-line `send-keys`.
6. The Cursor waiter must time out. Do not leave the worker `running` forever.

`agent-cmd` is one line. Its first token is the agent binary. A Codex non-interactive job uses `codex exec` with the arguments that CLI already accepts.

## GBrain pin: keep-exception and SO19 conformance gate

Do not rewrite the KM-owned `templates/run-codex-with-tmux-signal.py` body. Citing Cursor_sidecar does not waive SO19. Before launching a pinned alternate wrapper, require normal-return **and** timeout-forced smoke evidence bound to its current SHA256. Both paths must independently read back `exit.txt` and `agent.exit` (and `codex.exit` for a `codex` basename), with identical bytes, **before** forwarding `wait-for -S`. The evidence must also show an absolute tmux executable honoring `TMUX_BIN`, one session/signal per agent, bounded waiting, and no multi-line `send-keys`.

Missing evidence, a changed wrapper hash, or any failed requirement means `STATUS: STUCK`, item `SO19 noncompliant or unverified GBrain pin`. Do not run the pin. Redirect the launch plan to `"$SKILL_ROOT/scripts/run-agent-with-tmux-signal.py"` with the selected adapter and repeat preflight/smoke. If the job requires the exact alternate path, remain STUCK for KM/Owner to resolve. Do not alter that pin, production GBrain, or standing orders to clear this gate. A signal-before-write wrapper, a `codex.exit`-only wrapper, or bare `tmux` cannot pass.

The home repo's `smoke/check-so19.py` measures the installed skill wrapper under a private real tmux server with a fixture executable named `codex`. It is a launch-shell test, not a live Codex/GBrain test. Record its normal and timeout readbacks and wrapper hash; do not reuse its pass for a different pinned wrapper.

## Completion bell (structural only)

Inside the wrapper `finally` (and on any exit path):

1. Write `exit.txt` and `agent.exit` (same bytes: measured exit or timeout reason). When the agent basename is `codex`, also write `codex.exit`.
2. Then `wait-for -S <agreed-name>`.
3. If the child hangs: timeout-force `-S` and write the timeout reason into the exit files.
4. tmux failures must not abort the exit write (write the exit files even if tmux lookups fail).
5. **Forbidden in BRIEF or prompt:** 催回执, "remember to receipt", "ring the signal". Business STUCK is not a receipt-channel failure.

## RECEIPT means worker exit (SO #23)

Once `RUN_DIR` has a RECEIPT whose first STATUS line is `STATUS: FIXED` or `STATUS: STUCK`, the Cursor private worker must deliver final state and exit. Never stay `running` after that line exists (even if wait-for was lost or an exit file was briefly missing).

## What a business-only BRIEF must say

When the brief states only the business goal (no launch tutorial), it must still bind this path with a short cite, for example:

```
Agent launch: follow fleet skill Cursor_sidecar
(on-disk ~/.cursor/skills/Cursor_sidecar/SKILL.md or RUN_DIR copy).
Do not use plugin get_skill for this name.
Selection: agent: <name> or agents: [<names>].
Omit both to default to codex.
```

Dispatchers keep the full paste in the Cursor dispatch template hard rules 7 and 11. Point workers at this skill for the launch sequence. Do not invent a second Shared fact.

## Receipt must include (missing means bounce)

- tmux session name (one per agent)
- how the session was started (`new-session -d` or a one-line script path), proving no multi-line `send-keys`
- absolute `tmux` path used
- exit-file path and contents (`exit.txt`, `agent.exit`, and `codex.exit` when the agent is codex)
- wait-for signal name, and whether the bell was normal or timeout-forced
- adapter name
- installed `SKILL_ROOT`, wrapper SHA256, and alternate-pin gate disposition (when applicable)
- for codex, the model, reasoning effort and fast request actually used, plus defaults file path (name only) and whether BRIEF overrides were applied
- for any other adapter, the version line preflight printed
- first STATUS line of RECEIPT, and that the worker exited

## Anti-jobs

- Do not publish this as a Cursor Marketplace or plugin skill unless the Owner names that publish.
- Do not register it in a GBrain plugin `get_skill` catalog.
- Do not rewrite the KM-owned GBrain wrapper body from this skill.
- Owning bot is Engineering Lead · 工程师. Other bots do not rewrite the skill body without Owner or Engineering Lead.
