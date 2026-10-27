---
name: Cursor_sidecar
description: >-
  Use when Cursor (including a Project Shell) will start Codex via CLI — stable
  launch path, completion bell, preflight, and how a BRIEF that only states
  business goals must cite this fleet skill (never plugin get_skill). Formerly
  cursor-codex-launch.
---

# Cursor_sidecar (fleet skill)

Stable call path for starting Codex from Cursor. Authority is Shared **External-worker completion bell** plus machine `grokbot-cursor-standing-orders` **#19** and **#23** (and the matching hard rules in the Cursor dispatch template). This skill does **not** restate Shared as a twin; if wording ever conflicts, Shared wins, then SO #19/#23.

**Shape:** fleet on-disk skill — `~/.cursor/skills/Cursor_sidecar/SKILL.md`, or a copy under the job `RUN_DIR`. It is **not** a GBrain / plugin catalog name. Briefs and workers must **not** call `plugin get_skill` / `get_skill` for `Cursor_sidecar` (or the retired name `cursor-codex-launch`).

**Home repo / Project:** [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar) (public). Owning bot: tinkabot · 插件技能MCP.

Evidence for the launch hard rule: t1895u-r1 STUCK RECEIPT `e147a4c8` (tmux `send-keys` multi-line mangled `python3 '/Users/...`; wrapper and Codex never started). Mini smoke t2869u FIXED (RECEIPT sha256 `5a3b22e2…`).

## When to load

Load this skill before any Cursor (or Project Shell) step that will invoke Codex via CLI, including GBrain doctor/upgrade knives and non-GBrain AI_Workspace jobs. Skip only when the job never starts Codex.

## Preflight (fail ⇒ STUCK, do not launch)

1. Prefer the repo's `scripts/codex-preflight.sh` when present. If missing: `codex --version`; prove Codex auth exists (**never print secrets**); prove `~/.codex/config.toml` is model `gpt-6.1-sol`, reasoning `xhigh`.
2. Prove a **writable local** `RUN_DIR` (default local disk, not an external volume). External volumes need FDA/TCC for the Codex CLI identity first (SO #20/#21; setup before test).
3. Resolve `tmux` to an **absolute** path (`TMUX_BIN`, else `/opt/homebrew/bin/tmux` → `/usr/local/bin/tmux` → `command -v tmux`). Bare `tmux` under a narrowed PATH has failed measured jobs.
4. Prefer `wait-for -L <signal>` before start so the waiter is armed.
5. Any preflight fail: stop, write `STATUS: STUCK` with the failing item, exit. Cursor must not do the Codex work itself as a fallback.

## Launch hard steps

1. **Forbidden:** `tmux send-keys` for multi-line text or for pasting a full wrapper/python command line. That path mangled argv (e147a4c8) so Codex never ran.
2. **Required start:** one of:
   - `tmux new-session -d -s <session> -- env <KEY=VAL...> python3 <wrapper.py> <wrapper-args...>`
   - or write a **one-line** launcher script to disk, then `send-keys` **only that script path** (single line, no embedded newlines).
3. Wrapper choice:
   - GBrain: in-repo `templates/run-codex-with-tmux-signal.py` (**KM-owned**; do not rewrite the body from this skill or from EL).
   - Non-GBrain: `AI_Workspace/00_全局控制台/templates/run-codex-with-tmux-signal.py` (fleet mirror; may diverge).
4. Pass RUN_DIR, signal name, prompt path, and model/effort via **env argv**, not via multi-line `send-keys`.
5. Cursor waiter must **timeout**. Do not leave the worker `running` forever.

## Completion bell (structural only)

Inside the wrapper `finally` (and on any exit path):

1. Write exit artifacts: `exit.txt` **and** `codex.exit` (contents = measured exit / timeout reason).
2. Then `wait-for -S <agreed-name>`.
3. If the child hangs: **timeout-force** `-S` and write the timeout reason into the exit files.
4. tmux failures must not abort the exit write (write exit even if tmux lookups fail).
5. **Forbidden in BRIEF/prompt:**催回执 / "remember to receipt" / "ring the signal". Business STUCK ≠ receipt-channel failure.

## RECEIPT ⇒ worker exit (SO #23)

Once `RUN_DIR` has a RECEIPT whose first STATUS line is `STATUS: FIXED` or `STATUS: STUCK`, the Cursor private worker must deliver final state and **exit**. Never stay `running` after that line exists (even if wait-for was lost or `codex.exit` briefly missing).

## What a business-only BRIEF must say

When the brief states only the business goal (no launch tutorial), it must still bind this path with a short cite, for example:

```
Codex launch: follow fleet skill Cursor_sidecar
(on-disk ~/.cursor/skills/Cursor_sidecar/SKILL.md or RUN_DIR copy).
Do not use plugin get_skill for this name.
Paste dispatch-template Codex block (hard 7+11) if the template is the carrier.
```

Dispatchers: keep the full paste in the Cursor dispatch template hard rules 7 and 11; point workers at this skill for the launch sequence. Do not invent a second Shared fact.

## Receipt must include (missing ⇒ bounce)

- tmux session name
- how the session was started (`new-session -d` vs one-line script path) — prove no multi-line `send-keys`
- absolute `tmux` path used
- `codex exec` exit-file path + contents (`codex.exit` / `exit.txt`)
- wait-for signal name + normal vs timeout-forced
- model and reasoning effort actually used
- first STATUS line of RECEIPT, and that the worker exited

## Anti-jobs

- Do not publish this as a Cursor Marketplace / plugin skill unless Owner names that publish.
- Do not register it in a GBrain plugin `get_skill` catalog.
- Do not rewrite KM-owned GBrain wrapper body from this skill.
- Owning bot is **tinkabot · 插件技能MCP**; other bots do not rewrite the skill body without Owner/tinkabot.
