"""``SkillsIntegration`` — the single operative v0 base class for integrations.

Subclasses live under ``bookwright.integrations.<key>/`` and override:
    - ``key``, ``config``, ``default_skills_dir`` (always),
    - ``supports_*`` flags (when the agent supports the capability),
    - ``options()`` (when the integration declares ``--integration-options``
      flags), and
    - ``resolve_skills_dir()`` (when the resolved dir depends on
      ``parsed_options``).

``setup()`` is implemented once here (T013); no v0 subclass overrides it.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from bookwright.integrations.constants import SKILL_PLACEHOLDER_MARKER_NAME
from bookwright.integrations.errors import MalformedOptionError
from bookwright.integrations.options import IntegrationOption

if TYPE_CHECKING:
    from bookwright.core.manifest import Manifest


class SkillsIntegration:
    """Base contract every Bookwright v0 integration implements."""

    # Sentinel defaults — every concrete subclass MUST override `key`,
    # `config`, and `default_skills_dir`. The empty-string sentinel on
    # `key` ensures a forgetful subclass collides with any other forgetful
    # subclass on the registry, surfacing as DuplicateRegistrationError.
    key: ClassVar[str] = ""
    config: ClassVar[dict[str, str | bool]] = {}
    default_skills_dir: ClassVar[str] = ""

    supports_dynamic_context: ClassVar[bool] = False
    supports_subagents: ClassVar[bool] = False
    supports_tool_restrictions: ClassVar[bool] = False

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        """Return the integration's declared ``--integration-options`` flags.

        Default: empty list (FR-013). Override to declare flags.
        """

        return []

    def resolve_skills_dir(
        self,
        parsed_options: Mapping[str, object] | None = None,
    ) -> Path:
        """Return the project-relative skills directory for this integration.

        Default implementation returns ``Path(self.default_skills_dir)`` and
        ignores ``parsed_options`` (FR-023). Subclasses that declare options
        affecting the resolved directory (e.g., ``GenericIntegration``'s
        ``--skills-dir``) MUST override.

        ``Mapping`` (not ``dict``) is used in the signature so callers may
        pass the narrower ``dict[str, str | bool]`` returned by
        ``parse_options`` without an explicit cast (``dict`` is invariant).
        """

        del parsed_options
        return Path(self.default_skills_dir)

    def setup(
        self,
        project_root: Path,
        manifest: Manifest,
        parsed_options: Mapping[str, object] | None = None,
    ) -> None:
        """v0 stub: create the resolved skills dir + write a placeholder marker.

        Idempotent (FR-028); never writes outside the resolved dir (FR-029).
        Real ``SKILL.md`` materialization is iteration 9; this body marks
        the directory so iteration 9 can detect "setup() has run."
        """

        # `manifest` is part of the iteration-9 contract; unused in v0 body.
        del manifest

        resolved = self.resolve_skills_dir(parsed_options)
        target = (project_root / resolved).resolve()
        root = project_root.resolve()
        if target == root:
            # `--skills-dir=`, `--skills-dir .`, `--skills-dir ./`, etc. all
            # collapse the marker into project_root itself. Rejected as a
            # separate rule from `escapes_project_root` so the JSON envelope
            # can distinguish "lands AT root" from "lands OUTSIDE root" (R6).
            raise MalformedOptionError(rule="resolves_to_project_root", value=str(resolved))
        if not target.is_relative_to(root):
            raise MalformedOptionError(rule="escapes_project_root", value=str(resolved))
        target.mkdir(parents=True, exist_ok=True)
        marker = target / SKILL_PLACEHOLDER_MARKER_NAME
        if not marker.exists():
            marker.write_text(
                f"bookwright integration: {self.key} "
                f"— SKILL.md materialization deferred to iteration 9\n",
                encoding="utf-8",
            )
