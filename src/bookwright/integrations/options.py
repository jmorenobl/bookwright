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


def parse_options(  # noqa: PLR0912, PLR0915 — small hand-rolled state machine, one branch per FR-016..FR-021 rule.
    raw: str | None,
    integration_cls: type[SkillsIntegration],
) -> dict[str, str | bool]:
    """Parse ``--integration-options`` raw input against an integration's options().

    Returns a dict keyed by each captured option's normalized identifier
    (``--skills-dir`` → ``"skills_dir"``). Empty / ``None`` / whitespace
    input skips the tokenization loop and the required-flag check (FR-020
    wins over FR-021), but declared defaults are still applied (R8). All
    error paths raise structured exceptions; nothing is written to
    stdout/stderr.
    """

    # Validate every declared descriptor up front (FR-015, R9).
    # Runs BEFORE the empty-input short-circuit so a broken options()
    # declaration surfaces on the first parse_options call, not only when
    # the user happens to pass non-empty --integration-options.
    declared = integration_cls.options()
    for option in declared:
        _validate_descriptor(option)

    # R14 — two IntegrationOption descriptors with the same flag must not
    # silently coalesce in the lookup dict; surface the programming error
    # explicitly so the integration author fixes their options() list.
    flags = [opt.flag for opt in declared]
    if len(set(flags)) != len(flags):
        dup = next(f for f in flags if flags.count(f) > 1)
        raise InvalidOptionDeclarationError(rule="duplicate_flag", value=dup)

    # R15 — two flags that normalize to the same identifier
    # (e.g. `--skills-dir` and `--skills_dir` both → `skills_dir`) would
    # silently last-wins in `result`; detect at declaration time. Build
    # a flag→ident map so the error names BOTH colliding flags.
    idents: dict[str, str] = {}
    for flag in flags:
        ident = _normalize_identifier(flag)
        if ident in idents.values():
            collider = next(f for f, i in idents.items() if i == ident)
            raise InvalidOptionDeclarationError(
                rule="colliding_identifiers",
                value=f"{collider} and {flag} both normalize to {ident!r}",
            )
        idents[flag] = ident

    result: dict[str, str | bool] = {}

    if raw is not None and raw.strip() != "":
        lookup: dict[str, IntegrationOption] = {opt.flag: opt for opt in declared}
        declared_flags = sorted(lookup.keys())

        try:
            tokens = shlex.split(raw, posix=True)
        except ValueError as exc:
            # `shlex.split` raises `ValueError("No closing quotation")` on
            # unbalanced quotes. Translate into the structured-error contract
            # FR-035 promises — otherwise iteration-4's `--json` envelope sees
            # a bare ValueError without `code`/`message` keys (R7).
            raise MalformedOptionError(rule="malformed_shell_syntax", value=raw) from exc

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
                    # R11 — `--flag=` (empty inline value) is treated as a
                    # missing value, symmetric with bare `--flag`. Without
                    # this guard the empty string slipped through to the
                    # consumer and the failure surfaced later (e.g., as
                    # `resolves_to_project_root` in setup() when the
                    # consumer wrapped it as Path('')).
                    if value == "":
                        raise MalformedOptionError(rule="missing_value", value=flag)
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

    # R8 — apply declared defaults for opts the user did not supply. Runs
    # in both paths (empty + non-empty input) so an integration that
    # declares `default='X'` always sees `X` when the flag is omitted.
    for option in declared:
        if option.default is not None:
            ident = _normalize_identifier(option.flag)
            if ident not in result:
                result[ident] = option.default

    # Required-flag enforcement runs after defaults so `required=True,
    # default='x'` is always satisfied (FR-021 only fires for required
    # opts without a default that the user also omitted). Empty-input
    # short-circuit at top of branch skips this — FR-020 wins.
    if raw is not None and raw.strip() != "":
        for option in declared:
            if option.required and _normalize_identifier(option.flag) not in result:
                raise MalformedOptionError(rule="missing_required", value=option.flag)

    return result
