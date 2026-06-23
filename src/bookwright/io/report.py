"""The ``graph build`` report models (data-model § 5).

``BuildReport`` and its three soft-warning collections are frozen Pydantic
models. ``skipped`` drives the exit code (≥ 1 skip → exit 4); ``unknown_keys``
and ``unresolved_references`` are soft warnings that never change it.
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


class UnresolvedReference(BaseModel):
    """A name reference matching no built entity (FR-019).

    Covers a ``participants:`` member that names no built character **or** a
    location's ``setting:`` that names no built setting. The owning entity is
    still constructed; only that single edge is omitted.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    entity: str
    name: str


class ResearchTargetWarning(BaseModel):
    """A research ``bears_on``/``constrains`` target that did not resolve (D12).

    The link triple was omitted and the build still succeeds (exit code unchanged) —
    existence/kind enforcement is the iteration-15 ``factual_anchor`` validator's job.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    field: str
    name: str


class UntypedVocabTerm(BaseModel):
    """An authored term that, under an active vocabulary, matched no term and so
    minted an untyped node (DEBT-016, iteration 047).

    Non-fatal: never changes the exit code (an absent ``crm:P2_has_type`` is
    descriptive metadata that breaks no downstream gate — design § 4.4). The
    valid-term enumeration is render-derived from ``vocabulary`` (``VocabularyIndex
    .terms``), **not** stored here (FR-002) — mirroring ``ResearchTargetWarning``,
    which stores ``{path, field, name}`` and renders "not in bible" as derived text.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    field: str
    term: str
    vocabulary: str


class BuildReport(BaseModel):
    """The full outcome of a ``graph build`` (data-model § 5)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    files_processed: int
    entities: int
    triples: int
    graph_path: str
    skipped: tuple[SkippedFile, ...] = ()
    unknown_keys: tuple[UnknownKey, ...] = ()
    unresolved_references: tuple[UnresolvedReference, ...] = ()
    # Unrecognized controlled-vocabulary terms (iteration 047, DEBT-016): a soft
    # channel, sibling of unknown_keys/unresolved_references. Never gates the build —
    # it is *not* referenced in ``exit_code`` (FR-004). Empty on a vocabulary-free
    # build so existing output stays byte-stable.
    untyped_vocab_terms: tuple[UntypedVocabTerm, ...] = ()
    # Optional research metrics (iteration 012). Absent/zero on a research-free build
    # so existing build/`--json` output is byte-stable (research D8). Research warnings
    # never change the exit code (D12).
    sources: int = 0
    findings: int = 0
    anchors: int = 0
    research_warnings: tuple[ResearchTargetWarning, ...] = ()

    @property
    def exit_code(self) -> int:
        """Exit 4 when any file was skipped, else exit 0 (R7).

        Research warnings (D12) are deliberately **not** part of the exit code.
        """
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
            "unresolved_references": [u.model_dump() for u in self.unresolved_references],
            "untyped_vocab_terms": [w.model_dump() for w in self.untyped_vocab_terms],
            "sources": self.sources,
            "findings": self.findings,
            "anchors": self.anchors,
            "research_warnings": [w.model_dump() for w in self.research_warnings],
            "graph_path": self.graph_path,
        }
