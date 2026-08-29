# T3 — End-to-end suppressed fixture + regression gate

**status:** ready-for-agent · **blockedBy:** [02-engine-cli] · **seam:** S3 (e2e)

## Role

A committed fixture root that demonstrates every placement form against each of
the three rules, run through the real CLI as a subprocess — the persistent
regression gate proving inline-ignore works end to end exactly as the brief
scoped it (all rules, both placements, scoped and bare, correct counts, correct
exit codes).

## Contract

- **Fixture corpus.** A checked-in markdown fixture root (the off-repo
  directory) whose files trigger findings from each rule:
  - an entry-format finding suppressed by a trailing marker on the heading line;
  - an entry-format finding suppressed by a standalone marker on the line before
    the heading;
  - a spec-coordinates finding suppressed by a bare marker on the token line;
  - a spec-coordinates finding suppressed by a scoped marker naming only that
    rule;
  - a claude-md sections finding suppressed by a standalone marker before the
    first heading.
  The fixture also asserts the negative: at least one *unsuppressed* finding
  remains so the exit code is provably not trivially zero.
- **End-to-end drive.** The regression test invokes the CLI as a subprocess over
  the fixture and asserts: the unsuppressed findings list, the per-rule
  suppressed counts, the exit code, and — where the marker is scoped — that an
  unlisted rule's finding on the same protected line survives.

## Acceptance

- The fixture drive paints the full placement × rule matrix at least once:
  trailing, standalone, bare, and scoped.
- Suppressed findings are absent from stdout; unsuppressed ones still present.
- `--json` reports the expected per-rule counts, and the sum of suppressed +
  unsuppressed per rule equals the rule's total fired.
- Exit code is 1 when only an unsuppressed finding remains, and 0 on an
  all-suppressed root.
- Scoped suppression leaves the unlisted rule's finding intact on the same line.
- Existing v1 regression gate still passes — inline-ignore must not disturb the
  base rules.

## Integration wiring + smoke (F-0005)

The slice is a committed fixture plus a `test_*` module that mounts it through
the real CLI and asserts the outputs above; its smoke assertion is the subprocess
run with exit code + JSON round-trip over the fixture root.

## Not in scope

Matcher internals — T1. Engine/CLI wiring and the `--json` shape change — T2.