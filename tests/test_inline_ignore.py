"""S1 — inline-ignore matcher, exercised purely on string literals (no fixtures)."""

from context_lint import inline_ignore as ign

ALL = ign._ALL


def test_empty_text_no_suppression():
    assert ign.resolve("") == {}
    assert ign.resolve("# just a heading\nno markers\n") == {}


def test_trailing_bare_suppresses_own_line():
    protected = ign.resolve("## term <!-- context-lint:ignore -->\n")
    assert protected == {1: {ALL}}


def test_standalone_bare_protects_self_and_next():
    protected = ign.resolve("<!-- context-lint:ignore -->\n## term\n")
    assert protected[1] == {ALL}
    assert protected[2] == {ALL}


def test_trailing_scoped_maps_exact_ids():
    protected = ign.resolve("<!-- context-lint:ignore a,b -->\n")
    assert protected[1] == {"a", "b"}


def test_standalone_scoped_protects_self_and_next():
    protected = ign.resolve("<!-- context-lint:ignore a,b -->\ncontent\n")
    assert protected[1] == {"a", "b"}
    assert protected[2] == {"a", "b"}


def test_ids_trimmed_of_whitespace():
    protected = ign.resolve("<!-- context-lint:ignore  a ,  b  -->\n")
    assert protected[1] == {"a", "b"}


def test_scoped_does_not_suppress_unlisted_rule():
    protected = ign.resolve("<!-- context-lint:ignore a,b -->\n")
    assert ign.suppresses(protected, 1, "a")
    assert ign.suppresses(protected, 1, "b")
    assert not ign.suppresses(protected, 1, "c")


def test_malformed_marker_matches_nothing():
    cases = [
        "<!-- context-lint:ignore",  # missing close
        "<!-- contextlint:ignore -->",  # typo
        "<!-- context-lint:icons -->",  # typo in directive word
    ]
    for line in cases:
        assert ign.resolve(line + "\n") == {}


def test_bare_and_scoped_merge_to_all():
    protected = ign.resolve("<!-- context-lint:ignore a --> <!-- context-lint:ignore -->\n")
    assert protected[1] == {ALL}


def test_comma_only_body_treated_as_bare():
    # "ignore , ," trims to no usable ids -> treated as the bare all-rules form
    protected = ign.resolve("<!-- context-lint:ignore , , -->\n")
    assert protected[1] == {ALL}


def test_bom_standalone_protects_next_line():
    # a UTF-8-BOM-prefixed standalone marker must still protect the following line
    protected = ign.resolve("﻿<!-- context-lint:ignore -->\n## term\n")
    assert protected[1] == {ALL}
    assert protected[2] == {ALL}


def test_multiple_scoped_markers_union():
    protected = ign.resolve("<!-- context-lint:ignore a --> <!-- context-lint:ignore b -->\n")
    assert protected[1] == {"a", "b"}


def test_trailing_marker_not_standalone():
    # distinguishing a trailing marker from a standalone (blank aside from marker) line
    protected = ign.resolve("## t <!-- context-lint:ignore -->\n")
    assert 2 not in protected  # trailing must NOT protect the next line