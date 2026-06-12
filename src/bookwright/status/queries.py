"""Graph aggregations for ``bookwright status`` (020 research D8).

Written like :mod:`bookwright.validation.queries` / ``anchor_queries``: every
traversal runs through the :class:`~bookwright.indexers.Indexer` protocol with
IRIs from :mod:`bookwright.golem.namespaces` — no rdflib import, no hardcoded
IRI strings. Graph projections are joined back to **authored identity** via the
iteration-020 :class:`~bookwright.io.research.FindingIdentity` /
:class:`~bookwright.io.research.AnchorIdentity` maps (research D2): minted URIs
are in-process join keys only and never reach a returned record. Every result
is sorted by its corpus-stable key here, at construction — the single ordering
site the model and rule table rely on (SC-002).

Anchor-gap detection reuses the ``factual_anchor`` extraction (research D3):
the same :func:`anchor_unsourced` / :func:`anchor_under_reliable` predicates
and the same ``RELIABILITY_RANK`` scale, with zero logic forks (FR-005).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bookwright.golem.namespaces import (
    BW_CLAIM,
    BW_OPEN,
    BW_RELIABILITY,
    BW_SUPPORTED_BY,
    RELIABILITY_IRI,
)
from bookwright.status.model import (
    AnchorGap,
    LowReliabilityFinding,
    OpenQuestion,
    ValidationSummary,
)
from bookwright.validation.anchor_queries import (
    entity_present,
    load_anchors,
    load_sources_by_anchor,
)
from bookwright.validation.base import Severity, ValidationContext
from bookwright.validation.registry import discover_validators, resolve_active
from bookwright.validation.runner import run_validators
from bookwright.validation.validators.factual_anchor import (
    RELIABILITY_RANK,
    anchor_under_reliable,
    anchor_unsourced,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bookwright.core.manifest import Manifest
    from bookwright.indexers import Indexer
    from bookwright.io.research import AnchorIdentity, FindingIdentity

__all__ = [
    "anchor_gaps",
    "low_reliability_findings",
    "open_questions",
    "validation_summary",
]

_CUSTOM_SUBPATH = (".bookwright", "validators")

# Reliability rating name ← its E55 individual IRI, inverted from the single
# vocabulary source (the same derivation ``anchor_queries`` uses, research D6).
_RELIABILITY_NAME: dict[str, str] = {str(iri): name for name, iri in RELIABILITY_IRI.items()}


def open_questions(
    indexer: Indexer, identities: tuple[FindingIdentity, ...]
) -> tuple[OpenQuestion, ...]:
    """Every open finding in the graph, as authored-identity items (FR-004).

    ``bw:open`` is emitted only when true, with an optional ``bw:claim`` — an
    open question may carry none. Sorted by ``(file, id)``.
    """
    rows = indexer.query(
        f"""
        SELECT ?finding ?claim WHERE {{
          ?finding <{BW_OPEN}> true .
          OPTIONAL {{ ?finding <{BW_CLAIM}> ?claim . }}
        }}
        """
    )
    by_uri = {identity.uri: identity for identity in identities}
    items = [
        OpenQuestion(id=identity.id, text=row.get("claim"), file=identity.relpath)
        for row in rows
        if (identity := by_uri.get(row["finding"])) is not None
    ]
    return tuple(sorted(items, key=lambda q: (q.file, q.id)))


def low_reliability_findings(
    indexer: Indexer, identities: tuple[FindingIdentity, ...], minimum: str
) -> tuple[LowReliabilityFinding, ...]:
    """Findings whose best support ranks below ``minimum`` (FR-006).

    Membership (data-model § 2.4): only findings with ≥ 1 source qualify; a
    finding none of whose sources carries a rating is "unrated", which sits
    below every threshold (``best_reliability=None``). The rank is the
    ``factual_anchor`` scale, never a re-spelled copy (research D3). Sorted by
    ``(file, id)``.
    """
    rows = indexer.query(
        f"""
        SELECT ?finding ?source ?reliability WHERE {{
          ?finding <{BW_SUPPORTED_BY}> ?source .
          OPTIONAL {{ ?source <{BW_RELIABILITY}> ?reliability . }}
        }}
        """
    )
    best_by_finding: dict[str, str | None] = {}
    for row in rows:
        finding = row["finding"]
        rating = _RELIABILITY_NAME.get(row.get("reliability", ""))
        best = best_by_finding.get(finding)
        if best is None or _rank(rating) > _rank(best):
            best_by_finding[finding] = rating
    by_uri = {identity.uri: identity for identity in identities}
    items = [
        LowReliabilityFinding(id=identity.id, best_reliability=best, file=identity.relpath)
        for uri, best in best_by_finding.items()
        if _rank(best) < RELIABILITY_RANK[minimum] and (identity := by_uri.get(uri)) is not None
    ]
    return tuple(sorted(items, key=lambda f: (f.file, f.id)))


def _rank(rating: str | None) -> int:
    """A rating's ordinal on the shared scale; unrated ranks below everything."""
    return -1 if rating is None else RELIABILITY_RANK[rating]


def anchor_gaps(
    indexer: Indexer,
    identities: tuple[AnchorIdentity, ...],
    minimum: str,
    uri_base: str,
) -> tuple[AnchorGap, ...]:
    """Anchors lacking sufficient support or a resolvable target (FR-005).

    One row per defective anchor with **all** its problems aggregated, each
    problem decided by the extracted ``factual_anchor`` predicates over the
    same ``anchor_queries`` projections the validator reads (research D3).
    Sorted by ``(file, promotes, constrains or "")``.
    """
    sources_by_anchor = load_sources_by_anchor(indexer)
    by_uri = {identity.uri: identity for identity in identities}
    items: list[AnchorGap] = []
    for record in load_anchors(indexer):
        identity = by_uri.get(record.uri)
        if identity is None:
            continue  # not from this corpus mapping — nothing authored to report
        sources = sources_by_anchor.get(record.uri, [])
        finding_present = entity_present(indexer, record.promotes, uri_base)
        problems: set[str] = set()
        if not finding_present:
            problems.add("missing_finding")
        if anchor_unsourced(sources, finding_present):
            problems.add("unsourced")
        verdict = anchor_under_reliable(sources, minimum)
        if verdict is not None:
            problems.add(verdict)
        target_present = record.constrains is not None and entity_present(
            indexer, record.constrains, uri_base
        )
        if not target_present:
            problems.add("missing_target")
        if problems:
            items.append(
                AnchorGap(
                    promotes=identity.promotes_id,
                    constrains=identity.constrains,
                    file=identity.relpath,
                    problems=tuple(sorted(problems)),
                )
            )
    return tuple(sorted(items, key=lambda gap: (gap.file, gap.promotes, gap.constrains or "")))


def validation_summary(root: Path, manifest: Manifest, indexer: Indexer) -> ValidationSummary:
    """Run the existing validation runner and summarize it (FR-007, research D8).

    Counts per severity (zero-filled, the ``ValidationReport._by_severity``
    shape) plus the runner's sorted ``ran`` list. Violation *messages* stay out:
    they embed minted-URI labels (research D2). Discovery/run errors never
    affect the counts — exactly as they never affect ``validate``'s gate.

    Raises :class:`~bookwright.validation.base.UnknownValidatorError` when the
    manifest names an undiscovered validator — a config fault the command maps
    to exit 2, as ``validate`` does.
    """
    builtins, customs, _load_errors = discover_validators(root.joinpath(*_CUSTOM_SUBPATH))
    active = resolve_active(builtins, customs, manifest.validators)
    violations, _run_errors, ran = run_validators(
        active, ValidationContext(root=root, manifest=manifest), indexer
    )
    counts = {level.value: 0 for level in Severity}
    for violation in violations:
        counts[violation.severity.value] += 1
    return ValidationSummary(counts=counts, ran=tuple(ran))
