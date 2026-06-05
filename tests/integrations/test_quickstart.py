"""Quickstart validation - runs the code blocks from
``specs/003-integration-architecture/quickstart.md`` sections 1-5."""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwright.core import Manifest
from bookwright.integrations import (
    MalformedOptionError,
    UnknownIntegrationError,
    UnknownOptionError,
    get,
    list_keys,
    parse_options,
)

# §1 — Look up an integration by key


def test_quickstart_section_1_lookup() -> None:
    assert list_keys() == ["claude", "generic"]

    claude_cls = get("claude")
    generic_cls = get("generic")
    assert claude_cls.key == "claude"
    assert generic_cls.key == "generic"

    with pytest.raises(UnknownIntegrationError) as exc_info:
        get("copilot")
    payload = exc_info.value.to_json()
    assert payload["code"] == "unknown_integration"
    assert payload["details"]["value"] == "copilot"
    assert payload["details"]["valid"] == ["claude", "generic"]


# §2 — Inspect metadata


def test_quickstart_section_2_metadata() -> None:
    cls = get("claude")
    assert cls.key == "claude"
    assert cls.default_skills_dir == ".claude/skills"
    assert cls.config["name"] == "Claude Code"
    assert cls.config["install_url"] == "https://docs.claude.com/claude-code"
    assert cls.config["requires_cli"] is True
    assert cls.config["context_file"] == "CLAUDE.md"
    assert cls.supports_dynamic_context is True
    assert cls.supports_subagents is True
    assert cls.supports_tool_restrictions is True

    # GenericIntegration mirror without context_file, capabilities False.
    generic_cls = get("generic")
    assert "context_file" not in generic_cls.config
    assert generic_cls.supports_dynamic_context is False
    assert generic_cls.supports_subagents is False
    assert generic_cls.supports_tool_restrictions is False


# §3 — Parse --integration-options


def test_quickstart_section_3_parse_options() -> None:
    generic_cls = get("generic")

    # R8 — GenericIntegration declares `--skills-dir` with
    # `default='.agents/skills'`; the default is applied on empty input
    # so downstream consumers always observe an explicit value.
    assert parse_options(None, generic_cls) == {"skills_dir": ".agents/skills"}
    assert parse_options("", generic_cls) == {"skills_dir": ".agents/skills"}
    assert parse_options("--skills-dir .cursor/skills", generic_cls) == {
        "skills_dir": ".cursor/skills"
    }
    assert parse_options("--skills-dir=.cursor/skills", generic_cls) == {
        "skills_dir": ".cursor/skills"
    }

    with pytest.raises(UnknownOptionError) as unknown_info:
        parse_options("--bogus xyz", generic_cls)
    payload = unknown_info.value.to_json()
    assert payload["code"] == "unknown_option"
    assert payload["details"]["integration"] == "generic"
    assert payload["details"]["value"] == "--bogus"
    assert payload["details"]["valid"] == ["--skills-dir"]

    with pytest.raises(MalformedOptionError) as malformed_info:
        parse_options("--skills-dir", generic_cls)
    payload = malformed_info.value.to_json()
    assert payload["code"] == "malformed_option"
    assert payload["details"]["rule"] == "missing_value"
    assert payload["details"]["value"] == "--skills-dir"


# §4 — Materialize the integration into a project


def test_quickstart_section_4_setup(tmp_project: Path) -> None:
    cls = get("generic")
    parsed = parse_options("--skills-dir .cursor/skills", cls)
    manifest = Manifest.build(
        title="My Novel",
        authors=["Alice"],
        integration_key="generic",
        uri_base="https://example.org/my-novel/",
        language="en",
        type="novel",
        status="idea",
    )

    instance = cls()
    instance.setup(tmp_project, manifest, parsed)

    skills_dir = tmp_project / ".cursor/skills"
    assert skills_dir.is_dir()
    # setup() now materializes one SKILL.md per command (no placeholder marker).
    skill = skills_dir / "bookwright-bible" / "SKILL.md"
    assert skill.is_file()
    assert not (skills_dir / ".bookwright-skills-placeholder").exists()

    # Idempotent: re-running leaves an existing SKILL.md byte-for-byte unchanged.
    bytes_before = skill.read_bytes()
    instance.setup(tmp_project, manifest, parsed)
    assert skill.read_bytes() == bytes_before


# §5 — Resolve the skills dir without running setup


def test_quickstart_section_5_resolve_skills_dir() -> None:
    claude = get("claude")()
    assert claude.resolve_skills_dir() == Path(".claude/skills")
    assert claude.resolve_skills_dir({}) == Path(".claude/skills")
    assert claude.resolve_skills_dir({"skills_dir": "ignored"}) == Path(".claude/skills")

    generic = get("generic")()
    assert generic.resolve_skills_dir() == Path(".agents/skills")
    assert generic.resolve_skills_dir({}) == Path(".agents/skills")
    assert generic.resolve_skills_dir({"skills_dir": ".cursor/skills"}) == Path(".cursor/skills")
