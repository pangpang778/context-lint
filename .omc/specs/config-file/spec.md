# config-file Spec

## Problem

context-lint's only whole-rule control is `scope.py`'s path routing; a user
cannot disable a rule repository-wide or reweight a rule's severity without
editing the registry. And today every reported finding — regardless of
severity — forces exit 1, so a `low` housekeeping warning blocks the same gate
as a `high` contract break. There is no per-project configuration surface.

## Solution

Add an optional root configuration file that carries two controls:

- `ignore`: a list of rule ids to **disable outright** — the rule produces no
  violations and none appear under `--json`.
- `severityOverrides`: a map from rule id to `"high"` / `"low"`, **re-judging**
  every violation the rule fires (shown in output, and drives the exit gate).

The file lives at the root being scanned and is optional: a missing file is an
empty configuration, and the tool runs exactly as today.

### File shape

```json
{
  "ignore": ["rule-id"],
  "severityOverrides": { "rule-id": "high" }
}
```

- `ignore` entries must be known rule ids; an unknown id is a configuration
  error (exit 2) that names the offending id.
- `severityOverrides` keys must be known rule ids and values must be exactly
  `"high"` or `"low"`; anything else is a configuration error (exit 2).
- A rule listed in both maps is **ignored** — the severity override is moot for
  a disabled rule.

### Exit semantic evolution (contract change)

Severity now means something at the gate: **exit 1 fires if and only if a
non-exempt, severity-`high` violation survives.** `low` findings are still
reported in human and `--json` output, but they no longer fail the run. A
root whose only findings are `low` exits 0.

"Non-exempt" composes the existing exemptions: not config-ignored, not
inline-suppressed, and (in baseline mode) not a pre-existing / matched finding.
Because baseline matching keys on rule + file + message — never severity — a
severity override does not disturb whether a finding matches a baseline.

The overridden severity is the one shown in human output and `--json`, and is
the severity the exit gate evaluates. This is a deliberate contract change: the
existing rule that fires `low` findings no longer trips exit 1 by itself, and
existing exit-code tests are updated to the new semantics.

## User Stories

1. **As a user**, I list a rule id under `ignore` and that rule stops firing
   entirely across the whole scan.

   **Acceptance:**
   - Ignored rules' findings appear nowhere in human or `--json` output and
     never reach the exit threshold.
   - Ignored findings do **not** appear in the inline-ignore `suppressed`
     counts — config-ignore is a rule-level disable, semantically distinct from
     per-line suppression.
   - A rule that fires only `high` findings is fully neutralised by `ignore`;
     the root exits 0.

2. **As a user**, I set a severity override and every violation from that rule
   is reported at the new severity.

   **Acceptance:**
   - `--json` and human output show the overridden severity (not the rule's
     built-in default) for every finding of that rule.
   - Overriding a `high` rule's findings to `low` stops them from tripping
     exit 1; overriding a `low` rule's findings to `high` lets them.
   - Overrides apply per rule globally, across every file.

3. **As a user**, a broken config never fails silently.

   **Acceptance:**
   - Malformed JSON, a non-object config, an unknown `ignore` id, an unknown
     `severityOverrides` key, a non-`"high"`/`"low"` severity value, or an
     unknown top-level key each exit 2 with a message that names the problem
     (and, for unknown rule ids, the offending id).
   - A messed-up config does not attempt linting — the error is reported and
     exit 2 returned, matching the "损坏 JSON → exit 2" hard lesson.

4. **As a user**, no config file means today's behaviour, unchanged.

   **Acceptance:**
   - A root without the config file runs identically: same findings, same
     output shape, same exit codes as before.
   - The empty object `{}` is a valid configuration with no effect.
   - The discovery surface is limited to the scanned root's config file; global
     and flag-based config are out of scope.

## Implementation Decisions

- **New pure leaf module** housing the loader and the pure apply step. Loader:
  config text + known rule ids in, a frozen `Config` (`ignore` ids, severity
  overrides) out, raising `ConfigError` on any malformed or unknown input.
  Missing file is handled by the caller as an empty config.
- **Pure apply step** (`violations × config → surviving, re-judged set`): takes
  the produced findings and the config, drops any whose rule is ignored, and
  remaps severity per the overrides. Rules stay unaware of the feature, exactly
  like inline-ignore. Because outputs are identical, the engine may skip
  running ignored rules as an optimisation, but the pure function is the
  tested contract.
- **`Violation` is frozen** — a severity override yields a **new** `Violation`
  (and thus a new `RunItem`) carrying the overridden severity; the original is
  not mutated. No model change is required.
- **Config errors surface at the CLI** as exit 2 with a `config error: ...`
  line on stderr, before any linting output. They are NOT `InternalError`
  records — they are a distinct, human-readable failure channel.
- **Exit gate re-evaluated on surviving severity.** The CLI computes exit from
  the post-override severity of the surviving, non-exempt findings: any `high`
  → 1; only `low` or none → 0; any internal error → 2 (unchanged).
- **`ignore` and `suppressed` stay distinct.** Inline-ignore's `suppressed`
  map remains the per-line suppression count; config-ignore is a whole-rule
  disable and never contributes to it. The two mechanisms compose rather than
  merge.
- **Strict top-level keys.** Unknown top-level keys are a `ConfigError`,
  extending the brief's unknown-rule-id hard lesson so a typo'd key
  (`"severityoverrides"`) cannot silently no-op. This is slightly stricter than
  the minimal brief and is confirmed at C2.

## Testing Decisions

Only external behaviour is asserted: ignore filtering, severity remap in both
outputs and at the exit gate, config-error exit codes, and no-config identity.
The loader is tested purely with no fixtures. Engine/CLI behaviour runs over
throwaway root directories; the end-to-end slice runs a committed fixture root
through the real CLI as a subprocess. Existing exit-code tests that assumed a
`low` finding trips exit 1 are updated to the new high-only gate.

## Out of Scope

- CLI configuration flags, global (`~`) configuration, per-line ignore (already
  covered by the inline-ignore feature), and any new rule.
- Per-file or per-scope config files; the single root file is the surface.
- Changing a rule's built-in default severity; overrides only act at the gate.
- A distinct error code for config problems beyond the existing exit 2 family.