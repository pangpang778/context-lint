"""Inline-ignore matcher (pure, stdlib).

Given markdown text, resolve which rule ids are suppressed on each protected
line. A marker is an HTML comment of the form:

    <!-- context-lint:ignore -->                 bare  -> suppress *all* rules
    <!-- context-lint:ignore id1,id2,... -->     scoped-> suppress listed ids

Placement:
  - trailing : a marker after content on a line protects the violations anchored
               on that line;
  - standalone: a line whose only non-whitespace content is (one or more)
               markers protects its own line AND the immediately following line.

A protected line's suppression set is the union of every marker that protects
it; if any bare marker protects a line, that line is "_ALL" (every rule).
"""

import re

DIRECTIVE = "context-lint:ignore"
_ALL = "*"  # sentinel member meaning "all rules"

_MARKER = re.compile(r"<!--\s*context-lint:ignore(?:\s+([^>]*?))?\s*-->")


def _ids(body: str) -> set:
    """Split a scoped marker's comma-separated rule list into trimmed ids."""
    return {tok.strip() for tok in body.split(",") if tok.strip()}


def _protect(markers: list) -> set:
    """Collapse a line's markers into one suppression set ('*' = all rules)."""
    union = set()
    for body in markers:
        # bare/empty marker, or one with no usable ids (e.g. "ignore , ,") -> all rules
        if body is None or not body.strip():
            return {_ALL}
        ids = _ids(body)
        if not ids:
            return {_ALL}
        union |= ids
    return union


def resolve(text: str) -> dict:
    """Return {1-based protected line: set of suppressed rule ids (`_ALL` = all)}."""
    lines = text.splitlines()
    protected = {}
    for i, raw in enumerate(lines, 1):
        markers = [m.group(1) for m in _MARKER.finditer(raw)]
        if not markers:
            continue
        ids = _protect(markers)
        inst = protected.setdefault(i, set())
        inst |= ids
        # standalone line (BOM tolerated) -> also protect the next line
        if not _MARKER.sub("", raw).replace("﻿", "").strip() and i < len(lines):
            next_inst = protected.setdefault(i + 1, set())
            next_inst |= ids
    return protected


def suppresses(protected: dict, line: int, rule: str) -> bool:
    """True if the given rule is suppressed on `line` (or the line is _ALL)."""
    s = protected.get(line)
    if not s:
        return False
    return _ALL in s or rule in s


if __name__ == "__main__":
    # ponytail: self-check via asserts so the slice is runnable in isolation
    a = resolve("## t <!-- context-lint:ignore -->\n")
    assert a == {1: {_ALL}}, a
    b = resolve("<!-- context-lint:ignore a -->\nnext\n")
    assert b[2] == {"a"}, b
    assert suppresses(b, 2, "a") and not suppresses(b, 2, "z"), b
    print("inline-ignore matcher self-check OK")