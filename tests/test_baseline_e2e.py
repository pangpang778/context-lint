"""T3 — end-to-end baseline gate over the committed fixture (seam S4).

The fixture (tests/fixtures/baseline/) freezes one entry-format violation into a
committed baseline. This module drives the real CLI and pins: a frozen-snapshot
run is clean (exit 0, all [baseline]), a no-match baseline degrades to exit 1,
regeneration is fingerprint-set-equivalent, and the base rules are undisturbed
without a baseline.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from context_lint import baseline

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "baseline"
PERF_BASE = FIX / "baseline.v1.json"


def _run(*extra):
    return subprocess.run(
        [sys.executable, "-m", "context_lint", "--root", str(FIX), *extra],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_frozen_snapshot_clean():
    r = _run("--baseline", str(PERF_BASE))
    assert r.returncode == 0  # every finding is pre-existing
    assert "CONTEXT.md:1" in r.stdout
    assert "[baseline]" in r.stdout


def test_frozen_snapshot_json_counts():
    r = _run("--baseline", str(PERF_BASE), "--json")
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["findings"] == []  # new-only list is empty
    assert payload["baseline"]["new"] == 0
    assert payload["baseline"]["matched"] >= 1


def test_regenerate_is_fingerprint_equivalent():
    with tempfile.TemporaryDirectory() as td:
        regen = Path(td) / "regen.json"
        assert _run("--baseline-generate", str(regen)).returncode == 0
        # set-equality: record order and generatedAt must not matter
        assert baseline.load_baseline(PERF_BASE) == baseline.load_baseline(regen)


def test_no_match_baseline_exits_one():
    with tempfile.TemporaryDirectory() as td:
        empty = Path(td) / "empty.json"
        empty.write_text(json.dumps({"version": 1, "violations": []}), encoding="utf-8")
        r = _run("--baseline", str(empty))
        assert r.returncode == 1  # no silent "clean because baseline" trap
        assert "[baseline]" not in r.stdout


def test_base_rules_undisturbed_without_baseline():
    # Without a baseline the fixture's violation still raises exit 1.
    r = _run()
    assert r.returncode == 1
    assert "context-md/entry-format" in r.stdout