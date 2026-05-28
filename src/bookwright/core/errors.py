"""Public exception hierarchy and warning model for the manifest module.

JSON shapes returned by `.to_json()` are part of the FR-024 contract.
See specs/002-manifest-model/contracts/manifest_api.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class _FieldFailure:
    """One field-level validation failure.

    Internal type. The public JSON form is returned by
    `ManifestValidationError.to_json()`.
    """

    field_path: str
    rejected_value: Any
    rule_id: str
    message: str


class ManifestError(Exception):
    """Base for every failure mode the manifest module owns."""


class ManifestNotFoundError(ManifestError):
    """The manifest file does not exist."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).resolve() if isinstance(path, (str, Path)) else path
        message = f"no manifest at {self.path}"
        super().__init__(message)
        self.message = message

    def to_json(self) -> dict[str, Any]:
        return {
            "error": "manifest_not_found",
            "path": str(self.path),
            "message": self.message,
        }


class ManifestSyntaxError(ManifestError):
    """The manifest file exists but is not valid TOML."""

    def __init__(
        self,
        path: Path | str,
        line: int | None,
        column: int | None,
        message: str,
    ) -> None:
        self.path = Path(path)
        self.line = line
        self.column = column
        self.message = message
        super().__init__(message)

    def to_json(self) -> dict[str, Any]:
        return {
            "error": "manifest_syntax",
            "field": f"bookwright.{self.path.name}",
            "line": self.line,
            "column": self.column,
            "message": self.message,
        }


class ManifestValidationError(ManifestError):
    """One or more field-level validation failures (FR-004..FR-013)."""

    def __init__(self, failures: tuple[_FieldFailure, ...]) -> None:
        if not failures:
            raise ValueError("ManifestValidationError requires at least one failure")
        self.failures = failures
        first = failures[0]
        summary = (
            f"{len(failures)} validation failure(s); first: {first.field_path}: {first.message}"
        )
        super().__init__(summary)
        self.message = summary

    def to_json(self) -> dict[str, Any]:
        return {
            "error": "manifest_validation",
            "failures": [
                {
                    "field": f.field_path,
                    "value": f.rejected_value,
                    "rule": f.rule_id,
                    "message": f.message,
                }
                for f in self.failures
            ],
        }


class ManifestOverwriteError(ManifestError):
    """Refuse to overwrite an existing manifest (FR-019)."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).resolve() if isinstance(path, (str, Path)) else path
        message = (
            f"refuse to overwrite existing manifest at {self.path} (pass overwrite=True to force)"
        )
        super().__init__(message)
        self.message = message

    def to_json(self) -> dict[str, Any]:
        return {
            "error": "manifest_overwrite_refused",
            "path": str(self.path),
            "message": self.message,
        }


class ManifestWarning(BaseModel):
    """A non-fatal note attached to `Manifest.warnings` during `load()`."""

    rule_id: str
    field_path: str
    offending_value: Any
    message: str

    def to_json(self) -> dict[str, Any]:
        return {
            "rule": self.rule_id,
            "field": self.field_path,
            "value": self.offending_value,
            "message": self.message,
        }
