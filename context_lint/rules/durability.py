"""Rule: durability/spec-coordinates (high).

A path coordinate in a spec pins prose to a file address that drifts on
rename/move, breaking the launch durability gate. A token counts when it
ends with `/`, or it contains a `/` and its final `/`-separated segment
carries a dot (C2 ruling #1: a bare `contains / and .` predicate mis-flags
rule identifiers like `context-md/entry-format`; requiring the dot to sit
in a final segment also keeps bare dotted words like `spec.md` or `v1.2`
out). Two exemptions: lines carrying the `<!-- origin-fragment -->` marker,
and tokens touching or containing CJK text (the F-0008 prose lesson).
"""

import re

from ..model import Rule, Violation

ID = "durability/spec-coordinates"
SEVERITY = "high"

MARKER = "<!-- origin-fragment -->"
_LEAD = "(["  # stripped from a token before matching
_TAIL = ")]},."  # stripped from a token before matching


def _is_cjk(ch: str) -> bool:
    return "一" <= ch <= "鿿" or "㐀" <= ch <= "䶿"


def _is_coordinate(token: str) -> bool:
    if token.endswith("/"):
        return True
    head, sep, final = token.rpartition("/")
    return sep == "/" and "." in final


def run(text: str) -> list:
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if MARKER in line:
            continue
        for m in re.finditer(r"\S+", line):
            raw = m.group(0)
            body = raw.lstrip(_LEAD).rstrip(_TAIL)
            if not body or not _is_coordinate(body):
                continue
            start = m.start() + (len(raw) - len(raw.lstrip(_LEAD)))
            end = start + len(body)
            before = line[start - 1] if start > 0 else ""
            after = line[end] if end < len(line) else ""
            if _is_cjk(before) or _is_cjk(after) or any(_is_cjk(c) for c in body):
                continue
            out.append(
                Violation(
                    rule=ID,
                    severity=SEVERITY,
                    line=lineno,
                    message=f"file-path coordinate in spec: {body}",
                )
            )
    return out


RULE = Rule(id=ID, severity=SEVERITY, run=run)
