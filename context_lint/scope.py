"""Scope router: maps a repository-relative path to the rule ids that apply to it."""


def applicable_rules(rel_path: str) -> list:
    """Return rule ids for a repo-relative path (posix separators). Empty = not scanned."""
    rules = []
    if rel_path == "CONTEXT.md":
        rules.append("context-md/entry-format")
    if "specs" in rel_path.split("/"):
        rules.append("durability/spec-coordinates")
    if rel_path == "CLAUDE.md":
        rules.append("claude-md/sections")
    return rules