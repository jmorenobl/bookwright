"""The derived-state model for ``bookwright status`` (020 data-model § 2).

Frozen, in-memory records aggregating what the corpus + graph already say:
:class:`StatusState` is the **only** input to the rule table and the source of
the report's ``state`` object. Determinism rules (research D2): no minted URIs,
no timestamps, no environment data anywhere in a serialized shape — items carry
authored ids, file relpaths, and claim texts only.

Ordering is established **once, at construction** by the producer
(:mod:`bookwright.status.queries` sorts every item list by its corpus-stable
key: ``(file, id)`` for findings, ``(file, promotes, constrains or "")`` for
anchors); ``to_payload`` preserves stored order, so the serialized document is
byte-identical across runs on an unchanged corpus (SC-002) and the rule table's
prompts — which quote these same tuples — are equally stable.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from bookwright.validation.base import Severity


class _PayloadItem(Protocol):
    """Anything serializable as one entry of an item-list fact."""

    def to_payload(self) -> dict[str, Any]: ...


@dataclass(frozen=True)
class GraphFacts:
    """Headline graph metrics (data-model § 2.1).

    ``available`` is ``False`` only on the degraded path (research D5: build
    prerequisites absent); an empty-but-present bible builds normally and shows
    ``available=True, entities=0``.
    """

    available: bool
    entities: int
    triples: int

    def to_payload(self) -> dict[str, Any]:
        return {"available": self.available, "entities": self.entities, "triples": self.triples}


@dataclass(frozen=True)
class OpenQuestion:
    """One open research question — the bottom-up queue item (FR-004).

    ``id`` is the authored finding id; ``text`` its claim (an open question may
    have none); ``file`` the research file relpath.
    """

    id: str
    text: str | None
    file: str

    def to_payload(self) -> dict[str, Any]:
        return {"id": self.id, "text": self.text, "file": self.file}


@dataclass(frozen=True)
class AnchorGap:
    """One anchor lacking support or an unresolvable target (FR-005).

    ``promotes`` is the authored id of the promoted finding (the anchor's stable
    identity); ``constrains`` the authored target name, ``"timeline"``, or
    ``None`` for a dropped link; ``problems`` a sorted subset of ``{"unsourced",
    "under_reliable", "unrated", "missing_finding", "missing_target"}`` — one
    row per anchor with **all** its problems aggregated (data-model § 2.3).
    """

    promotes: str
    constrains: str | None
    file: str
    problems: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "promotes": self.promotes,
            "constrains": self.constrains,
            "file": self.file,
            "problems": list(self.problems),
        }


@dataclass(frozen=True)
class LowReliabilityFinding:
    """One finding whose best support ranks below the manifest threshold (FR-006).

    ``best_reliability`` is the best supporting rating name (``baja``/``media``/
    ``alta``) or ``None`` when no source carries a rating — which counts as
    below every threshold (data-model § 2.4).
    """

    id: str
    best_reliability: str | None
    file: str

    def to_payload(self) -> dict[str, Any]:
        return {"id": self.id, "best_reliability": self.best_reliability, "file": self.file}


@dataclass(frozen=True)
class ValidationSummary:
    """Counts per severity + the validators that ran (FR-007, data-model § 2.5).

    No violation items: their messages embed minted-URI labels (research D2/D8);
    counts are what FR-007 requires and what rule ④ consumes.
    """

    counts: dict[str, int]
    ran: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        # Fixed key order error/warning/info, zero-filled, regardless of the
        # construction-time dict order (byte-identity, SC-002).
        return {
            "counts": {level.value: self.counts.get(level.value, 0) for level in Severity},
            "ran": list(self.ran),
        }


def _fact(items: Sequence[_PayloadItem]) -> dict[str, Any]:
    """One item-list fact: always both ``count`` and ``items`` (FR-011a)."""
    return {"count": len(items), "items": [item.to_payload() for item in items]}


@dataclass(frozen=True)
class StatusState:
    """The aggregate of all derived facts — the rule table's only input.

    ``focus_defined`` is predicate input only (rule ⑤): the focus *content* is
    the report's top-level ``focus`` key, never duplicated inside ``state``.
    """

    phase: str
    focus_defined: bool
    graph: GraphFacts
    open_questions: tuple[OpenQuestion, ...]
    unresolved_anchors: tuple[AnchorGap, ...]
    low_reliability_findings: tuple[LowReliabilityFinding, ...]
    validation: ValidationSummary

    def to_payload(self) -> dict[str, Any]:
        """The report's ``state`` object (contracts/cli-status.md key set)."""
        return {
            "phase": self.phase,
            "graph": self.graph.to_payload(),
            "open_questions": _fact(self.open_questions),
            "unresolved_anchors": _fact(self.unresolved_anchors),
            "low_reliability_findings": _fact(self.low_reliability_findings),
            "validation": self.validation.to_payload(),
        }
