"""The ``graph build`` report models (data-model § 5).

``BuildReport`` and its three soft-warning collections are frozen Pydantic
models. ``skipped`` drives the exit code (≥ 1 skip → exit 4); ``unknown_keys``
and ``unresolved_participants`` are soft warnings that never change it.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

EXIT_OK = 0
EXIT_SKIPPED = 4


class SkippedFile(BaseModel):
    """A source file skipped because its frontmatter was unusable (FR-013)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    reason: str


class UnknownKey(BaseModel):
    """A frontmatter key not recognised for its concept — recorded, not fatal."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    key: str


class UnresolvedParticipant(BaseModel):
    """A ``participants:`` reference matching no built character (FR-019).

    The owning event/relationship is still constructed; only that participation
    edge is omitted.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    entity: str
    name: str


class BuildReport(BaseModel):
    """The full outcome of a ``graph build`` (data-model § 5)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    files_processed: int
    entities: int
    triples: int
    graph_path: str
    skipped: tuple[SkippedFile, ...] = ()
    unknown_keys: tuple[UnknownKey, ...] = ()
    unresolved_participants: tuple[UnresolvedParticipant, ...] = ()

    @property
    def exit_code(self) -> int:
        """Exit 4 when any file was skipped, else exit 0 (R7)."""
        return EXIT_SKIPPED if self.skipped else EXIT_OK

    def to_json(self) -> dict[str, Any]:
        """The contract success envelope (cli-graph.md): ``status:"ok"`` + metrics."""
        return {
            "status": "ok",
            "files_processed": self.files_processed,
            "entities": self.entities,
            "triples": self.triples,
            "skipped": [s.model_dump() for s in self.skipped],
            "unknown_keys": [u.model_dump() for u in self.unknown_keys],
            "unresolved_participants": [u.model_dump() for u in self.unresolved_participants],
            "graph_path": self.graph_path,
        }
