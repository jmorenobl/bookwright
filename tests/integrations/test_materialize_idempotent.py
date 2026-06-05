"""per-``SKILL.md`` idempotency (FR-014, SC-005, A-005)."""

from __future__ import annotations

import shutil
from importlib.resources.abc import Traversable
from pathlib import Path

from bookwright.core import Manifest
from bookwright.integrations import ClaudeIntegration
from bookwright.integrations.materialize import generate_skill_md, iter_command_sources
from bookwright.io.fs import NullLedger


def _bible_source() -> Traversable:
    return next(s for s in iter_command_sources() if Path(s.name).stem == "bookwright-bible")


def test_existing_skill_is_never_overwritten(tmp_path: Path) -> None:
    integration = ClaudeIntegration()
    source = _bible_source()

    first = generate_skill_md(source, tmp_path, integration, ledger=NullLedger())
    assert first is not None

    # Hand-edit the materialized skill.
    edited = "EDITED BY USER\n"
    first.write_text(edited, encoding="utf-8")

    # Re-run: the existing SKILL.md is skipped (returns None) and left byte-identical.
    second = generate_skill_md(source, tmp_path, integration, ledger=NullLedger())
    assert second is None
    assert first.read_text(encoding="utf-8") == edited


def test_deleted_skill_is_regenerated_others_untouched(
    tmp_project: Path, minimal_manifest: Manifest
) -> None:
    integration = ClaudeIntegration()
    integration.setup(tmp_project, minimal_manifest, None)
    skills_dir = tmp_project / ".claude/skills"

    # Snapshot one neighbour skill's bytes.
    neighbour = skills_dir / "bookwright-constitution" / "SKILL.md"
    neighbour_bytes = neighbour.read_bytes()

    # Delete one skill entirely and re-run setup().
    shutil.rmtree(skills_dir / "bookwright-bible")
    integration.setup(tmp_project, minimal_manifest, None)

    # Only the deleted skill is recreated, incl. its references/.
    assert (skills_dir / "bookwright-bible" / "SKILL.md").is_file()
    assert (skills_dir / "bookwright-bible" / "references").is_dir()
    # The neighbour was not touched.
    assert neighbour.read_bytes() == neighbour_bytes
