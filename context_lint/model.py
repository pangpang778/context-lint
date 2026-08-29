"""Core data shapes shared by the engine and rules (stdlib only)."""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Violation:
    """A confirmed format/discipline deviation, matching the data standard shape."""

    rule: str
    severity: str
    line: int
    message: str

    def to_dict(self) -> dict:
        return {"rule": self.rule, "severity": self.severity, "line": self.line, "message": self.message}


@dataclass(frozen=True)
class RunItem:
    """A violation attributed to the file that produced it (for human output)."""

    file: str
    violation: Violation


@dataclass(frozen=True)
class InternalError:
    """A rule crash or read failure — an internal error (exit 2), never a violation."""

    file: str
    rule: str
    message: str


@dataclass(frozen=True)
class RunResult:
    items: list
    errors: list


@dataclass(frozen=True)
class Rule:
    """A registered lint rule: metadata plus a pure text->violations function."""

    id: str
    severity: str
    run: Callable[[str], list]