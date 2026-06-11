"""Typed in-memory model of a Bookwright `manifest.toml`.

Public surface is re-exported from `bookwright.core` (see contracts/manifest_api.md).
This module owns the Pydantic v2 model tree and the load/dump/build entry
points. The builder body lives in `bookwright.core._build` and the
`pydantic.ValidationError` translator in `bookwright.core._translate`, both
internal helpers kept separate to honour the Principle IV 500-line ceiling.
"""

from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path
from typing import Any, Literal

import tomlkit
import tomlkit.exceptions
from packaging.version import InvalidVersion, Version
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    ValidationError,
    model_validator,
)
from pydantic_core import PydanticCustomError
from tomlkit.toml_document import TOMLDocument

from bookwright import __version__ as _BOOKWRIGHT_VERSION
from bookwright.core._blocks import (
    BOOK_STATUSES,
    BOOK_TYPES,
    BookBlock,
    BookwrightBlock,
    IntegrationBlock,
    PathsBlock,
    ValidatorsBlock,
    VocabulariesBlock,
)
from bookwright.core._build import _build_manifest
from bookwright.core._focus_block import FocusBlock
from bookwright.core._research_block import ResearchBlock
from bookwright.core._translate import _translate_validation_error
from bookwright.core.errors import (
    ManifestNotFoundError,
    ManifestOverwriteError,
    ManifestSyntaxError,
    ManifestWarning,
)

KNOWN_MANIFEST_VERSIONS: frozenset[int] = frozenset({1})
"""The set of `manifest_version` integers this CLI understands natively."""

__all__ = [
    "BOOK_STATUSES",
    "BOOK_TYPES",
    "KNOWN_MANIFEST_VERSIONS",
    "BookBlock",
    "BookwrightBlock",
    "IntegrationBlock",
    "Manifest",
    "PathsBlock",
    "ValidatorsBlock",
    "VocabulariesBlock",
]


def _default_skills_dir_map() -> dict[str, str]:
    """Late-imported view of the integrations registry.

    Used by ``_build_manifest`` to fill the per-key skills_dir default
    (R2). The late import inside the function body keeps ``bookwright.core``
    importable in isolation; no module-top dependency on
    ``bookwright.integrations`` exists.
    """

    # Late import per R2 — keeps bookwright.core importable in isolation
    # and prevents a load-order cycle between core and integrations.
    from bookwright.integrations import INTEGRATION_REGISTRY  # noqa: PLC0415

    return {key: cls.default_skills_dir for key, cls in INTEGRATION_REGISTRY.items()}


def _installed_version() -> str:
    """Thin indirection so tests can monkey-patch the installed CLI version."""

    return _BOOKWRIGHT_VERSION


def _classify_manifest_version(parsed: int) -> Literal["known", "future"]:
    """FR-013 vs FR-014 single source of truth."""

    if parsed in KNOWN_MANIFEST_VERSIONS:
        return "known"
    return "future"


def _classify_manifest_version_warnings(
    raw: str,
) -> tuple[ManifestWarning, ...]:
    """Return the (possibly empty) warning tuple for a known/future `manifest_version`.

    Called only after Pydantic validation accepted `raw`, so `int(raw)` is
    safe — no need to re-run the regex validator (which raises
    `PydanticCustomError` outside Pydantic's machinery).
    """

    parsed = int(raw)
    if _classify_manifest_version(parsed) == "known":
        return ()
    max_known = max(KNOWN_MANIFEST_VERSIONS)
    return (
        ManifestWarning(
            rule_id="manifest_version.unknown_future",
            field_path="bookwright.manifest_version",
            offending_value=raw,
            message=(
                f"manifest_version {parsed} is newer than this CLI knows about "
                f"(max known: {max_known}); load was best-effort"
            ),
        ),
    )


class Manifest(BaseModel):
    """Root model. Unknown top-level blocks round-trip via `extra='allow'`."""

    model_config = ConfigDict(extra="allow", strict=True)

    bookwright: BookwrightBlock
    book: BookBlock
    vocabularies: VocabulariesBlock = Field(default_factory=VocabulariesBlock)
    validators: ValidatorsBlock = Field(default_factory=ValidatorsBlock)
    integration: IntegrationBlock
    paths: PathsBlock = Field(default_factory=PathsBlock)
    research: ResearchBlock = Field(default_factory=ResearchBlock)
    focus: FocusBlock | None = None  # absent [focus] block ⇒ None (research D1)

    _document: TOMLDocument | None = PrivateAttr(default=None)
    _warnings: tuple[ManifestWarning, ...] = PrivateAttr(default=())

    @property
    def warnings(self) -> tuple[ManifestWarning, ...]:
        """Non-fatal notes attached during `load()`; empty for freshly built manifests.

        Exposed as a read-only property (not a Pydantic field) so a user-authored
        `[warnings]` block in `manifest.toml` rounds-trips via `extra="allow"`
        instead of colliding with a declared field.
        """

        return self._warnings

    @model_validator(mode="after")
    def _check_cli_floor(self) -> Manifest:
        # cli_version_min was already validated as PEP 440 by its field validator;
        # field errors short-circuit model_validators, so we never see invalid input here.
        required = Version(self.bookwright.cli_version_min)
        installed_raw = _installed_version()
        try:
            installed = Version(installed_raw)
        except InvalidVersion as exc:
            raise PydanticCustomError(
                "installed_not_pep440",
                "installed CLI version '{installed}' is not valid PEP 440",
                {
                    "value": self.bookwright.cli_version_min,
                    "installed": installed_raw,
                },
            ) from exc
        if installed < required:
            raise PydanticCustomError(
                "installed_too_old",
                "installed CLI {installed} is older than required {required}",
                {
                    "value": self.bookwright.cli_version_min,
                    "installed": installed_raw,
                    "required": self.bookwright.cli_version_min,
                },
            )
        return self

    @classmethod
    def load(cls, path: Path | str) -> Manifest:
        """Read, parse, and validate a manifest file. See contracts/manifest_api.md."""

        resolved = Path(path)
        if not resolved.exists():
            raise ManifestNotFoundError(resolved)
        text = resolved.read_text(encoding="utf-8")
        try:
            document = tomlkit.parse(text)
        except tomlkit.exceptions.ParseError as exc:
            line = getattr(exc, "line", None)
            column = getattr(exc, "col", None)
            raise ManifestSyntaxError(
                path=resolved,
                line=line,
                column=column,
                message=str(exc),
            ) from exc
        try:
            instance = cls.model_validate(document.unwrap())
        except ValidationError as exc:
            raise _translate_validation_error(exc) from exc
        instance._document = document
        instance._warnings = _classify_manifest_version_warnings(
            instance.bookwright.manifest_version
        )
        return instance

    @classmethod
    def build(
        cls,
        *,
        title: str,
        authors: list[str],
        integration_key: str,
        **overrides: Any,
    ) -> Manifest:
        """Construct a fresh manifest from minimal inputs. See contracts/manifest_api.md."""

        # R10 — only consult the integrations registry when the caller
        # didn't supply an explicit `integration_skills_dir`. Otherwise
        # `_build_manifest` ignores the map entirely, so building it
        # (and the `bookwright.integrations` import that triggers
        # `_register_builtins()`) is wasted work — and worse, it forces
        # every Manifest.build caller through the registry even when
        # core-only behaviour is what they want.
        #
        # R23 — align the "supplied" predicate with `_build_manifest`'s
        # documented None-as-default contract (see _build.py: explicit-None
        # overrides are dropped from `effective_overrides`). Using
        # ``"integration_skills_dir" in overrides`` here would diverge:
        # ``Manifest.build(..., integration_skills_dir=None)`` would skip
        # the registry, then `_build_manifest` would also skip the
        # override (None filtered), then `default_skills_dir[key]` would
        # raise KeyError → misleading TypeError. ``.get(...) is not None``
        # keeps both call sites in agreement.
        default_skills_dir: dict[str, str] = (
            {} if overrides.get("integration_skills_dir") is not None else _default_skills_dir_map()
        )

        return _build_manifest(
            cls,
            title=title,
            authors=authors,
            integration_key=integration_key,
            installed_version=_installed_version(),
            default_skills_dir=default_skills_dir,
            **overrides,
        )

    def _require_document(self, method: str) -> TOMLDocument:
        """The backing ``tomlkit`` document, or ``RuntimeError`` for bare constructions.

        The shared guard for every document-backed method (``set_integration``,
        ``set_focus``, ``clear_focus``, ``dump``): each requires an instance
        produced by :meth:`load` or :meth:`build`.
        """

        document = self._document
        if document is None:
            raise RuntimeError(
                f"Manifest.{method}() requires an instance produced by "
                "Manifest.load() or Manifest.build()."
            )
        return document

    def set_integration(self, *, key: str, skills_dir: str) -> None:
        """Update the ``[integration]`` block in place, preserving comments and order.

        Mutates **both** the validated model field and the backing ``tomlkit``
        document, so a subsequent :meth:`dump` writes the new ``key`` /
        ``skills_dir`` while every other key, comment, and the block ordering
        round-trip untouched (FR-020). The ``[integration.options]`` sub-table is
        left as-is — the two v0 integrations both default to no options, and a
        future per-integration option migration is an additive concern.

        Requires an instance produced by :meth:`load` or :meth:`build` (i.e. one
        carrying a ``tomlkit`` document); a bare construction raises ``RuntimeError``,
        the same contract as :meth:`dump`.
        """

        document = self._require_document("set_integration")
        table = document["integration"]
        table["key"] = key
        table["skills_dir"] = skills_dir
        self.integration = self.integration.model_copy(
            update={"key": key, "skills_dir": skills_dir}
        )

    def set_focus(self, *, target: str, notes: str, updated_at: str) -> FocusBlock:
        """Create or update the ``[focus]`` block in place, preserving comments and order.

        Validates first: the :class:`FocusBlock` is constructed *before* either
        the model or the backing document is touched, so invalid input raises
        ``pydantic.ValidationError`` and leaves the manifest unchanged — a failed
        call can never desync the two or poison a subsequent :meth:`dump`. On
        success it mutates **both** the validated ``self.focus`` field and the
        backing ``tomlkit`` document — exactly like :meth:`set_integration` — so a
        subsequent :meth:`dump` writes the new block while every other block,
        comment, and the block ordering round-trip untouched (FR-009, SC-002). The
        ``[focus]`` table is appended last when absent, or updated in place when
        present. ``notes`` is always written (an explicit ``notes = ""`` on a
        create with no ``--notes``), so an omitted and an empty key are
        equivalent — the explicit form is the greppable, unambiguous one
        (data-model write-shape decision 1). Returns the validated block.

        Requires an instance produced by :meth:`load` or :meth:`build`; a bare
        construction raises ``RuntimeError``, the same contract as :meth:`dump`.
        """

        document = self._require_document("set_focus")
        block = FocusBlock(target=target, notes=notes, updated_at=updated_at)
        if "focus" not in document:
            document["focus"] = tomlkit.table()
        table = document["focus"]
        table["target"] = block.target
        table["notes"] = block.notes
        table["updated_at"] = block.updated_at
        self.focus = block
        return block

    def clear_focus(self) -> None:
        """Remove the ``[focus]`` block if present; set ``self.focus = None``.

        A no-op (no error) when already absent. Mutates the backing ``tomlkit``
        document so a subsequent :meth:`dump` drops the block while preserving
        every other block, comment, and ordering (FR-010, SC-002). Same
        document-backed contract as :meth:`set_integration` / :meth:`dump`.
        """

        document = self._require_document("clear_focus")
        if "focus" in document:
            del document["focus"]
        self.focus = None

    def dump(self, path: Path | str, *, overwrite: bool = False) -> Path:
        """Atomically write the manifest to `path`. See contracts/manifest_api.md."""

        target = Path(path)
        if target.exists() and not overwrite:
            raise ManifestOverwriteError(target)

        document = self._require_document("dump")

        body = tomlkit.dumps(document)

        parent = target.parent
        parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(parent),
            prefix=f".{target.name}.",
            suffix=".tmp",
        )
        try:
            # `newline=""` disables Python's universal-newlines translation
            # so the file we hand-fsynced lands byte-identical on every
            # platform (Windows would otherwise rewrite `\n` to `\r\n`,
            # breaking the FR-020 round-trip guarantee).
            with os.fdopen(tmp_fd, "w", encoding="utf-8", newline="") as handle:
                handle.write(body)
                handle.flush()
                os.fsync(handle.fileno())
            if overwrite:
                os.replace(tmp_path, target)
            else:
                # `os.link` is atomic: if the target appears between the
                # early `exists()` check and here, link raises FileExistsError
                # rather than silently clobbering — closes the TOCTOU race.
                try:
                    os.link(tmp_path, target)
                except FileExistsError as exc:
                    raise ManifestOverwriteError(target) from exc
                # Once `os.link` succeeds, `target` already holds the new
                # bytes (as a hard link). Failing to remove the tmp side of
                # the link does NOT undo that commit — raising here would
                # mislead callers into thinking the write failed and would
                # violate the FR-021 atomicity contract from the opposite
                # direction. Best-effort cleanup; leave a leaked tmp file
                # rather than a phantom failure.
                with contextlib.suppress(OSError):
                    os.unlink(tmp_path)
        except BaseException:
            # Suppress *all* OSError variants during cleanup so the real
            # exception (the one that triggered this branch) is not
            # shadowed by a PermissionError / EBUSY / etc. raised by the
            # cleanup itself.
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise

        return target.resolve()
