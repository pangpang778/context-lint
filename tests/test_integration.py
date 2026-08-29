"""T4 — cross-slice integration + exit-code precedence + crash-resilience.

The persistent regression gate for the whole feature: all three rules must
accumulate in one run, exit codes must follow errors-trump-violations, and a
rule crash must never abort the batch.
"""

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
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")


def _cli(root, *extra):
    # PYTHONUTF8=1 pins the child's IO encoding so the parent's strict UTF-8
    # pipe decode isn't locale-dependent (GBK on this box).
    env = {**os.environ, "PYTHONUTF8": "1"}
    return subprocess.run(
        [sys.executable, "-m", "context_lint", "--root", str(root), *extra],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def test_accumulation_across_all_rules(tmp_path):
    _mk(tmp_path, {
        "CONTEXT.md": "## term\n- 定义: a\n- 边界: b\n",
        "specs/a.md": "Ref src/store.js here.\n",
        "CLAUDE.md": "no section headings here\n",
    })
    res = engine.run(str(tmp_path))
    ids = {it.violation.rule for it in res.items}
    assert ids == {
        "context-md/entry-format",
        "durability/spec-coordinates",
        "claude-md/sections",
    }
    assert res.errors == []


def test_mixed_all_violations_exit_one(tmp_path):
    _mk(tmp_path, {
        "CONTEXT.md": "## term\n- 定义: a\n- 边界: b\n",
        "specs/a.md": "Ref src/store.js\n",
        "CLAUDE.md": "no headings\n",
    })
    r = _cli(tmp_path)
    assert r.returncode == 1
    payload = json.loads(_cli(tmp_path, "--json").stdout)
    assert isinstance(payload, list) and len(payload) > 0
    assert all(set(v) == {"rule", "severity", "line", "message"} for v in payload)


def test_errors_trump_violations_exit_two(tmp_path):
    # specs/a.md is unreadable (decode error) -> internal error; specs/b.md flags -> violation.
    _mk(tmp_path, {
        "specs/a.md": b"\x80\x80\x81",
        "specs/b.md": "Ref src/store.js\n",
    })
    r = _cli(tmp_path)
    assert r.returncode == 2
    assert "internal error" in r.stderr
    # the violation must still be reported even though the error trumps to exit 2
    assert "spec-coordinates" in r.stdout


def test_json_mode_still_surfaces_internal_error(tmp_path):
    _mk(tmp_path, {"specs/a.md": b"\x80\x80\x81"})
    r = _cli(tmp_path, "--json")
    assert r.returncode == 2
    assert "internal error" in r.stderr
    assert r.stdout.strip() == "[]"  # no violations under --json, error on stderr only


def test_crashing_rule_does_not_abort_batch(tmp_path, monkeypatch):
    from context_lint.model import Rule

    def _boom(text):
        raise RuntimeError("bang")

    monkeypatch.setitem(
        engine.REGISTRY, "claude-md/sections", Rule(id="claude-md/sections", severity="high", run=_boom)
    )
    _mk(tmp_path, {
        "specs/a.md": "src/store.js\n",
        "CLAUDE.md": "blah\n",
    })
    res = engine.run(str(tmp_path))
    ids = {it.violation.rule for it in res.items}
    assert ids == {"durability/spec-coordinates"}  # surviving rule still ran
    assert len(res.errors) == 1
    assert res.errors[0].rule == "claude-md/sections"


def test_clean_root_exit_zero(tmp_path):
    _mk(tmp_path, {
        "CONTEXT.md": "## term\n- 定义: a\n- 边界: b\n- 已解决的歧义: c\n",
        "CLAUDE.md": "# Title\n## 项目约定\n## 架构原则\n## 规范索引\n## 决策记录\n## 共享背景\n## Agent 指南\n",
    })
    r = _cli(tmp_path)
    assert r.returncode == 0
    assert r.stdout == ""