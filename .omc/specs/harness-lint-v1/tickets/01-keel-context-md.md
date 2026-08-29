# T1 — Keel + context-md/entry-format

- **id:** T1
- **blockedBy:** []

## Output
The shipyard actually lints: a runnable read-only CLI that enforces rule 1 end-to-end, plus the architecture it hangs on (the rules package, the engine registry, the scope router, the CLI entrypoint). Everything a later rule needs to be *mounted*, not re-plumbed.

## Crosses every layer
- **Rules** — rule 1 pure function: markdown -> violations; detects `## <term>` entries missing any of the three labeled fields (`定义:`, `边界:`, `已解决的歧义:`). Never returns a violation on a rule crash (rule crash is an internal error).
- **Engine/registry** — registry holding rule metadata (id, severity, pure fn); runner that maps a file to its applicable rules via the scope router, walks the target files, accumulates violations, and treats a rule exception as an internal error (recorded per-file, scan continues).
- **Dispatcher (router)** — relative identity -> rule ids: root file named CONTEXT.md -> rule 1.
- **CLI** — argparse entry (via module invocation), `--root <dir>` defaulting to cwd, `--json` and human-readable output, exit contract 0/1/2 (1 = violations found; 2 = any internal error, errors trump).

## Demonstrable smoke
- On a fixture root whose CONTEXT.md has one malformed entry: CLI prints a violation and exits 1; `--json` emits a `{rule, severity, line, message}` object; a clean root exits 0 with no output; a read failure or rule crash exits 2 without aborting the rest of the batch.

## Accepts
- T1 is complete when the smoke above runs through the real CLI path, exit codes 0/1/2 are all asserted, and the seams S1, S4, S5, S6 for rule 1 are covered by external-behavior tests.

## Note
- No config surface. No file-graph/existence rules (out of scope). No auto-fix.