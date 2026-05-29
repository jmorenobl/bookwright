"""FR-021a ``PROJECT_NAME`` validation.

Pure functions only; no filesystem side-effects. Surfaces structured
``InvalidProjectNameError`` so the caller can branch on ``rule`` instead of
prose. Rules per research §R3 and contract §4.
"""

from __future__ import annotations

from typing import Literal

from bookwright.commands._init_envelope import emit_error

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


def check_mutex(project_name: str | None, here: bool, *, json_output: bool) -> None:
    """FR-002 — exactly one of ``PROJECT_NAME`` / ``--here`` is required.

    Emits a ``mutually_exclusive`` envelope and exits with code 2 on
    violation.
    """

    if project_name is not None and here:
        emit_error(
            code="mutually_exclusive",
            message="PROJECT_NAME and --here are mutually exclusive",
            details={},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )
    if project_name is None and not here:
        emit_error(
            code="mutually_exclusive",
            message="must specify PROJECT_NAME or --here",
            details={},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )


def parse_named_name(value: str, json_output: bool) -> str:
    """Run ``validate_project_name`` and translate failures to an envelope."""

    try:
        return validate_project_name(value)
    except InvalidProjectNameError as exc:
        emit_error(
            code=exc.code,
            message=str(exc),
            details={"value": exc.value, "rule": exc.rule},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )


def parse_here_basename(basename: str, json_output: bool) -> str:
    """Reduced FR-021a check for ``--here``: empty / path-separator / reserved only."""

    if not basename.strip():
        emit_error(
            code="invalid_project_name",
            message="current directory basename is empty",
            details={"value": basename, "rule": "empty"},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )
    if "/" in basename or "\\" in basename:
        emit_error(
            code="invalid_project_name",
            message=f"current directory basename {basename!r} contains a path separator",
            details={"value": basename, "rule": "path_separator"},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )
    try:
        check_slug_not_reserved(basename)
    except InvalidProjectNameError as exc:
        emit_error(
            code=exc.code,
            message=str(exc),
            details={"value": exc.value, "rule": exc.rule},
            exit_code=2,
            json_output=json_output,
            rolled_back=False,
        )
    return basename
