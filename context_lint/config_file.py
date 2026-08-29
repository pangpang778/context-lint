"""Config-file loader for context-lint.

Pure leaf module: consumes configuration *text* plus the set of known rule
ids, and produces an immutable-by-convention :class:`Config`. It never reads
files (a missing file is the caller's concern and maps to an empty config) and
never mutates anything it inspects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .model import RunItem, Violation

VALID_SEVERITIES = frozenset({"high", "low"})


class ConfigError(Exception):
    """A config file that cannot be consumed as a valid configuration."""


@dataclass(frozen=True)
class Config:
    """Validated configuration extracted from a config file text."""

    ignore: frozenset[str] = frozenset()
    # not deeply frozen: callers treat this map as read-only (apply builds a
    # fresh copy rather than mutating it)
    severity_overrides: dict[str, str] = field(default_factory=dict)  # rule -> "high"|"low"


def load(text: str, known_ids: set[str]) -> Config:
    """Parse and validate config *text* against *known_ids*.

    Raises :class:`ConfigError` for malformed JSON, a non-object root,
    unknown top-level keys, badly typed fields, unknown rule ids, or
    severity values other than "high"/"low".
    """
    ids = set(known_ids)

    try:
        data = json.loads(text)
    except ValueError as exc:
        raise ConfigError(f"malformed JSON in config: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(
            f"config root must be a JSON object, got {type(data).__name__}"
        )

    ignore, ignore_problems = _parse_ignore(data, ids)
    overrides, override_problems = _parse_severity_overrides(data, ids)

    unknown_keys = sorted(set(data) - {"ignore", "severityOverrides"})
    if unknown_keys:
        ignore_problems.append(f"unknown top-level key(s): {unknown_keys}")

    problems = ignore_problems + override_problems
    if problems:
        raise ConfigError("; ".join(problems))

    return Config(ignore=frozenset(ignore), severity_overrides=overrides)


def _parse_ignore(data: dict, ids: set) -> tuple[list, list]:
    if "ignore" not in data:
        return [], []
    raw = data["ignore"]
    if not isinstance(raw, list):
        raise ConfigError(f"'ignore' must be a JSON array, got {type(raw).__name__}")
    problems: list[str] = []
    unknown: list[str] = []
    for entry in raw:
        if not isinstance(entry, str):
            raise ConfigError(f"'ignore' entry must be a string, got {entry!r}")
        if entry not in ids:
            unknown.append(entry)
    if unknown:
        problems.append(f"unknown rule id(s) in ignore: {sorted(unknown)}")
    return raw, problems


def _parse_severity_overrides(data: dict, ids: set) -> tuple[dict, list]:
    if "severityOverrides" not in data:
        return {}, []
    raw = data["severityOverrides"]
    if not isinstance(raw, dict):
        raise ConfigError(
            f"'severityOverrides' must be a JSON object, got {type(raw).__name__}"
        )
    overrides: dict[str, str] = {}
    problems: list[str] = []
    unknown: list[str] = []
    for rule, severity in raw.items():
        if rule not in ids:
            unknown.append(rule)
            continue
        if not isinstance(severity, str) or severity not in VALID_SEVERITIES:
            raise ConfigError(
                f"invalid severity for rule {rule!r}: {severity!r} "
                f"(expected 'high' or 'low')"
            )
        overrides[rule] = severity
    if unknown:
        problems.append(f"unknown rule id(s) in severityOverrides: {sorted(unknown)}")
    return overrides, problems


def apply(items: list, config: Config) -> list:
    """Pure apply: `violations × config → surviving, re-judged set`.

    Drops findings whose rule is in ``config.ignore`` and remaps the severity of
    every surviving finding under ``config.severity_overrides``. Because
    ``Violation`` is frozen, a remap yields a **new** ``Violation``/``RunItem``;
    the original is untouched. When nothing changes the returned list shares the
    input objects (identity preserved); otherwise unchanged items are carried
    through by reference and changed ones are replaced.
    """
    out = []
    changed = False
    for it in items:
        rule = it.violation.rule
        if rule in config.ignore:
            changed = True
            continue
        remap = config.severity_overrides.get(rule)
        if remap is not None and remap != it.violation.severity:
            changed = True
            out.append(
                RunItem(
                    file=it.file,
                    violation=Violation(rule=rule, severity=remap, line=it.violation.line, message=it.violation.message),
                )
            )
        else:
            out.append(it)
    return out if changed else items


if __name__ == "__main__":
    known = {"rule-a", "rule-b"}
    empty = load("{}", known)
    assert empty.ignore == frozenset()
    assert empty.severity_overrides == {}
    populated = load(
        '{"ignore": ["rule-a"], "severityOverrides": {"rule-b": "high"}}', known
    )
    assert populated.ignore == frozenset({"rule-a"})
    assert populated.severity_overrides == {"rule-b": "high"}
    try:
        load('{"ignore": ["nope"]}', known)
    except ConfigError as exc:
        assert "nope" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ConfigError for unknown rule id")
    print("config_file self-check OK")
