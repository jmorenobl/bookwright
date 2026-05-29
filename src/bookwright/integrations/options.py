"""``IntegrationOption`` declarative descriptor and ``parse_options`` parser.

The descriptor is intentionally validation-free at construction time
(per research R1) — structural validation runs the first time the parser
introspects an integration's ``options()`` list, surfacing as
``InvalidOptionDeclarationError`` (FR-015).
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from bookwright.integrations.errors import (
    InvalidOptionDeclarationError,
    MalformedOptionError,
    UnknownOptionError,
)

if TYPE_CHECKING:
    from bookwright.integrations.base import SkillsIntegration


_VALID_TYPES: frozenset[str] = frozenset({"flag", "string"})


@dataclass(frozen=True)
class IntegrationOption:
    """Immutable declarative descriptor for one ``--integration-options`` flag.

    Subclasses return a list of these from their ``options()`` classmethod.
    The ``flag`` field MUST start with ``"--"`` (FR-012). The ``type`` field
    drives parser behaviour: ``"flag"`` is presence-only (boolean),
    ``"string"`` consumes the next token as its value.
    """

    flag: str
    type: Literal["flag", "string"] = "flag"
    required: bool = False
    default: str | None = None
    help: str = ""


def _validate_descriptor(option: IntegrationOption) -> None:
    """First-introspection validation of one declared option descriptor (FR-015)."""

    if not option.flag.startswith("--"):
        raise InvalidOptionDeclarationError(rule="bad_flag_prefix", value=option.flag)
    if option.type not in _VALID_TYPES:
        raise InvalidOptionDeclarationError(rule="bad_type", value=str(option.type))


def _normalize_identifier(flag: str) -> str:
    """``--skills-dir`` → ``skills_dir``."""

    return flag.removeprefix("--").replace("-", "_")


def parse_options(  # noqa: PLR0912 — small hand-rolled state machine, one branch per FR-016..FR-021 rule.
    raw: str | None,
    integration_cls: type[SkillsIntegration],
) -> dict[str, str | bool]:
    """Parse ``--integration-options`` raw input against an integration's options().

    Returns a dict keyed by each captured option's normalized identifier
    (``--skills-dir`` → ``"skills_dir"``). Empty / ``None`` / whitespace
    input short-circuits to ``{}`` (FR-020, R6). All error paths raise
    structured exceptions; nothing is written to stdout/stderr.
    """

    if raw is None or raw.strip() == "":
        return {}

    # Validate every declared descriptor up front (FR-015).
    declared = integration_cls.options()
    for option in declared:
        _validate_descriptor(option)

    lookup: dict[str, IntegrationOption] = {opt.flag: opt for opt in declared}
    declared_flags = sorted(lookup.keys())

    tokens = shlex.split(raw, posix=True)

    result: dict[str, str | bool] = {}
    seen: set[str] = set()

    index = 0
    while index < len(tokens):
        token = tokens[index]
        if "=" in token and token.startswith("--"):
            flag, _, value = token.partition("=")
            has_inline_value = True
        else:
            flag = token
            value = ""
            has_inline_value = False

        if flag not in lookup:
            raise UnknownOptionError(
                integration=integration_cls.key,
                value=flag,
                valid=declared_flags,
            )

        if flag in seen:
            raise MalformedOptionError(rule="duplicate_flag", value=flag)
        seen.add(flag)

        option = lookup[flag]

        if option.type == "string":
            if has_inline_value:
                result[_normalize_identifier(flag)] = value
                index += 1
                continue
            if index + 1 >= len(tokens):
                raise MalformedOptionError(rule="missing_value", value=flag)
            result[_normalize_identifier(flag)] = tokens[index + 1]
            index += 2
            continue

        # type == "flag"
        if has_inline_value:
            raise MalformedOptionError(rule="unexpected_value", value=flag)
        result[_normalize_identifier(flag)] = True
        index += 1

    # Required-flag enforcement runs after tokenization (FR-021).
    for option in declared:
        if option.required and _normalize_identifier(option.flag) not in result:
            raise MalformedOptionError(rule="missing_required", value=option.flag)

    return result
