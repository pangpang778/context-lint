import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(root, *extra):
    return subprocess.run(
        [sys.executable, "-m", "context_lint", "--root", str(root), *extra],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_clean_root_exits_zero(tmp_path):
    r = _run(tmp_path)
    assert r.returncode == 0
    assert r.stdout == ""


def test_clean_root_json_is_empty_object(tmp_path):
    r = _run(tmp_path, "--json")
    assert r.returncode == 0
    assert json.loads(r.stdout) == {"findings": [], "suppressed": {}}


def test_violation_exits_one(tmp_path):
    (tmp_path / "CONTEXT.md").write_text(
        "## rule（规则）\n- 定义: a\n- 边界: b\n", encoding="utf-8"
    )
    r = _run(tmp_path)
    assert r.returncode == 1
    assert "context-md/entry-format" in r.stdout
    assert "CONTEXT.md:1" in r.stdout


def test_json_shape(tmp_path):
    (tmp_path / "CONTEXT.md").write_text(
        "## rule（规则）\n- 定义: a\n- 边界: b\n", encoding="utf-8"
    )
    r = _run(tmp_path, "--json")
    assert r.returncode == 1
    payload = json.loads(r.stdout)
    assert len(payload["findings"]) == 1
    assert set(payload["findings"][0]) == {"rule", "severity", "line", "message"}


def test_root_flag_scans_other_dir(tmp_path):
    # --root default is cwd; an explicit --root to a dir with a bad CONTEXT.md drives it.
    other = tmp_path / "target"
    other.mkdir()
    (other / "CONTEXT.md").write_text("## no-fields-here\n", encoding="utf-8")
    r = _run(other)
    assert r.returncode == 1


def test_internal_error_exits_two_and_reports_stderr(tmp_path):
    # A non-UTF-8 CONTEXT.md is a read/decode failure -> internal error -> exit 2, not 1.
    (tmp_path / "CONTEXT.md").write_bytes(b"\x80\x80\x81")
    r = _run(tmp_path)
    assert r.returncode == 2
    assert "internal error" in r.stderr


def test_errors_trump_violations_exit_two(monkeypatch):
    import context_lint.cli as cli
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
    assert cli.main(["--root", "."]) == 2