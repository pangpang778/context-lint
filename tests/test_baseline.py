"""T1 — baseline fingerprint + version-1 baseline load/write (seams S1+S2)."""

import json

import pytest

from context_lint import baseline


def test_fingerprint_deterministic_and_sensitive():
    a = baseline.fingerprint("durability/spec-coordinates", "specs/a.md", "file-path coordinate")
    assert baseline.fingerprint("durability/spec-coordinates", "specs/a.md", "file-path coordinate") == a
    assert baseline.fingerprint("other", "specs/a.md", "file-path coordinate") != a
    assert baseline.fingerprint("durability/spec-coordinates", "specs/b.md", "file-path coordinate") != a
    assert baseline.fingerprint("durability/spec-coordinates", "specs/a.md", "different") != a


def test_fingerprint_is_line_free():
    # The fingerprint input omits line and severity, so line drift cannot break a match.
    assert baseline.fingerprint("r", "a.md", "msg") == baseline.fingerprint("r", "a.md", "msg")


def test_write_load_roundtrip(tmp_path):
    path = tmp_path / "base.json"
    records = [
        {"rule": "context-md/entry-format", "file": "CONTEXT.md", "message": "missing field"},
        {"rule": "durability/spec-coordinates", "file": "specs/a.md", "message": "src/x.js"},
    ]
    baseline.write_baseline(path, records, "2026-01-01T00:00:00+00:00")

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert data["generatedAt"] == "2026-01-01T00:00:00+00:00"
    assert len(data["violations"]) == 2

    loaded = baseline.load_baseline(path)
    assert baseline.fingerprint("context-md/entry-format", "CONTEXT.md", "missing field") in loaded
    assert baseline.fingerprint("durability/spec-coordinates", "specs/a.md", "src/x.js") in loaded


def test_load_collapses_duplicate_records(tmp_path):
    path = tmp_path / "d.json"
    baseline.write_baseline(
        path,
        [
            {"rule": "r", "file": "a.md", "message": "m"},
            {"rule": "r", "file": "a.md", "message": "m"},
        ],
        "t",
    )
    assert len(baseline.load_baseline(path)) == 1


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(baseline.BaselineError):
        baseline.load_baseline(tmp_path / "nope.json")


def test_load_malformed_json_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("not json {", encoding="utf-8")
    with pytest.raises(baseline.BaselineError):
        baseline.load_baseline(path)


def test_load_unsupported_version_raises(tmp_path):
    path = tmp_path / "v2.json"
    path.write_text(json.dumps({"version": 2, "violations": []}), encoding="utf-8")
    with pytest.raises(baseline.BaselineError):
        baseline.load_baseline(path)


def test_load_missing_records_list_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"version": 1}), encoding="utf-8")
    with pytest.raises(baseline.BaselineError):
        baseline.load_baseline(path)


def test_load_non_string_record_values_raise(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps({"version": 1, "violations": [{"rule": 1, "file": 2, "message": 3}]}),
        encoding="utf-8",
    )
    with pytest.raises(baseline.BaselineError):
        baseline.load_baseline(path)