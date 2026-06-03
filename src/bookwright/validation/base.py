"""Core finding types and the validator seam (data-model, contracts/validator-protocol.md).

In-memory only; the subsystem persists nothing (FR-020). Every type here is frozen
where it can be, so findings are hashable and dedupe is trivial (D8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Protocol, cast, runtime_checkable

from bookwright.indexers import Indexer

if TYPE_CHECKING:
    from bookwright.core.manifest import Manifest
    from bookwright.golem.base import SluggedEntity
    from bookwright.io.bible import MapResult

__all__ = [
    "Severity",
    "UnknownValidatorError",
    "ValidationContext",
    "Validator",
    "ValidatorError",
    "Violation",
]


class Severity(StrEnum):
    """A finding's level. String-valued (JSON-friendly, design § 13.1)."""

    error = "error"
    warning = "warning"
    info = "info"

    def at_least(self, threshold: Severity) -> bool:
        """Whether this severity meets ``threshold`` under ``error > warning > info``."""
        return _RANK[self] >= _RANK[threshold]


_RANK: dict[Severity, int] = {Severity.error: 2, Severity.warning: 1, Severity.info: 0}
"""Ordinal for the ``--severity`` threshold, the gate, and the total-order sort."""


@dataclass(frozen=True)
class Violation:
    """One finding produced by a validator (FR-002/003).

    ``frozen=True`` + tuple fields make it hashable so identical findings collapse
    to one in the runner (D8). ``source`` is a project-relative posix path, optionally
    ``:line``; ``None`` when no specific location applies (location-less).
    """

    validator: str
    severity: Severity
    message: str
    source: str | None = None
    triples: tuple[tuple[str, str, str], ...] = ()

    def source_file(self) -> str | None:
        """The path part of ``source`` (drops any ``:line`` suffix), or ``None``."""
        if self.source is None:
            return None
        head, _, tail = self.source.rpartition(":")
        return head if (head and tail.isdigit()) else self.source

    def source_line(self) -> int | None:
        """The 1-based line from ``source`` when present, else ``None``."""
        if self.source is None:
            return None
        _, sep, tail = self.source.rpartition(":")
        return int(tail) if (sep and tail.isdigit()) else None

    def to_json(self) -> dict[str, Any]:
        """Serialize to the contract shape (FR-002, SC-004); ``triples`` as lists."""
        return {
            "validator": self.validator,
            "severity": self.severity.value,
            "message": self.message,
            "source": self.source,
            "triples": [list(triple) for triple in self.triples],
        }


@dataclass(frozen=True)
class ValidatorError:
    """A validator that could not be loaded or that raised while running (FR-014).

    Surfaced in the report's ``errors[]``; never affects the gate. ``validator`` is
    the validator name, or the offending file path for ``phase="load"`` failures.
    """

    validator: str
    message: str
    phase: Literal["load", "run"]

    def to_json(self) -> dict[str, Any]:
        return {"validator": self.validator, "phase": self.phase, "message": self.message}


@runtime_checkable
class Validator(Protocol):
    """The stable seam between the runner and any validator (design § 13.1).

    A validator examines the project (``ValidationContext``) and the already-built
    graph (``indexer``, possibly empty) and returns a list of ``Violation`` — an
    empty list means "no problems" (FR-001). It MUST be deterministic (FR-019) and
    MUST NOT write to disk or mutate the graph (FR-020); it MAY raise — the runner
    isolates it (FR-014).
    """

    name: str
    severity_default: Severity

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]: ...


class UnknownValidatorError(Exception):
    """A configured ``[validators]`` name is absent from the discovered set (FR-007)."""

    code = "unknown_validator"

    def __init__(self, names: tuple[str, ...]) -> None:
        self.names = names
        joined = ", ".join(names)
        self.message = f"unknown validator(s): {joined}"
        super().__init__(self.message)

    def to_json(self) -> dict[str, Any]:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "details": {"names": list(self.names)},
        }


# Sentinel distinguishing "not yet computed" from a cached ``None`` result.
_UNSET = object()


@dataclass
class ValidationContext:
    """The ``project`` argument to every validator (data-model).

    Bundles the project root + manifest and exposes cached accessors so each source
    file is read once per run and shared across validators. Accessors memoize on
    first call.
    """

    root: Path
    manifest: Manifest

    _bible: Any = field(default=_UNSET, repr=False, compare=False)
    _character_names: Any = field(default=_UNSET, repr=False, compare=False)
    _setting_names: Any = field(default=_UNSET, repr=False, compare=False)
    _manuscript_files: Any = field(default=_UNSET, repr=False, compare=False)
    _constitution_text: Any = field(default=_UNSET, repr=False, compare=False)

    @property
    def uri_base(self) -> str:
        return self.manifest.bookwright.uri_base

    def bible(self) -> MapResult:
        """Map the project's bible to GOLEM entities (once per run)."""
        if self._bible is _UNSET:
            from bookwright.io.bible import map_bible  # noqa: PLC0415

            bible_dir = self.root / self.manifest.paths.bible
            self._bible = map_bible(self.root, bible_dir, self.uri_base)
        return cast("MapResult", self._bible)

    def _names_of(self, concept_cls: type[SluggedEntity]) -> tuple[tuple[str, str], ...]:
        """Sorted ``(name, bible_relpath)`` pairs for one bible concept class."""
        names = [
            (entity.name, mapped.relpath)
            for mapped in self.bible().mapped
            if isinstance((entity := mapped.entity), concept_cls)
        ]
        return tuple(sorted(names))

    def character_names(self) -> tuple[tuple[str, str], ...]:
        """Sorted ``(name, bible_relpath)`` for every bible Character."""
        if self._character_names is _UNSET:
            from bookwright.golem import Character  # noqa: PLC0415

            self._character_names = self._names_of(Character)
        return cast("tuple[tuple[str, str], ...]", self._character_names)

    def setting_names(self) -> tuple[tuple[str, str], ...]:
        """Sorted ``(name, bible_relpath)`` for every bible Setting."""
        if self._setting_names is _UNSET:
            from bookwright.golem import Setting  # noqa: PLC0415

            self._setting_names = self._names_of(Setting)
        return cast("tuple[tuple[str, str], ...]", self._setting_names)

    def manuscript_files(self) -> tuple[tuple[str, str], ...]:
        """Sorted ``(relpath, text)`` for every ``**/*.md`` under the manuscript dir.

        Unreadable files are skipped defensively (a validator never aborts on one
        bad file). Sorted by relpath for determinism (D8).
        """
        if self._manuscript_files is _UNSET:
            manuscript_dir = self.root / self.manifest.paths.manuscript
            collected: list[tuple[str, str]] = []
            if manuscript_dir.is_dir():
                for path in sorted(manuscript_dir.rglob("*.md")):
                    if not path.is_file():
                        continue
                    try:
                        text = path.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError):
                        continue
                    collected.append((path.relative_to(self.root).as_posix(), text))
            self._manuscript_files = tuple(sorted(collected))
        return cast("tuple[tuple[str, str], ...]", self._manuscript_files)

    def constitution_text(self) -> str | None:
        """The constitution file's text, or ``None`` when absent/unreadable."""
        if self._constitution_text is _UNSET:
            path = self.root / self.manifest.paths.constitution
            try:
                self._constitution_text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                self._constitution_text = None
        return cast("str | None", self._constitution_text)
