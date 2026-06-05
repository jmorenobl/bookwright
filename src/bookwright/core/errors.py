"""Public exception hierarchy and warning model for the manifest module.

The error JSON shape is the canonical envelope owned by ``BookwrightError``
(this iteration normalized the former flat ``{"error": …}`` bodies onto it).
See specs/018-unified-error-envelope/contracts/error-envelope.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from bookwright.errors import BookwrightError


@dataclass(frozen=True)
class _FieldFailure:
    """One field-level validation failure.

    Internal type. The public JSON form is emitted under
    ``ManifestValidationError``'s ``details["failures"]``.
    """

    field_path: str
    rejected_value: Any
    rule_id: str
    message: str


class ManifestError(BookwrightError):
    """Base for every failure mode the manifest module owns.

    Abstract: declares no ``code`` and is never serialized directly.
    """


class ManifestNotFoundError(ManifestError):
    """The manifest file does not exist."""

    code = "manifest_not_found"

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).resolve()
        super().__init__(f"no manifest at {self.path}", {"path": str(self.path)})


class ManifestSyntaxError(ManifestError):
    """The manifest file exists but is not valid TOML."""

    code = "manifest_syntax"

    def __init__(
        self,
        path: Path | str,
        line: int | None,
        column: int | None,
        message: str,
    ) -> None:
        self.path = Path(path).resolve()
        self.line = line
        self.column = column
        super().__init__(
            message,
            {"field": f"bookwright.{self.path.name}", "line": line, "column": column},
        )


class ManifestValidationError(ManifestError):
    """One or more field-level validation failures (FR-004..FR-013)."""

    code = "manifest_validation"

    def __init__(self, failures: tuple[_FieldFailure, ...]) -> None:
        if not failures:
            raise ValueError("ManifestValidationError requires at least one failure")
        self.failures = failures
        first = failures[0]
        summary = (
            f"{len(failures)} validation failure(s); first: {first.field_path}: {first.message}"
        )
        super().__init__(
            summary,
            {
                "failures": [
                    {
                        "field": f.field_path,
                        "value": f.rejected_value,
                        "rule": f.rule_id,
                        "message": f.message,
                    }
                    for f in failures
                ]
            },
        )


class ManifestOverwriteError(ManifestError):
    """Refuse to overwrite an existing manifest (FR-019)."""

    code = "manifest_overwrite_refused"

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).resolve()
        super().__init__(
            f"refuse to overwrite existing manifest at {self.path} (pass overwrite=True to force)",
            {"path": str(self.path)},
        )


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
