"""``GenericIntegration`` — neutral agentskills.io layout (FR-008, FR-010, FR-014, FR-024)."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar

from bookwright.integrations.base import SkillsIntegration
from bookwright.integrations.options import IntegrationOption


class GenericIntegration(SkillsIntegration):
    """Integration for any agentskills.io-compliant agent (Codex CLI, Cursor, ...).

    Declares one option (``--skills-dir``) so the user can re-target the
    skills layout (e.g., ``.cursor/skills``) without writing a dedicated
    integration class.
    """

    key: ClassVar[str] = "generic"
    default_skills_dir: ClassVar[str] = ".agents/skills"
    # FR-008: `context_file` MUST NOT be present in the generic config.
    config: ClassVar[dict[str, str | bool]] = {
        "name": "Generic (Agent Skills standard)",
        "install_url": "https://agentskills.io",
        "requires_cli": False,
    }

    supports_dynamic_context: ClassVar[bool] = False
    supports_subagents: ClassVar[bool] = False
    supports_tool_restrictions: ClassVar[bool] = False

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                flag="--skills-dir",
                type="string",
                required=False,
                default=".agents/skills",
                help=(
                    "Directory where SKILL.md files are materialized. "
                    "Default: .agents/skills (Codex/Cursor convention). "
                    "Common alternatives: .cursor/skills, .github/skills."
                ),
            ),
        ]

    def resolve_skills_dir(
        self,
        parsed_options: Mapping[str, object] | None = None,
    ) -> Path:
        if parsed_options and "skills_dir" in parsed_options:
            return Path(str(parsed_options["skills_dir"]))
        return Path(self.default_skills_dir)
