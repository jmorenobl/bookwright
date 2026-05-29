"""Success/error JSON envelopes and the ``.bookwright/init-options.json`` record.

Single source of truth for the contract-§3 envelope shapes and the
``InitOptionsRecord`` schema pinned in data-model §1. Pure helpers; the
only filesystem-touching primitive is ``dump_options_record`` and even
that just writes one JSON file.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from bookwright import __version__ as _BOOKWRIGHT_VERSION
from bookwright.core.iso639_1 import ISO_639_1_CODES

SCHEMA_VERSION = 1

_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class ResolvedInvocation(BaseModel):
    """Resolved values for one ``init`` invocation (data-model §2)."""

    model_config = ConfigDict(extra="forbid", strict=False)

    mode: Literal["named", "here"]
    project_name: str | None
    project_slug: str
    project_root: str
    title: str
    authors: list[str]
    language: str
    integration_key: str
    integration_skills_dir: str
    integration_options: dict[str, str | bool] = Field(default_factory=dict)
    no_git: bool
    force: bool
    json_output: bool
    git_status: Literal[
        "initialized",
        "skipped_by_flag",
        "skipped_no_binary",
        "skipped_existing_repo",
        "pending",
    ] = "pending"
    deprecated_flags_seen: list[str] = Field(default_factory=list)

    @field_validator("language")
    @classmethod
    def _check_language(cls, value: str) -> str:
        if value not in ISO_639_1_CODES:
            raise ValueError(f"language {value!r} is not a valid ISO 639-1 code")
        return value

    @field_validator("authors")
    @classmethod
    def _check_authors(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("authors must be non-empty")
        return value

    @field_validator("integration_skills_dir")
    @classmethod
    def _check_skills_dir(cls, value: str) -> str:
        if value.startswith("/"):
            raise ValueError(f"integration_skills_dir must be relative (got {value!r})")
        if ".." in Path(value).parts:
            raise ValueError(f"integration_skills_dir must not contain '..' (got {value!r})")
        return value


class InitOptionsRecord(BaseModel):
    """``.bookwright/init-options.json`` envelope (data-model §1)."""

    model_config = ConfigDict(extra="forbid", strict=False)

    schema_version: int = SCHEMA_VERSION
    created_at: str
    bookwright_version: str
    options: ResolvedInvocation

    @field_validator("schema_version")
    @classmethod
    def _check_schema_version(cls, value: int) -> int:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION} (got {value})")
        return value

    @field_validator("created_at")
    @classmethod
    def _check_created_at(cls, value: str) -> str:
        if not _ISO_UTC_RE.match(value):
            raise ValueError(f"created_at must match {_ISO_UTC_RE.pattern} (got {value!r})")
        return value


def _utc_now_iso_z() -> str:
    """ISO 8601 UTC second-precision suffixed with ``Z``."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def success_envelope(
    resolved: ResolvedInvocation,
    warnings: list[str],
) -> dict[str, Any]:
    """Contract §3.1 success-envelope shape."""

    return {
        "status": "ok",
        "project_root": resolved.project_root,
        "project_slug": resolved.project_slug,
        "mode": resolved.mode,
        "integration": {
            "key": resolved.integration_key,
            "skills_dir": resolved.integration_skills_dir,
            "options": dict(resolved.integration_options),
        },
        "git_status": resolved.git_status,
        "warnings": list(warnings),
        "bookwright_version": _BOOKWRIGHT_VERSION,
    }


def error_envelope(
    code: str,
    message: str,
    details: dict[str, Any],
    rolled_back: bool,
) -> dict[str, Any]:
    """Contract §3.2 error-envelope shape."""

    return {
        "status": "error",
        "code": code,
        "message": message,
        "details": dict(details),
        "rolled_back": rolled_back,
        "bookwright_version": _BOOKWRIGHT_VERSION,
    }


def dump_success_to_stdout(payload: dict[str, Any]) -> None:
    """Write the success envelope to stdout (contract §3.1 encoding)."""

    import sys  # noqa: PLC0415 — keeps the module importable in headless tests

    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")


def dump_error_to_stdout(payload: dict[str, Any]) -> None:
    """Write the error envelope to stdout (contract §3.2 encoding)."""

    import sys  # noqa: PLC0415 — keeps the module importable in headless tests

    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")


def build_options_record(resolved: ResolvedInvocation) -> InitOptionsRecord:
    """Wrap ``resolved`` in a versioned ``InitOptionsRecord``."""

    return InitOptionsRecord(
        schema_version=SCHEMA_VERSION,
        created_at=_utc_now_iso_z(),
        bookwright_version=_BOOKWRIGHT_VERSION,
        options=resolved,
    )


def serialize_options_record(record: InitOptionsRecord) -> bytes:
    """Encode an ``InitOptionsRecord`` for the on-disk copy (indent=2 + trailing newline)."""

    payload = record.model_dump(mode="json")
    return (json.dumps(payload, indent=2, sort_keys=False) + "\n").encode("utf-8")
