"""Ad-hoc agentskills.io linter for a materialized skill directory (FR-015).

``lint_skill_md`` enforces the agentskills.io invariants on one
``<skills_dir>/<command>/SKILL.md`` and raises :class:`SkillLintError` on the
**first** violation (Principle VII — fail loudly, never silently truncate or
auto-fix). It is pure: it reads the file, it never mutates the filesystem.

The full validation system is iteration 11; this module is the minimum gate
needed for Principle VII (and is reused by that later system).
"""

from __future__ import annotations

import math
import re
import shlex
from pathlib import Path

from bookwright.integrations.constants import (
    INJECTION_READ_COMMANDS,
    SKILL_BODY_MAX_TOKENS,
    SKILL_DESCRIPTION_MAX_LENGTH,
    SKILL_NAME_MAX_LENGTH,
)
from bookwright.integrations.errors import SkillLintError
from bookwright.io.frontmatter import parse_frontmatter

#: Matches a `` !`<cmd>` `` dynamic-context injection in a skill body.
_INJECTION = re.compile(r"!`([^`]*)`")


def approx_tokens(text: str) -> int:
    """Token estimate for the Tier-2 body budget (R6).

    Counts with ``tiktoken``'s ``cl100k_base`` encoding when the package is
    importable; otherwise falls back to the deterministic ``ceil(len / 4)``
    char heuristic — the same heuristic as the iteration-8 source-side gate, so
    a body that passed iteration 8 passes here. ``tiktoken`` is an optional
    import, never a runtime dependency.
    """

    try:
        import tiktoken  # type: ignore[import-not-found,import-untyped,unused-ignore]  # noqa: PLC0415
    except ImportError:
        return math.ceil(len(text) / 4)
    return len(tiktoken.get_encoding("cl100k_base").encode(text))


def _check_injections(skill_name: str, body: str) -> None:
    """Rule 5 — deny-by-default allowlist for `` !`…` `` injections (FR-013).

    Enumerate the only two valid shapes and reject everything else:
      - ``argv[0] == "bookwright"`` (the stable SKILL.md ↔ CLI contract), or
      - ``argv[0]`` in :data:`INJECTION_READ_COMMANDS` AND no argument is an
        absolute (``/``) or home-relative (``~``) path.

    Pure/read-only — the invariant is about the *shape* of the injection, never
    whether the target currently exists on disk.
    """

    for match in _INJECTION.finditer(body):
        cmd = match.group(1)
        try:
            argv = shlex.split(cmd)
        except ValueError as exc:
            # Unbalanced quotes etc. — surface as a structured lint failure
            # rather than letting shlex's ValueError escape the JSON envelope
            # (Principle IX). lint_skill_md is user-edit-facing.
            raise SkillLintError(
                skill=skill_name,
                rule="forbidden_injection",
                detail=f"unparseable dynamic-context injection {cmd!r}: {exc}",
            ) from exc
        if not argv:
            raise SkillLintError(
                skill=skill_name,
                rule="forbidden_injection",
                detail=f"empty dynamic-context injection: {cmd!r}",
            )
        if argv[0] == "bookwright":
            continue
        if argv[0] in INJECTION_READ_COMMANDS:
            bad = [a for a in argv[1:] if a.startswith("/") or a.startswith("~")]
            if bad:
                raise SkillLintError(
                    skill=skill_name,
                    rule="forbidden_injection",
                    detail=f"read command targets a non-project path: {bad!r} in {cmd!r}",
                )
            continue
        raise SkillLintError(
            skill=skill_name,
            rule="forbidden_injection",
            detail=f"injection invokes a non-allowlisted executable: {argv[0]!r} in {cmd!r}",
        )


def lint_skill_md(skill_dir: Path) -> None:
    """Validate one materialized skill dir against the agentskills.io spec.

    Raises :class:`SkillLintError` (``rule`` + ``detail``) on the FIRST violation.
    Returns ``None`` when compliant. Pure read-only; never mutates the filesystem.
    """

    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    # Rule 1 — invalid_frontmatter: SKILL.md exists, valid YAML fence, non-empty metadata.
    if not skill_md.is_file():
        raise SkillLintError(
            skill=skill_name,
            rule="invalid_frontmatter",
            detail=f"missing SKILL.md at {skill_md}",
        )
    parsed = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    metadata = parsed.metadata
    if not metadata:
        raise SkillLintError(
            skill=skill_name,
            rule="invalid_frontmatter",
            detail="empty or unparseable frontmatter metadata",
        )

    # Rule 2 — name_mismatch: metadata["name"] == dir and < SKILL_NAME_MAX_LENGTH.
    # Once name == skill_name is established, the length check is on the (always
    # non-empty) directory name, so no separate type/lower-bound guard is needed.
    name = metadata.get("name")
    if name != skill_name:
        raise SkillLintError(
            skill=skill_name,
            rule="name_mismatch",
            detail=f"frontmatter name {name!r} != directory {skill_name!r}",
        )
    if len(skill_name) >= SKILL_NAME_MAX_LENGTH:
        raise SkillLintError(
            skill=skill_name,
            rule="name_mismatch",
            detail=f"name length {len(skill_name)} not below {SKILL_NAME_MAX_LENGTH}",
        )

    # Rule 3 — description_too_long: 0 < len(description) < SKILL_DESCRIPTION_MAX_LENGTH.
    description = metadata.get("description")
    if not isinstance(description, str) or not (
        0 < len(description) < SKILL_DESCRIPTION_MAX_LENGTH
    ):
        length = len(description) if isinstance(description, str) else None
        raise SkillLintError(
            skill=skill_name,
            rule="description_too_long",
            detail=f"len={length} not in (0, {SKILL_DESCRIPTION_MAX_LENGTH})",
        )

    # Rule 4 — body_over_budget: approx_tokens(body) < SKILL_BODY_MAX_TOKENS.
    tokens = approx_tokens(parsed.body)
    if tokens >= SKILL_BODY_MAX_TOKENS:
        raise SkillLintError(
            skill=skill_name,
            rule="body_over_budget",
            detail=f"approx_tokens={tokens} >= {SKILL_BODY_MAX_TOKENS}",
        )

    # Rule 5 — forbidden_injection: deny-by-default allowlist (FR-013).
    _check_injections(skill_name, parsed.body)
