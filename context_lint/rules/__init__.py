"""Rule aggregate. Layer is imported by engine; individual rules are pure leaves."""

from . import claude_md, context_md, durability

ALL = (context_md.RULE, durability.RULE, claude_md.RULE)