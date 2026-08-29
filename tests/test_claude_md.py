import json
import subprocess
import sys
from pathlib import Path

from context_lint import engine
from context_lint.rules import claude_md as r

ROOT = Path(__file__).resolve().parents[1]

COMPLETE = (
    "# Shipyard\n"
    "\n"
    "## 项目约定\n"
    "## 架构原则\n"
    "## 规范索引\n"
    "## 决策记录\n"
    "## 共享背景\n"
    "## Agent 指南\n"
)


def test_missing_two_sections_yields_two_violations_at_first_heading():
    text = (
        "# Shipyard\n"
        "\n"
        "## 项目约定\n"
        "## 架构原则\n"
        "## 规范索引\n"
        "## 决策记录\n"
    )  # 共享背景 and Agent 指南 missing
    vs = r.run(text)
    assert len(vs) == 2
    assert {v.message for v in vs} == {
        "missing required section heading '共享背景'",
        "missing required section heading 'Agent 指南'",
    }
    for v in vs:
        assert v.rule == r.ID
        assert v.severity == r.SEVERITY
        assert v.line == 1  # first heading line


def test_complete_file_yields_no_violations():
    assert r.run(COMPLETE) == []


def test_no_headings_six_violations_anchored_at_line_1():
    text = "just prose\nno headings here\n"
    vs = r.run(text)
    assert len(vs) == 6
    assert {v.message.split("'")[1] for v in vs} == set(r.REQUIRED)
    assert all(v.line == 1 for v in vs)


def test_empty_text_six_violations():
    vs = r.run("")
    assert len(vs) == 6
    assert all(v.line == 1 for v in vs)


def test_h1_prefix_counts_as_present():
    text = COMPLETE.replace("## 项目约定", "# 项目约定", 1)
    assert r.run(text) == []


def test_heading_match_is_exact_no_substring():
    text = (
        "# Shipyard\n"
        "## 项目约定\n"
        "## 架构原则\n"
        "## 规范索引（扩展）\n"  # supersets do not count
        "## 决策记录\n"
        "## 共享背景\n"
        "## Agent 指南备查\n"
    )
    vs = r.run(text)
    assert len(vs) == 2
    assert {v.message.split("'")[1] for v in vs} == {"规范索引", "Agent 指南"}


def test_first_heading_line_is_anchor_when_title_is_not_line_one():
    text = "intro prose\n\n# Shipyard\n\n## 项目约定\n"
    vs = r.run(text)
    assert len(vs) == 5
    assert all(v.line == 3 for v in vs)


def test_engine_routes_root_claude_md(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Shipyard\n\n## 项目约定\n", encoding="utf-8")
    result = engine.run(str(tmp_path))
    assert result.errors == []
    assert {item.file for item in result.items} == {"CLAUDE.md"}
    assert {item.violation.rule for item in result.items} == {r.ID}
    assert len(result.items) == 5


def test_cli_json_smoke(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Shipyard\n\n## 项目约定\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "context_lint", "--root", str(tmp_path), "--json"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert isinstance(payload, list) and len(payload) == 5
    assert set(payload[0]) == {"rule", "severity", "line", "message"}
    assert {p["rule"] for p in payload} == {r.ID}
    assert {p["severity"] for p in payload} == {"high"}
