# context-lint

Lint shipyard-harness markdown discipline (stdlib-only, pytest). Read-only audit:
exit **0** clean or low-severity-only, **1** a surviving **high-severity**
violation, **2** usage/internal/config error.

## Configuration — `.context-lint.json`

An optional file at the scanned root tunes two controls. A missing file is an
empty configuration; the tool runs exactly as before.

```json
{
  "ignore": ["rule-id"],
  "severityOverrides": { "rule-id": "high" }
}
```

- **`ignore`** — a rule-id list. Ignored rules are disabled outright: they
  produce no findings, appear nowhere in output, and never fail the run.
- **`severityOverrides`** — a rule-id → `"high"`/`"low"` map. Every finding of
  that rule is re-judged at the new severity in both human and `--json` output,
  and at the exit gate. A rule in both maps is ignored (the override is moot).

**Exit semantics.** A finding's severity now decides the gate: exit **1** fires
only when a surviving, non-exempt finding is severity `high`. `low` findings are
still reported but no longer fail the run. "Non-exempt" composes the exemption
stacks — config `ignore`, inline suppression, and a baseline match.

**Bad config never fails silently.** Malformed JSON, a non-object root, an
unknown rule id, a non-`high`/`low` severity value, or an unknown top-level key
each exit **2** with a `config error:` line on stderr naming the problem (and
the offending id). Use `{}` for an empty config.

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
| `--baseline`, ≥ 1 new high-severity violation | 1 |
| missing / malformed / wrong-version baseline | 2 |
| `--baseline` + `--baseline-generate` together | 2 |

`--baseline` and `--baseline-generate` are mutually exclusive.

### Manual rebuild only

`--baseline` is never auto-updated. When you want to promote today's remaining
new violations into "known debt" (or a rule's messages change), regenerate:

```
context_lint --root <repo> --baseline-generate baseline.json
```