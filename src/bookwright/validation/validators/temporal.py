"""``temporal`` — timeline contradictions over the interval + relation graph (FR-015).

A pure graph consumer (research D12): it reads each event's begin/end years and the
five qualitative ``TR:*`` relations through :mod:`bookwright.validation.queries` and
emits one ``error`` ``Violation`` per contradiction — never consulting document order,
insensitive to the interval carrier-node shape. The four rules:

* **(a)** a ``follows`` / ``precedes`` cycle (mutually-before events),
* **(b)** a pair both strictly ordered *and* ``temporally-overlaps``,
* **(c)** containment conflicting with a strict order,
* **(d)** numeric begin/end contradicting a declared relation.
"""

from __future__ import annotations

from typing import ClassVar

from bookwright.golem.namespaces import TEMPORAL_RELATIONS
from bookwright.indexers import Indexer
from bookwright.validation.base import Severity, ValidationContext, Violation
from bookwright.validation.queries import (
    EventInterval,
    intervals_disjoint,
    load_intervals,
    load_relations,
    resolve_source,
)

_MIN_CYCLE = 2  # an SCC of ≥2 events is a follows/precedes cycle (rule a).

# Canonical relation name → its predicate string, derived from the single source
# of truth so this validator and the loader can never disagree on the key spelling.
_PRED: dict[str, str] = {rel.name: str(rel.predicate) for rel in TEMPORAL_RELATIONS}


def _label(uri: str) -> str:
    """A short, readable event name from its URI (the final path segment)."""
    return uri.rstrip("/").rsplit("/", 1)[-1]


class Temporal:
    """Detects the four FR-015 timeline contradictions in the graph."""

    name: ClassVar[str] = "temporal"
    severity_default: ClassVar[Severity] = Severity.error

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        intervals = load_intervals(indexer)
        relations = load_relations(indexer)

        # Normalize follows/precedes into a strict "x strictly before y" relation,
        # remembering which declared edge each came from for the implicated triples.
        before: set[tuple[str, str]] = set()
        before_triple: dict[tuple[str, str], tuple[str, str, str]] = {}
        for a, b in relations["precedes"]:  # a before b
            before.add((a, b))
            before_triple[(a, b)] = (a, _PRED["precedes"], b)
        for a, b in relations["follows"]:  # a after b → b before a
            before.add((b, a))
            before_triple[(b, a)] = (a, _PRED["follows"], b)

        out: list[Violation] = []
        out.extend(self._cycles(before, before_triple, indexer))
        out.extend(self._order_vs_overlap(before, relations, indexer))
        out.extend(self._containment_vs_order(before, relations, indexer))
        out.extend(self._numeric(relations, intervals, indexer))
        return out

    # --- rule (a): cycle in the strict-order graph --------------------------

    def _cycles(
        self,
        before: set[tuple[str, str]],
        before_triple: dict[tuple[str, str], tuple[str, str, str]],
        indexer: Indexer,
    ) -> list[Violation]:
        adjacency: dict[str, list[str]] = {}
        for x, y in before:
            adjacency.setdefault(x, []).append(y)
            adjacency.setdefault(y, [])
        out: list[Violation] = []
        for component in _strongly_connected(adjacency):
            if len(component) < _MIN_CYCLE:
                continue
            members = set(component)
            triples = tuple(
                sorted(before_triple[(x, y)] for (x, y) in before if x in members and y in members)
            )
            names = ", ".join(sorted(_label(uri) for uri in component))
            out.append(
                Violation(
                    validator=self.name,
                    severity=Severity.error,
                    message=(
                        f"temporal cycle: events {{{names}}} are each asserted to come "
                        "before another in the group (follows/precedes form a loop)"
                    ),
                    # No single subject spans the SCC → resolve from the lexicographically
                    # smallest event URI in the (already-sorted) component (FR-002).
                    source=resolve_source(indexer, component[0]),
                    triples=triples,
                )
            )
        return out

    # --- rule (b): a strictly ordered pair that also overlaps ---------------

    def _order_vs_overlap(
        self,
        before: set[tuple[str, str]],
        relations: dict[str, set[tuple[str, str]]],
        indexer: Indexer,
    ) -> list[Violation]:
        out: list[Violation] = []
        for a, b in _unordered_pairs(relations["overlaps"]):
            if (a, b) in before or (b, a) in before:
                out.append(
                    Violation(
                        validator=self.name,
                        severity=Severity.error,
                        message=(
                            f"'{_label(a)}' and '{_label(b)}' are asserted to overlap, "
                            "yet one is also strictly ordered before the other"
                        ),
                        # Resolve from the carried triple's subject `a`, mirroring rule (d).
                        source=resolve_source(indexer, a),
                        triples=((a, _PRED["overlaps"], b),),
                    )
                )
        return out

    # --- rule (c): containment conflicting with a strict order --------------

    def _containment_vs_order(
        self,
        before: set[tuple[str, str]],
        relations: dict[str, set[tuple[str, str]]],
        indexer: Indexer,
    ) -> list[Violation]:
        out: list[Violation] = []
        containments = [("includes", a, b) for a, b in relations["includes"]]
        containments += [("included_in", a, b) for a, b in relations["included_in"]]
        for key, a, b in sorted(containments):
            if (a, b) in before or (b, a) in before:
                out.append(
                    Violation(
                        validator=self.name,
                        severity=Severity.error,
                        message=(
                            f"'{_label(a)}' and '{_label(b)}' are in a containment relation "
                            f"({key}), which is incompatible with a strict before/after order"
                        ),
                        # Resolve from the carried triple's subject `a`, mirroring rule (d).
                        source=resolve_source(indexer, a),
                        triples=((a, _PRED[key], b),),
                    )
                )
        return out

    # --- rule (d): numeric begin/end contradicting a relation ---------------

    def _numeric(
        self,
        relations: dict[str, set[tuple[str, str]]],
        intervals: dict[str, EventInterval],
        indexer: Indexer,
    ) -> list[Violation]:
        out: list[Violation] = []

        def interval(uri: str) -> EventInterval:
            return intervals.get(uri, EventInterval(uri, None, None))

        def emit(a: str, key: str, b: str, why: str) -> None:
            out.append(
                Violation(
                    validator=self.name,
                    severity=Severity.error,
                    message=why,
                    source=resolve_source(indexer, a),
                    triples=((a, _PRED[key], b),),
                )
            )

        for a, b in sorted(relations["follows"]):  # a after b: a.begin must be >= b.end
            ia, ib = interval(a), interval(b)
            if ia.begin is not None and ib.end is not None and ia.begin < ib.end:
                emit(
                    a,
                    "follows",
                    b,
                    f"'{_label(a)}' (begins {ia.begin}) is asserted to follow "
                    f"'{_label(b)}' (ends {ib.end}), but starts before it ends",
                )
        for a, b in sorted(relations["precedes"]):  # a before b: a.end must be <= b.begin
            ia, ib = interval(a), interval(b)
            if ia.end is not None and ib.begin is not None and ia.end > ib.begin:
                emit(
                    a,
                    "precedes",
                    b,
                    f"'{_label(a)}' (ends {ia.end}) is asserted to precede "
                    f"'{_label(b)}' (begins {ib.begin}), but ends after it begins",
                )
        for a, b in _unordered_pairs(relations["overlaps"]):
            ia, ib = interval(a), interval(b)
            # The disjointness DECISION is the shared single source of truth (FR-011);
            # the two directional comparisons below only choose which message to emit
            # (formatting), never re-decide the contradiction.
            if not intervals_disjoint(ia, ib):
                continue
            if ia.end is not None and ib.begin is not None and ia.end < ib.begin:
                emit(
                    a,
                    "overlaps",
                    b,
                    f"'{_label(a)}' (ends {ia.end}) and '{_label(b)}' (begins {ib.begin}) "
                    "are asserted to overlap, but their year ranges are disjoint",
                )
            else:
                emit(
                    a,
                    "overlaps",
                    b,
                    f"'{_label(a)}' (begins {ia.begin}) and '{_label(b)}' (ends {ib.end}) "
                    "are asserted to overlap, but their year ranges are disjoint",
                )
        for key in ("includes", "included_in"):
            for a, b in sorted(relations[key]):
                container, contained = (a, b) if key == "includes" else (b, a)
                ic, ict = interval(container), interval(contained)
                if (ic.begin is not None and ict.begin is not None and ic.begin > ict.begin) or (
                    ic.end is not None and ict.end is not None and ic.end < ict.end
                ):
                    emit(
                        a,
                        key,
                        b,
                        f"'{_label(container)}' is asserted to contain "
                        f"'{_label(contained)}', but its year range does not enclose it",
                    )
        return out


def _unordered_pairs(pairs: set[tuple[str, str]]) -> list[tuple[str, str]]:
    """Collapse a symmetric relation to one canonical ``(min, max)`` pair each."""
    canonical = {tuple(sorted(pair)) for pair in pairs}
    return sorted(canonical)  # type: ignore[arg-type]


def _strongly_connected(adjacency: dict[str, list[str]]) -> list[list[str]]:
    """Tarjan's SCC over the directed ``adjacency`` graph (deterministic order)."""
    index_of: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    counter = 0
    result: list[list[str]] = []

    def strong(node: str) -> None:
        nonlocal counter
        index_of[node] = low[node] = counter
        counter += 1
        stack.append(node)
        on_stack.add(node)
        for nbr in sorted(adjacency.get(node, ())):
            if nbr not in index_of:
                strong(nbr)
                low[node] = min(low[node], low[nbr])
            elif nbr in on_stack:
                low[node] = min(low[node], index_of[nbr])
        if low[node] == index_of[node]:
            component: list[str] = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                component.append(w)
                if w == node:
                    break
            result.append(sorted(component))

    for vertex in sorted(adjacency):
        if vertex not in index_of:
            strong(vertex)
    return result
