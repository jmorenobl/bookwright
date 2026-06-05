"""The ``[research]`` manifest block contract (RB-1..RB-8).

The optional ``[research]`` block extends the iteration-2 model with three typed
fields (``enabled`` / ``source_languages`` / ``min_reliability_for_anchor``),
defaults applied on absence, field-naming validation errors, and (RB-7) comments
that survive a tomlkit round-trip. Contract: contracts/research-block.md.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import get_args

import pytest

from bookwright.core import Manifest, ManifestValidationError, ResearchBlock
from bookwright.core._research_block import ResearchBlock as _BlockDirect
from bookwright.golem.namespaces import RELIABILITY_IRI

_BASE = """\
[bookwright]
cli_version_min = "0.0.1"
schema_version = "golem-1.1"
manifest_version = "1"
uri_base = "https://example.org/research/"

[book]
title = "Research Book"
type = "novel"
language = "es"
authors = ["Solo Author"]

[integration]
key = "generic"
skills_dir = ".agents/skills"
"""


def _with_research(block: str) -> str:
    return f"{_BASE}\n[research]\n{block}"


# --- RB-1 / RB-5 — a present block exposes all three fields -------------------


def test_present_block_exposes_all_fields(tmp_manifest: Callable[[str], Path]) -> None:
    path = tmp_manifest(
        _with_research(
            'enabled = false\nsource_languages = ["de", "pl"]\n'
            'min_reliability_for_anchor = "alta"\n'
        )
    )
    manifest = Manifest.load(path)
    assert manifest.research.enabled is False  # RB-5
    assert manifest.research.source_languages == ["de", "pl"]
    assert manifest.research.min_reliability_for_anchor == "alta"


# --- RB-2 — an absent block loads with documented defaults -------------------


def test_absent_block_applies_defaults(tmp_manifest: Callable[[str], Path]) -> None:
    manifest = Manifest.load(tmp_manifest(_BASE))
    assert manifest.research.enabled is True
    assert manifest.research.source_languages == []
    assert manifest.research.min_reliability_for_anchor == "media"


# --- RB-3 — a bad reliability value names research.min_reliability_for_anchor -


def test_bad_reliability_names_the_field(tmp_manifest: Callable[[str], Path]) -> None:
    path = tmp_manifest(_with_research('min_reliability_for_anchor = "altísima"\n'))
    with pytest.raises(ManifestValidationError) as exc:
        Manifest.load(path)
    fields = {f.field_path for f in exc.value.failures}
    assert "research.min_reliability_for_anchor" in fields


# --- RB-4 — a non-ISO source language names research.source_languages[1] ------


def test_bad_source_language_names_indexed_field(tmp_manifest: Callable[[str], Path]) -> None:
    path = tmp_manifest(_with_research('source_languages = ["de", "zz"]\n'))
    with pytest.raises(ManifestValidationError) as exc:
        Manifest.load(path)
    failures = {f.field_path: f for f in exc.value.failures}
    assert "research.source_languages[1]" in failures
    assert failures["research.source_languages[1]"].rejected_value == "zz"


# --- RB-6 — an unknown key inside [research] is forbidden --------------------


def test_unknown_key_is_forbidden(tmp_manifest: Callable[[str], Path]) -> None:
    path = tmp_manifest(_with_research("foo = 1\n"))
    with pytest.raises(ManifestValidationError) as exc:
        Manifest.load(path)
    fields = {f.field_path for f in exc.value.failures}
    assert "research.foo" in fields


# --- RB-8 — anti-drift: the Literal mirrors the golem reliability vocabulary --


def test_reliability_literal_mirrors_golem_vocabulary() -> None:
    field = ResearchBlock.model_fields["min_reliability_for_anchor"]
    assert set(get_args(field.annotation)) == set(RELIABILITY_IRI)


def test_block_is_re_exported_from_core() -> None:
    # The public surface re-exports the same class the module defines.
    assert ResearchBlock is _BlockDirect


# --- RB-7 — the scaffolded [research] block + comments round-trip (SC-002) ----


def test_scaffolded_block_comments_round_trip(tmp_path: Path) -> None:
    built = Manifest.build(
        title="Round Trip",
        authors=["Solo Author"],
        integration_key="generic",
        uri_base="https://example.org/rt/",
    )
    target = tmp_path / "manifest.toml"
    built.dump(target)

    first = target.read_text(encoding="utf-8")
    # The three explanatory comment lines ship with the block.
    assert "the research system is active" in first
    assert "Source provenances (ISO 639-1 codes)" in first
    assert "Minimum source reliability required before a finding" in first

    # load → dump → load keeps the values and the comments byte-stable.
    reloaded = Manifest.load(target)
    assert reloaded.research.enabled is True
    assert reloaded.research.source_languages == []
    assert reloaded.research.min_reliability_for_anchor == "media"
    reloaded.dump(target, overwrite=True)
    assert target.read_text(encoding="utf-8") == first
