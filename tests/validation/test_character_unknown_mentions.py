"""``character_unknown_mentions`` — the open-set abstainer (issue #1, track A).

The validator abstains **unconditionally** — it abstains by approach, not by input — so
no project shape produces a finding. Since iteration 053 it abstains via the **returned**
partial-evaluation shape (form (c), ``EvalResult`` with no findings and one
:class:`Abstention`) rather than a raised total abstention (form (b)), so it can carry the
``code="undeclared_characters"`` discriminator the ``status`` nudge keys on. These tests
pin that across an empty project, a clean project, and a project full of off-roster proper
nouns; ``reason`` and ``kind`` are unchanged — only the additive wire ``code`` moves.
"""

from __future__ import annotations

from pathlib import Path

from bookwright.indexers import RdflibIndexer
from bookwright.validation.base import Abstention, EvalResult, NotEvaluatedKind, Severity
from bookwright.validation.validators.character_unknown_mentions import (
    CharacterUnknownMentions,
)
from tests.validation.conftest import load_context, write_project

_REASON = (
    "open-set proper-noun discovery requires semantic judgment (move 3); "
    "the deterministic heuristic was measured insufficient on real prose"
)


def _abstain(root: Path) -> Abstention:
    """Run the validator; assert the form-(c) shape and return its single abstention."""
    result = CharacterUnknownMentions().validate(load_context(root), RdflibIndexer())
    assert isinstance(result, EvalResult)
    assert result.violations == []  # a pure abstainer never emits a finding
    assert len(result.not_evaluated) == 1
    return result.not_evaluated[0]


def test_protocol_attributes() -> None:
    validator = CharacterUnknownMentions()
    assert validator.name == "character_unknown_mentions"
    assert validator.severity_default == Severity.warning


def test_empty_project_abstains_with_open_set_reason(project_root: Path) -> None:
    write_project(project_root, characters=[], manuscript={})
    assert _abstain(project_root).reason == _REASON


def test_abstainer_carries_pending_capability_and_code(project_root: Path) -> None:
    # FR-013 (iteration 053): the abstainer is a PERMANENT capability-gap (the kind is
    # unchanged from iteration 044) AND now carries `code="undeclared_characters"` — the
    # one wire delta of the form (b)→(c) conversion; `reason`/`kind` are byte-identical.
    write_project(project_root, characters=[], manuscript={})
    abstention = _abstain(project_root)
    assert abstention.kind is NotEvaluatedKind.pending_capability
    assert abstention.reason == _REASON
    assert abstention.code == "undeclared_characters"


def test_clean_project_still_abstains(project_root: Path) -> None:
    # Even a project with a roster and roster-only prose abstains — the verdict is about
    # the approach, never the input (FR-005).
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici saludó.\n"},
    )
    assert _abstain(project_root).reason == _REASON


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
    assert _abstain(project_root).reason == _REASON
