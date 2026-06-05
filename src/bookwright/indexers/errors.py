"""Exception hierarchy for the indexer (graph-engine) seam.

Every concrete error inherits the canonical ``--json`` envelope from the shared
``BookwrightError`` base (Principle IX, data-model § 6); this module declares only
each error's ``code`` and ``details``.
"""

from __future__ import annotations

from bookwright.errors import BookwrightError


class IndexerError(BookwrightError):
    """Base for every failure mode the ``bookwright.indexers`` package owns.

    Abstract: declares no ``code`` and is never serialized directly.
    """


class UnknownIndexerError(IndexerError):
    """The manifest names an engine that is not in ``INDEXER_REGISTRY`` (FR-007).

    Carries the offending name and the sorted set of registered engines so the
    error names both the unknown engine and the available ones.
    """

    code = "unknown_indexer"

    def __init__(self, name: str, available: list[str]) -> None:
        self.name = name
        self.available = available
        super().__init__(
            f"unknown indexer {name!r}; available: {', '.join(available)}",
            {"name": name, "available": available},
        )


class GraphNotBuiltError(IndexerError):
    """``graph query`` ran with no ``bible/graph.ttl`` on disk (FR-016)."""

    code = "graph_not_built"

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(
            f"no graph at {path}; run `bookwright graph build` first",
            {"path": path},
        )


class GraphLoadError(IndexerError):
    """``bible/graph.ttl`` exists but the engine could not parse it (FR-016).

    Distinct from :class:`GraphNotBuiltError` (no file at all): the file is there
    but malformed — e.g. a hand-edit broke the Turtle. Surfaced as a clean error
    envelope, never a raw rdflib traceback.
    """

    code = "graph_load_failed"

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(
            f"could not parse graph at {path}: {reason}",
            {"path": path, "reason": reason},
        )


class InvalidQueryError(IndexerError):
    """A malformed SPARQL string was handed to ``query`` (FR-016).

    No partial rows are yielded before this is raised.
    """

    code = "invalid_query"

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"invalid SPARQL query: {reason}", {"reason": reason})
