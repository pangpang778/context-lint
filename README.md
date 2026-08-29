# context-lint

Lint shipyard-harness markdown discipline (stdlib-only, pytest). Read-only audit:
exit **0** clean, **1** violations, **2** usage/internal error.

```
python -m context_lint --root <repo>
python -m context_lint --root <repo> --json
```

## Baseline mode — adopt a linter on an existing repo

Context-lint flags *every* violation, so first-running it on a mature repo exits 1
everywhere. Baseline mode freezes today's debt and only flags what is new from
then on.

**1. Freeze existing violations into a baseline file** (a capture; exits 0 even
when violations exist):

```
context_lint --root <repo> --baseline-generate baseline.json
```

**2. Run against it** — pre-existing findings are marked `[baseline]` and excluded
from the exit-1 threshold; only *new* findings fail the run:

```
context_lint --root <repo> --baseline baseline.json
```

Fingerprints are `sha1(rule + relpath + message)` — line-free and cross-platform
stable, so line edits (drift) don't invalidate a match. `relpath` is relative to
`--root` with posix `/` separators.

**JSON** (compare mode) reports the split — `findings` holds only new violations:

```json
{ "findings": [...], "suppressed": {...}, "baseline": { "matched": 3, "new": 1 } }
```

**Baseline file (version 1):**

```json
{ "version": 1, "generatedAt": "<ISO-8601>", "violations": [ { "rule": "...", "file": "<relpath>", "message": "..." } ] }
```

### Exit codes

| Operation | exit |
|-----------|------|
| `--baseline-generate` (capture) | 0 — even with violations |
| `--baseline`, no new violations | 0 |
| `--baseline`, ≥ 1 new violation | 1 |
| missing / malformed / wrong-version baseline | 2 |
| `--baseline` + `--baseline-generate` together | 2 |

`--baseline` and `--baseline-generate` are mutually exclusive.

### Manual rebuild only

`--baseline` is never auto-updated. When you want to promote today's remaining
new violations into "known debt" (or a rule's messages change), regenerate:

```
context_lint --root <repo> --baseline-generate baseline.json
```