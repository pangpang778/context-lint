"""Tests for context_lint.config_file (T1: config-file feature)."""

import pytest

from context_lint.config_file import Config, ConfigError, load

KNOWN_IDS = {"rule-a", "rule-b", "rule-c"}


class TestEmptyConfig:
    def test_empty_object_yields_empty_config(self):
        config = load("{}", KNOWN_IDS)
        assert config.ignore == frozenset()
        assert config.severity_overrides == {}

    def test_missing_keys_yield_defaults(self):
        config = load('{"ignore": []}', KNOWN_IDS)
        assert config.ignore == frozenset()
        assert config.severity_overrides == {}

    def test_config_is_frozen(self):
        config = load("{}", KNOWN_IDS)
        with pytest.raises(AttributeError):  # FrozenInstanceError subclasses AttributeError
            config.ignore = frozenset({"rule-a"})


class TestPopulatedConfig:
    def test_ignore_and_severity_overrides_populate(self):
        text = (
            '{"ignore": ["rule-a"],'
            ' "severityOverrides": {"rule-b": "high", "rule-c": "low"}}'
        )
        config = load(text, KNOWN_IDS)
        assert config.ignore == frozenset({"rule-a"})
        assert config.severity_overrides == {"rule-b": "high", "rule-c": "low"}

    def test_known_ids_iterable_is_deduped(self):
        config = load('{"ignore": ["rule-a"]}', ["rule-a", "rule-a", "rule-b"])
        assert config.ignore == frozenset({"rule-a"})


class TestUnknownRuleIds:
    def test_unknown_id_in_ignore_raises(self):
        with pytest.raises(ConfigError) as excinfo:
            load('{"ignore": ["nope"]}', KNOWN_IDS)
        assert "nope" in str(excinfo.value)

    def test_unknown_id_in_severity_overrides_raises(self):
        with pytest.raises(ConfigError) as excinfo:
            load('{"severityOverrides": {"nope": "high"}}', KNOWN_IDS)
        assert "nope" in str(excinfo.value)

    def test_unknown_top_level_key_raises(self):
        with pytest.raises(ConfigError) as excinfo:
            load('{"ingore": ["rule-a"]}', KNOWN_IDS)  # typo'd key
        assert "ingore" in str(excinfo.value)


class TestBadSeverityValues:
    def test_bad_severity_value_raises(self):
        with pytest.raises(ConfigError) as excinfo:
            load('{"severityOverrides": {"rule-a": "urgent"}}', KNOWN_IDS)
        assert "urgent" in str(excinfo.value)

    def test_unhashable_severity_value_raises(self):
        with pytest.raises(ConfigError):
            load('{"severityOverrides": {"rule-a": ["high"]}}', KNOWN_IDS)

    def test_non_string_severity_value_raises(self):
        with pytest.raises(ConfigError) as excinfo:
            load('{"severityOverrides": {"rule-a": 3}}', KNOWN_IDS)
        assert "3" in str(excinfo.value)


class TestMalformedInput:
    def test_empty_text_raises(self):
        with pytest.raises(ConfigError):
            load("", KNOWN_IDS)

    def test_malformed_json_raises(self):
        with pytest.raises(ConfigError):
            load('{"ignore": ["rule-a"', KNOWN_IDS)

    def test_trailing_garbage_json_raises(self):
        with pytest.raises(ConfigError):
            load('{"ignore": []} trailing', KNOWN_IDS)

    def test_non_object_root_array_raises(self):
        with pytest.raises(ConfigError):
            load('["rule-a"]', KNOWN_IDS)

    def test_non_object_root_string_raises(self):
        with pytest.raises(ConfigError):
            load('"just a string"', KNOWN_IDS)

    def test_non_object_root_null_raises(self):
        with pytest.raises(ConfigError):
            load("null", KNOWN_IDS)

    def test_ignore_not_a_list_raises(self):
        with pytest.raises(ConfigError) as excinfo:
            load('{"ignore": "rule-a"}', KNOWN_IDS)
        assert "ignore" in str(excinfo.value)

    def test_ignore_entry_not_a_string_raises(self):
        with pytest.raises(ConfigError) as excinfo:
            load('{"ignore": [42]}', KNOWN_IDS)
        assert "42" in str(excinfo.value)

    def test_severity_overrides_not_an_object_raises(self):
        with pytest.raises(ConfigError):
            load('{"severityOverrides": ["rule-a"]}', KNOWN_IDS)


class TestConfigErrorShape:
    def test_config_error_is_exception(self):
        assert issubclass(ConfigError, Exception)


class TestIgnorePlusOverrideInteraction:
    def test_rule_in_both_maps_still_ignored(self):
        text = (
            '{"ignore": ["rule-a"],'
            ' "severityOverrides": {"rule-a": "high"}}'
        )
        config = load(text, KNOWN_IDS)
        assert "rule-a" in config.ignore
        assert config.severity_overrides == {"rule-a": "high"}


class TestKnownIdsHandling:
    def test_empty_known_ids_reject_everything(self):
        with pytest.raises(ConfigError) as excinfo:
            load('{"ignore": ["rule-a"]}', set())
        assert "rule-a" in str(excinfo.value)


def test_config_defaults():
    config = Config()
    assert config.ignore == frozenset()
    assert config.severity_overrides == {}
