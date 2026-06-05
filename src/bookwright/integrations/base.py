"""``SkillsIntegration`` — the single operative v0 base class for integrations.

Subclasses live under ``bookwright.integrations.<key>/`` and override:
    - ``key``, ``config``, ``default_skills_dir`` (always),
    - ``supports_*`` flags (when the agent supports the capability),
    - ``options()`` (when the integration declares ``--integration-options``
      flags), and
    - ``resolve_skills_dir()`` (when the resolved dir depends on
      ``parsed_options``).

``setup()`` is implemented once here; no v0 subclass overrides it.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

from bookwright.integrations.errors import MalformedOptionError
from bookwright.integrations.materialize import generate_skill_md, iter_command_sources
from bookwright.integrations.options import IntegrationOption
from bookwright.io.fs import NullLedger, mkdir_tracked

if TYPE_CHECKING:
    from bookwright.core.manifest import Manifest
    from bookwright.io.fs import FileLedger


class SkillsIntegration:
    """Base contract every Bookwright v0 integration implements."""

    # Sentinel defaults — every concrete subclass MUST override `key`,
    # `config`, and `default_skills_dir`. The empty-string sentinel on
    # `key` is caught by `_register` (R13). `config`'s default is a
    # frozen `MappingProxyType` (R19) so a forgetful subclass that
    # accidentally writes `cls.config['x'] = 'y'` raises TypeError
    # instead of silently mutating the shared base dict and polluting
    # every other forgetful subclass.
    key: ClassVar[str] = ""
    config: ClassVar[Mapping[str, str | bool]] = MappingProxyType({})
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
        *,
        ledger: FileLedger | None = None,
    ) -> None:
        """Materialize one ``SKILL.md`` per source command under the resolved dir.

        Shared by every v0 integration (no subclass overrides it — the only
        per-integration variation is already behind ``resolve_skills_dir`` and
        the capability flags). For each packaged source command, delegate to
        ``generate_skill_md``; idempotent per-``SKILL.md`` (FR-014); never writes
        outside the resolved dir (FR-017).

        ``ledger`` is the rollback-recording ``FileLedger`` (``init`` passes its
        live ``BackupLedger``); when omitted it defaults to a ``NullLedger`` so
        ``setup()`` is standalone-callable. Every materialized path is recorded
        through it (FR-019). A ``SkillLintError``/``SkillMaterializationError``
        from any command propagates, aborting this integration (FR-016).
        """

        # `manifest` is part of the iteration-9 contract; unused in v0 body.
        del manifest

        ledger = ledger or NullLedger()
        resolved = self.resolve_skills_dir(parsed_options)
        target = (project_root / resolved).resolve()
        root = project_root.resolve()
        if target == root:
            # `--skills-dir=`, `--skills-dir .`, `--skills-dir ./`, etc. all
            # collapse the target into project_root itself. Rejected as a
            # separate rule from `escapes_project_root` so the JSON envelope
            # can distinguish "lands AT root" from "lands OUTSIDE root" (R6).
            raise MalformedOptionError(rule="resolves_to_project_root", value=str(resolved))
        if not target.is_relative_to(root):
            raise MalformedOptionError(rule="escapes_project_root", value=str(resolved))
        mkdir_tracked(target, ledger)
        for command_path in iter_command_sources():
            generate_skill_md(command_path, target, self, ledger=ledger)
