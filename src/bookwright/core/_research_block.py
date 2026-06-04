"""The ``[research]`` manifest block model (US2, FR-011..FR-016).

Extracted from ``manifest.py`` so that module stays under the Principle IV
500-line ceiling (it is already 535 lines). ``Manifest`` imports
:class:`ResearchBlock` and exposes it as ``Manifest.research``; the public surface
re-exports it from ``bookwright.core``.

The three reliability values are duplicated from
``golem.namespaces.RELIABILITY_IRI`` **on purpose**: ``core`` must not import
``golem`` (layer direction, and the registry already late-imports to avoid a
cycle). A unit test asserts the ``Literal`` stays in sync with that vocabulary
(RB-8, research §R5) — the same anti-drift discipline as the SC-009 gate.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from bookwright.core.iso639_1 import ISO_639_1_CODES


class ResearchBlock(BaseModel):
    """``[research]`` block — optional research-system configuration.

    All three fields carry documented defaults, so a manifest **without** a
    ``[research]`` block loads with the same values an explicit default block
    would produce (FR-012). ``extra="forbid", strict=True`` matches every sibling
    block — an unknown key inside ``[research]`` is a validation error.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    enabled: bool = True
    source_languages: list[str] = Field(default_factory=list)
    min_reliability_for_anchor: Literal["alta", "media", "baja"] = "media"

    @field_validator("source_languages", mode="after")
    @classmethod
    def _check_source_languages(cls, value: list[str]) -> list[str]:
        """Reject any non-ISO-639-1 entry, naming ``source_languages[i]`` (FR-016).

        Mirrors ``BookBlock._check_language``; the ``index``/``value`` context is
        spliced into the public ``field_path`` by ``_translate_validation_error``.
        """

        for index, entry in enumerate(value):
            if entry not in ISO_639_1_CODES:
                raise PydanticCustomError(
                    "not_iso_639_1",
                    "source_languages[{index}] '{value}' is not a valid ISO 639-1 code",
                    {"index": index, "value": entry},
                )
        return value
