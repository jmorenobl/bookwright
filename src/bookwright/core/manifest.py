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
import re
import tempfile
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

import tomlkit
import tomlkit.exceptions
from packaging.version import InvalidVersion, Version
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError
from tomlkit.toml_document import TOMLDocument

from bookwright import __version__ as _BOOKWRIGHT_VERSION
from bookwright.core._build import _build_manifest
from bookwright.core._translate import _translate_validation_error
from bookwright.core.errors import (
    ManifestNotFoundError,
    ManifestOverwriteError,
    ManifestSyntaxError,
    ManifestWarning,
)
from bookwright.core.iso639_1 import ISO_639_1_CODES

_MANIFEST_VERSION_RE = re.compile(r"^[1-9][0-9]*$")

KNOWN_MANIFEST_VERSIONS: frozenset[int] = frozenset({1})
"""The set of `manifest_version` integers this CLI understands natively."""

BOOK_TYPES: frozenset[str] = frozenset(
    {"novel", "essay", "memoir", "non-fiction-narrative", "other"}
)

BOOK_STATUSES: frozenset[str] = frozenset({"idea", "structuring", "drafting", "revising", "done"})

DEFAULT_SKILLS_DIR: dict[str, str] = {
    "claude": ".claude/skills",
    "generic": ".agents/skills",
}


def _installed_version() -> str:
    """Thin indirection so tests can monkey-patch the installed CLI version."""

    return _BOOKWRIGHT_VERSION


def _parse_manifest_version(raw: str) -> int:
    """Parse the `bookwright.manifest_version` string into a positive int.

    Raises a Pydantic-friendly error when the value does not match the
    `^[1-9][0-9]*$` shape required by FR-013.
    """

    if not _MANIFEST_VERSION_RE.match(raw):
        raise PydanticCustomError(
            "not_positive_integer_string",
            "manifest_version must match ^[1-9][0-9]*$ (got '{value}')",
            {"value": raw},
        )
    return int(raw)


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


class BookwrightBlock(BaseModel):
    """`[bookwright]` block — CLI/schema floor and project URI namespace."""

    model_config = ConfigDict(extra="forbid", strict=True)

    cli_version_min: str
    schema_version: str
    manifest_version: str
    uri_base: str
    indexer: str = "rdflib"

    @field_validator("cli_version_min", mode="after")
    @classmethod
    def _check_cli_version_min(cls, value: str) -> str:
        try:
            Version(value)
        except InvalidVersion as exc:
            raise PydanticCustomError(
                "not_pep440",
                "cli_version_min '{value}' is not a valid PEP 440 version",
                {"value": value},
            ) from exc
        return value

    @field_validator("manifest_version", mode="after")
    @classmethod
    def _check_manifest_version(cls, value: str) -> str:
        _parse_manifest_version(value)
        return value

    @field_validator("uri_base", mode="after")
    @classmethod
    def _check_uri_base(cls, value: str) -> str:
        try:
            parts = urlsplit(value)
        except ValueError as exc:
            raise PydanticCustomError(
                "invalid_uri",
                "uri_base '{value}' is not a parseable URI",
                {"value": value},
            ) from exc
        scheme = parts.scheme.lower()
        if scheme not in {"http", "https"}:
            raise PydanticCustomError(
                "wrong_scheme",
                "uri_base must use http or https (got scheme '{scheme}')",
                {"scheme": parts.scheme, "value": value},
            )
        if not parts.netloc:
            raise PydanticCustomError(
                "empty_host",
                "uri_base must include a non-empty host",
                {"value": value},
            )
        if parts.query:
            raise PydanticCustomError(
                "has_query",
                "uri_base must not include a query string",
                {"value": value},
            )
        if parts.fragment:
            raise PydanticCustomError(
                "has_fragment",
                "uri_base must not include a fragment",
                {"value": value},
            )
        if not value.endswith("/"):
            raise PydanticCustomError(
                "no_trailing_slash",
                "uri_base must end with '/'",
                {"value": value},
            )
        return value


class BookBlock(BaseModel):
    """`[book]` block — author-facing metadata about the work."""

    model_config = ConfigDict(extra="forbid", strict=True)

    title: str
    type: Literal["novel", "essay", "memoir", "non-fiction-narrative", "other"]
    language: str
    authors: list[str]
    subtitle: str = ""
    genre: list[str] = Field(default_factory=list)
    target_length_words: int | None = None
    status: Literal["idea", "structuring", "drafting", "revising", "done"] = "drafting"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", mode="after")
    @classmethod
    def _check_title(cls, value: str) -> str:
        if not value.strip():
            raise PydanticCustomError(
                "empty",
                "title must be a non-empty string",
                {"value": value},
            )
        return value

    @field_validator("language", mode="after")
    @classmethod
    def _check_language(cls, value: str) -> str:
        if value not in ISO_639_1_CODES:
            raise PydanticCustomError(
                "not_iso_639_1",
                "language '{value}' is not a valid ISO 639-1 code",
                {"value": value},
            )
        return value

    @field_validator("authors", mode="after")
    @classmethod
    def _check_authors(cls, value: list[str]) -> list[str]:
        if not value:
            raise PydanticCustomError(
                "empty",
                "authors must contain at least one entry",
                {"value": value},
            )
        for index, entry in enumerate(value):
            if not entry.strip():
                raise PydanticCustomError(
                    "entry.empty",
                    "authors[{index}] must be a non-empty string",
                    {"index": index, "value": entry},
                )
        return value


class VocabulariesBlock(BaseModel):
    """`[vocabularies]` block — names of active vocabulary lists."""

    model_config = ConfigDict(extra="forbid", strict=True)

    active: list[str] = Field(default_factory=list)


class ValidatorsBlock(BaseModel):
    """`[validators]` block — built-in and custom validator names."""

    model_config = ConfigDict(extra="forbid", strict=True)

    enabled: list[str] = Field(default_factory=list)
    disabled: list[str] = Field(default_factory=list)
    custom: list[str] = Field(default_factory=list)


class IntegrationBlock(BaseModel):
    """`[integration]` block — opaque data the loader never dispatches on."""

    model_config = ConfigDict(extra="forbid", strict=True)

    key: str
    skills_dir: str
    options: dict[str, Any] = Field(default_factory=dict)


class PathsBlock(BaseModel):
    """`[paths]` block — project-relative content roots."""

    model_config = ConfigDict(extra="forbid", strict=True)

    manuscript: str = "manuscript/"
    bible: str = "bible/"
    outline: str = "outline/"
    graph: str = "bible/graph.ttl"
    constitution: str = "bible/constitution.md"


class Manifest(BaseModel):
    """Root model. Unknown top-level blocks round-trip via `extra='allow'`."""

    model_config = ConfigDict(extra="allow", strict=True)

    bookwright: BookwrightBlock
    book: BookBlock
    vocabularies: VocabulariesBlock = Field(default_factory=VocabulariesBlock)
    validators: ValidatorsBlock = Field(default_factory=ValidatorsBlock)
    integration: IntegrationBlock
    paths: PathsBlock = Field(default_factory=PathsBlock)

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

        return _build_manifest(
            cls,
            title=title,
            authors=authors,
            integration_key=integration_key,
            installed_version=_installed_version(),
            default_skills_dir=DEFAULT_SKILLS_DIR,
            **overrides,
        )

    def dump(self, path: Path | str, *, overwrite: bool = False) -> Path:
        """Atomically write the manifest to `path`. See contracts/manifest_api.md."""

        target = Path(path)
        if target.exists() and not overwrite:
            raise ManifestOverwriteError(target)

        document = self._document
        if document is None:
            raise RuntimeError(
                "Manifest.dump() requires an instance produced by Manifest.load() "
                "or Manifest.build(); bare constructions have no tomlkit document "
                "to serialize."
            )

        body = tomlkit.dumps(document)

        parent = target.parent
        parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(parent),
            prefix=f".{target.name}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as handle:
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
                os.unlink(tmp_path)
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(tmp_path)
            raise

        return target.resolve()
