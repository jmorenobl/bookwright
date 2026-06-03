"""``focalization`` — narrative-voice breaks, bilingual declaration parsing (T023)."""

from __future__ import annotations

from pathlib import Path

from bookwright.indexers import RdflibIndexer
from bookwright.validation.base import Severity, Violation
from bookwright.validation.validators.focalization import Focalization
from tests.validation.conftest import load_context, write_project


def _run(root: Path) -> list[Violation]:
    return Focalization().validate(load_context(root), RdflibIndexer())


def test_first_person_outside_dialogue_warns(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="# Constitución\n\nVoz narrativa: tercera persona\n",
        manuscript={"cap-01.md": "Aparici caminaba.\nYo no entendía nada.\n"},
    )
    findings = _run(project_root)
    assert any(f.severity == Severity.warning and "first-person" in f.message for f in findings)


def test_head_hopping_on_non_focal_character_warns(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici", "Peña"],
        constitution="Voz narrativa: tercera persona limitada, focalizada en Aparici\n",
        manuscript={"cap-01.md": "Aparici observó la sala.\nPeña pensó que todo acababa.\n"},
    )
    findings = _run(project_root)
    hops = [f for f in findings if "head-hopping" in f.message]
    assert len(hops) == 1
    assert "Peña" in hops[0].message
    assert hops[0].source == "manuscript/cap-01.md:2"


def test_english_declaration_parses_equivalently(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Narrative voice: third person limited, focused on Aparici\n",
        manuscript={"cap-01.md": "Aparici walked on.\nI did not understand.\n"},
    )
    findings = _run(project_root)
    assert any("first-person" in f.message for f in findings)


def test_dialogue_line_is_exempt(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Voz narrativa: tercera persona\n",
        manuscript={"cap-01.md": "Aparici asintió.\n—Yo me marcho —dijo.\n"},
    )
    # The first-person pronoun sits in dialogue (em-dash opener) → not a break.
    assert all("first-person" not in f.message for f in _run(project_root))


def test_no_parsable_declaration_yields_nothing(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="# Constitución\n\nSin declaración de punto de vista.\n",
        manuscript={"cap-01.md": "Yo llegué tarde.\n"},
    )
    assert _run(project_root) == []
