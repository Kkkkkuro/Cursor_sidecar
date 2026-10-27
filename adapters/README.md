# Adapter contract

The shared launch shell is `scripts/run-agent-with-tmux-signal.py`. An adapter tells that shell which CLI to run. The shell does not choose the product.

Each agent directory contains two files.

- `preflight.sh` exits 0 when the CLI can be launched. Any failure prints `STATUS: STUCK` and the failing item on stderr, then exits non-zero. The script must not print secrets. An auth proof prints a file path and a byte length, never the file contents.
- `ADAPTER.md` names the CLI, the version check, the auth proof, and how to build the one-line `agent-cmd` passed to the shell.

`agent-cmd` is one argv vector. Its first token is the agent binary. The shell does not start a second CLI in the same tmux session.

Copy `adapters/_template/` when the Owner names a new agent. Do not point a copy at a product the Owner has not named.
