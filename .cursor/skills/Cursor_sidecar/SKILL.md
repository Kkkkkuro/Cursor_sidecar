---
name: Cursor_sidecar
description: >-
  Use when Cursor (including a Project Shell) will start any device agent CLI
  through an adapter and the shared tmux launch shell. Covers codex, hermes,
  and future CLIs. A BRIEF that omits agent selection defaults to codex.
  Stable launch path, completion bell, preflight, and the cite a business-only
  BRIEF must include (never plugin get_skill). Formerly cursor-codex-launch.
---

# Cursor_sidecar (fleet skill)

Stable call path for starting a device agent CLI from Cursor. The caller chooses the agent. This skill does not hard-code a single product as the only path.

Authority is the Shared completion bell, then machine `grokbot-cursor-standing-orders` **#19** and **#23** (and the matching hard rules in the Cursor dispatch template). This skill does not restate Shared. If wording conflicts, Shared wins, then SO #19 and SO #23.

**Shape:** fleet on-disk skill at `~/.cursor/skills/Cursor_sidecar/SKILL.md`, or a copy under the job `RUN_DIR`. It is not a GBrain or plugin catalog name. Briefs and workers must not call `plugin get_skill` or `get_skill` for `Cursor_sidecar` or the retired name `cursor-codex-launch`.

**Home repo / Project:** [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar) (public). Owning bot: tinkabot · 插件技能MCP.

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

## Preflight (fail means STUCK, do not launch)

1. Run `adapters/<name>/preflight.sh`. Codex checks live in `adapters/codex/preflight.sh` (version, auth file present with byte length only, config `model` `gpt-6.1-sol` and `model_reasoning_effort` `xhigh`). Hermes checks live in `adapters/hermes/preflight.sh`. Do not print secrets.
2. Prove a writable local `RUN_DIR` (default local disk, not an external volume). External volumes need FDA/TCC for the CLI identity first (SO #20 and #21; setup before test).
3. Resolve `tmux` to an absolute path (`TMUX_BIN`, else `/opt/homebrew/bin/tmux`, then `/usr/local/bin/tmux`, then `command -v tmux`). Pass that path as `TMUX_BIN` into the session. Bare `tmux` under a narrowed PATH has failed measured jobs.
4. Prefer `wait-for -L <signal>` before start so the waiter is armed. Use one waiter per session.
5. Any preflight fail: stop, write `STATUS: STUCK` with the failing item, exit. Cursor must not do the agent work itself as a fallback.

## Launch hard steps

1. **Forbidden:** `tmux send-keys` for multi-line text or for pasting a full wrapper or python command line. That path mangled argv (e147a4c8) so the agent never ran.
2. **Required start:** one of these.
   - `tmux new-session -d -s <session> -- env TMUX_BIN=<abs-tmux> python3 <scripts/run-agent-with-tmux-signal.py> --agent-cmd '<one line>' --session <session> --signal <signal> --run-dir <dir> --timeout-sec <n>`
   - or write a one-line launcher script to disk, then `send-keys` only that script path (single line, no embedded newlines).
3. Shared shell: `scripts/run-agent-with-tmux-signal.py` in this repo. One agent command per session. The script does not call `send-keys`.
4. GBrain jobs that already pin in-repo `templates/run-codex-with-tmux-signal.py` keep that file. It is KM-owned. Do not rewrite the body from this skill or from EL.
5. Pass `RUN_DIR`, the signal name, and `agent-cmd` as arguments to the shell. Do not pass them through multi-line `send-keys`.
6. The Cursor waiter must time out. Do not leave the worker `running` forever.

`agent-cmd` is one line. Its first token is the agent binary. A Codex non-interactive job uses `codex exec` with the arguments that CLI already accepts.

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
- for codex, the model and reasoning effort actually used
- for any other adapter, the version line preflight printed
- first STATUS line of RECEIPT, and that the worker exited

## Anti-jobs

- Do not publish this as a Cursor Marketplace or plugin skill unless the Owner names that publish.
- Do not register it in a GBrain plugin `get_skill` catalog.
- Do not rewrite the KM-owned GBrain wrapper body from this skill.
- Owning bot is tinkabot · 插件技能MCP. Other bots do not rewrite the skill body without Owner or tinkabot.
