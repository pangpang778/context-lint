# inline-ignore Spec

## Problem

context-lint flags violated lines but offers no way to mark a specific line as a
deliberate exemption. Real shipyard files carry transient or positional fixes
that a reviewer wants to green-light locally without weakening the rule itself.
Today the only knob is the whole rule via `scope.py`; there is no per-line
opt-out.

## Solution

Add an inline-ignore marker: an HTML comment on a line (or on the standalone
line immediately before it) suppresses the linter's findings anchored at that
line. Bare markers suppress every rule; a marker may name a comma-separated rule
list to suppress only those. Suppressed findings are dropped from the result and
— critically — are **not** counted toward the exit-1 threshold, but each rule's
suppressed count is reported under `--json`.

The mechanism is a pure matching layer over the existing rules. No rule's
judgement semantics change; the engine simply filters anchored findings through
a per-file suppression map.

### Marker forms

```
<!-- context-lint:ignore -->
<!-- context-lint:ignore <rule-id>,<rule-id>,... -->
```

Rule ids in a scoped marker are the full rule ids (e.g.
`context-lint:ignore durability/spec-coordinates`). Whitespace around ids is
trimmed. A scoped marker suppresses only the listed rules; the bare form
suppresses all rules. An empty scoped list (`ignore ` with nothing after) is
treated as bare (all rules).

### Placement and resolution

- **Trailing** — a marker appearing after content on the same line protects the
  violations anchored at that line.
- **Standalone** — a line whose only content (aside from surrounding whitespace)
  is one or more markers protects the violations anchored at the immediately
  following line, and, being a marker on its own line, also protects its own
  line.

A protected line's suppression set is the union of every marker that protects
it. If any bare marker protects a line, the line is exempt from *all* rules;
otherwise only the union of the listed rule ids is exempt.

Violation anchor lines under this feature:
- **context-md/entry-format** — the entry's `## <term>` heading line.
- **durability/spec-coordinates** — the line holding the flagged token.
- **claude-md/sections** — the file's first heading line (all missing-section
  findings anchor there).

Because suppression is line-anchored, all three existing rules are covered
uniformly: no rule needs to know the feature exists.

**Placement constraint (implementing this taught the spec):** a rule that
anchors findings at a file level — `claude-md/sections` anchors all its findings
at the file's *first* heading — is suppressed only when a standalone marker or a
trailing marker sits **directly on / immediately above that anchor line**. A
blank line between the marker and the first heading (the natural way a user
drafts it) moves the marker's protection onto the blank line, and suppression
fails silently. The marker must be flush against the anchor.

## User Stories

1. **As a user**, I place a bare marker on a line (or on the standalone line
   right before it) to exempt all findings anchored at that line.

   **Acceptance:**
   - A trailing bare marker suppresses every assigned rule's findings on that
     line; none appear in the result and none raise the exit code.
   - A standalone bare-marker line suppresses the following line's findings for
     every assigned rule.
   - A standalone marker also suppresses anything assigned to its own line.

2. **As a user**, I place a scoped marker naming one or more rule ids to exempt
   only those rules, leaving others on the same line intact.

   **Acceptance:**
   - Only the named rules' findings on the protected line are suppressed;
     unlisted rules' findings on that line are unchanged.
   - Ids are trimmed of surrounding whitespace; the bare (list-less) form means
     all rules.
   - An unrecognised or malformed marker (missing close, typo in the directive
     word) matches nothing and suppresses nothing.

3. **As a user**, when findings are suppressed, `--json` tells me how many each
   rule lost.

   **Acceptance:**
   - A per-rule suppressed count is present in the `--json` output.
   - Suppressed findings are absent from the JSON findings list.
   - In human-readable mode suppressed findings are simply absent (shortest
     surface; no human-mode count is added).

4. **As a user**, suppression is per-file and never weakens error handling.

   **Acceptance:**
   - A marker in one file never affects another file.
   - Suppressing the last finding leaves the exit code clean (0) — suppressed
     findings never count toward exit 1.
   - An internal error still forces exit 2 and still surfaces on stderr whether
     or not findings on the same or other files were suppressed.
   - A crashing rule remains an internal error; the suppression layer never
     swallows or relabels it.

## Implementation Decisions

- **New pure leaf module** housing the matcher: markdown text in, a line→
  suppressed-rule-set map out. The "all rules" condition is represented by a
  single sentinel member (`*`). Stdlib only.
- **Matcher contract**: returns a map keyed by 1-based protected line to a set
  of rule ids (or the all-rules sentinel). Both placements converge onto this
  one map: a trailing marker contributes to its own line; a standalone marker
  contributes to its own line and the next line. Rule ids are matched verbatim
  after trimming.
- **`RunResult` gains a `suppressed` field** — a rule→count map of findings the
  engine dropped. It defaults to empty so any existing positional construction
  keeps working; the engine always sets it from its own run.
- **Engine**: compute the protected-line map once per scanned file, then filter
  and count each rule's findings against it as they are produced. Filtering is
  post-hoc at the engine, so rule functions stay unaware of the feature.
- **`--json` shape change**: per-rule suppressed counts cannot sit inside a flat
  findings list, so the JSON payload becomes an object of the form
  `{"findings": [...], "suppressed": {<rule>: <count>}}`. This is a **breaking
  change** to the existing flat-list contract; the human confirms it at C2.
  Existing `--json` list expectations in the test suite are updated to the new
  shape in the ticket that touches the CLI.
- **Human-readable output** keeps its format; suppressed findings are merely
  not printed.

## Testing Decisions

Only external behavior is asserted — line-anchored filtering, counts, exit
codes, and JSON round-trips. The matcher is tested purely (text in, map out)
with no fixtures. Engine/CLI behavior runs over throwaway root directories;
the end-to-end slice runs a committed fixture root through the real CLI as a
subprocess and checks stdout shape, the suppressed counts, and exit codes.

## Out of Scope

- Whole-file ignore (a marker covering an entire file), block/range ignore (a
  marker opening and closing an interval), and `--fix`.
- Baseline / suppressions persisted across runs — a later feature.
- Any change to an existing rule's judgement semantics; this feature is purely a
  filtering layer.
- Any config surface; markers are the only mechanism.
- A suppressed count in human-readable mode (JSON only, per the brief).