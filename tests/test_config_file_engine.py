"""T2 - config-file integration: engine wiring, severity gate, CLI surfacing.

Covers the load-once seam (the engine reads <root>/.context-lint.json itself),
the skip-before-suppression contract for ignored rules, the pure `apply`
severity remap, the high-only exit gate, ConfigError -> exit 2, baseline
composition with overrides, and inline-ignore + config-ignore composition.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from context_lint import engine
from context_lint.config_file import Config, ConfigError, apply
from context_lint.model import RunItem, Violation

ROOT = Path(__file__).resolve().parents[1]

LOW_RULE = "context-md/entry-format"     # naturally "low"
HIGH_RULE = "durability/spec-coordinates"  # naturally "high"

# One entry-format violation (missing 已解决的歧义) anchored on line 1.
BAD_CONTEXT = "## term\n- 定义: a\n- 边界: b\n"
# One spec-coordinate violation (high) in a specs/ file.
SPEC_COORD = "Ref src/store.js here.\n"


def _mk(root, files):
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _config(root, text):
    (root / ".context-lint.json").write_text(text, encoding="utf-8")


def _cli(root, *extra):
    # PYTHONUTF8=1 pins the child's IO encoding (this box defaults to GBK).
    env = {**os.environ, "PYTHONUTF8": "1"}
    return subprocess.run(
        [sys.executable, "-m", "context_lint", "--root", str(root), *extra],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def _item(rule, severity, line=1):
    return RunItem(file="CONTEXT.md", violation=Violation(rule=rule, severity=severity, line=line, message="m"))


class TestIgnoredRuleSkipsWalk:
    def test_engine_ignored_rule_never_items_nor_suppressed(self, tmp_path):
        _mk(tmp_path, {"CONTEXT.md": BAD_CONTEXT})
        _config(tmp_path, '{"ignore": ["context-md/entry-format"]}')
        res = engine.run(str(tmp_path))
        assert res.items == []
        assert res.errors == []
        # the crux: skipped BEFORE suppression counting, so not even a count
        assert res.suppressed == {}

    def test_cli_only_firing_rule_ignored_exits_zero(self, tmp_path):
        _mk(tmp_path, {"CONTEXT.md": BAD_CONTEXT})
        _config(tmp_path, '{"ignore": ["context-md/entry-format"]}')
        r = _cli(tmp_path)
        assert r.returncode == 0
        assert r.stdout == ""

    def test_cli_ignored_rule_absent_from_json(self, tmp_path):
        _mk(tmp_path, {"CONTEXT.md": BAD_CONTEXT})
        _config(tmp_path, '{"ignore": ["context-md/entry-format"]}')
        r = _cli(tmp_path, "--json")
        assert r.returncode == 0
        payload = json.loads(r.stdout)
        assert payload["findings"] == []
        assert payload["suppressed"] == {}

    def test_smoke_config_ignores_own_firing_high_rule(self, tmp_path):
        # F-0005: a root whose config ignores its own firing high rule exits 0
        # and the rule is absent from stdout and --json entirely.
        _mk(tmp_path, {"specs/a.md": SPEC_COORD})
        _config(tmp_path, '{"ignore": ["durability/spec-coordinates"]}')
        r = _cli(tmp_path)
        assert r.returncode == 0
        assert r.stdout == ""
        rj = _cli(tmp_path, "--json")
        assert rj.returncode == 0
        payload = json.loads(rj.stdout)
        assert payload["findings"] == []
        assert payload["suppressed"] == {}
        assert HIGH_RULE not in json.dumps(payload)


class TestSeverityOverride:
    def test_engine_override_loaded_from_root_config_file(self, tmp_path):
        _mk(tmp_path, {"CONTEXT.md": BAD_CONTEXT})
        _config(tmp_path, '{"severityOverrides": {"context-md/entry-format": "high"}}')
        res = engine.run(str(tmp_path))
        assert len(res.items) == 1
        assert res.items[0].violation.severity == "high"

    def test_engine_explicit_config_beats_config_file(self, tmp_path):
        _mk(tmp_path, {"CONTEXT.md": BAD_CONTEXT})
        _config(tmp_path, "not json")  # must NOT be read when config is passed
        config = Config(severity_overrides={LOW_RULE: "high"})
        res = engine.run(str(tmp_path), config)
        assert res.items[0].violation.severity == "high"

    def test_cli_low_overridden_to_high_exits_one(self, tmp_path):
        _mk(tmp_path, {"CONTEXT.md": BAD_CONTEXT})
        _config(tmp_path, '{"severityOverrides": {"context-md/entry-format": "high"}}')
        r = _cli(tmp_path)
        assert r.returncode == 1
        assert "context-md/entry-format" in r.stdout
        assert "[high]" in r.stdout

    def test_cli_high_overridden_to_low_exits_zero_still_prints(self, tmp_path):
        _mk(tmp_path, {"specs/a.md": SPEC_COORD})
        _config(tmp_path, '{"severityOverrides": {"durability/spec-coordinates": "low"}}')
        r = _cli(tmp_path)
        assert r.returncode == 0
        assert "spec-coordinates" in r.stdout  # finding still printed
        assert "[low]" in r.stdout

    def test_cli_json_renders_overridden_severity(self, tmp_path):
        _mk(tmp_path, {"CONTEXT.md": BAD_CONTEXT})
        _config(tmp_path, '{"severityOverrides": {"context-md/entry-format": "high"}}')
        r = _cli(tmp_path, "--json")
        assert r.returncode == 1
        payload = json.loads(r.stdout)
        assert len(payload["findings"]) == 1
        assert payload["findings"][0]["severity"] == "high"


class TestApplyPure:
    def test_apply_remaps_severity_without_mutation(self):
        items = [_item(LOW_RULE, "low")]
        config = Config(severity_overrides={LOW_RULE: "high"})
        out = apply(items, config)
        assert len(out) == 1
        assert out[0] is not items[0]
        assert out[0].violation is not items[0].violation
        assert out[0].violation.severity == "high"
        assert items[0].violation.severity == "low"  # original untouched

    def test_apply_drops_ignored_rule_items(self):
        items = [_item(LOW_RULE, "low"), _item(HIGH_RULE, "high")]
        config = Config(ignore=frozenset({LOW_RULE}))
        out = apply(items, config)
        assert [it.violation.rule for it in out] == [HIGH_RULE]

    def test_apply_noop_without_overrides(self):
        items = [_item(LOW_RULE, "low"), _item(HIGH_RULE, "high")]
        out = apply(items, Config())
        assert out == items
        assert out[0] is items[0] and out[1] is items[1]

    def test_apply_preserves_identity_fields(self):
        items = [
            RunItem(
                file="CONTEXT.md",
                violation=Violation(rule=LOW_RULE, severity="low", line=7, message="msg"),
            )
        ]
        out = apply(items, Config(severity_overrides={LOW_RULE: "high"}))
        v = out[0].violation
        assert (out[0].file, v.rule, v.line, v.message) == ("CONTEXT.md", LOW_RULE, 7, "msg")


class TestConfigErrorPaths:
    def test_engine_raises_config_error_on_malformed_file(self, tmp_path):
        _mk(tmp_path, {"CONTEXT.md": BAD_CONTEXT})
        _config(tmp_path, "not json")
        with pytest.raises(ConfigError):
            engine.run(str(tmp_path))

    def test_engine_raises_config_error_on_unknown_id(self, tmp_path):
        _config(tmp_path, '{"ignore": ["nope/nope"]}')
        with pytest.raises(ConfigError):
            engine.run(str(tmp_path))

    def test_cli_malformed_config_exits_two_no_findings(self, tmp_path):
        _mk(tmp_path, {"specs/a.md": SPEC_COORD})
        _config(tmp_path, "{not json")
        r = _cli(tmp_path)
        assert r.returncode == 2
        assert "config error:" in r.stderr
        assert r.stdout == ""
        # config beats linting: --json emits no findings either
        rj = _cli(tmp_path, "--json")
        assert rj.returncode == 2
        assert rj.stdout == ""

    def test_cli_empty_config_file_exits_two(self, tmp_path):
        _mk(tmp_path, {"CONTEXT.md": BAD_CONTEXT})
        _config(tmp_path, "")
        r = _cli(tmp_path)
        assert r.returncode == 2
        assert "config error:" in r.stderr
        assert r.stdout == ""

    def test_cli_unknown_id_config_exits_two(self, tmp_path):
        _mk(tmp_path, {"CONTEXT.md": BAD_CONTEXT})
        _config(tmp_path, '{"severityOverrides": {"nope/nope": "high"}}')
        r = _cli(tmp_path)
        assert r.returncode == 2
        assert "config error:" in r.stderr
        assert r.stdout == ""


class TestNoConfigIdentity:
    def test_engine_missing_config_equals_explicit_empty(self, tmp_path):
        _mk(tmp_path, {"CONTEXT.md": BAD_CONTEXT, "specs/s.md": SPEC_COORD})
        implicit = engine.run(str(tmp_path))
        explicit = engine.run(str(tmp_path), Config())
        assert implicit.items == explicit.items
        assert implicit.errors == explicit.errors
        assert implicit.suppressed == explicit.suppressed

    def test_cli_output_identical_with_and_without_empty_config_file(self, tmp_path):
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        _mk(a, {"CONTEXT.md": BAD_CONTEXT, "specs/s.md": SPEC_COORD})
        _mk(b, {"CONTEXT.md": BAD_CONTEXT, "specs/s.md": SPEC_COORD})
        _config(b, "{}")
        ra = _cli(a)
        rb = _cli(b)
        assert ra.returncode == rb.returncode
        assert ra.stdout == rb.stdout


class TestBaselineComposition:
    def test_baseline_new_high_still_trips_exit_one(self, tmp_path):
        _mk(tmp_path, {"specs/a.md": SPEC_COORD})
        base = tmp_path / "base.json"
        assert _cli(tmp_path, "--baseline-generate", str(base)).returncode == 0
        _mk(tmp_path, {"specs/b.md": "Ref lib/util.js here.\n"})
        r = _cli(tmp_path, "--baseline", str(base))
        assert r.returncode == 1
        assert r.stdout.count("[baseline]") == 1
        assert "specs/b.md" in r.stdout

    def test_baseline_matched_high_stays_exempt(self, tmp_path):
        _mk(tmp_path, {"specs/a.md": SPEC_COORD})
        base = tmp_path / "base.json"
        assert _cli(tmp_path, "--baseline-generate", str(base)).returncode == 0
        r = _cli(tmp_path, "--baseline", str(base))
        assert r.returncode == 0
        assert "[baseline]" in r.stdout
        assert "spec-coordinates" in r.stdout

    def test_baseline_new_low_after_override_does_not_trip_exit_one(self, tmp_path):
        _config(tmp_path, '{"severityOverrides": {"durability/spec-coordinates": "low"}}')
        _mk(tmp_path, {"specs/a.md": SPEC_COORD})
        base = tmp_path / "base.json"
        assert _cli(tmp_path, "--baseline-generate", str(base)).returncode == 0
        _mk(tmp_path, {"specs/b.md": "Ref lib/util.js here.\n"})
        r = _cli(tmp_path, "--baseline", str(base))
        # the NEW finding is low after the override -> exit 0, both printed
        assert r.returncode == 0
        assert r.stdout.count("[baseline]") == 1
        assert "specs/b.md" in r.stdout
        assert "[low]" in r.stdout


class TestInlineIgnoreComposition:
    def test_inline_suppressed_counts_and_config_ignored_absent(self, tmp_path):
        _mk(
            tmp_path,
            {
                "CONTEXT.md": "## term <!-- context-lint:ignore -->\n- 定义: a\n- 边界: b\n",
                "specs/a.md": SPEC_COORD,
            },
        )
        _config(tmp_path, '{"ignore": ["durability/spec-coordinates"]}')
        res = engine.run(str(tmp_path))
        # inline-suppressed low finding still counts in suppressed...
        assert res.suppressed == {"context-md/entry-format": 1}
        # ...while the config-ignored high rule is in neither items nor suppressed
        assert res.items == []
        assert res.errors == []

    def test_cli_json_composition(self, tmp_path):
        _mk(
            tmp_path,
            {
                "CONTEXT.md": "## term <!-- context-lint:ignore -->\n- 定义: a\n- 边界: b\n",
                "specs/a.md": SPEC_COORD,
            },
        )
        _config(tmp_path, '{"ignore": ["durability/spec-coordinates"]}')
        r = _cli(tmp_path, "--json")
        assert r.returncode == 0
        payload = json.loads(r.stdout)
        assert payload["findings"] == []
        assert payload["suppressed"] == {"context-md/entry-format": 1}
