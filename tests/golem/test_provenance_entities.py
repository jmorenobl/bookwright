"""Unit tests for the provenance entities — Source / Finding / Anchor (iteration 012).

Covers the RDF emission contract (contracts/provenance-graph.md): Source is typed
via E55 and emits **no** ``rdf:type``; Finding/Anchor reify on E13; the open-finding
and time-span emission invariants; and the model-level vocabulary enforcement.
"""

from __future__ import annotations

import datetime

import pytest
from pydantic import ValidationError
from rdflib.namespace import RDF, XSD
from rdflib.term import Literal, URIRef

from bookwright.golem import Anchor, Finding, Source
from bookwright.golem.namespaces import (
    ASSIGNED_ATTRIBUTE_TO,
    BEGIN_OF_BEGIN,
    BW_ASSERTED_BY,
    BW_AUTHOR,
    BW_CLAIM,
    BW_CONSTRAINS,
    BW_OPEN,
    BW_PROMOTES,
    BW_REFERENCE,
    BW_RELIABILITY,
    BW_RELIABILITY_JUSTIFICATION,
    BW_SUPPORTED_BY,
    BW_TRANSLATION,
    CLASS_IRI,
    E52_TIME_SPAN,
    END_OF_END,
    HAS_TIME_SPAN,
    HAS_TYPE,
    RELIABILITY_IRI,
    SOURCE_TYPE_IRI,
)

URI_BASE = "https://example.org/n/"
E13 = CLASS_IRI["AttributeAssignment"]


def _po(entity: object) -> dict[URIRef, list[object]]:
    """Group an entity's emitted triples by predicate → list of objects."""
    grouped: dict[URIRef, list[object]] = {}
    for _s, p, o in entity.to_triples():  # type: ignore[attr-defined]
        grouped.setdefault(p, []).append(o)
    return grouped


def _make_source(**overrides: object) -> Source:
    kwargs: dict[str, object] = {
        "uri_base": URI_BASE,
        "name": "Registro TIP",
        "reference": "https://www.interior.gob.es/tip",
        "author": "Ministerio del Interior",
        "original_language": "es",
        "type": "oficial",
        "reliability": "alta",
        "reliability_justification": "Fuente oficial primaria.",
        "access_date": datetime.date(2026, 5, 30),
        "original_quote": "El detective privado requiere la TIP.",
    }
    kwargs.update(overrides)
    return Source(**kwargs)  # type: ignore[arg-type]


# --- Source (US1) -----------------------------------------------------------


def test_source_uri_is_slugged_segment() -> None:
    source = _make_source()
    assert source.uri == URIRef(f"{URI_BASE}source/registro-tip")


def test_source_emits_no_rdf_type() -> None:
    source = _make_source()
    assert all(p != RDF.type for _s, p, _o in source.to_triples())


def test_source_types_via_e55_individuals() -> None:
    source = _make_source(type="oficial", reliability="alta")
    grouped = _po(source)
    assert grouped[HAS_TYPE] == [SOURCE_TYPE_IRI["oficial"]]
    assert grouped[BW_RELIABILITY] == [RELIABILITY_IRI["alta"]]


def test_source_emits_every_provenance_facet() -> None:
    grouped = _po(_make_source())
    ref = "https://www.interior.gob.es/tip"
    assert grouped[BW_REFERENCE] == [Literal(ref, datatype=XSD.string)]
    assert grouped[BW_AUTHOR] == [Literal("Ministerio del Interior", datatype=XSD.string)]
    assert grouped[BW_RELIABILITY_JUSTIFICATION] == [
        Literal("Fuente oficial primaria.", datatype=XSD.string)
    ]


def test_source_translation_omitted_when_unset() -> None:
    assert BW_TRANSLATION not in _po(_make_source())


def test_source_translation_emitted_when_set() -> None:
    grouped = _po(_make_source(translation="The private detective requires the TIP."))
    assert grouped[BW_TRANSLATION] == [
        Literal("The private detective requires the TIP.", datatype=XSD.string)
    ]


@pytest.mark.parametrize("bad_field", ["type", "reliability"])
def test_source_rejects_out_of_vocabulary(bad_field: str) -> None:
    with pytest.raises(ValidationError):
        _make_source(**{bad_field: "inventado"})


def test_source_rejects_empty_reliability_justification() -> None:
    with pytest.raises(ValidationError):
        _make_source(reliability_justification="   ")


# --- Finding (US2) ----------------------------------------------------------


def test_finding_reifies_on_e13_with_segment() -> None:
    finding = Finding(uri_base=URI_BASE, claim="x", sources=(URIRef(f"{URI_BASE}source/s"),))
    assert finding.uri.startswith(f"{URI_BASE}finding/")
    assert _po(finding)[RDF.type] == [E13]


def test_finding_emits_claim_asserter_bears_on_and_sources() -> None:
    target = URIRef(f"{URI_BASE}character/manuel-de-aparici")
    src = URIRef(f"{URI_BASE}source/registro-tip")
    finding = Finding(
        uri_base=URI_BASE, claim="needs TIP", asserted_by="agent", bears_on=target, sources=(src,)
    )
    grouped = _po(finding)
    assert grouped[BW_CLAIM] == [Literal("needs TIP", datatype=XSD.string)]
    assert grouped[BW_ASSERTED_BY] == [Literal("agent", datatype=XSD.string)]
    assert grouped[ASSIGNED_ATTRIBUTE_TO] == [target]
    assert grouped[BW_SUPPORTED_BY] == [src]


def test_finding_asserted_by_defaults_to_author() -> None:
    finding = Finding(uri_base=URI_BASE, claim="x", sources=(URIRef(f"{URI_BASE}source/s"),))
    assert _po(finding)[BW_ASSERTED_BY] == [Literal("author", datatype=XSD.string)]


def test_finding_one_supported_by_per_source() -> None:
    sources = tuple(URIRef(f"{URI_BASE}source/s{i}") for i in range(3))
    finding = Finding(uri_base=URI_BASE, claim="x", sources=sources)
    assert _po(finding)[BW_SUPPORTED_BY] == list(sources)


def test_open_finding_emits_only_type_and_open() -> None:
    finding = Finding(uri_base=URI_BASE, open=True)
    grouped = _po(finding)
    assert grouped[RDF.type] == [E13]
    assert grouped[BW_OPEN] == [Literal(True)]
    assert BW_CLAIM not in grouped
    assert BW_ASSERTED_BY not in grouped
    assert BW_SUPPORTED_BY not in grouped


def test_closed_finding_emits_no_open_flag() -> None:
    finding = Finding(uri_base=URI_BASE, claim="x", sources=(URIRef(f"{URI_BASE}source/s"),))
    assert BW_OPEN not in _po(finding)


# --- Anchor (US3) -----------------------------------------------------------


def _anchor(**overrides: object) -> Anchor:
    kwargs: dict[str, object] = {
        "uri_base": URI_BASE,
        "promotes": URIRef(f"{URI_BASE}finding/abc"),
        "constrains": URIRef(f"{URI_BASE}character/manuel-de-aparici"),
    }
    kwargs.update(overrides)
    return Anchor(**kwargs)  # type: ignore[arg-type]


def test_anchor_reifies_on_e13_with_segment() -> None:
    anchor = _anchor()
    assert anchor.uri.startswith(f"{URI_BASE}anchor/")
    grouped = _po(anchor)
    assert grouped[RDF.type] == [E13]
    assert grouped[BW_PROMOTES] == [URIRef(f"{URI_BASE}finding/abc")]
    assert grouped[BW_CONSTRAINS] == [URIRef(f"{URI_BASE}character/manuel-de-aparici")]


def test_anchor_with_span_emits_e52_subnode() -> None:
    anchor = _anchor(begin=1995, end=2026)
    grouped = _po(anchor)
    span_uri = URIRef(f"{anchor.uri}/time-span")
    assert grouped[HAS_TIME_SPAN] == [span_uri]
    span = {(p, o) for s, p, o in anchor.to_triples() if s == span_uri}
    assert (RDF.type, E52_TIME_SPAN) in span
    assert (BEGIN_OF_BEGIN, Literal("1995", datatype=XSD.gYear)) in span
    assert (END_OF_END, Literal("2026", datatype=XSD.gYear)) in span


def test_anchor_single_year_span_has_equal_begin_end() -> None:
    anchor = _anchor(begin=2000, end=2000)
    span_uri = URIRef(f"{anchor.uri}/time-span")
    span = {(p, o) for s, p, o in anchor.to_triples() if s == span_uri}
    assert (BEGIN_OF_BEGIN, Literal("2000", datatype=XSD.gYear)) in span
    assert (END_OF_END, Literal("2000", datatype=XSD.gYear)) in span


def test_anchor_without_span_emits_no_time_span() -> None:
    grouped = _po(_anchor())
    assert HAS_TIME_SPAN not in grouped


def test_anchor_omits_constrains_when_none() -> None:
    grouped = _po(_anchor(constrains=None))
    assert BW_CONSTRAINS not in grouped
    assert grouped[BW_PROMOTES] == [URIRef(f"{URI_BASE}finding/abc")]
