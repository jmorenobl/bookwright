"""``factual_anchor`` validator — structural audit + the drift-guard.

One hand-built graph per case (defense-in-depth: the validator is exercised against
graphs the iteration-12 reader could not emit — e.g. an incomplete source). Each
rule is pinned in isolation, plus the fully well-formed anchor → zero violations
(SC-001) and the ``Source.to_triples`` ↔ facet-tuple drift guard (D5).
"""

from __future__ import annotations

import datetime
from pathlib import Path

from bookwright.core.manifest import Manifest
from bookwright.golem.modules.provenance import Source
from bookwright.golem.namespaces import RELIABILITY_IRI, timeline_uri
from bookwright.indexers import RdflibIndexer
from bookwright.validation.anchor_queries import FACETS
from bookwright.validation.base import Severity, ValidationContext, Violation
from bookwright.validation.registry import discover_validators, resolve_active
from bookwright.validation.report import ScopeFilter, ValidationReport
from bookwright.validation.validators.factual_anchor import _RELIABILITY_RANK, FactualAnchor
from tests.validation.conftest import (
    CORE_FACETS,
    URI_BASE,
    AnchorSpec,
    SourceSpec,
    add_anchor,
    add_event,
    add_present_entity,
    load_context,
    research_context,
    research_graph,
    write_project,
)


def _ctx(root: Path) -> ValidationContext:
    """A research-enabled context (book language ``es``, threshold ``media``)."""
    return load_context(write_project(root))


def _run(ctx: ValidationContext, engine: RdflibIndexer) -> list[Violation]:
    return FactualAnchor().validate(ctx, engine)


def _well_formed(engine: RdflibIndexer) -> str:
    """Add a present narrative target and return its URI (a valid constrains)."""
    return add_present_entity(engine, "characters/ana")


# --- R1 unsourced -----------------------------------------------------------


def test_unsourced_anchor_warns(project_root: Path) -> None:
    engine = research_graph()
    target = _well_formed(engine)
    add_anchor(engine, AnchorSpec(constrains=target, sources=()))
    findings = _run(_ctx(project_root), engine)
    assert len(findings) == 1
    assert findings[0].severity == Severity.warning
    assert "no supporting source" in findings[0].message


# --- R2 provenance-incomplete ----------------------------------------------


def test_source_missing_facets_one_warning_each(project_root: Path) -> None:
    incomplete = tuple(f for f in CORE_FACETS if f not in {"author", "reference"})
    engine = research_graph()
    target = _well_formed(engine)
    add_anchor(
        engine,
        AnchorSpec(constrains=target, sources=(SourceSpec(facets=incomplete),)),
    )
    findings = _run(_ctx(project_root), engine)
    messages = [f.message for f in findings]
    assert sum("is missing its author" in m for m in messages) == 1
    assert sum("is missing its reference" in m for m in messages) == 1
    # exactly the two missing facets — no spurious extra (reliability is present, etc.)
    assert len([m for m in messages if "is missing its" in m]) == 2


def test_translation_required_only_for_foreign_source(project_root: Path) -> None:
    # Foreign-language source with every core facet but no translation → flagged.
    engine = research_graph()
    target = _well_formed(engine)
    add_anchor(
        engine,
        AnchorSpec(
            constrains=target,
            sources=(SourceSpec(facets=CORE_FACETS, original_language="en"),),
        ),
    )
    findings = _run(_ctx(project_root), engine)
    assert [f.message for f in findings if "translation" in f.message]


def test_translation_not_required_for_same_language_source(project_root: Path) -> None:
    engine = research_graph()
    target = _well_formed(engine)
    add_anchor(
        engine,
        AnchorSpec(
            constrains=target,
            sources=(SourceSpec(facets=CORE_FACETS, original_language="es"),),
        ),
    )
    assert _run(_ctx(project_root), engine) == []


def test_empty_source_flags_every_core_facet(project_root: Path) -> None:
    # A dangling supporting source with no facet triple at all → one warning per core
    # facet (translation is moot: the language is unknown, so it is not demanded).
    engine = research_graph()
    target = _well_formed(engine)
    add_anchor(engine, AnchorSpec(constrains=target, sources=(SourceSpec(facets=()),)))
    findings = _run(_ctx(project_root), engine)
    missing = [f for f in findings if "is missing its" in f.message]
    assert len(missing) == len(CORE_FACETS)


# --- R3 under-reliable ------------------------------------------------------


def test_mixed_reliability_judged_by_best(project_root: Path) -> None:
    engine = research_graph()
    target = _well_formed(engine)
    add_anchor(
        engine,
        AnchorSpec(
            constrains=target,
            sources=(
                SourceSpec(suffix="source/low", reliability="baja"),
                SourceSpec(suffix="source/high", reliability="alta"),
            ),
        ),
    )
    # best == alta ≥ media → no under-reliable warning, all facets present → silent.
    assert _run(_ctx(project_root), engine) == []


def test_unrated_source_flagged_once_by_r2_not_double_labelled(project_root: Path) -> None:
    # One complete alta source (so R3 stays silent) + one source missing reliability.
    incomplete = tuple(f for f in CORE_FACETS if f != "reliability")
    engine = research_graph()
    target = _well_formed(engine)
    add_anchor(
        engine,
        AnchorSpec(
            constrains=target,
            sources=(
                SourceSpec(suffix="source/ok", reliability="alta"),
                SourceSpec(suffix="source/unrated", facets=incomplete, reliability=None),
            ),
        ),
    )
    findings = _run(_ctx(project_root), engine)
    messages = [f.message for f in findings]
    # exactly one warning, about the missing reliability facet; no anchor-level R3.
    assert len(findings) == 1
    assert "is missing its reliability" in messages[0]
    assert not any("minimum reliability" in m for m in messages)


def test_rated_below_threshold_is_under_reliable(project_root: Path) -> None:
    # A source that IS rated, just below the threshold (baja < media).
    engine = research_graph()
    target = _well_formed(engine)
    add_anchor(
        engine,
        AnchorSpec(constrains=target, sources=(SourceSpec(reliability="baja"),)),
    )
    findings = _run(_ctx(project_root), engine)
    assert len(findings) == 1
    assert findings[0].severity == Severity.warning
    assert "below the minimum reliability" in findings[0].message
    assert "media" in findings[0].message


def test_all_unrated_sources_flag_anchor_under_reliable(project_root: Path) -> None:
    # Sources present but none carries a rating → R2 flags each source's missing
    # reliability facet (clarification 2), AND R3 flags the anchor once — different
    # subjects, not a double-label of the same thing. The R3 message says the
    # support is unrated, never the inexact "below the minimum reliability".
    incomplete = tuple(f for f in CORE_FACETS if f != "reliability")
    engine = research_graph()
    target = _well_formed(engine)
    add_anchor(
        engine,
        AnchorSpec(constrains=target, sources=(SourceSpec(facets=incomplete, reliability=None),)),
    )
    findings = _run(_ctx(project_root), engine)
    messages = [f.message for f in findings]
    assert sum("is missing its reliability" in m for m in messages) == 1  # R2 on the source
    assert sum("none carries a reliability rating" in m for m in messages) == 1  # R3 on the anchor
    assert not any("below the minimum reliability" in m for m in messages)


# --- R4 missing entity ------------------------------------------------------


def test_dropped_constrains_is_missing_entity(project_root: Path) -> None:
    engine = research_graph()
    add_anchor(engine, AnchorSpec(constrains=None, sources=(SourceSpec(),)))
    findings = _run(_ctx(project_root), engine)
    assert len(findings) == 1
    assert "not present in the graph" in findings[0].message


def test_dangling_constrains_is_missing_entity(project_root: Path) -> None:
    engine = research_graph()
    add_anchor(
        engine,
        AnchorSpec(constrains=f"{URI_BASE}characters/ghost", sources=(SourceSpec(),)),
    )
    findings = _run(_ctx(project_root), engine)
    assert len(findings) == 1
    assert "not present in the graph" in findings[0].message


def test_absent_finding_is_missing_entity_only_not_unsourced(project_root: Path) -> None:
    # Promoted finding absent from the graph → R4 only; R1 suppressed (no double-label).
    engine = research_graph()
    target = _well_formed(engine)
    add_anchor(engine, AnchorSpec(constrains=target, finding_present=False))
    findings = _run(_ctx(project_root), engine)
    assert len(findings) == 1
    assert "finding" in findings[0].message
    assert "no supporting source" not in findings[0].message


# --- Clean anchor (SC-001) --------------------------------------------------


def test_well_formed_anchor_is_silent(project_root: Path) -> None:
    engine = research_graph()
    target = _well_formed(engine)
    add_anchor(
        engine,
        AnchorSpec(constrains=target, sources=(SourceSpec(reliability="alta"),)),
    )
    assert _run(_ctx(project_root), engine) == []


# --- Drift guard: facet tuple ↔ Source.to_triples (D5) ----------------------


def test_facet_predicates_match_source_model() -> None:
    fully_populated = Source(
        uri_base=URI_BASE,
        name="Fuente",
        reference="ref",
        author="autor",
        original_language="en",
        type="primaria",
        reliability="alta",
        reliability_justification="porque sí",
        access_date=datetime.date(2020, 1, 1),
        original_quote="cita",
        translation="quote",
    )
    source_predicates = {str(p) for _, p, _ in fully_populated.to_triples()}
    facet_predicates = {str(f.predicate) for f in FACETS}
    assert facet_predicates == source_predicates


def test_reliability_scale_matches_vocabulary() -> None:
    # The rank's membership is single-sourced from the ontology vocabulary; if a
    # rating is added/renamed in RELIABILITY_IRI this fails and forces the scale to
    # follow (parity with the facet drift guard above, and -O-safe unlike the inline
    # module assert, which python -O strips).
    assert set(_RELIABILITY_RANK) == set(RELIABILITY_IRI)


# --- R5 anachronism ---------------------------------------------------------


def _errors(findings: list[Violation]) -> list[Violation]:
    return [f for f in findings if f.severity == Severity.error]


def _sourced(constrains: str, span: tuple[int | None, int | None]) -> AnchorSpec:
    """A structurally well-formed anchor (so only R5 can speak) with a span."""
    return AnchorSpec(constrains=constrains, span=span, sources=(SourceSpec(reliability="alta"),))


def test_disjoint_span_vs_event_is_an_error(project_root: Path) -> None:
    engine = research_graph()
    event = add_event(engine, "battle", begin=1950, end=1950)
    add_anchor(engine, _sourced(event, (1957, 1957)))
    errors = _errors(_run(_ctx(project_root), engine))
    assert len(errors) == 1
    assert "anachronism" in errors[0].message
    assert errors[0].triples  # carries the implicated constrains edge


def test_consistent_span_vs_event_no_error(project_root: Path) -> None:
    engine = research_graph()
    event = add_event(engine, "battle", begin=1950, end=1950)
    add_anchor(engine, _sourced(event, (1950, 1950)))
    assert _errors(_run(_ctx(project_root), engine)) == []


def test_non_temporal_target_no_error(project_root: Path) -> None:
    engine = research_graph()
    target = add_present_entity(engine, "characters/ana")
    add_anchor(engine, _sourced(target, (1957, 1957)))
    assert _errors(_run(_ctx(project_root), engine)) == []


def test_span_with_dropped_constrains_no_error(project_root: Path) -> None:
    # A spanned anchor whose constrains link was dropped has no target to compare →
    # no anachronism error (the dropped link is reported by R4 as a warning instead).
    engine = research_graph()
    add_anchor(
        engine,
        AnchorSpec(constrains=None, span=(1957, 1957), sources=(SourceSpec(reliability="alta"),)),
    )
    assert _errors(_run(_ctx(project_root), engine)) == []


def test_event_without_year_no_error(project_root: Path) -> None:
    engine = research_graph()
    event = add_event(engine, "vague", begin=None, end=None)
    add_anchor(engine, _sourced(event, (1957, 1957)))
    assert _errors(_run(_ctx(project_root), engine)) == []


def test_open_ended_span_compares_present_bound(project_root: Path) -> None:
    engine = research_graph()
    event = add_event(engine, "battle", begin=1950, end=1950)
    # span begins 1957 with no end → still provably after the event ends → error.
    add_anchor(engine, _sourced(event, (1957, None)))
    assert len(_errors(_run(_ctx(project_root), engine))) == 1


def test_timeline_target_uses_overall_bounds(project_root: Path) -> None:
    engine = research_graph()
    add_event(engine, "early", begin=1950, end=1955)
    add_event(engine, "late", begin=1958, end=1960)
    timeline = str(timeline_uri(URI_BASE))
    add_anchor(engine, _sourced(timeline, (1900, 1910)))  # before the whole timeline
    errors = _errors(_run(_ctx(project_root), engine))
    assert len(errors) == 1
    assert "anachronism" in errors[0].message


# --- discovery / selection / inert / scope ----------------------------------


def _active_names(root: Path) -> set[str]:
    builtins, customs, _e = discover_validators(root / ".bookwright" / "validators")
    block = Manifest.load(root / "manifest.toml").validators
    return {v.name for v in resolve_active(builtins, customs, block)}


def test_auto_discovered_and_active_by_default(project_root: Path) -> None:
    root = write_project(project_root)
    assert "factual_anchor" in _active_names(root)


def test_disabled_block_removes_it(project_root: Path) -> None:
    root = write_project(project_root, disabled=["factual_anchor"])
    assert "factual_anchor" not in _active_names(root)


def test_enabled_allow_list_includes_it(project_root: Path) -> None:
    root = write_project(project_root, enabled=["factual_anchor"])
    assert _active_names(root) == {"factual_anchor"}


def test_inert_when_research_disabled_even_with_anchors(project_root: Path) -> None:
    root = research_context(project_root, enabled=False)
    engine = research_graph()
    add_anchor(engine, AnchorSpec(constrains=None))  # a clearly malformed anchor
    assert FactualAnchor().validate(load_context(root), engine) == []


def test_zero_violations_when_no_anchors(project_root: Path) -> None:
    engine = research_graph()  # empty graph, no anchors
    assert _run(_ctx(project_root), engine) == []


def test_scope_drops_location_less_violations(project_root: Path) -> None:
    engine = research_graph()
    add_anchor(engine, AnchorSpec(constrains=None, sources=()))  # R1 + R4 warnings
    findings = _run(_ctx(project_root), engine)
    assert findings  # the unscoped run sees the defects
    assert all(f.source is None for f in findings)  # anchors are location-less (D7)

    report = ValidationReport(violations=tuple(findings), errors=(), ran=("factual_anchor",))
    scope = ScopeFilter(rel="bible/research", is_dir=True)
    # SC-005: a scoped report drops every location-less violation; unscoped keeps all.
    assert report.reported(scope=scope, severity=None) == []
    assert report.reported(scope=None, severity=None) == findings
    assert scope.matches(None) is False
