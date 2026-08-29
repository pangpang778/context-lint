"""Rule registry + runner. cli -> engine -> rules, strictly one-way."""

import os

from . import inline_ignore, scope
from .model import InternalError, Rule, RunItem, RunResult
from .rules import ALL

REGISTRY: dict = {r.id: r for r in ALL}

# Pruned while walking so the scanner never descends into noise we won't lint.
_PRUNE = {".git", "__pycache__"}


def run(root: str) -> RunResult:
    items = []
    errors = []
    suppressed = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _PRUNE]
        for name in filenames:
            if not name.endswith((".md", ".markdown")):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            ids = scope.applicable_rules(rel)
            if not ids:
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
            except (OSError, UnicodeDecodeError) as exc:
                # UnicodeDecodeError (GBK/other non-UTF8 inputs) is a ValueError, not OSError.
                errors.append(InternalError(file=rel, rule=",".join(ids), message=f"read failed: {exc}"))
                continue
            protected = inline_ignore.resolve(text)
            for rid in ids:
                rule: Rule = REGISTRY.get(rid)
                if rule is None:
                    errors.append(InternalError(file=rel, rule=rid, message="unknown rule"))
                    continue
                try:
                    for violation in rule.run(text):
                        if inline_ignore.suppresses(protected, violation.line, rid):
                            suppressed[rid] = suppressed.get(rid, 0) + 1
                        else:
                            items.append(RunItem(file=rel, violation=violation))
                except Exception as exc:  # rule crash != violation
                    errors.append(InternalError(file=rel, rule=rid, message=f"rule crashed: {exc}"))
    return RunResult(items=items, errors=errors, suppressed=suppressed)