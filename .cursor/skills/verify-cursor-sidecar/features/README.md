# Cursor_sidecar feature map

Use this index when verifying a change or maintaining the local verification skill
at a stage close. Start with [Launch and Doctor](../SKILL.md), then read the affected
feature. The default complete journey is `wrapper-so19-dual-path`; installation is
its prerequisite. A row maps coverage, not a claim that a future checkout passed.

| Feature | Surface and source | Journey / evidence |
| --- | --- | --- |
| [install-skill-complete-tree](install-skill-complete-tree.md) | CLI bundle validation and isolated directory install; `scripts/install-skill.py` | Identical payload/modes, overwrite refusal; transcript and payload hashes |
| [adapters-codex-preflight](adapters-codex-preflight.md) | CLI readiness gate; `adapters/codex/preflight.sh` | Version, auth byte length, exact model/effort; curated output/exit code |
| [wrapper-so19-dual-path](wrapper-so19-dual-path.md) | Installed tmux wrapper; `smoke/check-so19.py` | Normal + timeout, bounded waiter and pre-signal exits; archived JSON/exit files |

Each feature has an H1, an intro and four H2s: `Sub-features`,
`How to get to it (user POV)`, `Driving it with Bash and Python`, `Gotchas`.
Add or refine a row when behavior changes, preserving its source and observable
acceptance. Record a run's result under the job RUN_DIR, not as permanent pass status
here. Hermes remains a documented fail-closed boundary in the skill Helpers section;
no Hermes live invocation is claimed by this map.
