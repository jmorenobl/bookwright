"""``RdflibIndexer`` — the v0 default engine (wraps :class:`rdflib.Graph`).

Owns Turtle serialization and prefix binding so FR-015 (short prefixes) holds
regardless of which engine the manifest selects (R5). The build command feeds
``entity.to_triples()`` through :meth:`add_triple`; ``graph query`` runs SPARQL
through :meth:`query`.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from rdflib import Graph
from rdflib.query import ResultRow
from rdflib.term import Literal, URIRef

from bookwright.golem.namespaces import bind_prefixes

from .errors import GraphLoadError, InvalidQueryError


class RdflibIndexer:
    """An :class:`~bookwright.indexers.base.Indexer` backed by ``rdflib``."""

    def __init__(self, graph: Graph | None = None) -> None:
        self._graph = graph if graph is not None else Graph()
        bind_prefixes(self._graph)

    # --- ingestion ----------------------------------------------------------

    def add_triple(
        self,
        s: URIRef | str,
        p: URIRef | str,
        o: URIRef | Literal | str | int | float,
    ) -> None:
        """Add one triple. IRI-like ``str`` subjects/predicates coerce to ``URIRef``;
        objects that are already rdflib terms pass through, scalars become literals."""
        subject = s if isinstance(s, URIRef) else URIRef(s)
        predicate = p if isinstance(p, URIRef) else URIRef(p)
        if isinstance(o, (URIRef, Literal)):
            obj: URIRef | Literal = o
        else:
            obj = Literal(o)
        self._graph.add((subject, predicate, obj))

    # --- persistence --------------------------------------------------------

    def load(self, ttl_path: Path) -> None:
        """Parse the Turtle at ``ttl_path`` into the engine's graph.

        A malformed file raises :class:`GraphLoadError` (a clean envelope) rather
        than letting an rdflib parse error escape as a raw traceback.
        """
        try:
            self._graph.parse(str(ttl_path), format="turtle")
        except Exception as exc:  # rdflib raises a variety of parse errors
            raise GraphLoadError(str(ttl_path), str(exc)) from exc

    def save(self, ttl_path: Path) -> None:
        """Serialize the graph to Turtle (short prefixes), creating parent dirs."""
        ttl_path.parent.mkdir(parents=True, exist_ok=True)
        self._graph.serialize(destination=str(ttl_path), format="turtle")

    # --- querying -----------------------------------------------------------

    def query(self, sparql: str) -> Iterable[dict[str, Any]]:
        """Run a SELECT/ASK; return one dict per row (projected var → ``str``).

        The result is fully materialized inside the ``try`` so a malformed query
        raises :class:`InvalidQueryError` with **no partial rows** yielded first
        (FR-016).
        """
        try:
            result = self._graph.query(sparql)
            rows: list[dict[str, Any]] = [
                {str(var): str(value) for var, value in row.asdict().items()}
                for row in result
                if isinstance(row, ResultRow)
            ]
        except InvalidQueryError:
            raise
        except Exception as exc:  # rdflib raises a variety of parse errors
            raise InvalidQueryError(str(exc)) from exc
        return rows

    def construct(self, sparql: str) -> RdflibIndexer:
        """Run a CONSTRUCT; return a fresh engine wrapping the resulting sub-graph."""
        try:
            result = self._graph.query(sparql)
            graph = result.graph
        except Exception as exc:  # rdflib raises a variety of parse errors
            raise InvalidQueryError(str(exc)) from exc
        if graph is None:  # pragma: no cover - defensive; CONSTRUCT always yields a graph
            graph = Graph()
        return RdflibIndexer(graph=graph)

    def count(self) -> int:
        """Return the number of triples currently held."""
        return len(self._graph)
