"""FR-021a ``PROJECT_NAME`` validation.

Pure functions only; no filesystem side-effects. Surfaces structured
``InvalidProjectNameError`` so the caller can branch on ``rule`` instead of
prose. Rules per research §R3 and contract §4.
"""

from __future__ import annotations

from typing import Literal

ProjectNameRule = Literal[
    "empty",
    "path_separator",
    "dot_or_dotdot",
    "leading_dot",
    "too_long",
    "reserved_name",
]

_MAX_LENGTH = 100

_WINDOWS_RESERVED: frozenset[str] = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
)


class InvalidProjectNameError(Exception):
    """Raised when ``PROJECT_NAME`` violates one of the FR-021a rules."""

    code = "invalid_project_name"

    def __init__(self, *, value: str, rule: ProjectNameRule) -> None:
        self.value = value
        self.rule = rule
        super().__init__(f"invalid project name {value!r}; rule: {rule}")


def _is_reserved(candidate: str) -> bool:
    return candidate.upper() in _WINDOWS_RESERVED


def validate_project_name(value: str) -> str:
    """Validate and normalise a raw ``PROJECT_NAME``.

    Returns the value with leading/trailing whitespace stripped. Raises
    ``InvalidProjectNameError`` on any rule violation. The check order is
    fixed: empty → path_separator → dot_or_dotdot → leading_dot → too_long
    → reserved_name. The first failing rule wins (so ``"."`` is
    ``dot_or_dotdot``, not ``leading_dot``).
    """

    stripped = value.strip()
    if not stripped:
        raise InvalidProjectNameError(value=value, rule="empty")
    if "/" in stripped or "\\" in stripped:
        raise InvalidProjectNameError(value=stripped, rule="path_separator")
    if stripped in {".", ".."}:
        raise InvalidProjectNameError(value=stripped, rule="dot_or_dotdot")
    if stripped.startswith("."):
        raise InvalidProjectNameError(value=stripped, rule="leading_dot")
    if len(stripped) > _MAX_LENGTH:
        raise InvalidProjectNameError(value=stripped, rule="too_long")
    if _is_reserved(stripped):
        raise InvalidProjectNameError(value=stripped, rule="reserved_name")
    return stripped


def check_slug_not_reserved(slug: str) -> str:
    """Re-check a slug against the reserved-name list (R3).

    Same exception family so callers can fold both checks into one
    error envelope.
    """

    if not slug:
        raise InvalidProjectNameError(value=slug, rule="empty")
    if _is_reserved(slug):
        raise InvalidProjectNameError(value=slug, rule="reserved_name")
    return slug
