"""S3 — end-to-end regression gate over the committed inline-ignore fixture.

The fixture (tests/fixtures/inline_ignore/) paints every placement form against
every rule; this module drives it through the real CLI and pins the resulting
counts, surviving findings, and exit code.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "inline_ignore"


def _cli(*extra):
    env = {**os.environ, "PYTHONUTF8": "1"}
    return subprocess.run(
        [sys.executable, "-m", "context_lint", "--root", str(FIX), *extra],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def test_fixture_json_counts_and_survivors():
    r = _cli("--json")
    assert r.returncode == 1  # unsuppressed findings remain
    payload = json.loads(r.stdout)
    # suppressed across the two entry-format files + the claude-md batch
    assert payload["suppressed"] == {
        "context-md/entry-format": 2,
        "durability/spec-coordinates": 2,
        "claude-md/sections": 6,
    }
    # only the unsuppressed findings surface
    rules = {f["rule"] for f in payload["findings"]}
    assert rules == {"context-md/entry-format", "durability/spec-coordinates"}
    lines = {f["line"] for f in payload["findings"] if f["rule"] == "durability/spec-coordinates"}
    assert lines == {6}  # the scoped-wrong-rule coordinate line survives


def test_fixture_human_mode_survivors():
    r = _cli()
    assert r.returncode == 1
    assert "spec-coordinates" in r.stdout
    assert "src/data.ts" in r.stdout  # the scoped-wrong-rule line is live
    # suppressed entries are absent
    assert "standalone-entry" not in r.stdout
    assert "trailing-bare" not in r.stdout