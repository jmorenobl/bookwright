"""declared metadata pinning (FR-006..FR-011)."""

from __future__ import annotations

import pytest

from bookwright.integrations import (
    ClaudeIntegration,
    GenericIntegration,
    SkillsIntegration,
)


def test_claude_metadata_locked() -> None:
    assert ClaudeIntegration.key == "claude"
    assert ClaudeIntegration.default_skills_dir == ".claude/skills"
    assert ClaudeIntegration.config == {
        "name": "Claude Code",
        "install_url": "https://docs.claude.com/claude-code",
        "requires_cli": True,
        "context_file": "CLAUDE.md",
    }
    assert ClaudeIntegration.supports_dynamic_context is True
    assert ClaudeIntegration.supports_subagents is True
    assert ClaudeIntegration.supports_tool_restrictions is True


def test_generic_metadata_locked() -> None:
    assert GenericIntegration.key == "generic"
    assert GenericIntegration.default_skills_dir == ".agents/skills"
    assert GenericIntegration.config == {
        "name": "Generic (Agent Skills standard)",
        "install_url": "https://agentskills.io",
        "requires_cli": False,
    }
    # FR-008 — explicit absence.
    assert "context_file" not in GenericIntegration.config
    assert GenericIntegration.supports_dynamic_context is False
    assert GenericIntegration.supports_subagents is False
    assert GenericIntegration.supports_tool_restrictions is False


def test_base_capability_flags_default_false() -> None:
    """FR-009 — base class defence-in-depth."""

    assert SkillsIntegration.supports_dynamic_context is False
    assert SkillsIntegration.supports_subagents is False
    assert SkillsIntegration.supports_tool_restrictions is False


def test_base_config_default_is_immutable() -> None:
    """R19 — `SkillsIntegration.config`'s default is a frozen mapping so
    accidental writes (`cls.config['x'] = 'y'`) raise TypeError instead
    of silently mutating the shared base dict and polluting every other
    forgetful subclass for the rest of the process.
    """

    with pytest.raises(TypeError):
        SkillsIntegration.config["accidental"] = "write"  # type: ignore[index]
