"""Unit tests for the frontmatter reader (data-model § 2)."""

from __future__ import annotations

import textwrap

import pytest
import yaml

from bookwright.io.frontmatter import parse_frontmatter


def test_valid_fence_returns_metadata_body_and_key_lines() -> None:
    text = textwrap.dedent(
        """\
        ---
        name: "Aparici"
        born: 1828
        ---
        The body.
        """
    )
    fm = parse_frontmatter(text)
    assert fm.metadata == {"name": "Aparici", "born": 1828}
    assert fm.body.strip() == "The body."
    # `name` is the file's line 2, `born` line 3 (line 1 is the opening fence).
    assert fm.key_lines == {"name": 2, "born": 3}


def test_no_fence_yields_empty_metadata() -> None:
    text = "Just a body, no frontmatter.\n"
    fm = parse_frontmatter(text)
    assert fm.metadata == {}
    assert fm.body == text.rstrip("\n") or fm.body == text
    assert fm.key_lines == {}


def test_unclosed_fence_yields_empty_metadata() -> None:
    text = "---\nname: x\n"
    fm = parse_frontmatter(text)
    assert fm.metadata == {}


def test_key_lines_are_one_based_and_track_nested_owner() -> None:
    text = textwrap.dedent(
        """\
        ---
        name: "Aparici"
        features:
          - one
          - two
        narrative_roles:
          - protagonist
        ---
        """
    )
    fm = parse_frontmatter(text)
    assert fm.key_lines["name"] == 2
    assert fm.key_lines["features"] == 3
    assert fm.key_lines["narrative_roles"] == 6


def test_malformed_yaml_surfaces_for_caller_to_wrap() -> None:
    text = "---\nname: : :\n  bad\n---\n"
    with pytest.raises(yaml.YAMLError):
        parse_frontmatter(text)
