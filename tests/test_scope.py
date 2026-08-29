from context_lint import scope


def test_root_context_md_maps_to_rule1():
    assert scope.applicable_rules("CONTEXT.md") == ["context-md/entry-format"]


def test_nested_context_md_is_not_root_scope():
    assert scope.applicable_rules("docs/CONTEXT.md") == []


def test_unrelated_md_is_null():
    assert scope.applicable_rules("README.md") == []
    assert scope.applicable_rules("src/foo.md") == []


def test_specs_segment_maps_to_rule2():
    assert scope.applicable_rules("specs/foo.md") == ["durability/spec-coordinates"]
    assert scope.applicable_rules(".omc/specs/a.md") == ["durability/spec-coordinates"]
    assert scope.applicable_rules("x/specs/deep/b.md") == ["durability/spec-coordinates"]


def test_root_claude_md_maps_to_rule3():
    assert scope.applicable_rules("CLAUDE.md") == ["claude-md/sections"]
    assert scope.applicable_rules("docs/CLAUDE.md") == []