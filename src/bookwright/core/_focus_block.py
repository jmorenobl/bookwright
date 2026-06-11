"""The ``[focus]`` manifest block model (FR-001, FR-008, FR-011, FR-012).

Extracted from ``manifest.py`` so that module stays under the Principle IV
500-line ceiling, mirroring ``_research_block.py``. ``Manifest`` imports
:class:`FocusBlock` and exposes it as ``Manifest.focus``; the public surface
re-exports it from ``bookwright.core``.

Unlike ``ResearchBlock`` (all fields defaulted, attached via ``default_factory``),
``[focus]`` is entirely optional but its ``target``/``updated_at`` are **required
when the block is present**, so it is attached as ``focus: FocusBlock | None =
None`` — ``None`` is the canonical "no ``[focus]``" encoding (research D1).
"""

from __future__ import annotations

import datetime
import re

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_core import PydanticCustomError

_ISO_CALENDAR_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


class FocusBlock(BaseModel):
    """``[focus]`` block — the author's current working intent.

    ``extra="forbid", strict=True`` matches every sibling block — an unknown key
    or a non-string ``target``/``notes`` is a validation error. ``target`` must be
    non-empty/non-whitespace; ``updated_at`` must be an ISO 8601 calendar date
    ``YYYY-MM-DD`` (no time/timezone), CLI-stamped on every write.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    target: str
    notes: str = ""
    updated_at: str

    @field_validator("target", mode="after")
    @classmethod
    def _check_target(cls, value: str) -> str:
        """Reject an empty/whitespace-only ``target`` (FR-008, FR-012).

        The command rejects an empty ``--target`` *before* constructing a block
        (so the manifest is left unchanged); this is the second line of defence
        covering a hand-edited manifest.
        """

        if not value.strip():
            raise PydanticCustomError("empty", "target must be a non-empty string")
        return value

    @field_validator("updated_at", mode="before")
    @classmethod
    def _accept_toml_date(cls, value: object) -> object:
        """Accept TOML's native (unquoted) date — the idiomatic TOML spelling.

        ``updated_at = 2026-06-11`` parses to a ``datetime.date``, which
        ``strict=True`` would otherwise reject with a generic "should be a valid
        string" *before* the bespoke ``not_iso_date`` validator could fire —
        bricking every manifest-loading command over a spelling that is a valid
        ISO 8601 calendar date. Normalizing it to its ``isoformat()`` string here
        keeps the stored type a string (Principle I, research D2) without
        rejecting the natural hand-edit. A ``datetime`` (date *with* time) stays
        rejected — the clarification fixed the no-time/no-timezone form.
        """

        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            return value.isoformat()
        return value

    @field_validator("updated_at", mode="after")
    @classmethod
    def _check_updated_at(cls, value: str) -> str:
        """Require the exact ``YYYY-MM-DD`` shape *and* a valid calendar date (FR-001, FR-011).

        ``date.fromisoformat`` alone accepts other ISO 8601 spellings (e.g.
        ``2026-W01-1``), so the regex pins the calendar-date form the
        clarification fixed before the date-validity check. Stored as a string —
        never coerced to ``date`` — so the author's exact bytes round-trip
        (Principle I, research D2).
        """

        try:
            if not _ISO_CALENDAR_DATE.fullmatch(value):
                raise ValueError(value)
            datetime.date.fromisoformat(value)
        except ValueError as exc:
            raise PydanticCustomError(
                "not_iso_date",
                "updated_at must be an ISO 8601 calendar date YYYY-MM-DD",
            ) from exc
        return value
