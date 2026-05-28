"""US4 — Acceptance Scenarios 1, 1a, 1b (FR-015, FR-016, FR-017, SC-004)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from bookwright.core import Manifest, ManifestValidationError


def test_minimal_build_applies_fr017_defaults() -> None:
    """FR-015 + FR-017 + AS1: minimal-input build fills defaults."""

    m = Manifest.build(
        title="The Default Book",
        authors=["Default Author"],
        integration_key="claude",
        uri_base="https://example.org/d/",
    )

    assert m.book.title == "The Default Book"
    assert m.book.authors == ["Default Author"]
    assert m.integration.key == "claude"
    assert m.integration.skills_dir == ".claude/skills"
    assert m.bookwright.uri_base == "https://example.org/d/"

    # FR-017 defaults
    assert m.book.type == "novel"
    assert m.book.language == "en"
    assert m.book.status == "drafting"
    assert m.book.subtitle == ""
    assert m.book.genre == []
    assert m.book.target_length_words is None
    assert m.bookwright.manifest_version == "1"
    assert m.bookwright.schema_version == "golem-1.0"
    assert m.bookwright.indexer == "rdflib"
    assert m.paths.manuscript == "manuscript/"
    assert m.paths.bible == "bible/"
    assert m.paths.outline == "outline/"
    assert m.paths.graph == "bible/graph.ttl"
    assert m.paths.constitution == "bible/constitution.md"


def test_generic_integration_default_skills_dir() -> None:
    """FR-017: skills_dir default differs by integration_key."""

    m = Manifest.build(
        title="G",
        authors=["A"],
        integration_key="generic",
        uri_base="https://example.org/g/",
    )
    assert m.integration.skills_dir == ".agents/skills"


def test_overrides_take_effect_and_validate() -> None:
    """AS1a: overrides land in the manifest and still pass validation."""

    m = Manifest.build(
        title="Una memoria",
        authors=["Ana Ruiz"],
        integration_key="generic",
        uri_base="https://example.org/m/",
        language="es",
        type="memoir",
        status="structuring",
        subtitle="Entre dos puertos",
        genre=["literatura", "memoria"],
        target_length_words=60000,
        integration_options={"flavor": "cursor"},
        vocabularies_active=["core"],
    )

    assert m.book.language == "es"
    assert m.book.type == "memoir"
    assert m.book.status == "structuring"
    assert m.book.subtitle == "Entre dos puertos"
    assert m.book.genre == ["literatura", "memoria"]
    assert m.book.target_length_words == 60000  # noqa: PLR2004
    assert m.integration.options == {"flavor": "cursor"}
    assert m.vocabularies.active == ["core"]


def test_unknown_override_raises_type_error() -> None:
    """AS1b + SC-004: unknown override names raise `TypeError` immediately."""

    with pytest.raises(TypeError) as exc_info:
        Manifest.build(
            title="x",
            authors=["a"],
            integration_key="claude",
            uri_base="https://example.org/x/",
            flavor="spicy",
        )
    assert "flavor" in str(exc_info.value)


def test_rule_violating_override_raises_validation_error() -> None:
    """A rule-violating override raises `ManifestValidationError`, not TypeError."""

    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.build(
            title="x",
            authors=["a"],
            integration_key="claude",
            uri_base="https://example.org/x/",
            language="klingon",
        )
    assert any(
        f.field_path == "book.language" and f.rule_id == "book.language.not_iso_639_1"
        for f in exc_info.value.failures
    )


def test_omitting_uri_base_raises_validation_error() -> None:
    """A `build(...)` call without `uri_base=` fails validation citing bookwright.uri_base."""

    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.build(title="x", authors=["a"], integration_key="claude")
    assert any(f.field_path == "bookwright.uri_base" for f in exc_info.value.failures)


def test_unknown_integration_key_without_skills_dir_raises_type_error() -> None:
    """An unknown integration_key without an explicit skills_dir is a programming error."""

    with pytest.raises(TypeError):
        Manifest.build(
            title="x",
            authors=["a"],
            integration_key="cursor",  # not in DEFAULT_SKILLS_DIR
            uri_base="https://example.org/x/",
        )


def test_unknown_integration_key_with_explicit_skills_dir_succeeds() -> None:
    """An explicit `integration_skills_dir` rescues an unknown integration_key."""

    m = Manifest.build(
        title="x",
        authors=["a"],
        integration_key="cursor",
        uri_base="https://example.org/x/",
        integration_skills_dir=".cursor/skills",
    )
    assert m.integration.key == "cursor"
    assert m.integration.skills_dir == ".cursor/skills"


@pytest.mark.parametrize(
    "override_name",
    [
        "subtitle",
        "genre",
        "target_length_words",
        "book_metadata",
        "integration_options",
        "vocabularies_active",
        "validators_enabled",
        "indexer",
    ],
)
def test_none_override_is_treated_as_default(override_name: str) -> None:
    """Passing `None` for an optional override falls back to the template default.

    Regression: previously leaked `tomlkit.exceptions.ConvertError` because
    `document[block][key] = None` is rejected by tomlkit. Callers doing
    conditional propagation (`build(..., subtitle=user_subtitle)` where
    `user_subtitle` may be `None`) MUST get the same result as omitting
    the kwarg entirely.
    """

    m_default = Manifest.build(
        title="X",
        authors=["A"],
        integration_key="claude",
        uri_base="https://example.org/x/",
    )
    m_none = Manifest.build(
        title="X",
        authors=["A"],
        integration_key="claude",
        uri_base="https://example.org/x/",
        **{override_name: None},
    )
    # `None` override produces the same field state as omitting the kwarg.
    assert m_none.model_dump() == m_default.model_dump()


def test_multiple_unknown_overrides_are_all_reported() -> None:
    """Unknown kwargs accumulate into a single `TypeError` message (no fix-and-retry)."""

    with pytest.raises(TypeError) as exc_info:
        Manifest.build(
            title="x",
            authors=["a"],
            integration_key="claude",
            uri_base="https://example.org/x/",
            flavor="spicy",
            spice="mild",
        )
    msg = str(exc_info.value)
    assert "'flavor'" in msg
    assert "'spice'" in msg


def test_non_pep440_installed_version_without_override_raises_runtime_error(
    installed_version: Callable[[str], None],
) -> None:
    """`build()` with a non-PEP-440 installed CLI version blames the *environment*.

    Regression: previously surfaced as `ManifestValidationError` with rule
    `bookwright.cli_version_min.not_pep440`, which is misleading because
    the caller never supplied `cli_version_min`.
    """

    installed_version("not-a-version")
    with pytest.raises(RuntimeError) as exc_info:
        Manifest.build(
            title="X",
            authors=["A"],
            integration_key="claude",
            uri_base="https://example.org/x/",
        )
    msg = str(exc_info.value)
    assert "not-a-version" in msg
    assert "PEP 440" in msg
    assert "cli_version_min" in msg  # message names the kwarg the user can pass


def test_non_pep440_installed_version_with_explicit_override_surfaces_installed_rule(
    installed_version: Callable[[str], None],
) -> None:
    """With an explicit override, the floor check still runs and names *installed*.

    Pins the rule-id distinction: when the user supplied `cli_version_min`,
    a broken environment surfaces as `installed_not_pep440` (well-named),
    NOT as `not_pep440` (which would blame the user's input).
    """

    installed_version("not-a-version")
    with pytest.raises(ManifestValidationError) as exc_info:
        Manifest.build(
            title="X",
            authors=["A"],
            integration_key="claude",
            uri_base="https://example.org/x/",
            cli_version_min="0.0.1",
        )
    failure = exc_info.value.failures[0]
    assert failure.field_path == "bookwright.cli_version_min"
    assert failure.rule_id == "bookwright.cli_version_min.installed_not_pep440"
