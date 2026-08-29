"""T2 — baseline CLI: generate/compare modes, [baseline] marker, exit codes, --json (seam S3)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

import context_lint.cli as cli

ROOT = Path(__file__).resolve().parents[1]


def _run(root, *extra):
    return subprocess.run(
        [sys.executable, "-m", "context_lint", "--root", str(root), *extra],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _bad_context(tmp_path):
    # One entry missing 已解决的歧义: -> a single context-md/entry-format violation on line 1.
    p = tmp_path / "CONTEXT.md"
    p.write_text("## adoption（采用）\n- 定义: a\n- 边界: b\n", encoding="utf-8")
    return p


def _bad_spec(tmp_path, name="a.md"):
    # One durability/spec-coordinates violation (severity high) on line 1.
    p = tmp_path / "specs" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("Ref src/store.js here.\n", encoding="utf-8")
    return p


def test_generate_exits_zero_with_violations(tmp_path):
    _bad_context(tmp_path)
    base = tmp_path / "base.json"
    r = _run(tmp_path, "--baseline-generate", str(base))
    assert r.returncode == 0
    assert base.exists()
    assert json.loads(base.read_text(encoding="utf-8"))["version"] == 1


def test_generate_writes_records(tmp_path):
    _bad_context(tmp_path)
    base = tmp_path / "base.json"
    assert _run(tmp_path, "--baseline-generate", str(base)).returncode == 0
    data = json.loads(base.read_text(encoding="utf-8"))
    assert len(data["violations"]) == 1
    rec = data["violations"][0]
    assert rec["rule"] == "context-md/entry-format"
    assert rec["file"] == "CONTEXT.md"


def test_generate_internal_error_exits_two(tmp_path):
    (tmp_path / "CONTEXT.md").write_bytes(b"\x80\x80\x81")
    r = _run(tmp_path, "--baseline-generate", str(tmp_path / "base.json"))
    assert r.returncode == 2
    assert "internal error" in r.stderr


def test_generate_unwritable_path_exits_two(tmp_path):
    _bad_context(tmp_path)
    # parent directory does not exist -> the write raises OSError -> exit 2, not 1
    r = _run(tmp_path, "--baseline-generate", str(tmp_path / "nodir" / "base.json"))
    assert r.returncode == 2
    assert "baseline" in r.stderr.lower() or "error" in r.stderr.lower()


def test_compare_clean_exits_zero_and_marks(tmp_path):
    _bad_context(tmp_path)
    base = tmp_path / "base.json"
    assert _run(tmp_path, "--baseline-generate", str(base)).returncode == 0
    r = _run(tmp_path, "--baseline", str(base))
    assert r.returncode == 0
    assert "[baseline]" in r.stdout
    assert "CONTEXT.md:1" in r.stdout


def test_compare_new_violation_exits_one(tmp_path):
    # a NEW high finding fails the severity gate even in baseline mode
    _bad_spec(tmp_path, "a.md")
    base = tmp_path / "base.json"
    assert _run(tmp_path, "--baseline-generate", str(base)).returncode == 0
    # add a second file -> one matched, one new (high)
    _bad_spec(tmp_path, "b.md")
    r = _run(tmp_path, "--baseline", str(base))
    assert r.returncode == 1
    assert r.stdout.count("[baseline]") == 1  # only the frozen one is marked
    assert "specs/b.md" in r.stdout


def test_compare_no_match_exits_one(tmp_path):
    _bad_spec(tmp_path)
    base = tmp_path / "empty.json"
    base.write_text(json.dumps({"version": 1, "violations": []}), encoding="utf-8")
    r = _run(tmp_path, "--baseline", str(base))
    assert r.returncode == 1
    assert "[baseline]" not in r.stdout


def test_compare_json_shape(tmp_path):
    _bad_context(tmp_path)
    base = tmp_path / "base.json"
    assert _run(tmp_path, "--baseline-generate", str(base)).returncode == 0
    r = _run(tmp_path, "--baseline", str(base), "--json")
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["findings"] == []
    assert payload["suppressed"] == {}
    assert payload["baseline"] == {"matched": 1, "new": 0}


def test_compare_corrupt_baseline_exits_two(tmp_path):
    _bad_context(tmp_path)
    base = tmp_path / "bad.json"
    base.write_text("not json", encoding="utf-8")
    r = _run(tmp_path, "--baseline", str(base))
    assert r.returncode == 2
    assert "baseline error" in r.stderr


def test_compare_missing_baseline_exits_two(tmp_path):
    r = _run(tmp_path, "--baseline", str(tmp_path / "nope.json"))
    assert r.returncode == 2


def test_both_flags_usage_exits_two(tmp_path):
    _bad_context(tmp_path)
    r = _run(
        tmp_path,
        "--baseline",
        str(tmp_path / "a.json"),
        "--baseline-generate",
        str(tmp_path / "b.json"),
    )
    assert r.returncode == 2


def test_main_compare_errors_trump_violations_exit_two(monkeypatch, tmp_path):
    # An internal error forces exit 2 even when findings were matched.
    from context_lint import model

    res = model.RunResult(
        items=[
            model.RunItem(
                file="CONTEXT.md",
                violation=model.Violation(rule="context-md/entry-format", severity="low", line=1, message="x"),
            )
        ],
        errors=[model.InternalError(file="CONTEXT.md", rule="context-md/entry-format", message="boom")],
    )
    monkeypatch.setattr(cli, "run_engine", lambda root: res)
    base = tmp_path / "base.json"
    base.write_text(
        json.dumps({"version": 1, "violations": [{"rule": "context-md/entry-format", "file": "CONTEXT.md", "message": "x"}]}),
        encoding="utf-8",
    )
    assert cli.main(["--root", ".", "--baseline", str(base)]) == 2