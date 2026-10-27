# Cursor_sidecar

Stable launch path from Cursor to a device agent CLI.

<!-- Cover image (docs/assets/social-preview.png) lands after Art Director QC + Owner approval. Follow-up PR. -->

**Languages:** [English](README.md) · [简体中文](docs/i18n/README.zh-CN.md) · [日本語](docs/i18n/README.ja.md) · [한국어](docs/i18n/README.ko.md)

---

## What it is

**Cursor_sidecar** is the public home for the fleet skill of the same name (formerly `cursor-codex-launch`).

When Cursor — including a Project Shell — needs to start a device agent CLI, this skill defines the shared path: a **tmux launch shell**, a **per-agent adapter**, a **preflight** gate, and a **completion bell** so the worker knows when to exit.

It lives on disk as a fleet skill, not as a plugin catalog entry.

**Owning bot:** tinkabot · 插件技能MCP  
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

On machines that run the fleet:

```
~/.cursor/skills/Cursor_sidecar/SKILL.md
```

Jobs may also keep a copy under the job `RUN_DIR`. Load this file before any Cursor step that will start an agent CLI through an adapter.

This name is **not** a GBrain / plugin `get_skill` catalog entry. Briefs must not call plugin `get_skill` for `Cursor_sidecar`.

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

1. Run `adapters/<name>/preflight.sh`. On failure → `STATUS: STUCK`, stop. Do not launch.
2. Prefer `tmux new-session -d` with env/argv into the shared wrapper. **Do not** paste a multi-line wrapper via `tmux send-keys` (that mangled argv and left the agent unstarted).
3. Shared shell: `scripts/run-agent-with-tmux-signal.py` — one agent command per session.
4. Waiter must time out; do not leave the worker `running` forever.

Full hard rules live in the skill body and in `docs/architecture.md`.

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
- **Not** a license to rewrite the KM-owned GBrain wrapper body (`templates/run-codex-with-tmux-signal.py`). GBrain jobs that already pin that file keep it.

---

## Links

| What | Where |
| --- | --- |
| Skill body | `~/.cursor/skills/Cursor_sidecar/SKILL.md` (or job `RUN_DIR` copy) |
| Shared shell | [`scripts/run-agent-with-tmux-signal.py`](scripts/run-agent-with-tmux-signal.py) |
| Adapters | [`adapters/`](adapters/) |
| Architecture | [`docs/architecture.md`](docs/architecture.md) |
| Public repo | [Kkkkkuro/Cursor_sidecar](https://github.com/Kkkkkuro/Cursor_sidecar) |
