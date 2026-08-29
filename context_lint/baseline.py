"""Baseline-mode: freeze pre-existing violations, flag only new ones.

Pure/IO leaf: fingerprinting, the version-1 baseline file load/write, and the
compare filter. The engine and every rule stay untouched — baseline is a
reporting/adoption post-filter the CLI layers over its surviving findings.
"""

import hashlib
import json

VERSION = 1
_REQUIRED_KEYS = ("rule", "file", "message")


class BaselineError(Exception):
    """A baseline file that cannot be consumed as a version-1 snapshot."""


def fingerprint(rule: str, relpath: str, message: str) -> str:
    """Deterministic, line-free fingerprint: hex sha1 of rule + relpath + message.

    Exact concatenation per the brief. No line, no severity — line drift and
    severity changes cannot invalidate a match.
    """
    return hashlib.sha1((rule + relpath + message).encode("utf-8")).hexdigest()


def _record_fingerprint(record: dict) -> str:
    return fingerprint(record["rule"], record["file"], record["message"])


def write_baseline(path, records: list, generated_at: str) -> None:
    """Write a version-1 baseline snapshot. `generated_at` is injected by the caller
    (CLI supplies `datetime.now()`, tests a fixed value) so the writer is deterministic."""
    payload = {"version": VERSION, "generatedAt": generated_at, "violations": list(records)}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def load_baseline(path) -> frozenset:
    """Load a version-1 baseline file into a set of fingerprints (duplicates collapse).

    Missing file, malformed JSON, and wrong version all raise BaselineError.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, UnicodeDecodeError, ValueError) as exc:  # ValueError covers JSONDecodeError
        raise BaselineError(f"baseline read failed: {exc}") from exc
    if not isinstance(data, dict) or data.get("version") != VERSION:
        version = data.get("version") if isinstance(data, dict) else None
        raise BaselineError(f"unsupported baseline version: {version!r}")
    records = data.get("violations")
    if not isinstance(records, list):
        raise BaselineError("baseline violations is not a list")
    fps = set()
    for rec in records:
        if not isinstance(rec, dict) or not all(isinstance(rec.get(k), str) for k in _REQUIRED_KEYS):
            raise BaselineError(f"invalid baseline record: {rec!r}")
        fps.add(_record_fingerprint(rec))
    return frozenset(fps)


def is_matched(item, baseline_set: frozenset) -> bool:
    """True if a RunItem's fingerprint is present in the baseline set."""
    return fingerprint(item.violation.rule, item.file, item.violation.message) in baseline_set


def filter_baseline(items: list, baseline_set: frozenset):
    """Classify RunItems into (new_items, matched_items) against the baseline set."""
    new, matched = [], []
    for it in items:
        (matched if is_matched(it, baseline_set) else new).append(it)
    return new, matched


if __name__ == "__main__":
    a = fingerprint("context-md/entry-format", "CONTEXT.md", "entry 'x' missing required label '边界:'")
    assert a == fingerprint("context-md/entry-format", "CONTEXT.md", "entry 'x' missing required label '边界:'")
    assert a != fingerprint("context-md/entry-format", "CONTEXT.md", "different")
    print("baseline self-check ok")