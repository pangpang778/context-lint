# T1 — Inline-ignore matcher (pure leaf)

**status:** ready-for-agent · **blockedBy:** [] · **seam:** S1 (matcher, pure)

## Role

The matcher is the pure heart of the feature: markdown text in, a line→
suppressed-rule-set map out. It exists and is fully demonstrable on its own
before the engine is touched, giving the engine a stable contract to consume.

## Contract

- Input: raw file text. Output: a map keyed by **1-based protected line** to the
  set of rule ids suppressed on that line, with a single sentinel member (`*`)
  standing for "all rules".
- Two placements converge onto the map:
  - a **trailing** marker (marker after content on the same line) adds its
    suppression to that line;
  - a **standalone** marker (the line's only non-whitespace content) adds its
    suppression to its own line *and* the immediately following line.
- Marker syntax: `<!-- context-lint:ignore -->` (bare → all rules) or
  `<!-- context-lint:ignore <id>,<id>,... -->` (scoped). Ids are trimmed of
  surrounding whitespace and matched verbatim; an empty id list behaves as bare.
- Merge rule on a protected line: if any bare marker protects it, the line is
  all-rules (`*`); otherwise the union of the scoped ids.
- A malformed marker (missing close, misspelt directive word) contributes
  nothing.

## Acceptance

- Trailing bare marker → the line maps to `*` (all rules).
- Standalone bare marker on line N → line N and line N+1 both map to `*`.
- Trailing scoped marker listing two ids → the line maps to exactly those two.
- Standalone scoped marker → only the following line is protected, and only by
  the listed ids.
- Ids with surrounding spaces are trimmed before matching.
- A line with a scoped marker names only ids A and B; a finding from rule C on
  that line is not suppressed.
- Malformed markers (partial, typo) produce no suppression for any line.
- A protected line reached by both a bare and a scoped marker is all-rules.

## Integration wiring + smoke (F-0005)

The matcher is a module with a public entry point; this ticket adds a `test_*`
module covering the matcher on string literals (no fixtures) and a one-line
`if __name__ == "__main__"` self-check that runs two known texts through the
matcher and asserts the resulting maps with `assert`, so the slice is runnable
and importable in isolation. The engine consumes its public entry point in T2;
nothing mounts it yet here besides the self-check.

## Not in scope

Engine filtering, suppression counts, `--json`, exit codes, CLI — all T2.