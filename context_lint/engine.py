"""Rule registry + runner. cli -> engine -> rules, strictly one-way."""

import os

from . import inline_ignore, scope
from .config_file import Config, ConfigError, apply as apply_config
from .model import InternalError, Rule, RunItem, RunResult
from .rules import ALL

REGISTRY: dict = {r.id: r for r in ALL}

# Pruned while walking so the scanner never descends into noise we won't lint.
_PRUNE = {".git", "__pycache__"}

_CONFIG_NAME = ".context-lint.json"


def _load_root_config(root: str) -> Config:
    """Read and validate <root>/<config-name>; a missing file is an empty config.

    Only ever called when the caller did not supply an explicit config. A
    present-but-unreadable or malformed file raises ConfigError.
    """
    path = os.path.join(root, _CONFIG_NAME)
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except FileNotFoundError:
        return Config()
    except OSError as exc:
        raise ConfigError(f"could not read {path}: {exc}") from exc
    from .config_file import load as load_config_text

    return load_config_text(text, set(REGISTRY))


def run(root: str, config: Config | None = None) -> RunResult:
    items = []
    errors = []
    suppressed = {}
    if config is None:
        config = _load_root_config(root)
    ignored = config.ignore
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _PRUNE]
        for name in filenames:
            if not name.endswith((".md", ".markdown")):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            ids = scope.applicable_rules(rel)
            ids = [i for i in ids if i not in ignored]  # disabled rules never run nor suppress
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
    # ignored rules were skipped in the walk, so apply only remaps severities
    # (and returns the same list object when nothing changed).
    return RunResult(items=apply_config(items, config), errors=errors, suppressed=suppressed)