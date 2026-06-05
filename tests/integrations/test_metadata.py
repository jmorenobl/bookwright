"""declared metadata pinning (FR-006..FR-011)."""

from __future__ import annotations

import ast
import pathlib

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


# ---------- FR-011 negative assertion: capability flags are pure metadata in v0 ----------


_CAPABILITY_FLAGS = (
    "supports_dynamic_context",
    "supports_subagents",
    "supports_tool_restrictions",
)
_INTEGRATIONS_ROOT = (
    pathlib.Path(__file__).resolve().parents[2] / "src" / "bookwright" / "integrations"
)


def _iter_integration_sources() -> list[pathlib.Path]:
    return [path for path in _INTEGRATIONS_ROOT.rglob("*.py") if "__pycache__" not in path.parts]


@pytest.mark.parametrize("flag_name", _CAPABILITY_FLAGS)
def test_no_branching_on_capability_flags(flag_name: str) -> None:
    """FR-011 — capability flags are not branched on by integration-layer code.

    An AST walk over every `.py` under `src/bookwright/integrations/` looks
    for `if <something>.<flag>` / `while <something>.<flag>` /
    `<flag> in ...` constructs that would prove the flag is being used as
    a runtime switch. None should exist in v0.
    """

    offenders: list[str] = []
    for path in _iter_integration_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.IfExp)):
                for inner in ast.walk(node.test):
                    if isinstance(inner, ast.Attribute) and inner.attr == flag_name:
                        offenders.append(f"{path}:{node.lineno}")
                        break
    assert not offenders, (
        f"Found branching on capability flag {flag_name!r} in: {offenders}. "
        "Capability flags are pure metadata in v0 (FR-011)."
    )
