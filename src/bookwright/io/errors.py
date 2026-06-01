"""Exception hierarchy for plain-text → model parsing (the ``io`` package).

The ``.to_json()`` shapes mirror ``bookwright.core.errors`` so a downstream
``--json`` command that surfaces one of these stays Principle-IX compliant
(data-model § 6).
"""

from __future__ import annotations

from typing import Any


class IOError_(Exception):
    """Base for every failure mode the ``bookwright.io`` package owns.

    Named with a trailing underscore so it never shadows the builtin ``IOError``.
    """


class ProjectNotFoundError(IOError_):
    """No ``manifest.toml`` was found in the cwd or any ancestor (R8)."""

    code = "not_a_project"

    def __init__(self, start: str) -> None:
        self.start = start
        message = f"no manifest.toml in {start} or any parent directory"
        super().__init__(message)
        self.message = message

    def to_json(self) -> dict[str, Any]:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "details": {"start": self.start},
        }


class MissingDirectoryError(IOError_):
    """A required content directory (``bible/`` or ``manuscript/``) is absent (FR-012)."""

    code = "missing_directory"

    def __init__(self, name: str, path: str) -> None:
        self.name = name
        self.path = path
        message = f"required directory {name!r} is missing at {path}"
        super().__init__(message)
        self.message = message

    def to_json(self) -> dict[str, Any]:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "details": {"name": self.name, "path": self.path},
        }


class InvalidFrontmatterError(IOError_):
    """A single source file's frontmatter is unusable (FR-013).

    Per-file and collected: the build skips the file, records ``(path, reason)``,
    and continues — it never aborts the whole build.
    """

    code = "invalid_frontmatter"

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        message = f"invalid frontmatter in {path}: {reason}"
        super().__init__(message)
        self.message = message

    def to_json(self) -> dict[str, Any]:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "details": {"path": self.path, "reason": self.reason},
        }


class SlugCollisionError(IOError_):
    """Two entities of one concept share an identifier (FR-014) — fatal, no graph."""

    code = "slug_collision"

    def __init__(self, identifier: str, first_path: str, second_path: str) -> None:
        self.identifier = identifier
        self.first_path = first_path
        self.second_path = second_path
        message = f"identifier {identifier!r} is claimed by both {first_path} and {second_path}"
        super().__init__(message)
        self.message = message

    def to_json(self) -> dict[str, Any]:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "details": {
                "identifier": self.identifier,
                "sources": [self.first_path, self.second_path],
            },
        }
