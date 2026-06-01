"""The ``Indexer`` protocol — the stable engine seam build/query depend on.

Both ``graph`` verbs depend only on this structural contract (design § 12.1),
never on a concrete engine (FR-005/008). A future engine conforms by shape
alone — ``Protocol`` over ABC keeps it decoupled (R4).
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from rdflib.term import Literal, URIRef

IndexTriple = tuple[
    URIRef | str,
    URIRef | str,
    URIRef | Literal | str | int | float,
]
"""One triple accepted by :meth:`Indexer.add_triple` (IRI-like ``str`` coerced)."""


@runtime_checkable
class Indexer(Protocol):
    """A pluggable graph engine (design § 12.1)."""

    def load(self, ttl_path: Path) -> None:
        """Parse a Turtle file into the engine's graph."""
        ...

    def save(self, ttl_path: Path) -> None:
        """Serialize to Turtle with short prefixes bound (FR-015); make parent dirs."""
        ...

    def add_triple(
        self,
        s: URIRef | str,
        p: URIRef | str,
        o: URIRef | Literal | str | int | float,
    ) -> None:
        """Add one triple; IRI-like ``str`` subjects/predicates coerce to ``URIRef``."""
        ...

    def query(self, sparql: str) -> Iterable[dict[str, Any]]:
        """Run a SELECT; yield one dict per row (var → ``str``). Raise on bad SPARQL."""
        ...

    def construct(self, sparql: str) -> Indexer:
        """Run CONSTRUCT; return a fresh engine over the resulting sub-graph."""
        ...

    def count(self) -> int:
        """Return the number of triples currently held."""
        ...
