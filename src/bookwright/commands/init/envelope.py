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
from bookwright.errors import BookwrightError
from bookwright.integrations import (
    MalformedOptionError,
    SkillLintError,
    SkillMaterializationError,
)

from .._envelope import emit_json
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
    error: BookwrightError | str,
    message: str | None = None,
    details: dict[str, Any] | None = None,
    *,
    rolled_back: bool,
) -> dict[str, Any]:
    """Contract §3.2 error-envelope shape: the canonical body + init's superset.

    The ``{status,code,message[,details]}`` skeleton lives in exactly one place —
    ``BookwrightError.to_json`` (review R1). Pass a ``BookwrightError`` to spread
    that body; pass a primitive ``code`` (as ``error``) plus ``message``/``details``
    for the non-``BookwrightError`` carve-outs that ``classify_filesystem_failure``
    maps by hand (``OSError``/``PermissionError``/``GitInitError`` and the two
    ``io.fs`` errors).
    """

    body: dict[str, Any]
    if isinstance(error, BookwrightError):
        body = error.to_json()
    else:
        body = {
            "status": "error",
            "code": error,
            "message": message,
            "details": dict(details or {}),
        }
    return {**body, "rolled_back": rolled_back, "bookwright_version": _BOOKWRIGHT_VERSION}


def dump_success_to_stdout(payload: dict[str, Any]) -> None:
    """Write the success envelope to stdout (contract §3.1 encoding).

    The encoding itself is single-sourced in ``commands._envelope.emit_json``;
    this name (and its §3.2 sibling) survives so init call sites keep naming
    which contract section they are emitting.
    """

    emit_json(payload)


def dump_error_to_stdout(payload: dict[str, Any]) -> None:
    """Write the error envelope to stdout (contract §3.2 encoding)."""

    emit_json(payload)


def _emit(payload: dict[str, Any], message: str, *, exit_code: int, json_output: bool) -> NoReturn:
    """Surface an error envelope, then exit: one JSON document on stdout under
    ``--json`` (contract §3.2), else a single ``bookwright: error: <message>``
    line on stderr (Principle IX). Always raises."""

    if json_output:
        dump_error_to_stdout(payload)
    else:
        sys.stderr.write(f"bookwright: error: {message}\n")
    raise typer.Exit(exit_code)


def emit_error(  # noqa: PLR0913 — structured-error envelope demands all six fields
    *,
    code: str,
    message: str,
    details: dict[str, Any],
    exit_code: int,
    json_output: bool,
    rolled_back: bool,
) -> NoReturn:
    """Build and emit the error envelope for a primitive ``code``/``message``/
    ``details`` triple, then raise ``typer.Exit(exit_code)``.

    The call sites with no ``BookwrightError`` in hand (mutex, removed flags, the
    conflict matrix, and the filesystem/permission carve-outs). Always raises —
    callers can rely on ``NoReturn`` for control-flow analysis.
    """

    _emit(
        error_envelope(code, message, details, rolled_back=rolled_back),
        message,
        exit_code=exit_code,
        json_output=json_output,
    )


def emit_scaffold_failure(exc: BaseException, *, json_output: bool) -> NoReturn:
    """Emit the §3.2 envelope for a caught scaffold-time exception, then exit.

    A ``BookwrightError`` (``MalformedOptionError``/``SkillLintError``/
    ``SkillMaterializationError``) carries its own canonical body, so we spread
    ``error_envelope(exc, ...)`` — keeping the skeleton single-sourced in
    ``BookwrightError.to_json`` (review R1). The non-``BookwrightError`` carve-outs
    (``OSError``/``PermissionError``/``GitInitError`` and the two ``io.fs`` errors)
    have no envelope, so ``classify_filesystem_failure`` maps them to a primitive
    ``code``/``details`` pair; only its ``exit_code`` is consulted for the base
    path. The scaffold is already rolled back by the caller, hence
    ``rolled_back=True``.
    """

    code, exit_code, details = classify_filesystem_failure(exc)
    if isinstance(exc, BookwrightError):
        payload = error_envelope(exc, rolled_back=True)
        message = exc.message
    else:
        message = str(exc) or code
        payload = error_envelope(code, message, details, rolled_back=True)
    _emit(payload, message, exit_code=exit_code, json_output=json_output)


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
    if isinstance(exc, (SkillLintError, SkillMaterializationError)):
        # The skills materializer (SkillsIntegration.setup()) aborts the
        # integration on a lint failure or an authoring error. Surface the
        # structured error verbatim (its `code` distinguishes the two) so the
        # JSON envelope carries the skill/rule/detail triple (FR-016/FR-020).
        return (
            exc.code,
            6,
            {"skill": exc.skill, "rule": exc.rule, "detail": exc.detail},
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
