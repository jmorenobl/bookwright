"""C3 / FR-008 — the claude → generic integration swap, end to end.

A project initialized with ``claude`` (skills under ``.claude/skills/``) is switched
to ``generic`` with ``bookwright integration use generic``; the skills are then
correctly materialized under ``.agents/skills/`` and the manifest reflects the new
integration. Per the clarified residue policy (spec Assumptions, 2026-06-03) the test
asserts only the **new** location and makes **no** assertion about removal of the old
``.claude/skills/`` directory.

Mechanism note: FR-008's original wording ("re-initialize with ``--here --force``")
is incompatible with the ratified ``init`` guard that refuses any re-init of an
existing project (``.bookwright/`` present → ``already_initialized``, even with
``--force``). The swap is therefore its own intention-revealing command,
``integration use`` — which is what this E2E exercises.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.core.manifest import Manifest
from bookwright.integrations.lint import lint_skill_md
from bookwright.integrations.materialize import iter_command_sources

EXPECTED_SKILL_COUNT = len(iter_command_sources())


def _skill_dirs(skills_root: Path) -> list[Path]:
    return sorted(p.parent for p in skills_root.rglob("SKILL.md"))


def test_integration_swap_claude_to_generic(
    cli: CliRunner, workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # GIVEN a project initialized with --integration claude (skills under .claude/skills/).
    init = cli.invoke(app, ["init", "libro", "--integration", "claude", "--no-git", "--json"])
    assert init.exit_code == 0, init.stdout
    project = workdir / "libro"
    assert _skill_dirs(project / ".claude" / "skills")
    monkeypatch.chdir(project)

    # WHEN the project is switched to generic.
    swap = cli.invoke(app, ["integration", "use", "generic", "--json"])
    assert swap.exit_code == 0, swap.stdout

    # THEN skills are correctly materialized under .agents/skills/ (a valid SKILL.md set)…
    agents = _skill_dirs(project / ".agents" / "skills")
    assert len(agents) == EXPECTED_SKILL_COUNT
    for skill_dir in agents:
        lint_skill_md(skill_dir)

    # …and the manifest now records the generic integration.
    manifest = Manifest.load(project / "manifest.toml")
    assert manifest.integration.key == "generic"
    assert manifest.integration.skills_dir == ".agents/skills"

    # Deliberately NO assertion that .claude/skills/ was removed (residue policy).
    payload = json.loads(swap.stdout)
    assert payload["integration"] == "generic"
