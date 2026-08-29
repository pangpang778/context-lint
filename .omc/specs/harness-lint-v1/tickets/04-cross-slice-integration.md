# T4 — cross-slice integration + exit precedence

- **id:** T4
- **blockedBy:** [T2, T3]

## Output
The last frontier item (F-0005 dogfood): a whole-repo verification that all three rules accumulate correctly through one run, the exit-code precedence (internal error > violations) holds with all rules present, and a rule crash still does not abort the batch. Owns the cross-slice seams no single rule slice owns.

## Crosses every layer
- **Engine/registry** — cumulative run over a fixture exercising rule 1 + rule 2 + rule 3 together; asserts aggregated violation accumulation and JSON structure for a mixed rule set.
- **CLI** — exit-code precedence asserted explicitly: a batch with ≥1 violation AND ≥1 internal error exits 2 (errors trump, C2 #2); a batch with violations and no error exits 1; a batch with neither is clean exits 0.
- **Resilience** — a deliberately crashing rule in a mixed batch: its file records an internal error, the other files still lint, and the run exits 2 (not aborting mid-scan).

## Demonstrable smoke
- One fixture repo that is simultaneously bad in all three ways (a malformed CONTEXT.md entry, a spec coordinate, a missing CLAUDE.md section) plus one crashing hook: CLI reports the real violations AND the internal error, exits 2.

## Accepts
- T4 is complete when the three-rule accumulation, exit precedence, and crash-resilience smokes pass through the real CLI (seams S5/S6), forming the project's regression suite entry point.

## Note
- No first-pass-only assertions: this ticket is the persistent `pytest` regression gate for the whole feature.