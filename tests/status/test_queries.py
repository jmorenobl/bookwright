"""Status aggregations against an in-memory ``RdflibIndexer`` (020).

Exercises the four entry points of :mod:`bookwright.status.queries` over
hand-built graphs (the ``tests/validation/conftest`` scaffolding, so the anchor
sub-graph shape matches what the validator reads): the open-findings
projection, low-reliability membership (data-model § 2.4), anchor-gap problem
aggregation (one row per anchor), and the validation summary.
"""

from __future__ import annotations

from pathlib import Path

from rdflib.term import Literal as RdfLiteral
from rdflib.term import URIRef

from bookwright.golem.namespaces import (
    BW_CLAIM,
    BW_OPEN,
    BW_RELIABILITY,
    BW_SUPPORTED_BY,
    RELIABILITY_IRI,
)
from bookwright.indexers import RdflibIndexer
from bookwright.io.research import AnchorIdentity, FindingIdentity
from bookwright.status.queries import (
    anchor_gaps,
    low_reliability_findings,
    open_questions,
    validation_summary,
)
from tests.validation.conftest import (
    CORE_FACETS,
    URI_BASE,
    AnchorSpec,
    SourceSpec,
    add_anchor,
    add_present_entity,
    graph_uri,
    load_context,
    research_graph,
    write_project,
)

_TOPIC = "bible/research/tema.md"
_INDEX = "bible/research/_index.md"


def _finding_identity(suffix: str, authored_id: str, relpath: str = _TOPIC) -> FindingIdentity:
    return FindingIdentity(id=authored_id, relpath=relpath, uri=graph_uri(suffix))


def _add_open_finding(engine: RdflibIndexer, suffix: str, claim: str | None) -> None:
    uri = graph_uri(suffix)
    engine.add_triple(uri, str(BW_OPEN), RdfLiteral(True))
    if claim is not None:
        engine.add_triple(uri, str(BW_CLAIM), RdfLiteral(claim))


# --- open_questions -----------------------------------------------------------


def test_open_questions_project_authored_identity_and_optional_claim() -> None:
    engine = RdflibIndexer()
    _add_open_finding(engine, "finding/q1", "¿Qué pasó?")
    _add_open_finding(engine, "finding/q2", None)
    identities = (
        _finding_identity("finding/q2", "q-sin-texto", _INDEX),
        _finding_identity("finding/q1", "q-archivo", _INDEX),
    )
    questions = open_questions(engine, identities)
    # Sorted by (file, id); text is the optional claim; no URI in any record.
    assert [(q.id, q.text, q.file) for q in questions] == [
        ("q-archivo", "¿Qué pasó?", _INDEX),
        ("q-sin-texto", None, _INDEX),
    ]


def test_closed_findings_are_not_open_questions() -> None:
    engine = RdflibIndexer()
    uri = graph_uri("finding/closed")
    engine.add_triple(uri, str(BW_CLAIM), RdfLiteral("Cerrado."))  # no bw:open
    assert open_questions(engine, (_finding_identity("finding/closed", "f1"),)) == ()


# --- low_reliability_findings ---------------------------------------------------


def _add_support(engine: RdflibIndexer, finding: str, source: str, rating: str | None) -> None:
    finding_uri = graph_uri(finding)
    source_uri = graph_uri(source)
    engine.add_triple(finding_uri, str(BW_SUPPORTED_BY), URIRef(source_uri))
    if rating is not None:
        engine.add_triple(source_uri, str(BW_RELIABILITY), RELIABILITY_IRI[rating])


def test_below_threshold_best_support_qualifies() -> None:
    engine = RdflibIndexer()
    _add_support(engine, "finding/f1", "source/s1", "baja")
    items = low_reliability_findings(engine, (_finding_identity("finding/f1", "f-1"),), "media")
    assert [(f.id, f.best_reliability, f.file) for f in items] == [("f-1", "baja", _TOPIC)]


def test_best_rated_support_wins_across_sources() -> None:
    engine = RdflibIndexer()
    _add_support(engine, "finding/f1", "source/low", "baja")
    _add_support(engine, "finding/f1", "source/high", "alta")
    identities = (_finding_identity("finding/f1", "f-1"),)
    assert low_reliability_findings(engine, identities, "media") == ()


def test_unrated_support_ranks_below_every_threshold() -> None:
    engine = RdflibIndexer()
    _add_support(engine, "finding/f1", "source/s1", None)
    items = low_reliability_findings(engine, (_finding_identity("finding/f1", "f-1"),), "baja")
    assert [(f.id, f.best_reliability) for f in items] == [("f-1", None)]


def test_finding_without_sources_never_qualifies() -> None:
    # Membership requires ≥ 1 source (data-model § 2.4): an unsourced finding is
    # the anchor-gap rule's concern, not a reliability fact.
    engine = RdflibIndexer()
    _add_open_finding(engine, "finding/f1", "claim")
    assert low_reliability_findings(engine, (_finding_identity("finding/f1", "f-1"),), "alta") == ()


def test_low_reliability_sorted_by_file_then_id() -> None:
    engine = RdflibIndexer()
    _add_support(engine, "finding/f1", "source/s1", "baja")
    _add_support(engine, "finding/f2", "source/s2", "baja")
    identities = (
        _finding_identity("finding/f2", "a-second", "bible/research/zz.md"),
        _finding_identity("finding/f1", "b-first", "bible/research/aa.md"),
    )
    items = low_reliability_findings(engine, identities, "media")
    assert [(f.file, f.id) for f in items] == [
        ("bible/research/aa.md", "b-first"),
        ("bible/research/zz.md", "a-second"),
    ]


# --- anchor_gaps ----------------------------------------------------------------


def _anchor_identity(
    suffix: str = "anchor/a1", promotes: str = "f-1", constrains: str | None = "Ana"
) -> AnchorIdentity:
    return AnchorIdentity(
        promotes_id=promotes, constrains=constrains, relpath=_TOPIC, uri=graph_uri(suffix)
    )


def test_anchor_with_all_problems_yields_one_aggregated_row() -> None:
    # Missing finding + dropped target: every fired predicate lands in ONE row,
    # problems sorted (data-model § 2.3 — no duplicate rows per rule).
    engine = research_graph(AnchorSpec(constrains=None, finding_present=False))
    gaps = anchor_gaps(engine, (_anchor_identity(constrains=None),), "media", URI_BASE)
    assert [(g.promotes, g.constrains, g.problems) for g in gaps] == [
        ("f-1", None, ("missing_finding", "missing_target"))
    ]


def test_unsourced_anchor_gap() -> None:
    engine = research_graph()
    target = add_present_entity(engine, "characters/ana")
    add_anchor(engine, AnchorSpec(constrains=target, sources=()))
    gaps = anchor_gaps(engine, (_anchor_identity(),), "media", URI_BASE)
    assert gaps[0].problems == ("unsourced",)


def test_under_reliable_and_unrated_are_distinct_problems() -> None:
    engine = research_graph()
    target = add_present_entity(engine, "characters/ana")
    add_anchor(engine, AnchorSpec(constrains=target, sources=(SourceSpec(reliability="baja"),)))
    gaps = anchor_gaps(engine, (_anchor_identity(),), "media", URI_BASE)
    assert gaps[0].problems == ("under_reliable",)

    unrated = tuple(f for f in CORE_FACETS if f != "reliability")
    engine2 = research_graph()
    target2 = add_present_entity(engine2, "characters/ana")
    add_anchor(
        engine2,
        AnchorSpec(constrains=target2, sources=(SourceSpec(facets=unrated, reliability=None),)),
    )
    gaps2 = anchor_gaps(engine2, (_anchor_identity(),), "media", URI_BASE)
    assert gaps2[0].problems == ("unrated",)


def test_well_formed_anchor_is_not_a_gap() -> None:
    engine = research_graph()
    target = add_present_entity(engine, "characters/ana")
    add_anchor(engine, AnchorSpec(constrains=target, sources=(SourceSpec(reliability="alta"),)))
    assert anchor_gaps(engine, (_anchor_identity(),), "media", URI_BASE) == ()


def test_anchor_gaps_sorted_by_file_promotes_constrains() -> None:
    engine = research_graph(
        AnchorSpec(suffix="anchor/a1", finding_suffix="finding/f1", constrains=None),
        AnchorSpec(suffix="anchor/a2", finding_suffix="finding/f2", constrains=None),
    )
    identities = tuple(
        AnchorIdentity(promotes_id=promotes, constrains=None, relpath=_TOPIC, uri=graph_uri(uri))
        for promotes, uri in (("zz", "anchor/a1"), ("aa", "anchor/a2"))
    )
    gaps = anchor_gaps(engine, identities, "media", URI_BASE)
    assert [g.promotes for g in gaps] == ["aa", "zz"]


# --- validation_summary ---------------------------------------------------------


def test_validation_summary_counts_and_ran(tmp_path: Path) -> None:
    root = write_project(tmp_path / "novel")
    context = load_context(root)
    engine = RdflibIndexer()  # empty graph: the built-ins run and stay silent
    summary = validation_summary(root, context.manifest, engine)
    assert summary.counts == {"error": 0, "warning": 0, "info": 0}  # zero-filled
    assert summary.ran == tuple(sorted(summary.ran))
    assert "factual_anchor" in summary.ran


def test_validation_summary_counts_real_violations(tmp_path: Path) -> None:
    root = write_project(tmp_path / "novel")
    context = load_context(root)
    engine = research_graph(AnchorSpec(constrains=None, sources=()))  # R1 + R4 warnings
    summary = validation_summary(root, context.manifest, engine)
    assert summary.counts["warning"] > 0
    assert summary.counts["error"] == 0
