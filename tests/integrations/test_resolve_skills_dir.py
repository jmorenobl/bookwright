"""Resolve-skills-dir contract (FR-022..FR-025, SC-003, SC-004)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.integrations import ClaudeIntegration, GenericIntegration


@pytest.mark.parametrize(
    "parsed_options",
    [
        None,
        {},
        {"skills_dir": "anything"},
        {"skills_dir": ".cursor/skills"},
    ],
)
def test_claude_ignores_parsed_options(parsed_options: dict[str, object] | None) -> None:
    """FR-023 / SC-003 — Claude always returns its locked default."""

    assert ClaudeIntegration().resolve_skills_dir(parsed_options) == Path(".claude/skills")


@pytest.mark.parametrize(
    "parsed_options,expected",
    [
        (None, Path(".agents/skills")),
        ({}, Path(".agents/skills")),
        ({"skills_dir": ".cursor/skills"}, Path(".cursor/skills")),
        ({"skills_dir": "path with spaces/skills"}, Path("path with spaces/skills")),
    ],
)
def test_generic_honours_skills_dir_option(
    parsed_options: dict[str, object] | None,
    expected: Path,
) -> None:
    """FR-024 / SC-004 — Generic returns the user's override when present."""

    assert GenericIntegration().resolve_skills_dir(parsed_options) == expected


@pytest.mark.parametrize(
    "integration_cls,parsed_options",
    [
        (ClaudeIntegration, None),
        (ClaudeIntegration, {"skills_dir": ".x/skills"}),
        (GenericIntegration, None),
        (GenericIntegration, {"skills_dir": ".cursor/skills"}),
    ],
)
def test_resolved_paths_are_relative(
    integration_cls: type,
    parsed_options: dict[str, object] | None,
) -> None:
    """FR-025 — every returned path is project-relative.

    Note: ``resolve_skills_dir`` only guarantees ``not is_absolute()``;
    paths that *escape* ``project_root`` via ``..`` components are still
    relative and pass here. Containment is enforced one layer down in
    ``SkillsIntegration.setup()`` (see
    ``test_setup_stub.test_generic_setup_rejects_skills_dir_escaping_project_root``).
    """

    result = integration_cls().resolve_skills_dir(parsed_options)
    assert result.is_absolute() is False
