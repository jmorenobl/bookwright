"""Success/error JSON envelopes and the ``.bookwright/init-options.json`` record.

Single source of truth for the contract-§3 envelope shapes and the
``InitOptionsRecord`` schema pinned in data-model §1. Pure helpers; the
only filesystem-touching primitive is ``dump_options_record`` and even
that just writes one JSON file.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, NoReturn

import typer
from pydantic import BaseModel, ConfigDict, Field, field_validator

from bookwright import __version__ as _BOOKWRIGHT_VERSION
from bookwright.core.iso639_1 import ISO_639_1_CODES
from bookwright.integrations import MalformedOptionError

from .git import GitInitError
from .scaffold import BackupCreationError, TargetOutsideProjectRootError

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
    ]
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

    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")


def dump_error_to_stdout(payload: dict[str, Any]) -> None:
    """Write the error envelope to stdout (contract §3.2 encoding)."""

    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")


def emit_error(  # noqa: PLR0913 — structured-error envelope demands all six fields
    *,
    code: str,
    message: str,
    details: dict[str, Any],
    exit_code: int,
    json_output: bool,
    rolled_back: bool,
) -> NoReturn:
    """Build and emit the error envelope, then raise ``typer.Exit(exit_code)``.

    JSON callers get a single envelope on stdout (contract §3.2); humans
    get a single ``bookwright: error: <message>`` line on stderr. Always
    raises — callers can rely on ``NoReturn`` for control-flow analysis.
    """

    if json_output:
        payload = error_envelope(
            code=code, message=message, details=details, rolled_back=rolled_back
        )
        dump_error_to_stdout(payload)
    else:
        sys.stderr.write(f"bookwright: error: {message}\n")
    raise typer.Exit(exit_code)


def classify_filesystem_failure(  # noqa: PLR0911 — one branch per contract §4 exception type
    exc: BaseException,
) -> tuple[str, int, dict[str, Any]]:
    """Map a scaffold-time exception to ``(code, exit_code, details)`` (contract §4)."""

    if isinstance(exc, MalformedOptionError):
        # `SkillsIntegration.setup()` raises this at scaffold time for
        # `resolves_to_project_root` / `escapes_project_root` (and similar
        # option-domain rules). Surface it with the same code/exit_code/details
        # shape that parse-time `MalformedOptionError` uses in
        # `resolve.resolve_integration`, so consumers see a single contract.
        return (
            "malformed_option",
            5,
            {"value": exc.value, "rule": exc.rule},
        )
    if isinstance(exc, BackupCreationError):
        return (
            "backup_creation_error",
            6,
            {"target": str(exc.target), "reason": exc.reason},
        )
    if isinstance(exc, PermissionError):
        return (
            "permission_denied",
            6,
            {"path": str(getattr(exc, "filename", "") or ""), "errno": exc.errno or 0},
        )
    if isinstance(exc, GitInitError):
        return (
            "git_error",
            7,
            {"stderr": exc.stderr},
        )
    if isinstance(exc, TargetOutsideProjectRootError):
        return (
            "filesystem_error",
            6,
            {"path": str(exc.target), "errno": 0},
        )
    if isinstance(exc, OSError):
        return (
            "filesystem_error",
            6,
            {"path": str(getattr(exc, "filename", "") or ""), "errno": exc.errno or 0},
        )
    return (
        "filesystem_error",
        6,
        {"path": "", "errno": 0},
    )


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
