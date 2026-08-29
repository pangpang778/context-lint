# baseline-mode Spec

## Problem

Adopting context-lint on an existing repo instantly floods the user with every
pre-existing violation at once, forcing a choice between an unreachable first
run (exit 1 everywhere) or weakening and scoping out rules globally. The
standard adoption move — "freeze today's violations, only flag what's new from
here on" — has no surface. `inline-ignore` handles one line at a time; there is
no whole-repo snapshot.

## Solution

Two new CLI flags that turn a one-time existing-debt freeze into the baseline
for future runs:

- **`--baseline-generate <file>`** — run every applicable rule over the root,
  compute each current violation's fingerprint, and write them into the baseline
  file (JSON). This is a capture operation: it exits **0** regardless of how
  many violations were found (internal errors still force exit 2).
- **`--baseline <file>`** — compute each current violation's fingerprint and
  compare it against the baseline file. A **matched** fingerprint is pre-existing
  debt: printed in human mode with a `[baseline]` marker and **excluded from the
  exit-1 threshold**. An unmatched fingerprint is **new**: counted toward exit 1
  and printed unmarked. Exit is **1 iff any new violation exists**.

Fingerprints make the comparison line-number-free and cross-platform stable:
`sha1(rule + relpath + message)`, where `relpath` is the file path relative to
`--root` with posix `/` separators (already the shape the engine emits). The
baseline is therefore immune to line drift and to reformatting that keeps
`rule`/`file`/`message` intact.

The comparison is a **CLI-level post-filter** over the surviving run findings.
The engine and every rule stay untouched — baseline is a reporting/adoption
seam layered on top of the existing `RunItem(file, violation)` shape. It also
composes cleanly with `inline-ignore`: a suppressed finding never reaches the
items list, so it is simply not subject to baseline comparison.

### Baseline file format (version 1)

```json
{
  "version": 1,
  "generatedAt": "<ISO-8601 timestamp>",
  "violations": [ { "rule": "...", "file": "<relpath>", "message": "..." } ]
}
```

- `violations` is the full snapshot — every violation's record, in engine order
  (order is not meaningful; comparison is set-based).
- Comparison treats the file as a **set of fingerprints**: duplicate records
  (same `rule` + `file` + `message`, e.g. repeated identical-coordinate messages
  in one file) collapse to one membership test. Each current-run violation is
  independently classified *matched* (fingerprint in the set) or *new*.

### Exit-code contract

| Operation | exit |
|-----------|------|
| `--baseline-generate` (capture) | 0 — even with violations; **2** if internal errors |
| `--baseline` (compare), no new violations | 0 |
| `--baseline` (compare), ≥ 1 new violation | 1 |
| missing / unparseable / wrong-version baseline | 2 |
| `--baseline` and `--baseline-generate` together | 2 (usage) |

The contract is unchanged by the number of *matched* (pre-existing) findings —
freezing an existing repo yields a clean run.

## User Stories

1. **As a user**, I freeze my existing debt so my next run starts clean instead
   of failing on every historical violation.

   **Acceptance:**
   - `--baseline-generate <file>` runs every applicable rule over `--root` and
     writes a version-1 JSON baseline file containing every current violation's
     `{rule, file, message}` record.
   - The exit code is 0 even when violations were found; internal errors still
     force exit 2.
   - `generatedAt` is an ISO-8601 timestamp; comparison ignores it.

2. **As a user**, I run with a baseline so pre-existing violations are frozen
   and only new ones fail the run.

   **Acceptance:**
   - A violation whose fingerprint is in the baseline is pre-existing: in human
     mode it prints with a `[baseline]` marker and does not raise the exit code.
   - A violation whose fingerprint is not in the baseline is new: it prints
     unmarked and raises the exit code.
   - If every current violation is matched, exit is 0.
   - If any violation is new, exit is 1.
   - A missing, malformed-JSON, or non-version-1 baseline file forces exit 2
     with the error on stderr.

3. **As a user**, I see baseline accounting under `--json`.

   **Acceptance:**
   - In compare mode with `--json`, the payload's `findings` list holds only the
     **new** violations; a `baseline` object reports `{ "matched": N, "new": M }`
     where `M` equals `len(findings)` and `N` + `M` equals the total violations.
   - `suppressed` from inline-ignore is still present and unchanged.
   - In human compare mode, pre-existing findings carry the `[baseline]` marker;
     the exact placement of the marker is the human-readable surface and is the
     only visual difference between matched and new.

4. **As a user**, I can adopt cleanly even if my baseline has no entries and my
   code has no perfect matches.

   **Acceptance:**
   - An empty baseline (no `violations`) or a baseline with zero fingerprints
     matching the current run makes every violation new → exit 1 (no silent
     "clean because baseline" trap).
   - Fingerprints are deterministic: identical `rule`/`file`/`message` on
     different lines (or after line-shift edits) still match, not drift.

## Implementation Decisions

- **New pure leaf module `baseline.py`.** Holds the fingerprint function, the
  compare-filter pure function, and the baseline file load/write IO. Stdlib
  only (`hashlib`, `json`). Engine and rules are not modified — compare is a
  post-filter over the existing `RunItem` shape (see "compare at the CLI").
- **Fingerprint is exactly `sha1(rule + relpath + message)`** per the brief,
  over the current violation's `rule`, the engine's already-posix `relpath`
  (the same value currently computed as `os.path.relpath(path, root)` with
  `/` separators), and the message. No line, no severity — line drift and
  severity changes cannot invalidate a match (non-goal: no line-based
  fingerprint).
- **Exact concatenation, per the brief.** Field-boundary ambiguity is accepted
  (a deliberate simplification; collisions require coincidental adjacent-token
  confusion and are out of scope).
- **Compare at the CLI**, not the engine. `filter_baseline(items, baseline_set)`
  is a pure function over `RunItem` + a fingerprint set → (new items, matched
  count). The CLI computes findings normally, then classifies them. This keeps
  the change one file (plus the CLI) instead of threading a fingerprint through
  the engine loop.
- **Baseline is a fingerprint set for comparison.** The file stores records;
  the loader collapses to a `set` so duplicate and reordered records are
  irrelevant and deterministic across `os.walk` ordering.
- **`--json` shape**: the existing `{"findings", "suppressed"}` object is
  extended with `"baseline": {"matched", "new"}` in compare mode. The brief's
  prose word "violations" is realized as the existing `findings` key to keep the
  inline-ignore contract intact. **`findings` holds only new violations in
  compare mode** (matched ones are enumerated by the `matched` count, not listed,
  since no per-item flag exists in the brief's shape). This is a real ambiguity
  in the brief and the human confirms it at C2.
- **`--baseline` and `--baseline-generate` are an argparse mutually-exclusive
  group** and both take a file path; passing both is a usage error (exit 2).
- **`generatedAt` is injected** when writing so the writer is deterministic in
  tests (which pass a fixed timestamp) while the CLI supplies `datetime.now()`.
- **Generate ignores `--json`.** Capture writes the file and prints a one-line
  confirmation; there is nothing to compare, so the `baseline` key has no
  meaning there.

## Testing Decisions

Only external behavior is asserted: matcher-free pure function unit checks
(fingerprint determinism, compare classification), baseline file round-trips
(with an injected `generatedAt` for determinism), CLI exit codes for generate /
compare / corrupt-baseline, and the `[baseline]` marker + JSON baseline counts.
Engine/rule-level tests over throwaway temp roots; the end-to-end slice drives a
committed fixture root through the real CLI as a subprocess and pins the
surviving-findings split, the marker, and the exit code.

## Out of Scope

- Auto-fix of the baseline (rebuild is manual via `--baseline-generate`) —
  explicit non-goal.
- Line-number-based or severity-based fingerprinting — explicit non-goal.
- Merging multiple baseline files, editing/pruning a baseline, or per-rule
  baselines.
- Appending to or back-filling a baseline; a file is captured as-is and compared
  as-is.
- Any change to an existing rule's judgement semantics; baseline is purely a
  reporting/adoption post-filter.
- `--baseline` semantics in generate mode, or `--json` baseline accounting in
  generate mode.