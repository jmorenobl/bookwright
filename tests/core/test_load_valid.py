"""US1 - Acceptance Scenarios 1-3 (FR-001, FR-003, FR-022)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from bookwright.core import BOOK_STATUSES, BOOK_TYPES, Manifest

from .conftest import load_fixture


def test_load_full_returns_every_field() -> None:
    """FR-001 + AS1: full-field load returns every value as declared."""

    m = Manifest.load(load_fixture("valid_full.toml"))

    assert m.bookwright.cli_version_min == "0.0.1"
    assert m.bookwright.schema_version == "golem-1.0"
    assert m.bookwright.manifest_version == "1"
    assert m.bookwright.uri_base == "https://example.org/full/"
    assert m.bookwright.indexer == "rdflib"

    assert m.book.title == "The Full Test"
    assert m.book.type == "novel"
    assert m.book.language == "en"
    assert m.book.authors == ["Alice Author", "Bob Writer", "Alice Author"]
    assert m.book.subtitle == "An Exhaustive Fixture"
    assert m.book.genre == ["literary", "speculative"]
    assert m.book.target_length_words == 90000  # noqa: PLR2004
    assert m.book.status == "drafting"
    assert m.book.metadata == {
        "isbn_planned": "978-0-00-000000-0",
        "arbitrary_key": "kept verbatim",
        "nested": {"deeply": "nested too"},
    }

    assert m.vocabularies.active == ["core", "extra"]

    assert m.validators.enabled == ["title-case"]
    assert m.validators.disabled == ["legacy-rule"]
    assert m.validators.custom == ["./validators/my_rule.py"]

    assert m.integration.key == "claude"
    assert m.integration.skills_dir == ".claude/skills"
    assert m.integration.options == {"flavor": "default", "extra_setting": 42}

    assert m.paths.manuscript == "manuscript/"
    assert m.paths.bible == "bible/"
    assert m.paths.outline == "outline/"
    assert m.paths.graph == "bible/graph.ttl"
    assert m.paths.constitution == "bible/constitution.md"

    assert m.warnings == ()


def test_load_minimal_applies_defaults() -> None:
    """FR-001 + AS2: minimal-required load fills optional fields with FR-017 defaults."""

    m = Manifest.load(load_fixture("valid_minimal.toml"))

    assert m.book.title == "Minimal Book"
    assert m.book.type == "essay"
    assert m.book.language == "en"
    assert m.book.authors == ["Solo Author"]

    # FR-017 defaults for optional fields not supplied.
    assert m.book.subtitle == ""
    assert m.book.genre == []
    assert m.book.target_length_words is None
    assert m.book.status == "drafting"
    assert m.book.metadata == {}

    assert m.vocabularies.active == []
    assert m.validators.enabled == []
    assert m.validators.disabled == []
    assert m.validators.custom == []

    assert m.integration.key == "generic"
    assert m.integration.skills_dir == ".agents/skills"
    assert m.integration.options == {}

    assert m.paths.manuscript == "manuscript/"
    assert m.paths.bible == "bible/"
    assert m.paths.outline == "outline/"
    assert m.paths.graph == "bible/graph.ttl"
    assert m.paths.constitution == "bible/constitution.md"

    assert m.bookwright.indexer == "rdflib"


def test_load_exposes_integration_as_data() -> None:
    """FR-022 + AS3: `[integration]` is exposed as data and never re-interpreted."""

    m = Manifest.load(load_fixture("valid_full.toml"))

    # The key is just read; the model layer never consults a dispatcher.
    assert m.integration.key == "claude"
    assert m.integration.skills_dir == ".claude/skills"

    # No registry call should happen — proven by the absence of any symbol
    # the model could have called. Reading the attribute is the entire contract.


def test_load_preserves_duplicate_authors() -> None:
    """Edge case: legitimate duplicate co-author entries round-trip verbatim."""

    m = Manifest.load(load_fixture("valid_full.toml"))
    assert m.book.authors.count("Alice Author") == 2  # noqa: PLR2004


@pytest.mark.parametrize("book_type", sorted(BOOK_TYPES))
def test_load_accepts_every_book_type(book_type: str, tmp_manifest: Callable[[str], Path]) -> None:
    """SC-002: every documented `book.type` loads cleanly."""

    body = f"""
[bookwright]
cli_version_min = "0.0.1"
schema_version = "golem-1.0"
manifest_version = "1"
uri_base = "https://example.org/types/"

[book]
title = "Type Smoke"
type = "{book_type}"
language = "en"
authors = ["Type Tester"]

[integration]
key = "claude"
skills_dir = ".claude/skills"
"""
    path = tmp_manifest(body)
    m = Manifest.load(path)
    assert m.book.type == book_type


@pytest.mark.parametrize("status", sorted(BOOK_STATUSES))
def test_load_accepts_every_book_status(status: str, tmp_manifest: Callable[[str], Path]) -> None:
    """SC-002: every documented `book.status` loads cleanly."""

    body = f"""
[bookwright]
cli_version_min = "0.0.1"
schema_version = "golem-1.0"
manifest_version = "1"
uri_base = "https://example.org/status/"

[book]
title = "Status Smoke"
type = "novel"
language = "en"
authors = ["Status Tester"]
status = "{status}"

[integration]
key = "claude"
skills_dir = ".claude/skills"
"""
    path = tmp_manifest(body)
    m = Manifest.load(path)
    assert m.book.status == status


def test_load_does_not_check_vocabulary_existence(
    tmp_manifest: Callable[[str], Path],
) -> None:
    """FR-023: `vocabularies.active` is not checked against the filesystem in v0."""

    body = """
[bookwright]
cli_version_min = "0.0.1"
schema_version = "golem-1.0"
manifest_version = "1"
uri_base = "https://example.org/voc/"

[book]
title = "Voc Test"
type = "novel"
language = "en"
authors = ["Voc Tester"]

[vocabularies]
active = ["does-not-exist"]

[integration]
key = "claude"
skills_dir = ".claude/skills"
"""
    path = tmp_manifest(body)
    m = Manifest.load(path)
    assert m.vocabularies.active == ["does-not-exist"]
