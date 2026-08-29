from context_lint import engine


def _mk(root, files):
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def test_bad_context_md_engine(tmp_path):
    _mk(tmp_path, {"CONTEXT.md": "## rule（规则）\n- 定义: a\n- 边界: b\n"})
    res = engine.run(str(tmp_path))
    assert len(res.items) == 1
    item = res.items[0]
    assert item.file == "CONTEXT.md"
    assert item.violation.rule == "context-md/entry-format"
    assert item.violation.severity == "low"
    assert len(res.errors) == 0


def test_clean_root_engine(tmp_path):
    _mk(
        tmp_path,
        {"CONTEXT.md": "## rule（规则）\n- 定义: a\n- 边界: b\n- 已解决的歧义: c\n"},
    )
    res = engine.run(str(tmp_path))
    assert res.items == []
    assert res.errors == []


def test_non_markdown_ignored(tmp_path):
    _mk(tmp_path, {"foo.py": "## x\n", "notes.txt": "## y\n"})
    res = engine.run(str(tmp_path))
    assert res.items == []


def test_absent_target_is_not_an_error(tmp_path):
    res = engine.run(str(tmp_path))
    assert res.items == []
    assert res.errors == []


def test_decode_failure_is_internal_error(tmp_path):
    # Invalid UTF-8 bytes make open(encoding="utf-8").read() raise UnicodeDecodeError.
    (tmp_path / "CONTEXT.md").write_bytes(b"\x80\x80\x81")
    res = engine.run(str(tmp_path))
    assert res.items == []
    assert len(res.errors) == 1
    assert "read failed" in res.errors[0].message


def test_rule_crash_is_internal_error_not_violation(tmp_path, monkeypatch):
    from context_lint.model import Rule

    def _boom(text):
        raise RuntimeError("boom")

    monkeypatch.setitem(
        engine.REGISTRY,
        "context-md/entry-format",
        Rule(id="context-md/entry-format", severity="low", run=_boom),
    )
    (tmp_path / "CONTEXT.md").write_text("## t\n- 定义: a\n- 边界: b\n- 已解决的歧义: c\n", encoding="utf-8")
    res = engine.run(str(tmp_path))
    assert res.items == []  # crash is NOT a violation
    assert len(res.errors) == 1
    assert res.errors[0].rule == "context-md/entry-format"
    assert "crashed" in res.errors[0].message