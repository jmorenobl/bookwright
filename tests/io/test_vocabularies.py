"""Unit tests for the controlled-vocabulary loader (iteration 030).

Covers the vocabulary-agnostic loader contract (C2/C4/C5) plus the populated
Propp/Greimas data (C1 term counts, C2/C4 ES-EN resolution). See
contracts/vocabulary-typing.md.
"""

from __future__ import annotations

import pytest

from bookwright.io.vocabularies import (
    KNOWN_VOCABULARIES,
    VocabularyDataError,
    _index_turtle,
    load_active_vocabularies,
    load_vocabulary,
)

# --- loader-agnostic clauses (C2/C4/C5) -------------------------------------

_COLLIDING_TTL = """\
@prefix crm:  <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<https://example.org/v#a>
    a crm:E55_Type ; rdfs:label "Hero"@en .
<https://example.org/v#b>
    a crm:E55_Type ; rdfs:label "hero"@es .
"""

_OK_TTL = """\
@prefix crm:  <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<https://example.org/v#a>
    a crm:E55_Type ; rdfs:label "Hero"@en, "héroe"@es .
"""


def test_disjointness_guard_raises_on_slug_collision() -> None:
    """C2/FR-011: two distinct terms slugging to one alias is a load-time data error."""
    with pytest.raises(VocabularyDataError):
        _index_turtle(_COLLIDING_TTL, "fixture")


def test_two_labels_on_one_term_do_not_collide() -> None:
    """The guard fires only across *distinct* terms — multiple labels (even slugging
    to the same value) on one term are fine, and both forms resolve to it."""
    index = _index_turtle(_OK_TTL, "fixture")
    assert index.resolve("Hero") == index.resolve("héroe") is not None


def test_resolve_returns_none_for_no_match() -> None:
    """C4: a name matching no term resolves to ``None``."""
    index = _index_turtle(_OK_TTL, "fixture")
    assert index.resolve("villain") is None


def test_resolve_returns_none_for_unsluggable_name() -> None:
    """C4: a name that slugs to the empty string resolves to ``None`` (no raise)."""
    index = _index_turtle(_OK_TTL, "fixture")
    assert index.resolve("!!!") is None


def test_load_active_ignores_unknown_name() -> None:
    """C5: ``load_active_vocabularies`` loads known names and silently ignores the rest."""
    active = load_active_vocabularies(["propp", "totally-unknown"])
    assert active.propp is not None
    assert active.greimas is None


def test_load_active_empty_is_all_none() -> None:
    """An empty active list types nothing (FR-008): both slots ``None``."""
    active = load_active_vocabularies([])
    assert active.propp is None and active.greimas is None


def test_known_vocabularies_set() -> None:
    assert set(KNOWN_VOCABULARIES) == {"propp", "greimas"}


# --- Propp populated data (C1/C2/C4) ----------------------------------------


def test_propp_loads_31_terms_without_collision() -> None:
    """C1 (Propp): exactly 31 distinct ``crm:E55_Type`` terms, no slug collision."""
    index = load_vocabulary("propp")
    assert len(set(index._by_slug.values())) == 31


def test_propp_resolves_en_es_and_villainy_lack_to_one_term() -> None:
    """C2/C4: departure/partida share a term; all four villainy/lack forms share one."""
    index = load_vocabulary("propp")
    assert index.resolve("departure") == index.resolve("partida") is not None
    villainy = index.resolve("villainy")
    assert villainy is not None
    assert index.resolve("LACK") == villainy
    assert index.resolve("carencia") == villainy
    assert index.resolve("fechoría") == villainy


# --- Greimas populated data (C1/C2/C4) --------------------------------------


def test_greimas_loads_6_terms_without_collision() -> None:
    """C1 (Greimas): exactly 6 distinct ``crm:E55_Type`` terms, no slug collision."""
    index = load_vocabulary("greimas")
    assert len(set(index._by_slug.values())) == 6


def test_greimas_resolves_en_es_to_same_term() -> None:
    """C2/C4: sender/destinador resolve to the same actant term."""
    index = load_vocabulary("greimas")
    assert index.resolve("sender") == index.resolve("destinador") is not None


# --- iteration 047: the render-derived valid-term enumeration (FR-002/016) ---


def test_index_terms_sorted_unique_and_bilingual() -> None:
    """FR-002/FR-016: ``terms`` is the sorted, deduplicated ES+EN ``rdfs:label`` set.

    Greimas has 6 actants, each with one EN + one ES label → 12 distinct, sorted terms
    including both forms of one actant (``helper``/``ayudante``)."""
    terms = load_vocabulary("greimas").terms
    assert list(terms) == sorted(terms)  # sorted → byte-stable
    assert len(terms) == len(set(terms))  # deduplicated
    assert len(terms) == 12
    assert "helper" in terms and "ayudante" in terms  # both languages present


def test_index_terms_stable_across_loads() -> None:
    """FR-016: two ``load_vocabulary`` calls expose an identical ``terms`` tuple."""
    assert load_vocabulary("propp").terms == load_vocabulary("propp").terms


def test_index_terms_from_constructed_ttl() -> None:
    """FR-002: ``_index_turtle`` collects every label of every term, sorted+unique."""
    index = _index_turtle(_OK_TTL, "fixture")
    assert index.terms == ("Hero", "héroe")
