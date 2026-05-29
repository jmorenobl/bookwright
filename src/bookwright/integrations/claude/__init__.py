"""``ClaudeIntegration`` — Claude Code integration (FR-007, FR-010, FR-013)."""

from __future__ import annotations

from typing import ClassVar

from bookwright.integrations.base import SkillsIntegration


class ClaudeIntegration(SkillsIntegration):
    """Integration for the Claude Code agent (.claude/skills layout).

    Inherits the base ``setup()`` body and the base ``resolve_skills_dir``
    (which already returns ``Path(default_skills_dir)``); no overrides are
    necessary in v0.
    """

    key: ClassVar[str] = "claude"
    default_skills_dir: ClassVar[str] = ".claude/skills"
    config: ClassVar[dict[str, str | bool]] = {
        "name": "Claude Code",
        "install_url": "https://docs.claude.com/claude-code",
        "requires_cli": True,
        "context_file": "CLAUDE.md",
    }

    supports_dynamic_context: ClassVar[bool] = True
    supports_subagents: ClassVar[bool] = True
    supports_tool_restrictions: ClassVar[bool] = True
