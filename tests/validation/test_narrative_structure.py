"""``narrative_structure`` — orphan beats and unresolved roles.

Drives the validator over outline-aware graphs built by the ``conftest`` helpers
(``build_outline_indexer`` produces the ``G7``/``G9`` triples and outline
provenance). Rule a flags every ``G9_Narrative_Unit`` belonging to no
``G7_Narrative_Sequence`` via SPARQL; Rule c re-surfaces the outline ingestion's
``UnresolvedReference`` role misses; the configuration cases pin config/envelope
conformance. See contracts/narrative-structure-validator.md.
"""

from __future__ import annotations

from pathlib import Path

from bookwright.core.manifest import Manifest, ValidatorsBlock
from bookwright.indexers import RdflibIndexer
from bookwright.validation.base import Severity, Violation
from bookwright.validation.registry import discover_validators, resolve_active
from bookwright.validation.runner import run_validators
from bookwright.validation.validators.narrative_structure import NarrativeStructure
from tests.validation.conftest import (
    UnitSpec,
    build_indexer,
    load_context,
    write_project,
)


def _run(root: Path) -> list[Violation]:
    """The ``narrative_structure`` findings over a project's outline-aware graph."""
    return NarrativeStructure().validate(load_context(root), build_indexer(root, outline=True))


# --- User Story 1: orphan beat (Rule a) -------------------------------------


def test_orphan_beat_flagged_sequenced_not(project_root: Path) -> None:
    # One beat joins a sequence; one beat joins none → exactly the orphan is flagged.
    write_project(
        project_root,
        units=[
            UnitSpec("anchored", "Anchored Beat", sequence="Act I", order=1),
            UnitSpec("orphan", "Orphan Beat"),
        ],
    )
    findings = _run(project_root)
    assert len(findings) == 1
    (finding,) = findings
    assert finding.validator == "narrative_structure"
    assert finding.severity == Severity.warning
    assert "orphan-beat" in finding.message  # named by URI slug (research D4)
    assert finding.source is not None
    assert finding.source.startswith("outline/units/orphan.md")
    # The sequenced beat is never named.
    assert "anchored-beat" not in finding.message


def test_every_beat_sequenced_no_findings(project_root: Path) -> None:
    write_project(
        project_root,
        units=[
            UnitSpec("a", "Beat A", sequence="Act I", order=1),
            UnitSpec("b", "Beat B", sequence="Act I", order=2),
        ],
    )
    assert _run(project_root) == []


def test_no_outline_units_directory_is_inert(project_root: Path) -> None:
    # A project with no outline/units/ yields no findings and no run errors (FR-009).
    write_project(project_root, characters=["Aparici"])
    assert _run(project_root) == []

    project = load_context(project_root)
    builtins, customs, _ = discover_validators(project_root / ".bookwright" / "validators")
    active = resolve_active(builtins, customs, ValidatorsBlock(enabled=["narrative_structure"]))
    indexer = build_indexer(project_root, outline=True)
    violations, errors, ran = run_validators(active, project, indexer)
    assert violations == []
    assert errors == []
    assert ran == ["narrative_structure"]


def test_order_gap_or_duplicate_yields_no_order_finding(project_root: Path) -> None:
    # All beats are sequenced (so no orphan) and the order: gap/duplicate is not an
    # incoherence → zero findings (FR-007, research D8).
    write_project(
        project_root,
        units=[
            UnitSpec("a", "Beat A", sequence="Act I", order=10),
            UnitSpec("b", "Beat B", sequence="Act I", order=30),
            UnitSpec("c", "Beat C", sequence="Act I", order=30),  # duplicate ordinal
        ],
    )
    assert _run(project_root) == []


def test_deterministic_and_read_only(project_root: Path) -> None:
    write_project(
        project_root,
        units=[
            UnitSpec("first", "First Orphan"),
            UnitSpec("second", "Second Orphan"),
        ],
    )
    indexer = build_indexer(project_root, outline=True)
    project = load_context(project_root)

    before_count = indexer.count()

    first = NarrativeStructure().validate(project, indexer)
    second = NarrativeStructure().validate(project, indexer)

    assert first == second  # byte-for-byte identical finding lists (SC-005)
    assert len(first) == 2
    # The validator writes nothing to the graph (FR-008): the triple count is unchanged.
    assert indexer.count() == before_count


# --- User Story 2: unresolved role (Rule c) ----------------------------------

# A bible timeline whose event names a character that does not exist → a
# bible-level UnresolvedReference (path bible/timeline.md), which Rule c must NOT report.
_TIMELINE_BAD_PARTICIPANT = """\
---
events:
  - name: "Duelo"
    participants: ["Ghost"]
---
"""


def test_unresolved_role_flagged_with_location(project_root: Path) -> None:
    # The unit is sequenced (so Rule a does not fire); its `villain` role resolves to
    # no character role → exactly one Rule c finding naming the beat and the role.
    write_project(
        project_root,
        character_roles={"Ada": ["hero"]},
        units=[UnitSpec("opening", "Opening", roles=("villain",), sequence="Act I", order=1)],
    )
    findings = _run(project_root)
    assert len(findings) == 1
    (finding,) = findings
    assert finding.validator == "narrative_structure"
    assert finding.severity == Severity.warning
    assert "Opening" in finding.message and "villain" in finding.message
    assert finding.source is not None
    assert finding.source.startswith("outline/units/opening.md")


def test_unresolved_role_stale_graph_falls_back_to_card_path(project_root: Path) -> None:
    # When graph.ttl is absent/stale (no E13 provenance for the unit), resolve_source
    # returns None and Rule c still locates the finding via the card relpath (no :line).
    write_project(
        project_root,
        character_roles={"Ada": ["hero"]},
        units=[UnitSpec("opening", "Opening", roles=("villain",), sequence="Act I", order=1)],
    )
    findings = NarrativeStructure().validate(load_context(project_root), RdflibIndexer())
    assert len(findings) == 1
    (finding,) = findings
    assert "villain" in finding.message
    assert finding.source == "outline/units/opening.md"  # card relpath, no :line suffix


def test_resolvable_role_not_flagged(project_root: Path) -> None:
    write_project(
        project_root,
        character_roles={"Ada": ["hero"]},
        units=[UnitSpec("opening", "Opening", roles=("hero",), sequence="Act I", order=1)],
    )
    assert _run(project_root) == []


def test_no_outline_units_no_role_finding(project_root: Path) -> None:
    # A bible participant miss exists, but with no outline/units/ there is no role
    # finding (FR-009) — and the bible miss is never reported regardless.
    write_project(
        project_root,
        characters=["Aparici"],
        timeline=_TIMELINE_BAD_PARTICIPANT,
    )
    assert _run(project_root) == []


def test_bible_level_unresolved_reference_not_reported(project_root: Path) -> None:
    # Both a bible participant miss (path bible/timeline.md) and an outline role miss
    # (path outline/units/...) are present; only the outline one is reported (D6).
    write_project(
        project_root,
        character_roles={"Ada": ["hero"]},
        timeline=_TIMELINE_BAD_PARTICIPANT,
        units=[UnitSpec("opening", "Opening", roles=("villain",), sequence="Act I", order=1)],
    )
    findings = _run(project_root)
    assert len(findings) == 1
    (finding,) = findings
    assert "villain" in finding.message
    assert "Ghost" not in finding.message  # the bible miss is filtered out


# --- User Story 3: configuration & envelope conformance ----------------------


def _resolve(root: Path, block: ValidatorsBlock) -> list[str]:
    builtins, customs, _ = discover_validators(root / ".bookwright" / "validators")
    return [v.name for v in resolve_active(builtins, customs, block)]


def test_in_default_active_set(project_root: Path) -> None:
    write_project(project_root, characters=["Aparici"])
    manifest = Manifest.load(project_root / "manifest.toml")
    assert "narrative_structure" in _resolve(project_root, manifest.validators)


def test_disabled_by_name_does_not_run(project_root: Path) -> None:
    write_project(
        project_root,
        units=[UnitSpec("orphan", "Orphan Beat")],
        disabled=["narrative_structure"],
    )
    manifest = Manifest.load(project_root / "manifest.toml")
    active = _resolve(project_root, manifest.validators)
    assert "narrative_structure" not in active
    # Every other built-in is still present.
    assert "temporal" in active and "setting_continuity" in active


def test_enabled_only_it_runs(project_root: Path) -> None:
    write_project(
        project_root,
        units=[UnitSpec("orphan", "Orphan Beat")],
        enabled=["narrative_structure"],
    )
    manifest = Manifest.load(project_root / "manifest.toml")
    assert _resolve(project_root, manifest.validators) == ["narrative_structure"]
