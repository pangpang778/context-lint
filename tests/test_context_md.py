from context_lint.rules import context_md as r


def test_clean_entry_yields_no_violations():
    text = (
        "# Glossary\n\n"
        "## rule（规则）\n"
        "- 定义: 一条检查\n"
        "- 边界: 只读\n"
        "- 已解决的歧义: 无\n"
    )
    assert r.run(text) == []


def test_missing_one_label():
    text = "## rule（规则）\n- 定义: a\n- 边界: b\n"
    vs = r.run(text)
    assert len(vs) == 1
    assert vs[0].rule == r.ID
    assert vs[0].severity == r.SEVERITY
    assert vs[0].line == 1
    assert vs[0].message == "entry 'rule（规则）' missing required label '已解决的歧义:'"


def test_missing_all_three():
    text = "## empty\njust prose\n"
    vs = r.run(text)
    assert len(vs) == 3
    assert {v.message.split("'")[3] for v in vs} == {"定义:", "边界:", "已解决的歧义:"}


def test_h1_heading_terminates_entry_without_starting_one():
    text = (
        "# Title\n"
        "## a\n- 定义: 1\n- 边界: 2\n- 已解决的歧义: 3\n"
        "# Middle\n"
        "## b\n- 定义: 4\n"
    )
    vs = r.run(text)
    assert len(vs) == 2  # entry b missing 边界: and 已解决的歧义:


def test_no_entries_no_violations():
    assert r.run("# Glossary\n") == []
    assert r.run("") == []


def test_fenced_hash_comment_is_not_a_heading():
    text = (
        "## term\n"
        "```sh\n"
        "# comment inside fence\n"
        "```\n"
        "- 定义: a\n"
        "- 边界: b\n"
        "- 已解决的歧义: c\n"
    )
    assert r.run(text) == []