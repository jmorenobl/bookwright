"""``character_unknown_mentions`` — the open-set abstainer (issue #1, track A).

The validator raises :class:`NotEvaluated` **unconditionally** — it abstains by approach,
not by input — so no project shape produces a finding. These tests pin that across an
empty project, a clean project, and a project full of off-roster proper nouns.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.indexers import RdflibIndexer
from bookwright.validation.base import NotEvaluated, Severity
from bookwright.validation.validators.character_unknown_mentions import (
    CharacterUnknownMentions,
)
from tests.validation.conftest import load_context, write_project

_REASON = (
    "open-set proper-noun discovery requires semantic judgment (move 3); "
    "the deterministic heuristic was measured insufficient on real prose"
)


def _raise(root: Path) -> NotEvaluated:
    with pytest.raises(NotEvaluated) as excinfo:
        CharacterUnknownMentions().validate(load_context(root), RdflibIndexer())
    return excinfo.value


def test_protocol_attributes() -> None:
    validator = CharacterUnknownMentions()
    assert validator.name == "character_unknown_mentions"
    assert validator.severity_default == Severity.warning


def test_empty_project_abstains_with_open_set_reason(project_root: Path) -> None:
    write_project(project_root, characters=[], manuscript={})
    assert _raise(project_root).reason == _REASON


def test_clean_project_still_abstains(project_root: Path) -> None:
    # Even a project with a roster and roster-only prose abstains — the verdict is about
    # the approach, never the input (FR-005).
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici saludó.\n"},
    )
    assert _raise(project_root).reason == _REASON


def test_off_roster_proper_nouns_still_abstain(project_root: Path) -> None:
    # Organization, title word and a quoted opening word — the exact shapes the old
    # heuristic mis-flagged — produce NO warning; the validator abstains regardless.
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={
            "cap-01.md": (
                "# La caída de Elena\n"
                "Aparici trabajó en la Naviera Salas.\n"
                "«Esto es el porvenir», dijo.\n"
            )
        },
    )
    assert _raise(project_root).reason == _REASON
