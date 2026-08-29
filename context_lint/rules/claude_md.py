"""Rule: claude-md/sections (high).

A root CLAUDE.md must carry the six required section headings
(项目约定 / 架构原则 / 规范索引 / 决策记录 / 共享背景 / Agent 指南).
Each missing section is one violation, anchored at the file's first heading
line (an absent heading has no natural line of its own).
"""

from ..model import Rule, Violation

ID = "claude-md/sections"
SEVERITY = "high"
REQUIRED = ("项目约定", "架构原则", "规范索引", "决策记录", "共享背景", "Agent 指南")


def _heading_token(line: str):
    """Return the heading text of a line, or None if the line is not a heading.

    `#`, `##`, `###` ... prefixes all count; surrounding whitespace is
    tolerated. The token must equal a section name exactly (no substring).
    """
    stripped = line.strip()
    if not stripped.startswith("#"):
        return None
    return stripped.lstrip("#").strip()


def run(text: str) -> list:
    lines = text.splitlines()
    anchor = 1
    for lineno, raw in enumerate(lines, 1):
        if raw.strip().startswith("#"):
            anchor = lineno
            break
    found = {token for token in (_heading_token(raw) for raw in lines) if token}
    out = []
    for name in REQUIRED:
        if name not in found:
            out.append(
                Violation(
                    rule=ID,
                    severity=SEVERITY,
                    line=anchor,
                    message=f"missing required section heading '{name}'",
                )
            )
    return out


RULE = Rule(id=ID, severity=SEVERITY, run=run)
