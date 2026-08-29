import json
import subprocess
import sys
from pathlib import Path

from context_lint import engine
from context_lint.rules import durability as r

ROOT = Path(__file__).resolve().parents[1]


def test_plain_file_path_flagged():
    vs = r.run("See src/store.js for details.\n")
    assert len(vs) == 1
    assert vs[0].rule == r.ID
    assert vs[0].severity == r.SEVERITY
    assert vs[0].severity == "high"
    assert vs[0].line == 1
    assert "src/store.js" in vs[0].message


def test_directory_address_flagged():
    vs = r.run("Layout lives under path/to/ for now.\n")
    assert len(vs) == 1
    assert vs[0].line == 1
    assert "path/to/" in vs[0].message


def test_rule_identifier_not_flagged():
    # Final `/` segment `entry-format` has no dot -> not a coordinate (C2 #1).
    assert r.run("Routed by context-md/entry-format above.\n") == []


def test_dot_in_non_final_segment_not_flagged():
    # Refined predicate (C2 #1): a dot must sit in the FINAL `/` segment. These
    # all carry a dot in a non-final segment but their final segment is clean,
    # so the old "contains / and ." wording would have false-flagged them.
    assert r.run("lives under docs/v1.2/api for now.\n") == []
    assert r.run("Ref models/user.v2/schema.\n") == []


def test_origin_fragment_marker_exempts_whole_line():
    assert r.run("See src/store.js <!-- origin-fragment --> for provenance.\n") == []


def test_cjk_adjacent_token_exempt():
    # F-0008 lesson: coordinates embedded in CJK prose are exempt.
    assert r.run("关于/src/store.js的说明\n") == []


def test_cjk_inside_token_exempt():
    assert r.run("见 src/文件.md 条目\n") == []


def test_bare_filename_without_slash_not_flagged():
    assert r.run("Read spec.md before starting.\n") == []


def test_clean_prose_line():
    assert r.run("No coordinates here, just words and 42 numbers.\n") == []


def test_wrapping_punctuation_stripped_and_line_number_kept():
    text = "# Title\n\nUses (src/store.js) at the core.\n"
    vs = r.run(text)
    assert len(vs) == 1
    assert vs[0].line == 3
    assert "src/store.js" in vs[0].message


def test_empty_text():
    assert r.run("") == []


def test_engine_routes_specs_file(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "a.md").write_text("See src/store.js for details.\n", encoding="utf-8")
    res = engine.run(str(tmp_path))
    assert res.errors == []
    assert len(res.items) == 1
    item = res.items[0]
    assert item.file == "specs/a.md"
    assert item.violation.rule == r.ID
    assert item.violation.severity == "high"


def test_cli_json_smoke(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "a.md").write_text("See src/store.js for details.\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "context_lint", "--root", str(tmp_path), "--json"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert isinstance(payload, list) and len(payload) == 1
    assert set(payload[0]) == {"rule", "severity", "line", "message"}
    assert payload[0]["rule"] == r.ID
    assert payload[0]["severity"] == "high"
