# Cursor_sidecar

Public home for the fleet Cursor_sidecar skill. Cursor starts a device agent CLI through a shared tmux launch shell and a per-agent adapter.

- Skill path on machines: `~/.cursor/skills/Cursor_sidecar/SKILL.md`
- Shared shell: `scripts/run-agent-with-tmux-signal.py`
- Adapters: `adapters/codex/`, `adapters/hermes/`, and `adapters/_template/`
- A BRIEF sets `agent:` or `agents:`. Omitting both defaults to `codex`.
- Not a GBrain plugin `get_skill` name
- Do not publish to the Cursor Marketplace unless the Owner names that publish
- Cursor Project: **Cursor_sidecar** (owned by tinkabot)

The shell rules and the BRIEF cite live in the skill. Adapter rules live in `adapters/README.md`. Session patterns live in `docs/architecture.md`.

Formerly known as `cursor-codex-launch`.
