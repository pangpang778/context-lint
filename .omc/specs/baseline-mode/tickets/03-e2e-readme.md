# T3 — End-to-end baseline fixture + README

**status:** ready-for-agent · **blockedBy:** [02-compare-cli] · **seam:** S4 (e2e)

## Role

The persistent regression gate proving baseline-mode works end to end exactly as
the brief scoped it: freeze a repo, verify a clean compare, then prove a new
violation flips the run to exit 1. Plus the README documentation that makes the
adoption story a user can actually follow.

## Contract

- **Committed fixture.** A checked-in markdown fixture root under
  `tests/fixtures/baseline/` whose files trigger at least one finding from the
  existing rules when scanned by the real CLI as a subprocess. Alongside it, a
  committed `baseline.v1.json` capturing that root's frozen fingerprints
  (generated against the root with `--baseline-generate`).
- **End-to-end drive.** A `test_*` module invokes the CLI as a subprocess over
  the fixture root with `--baseline <fixture baseline>` and asserts:
  - every fixture finding is `[baseline]`-marked and absent from the exit-1
    count → exit **0** against the frozen snapshot;
  - the JSON `baseline` accounting reports `matched` = total findings,
    `new` = 0, and `findings` empty;
  - `--baseline-generate` over the same root reproduces an equivalent baseline
    (same fingerprint set, regardless of record order — set-comparison), and
    exits 0.
- **No-baseline degradation (S4).** A second drive proves the non-goal trap is
  closed: with a baseline whose fingerprint set matches nothing, every fixture
  finding is new → exit **1**, all findings present and unmarked. This also
  proves the positive path is not trivially zero.
- **README.** Document both flags — objective, the freeze→run adoption flow, the
  JSON shape, the exit-code table, and the manual-rebuild note (`--baseline` is
  never auto-updated; regenerate with `--baseline-generate`).

## Acceptance

- The frozen-snapshot drive exits 0 with every finding marked `[baseline]`.
- The no-match baseline drive exits 1 with every finding new and unmarked.
- `--baseline-generate` over the fixture reproduces the same fingerprint set as
  the committed baseline (order-insensitive).
- `--json` over the fixture shows `matched` = total findings, `new` = 0, `findings`
  empty.
- README documents both flags, the adoption flow, the JSON shape, exit codes, and
  manual rebuild.
- The existing v1 regression gate and inline-ignore gate still pass — baseline
  mode must not disturb the base rules or inline suppression.

## Integration wiring + smoke (F-0005)

The slice is a committed fixture + committed baseline + a `test_*` module that
mounts both through the real CLI as a subprocess and asserts the markers,
counts, JSON, and exit codes above. Its smoke assertion is the frozen-snapshot
subprocess run: exit 0 with the JSON `matched`/`new` split as documented.

## Not in scope

Fingerprint / IO internals — T1. Compare filter internals and the CLI wiring —
T2. Auto-updating, merging, or pruning a baseline — the whole feature's explicit
non-goals.