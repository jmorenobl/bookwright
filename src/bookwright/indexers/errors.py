"""Exception hierarchy for the indexer (graph-engine) seam.

The ``.to_json()`` shapes mirror ``bookwright.golem.errors`` /
``bookwright.core.errors`` so a downstream ``--json`` command that surfaces one
of these stays Principle-IX compliant (data-model § 6).
"""

from __future__ import annotations

from typing import Any


class IndexerError(Exception):
    """Base for every failure mode the ``bookwright.indexers`` package owns."""


class UnknownIndexerError(IndexerError):
    """The manifest names an engine that is not in ``INDEXER_REGISTRY`` (FR-007).

    Carries the offending name and the sorted set of registered engines so the
    error names both the unknown engine and the available ones.
    """

    code = "unknown_indexer"

    def __init__(self, name: str, available: list[str]) -> None:
        self.name = name
        self.available = available
        message = f"unknown indexer {name!r}; available: {', '.join(available)}"
        super().__init__(message)
        self.message = message

    def to_json(self) -> dict[str, Any]:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "details": {"name": self.name, "available": self.available},
        }


class GraphNotBuiltError(IndexerError):
    """``graph query`` ran with no ``bible/graph.ttl`` on disk (FR-016)."""

    code = "graph_not_built"

    def __init__(self, path: str) -> None:
        self.path = path
        message = f"no graph at {path}; run `bookwright graph build` first"
        super().__init__(message)
        self.message = message

    def to_json(self) -> dict[str, Any]:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "details": {"path": self.path},
        }


class InvalidQueryError(IndexerError):
    """A malformed SPARQL string was handed to ``query`` / ``construct`` (FR-016).

    No partial rows are yielded before this is raised.
    """

    code = "invalid_query"

    def __init__(self, reason: str) -> None:
        self.reason = reason
        message = f"invalid SPARQL query: {reason}"
        super().__init__(message)
        self.message = message

    def to_json(self) -> dict[str, Any]:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "details": {"reason": self.reason},
        }
