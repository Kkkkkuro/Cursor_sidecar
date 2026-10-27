# Shared launch shell and adapters

Cursor starts device agents from one tmux launch shell. The caller picks which agent runs. The shell does not.

Authority for the completion bell is the Shared completion bell, then SO #19 and SO #23. This page names those sources. It does not restate them.

## What the shell owns

`scripts/run-agent-with-tmux-signal.py` is the shell, relative to the complete installed `SKILL_ROOT` (the directory containing the loaded `SKILL.md`). The caller puts that process in a tmux session with `new-session -d`. The process runs one agent command, writes the exit files, and then runs `tmux wait-for -S`. The agent is not asked to ring the bell.

The shell keeps these launch rules.

- Resolve `tmux` to an absolute path. `TMUX_BIN` wins when it is set. Otherwise the shell tries `/opt/homebrew/bin/tmux`, `/usr/local/bin/tmux`, then `command -v tmux`.
- Write `exit.txt` and `agent.exit` with the same bytes. When the agent binary's basename is `codex`, also write `codex.exit`.
- Write those files in `finally` before `wait-for -S`, including on timeout. A hung child is a timeout-force of the bell, with the timeout reason stored in the exit files.
- A tmux lookup failure still leaves the exit files in place.
- Do not call `send-keys` with more than one line. The supported start is `tmux new-session -d`, or a one-line script path if `send-keys` is unavoidable.
- One agent CLI per tmux session. One session has one signal and one completion bell.

A GBrain job that already pins `templates/run-codex-with-tmux-signal.py` keeps that file. That body is KM-owned. This repo does not rewrite it. The keep-exception is subject to the skill's SO19 conformance gate: normal-return and timeout-forced readbacks bound to the current wrapper SHA256, all applicable exit files written before signaling, absolute tmux honoring `TMUX_BIN`, and no multi-line `send-keys`. Missing or failing evidence is `STATUS: STUCK`. Redirect the launch plan to the installed skill wrapper and repeat preflight/smoke; an exact-path pin stays STUCK for KM/Owner.

## Installing the skill

The repo's `.cursor/skills/Cursor_sidecar/` is a self-contained directory with `SKILL.md`, the shared shell, adapter docs and executable preflights, and this architecture page. `python3 scripts/install-skill.py --check` rejects missing or stale bundled copies. `--dest <new-or-empty-directory>` installs and reads back the complete payload without overwriting an existing install. The top-level repo files remain the source for bundled mirrors; update both and run the check when they change. `SKILL.md` alone is not an installation.

## What an adapter owns

An adapter is a directory under `adapters/`. It supplies `preflight.sh` and `ADAPTER.md`. The contract is in `adapters/README.md`. Preflight proves the binary, the version, and auth without printing secrets. `ADAPTER.md` tells the caller how to build the one-line `agent-cmd`.

This repo ships `adapters/codex/`, `adapters/hermes/`, and `adapters/_template/`.

## Who picks the agent

The BRIEF picks the agent for that job.

- `agent:` names one adapter.
- `agents:` names a list of adapters.
- If the BRIEF sets both keys, stop with `STATUS: STUCK` and fix the BRIEF.
- If the BRIEF sets `agents:` to an empty list, stop with `STATUS: STUCK`.
- If the BRIEF omits both keys, the agent is `codex`. That default is back-compat for briefs that only know the old Codex path.

## Several agents

Several agents means several sessions. Each agent gets its own tmux session, its own signal name, and its own subdirectory of `RUN_DIR`. Each session rings its own completion bell. Do not place two unrelated CLIs in one pane.

Sequential work starts the next session only after the previous signal has arrived. Parallel work starts the sessions together and waits on each signal with its own waiter. Both patterns use the same shell and the same one-CLI rule. The difference is only when the caller starts the next session.
