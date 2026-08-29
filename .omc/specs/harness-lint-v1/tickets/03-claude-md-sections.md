# T3 — claude-md/sections

- **id:** T3
- **blockedBy:** [T1]

## Output
Rule 3 wired through the same pipeline as T1, enforcing the six required CLAUDE.md section headings.

## Crosses every layer
- **Rules** — rule 3 pure function: markdown -> violations, one per missing required section. The six required headings: 项目约定, 架构原则, 规范索引, 决策记录, 共享背景, Agent 指南. A required section is present when a heading for it appears.
- **Engine/registry** — rule registered with severity high; reuse T1's runner unchanged.
- **Dispatcher (router)** — root file named CLAUDE.md -> rule 3 (root only, per C2 #3; a nested CLAUDE.md is out of scope).
- **CLI** — mounts automatically via registry; no CLI change.
- **Anchor decision** — a missing section is reported at the file's first heading line (the `#` title if present, else line 1), since an absent heading has no natural line.

## Demonstrable smoke
- A CLAUDE.md missing two of the six headings -> two high violations (one per missing section), each anchored at the first heading line; a complete CLAUDE.md -> no violations.

## Accepts
- T3 is complete when the six-heading presence logic and the missing-section anchor are asserted via seam S3, and at least one end-to-end smoke via S5/S6.

## Note
- Root-scope only (C2 #3). Nested CLAUDE.md files are not scanned.