# T1 — Fingerprint + baseline IO (pure / IO)

**status:** ready-for-agent · **blockedBy:** [] · **seam:** S1+S2 (fingerprint, baseline IO)

## Role

The pure and IO heart of baseline-mode: (a) a deterministic fingerprint function
that maps a violation to a stable string, and (b) a loader/writer for the
version-1 baseline file. The compare filter in T2 consumes the fingerprint set
this module produces; nothing compares yet here.

## Contract

- **`fingerprint(rule, relpath, message) -> str`** (pure): hex sha1 of the exact
  concatenation `rule + relpath + message`. `rule` and `relpath` use posix
  separators; the caller (CLI) passes the already-posix relpath. No line, no
  severity — line drift must not change the fingerprint.
- **`write_baseline(path, records, generated_at)`** (IO): writes
  `{ "version": 1, "generatedAt": <ISO-8601>, "violations": [records] }` where
  each record is `{ "rule": ..., "file": <relpath>, "message": ... }`. `records`
  is a list in engine order; `generated_at` is **injected** (CLI supplies
  `datetime.now()`, tests a fixed value) so the writer is deterministic.
- **`load_baseline(path) -> frozenset[str]`** (IO): reads the file, validates
  `version == 1` and that `violations` is a list of dicts each carrying
  `rule`/`file`/`message`, returns a **set of fingerprints** (duplicates collapse;
  record order is irrelevant). Missing file, JSON decode failure, or
  `version != 1` raises a typed `BaselineError` the CLI maps to exit 2.

## Acceptance

- Fingerprints are identical for equal `rule`/`relpath`/`message`, regardless of
  the line or severity a violation carries.
- Fingerprints differ when any of the three inputs differs.
- `write_baseline` then `load_baseline` round-trips: every written record's
  fingerprint is in the loaded set; `generatedAt` is preserved verbatim.
- Two records with the same `rule`/`file`/`message` load as one set member.
- A missing file, malformed JSON, or `version != 1` raises `BaselineError`
  (propagated to the CLI as exit 2).

## Integration wiring + smoke (F-0005)

The module has public `fingerprint` / `load_baseline` / `write_baseline` entry
points. This ticket adds a `test_*` module over string literals and a temp file
(no fixtures): fingerprint determinism, a write→load round-trip with a fixed
`generated_at`, duplicate-collapse, and a `BaselineError` on a bad file. A
one-line `if __name__ == "__main__"` self-check fingerprints two known tuples
and asserts the hex values. The engine/CLI consume it in T2; nothing mounts it
here besides the self-check.

## Not in scope

Compare filtering, `[baseline]` marking, exit-code wiring, `--json` — all T2.
The committed e2e fixture and README — T3.