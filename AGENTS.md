# Workers

This repo is the public home of the Cursor_sidecar fleet skill. Workers launch device agents through that skill. They do not invent a second launch path.

Read `~/.cursor/skills/Cursor_sidecar/SKILL.md` before a launch. The copy in this repo is `.cursor/skills/Cursor_sidecar/SKILL.md`. A job may also carry a copy under its `RUN_DIR`.

Do not call plugin `get_skill` for `Cursor_sidecar` or the retired name `cursor-codex-launch`.

Do not publish this skill to the Cursor Marketplace unless the Owner names that publish.

The BRIEF selects the adapter with `agent:` or `agents:`. When both keys are absent, use `codex`. Run `adapters/<name>/preflight.sh` before the shell. A preflight failure is `STATUS: STUCK`. Leave the agent work unstarted.

Start `scripts/run-agent-with-tmux-signal.py` inside one tmux session per agent. Give each agent its own signal and its own `RUN_DIR` subdirectory.

Do not rewrite the KM-owned GBrain wrapper `templates/run-codex-with-tmux-signal.py`. Do not edit standing-order files from this repo. Add an adapter directory only after the Owner names that agent. Copy `adapters/_template/` for that work.

`PROJECT.md` is the identity doc. While the identity pull request is open, leave that file on its own branch.
