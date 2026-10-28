# Installed wrapper SO19 dual path

The completion bell must release a bounded waiter after writing identical exit
records on both normal return and forced timeout. `smoke/check-so19.py` exercises
the exact installed wrapper with real private tmux and a fixture executable named
`codex`; it starts no real Codex/Hermes job and touches no GBrain data.

## Sub-features

- Normal fixture exits 7; wrapper records `status: exit`, `code: 7`.
- Timeout fixture is terminated; wrapper records `status: timeout`, `code: 124`
  with a `timeout-force` reason.
- `exit.txt`, `agent.exit` and `codex.exit` have identical contents and SHA256 values.
- The proxy reads all exit records before forwarding `wait-for -S`; waiter exits 0.
- Launch uses `new-session -d`, absolute tmux/proxy paths and no `send-keys`.
- Installed wrapper SHA256 remains unchanged; only the private test server is stopped.

## How to get to it (user POV)

From the repository root, follow [SKILL.md](../SKILL.md) in one Bash session:
Launch → Doctor → Drive → Evidence → Cleanup. Choose fresh directories; never
use the worker's running agent session as a test target.

## Driving it with Bash and Python

The skill's default Drive installs first, then calls the existing smoke twice:

```bash
run python3 scripts/install-skill.py --dest "$INSTANCE/skill"
run python3 smoke/check-so19.py --wrapper "$INSTANCE/skill/scripts/run-agent-with-tmux-signal.py" --run-dir "$INSTANCE/n" --mode normal
run python3 smoke/check-so19.py --wrapper "$INSTANCE/skill/scripts/run-agent-with-tmux-signal.py" --run-dir "$INSTANCE/t" --mode timeout
```

Require both smoke commands to exit 0 and each `summary.json` to say PASS.
Run the skill's Evidence checks for codes 7/124, zero `send-keys`, pre-signal
readback and identical exits. Preserve `at-signal.json`, `launch.json`,
`tmux-calls.jsonl`, summaries, exit files, logs and the exact wrapper under
`$EVIDENCE_DIR`. Cleanup must remove `$INSTANCE` while that evidence and the
proof transcript/hash manifest remain readable.

## Gotchas

The smoke requires a new/empty run directory and rejects Unix socket paths over
100 bytes. The short `n`/`t` children avoid that limit on the shared Mini.
The fixture's code 7 is intentional, not a failed smoke. The timeout path uses
0.25 seconds internally; do not loosen it or extend a waiter to hide a failure.
The controller removes `TMUX`/`TMUX_PANE` from its child environment and selects
its own `-S` socket. Never use unscoped `tmux kill-server`, shared-session
`send-keys` or a live agent as a replacement probe. Evidence for one wrapper hash
does not certify another wrapper or authorize a live cutover.
