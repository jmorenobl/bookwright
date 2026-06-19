"""``generate_skill_md`` contract — generation, roster, tokens, refs, ledger.

Covers FR-007/008/009/010/017/018/019/020, SC-003/004/007.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import bookwright
from bookwright.integrations import ClaudeIntegration
from bookwright.integrations.constants import (
    NEXT_STEPS_BOILERPLATE,
    STATUS_INJECTION_CLAUDE,
)
from bookwright.integrations.descriptions import SKILL_DESCRIPTIONS
from bookwright.integrations.errors import SkillMaterializationError
from bookwright.integrations.generic import GenericIntegration
from bookwright.integrations.lint import lint_skill_md
from bookwright.integrations.materialize import generate_skill_md, iter_command_sources
from bookwright.io.frontmatter import parse_frontmatter
from bookwright.io.fs import NullLedger

_ROSTER = {
    "bookwright-constitution",
    "bookwright-bible",
    "bookwright-outline",
    "bookwright-scenes",
    "bookwright-draft",
    "bookwright-synopsis",
    "bookwright-clarify",
    "bookwright-analyze",
    "bookwright-continuity",
    "bookwright-checklist",
    "bookwright-research",
    "bookwright-verify",
}

# FR-003 — the phase-transition skills that hardcode the focus handoff.
_FOCUS_HANDOFF_SKILLS = {"bookwright-bible", "bookwright-outline"}
_FOCUS_HANDOFF_INSTRUCTION = "bookwright focus set --target"


class RecordingLedger:
    """A FileLedger fake that records every path it is asked to track."""

    def __init__(self) -> None:
        self.new_files: list[Path] = []
        self.new_dirs: list[Path] = []
        self.overwrites: list[Path] = []

    def record_new_file(self, target: Path) -> None:
        self.new_files.append(target)

    def record_new_directory(self, target: Path) -> None:
        self.new_dirs.append(target)

    def record_overwrite(self, target: Path) -> Path:
        self.overwrites.append(target)
        return target


def _write_source(path: Path, *, name: str, body: str, description: str = "trigger text") -> Path:
    path.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n{body}",
        encoding="utf-8",
    )
    return path


# ---------- roster ----------


def test_iter_command_sources_is_exactly_the_roster() -> None:
    names = {Path(node.name).stem for node in iter_command_sources()}
    assert names == _ROSTER
    # references/ subdir is skipped (only *.md files at the top level).
    assert all(node.name.endswith(".md") for node in iter_command_sources())


# ---------- focus handoff (FR-003) ----------


@pytest.mark.parametrize("skill_name", sorted(_FOCUS_HANDOFF_SKILLS))
def test_phase_transition_skills_carry_focus_handoff(skill_name: str, tmp_path: Path) -> None:
    """FR-003 — bible/outline hardcode `bookwright focus set --target`, in source and output."""

    integration = ClaudeIntegration()
    source = next(s for s in iter_command_sources() if Path(s.name).stem == skill_name)

    source_body = parse_frontmatter(source.read_text(encoding="utf-8")).body
    assert _FOCUS_HANDOFF_INSTRUCTION in source_body

    written = generate_skill_md(source, tmp_path, integration, ledger=NullLedger())
    assert written is not None
    assert _FOCUS_HANDOFF_INSTRUCTION in written.read_text(encoding="utf-8")


def test_only_phase_transition_skills_carry_focus_handoff() -> None:
    """FR-003 — the focus handoff lives in *exactly* bible/outline, nowhere else."""

    carriers = {
        Path(source.name).stem
        for source in iter_command_sources()
        if _FOCUS_HANDOFF_INSTRUCTION in parse_frontmatter(source.read_text(encoding="utf-8")).body
    }
    assert carriers == _FOCUS_HANDOFF_SKILLS


# ---------- generation / frontmatter / body transform ----------


def test_each_source_materializes_with_expected_frontmatter_and_body(tmp_path: Path) -> None:
    integration = ClaudeIntegration()
    for source in iter_command_sources():
        name = Path(source.name).stem
        written = generate_skill_md(source, tmp_path, integration, ledger=NullLedger())
        assert written is not None
        assert written == tmp_path / name / "SKILL.md"

        parsed = parse_frontmatter(written.read_text(encoding="utf-8"))
        meta = parsed.metadata
        assert meta["name"] == name
        assert meta["description"] == SKILL_DESCRIPTIONS[name]
        assert meta["license"] == "Apache-2.0"
        assert meta["metadata"] == {"author": "bookwright", "version": bookwright.__version__}

        source_body = parse_frontmatter(source.read_text(encoding="utf-8")).body
        expected_core_body = source_body.replace("{ARGS}", "$ARGUMENTS")
        assert expected_core_body in parsed.body
        assert parsed.body.startswith(STATUS_INJECTION_CLAUDE)
        assert parsed.body.endswith(NEXT_STEPS_BOILERPLATE.strip())
        assert "{ARGS}" not in parsed.body
        assert "{SCRIPT}" not in parsed.body


def test_json_calls_survive_verbatim(tmp_path: Path) -> None:
    """FR-009 — known agent-facing call is preserved exactly in bodies that carry it."""

    integration = ClaudeIntegration()
    found = False
    for source in iter_command_sources():
        source_body = parse_frontmatter(source.read_text(encoding="utf-8")).body
        if "bookwright graph build --json" not in source_body:
            continue
        found = True
        written = generate_skill_md(source, tmp_path, integration, ledger=NullLedger())
        assert written is not None
        assert "bookwright graph build --json" in written.read_text(encoding="utf-8")
    assert found, "expected at least one source to carry `bookwright graph build --json`"


# ---------- references ----------


def test_cited_references_are_copied_per_skill(tmp_path: Path) -> None:
    """SC-004 — bookwright-bible cites several references; each is copied alongside."""

    integration = ClaudeIntegration()
    source = next(s for s in iter_command_sources() if Path(s.name).stem == "bookwright-bible")
    written = generate_skill_md(source, tmp_path, integration, ledger=NullLedger())
    assert written is not None
    refs_dir = written.parent / "references"
    copied = {p.name for p in refs_dir.iterdir()}
    # bible cites these four (golem-character/relationships/events-timeline + pending-protocol).
    assert copied == {
        "golem-character.md",
        "golem-relationships.md",
        "golem-events-timeline.md",
        "pending-protocol.md",
    }


def test_bible_skill_teaches_location_frontmatter(tmp_path: Path) -> None:
    """FR-010 — the materialized bookwright-bible skill prescribes location `name:`/`setting:`.

    The SKILL.md is generated from the packaged source command, so the iteration-025
    edit (locations get `name:` + optional `setting:`, retiring the v0 "no se indexa"
    shortcut) must flow through into the rendered skill body, with its YAML
    front-matter and bilingual author triggers intact.
    """
    integration = ClaudeIntegration()
    source = next(s for s in iter_command_sources() if Path(s.name).stem == "bookwright-bible")
    written = generate_skill_md(source, tmp_path, integration, ledger=NullLedger())
    assert written is not None
    body = written.read_text(encoding="utf-8")
    assert "bible/locations/<slug>.md" in body
    assert "`setting:`" in body
    # The retired v0 shortcut wording is gone.
    assert "no se\n   indexa en v0" not in body and "no se indexa en v0" not in body
    # Front-matter + bilingual triggers survive (the lint gate enforces the YAML shape).
    assert body.startswith("---\n")
    assert "name: bookwright-bible" in body
    assert "location sheets" in body  # EN trigger
    assert "localizaciones" in body  # ES trigger


def test_bible_skill_teaches_object_frontmatter(tmp_path: Path) -> None:
    """FR-008/FR-009 — the materialized bookwright-bible skill prescribes object `name:`.

    The iteration-026 edit (objects get `bible/objects/<slug>.md` with a required
    `name:`, retiring the G16 orphan) must flow through into the rendered skill body,
    with `bible/objects/` listed among the entity directories and files-to-write and
    the bilingual triggers intact.
    """
    integration = ClaudeIntegration()
    source = next(s for s in iter_command_sources() if Path(s.name).stem == "bookwright-bible")
    written = generate_skill_md(source, tmp_path, integration, ledger=NullLedger())
    assert written is not None
    body = written.read_text(encoding="utf-8")
    assert "bible/objects/<slug>.md" in body
    assert "bible/objects/*.md" in body  # files-to-write listing
    assert "`bible/objects/`" in body  # entity-directory listing
    # Front-matter + bilingual triggers survive.
    assert body.startswith("---\n")
    assert "location sheets" in body  # EN trigger
    assert "localizaciones" in body  # ES trigger


@pytest.mark.parametrize("integration", [ClaudeIntegration(), GenericIntegration()])
def test_outline_skill_teaches_unit_cards(
    integration: ClaudeIntegration | GenericIntegration, tmp_path: Path
) -> None:
    """SC-007/A1 — the materialized bookwright-outline skill prescribes `outline/units/` cards.

    The iteration-028 edit (one card per narrative unit with `name`/`functions`/`roles`
    front-matter, ingested to the graph) must flow through into the rendered skill body
    for **both** integrations, with its YAML front-matter and bilingual author triggers
    intact, and still lint clean.
    """
    source = next(s for s in iter_command_sources() if Path(s.name).stem == "bookwright-outline")
    written = generate_skill_md(source, tmp_path, integration, ledger=NullLedger())
    assert written is not None
    body = written.read_text(encoding="utf-8")
    # The unit-card surface and its three front-matter keys are documented.
    assert "outline/units/" in body
    assert "`functions`" in body
    assert "`roles`" in body
    # Front-matter + bilingual triggers survive (the lint gate enforces the YAML shape).
    assert body.startswith("---\n")
    assert "name: bookwright-outline" in body
    assert "outline the plot" in body  # EN trigger
    assert "estructurar la trama" in body  # ES trigger
    lint_skill_md(written.parent)  # A1 — still lints clean


def test_dangling_reference_aborts_pre_write(tmp_path: Path) -> None:
    src = _write_source(
        tmp_path / "bookwright-x.md",
        name="bookwright-x",
        body="See `references/does-not-exist.md` for details.\n",
    )
    target = tmp_path / "out"
    target.mkdir()
    with pytest.raises(SkillMaterializationError) as exc:
        generate_skill_md(src, target, ClaudeIntegration(), ledger=NullLedger())
    assert exc.value.rule == "dangling_reference"
    # Zero on-disk state — the skill dir was never created.
    assert not (target / "bookwright-x").exists()


# ---------- authoring invariant ----------


def test_name_frontmatter_mismatch_aborts_pre_write(tmp_path: Path) -> None:
    src = _write_source(
        tmp_path / "bookwright-x.md",
        name="bookwright-WRONG",
        body="# body\n",
    )
    target = tmp_path / "out"
    target.mkdir()
    with pytest.raises(SkillMaterializationError) as exc:
        generate_skill_md(src, target, ClaudeIntegration(), ledger=NullLedger())
    assert exc.value.rule == "name_frontmatter_mismatch"
    assert not (target / "bookwright-x").exists()


# ---------- ledger recording (FR-019) ----------


def test_recording_ledger_captures_every_created_path(tmp_path: Path) -> None:
    integration = ClaudeIntegration()
    source = next(s for s in iter_command_sources() if Path(s.name).stem == "bookwright-bible")
    ledger = RecordingLedger()
    written = generate_skill_md(source, tmp_path, integration, ledger=ledger)
    assert written is not None

    recorded_files = set(ledger.new_files)
    recorded_dirs = set(ledger.new_dirs)

    skill_dir = tmp_path / "bookwright-bible"
    assert skill_dir in recorded_dirs
    assert (skill_dir / "references") in recorded_dirs
    assert written in recorded_files
    for ref in (skill_dir / "references").iterdir():
        assert ref in recorded_files


# ---------- containment ----------


def test_no_write_escapes_target_dir(tmp_path: Path) -> None:
    """SC-007 — every created path stays under target_dir."""

    integration = ClaudeIntegration()
    target = tmp_path / "skills"
    target.mkdir()
    for source in iter_command_sources():
        generate_skill_md(source, target, integration, ledger=NullLedger())
    for path in target.rglob("*"):
        assert path.is_relative_to(target)
