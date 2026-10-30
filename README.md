# Cursor_sidecar

Stable launch path from Cursor to a device agent CLI.

![Cursor_sidecar cover](docs/assets/social-preview.png)

**Languages:** [English](README.md) · [简体中文](docs/i18n/README.zh-CN.md) · [日本語](docs/i18n/README.ja.md) · [한국어](docs/i18n/README.ko.md)

---

## What it is

When you write code or change a repo in Cursor, you sometimes need to hand the work to an agent already installed on this device — Codex or Hermes today, and later Claude, Kimi, and similar tools.

In this skill, we use tmux so Cursor can call those on-device agents. When a Cursor Project Agent hands out a task, as long as the task runs through this skill, it uses the external agent you named for that task: it checks the environment first, starts the agent on this machine, and rings a completion bell when the work is done so the worker knows it can finish. Different projects can each pick their own — for example Codex in one repo and Hermes in another — by saying so in that project's tasks; omit the choice and the default is Codex.

One shared path covers many agents, so you do not need a different launch setup for each tool. It is the public home for the fleet skill of the same name. It lives on disk as a complete skill directory, not as a plugin catalog entry.

**Owning bot:** Engineering Lead · 工程师  
**Repo:** [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar)

---

## Features

- **Multi-adapter selection** — BRIEF picks `agent:` (one) or `agents:` (list); omit both to default to `codex`
- **Shared tmux shell + completion bell** — one wrapper starts the agent, writes exit files, then signals waiters
- **Per-adapter preflight** — fail closed with `STATUS: STUCK`; Cursor does not do the agent work as a fallback
- **Multi-session** — sequential or parallel; each agent gets its own session, signal, and `RUN_DIR` subdirectory
- **Business-only BRIEF cite** — a short pointer is enough; no launch tutorial required in the brief
- **Receipt requirements** — session start shape, exit files, signal, adapter, and STATUS line must be present

---

## How to use

### Land the skill

Install the **complete directory**, including its wrapper and adapters. From this repo:

```sh
python3 scripts/install-skill.py --check
python3 scripts/install-skill.py --dest ~/.cursor/skills/Cursor_sidecar
```

The destination must be new or empty. The helper verifies the checked-in bundle against the repo sources, preserves executable modes, reads back the installed files, and prints the wrapper SHA256. It never overwrites an existing install. Stage upgrades in a new directory and have the install owner replace the old directory after verification. A job-local install uses `--dest "$RUN_DIR/skill-install-dst"`.

The repo's [complete skill tree](.cursor/skills/Cursor_sidecar/) can also be copied as a directory:

```text
~/.cursor/skills/Cursor_sidecar/
  SKILL.md
  scripts/run-agent-with-tmux-signal.py
  scripts/agent_defaults.py
  adapters/README.md
  adapters/{codex,hermes,_template}/{ADAPTER.md,preflight.sh}
  docs/architecture.md
```

Loading `SKILL.md` alone is insufficient. Set `SKILL_ROOT` to its absolute containing directory and resolve all relative paths there, including in a business repository or job `RUN_DIR`. Missing wrapper or selected adapter means `STATUS: STUCK`; reinstall the complete tree before launch.

This name is **not** a GBrain / plugin `get_skill` catalog entry. Briefs must not call plugin `get_skill` for `Cursor_sidecar`.

### First-run model, effort and fast

Requires Python 3.11+. Before the first Codex launch, choose all three values explicitly:

```sh
python3 "$SKILL_ROOT/scripts/agent_defaults.py" setup --model <your-model> --effort <your-effort> --fast false
```

This documented setup writes `[codex]` with `model`, `effort` and boolean `fast` to `$SKILL_ROOT/defaults.toml` (normally `~/.cursor/skills/Cursor_sidecar/defaults.toml`). Use a model and effort supported by your installed CLI/account. Missing defaults stop preflight and launch with `STATUS: STUCK` and a setup instruction; there is no forced product-model fallback. Change defaults later by repeating setup with all three values and `--replace`; the previous bytes are backed up as `defaults.toml.backup-*`. Keep local choices/backups out of Git and preserve them separately when staging an upgrade.

For one job, place unquoted, unindented scalar keys in its BRIEF:

```text
agent_model: your-model
agent_effort: high
agent_fast: true
```

Each present key overrides the saved field; omitted keys keep defaults. A saved file is still required. Pass the **same** `--brief /absolute/BRIEF.md` to preflight and the shared wrapper. Optional `--defaults-file /absolute/defaults.toml` selects another saved file on both; for the setup helper it goes **before** `setup`/`resolve`. Duplicate keys, empty/invalid identifiers, non-literal fast values and malformed TOML are refused. `agents:` applies these flat overrides to each Codex session; use separate BRIEFs for different choices.

Configuration/BRIEF paths must be regular files; empty paths are refused. If setup publishes choices but readback fails, it reports an error and retains the backup. Inspect both before retrying or manually restoring; it does not automatically overwrite a concurrent change.

```sh
"$SKILL_ROOT/adapters/codex/preflight.sh" --brief "$BRIEF"
# Append --brief "$BRIEF" to the existing tmux wrapper invocation too.
```

The wrapper applies resolved choices as per-process Codex CLI overrides; preflight validates base TOML and the resolved launch settings rather than requiring fixed model/effort values. It never rewrites `~/.codex/config.toml`. Use `codex exec -- 'prompt'`; settings flags in `agent-cmd` are refused before `--` so they cannot bypass defaults/BRIEF. Fast maps to `service_tier="fast"` plus `features.fast_mode=true`; false explicitly uses `"default"` and false. Availability is account/model dependent and fast can increase usage; see [official speed docs](https://learn.chatgpt.com/docs/agent-configuration/speed). Hermes and `_template` mark all three fields N/A in `ADAPTER.md` because their invocation/config mappings are unmeasured; Hermes remains fail-closed.

### Cite it in a business-only BRIEF

```
Agent launch: follow fleet skill Cursor_sidecar
(on-disk ~/.cursor/skills/Cursor_sidecar/SKILL.md or RUN_DIR copy).
Do not use plugin get_skill for this name.
Selection: agent: <name> or agents: [<names>].
Omit both to default to codex.
```

### Select an agent

| BRIEF field | Meaning |
| --- | --- |
| `agent: <name>` | One adapter under `adapters/` |
| `agents: [<names>]` | One session per entry |
| Both set, or `agents:` empty | `STATUS: STUCK` — fix the BRIEF |
| Both omitted | Default `codex` |

### Launch shape (high level)

1. Run `"$SKILL_ROOT/adapters/<name>/preflight.sh"`. On failure → `STATUS: STUCK`, stop. Do not launch.
2. Prefer `tmux new-session -d` with env/argv into the shared wrapper. **Do not** paste a multi-line wrapper via `tmux send-keys` (that mangled argv and left the agent unstarted).
3. Shared shell: `"$SKILL_ROOT/scripts/run-agent-with-tmux-signal.py"` — one agent command per session.
4. Waiter must time out; do not leave the worker `running` forever.

Full hard rules live in the skill body and in `docs/architecture.md`.

### GBrain pin keep-exception

Keep the KM-owned `templates/run-codex-with-tmux-signal.py` file intact; **do not rewrite the KM wrapper body**. Keeping the file does not authorize running a noncompliant pin. The skill's **SO19 conformance gate** requires current-hash normal-return and timeout-forced evidence: identical `exit.txt` + `agent.exit` (+ `codex.exit` for codex) written before `wait-for -S`, absolute tmux honoring `TMUX_BIN`, bounded waiting, and no multi-line `send-keys`.

Absent or failing evidence means `STATUS: STUCK`. Redirect the launch plan to the installed skill wrapper and repeat preflight/smoke, or leave an exact-path job STUCK for KM/Owner. A citation of Cursor_sidecar never bypasses this gate. See [smoke instructions](smoke/README.md) for isolated wrapper verification; this does not authorize a GBrain cutover.

---

## Adapters

| Adapter | Path | Notes |
| --- | --- | --- |
| Codex | `adapters/codex/` | Default when BRIEF omits selection. Preflight checks version, auth presence, and config. |
| Hermes | `adapters/hermes/` | Adapter is present. If the `hermes` CLI is missing from `PATH`, preflight fails closed. Non-interactive flags are still TODO — install the CLI before treating this path as smoke-clean. |
| Template | `adapters/_template/` | Copy when the Owner names a new agent. |

Contract details: [`adapters/README.md`](adapters/README.md).

---

## Receipt and completion

Inside the wrapper `finally` (and on any exit path):

1. Write `exit.txt` and `agent.exit` (same bytes). When the binary basename is `codex`, also write `codex.exit`.
2. Then `tmux wait-for -S <signal>`.
3. On hang: timeout must still force `-S`, with the timeout reason in the exit files.

Once `RUN_DIR` has a RECEIPT whose first STATUS line is `STATUS: FIXED` or `STATUS: STUCK`, the Cursor private worker delivers final state and **exits**.

---

## What this is not

- **Not** a Cursor Marketplace skill — do not publish there unless the Owner names that publish.
- **Not** a GBrain / plugin `get_skill` registration — do not add this name to those catalogs.
- **Not** a license to rewrite the KM-owned GBrain wrapper body (`templates/run-codex-with-tmux-signal.py`). Pinned jobs keep the file and must pass the SO19 conformance gate before using it.

---

## Links

| What | Where |
| --- | --- |
| Skill body | `~/.cursor/skills/Cursor_sidecar/SKILL.md` (or job `RUN_DIR` copy) |
| Shared shell | [`scripts/run-agent-with-tmux-signal.py`](scripts/run-agent-with-tmux-signal.py) |
| Adapters | [`adapters/`](adapters/) |
| Architecture | [`docs/architecture.md`](docs/architecture.md) |
| Public repo | [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar) |
