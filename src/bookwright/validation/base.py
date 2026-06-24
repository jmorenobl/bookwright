"""Core finding types and the validator seam (data-model, contracts/validator-protocol.md).

In-memory only; the subsystem persists nothing (FR-020). Every type here is frozen
where it can be, so findings are hashable and dedupe is trivial (D8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Protocol, cast, runtime_checkable

from bookwright.errors import BookwrightError
from bookwright.indexers import Indexer

if TYPE_CHECKING:
    from bookwright.core.manifest import Manifest
    from bookwright.golem.base import SluggedEntity
    from bookwright.io.bible import MapResult
    from bookwright.io.prose import ProseView
    from bookwright.io.research import AnchorIdentity

__all__ = [
    "NotEvaluated",
    "NotEvaluatedKind",
    "NotEvaluatedResult",
    "Severity",
    "UnknownValidatorError",
    "ValidationContext",
    "Validator",
    "ValidatorError",
    "Violation",
    "split_source",
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


class NotEvaluatedKind(StrEnum):
    """Why a validator consciously did not evaluate (iteration 044, design § 13.4).

    A small closed vocabulary mirroring :class:`Severity`. The wire value is the
    member name; carried on the not-evaluated signal and its recorded result.
    """

    missing_input = "missing_input"
    """Input-conditional: an input of THIS project was missing/malformed —
    actionable, per-project, transient. The default (FR-002)."""

    pending_capability = "pending_capability"
    """Permanent capability-gap: no deterministic run evaluates this; it awaits
    move 3 (§ 13.5) — not author-actionable, identical in every project."""


def split_source(source: str | None) -> tuple[str | None, int | None]:
    """Split a ``relpath[:line]`` provenance string into ``(path, line)``.

    The ``:line`` suffix is recognized only when a non-empty path precedes a
    digit-only tail; otherwise the whole string is the path and the line is ``None``.
    ``source=None`` yields ``(None, None)``. This is the single place the ``source``
    grammar is parsed — every consumer (``Violation`` accessors, the report scope
    filter, provenance resolution) routes through it so the parsing never forks.
    """
    if source is None:
        return None, None
    head, sep, tail = source.rpartition(":")
    if head and sep and tail.isdigit():
        return head, int(tail)
    return source, None


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
        return split_source(self.source)[0]

    def source_line(self) -> int | None:
        """The 1-based line from ``source`` when present, else ``None``."""
        return split_source(self.source)[1]

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


class NotEvaluated(Exception):
    """A validator's opt-in signal that it consciously did not evaluate (FR-001).

    Raised from inside ``validate`` when the validator has no input for ANY of its
    checks. It is **not** a ``BookwrightError`` (it carries no error envelope) and
    **not** a failure: the runner catches it BEFORE its generic handler and records a
    :class:`NotEvaluatedResult` in the ``not_evaluated`` channel, never in ``errors[]``
    (FR-005). A validator that never raises it is always **evaluated** (FR-014).

    The ``kind`` (default :attr:`NotEvaluatedKind.missing_input`) records whether the
    gap is about *this input* (actionable, transient) or about the *approach* (a
    permanent capability-gap); the validator is the only party that knows, so it
    declares it at raise time. Every existing ``raise NotEvaluated(reason)`` is
    unchanged and yields ``missing_input`` (FR-002).
    """

    def __init__(
        self, reason: str, kind: NotEvaluatedKind = NotEvaluatedKind.missing_input
    ) -> None:
        self.reason = reason
        self.kind = kind
        super().__init__(reason)


@dataclass(frozen=True)
class NotEvaluatedResult:
    """One validator that ran without error but consciously did not evaluate.

    Sibling to :class:`ValidatorError`; surfaced in the ``not_evaluated`` channel. It
    is not a finding (no severity, never gates) and not a load/run error (FR-005). The
    ``reason`` is the validator's English ``NotEvaluated`` reason; the runner stamps
    the ``validator`` name (the validator never names itself). The ``kind`` (default
    :attr:`NotEvaluatedKind.missing_input`) categorizes the gap as input-conditional
    or a permanent capability-gap (iteration 044); it is stamped by the runner from
    the signal and serialized as an additive key (FR-008).
    """

    validator: str
    reason: str
    kind: NotEvaluatedKind = NotEvaluatedKind.missing_input

    def to_json(self) -> dict[str, Any]:
        return {
            "validator": self.validator,
            "reason": self.reason,
            "kind": self.kind.value,
        }


@runtime_checkable
class Validator(Protocol):
    """The stable seam between the runner and any validator (design § 13.1).

    A validator examines the project (``ValidationContext``) and the already-built
    graph (``indexer``, possibly empty) and returns a list of ``Violation`` — an
    empty list means "evaluated, no findings" (a legitimate green, FR-001/FR-003). A
    validator that has no input for ANY of its checks MAY ``raise NotEvaluated(reason)``
    to declare it consciously did not look; the runner routes that to the
    ``not_evaluated`` channel (FR-001). The ``validate`` return type is **unchanged**:
    a custom validator returning a bare list keeps working as evaluated (FR-014). It
    MUST be deterministic (FR-019) and MUST NOT write to disk or mutate the graph
    (FR-020); it MAY raise — the runner isolates it (FR-014).
    """

    name: str
    severity_default: Severity

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]: ...


class UnknownValidatorError(BookwrightError):
    """A configured ``[validators]`` name is absent from the discovered set (FR-007)."""

    code = "unknown_validator"

    def __init__(self, names: tuple[str, ...]) -> None:
        self.names = names
        joined = ", ".join(names)
        super().__init__(f"unknown validator(s): {joined}", {"names": list(names)})


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
    _outline: Any = field(default=_UNSET, repr=False, compare=False)
    _character_names: Any = field(default=_UNSET, repr=False, compare=False)
    _setting_names: Any = field(default=_UNSET, repr=False, compare=False)
    _manuscript_files: Any = field(default=_UNSET, repr=False, compare=False)
    _constitution_text: Any = field(default=_UNSET, repr=False, compare=False)
    _manuscript_view: Any = field(default=_UNSET, repr=False, compare=False)
    _constitution_view: Any = field(default=_UNSET, repr=False, compare=False)
    _anchor_corpus: Any = field(default=_UNSET, repr=False, compare=False)

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

    def outline(self) -> MapResult:
        """Map the bible **and** ``outline/units/`` to GOLEM entities (once per run).

        Runs the combined ``map_bible`` → ``map_outline`` pipeline (the same one
        ``commands/_graph.build_project_graph`` runs) into a fresh ``MapResult`` so
        its ``unresolved_references`` carry the outline pass's role misses — which the
        bible-only :meth:`bible` never produces, and ``map_outline`` cannot produce
        standalone because it needs the character pass's ``roles_index``. Vocabularies
        are omitted on purpose: they only add ``crm:P2_has_type`` typing triples and do
        not affect ``unresolved_references`` (research D5). Writes nothing; reads no
        card by hand. The result is the single source of truth for role resolution
        ``narrative_structure``'s Rule c reuses (FR-006)."""
        if self._outline is _UNSET:
            from bookwright.io.bible import map_bible  # noqa: PLC0415
            from bookwright.io.outline import map_outline  # noqa: PLC0415

            bible_dir = self.root / self.manifest.paths.bible
            result = map_bible(self.root, bible_dir, self.uri_base)
            map_outline(self.root, self.root / self.manifest.paths.outline, self.uri_base, result)
            self._outline = result
        return cast("MapResult", self._outline)

    def anchor_corpus(self) -> tuple[Indexer, tuple[AnchorIdentity, ...]]:
        """An in-process research corpus engine + its anchor identities (048 research D1).

        Returns a fresh, **non-persisting** engine carrying the bible + outline +
        ``bible/research/`` triples and the ``AnchorIdentity`` records from one
        ``map_research`` pass, so the anchor URIs in the engine and the identities
        come from the **same build** and join by URI coherently — exactly how
        ``status`` resolves the same anchors. This is the only faithful realization
        of "the machinery ``status`` uses": anchors are ``MintedEntity`` (uuid7,
        re-minted every build), so a URI join against the *persisted* graph from a
        prior ``graph build`` would miss for every anchor (research D1).

        Assembled by the shared :func:`bookwright.io.bible.feed_graph` — the same
        triple-feeding ``commands._graph.build_project_graph`` uses — over ``io``/
        ``indexers``/``golem`` directly (reusing the memoized :meth:`outline`
        ``MapResult``), **not** via ``build_project_graph`` itself, which persists
        (``engine.save``) and would invert the layer direction. A validator never
        writes (FR-013): ``feed_graph`` saves nothing and ``engine.save`` is **not**
        called. Memoized once per run; an injected corpus (:meth:`set_anchor_corpus`)
        is returned as-is (test seam, research D4)."""
        if self._anchor_corpus is _UNSET:
            from bookwright.golem.namespaces import timeline_uri  # noqa: PLC0415
            from bookwright.indexers import resolve_indexer  # noqa: PLC0415
            from bookwright.io.bible import feed_graph  # noqa: PLC0415
            from bookwright.io.research import map_research  # noqa: PLC0415

            uri_base = self.uri_base
            result = self.outline()
            engine = resolve_indexer(self.manifest.bookwright.indexer)()
            research = map_research(
                self.root,
                self.root / self.manifest.paths.bible / "research",
                uri_base,
                self.manifest.book.language,
                result.entity_index,
                timeline_uri(uri_base),
            )
            feed_graph(engine, result, research, uri_base)
            self._anchor_corpus = (engine, research.anchor_identities)
        return cast("tuple[Indexer, tuple[AnchorIdentity, ...]]", self._anchor_corpus)

    def set_anchor_corpus(self, engine: Indexer, identities: tuple[AnchorIdentity, ...]) -> None:
        """Inject a pre-built ``(engine, identities)`` corpus (test seam, 048 D4).

        Pre-setting the memo slot **is** the whole seam: :meth:`anchor_corpus`
        returns the injected value instead of building. Lets a hand-built
        ``AnchorSpec`` fixture supply the corpus directly; production builds it lazily.
        """
        self._anchor_corpus = (engine, identities)

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

    def manuscript_view(self) -> tuple[tuple[str, ProseView], ...]:
        """Sorted ``(relpath, ProseView)`` parallel to :meth:`manuscript_files`.

        Built from the already-cached files (no second disk read), so the prose
        seam splits each manuscript file exactly once per run and every prose
        validator shares the result (C5.1/C5.3, FR-006).
        """
        if self._manuscript_view is _UNSET:
            from bookwright.io.prose import prose_view  # noqa: PLC0415

            self._manuscript_view = tuple(
                (relpath, prose_view(text)) for relpath, text in self.manuscript_files()
            )
        return cast("tuple[tuple[str, ProseView], ...]", self._manuscript_view)

    def constitution_view(self) -> ProseView:
        """The constitution's :class:`ProseView`, or ``()`` when it is absent (C5.2)."""
        if self._constitution_view is _UNSET:
            from bookwright.io.prose import prose_view  # noqa: PLC0415

            text = self.constitution_text()
            self._constitution_view = () if text is None else prose_view(text)
        return cast("ProseView", self._constitution_view)
