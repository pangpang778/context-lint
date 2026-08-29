"""Rule: context-md/entry-format (low).

Every `## <term>` entry must carry the three labeled fields (定义 / 边界 / 已解决的歧义).
A missing label is one violation.
"""

from ..model import Rule, Violation

ID = "context-md/entry-format"
SEVERITY = "low"
REQUIRED = ("定义:", "边界:", "已解决的歧义:")


def _label(line: str) -> set:
    stripped = line.strip().lstrip("-*").strip()
    return {lb for lb in REQUIRED if stripped.startswith(lb)}


def _parse(text: str):
    """Yield (term, heading_line) per `## <term>` entry; a `#` heading closes without starting.

    Fenced code blocks are skipped entirely (their `#` comments must not read as headings
    or as field labels).
    """
    entries = []
    cur_term = None
    cur_line = None
    cur_labels = set()
    in_fence = False
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("## "):
            if cur_term is not None:
                entries.append((cur_term, cur_line, cur_labels))
            cur_term = line[3:].strip()
            cur_line = lineno
            cur_labels = set()
        elif line.startswith("#"):
            if cur_term is not None:
                entries.append((cur_term, cur_line, cur_labels))
            cur_term = None
            cur_line = None
            cur_labels = set()
        elif cur_line is not None:
            cur_labels |= _label(line)
    if cur_term is not None:
        entries.append((cur_term, cur_line, cur_labels))
    return entries


def run(text: str) -> list:
    out = []
    for term, lineno, labels in _parse(text):
        for required in REQUIRED:
            if required not in labels:
                out.append(
                    Violation(
                        rule=ID,
                        severity=SEVERITY,
                        line=lineno,
                        message=f"entry '{term}' missing required label '{required}'",
                    )
                )
    return out


RULE = Rule(id=ID, severity=SEVERITY, run=run)