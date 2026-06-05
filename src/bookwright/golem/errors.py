"""Exception hierarchy for the GOLEM domain model.

The error JSON shape is the canonical envelope owned by ``BookwrightError`` (this
iteration normalized the former flat ``{"error": …}`` body onto it).
"""

from __future__ import annotations

from bookwright.errors import BookwrightError


class GolemError(BookwrightError):
    """Base for every failure mode the ``bookwright.golem`` package owns.

    Abstract: declares no ``code`` and is never serialized directly.
    """


class EmptySlugError(GolemError):
    """A canonical name slugged to the empty string (FR-006).

    Carries the offending name so a caller can report exactly what was rejected.
    """

    code = "golem_empty_slug"

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"name {name!r} slugifies to an empty string", {"name": name})
