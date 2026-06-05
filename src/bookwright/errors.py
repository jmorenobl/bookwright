"""The shared error base — the single source of truth for the JSON-over-stdout
error envelope (Principle IX, review finding R3).

Every Bookwright error that can reach a ``--json`` boundary subclasses
``BookwrightError`` and inherits its one canonical ``to_json()``; no error class
defines its own envelope serializer. This module is the lowest layer: it imports
**nothing** from ``core``/``golem``/``io``/``indexers``/``validation``/
``integrations``/``commands`` (FR-010), so it can be imported by all of them with
no risk of a cycle.
"""

from __future__ import annotations

from typing import Any


class BookwrightError(Exception):
    """Base for every Bookwright error that reaches a ``--json`` boundary.

    Subclasses declare a class-level ``code`` (the machine-readable identifier),
    pass a human ``message`` and optional ``details`` to ``__init__``, and inherit
    the one canonical ``to_json()``. A subclass MAY set ``self.code`` per instance
    (``_UsageError``). Abstract package roots leave ``code`` unset and are never
    serialized.
    """

    # Class-level default; concrete subclasses assign it (or set ``self.code``).
    # Deliberately a plain annotation, NOT ``ClassVar[str]``: a ``ClassVar`` would
    # forbid ``_UsageError``'s per-instance ``self.code`` override under
    # ``mypy --strict`` (research Decision 2).
    code: str

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)

    def to_json(self) -> dict[str, Any]:
        """The canonical error envelope; ``details`` only when non-empty."""
        payload: dict[str, Any] = {
            "status": "error",
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload
