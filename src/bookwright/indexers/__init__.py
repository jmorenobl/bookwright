"""Pluggable graph-engine seam: the ``Indexer`` protocol + a name→class registry.

Adding a future engine is one ``INDEXER_REGISTRY`` entry — never a change to
build/query command code (FR-008). ``GrafeoIndexer`` is intentionally **not**
registered (deferred to v0.3 — Principle X).
"""

from __future__ import annotations

from .base import Indexer, IndexTriple
from .errors import (
    GraphNotBuiltError,
    IndexerError,
    InvalidQueryError,
    UnknownIndexerError,
)
from .rdflib_indexer import RdflibIndexer

INDEXER_REGISTRY: dict[str, type[Indexer]] = {"rdflib": RdflibIndexer}
"""Engine name → concrete class. The manifest's ``[bookwright] indexer`` keys it."""


def resolve_indexer(name: str) -> type[Indexer]:
    """Return the engine class registered under ``name`` (FR-007).

    Raises :class:`UnknownIndexerError` — naming the unknown engine and listing
    the available ones — when ``name`` is not registered.
    """
    try:
        return INDEXER_REGISTRY[name]
    except KeyError as exc:
        raise UnknownIndexerError(name, available=sorted(INDEXER_REGISTRY)) from exc


__all__ = [
    "INDEXER_REGISTRY",
    "GraphNotBuiltError",
    "IndexTriple",
    "Indexer",
    "IndexerError",
    "InvalidQueryError",
    "RdflibIndexer",
    "UnknownIndexerError",
    "resolve_indexer",
]
