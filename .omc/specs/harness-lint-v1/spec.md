# harness-lint v1 Spec

## Problem

The shipyard harness encodes markdown discipline as human checkpoints — the durability gate (no path/line coordinates in specs), CONTEXT.md entry format, and the six required CLAUDE.md sections. These are enforced today by review, i.e. by hand. context-lint v1 mechanizes them as a read-only Python CLI, dogfooding the harness stack portability onto Python (zero third-party runtimes).

## Solution

A read-only lint CLI. Three single-purpose rule functions, each registered in a rule registry, dispatched to files by a scope router. Run produces zero-or-more violations; never modifies scanned files.

- **Rule 1 — `context-md/entry-format`** (low) on the root CONTEXT.md: every `## <term>` entry must carry the three labeled fields `定义:`, `边界:`, `已解决的歧义:`. A missing label is a violation naming the term and the absent label.
- **Rule 2 — `durability/spec-coordinates`** (high) on markdown under the specs directory: a path-coordinate token (contains `/` and either contains `.` or ends with `/`) is a violation. Exempt: a line carrying the inline marker `<!-- origin-fragment -->`; a token adjacent to a CJK character on either side, or containing a CJK character (the F-0008 lesson — CJK prose adjacency is not a coordinate).
- **Rule 3 — `claude-md/sections`** (high) on the root CLAUDE.md: each of the six required sections (项目约定, 架构原则, 规范索引, 决策记录, 共享背景, Agent 指南) must have a heading. A missing heading is a violation.

Scope router decides which rule applies to a file by relative identity: root container file named CONTEXT.md → Rule 1; any markdown under a `specs` directory segment → Rule 2; root file named CLAUDE.md → Rule 3.

## User Stories

1. **As a user**, running the CLI over a repo root reports every confirmed violation in the shared shape `{rule, severity, line, message}`. If a scan finds none, it exits 0 and prints nothing (or an empty JSON list under `--json`).
2. **As a user**, I get exit code 1 when one or more violations are found, and 2 when the run hits an internal error — so the codes are scriptable and distinct.
3. **As a user**, passing `--root <dir>` scans that directory instead of the current working directory, so I can lint any checkout.
4. **As a user**, passing `--json` emits the violation list as JSON (one object per violation), each with rule, severity, line, message — so I can pipe into tools.
5. **As a user**, a rule that crashes on a file does not take down the batch: that file records an internal-error entry and the scan continues, and the run still surfaces exit 2.
6. **As a spec author**, a path coordinate accidentally dropped into a spec doc is caught as a high violation (Rule 2), unless the line is marked `<!-- origin-fragment -->` or the token borders CJK text.
7. **As a CONTEXT.md editor**, an entry missing any of the three fields (定义 / 边界 / 已解决的歧义) is flagged low.
8. **As a CLAUDE.md editor**, a missing required section heading is flagged high.

## Implementation Decisions

- **Rule failure ≠ violation.** A crash inside a rule is an internal error (exit 2), never reported as a violation. Mirrors CONTEXT.md's rule boundary.
- **File read failure = internal error, continue.** Lint-all takes precedence over any single file's readability; the failed file is recorded and scanning proceeds.
- **Detection of "markdown under specs"** is by directory segment named `specs`, independent of repo layout nesting.
- **Rule 3 missing-section anchor line.** A missing section is reported at the file's first heading line (the `#` title if present, else line 1) — a stable anchor since there is no natural line for an absent heading.
- **Rule 2 white-space tokenization** with trailing punctuation (`)`, `]`, `}`, `)`, `,`, `.`) stripped from the token end; leading `(`/`[` stripped — so `(spec.md)` still resolves to the bare token `spec.md`. Non-coordinate single filenames (no slash) are not flagged.
- **The refined predicate is the authoritative correction of the data standard (C2 ruling #1).** The data standard document's earlier wording ("contains `/` and contains `.`") over-matched rule-identifier tokens; the refined predicate (final slash-segment contains a dot, or token ends with `/`) replaces it in both that document and this spec. Correcting that standard document is in-scope for this run and lands in the Rule 2 ticket.
- **Rule 1 field matching** by line prefix `定义:` / `边界:` / `已解决的歧义:` (the label colon, Chinese). An entry missing any of the three yields one violation per missing field.

## Testing Decisions

External behavior only — no private internals.

- **Rule seam tests** feed raw markdown strings to each rule's pure function and assert the resulting violation list (rule id, severity, line, message), including the CJK adjacency exemption and the origin-fragment exemption for Rule 2.
- **Router seam tests** assert, for a set of relative identities, which rule(s) apply.
- **Integration tests** drive the CLI end-to-end over a fixture repo: exit codes 0/1/2 (`--root`), JSON shape under `--json`, human-readable output otherwise, and a rule crash that does not abort the batch (exit 2 with the rest intact).
- Test runner is **pytest** (dev dependency only); runtime stays standard-library-only.

## Out of Scope

- Auto-fix (`--fix`) — read-only only.
- File-graph rules (existence / pointers) — the sy check domain, per process standard.
- Configuration files — no config surface; defaults and `--root`/`--json` only.
- Any rule beyond the three seeds above.