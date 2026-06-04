"""TOML block models for the Bookwright manifest.

Internal helper extracted from `bookwright.core.manifest` to honour the
Principle IV 500-line ceiling, mirroring the established `_build`,
`_translate`, and `_research_block` split. The root `Manifest` model and the
load/dump/build entry points stay in `manifest.py`, which re-exports the
public members defined here (`BOOK_TYPES`, `BOOK_STATUSES`) so the
`bookwright.core` surface is unchanged.
"""

from __future__ import annotations

import re
from typing import Any, Literal, get_args
from urllib.parse import urlsplit

from packaging.version import InvalidVersion, Version
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from pydantic_core import PydanticCustomError

from bookwright.core.iso639_1 import ISO_639_1_CODES

_MANIFEST_VERSION_RE = re.compile(r"^[1-9][0-9]*$")

BookType = Literal["novel", "essay", "memoir", "non-fiction-narrative", "other"]
BookStatus = Literal["idea", "structuring", "drafting", "revising", "done"]

BOOK_TYPES: frozenset[str] = frozenset(get_args(BookType))
BOOK_STATUSES: frozenset[str] = frozenset(get_args(BookStatus))


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

    @field_validator("schema_version", mode="after")
    @classmethod
    def _check_schema_version(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise PydanticCustomError(
                "empty",
                "schema_version must be a non-empty string",
                {"value": value},
            )
        if stripped != value:
            raise PydanticCustomError(
                "whitespace",
                "schema_version must not have leading or trailing whitespace",
                {"value": value},
            )
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
    type: BookType
    language: str
    authors: list[str]
    subtitle: str = ""
    genre: list[str] = Field(default_factory=list)
    target_length_words: int | None = None
    status: BookStatus = "drafting"
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
