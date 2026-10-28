# Install the complete skill tree

A user installs a self-contained Cursor_sidecar directory with its wrapper,
executable preflights and architecture document. `scripts/install-skill.py` validates
the bundled payload against authoritative sources and refuses to overwrite an install.

## Sub-features

- `--check` verifies the exact payload list, bytes and mirror modes without installing.
- `--dest` accepts a new or empty directory and prints `installed:` and `wrapper_sha256:`.
- Installed files and executable modes match `.cursor/skills/Cursor_sidecar/`.
- A second install into that populated destination exits 1, reports `STATUS: STUCK`,
  and preserves the existing files. A racing exclusive file creation also fails closed.

## How to get to it (user POV)

From the repository root, validate the bundle, then choose a fresh destination.
Use the [skill Launch/Doctor](../SKILL.md) first. For this standalone feature,
set `EVIDENCE_DIR="$RUN_DIR/evidence/install-skill-complete-tree/$RUN_ID"`.
Never select an existing home skill directory or replace a deployed installation.

## Driving it with Bash and Python

After Launch/Doctor, use this feature's Drive instead of the default wrapper Drive:

```bash
run python3 scripts/install-skill.py --check
run python3 scripts/install-skill.py --dest "$INSTANCE/skill"
run python3 -E - <<'PY'
import hashlib, json, os, subprocess, sys
from pathlib import Path
source = Path('.cursor/skills/Cursor_sidecar')
dest = Path(os.environ['INSTANCE']) / 'skill'
def snapshot(root):
    return {p.relative_to(root).as_posix(): [hashlib.sha256(p.read_bytes()).hexdigest(),
                                           p.stat().st_mode & 0o777]
            for p in sorted(root.rglob('*')) if p.is_file()}
before = snapshot(dest)
assert before == snapshot(source), 'installed payload differs'
cmd = [sys.executable, 'scripts/install-skill.py', '--dest', str(dest)]
print('command:', cmd)
proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
print(proc.stdout, proc.stderr, f'exit_code: {proc.returncode}')
assert proc.returncode == 1 and 'STATUS: STUCK' in proc.stderr
assert 'existing installs are never overwritten' in proc.stderr
assert snapshot(dest) == before, 'refused install changed files'
evidence = Path(os.environ['EVIDENCE_DIR'])
evidence.mkdir(parents=True, exist_ok=False)
(evidence / 'payload.json').write_text(json.dumps(before, indent=2) + '\n')
(evidence / 'overwrite-refusal.txt').write_text(proc.stderr + f'exit_code: {proc.returncode}\n')
manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence.iterdir()}
(evidence / 'sha256.json').write_text(json.dumps(manifest, indent=2) + '\n')
(Path(os.environ['PROOF_DIR']) / 'artifact-sha256.json').write_text(json.dumps(manifest, indent=2) + '\n')
PY
```

This archives the standalone feature's Evidence. Skip the wrapper-specific Evidence
block; run the common Cleanup and verify `post-cleanup.json` plus the preserved
`payload.json`, refusal output and command transcript.

## Gotchas

`SKILL.md` alone is incomplete. Bundle validation happens before destination creation.
An existing symlink destination is refused. A racing install may leave a partial
new destination; retain that attempt for diagnosis and use a fresh instance next time.
Do not refresh mirrors or change wrapper behavior just to make verification pass.
