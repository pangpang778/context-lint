# T2 — Engine filter + suppressed counts + CLI `--json`

**status:** ready-for-agent · **blockedBy:** [01-matcher] · **seam:** S2 (engine integration)

## Role

Wire the matcher into the run: findings anchored on protected lines are dropped
from the result, counted per rule into a new suppressed map, and surfaced under
`--json`. This is the vertical slice that makes suppression actually bite at the
exit code and the CLI.

## Contract

- **Result carries suppression.** The run result gains a `suppressed` field: a
  rule→count map of findings the engine dropped. It defaults to empty so an
  existing positional construction of the result shape still works; the engine
  always sets it from its own run.
- **Per file, once.** For each scanned file, compute the protected-line map once,
  then filter and count each rule's findings against it as they are produced.
  Suppression is line-anchored, so it applies to every rule uniformly.
- **Filtered findings vanish.** A finding whose rule is in the protected line's
  set (or whose line is all-rules) never reaches the items list and never
  contributes to the exit-1 threshold.
- **Counts real.** Each dropped finding increments its rule's count in the
  suppressed map; a rule that never fired simply has no entry.
- **Error handling untouched.** Internal errors and rule crashes still flow to
  the errors list and still force exit 2. Suppression never swallows or relabels
  an error.

## Acceptance

- A finding suppressed by a trailing marker, a standalone marker, and a scoped
  marker is absent from the items list and from the exit-1 count.
- A scoped marker suppresses only its named rule; a different rule's finding on
  the same protected line still appears.
- The suppressed map counts each rule correctly across multiple files.
- Suppressing the last finding of a root yields a clean (0) exit and an empty
  items list.
- An internal error in the same root still yields exit 2 with the error on
  stderr, even when other files' findings were suppressed.
- A crashing rule is still an internal error, not a suppressed finding.
- A marker in one file does not suppress another file's findings.
- `--json` output changes shape to report suppression. **This is the breaking
  change confirmed at C2:** the payload becomes an object
  `{"findings": [...], "suppressed": {<rule>: <count>}}`, findings list holding
  only unsuppressed findings. Existing `--json` expectations that asserted a
  flat list are updated to the new object shape in this ticket.
- Human-readable output is unchanged in format; suppressed findings are simply
  absent (no human-mode count).

## Integration wiring + smoke (F-0005)

This ticket wires the matcher's public entry point into the engine run loop and
threads the suppressed map through the CLI's `--json` renderer, then adds
engine-level and CLI-level tests over throwaway root directories (a `test_*`
module). The smoke assertion is a CLI invocation over a temp root containing a
suppressed finding: it must exit 0 and emit `suppressed` with the right count.

## Not in scope

The off-repo fixture corpus and the end-to-end regression suite across all
three placement forms — T3. Matcher semantics — T1.