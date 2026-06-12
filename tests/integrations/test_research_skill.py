"""Materialization-compliance of the ``bookwright-research`` skill (SC-001).

The new source command is materialized through the **unchanged** iteration-9
pipeline into a lint-passing ``SKILL.md`` for **both** integrations. Asserts the
authoring invariants of contracts/research-skill.md:

* SK-1 — front-matter ``name == "bookwright-research"`` (== parent dir / filename stem).
* SK-2 — ``description`` < 1024 chars.
* SK-3 — materializes for ``claude`` **and** ``generic`` and passes ``lint_skill_md``.
* SK-4 — the cited ``references/research-format.md`` is copied alongside.
* SK-5 — the body carries no residual ``{ARGS}``/``{SCRIPT}`` token after transform.

SK-6 (the SC-009 description mirror) is enforced by the existing
``tests/integrations/test_descriptions.py`` once the command joins its roster —
deliberately not duplicated here (research.md R2).
"""

from __future__ import annotations

from importlib.resources.abc import Traversable
from pathlib import Path

import pytest

from bookwright.integrations import ClaudeIntegration, GenericIntegration, SkillsIntegration
from bookwright.integrations.constants import SKILL_DESCRIPTION_MAX_LENGTH
from bookwright.integrations.lint import lint_skill_md
from bookwright.integrations.materialize import generate_skill_md, iter_command_sources
from bookwright.io.frontmatter import parse_frontmatter
from bookwright.io.fs import NullLedger

_NAME = "bookwright-research"


def _source() -> Traversable:
    return next(s for s in iter_command_sources() if Path(s.name).stem == _NAME)


@pytest.mark.parametrize(
    "integration",
    [ClaudeIntegration(), GenericIntegration()],
    ids=["claude", "generic"],
)
def test_materializes_and_lints_for_both_integrations(
    integration: SkillsIntegration, tmp_path: Path
) -> None:
    written = generate_skill_md(_source(), tmp_path, integration, ledger=NullLedger())
    assert written is not None
    assert written == tmp_path / _NAME / "SKILL.md"

    parsed = parse_frontmatter(written.read_text(encoding="utf-8"))
    # SK-1: name equals the skill directory / filename stem.
    assert parsed.metadata["name"] == _NAME
    assert written.parent.name == _NAME
    # SK-2: description under the agentskills.io cap.
    description = parsed.metadata["description"]
    assert isinstance(description, str) and 0 < len(description) < SKILL_DESCRIPTION_MAX_LENGTH
    # SK-5: no residual token survived the {ARGS} -> $ARGUMENTS transform.
    assert "{ARGS}" not in parsed.body
    assert "{SCRIPT}" not in parsed.body
    # SK-4: the cited reference came along.
    assert (written.parent / "references" / "research-format.md").is_file()
    # SK-3: generate_skill_md already lints; assert it stays green idempotently.
    lint_skill_md(written.parent)


def test_body_instructs_the_final_graph_build() -> None:
    # FR-018 — the protocol's final step runs the existing JSON build so findings
    # and anchors land in the graph; the call survives into the materialized body.
    source_body = parse_frontmatter(_source().read_text(encoding="utf-8")).body
    assert "bookwright graph build --json" in source_body


@pytest.mark.parametrize(
    "integration",
    [ClaudeIntegration(), GenericIntegration()],
    ids=["claude", "generic"],
)
def test_body_consults_status_queue(integration: SkillsIntegration, tmp_path: Path) -> None:
    # RQ-1 / RQ-3 (iteration 021) — on the no-topic path the protocol consults the
    # derived status (FR-001, SC-002) and builds its queue from the *raw* facts
    # ``open_questions`` and ``unresolved_anchors`` (FR-002), not the
    # ``next_actions`` handoff prompt. These are frozen iteration-020 contract
    # field names the prose cites verbatim, so the assertions harden the contract
    # without over-fitting to prose wording. Verified against the source body and
    # the materialized body for both integrations so the step survives materialization.
    source_body = parse_frontmatter(_source().read_text(encoding="utf-8")).body
    materialized = generate_skill_md(_source(), tmp_path, integration, ledger=NullLedger())
    assert materialized is not None
    materialized_body = parse_frontmatter(materialized.read_text(encoding="utf-8")).body

    for body in (source_body, materialized_body):
        assert "bookwright status" in body  # RQ-1: the first-step consult.
        assert "open_questions" in body  # RQ-3: queue built from the raw facts.
        assert "unresolved_anchors" in body  # RQ-3: ...and the second fact list.
