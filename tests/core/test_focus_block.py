"""The ``[focus]`` block model contract (FR-001, FR-008, FR-011, FR-012).

``FocusBlock`` is the authored focus state — ``target`` (non-empty), ``notes``
(defaults to ``""``), ``updated_at`` (ISO ``YYYY-MM-DD`` calendar date). It is
``extra="forbid", strict=True`` like every sibling block, and its field
validators surface ``empty`` / ``not_iso_date`` ``PydanticCustomError``s that
``_translate_validation_error`` renders as normal ``manifest_validation``
failures. See specs/019-focus-state/data-model.md.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from bookwright.core import FocusBlock


def _errors(exc: ValidationError) -> set[str]:
    """The set of Pydantic error ``type`` strings raised."""
    return {e["type"] for e in exc.errors()}


# --- valid block round-trips --------------------------------------------------


def test_valid_block_round_trips() -> None:
    block = FocusBlock(target="cap-04", notes="cerrar timeline", updated_at="2026-06-11")
    assert block.target == "cap-04"
    assert block.notes == "cerrar timeline"
    assert block.updated_at == "2026-06-11"


def test_notes_defaults_to_empty_string_when_omitted() -> None:
    block = FocusBlock(target="cap-04", updated_at="2026-06-11")
    assert block.notes == ""


# --- target validation (FR-008, FR-012) --------------------------------------


@pytest.mark.parametrize("bad", ["", "   ", "\t\n"])
def test_empty_or_whitespace_target_rejected(bad: str) -> None:
    with pytest.raises(ValidationError) as exc:
        FocusBlock(target=bad, updated_at="2026-06-11")
    assert "empty" in _errors(exc.value)


def test_non_string_target_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        FocusBlock(target=123, updated_at="2026-06-11")  # type: ignore[arg-type]
    assert "string_type" in _errors(exc.value)


# --- notes validation (FR-012) -----------------------------------------------


def test_non_string_notes_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        FocusBlock(target="cap-04", notes=123, updated_at="2026-06-11")  # type: ignore[arg-type]
    assert "string_type" in _errors(exc.value)


# --- updated_at shape + validity (FR-001, FR-011) ----------------------------


@pytest.mark.parametrize("bad", ["2026-W01-1", "2026-6-1", "2026/06/01", "nope", "20260601"])
def test_non_iso_calendar_shape_rejected(bad: str) -> None:
    with pytest.raises(ValidationError) as exc:
        FocusBlock(target="cap-04", updated_at=bad)
    assert "not_iso_date" in _errors(exc.value)


def test_impossible_date_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        FocusBlock(target="cap-04", updated_at="2026-13-40")
    assert "not_iso_date" in _errors(exc.value)


# --- block hygiene -----------------------------------------------------------


def test_unknown_key_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        FocusBlock(target="cap-04", updated_at="2026-06-11", surprise="x")  # type: ignore[call-arg]
    assert "extra_forbidden" in _errors(exc.value)
