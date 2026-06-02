"""Shared ``SKILL.md`` materializer (FR-001..FR-020).

``generate_skill_md`` turns one packaged source command into a per-skill
directory ``<skills_dir>/<command>/SKILL.md`` with authoritative frontmatter, the
source body (only ``{ARGS}`` → ``$ARGUMENTS`` substituted), and its cited
``references/`` copied alongside — then lints the result. All *authoring*
validation runs strictly **before** the first filesystem write, so a rejected
source leaves zero on-disk state; a lint failure is the only post-write error and
deletes its own half-written dir.

Every directory and file it creates is recorded through a ``FileLedger`` so
``init`` can roll the whole materialization back (FR-019), even over a
pre-existing ``skills_dir``.
"""

from __future__ import annotations

import re
import shutil
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

import bookwright
from bookwright.integrations.constants import DEFAULT_SKILL_LICENSE
from bookwright.integrations.descriptions import get_description
from bookwright.integrations.errors import SkillMaterializationError
from bookwright.integrations.lint import lint_skill_md
from bookwright.io.frontmatter import parse_frontmatter
from bookwright.io.fs import mkdir_tracked, write_bytes_atomic

if TYPE_CHECKING:
    from bookwright.integrations.base import SkillsIntegration
    from bookwright.io.fs import FileLedger

#: Matches a ``references/<file>.md`` citation anywhere in a source body.
_REFERENCE_CITATION = re.compile(r"references/([\w-]+)\.md")

#: Tokens that MUST NOT survive the body transform (SC-003).
_RESIDUAL_TOKENS = ("{ARGS}", "{SCRIPT}")


def iter_command_sources() -> list[Traversable]:
    """Yield the packaged source command ``*.md`` (excludes ``references/``, R4).

    Enumerates the top level of ``bookwright.resources.commands`` — the whole
    resources tree is force-included in the wheel, so this survives both editable
    and wheel installs.
    """

    commands = files("bookwright.resources").joinpath("commands")
    return sorted(
        (child for child in commands.iterdir() if child.is_file() and child.name.endswith(".md")),
        key=lambda node: node.name,
    )


def _transform_body(skill_name: str, body: str) -> str:
    """Substitute the sole ``{ARGS}`` token; reject any residual token (SC-003).

    Raises ``SkillMaterializationError`` (``residual_token``) rather than asserting,
    so the fail-loud guarantee survives ``python -O`` (which strips ``assert``).
    Pre-write, so a rejected source still leaves zero on-disk state.
    """

    transformed = body.replace("{ARGS}", "$ARGUMENTS")
    for token in _RESIDUAL_TOKENS:
        if token in transformed:
            raise SkillMaterializationError(
                skill=skill_name,
                rule="residual_token",
                detail=f"residual token {token!r} survived body transform",
            )
    return transformed


def _render_frontmatter(name: str, description: str, license_: str, version: str) -> str:
    """Render ordered ``name``/``description``/``license``/``metadata`` YAML frontmatter."""

    document: dict[str, object] = {
        "name": name,
        "description": description,
        "license": license_,
        "metadata": {"author": "bookwright", "version": version},
    }
    block = yaml.safe_dump(document, allow_unicode=True, sort_keys=False)
    return f"---\n{block}---\n"


def _resolve_references(skill_name: str, body: str) -> list[tuple[str, Traversable]]:
    """Resolve each distinct ``references/<file>.md`` cited in ``body`` (pure, no writes).

    A citation with no matching packaged source raises ``SkillMaterializationError``
    (``dangling_reference``) — before any directory is created. Returns the resolved
    ``(filename, source_node)`` copy-list consumed by :func:`_copy_references`.

    ``skill_name`` is the citing command's name, carried onto the error so the JSON
    envelope's ``skill`` field identifies the skill (not the missing reference file).
    """

    refs_root = files("bookwright.resources").joinpath("commands").joinpath("references")
    seen: dict[str, Traversable] = {}
    for match in _REFERENCE_CITATION.finditer(body):
        filename = f"{match.group(1)}.md"
        if filename in seen:
            continue
        node = refs_root.joinpath(filename)
        if not node.is_file():
            raise SkillMaterializationError(
                skill=skill_name,
                rule="dangling_reference",
                detail=f"cited reference {filename!r} has no packaged source",
            )
        seen[filename] = node
    return list(seen.items())


def _copy_references(
    skill_dir: Path,
    copy_list: list[tuple[str, Traversable]],
    ledger: FileLedger,
) -> None:
    """Write the already-resolved reference copy-list into ``skill_dir/references/``."""

    if not copy_list:
        return
    refs_target = skill_dir / "references"
    mkdir_tracked(refs_target, ledger)
    for filename, node in copy_list:
        write_bytes_atomic(refs_target / filename, node.read_bytes(), ledger)


def generate_skill_md(
    command_path: Traversable | Path,
    target_dir: Path,
    integration: SkillsIntegration,
    *,
    ledger: FileLedger,
) -> Path | None:
    """Materialize one source command into a per-skill directory.

    Returns the written ``SKILL.md`` path, or ``None`` if the skill already
    existed (idempotency skip). Raises ``SkillLintError`` on a lint failure (after
    removing the half-written skill dir). Raises ``SkillMaterializationError`` on a
    dangling reference or a frontmatter ``name`` ≠ filename-stem mismatch.
    """

    # `integration` is read structurally in v0 only via the shared roster; its
    # `supports_dynamic_context` flag is intentionally NOT acted on (FR-011).
    del integration

    name = Path(command_path.name).stem
    skill_dir = target_dir / name

    # Step 2 — idempotency (FR-014): never overwrite an existing skill.
    if (skill_dir / "SKILL.md").exists():
        return None

    source_text = command_path.read_text(encoding="utf-8")
    parsed = parse_frontmatter(source_text)

    # Step 1 — authoring invariant (FR-020): frontmatter name == filename stem.
    fm_name = parsed.metadata.get("name")
    if fm_name != name:
        raise SkillMaterializationError(
            skill=name,
            rule="name_frontmatter_mismatch",
            detail=f"frontmatter name {fm_name!r} != filename stem {name!r}",
        )

    # Step 3 — authoritative description (R3, FR-004). The 1024-char cap is owned
    # by get_description and re-enforced loudly by lint_skill_md's Rule 3 below.
    description = get_description(name, parsed.metadata.get("description", ""))

    # Step 4 — body transform (sole token substitution).
    body = _transform_body(name, parsed.body)

    # Step 5 — resolve cited references (pure; a dangling ref aborts pre-write).
    copy_list = _resolve_references(name, body)

    # Step 6 — frontmatter (honour a source-declared license, else the design default).
    license_ = parsed.metadata.get("license", DEFAULT_SKILL_LICENSE)
    frontmatter = _render_frontmatter(name, description, license_, bookwright.__version__)
    skill_md_payload = (frontmatter + body).encode("utf-8")

    # Step 7 — the single first mutation point. Every created path is recorded.
    mkdir_tracked(skill_dir, ledger)
    skill_md = skill_dir / "SKILL.md"
    write_bytes_atomic(skill_md, skill_md_payload, ledger)
    _copy_references(skill_dir, copy_list, ledger)

    # Lint the result; on failure remove this skill dir and re-raise (FR-016).
    try:
        lint_skill_md(skill_dir)
    except Exception:
        shutil.rmtree(skill_dir, ignore_errors=True)
        raise

    return skill_md
