# T2 — Engine apply + CLI exit-gate

**status:** done · **blockedBy:** [01-loader] · **seam:** S2 (engine apply)

## Role

Wire the loader into the run: the engine loads the root config once, applies it
to the produced findings (`ignore` then `severityOverrides`), and the CLI's
exit gate and both output formats reflect the re-judged severities. This is the
vertical slice that makes configuration actually bite.

## Contract

- **Load once, per run.** The engine reads the root config at the start of a
  run; a missing file yields an empty `Config`. A `ConfigError` is surfaced to
  the caller (CLI) as exit 2 with `config error: ...` on stderr, before linting
  output.
- **Pure apply.** `violations × Config → surviving, re-judged set`: findings
  whose rule is in `ignore` are dropped entirely; the rest have their severity
  remapped per `severityOverrides`. Because `Violation` is frozen, an override
  produces a **new** `Violation`/`RunItem`; the original is untouched. The
  engine may skip running ignored rules as an equivalent optimisation.
- **Config-ignore stays out of `suppressed`.** Dropped findings never enter the
  inline-ignore `suppressed` map — config-ignore is a whole-rule disable,
  semantically distinct from per-line suppression. The two compose, never merge.
- **New severity is authoritative.** Human output and `--json` show the
  overridden severity; the exit gate evaluates it.
- **Exit gate:** return 1 iff a surviving, non-exempt finding has severity
  `"high"` after override; return 0 when only `low` (or none); return 2 on an
  internal error (unchanged). Baseline composition holds: matched/pre-existing
  findings stay exempt, and severity overrides do not affect baseline matching
  (keys on rule + file + message only).

## Acceptance

- A survival (items) list run through the pure apply: ignored rules vanish, and
  every surviving finding carries its overridden severity.
- A root with a config `ignore`ing the only firing rule exits 0 with both
  outputs empty of that rule; the ignored rule never appears in `suppressed`.
- A `high` rule overridden to `low` still prints its findings but the root
  exits 0; a `low` rule overridden to `high` makes the root exit 1.
- Human output and `--json` both render the overridden severity for every
  finding of an overridden rule.
- No config file → identical findings, output shape, and exit codes to today
  (identity check over a root).
- A present-but-broken config (bad JSON, unknown id, bad severity, unknown
  top-level key) yields exit 2, prints `config error: ...` naming the problem,
  and prints no lint findings.
- Config-ignore does not leak into the `suppressed` count of an inline marker.

## Integration wiring + smoke (F-0005)

This ticket threads the loader's public entry point into the engine run and the
remapped severities through the CLI renderers and exit gate, then adds
engine-level and CLI-level tests over throwaway root directories (a `test_*`
module). The smoke assertion is a CLI invocation over a temp root whose config
ignores its own `high` finding: it must exit 0 with that rule absent from stdout
and `--json`.

## Not in scope

The committed off-repo fixture and the full regression gate — T3. Code-layer
parse/validation of the loader — T1.