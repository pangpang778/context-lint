# T2 — Compare filter + CLI two modes

**status:** ready-for-agent · **blockedBy:** [01-fingerprint-io] · **seam:** S3 (compare + CLI)

## Role

Make baseline-mode bite: wire the two CLI flags, classify every surviving
finding as matched (pre-existing) or new, and turn that classification into the
`[baseline]` mark, the exit code, and the `--json` baseline counts. This is the
vertical slice a user actually invokes.

## Contract

- **Mutually-exclusive flags.** `--baseline <file>` and
  `--baseline-generate <file>` are an argparse mutually-exclusive group over the
  same positional; passing both is a usage error (exit 2).
- **Generate mode.** Run the engine normally, collect every surviving violation
  as a `{rule, file, message}` record (file = the engine's posix relpath,
  message = the violation's message), call `write_baseline`, print a one-line
  confirmation. Exit **0** even when violations were found. Internal errors
  still surface on stderr and force exit 2. `--json` is ignored in this mode.
- **Compare mode.** Run the engine normally, `load_baseline`, then a pure
  `filter_baseline(items, baseline_set) -> (new_items, matched_count)` that
  classifies each `RunItem` by `fingerprint(rule, file, message)`. New items
  drive the exit code; matched items are marked and excluded.
- **`[baseline]` mark.** In human mode, every matched finding prints with a
  ` [baseline]` marker appended (after the existing
  `file:line: [sev] rule: message` line); new findings print unchanged. Line
  order is preserved.
- **Exit code.** Compare mode returns exit 1 **iff any new finding exists**;
  0 when all findings match (or the root is clean). Missing / malformed /
  non-v1 baseline and internal errors all force exit 2 with the error on stderr.
- **`--json` (compare mode).** Extend the existing payload with a `baseline`
  object: `{ "findings": [<new only>], "suppressed": {...}, "baseline": { "matched": N, "new": M } }`.
  `M == len(findings)`; `N + M ==` total surviving findings; `suppressed` is
  unchanged from inline-ignore. Matched findings are **not** listed — only
  counted. **This new-only `findings` reading and the `findings` (not the
  brief's prose "violations") key are the C2 confirmation point.**

## Acceptance

- `--baseline-generate` writes a version-1 file whose records cover every
  surviving violation and exits 0, even with violations present.
- Running `--baseline` over the identical root exits 0 with every finding marked
  `[baseline]` in human mode.
- Adding one new violation and re-running `--baseline` exits 1; the new violation
  is unmarked, the old ones still carry `[baseline]`.
- A baseline that matches nothing makes every violating root exit 1 (no silent
  clean).
- `--json` reports `baseline.matched`/`baseline.new` correctly and `findings`
  holds only new items; `suppressed` is intact.
- A missing / malformed / version-2 baseline forces exit 2 with the error on
  stderr.
- Passing both flags together exits 2 (usage).
- Internal errors force exit 2 whether or not findings were matched.

## Integration wiring + smoke (F-0005)

This ticket wires `baseline.load_baseline` / `baseline.write_baseline` /
`baseline.fingerprint` / `baseline.filter_baseline` into the CLI's two new
modes, then adds CLI-level tests over throwaway temp roots (a `test_*` module):
generate-round-trip, clean-comparison exit 0, new-finding exit 1, corrupt
baseline exit 2, both-flags usage exit. The smoke assertion is a single
`--baseline-generate` run followed by a `--baseline` run over a temp root that
must both succeed with the documented exit codes.

## Not in scope

The committed fixture corpus and the cross-mode regression gate — T3.
Fingerprint / IO internals — T1.