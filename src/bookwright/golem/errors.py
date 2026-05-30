"""Exception hierarchy for the GOLEM domain model.

The ``.to_json()`` shapes mirror ``bookwright.core.errors`` so a downstream
``--json`` command that surfaces one of these stays Principle-IX compliant.
"""

from __future__ import annotations

from typing import Any


class GolemError(Exception):
    """Base for every failure mode the ``bookwright.golem`` package owns."""


class EmptySlugError(GolemError):
    """A canonical name slugged to the empty string (FR-006).

    Carries the offending name so a caller can report exactly what was rejected.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        message = f"name {name!r} slugifies to an empty string"
        super().__init__(message)
        self.message = message

    def to_json(self) -> dict[str, Any]:
        return {
            "error": "golem_empty_slug",
            "name": self.name,
            "message": self.message,
        }
