# T3 — End-to-end config fixture + exit-contract regression

**status:** done · **blockedBy:** [02-engine-cli] · **seam:** S4 (e2e)

## Role

A committed fixture root plus the exit-contract regression gate: prove config
works through the real CLI as a subprocess across both controls, all error
paths, and the no-config identity — and migrate every existing exit-code test
that assumed a `low` finding trips exit 1 to the new high-only gate.

## Contract

- **Fixture corpus.** A checked-in root whose files fire findings from at least
  one `high` rule and one `low` rule, plus config variants:
  - an ignored-root with the `high`-firing rule in `ignore`;
  - an overridden-root with the `low` rule raised to `high` (and, as the
    negative, the `high` rule lowered to `low`);
  - a broken-config root and an unknown-id root, each proving exit 2.
  At least one *unsuppressed, non-exempt* `high` finding survives somewhere so
  exit 1 is provably not trivially zero.
- **README.** Document the config file's shape (both keys), the exit-code
  contract change (exit 1 only on a surviving `high` finding), and the config
  error paths in the project README.
- **End-to-end drive.** The regression test invokes the real CLI as a subprocess
  over each fixture and asserts findings, overridden severities, `--json`
  severity values, exit codes, and the `config error: ...` stderr line.
- **Exit-contract migration.** Existing tests that asserted any violation (or a
  specifically `low` one) raises exit 1 are updated to the new gate: only a
  surviving `high` finding does. The change is mechanical but must be made
  explicitly, not by accident of coverage.
- **No-config identity.** A fixture root with no config file matches today's
  behaviour (findings, output shape, exit codes).

## Acceptance

- `ignore` neutralises the sole firing `high` rule → exit 0, rule absent from
  both outputs, absent from `suppressed`.
- Severity override raises a `low` rule's findings to `high` → they appear at
  `high` in both outputs and trip exit 1; lowering a `high` rule stops exit 1.
- Broken JSON, an unknown `ignore` id, an unknown override key, a bad severity
  value, and an unknown top-level key each yield exit 2 with a `config error`
  stderr line naming the problem.
- The no-config root behaves identically to today (same findings, same exit).
- The README documents the config file's shape, the re-judged severity shown in
  output, the high-only exit gate, and the `config error` failure modes.
- All pre-existing exit-code tests now encode the high-only gate and pass.
- The v1 regression gate still passes — config must not disturb the base rules
  or inline-ignore.

## Integration wiring + smoke (F-0005)

The slice is a committed fixture corpus plus a `test_*` module that mounts each
variant through the real CLI and asserts the outputs above; its smoke assertion
is the subprocess run over the ignored-root with exit code + JSON round-trip.

## Not in scope

Loader parse/validation internals — T1. Engine/CLI wiring and the exit-gate
change — T2.