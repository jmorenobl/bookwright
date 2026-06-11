"""Command-layer errors for the ``focus`` sub-app (research D6).

The one genuinely new failure this iteration introduces is an empty/whitespace
``--target`` passed to ``focus set`` (FR-008) — a command-input concern, not an
on-disk manifest concern, so it lives in the command layer rather than ``core``.
Project/manifest faults reuse the existing ``ProjectNotFoundError`` /
``invalid_manifest`` remap; nothing new is needed for them.

Subclassing :class:`bookwright.errors.BookwrightError` directly (the same shape
as ``commands.init``'s ``InvalidProjectNameError``) inherits the canonical
``--json`` envelope (``to_json``) — no per-class serializer (Principle IX,
FR-013). A focus-group error base can be reintroduced when a second
focus-owned failure mode actually exists.
"""

from __future__ import annotations

from bookwright.errors import BookwrightError


class FocusTargetEmptyError(BookwrightError):
    """``focus set`` was given an empty/whitespace-only ``--target`` (FR-008)."""

    code = "focus_target_empty"

    def __init__(self) -> None:
        super().__init__("--target must be a non-empty string")
