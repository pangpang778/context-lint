# T1 — Config loader (pure leaf)

**status:** done · **blockedBy:** [] · **seam:** S1 (loader, pure)

## Role

The loader parses and validates the root config, turning raw text into a
validated `Config` contract that the engine (T2) can trust. It is the pure
heart of the feature — fully demonstrable on its own, before any engine wiring.

## Contract

- **Input:** configuration text plus the set of known rule ids (from the
  registry). **Output:** a frozen `Config` holding the `ignore` id set and the
  `{rule: severity}` override map, or raise `ConfigError`.
- **`ignore`:** an optional JSON array of rule ids. Entries must be strings and
  must be known rule ids.
- **`severityOverrides`:** an optional JSON object of `rule → severity`.
  Keys must be known rule ids; values must be exactly `"high"` or `"low"`.
- **Top-level shape:** the config must be a JSON object. Unknown top-level keys
  are a `ConfigError` (anti-silent-failure: a typo'd key cannot no-op). Unknown
  ids in either map are reported with the offending id(s).
- **Empty config:** missing file is the caller's signal and maps to an empty
  `Config` (no parsing). The text `{}` is a valid empty configuration. Any other
  present-but-broken JSON (including an empty file) is a `ConfigError`.
- `ConfigError` is a dedicated exception with a human-readable message naming
  the offending field/value — it is NOT an `InternalError` and NOT a violation.

## Acceptance

- `{}` parses to an empty config with no effect.
- `ignore` and `severityOverrides` populated correctly from a well-formed
  object.
- An unknown id in `ignore` raises `ConfigError` that names the id.
- An unknown key in `severityOverrides` raises `ConfigError` that names the id.
- A severity value other than `"high"`/`"low"` raises `ConfigError` naming the
  value.
- Malformed JSON, a non-object root, a non-list `ignore`, a non-string `ignore`
  entry, and an unknown top-level key each raise `ConfigError`.
- The empty text (an empty file) raises `ConfigError`; only a *missing* file
  maps to the empty config.
- A rule listed in both maps is present in `ignore` (override is moot).

## Integration wiring + smoke (F-0005)

A `test_*` module asserts the loader on string literals (no fixtures) and a
one-line `if __name__ == "__main__"` self-check drives two known texts through
the loader with `assert`, so the slice is importable and runnable in isolation.
The engine consumes its public entry point in T2; nothing mounts it yet beyond
the self-check.

## Not in scope

Engine application, severity remap, exit-gate change, CLI, e2e — T2/T3.