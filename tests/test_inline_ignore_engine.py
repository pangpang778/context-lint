"""S2 — engine suppression filtering + per-rule suppressed counts + CLI --json."""

import json
import os
import subprocess
import sys
from pathlib import Path

from context_lint import engine

ROOT = Path(__file__).resolve().parents[1]


def _mk(root, files):
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _cli(root, *extra):
    env = {**os.environ, "PYTHONUTF8": "1"}
    return subprocess.run(
        [sys.executable, "-m", "context_lint", "--root", str(root), *extra],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def test_trailing_bare_suppresses_engine_item(tmp_path):
    _mk(tmp_path, {"CONTEXT.md": "## term <!-- context-lint:ignore -->\n- 定义: a\n- 边界: b\n"})
    res = engine.run(str(tmp_path))
    assert res.items == []
    assert res.suppressed == {"context-md/entry-format": 1}


def test_standalone_suppresses_next_line(tmp_path):
    _mk(tmp_path, {"CONTEXT.md": "<!-- context-lint:ignore -->\n## term\n- 定义: a\n- 边界: b\n"})
    res = engine.run(str(tmp_path))
    assert res.items == []
    assert res.suppressed == {"context-md/entry-format": 1}


def test_scoped_marker_leaves_other_rule_live(tmp_path):
    # marker names a rule that does not govern this file -> durability finding survives
    _mk(tmp_path, {"specs/a.md": "src/data.ts <!-- context-lint:ignore context-md/entry-format -->\n"})
    res = engine.run(str(tmp_path))
    assert len(res.items) == 1
    assert res.items[0].violation.rule == "durability/spec-coordinates"
    assert res.suppressed == {}


def test_scoped_marker_suppresses_named_rule(tmp_path):
    _mk(tmp_path, {"specs/a.md": "<!-- context-lint:ignore durability/spec-coordinates -->\nsrc/api.ts\n"})
    res = engine.run(str(tmp_path))
    assert res.items == []
    assert res.suppressed == {"durability/spec-coordinates": 1}


def test_suppression_is_per_file(tmp_path):
    _mk(tmp_path, {
        "CONTEXT.md": "<!-- context-lint:ignore -->\n## term\n- 定义: a\n- 边界: b\n",
        "specs/b.md": "lib/util.js\n",
    })
    res = engine.run(str(tmp_path))
    assert len(res.items) == 1
    assert res.items[0].violation.rule == "durability/spec-coordinates"
    assert res.suppressed == {"context-md/entry-format": 1}


def test_crash_is_still_internal_error_not_suppressed(tmp_path, monkeypatch):
    from context_lint.model import Rule

    def _boom(text):
        raise RuntimeError("boom")

    monkeypatch.setitem(engine.REGISTRY, "context-md/entry-format",
                        Rule(id="context-md/entry-format", severity="low", run=_boom))
    _mk(tmp_path, {"CONTEXT.md": "<!-- context-lint:ignore -->\n## term\n- 定义: a\n- 边界: b\n"})
    res = engine.run(str(tmp_path))
    assert res.items == []
    assert res.suppressed == {}
    assert len(res.errors) == 1  # a crash is never a suppressed finding


def test_cli_json_shape_object(tmp_path):
    _mk(tmp_path, {"CONTEXT.md": "## term <!-- context-lint:ignore -->\n- 定义: a\n- 边界: b\n"})
    r = _cli(tmp_path, "--json")
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert set(payload) == {"findings", "suppressed"}
    assert payload["findings"] == []
    assert payload["suppressed"] == {"context-md/entry-format": 1}


def test_cli_exit_zero_when_all_suppressed(tmp_path):
    _mk(tmp_path, {"CONTEXT.md": "<!-- context-lint:ignore -->\n## term\n- 定义: a\n- 边界: b\n"})
    r = _cli(tmp_path)
    assert r.returncode == 0
    assert r.stdout == ""


def test_cli_exit_one_with_unsuppressed_remaining(tmp_path):
    _mk(tmp_path, {"specs/a.md": "src/data.ts <!-- context-lint:ignore context-md/entry-format -->\n"})
    r = _cli(tmp_path)
    assert r.returncode == 1
    assert "spec-coordinates" in r.stdout


def test_cli_json_reports_mixed_suppressed_and_live(tmp_path):
    _mk(tmp_path, {
        "CONTEXT.md": "## term <!-- context-lint:ignore -->\n- 定义: a\n- 边界: b\n",
        "specs/b.md": "lib/util.js\n",
    })
    r = _cli(tmp_path, "--json")
    assert r.returncode == 1
    payload = json.loads(r.stdout)
    rules = {f["rule"] for f in payload["findings"]}
    assert rules == {"durability/spec-coordinates"}
    assert payload["suppressed"] == {"context-md/entry-format": 1}