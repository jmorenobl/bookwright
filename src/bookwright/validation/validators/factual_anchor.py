"""``factual_anchor`` — structural + chronological audit of research anchors (§ 20.6).

The fifth built-in validator. A pure graph consumer (FR-003): it reads the anchor
sub-graph through :mod:`bookwright.validation.anchor_queries` and the manifest
through the :class:`ValidationContext`, and emits

* **warnings** for structural defects — an unsourced anchor (R1/FR-006), a source
  missing a mandatory provenance facet (R2/FR-007), under-reliable support
  (R3/FR-008), and a missing promoted finding or constrained entity (R4/FR-009);
* an **error** for a hard anachronism between an anchor's time-span and the
  interval of the event (or timeline) it constrains (R5/FR-010), decided by the
  shared :func:`~bookwright.validation.queries.intervals_disjoint` predicate so the
  contradiction logic is never forked from ``temporal`` (FR-011).

It is inert — returns ``[]`` immediately — when ``[research].enabled`` is false
(FR-015) or the graph carries no anchor (FR-016), so it costs nothing on a
non-research project. No rdflib here: all SPARQL lives in the projection modules.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar, Literal

from bookwright.golem.namespaces import (
    BW_CONSTRAINS,
    BW_PROMOTES,
    BW_SUPPORTED_BY,
    RELIABILITY_IRI,
    timeline_uri,
)
from bookwright.indexers import Indexer
from bookwright.validation.anchor_queries import (
    FACETS,
    AnchorRecord,
    SourceRecord,
    entity_present,
    load_anchors,
    load_sources_by_anchor,
)
from bookwright.validation.base import Severity, ValidationContext, Violation
from bookwright.validation.queries import (
    EventInterval,
    intervals_disjoint,
    load_intervals,
    resolve_source,
    timeline_bounds,
)

# The reliability scale, lowest → highest. The rating NAMES are the single
# vocabulary source (``RELIABILITY_IRI`` keys); only the domain ordering
# (``baja < media < alta``) lives here. The membership guard below trips if the
# vocabulary ever gains or renames a rating, so the scale can never silently drift.
# Public alongside the extracted predicates (020 research D3): ``status``
# aggregation ranks reliabilities on this same scale, never a re-spelled copy.
RELIABILITY_ORDER: tuple[str, ...] = ("baja", "media", "alta")
RELIABILITY_RANK: dict[str, int] = {name: rank for rank, name in enumerate(RELIABILITY_ORDER)}
assert set(RELIABILITY_RANK) == set(RELIABILITY_IRI), (
    "reliability scale drifted from RELIABILITY_IRI"
)


# --- Pure rule predicates (020 research D3) ----------------------------------
#
# The R1/R3 *decisions*, extracted so `status` aggregation reuses the exact
# detection logic (020 FR-005) with zero forks. The validator's methods call
# these and keep owning message construction and `Violation` assembly; R4's
# presence decision is already the public `anchor_queries.entity_present`.


def anchor_unsourced(sources: Sequence[SourceRecord], finding_present: bool) -> bool:
    """R1 (FR-006): the anchor promotes a present finding with zero sources.

    A missing finding suppresses R1 — that defect is R4's to report once.
    """
    return finding_present and not sources


def anchor_under_reliable(
    sources: Sequence[SourceRecord], minimum: str
) -> Literal["under_reliable", "unrated"] | None:
    """R3 (FR-008): how the anchor's best support compares to ``minimum``.

    ``None`` when satisfied (or when unsourced — R1's concern, no double-label);
    ``"under_reliable"`` when the best *rated* support ranks below ``minimum``;
    ``"unrated"`` when sources exist but none carries a rating at all — which
    sits below every threshold without being literally "below" any rating.
    """
    if not sources:
        return None
    rated = [RELIABILITY_RANK[s.reliability] for s in sources if s.reliability is not None]
    if not rated:
        return "unrated"
    return None if max(rated) >= RELIABILITY_RANK[minimum] else "under_reliable"


def _label(uri: str) -> str:
    """A short, readable name from a URI (its final path segment)."""
    return uri.rstrip("/").rsplit("/", 1)[-1]


def _range(interval: EventInterval) -> str:
    """A human ``begin-end`` year range, an open bound shown as ``?``."""
    begin = interval.begin if interval.begin is not None else "?"
    end = interval.end if interval.end is not None else "?"
    return f"{begin}-{end}"


@dataclass(frozen=True)
class _IntervalView:
    """The run-wide interval data the anachronism rule needs (loaded once).

    ``events`` maps every ``G5_Narrative_Event`` URI to its interval; ``timeline``
    is the overall bounds for a timeline-targeting anchor (``None`` when no anchor
    carries a span, so the data was never loaded).
    """

    events: dict[str, EventInterval]
    timeline: EventInterval | None


class FactualAnchor:
    """Audits each research anchor's structural integrity and chronology."""

    name: ClassVar[str] = "factual_anchor"
    severity_default: ClassVar[Severity] = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        if project.manifest.research.enabled is False:
            return []  # FR-015: the research system is turned off
        anchors = load_anchors(indexer)
        if not anchors:
            return []  # FR-016: nothing to audit on a non-research project
        sources_by_anchor = load_sources_by_anchor(indexer)
        # Interval data is only loaded when at least one anchor carries a time-span —
        # a non-temporal research project pays nothing for the anachronism rule.
        spanned = any(a.span.begin is not None or a.span.end is not None for a in anchors)
        events = load_intervals(indexer) if spanned else {}
        intervals = _IntervalView(
            events=events,
            timeline=timeline_bounds(events) if spanned else None,
        )
        out: list[Violation] = []
        for anchor in anchors:  # already sorted by URI (deterministic, FR-003)
            sources = sources_by_anchor.get(anchor.uri, [])
            out.extend(self._audit(anchor, sources, intervals, project, indexer))
        return out

    def _audit(
        self,
        anchor: AnchorRecord,
        sources: list[SourceRecord],
        intervals: _IntervalView,
        project: ValidationContext,
        indexer: Indexer,
    ) -> list[Violation]:
        """Run every rule against one anchor, collecting its violations in order."""
        finding_present = entity_present(indexer, anchor.promotes, project.uri_base)
        out: list[Violation] = []
        out.extend(self._unsourced(anchor, sources, finding_present, indexer))
        out.extend(self._incomplete(anchor, sources, project, indexer))
        out.extend(self._under_reliable(anchor, sources, project, indexer))
        out.extend(self._missing_entity(anchor, finding_present, project, indexer))
        out.extend(self._anachronism(anchor, intervals, project, indexer))
        return out

    def _violation(
        self, anchor: AnchorRecord, indexer: Indexer, message: str, triple: tuple[str, str, str]
    ) -> Violation:
        """A ``warning`` carrying the anchor's locator (``None`` today) + one edge."""
        return Violation(
            validator=self.name,
            severity=Severity.warning,
            message=message,
            source=resolve_source(indexer, anchor.uri),
            triples=(triple,),
        )

    # --- R1 unsourced (FR-006) ----------------------------------------------

    def _unsourced(
        self,
        anchor: AnchorRecord,
        sources: list[SourceRecord],
        finding_present: bool,
        indexer: Indexer,
    ) -> list[Violation]:
        # Suppressed when the finding is absent — R4 reports that once (no double-label).
        if not anchor_unsourced(sources, finding_present):
            return []
        message = f"anchor '{_label(anchor.uri)}' promotes a finding with no supporting source"
        triple = (anchor.uri, str(BW_PROMOTES), anchor.promotes)
        return [self._violation(anchor, indexer, message, triple)]

    # --- R2 provenance-incomplete (FR-007) ----------------------------------

    def _incomplete(
        self,
        anchor: AnchorRecord,
        sources: list[SourceRecord],
        project: ValidationContext,
        indexer: Indexer,
    ) -> list[Violation]:
        book_language = project.manifest.book.language
        out: list[Violation] = []
        for source in sources:
            # The implicated edge is the real finding→source link that locates the
            # source; a missing facet has no object, so it is never a fabricated triple.
            located = (anchor.promotes, str(BW_SUPPORTED_BY), source.uri)
            for facet in FACETS:
                if str(facet.predicate) in source.present_predicates:
                    continue
                # ``translation`` is mandatory only for a foreign-language source; if
                # the language itself is unknown it is already flagged, so skip here.
                if facet.foreign_only and (
                    source.original_language is None or source.original_language == book_language
                ):
                    continue
                message = (
                    f"source '{_label(source.uri)}' backing anchor '{_label(anchor.uri)}' "
                    f"is missing its {facet.label}"
                )
                out.append(self._violation(anchor, indexer, message, located))
        return out

    # --- R3 under-reliable (FR-008) -----------------------------------------

    def _under_reliable(
        self,
        anchor: AnchorRecord,
        sources: list[SourceRecord],
        project: ValidationContext,
        indexer: Indexer,
    ) -> list[Violation]:
        minimum = project.manifest.research.min_reliability_for_anchor
        verdict = anchor_under_reliable(sources, minimum)
        if verdict is None:  # satisfied, or unsourced (R1's concern, no double-label)
            return []
        if verdict == "under_reliable":  # a rating is present, it is just too low
            message = (
                f"anchor '{_label(anchor.uri)}' is backed only by sources below the "
                f"minimum reliability '{minimum}'"
            )
        else:  # sources exist but none carries a rating at all — not "below", unrated
            message = (
                f"anchor '{_label(anchor.uri)}' is backed by sources but none carries a "
                f"reliability rating (minimum required: '{minimum}')"
            )
        triple = (anchor.uri, str(BW_PROMOTES), anchor.promotes)
        return [self._violation(anchor, indexer, message, triple)]

    # --- R4 missing entity (FR-009) -----------------------------------------

    def _missing_entity(
        self,
        anchor: AnchorRecord,
        finding_present: bool,
        project: ValidationContext,
        indexer: Indexer,
    ) -> list[Violation]:
        out: list[Violation] = []
        if not finding_present:
            message = f"anchor '{_label(anchor.uri)}' promotes a finding not present in the graph"
            triple = (anchor.uri, str(BW_PROMOTES), anchor.promotes)
            out.append(self._violation(anchor, indexer, message, triple))
        target = anchor.constrains
        target_present = target is not None and entity_present(indexer, target, project.uri_base)
        if not target_present:
            message = (
                f"anchor '{_label(anchor.uri)}' constrains a narrative entity "
                "that is not present in the graph"
            )
            # The dropped-link case has no constrains triple → cite the promotes edge.
            triple = (
                (anchor.uri, str(BW_CONSTRAINS), target)
                if target is not None
                else (anchor.uri, str(BW_PROMOTES), anchor.promotes)
            )
            out.append(self._violation(anchor, indexer, message, triple))
        return out

    # --- R5 anachronism (FR-010/FR-012) -------------------------------------

    def _anachronism(
        self,
        anchor: AnchorRecord,
        intervals: _IntervalView,
        project: ValidationContext,
        indexer: Indexer,
    ) -> list[Violation]:
        span = anchor.span
        if span.begin is None and span.end is None:
            return []  # no time-span → nothing to compare against
        target = anchor.constrains
        if target is None:
            return []  # dropped link — already R4's concern, no interval to compare
        target_interval = self._target_interval(target, intervals, project.uri_base)
        if target_interval is None:
            return []  # non-temporal / non-event target → no comparable interval (FR-012)
        if not intervals_disjoint(span, target_interval):
            return []
        message = (
            f"anchor '{_label(anchor.uri)}' ({_range(span)}) constrains "
            f"'{_label(target)}' ({_range(target_interval)}), but their year ranges "
            "are disjoint (anachronism)"
        )
        return [
            Violation(
                validator=self.name,
                severity=Severity.error,
                message=message,
                source=resolve_source(indexer, anchor.uri),
                triples=((anchor.uri, str(BW_CONSTRAINS), target),),
            )
        ]

    def _target_interval(
        self, target: str, intervals: _IntervalView, uri_base: str
    ) -> EventInterval | None:
        """The interval to compare the span against: timeline bounds, an event's
        interval, or ``None`` for a non-temporal / non-event target (D3)."""
        if target == str(timeline_uri(uri_base)):
            return intervals.timeline
        return intervals.events.get(target)
