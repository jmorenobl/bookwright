"""US2 — ``setup()`` stub contract (FR-026..FR-030, SC-006)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bookwright.core import Manifest
from bookwright.integrations import (
    SKILL_PLACEHOLDER_MARKER_NAME,
    ClaudeIntegration,
    GenericIntegration,
    MalformedOptionError,
)

MARKER_NAME = SKILL_PLACEHOLDER_MARKER_NAME


def _expected_marker_text(key: str) -> str:
    return f"bookwright integration: {key} — SKILL.md materialization deferred to iteration 9\n"


def test_claude_setup_creates_dir_and_marker(tmp_project: Path, minimal_manifest: Manifest) -> None:
    ClaudeIntegration().setup(tmp_project, minimal_manifest, None)
    skills_dir = tmp_project / ".claude/skills"
    assert skills_dir.is_dir()
    marker = skills_dir / MARKER_NAME
    assert marker.read_text(encoding="utf-8") == _expected_marker_text("claude")


def test_generic_setup_default_dir(tmp_project: Path, minimal_manifest: Manifest) -> None:
    GenericIntegration().setup(tmp_project, minimal_manifest, None)
    skills_dir = tmp_project / ".agents/skills"
    assert skills_dir.is_dir()
    marker = skills_dir / MARKER_NAME
    assert marker.read_text(encoding="utf-8") == _expected_marker_text("generic")


def test_generic_setup_with_parsed_options_overrides_dir(
    tmp_project: Path, minimal_manifest: Manifest
) -> None:
    GenericIntegration().setup(tmp_project, minimal_manifest, {"skills_dir": ".cursor/skills"})
    assert (tmp_project / ".cursor/skills").is_dir()
    assert (tmp_project / ".cursor/skills" / MARKER_NAME).exists()
    # Default dir MUST NOT be created when the user re-targeted.
    assert (tmp_project / ".agents/skills").exists() is False


def test_setup_is_idempotent(tmp_project: Path, minimal_manifest: Manifest) -> None:
    """SC-006 — two calls leave on-disk bytes identical."""

    ClaudeIntegration().setup(tmp_project, minimal_manifest, None)
    marker = tmp_project / ".claude/skills" / MARKER_NAME
    first_digest = hashlib.sha256(marker.read_bytes()).hexdigest()

    ClaudeIntegration().setup(tmp_project, minimal_manifest, None)
    second_digest = hashlib.sha256(marker.read_bytes()).hexdigest()

    assert first_digest == second_digest


def test_setup_preserves_user_content(tmp_project: Path, minimal_manifest: Manifest) -> None:
    """FR-028 — user-authored files MUST NOT be touched by setup()."""

    user_skill_dir = tmp_project / ".claude/skills/my-skill"
    user_skill_dir.mkdir(parents=True)
    user_file = user_skill_dir / "SKILL.md"
    user_file.write_text("user content\n", encoding="utf-8")

    ClaudeIntegration().setup(tmp_project, minimal_manifest, None)

    assert user_file.read_text(encoding="utf-8") == "user content\n"
    assert (tmp_project / ".claude/skills" / MARKER_NAME).exists()


def test_setup_does_not_overwrite_existing_marker(
    tmp_project: Path, minimal_manifest: Manifest
) -> None:
    """FR-028 — never re-write a marker that already exists."""

    skills_dir = tmp_project / ".claude/skills"
    skills_dir.mkdir(parents=True)
    marker = skills_dir / MARKER_NAME
    marker.write_text("pre-existing marker payload\n", encoding="utf-8")

    ClaudeIntegration().setup(tmp_project, minimal_manifest, None)

    assert marker.read_text(encoding="utf-8") == "pre-existing marker payload\n"


def test_setup_writes_only_inside_resolved_dir(
    tmp_project: Path, minimal_manifest: Manifest
) -> None:
    """FR-029 — every new path lies on the chain project_root → resolved_dir."""

    before = set(tmp_project.rglob("*"))
    ClaudeIntegration().setup(tmp_project, minimal_manifest, None)
    after = set(tmp_project.rglob("*"))

    new_paths = after - before
    assert new_paths, "setup() created nothing"

    resolved = tmp_project / ".claude/skills"
    marker = resolved / MARKER_NAME
    new_files = [p for p in new_paths if p.is_file()]

    assert new_files == [marker]

    for path in new_paths:
        if path.is_file():
            assert path == marker
            continue
        # Directory: must be on the chain project_root → resolved_dir.
        assert path.is_relative_to(tmp_project)
        assert resolved.is_relative_to(path) or path == resolved


def test_setup_creates_missing_project_root(tmp_path: Path, minimal_manifest: Manifest) -> None:
    """Edge case #4 — project_root does not exist on disk; mkdir(parents=True) handles it."""

    fresh_root = tmp_path / "fresh-root"
    assert not fresh_root.exists()

    ClaudeIntegration().setup(fresh_root, minimal_manifest, None)

    assert (fresh_root / ".claude/skills").is_dir()
    assert (fresh_root / ".claude/skills" / MARKER_NAME).exists()


def test_setup_does_not_read_manifest(
    tmp_project: Path,
) -> None:
    """v0 contract: manifest argument is opaque/unused.

    Pass a clearly-sentinel object; setup() must not call any attribute on it.
    """

    class SentinelManifest:
        def __getattr__(self, item: str) -> object:  # pragma: no cover - guard only
            raise AssertionError(
                f"setup() must NOT read manifest attributes in v0 (touched {item!r})"
            )

    sentinel = SentinelManifest()
    # mypy: type-checker doesn't know setup() doesn't touch the manifest.
    GenericIntegration().setup(tmp_project, sentinel, None)  # type: ignore[arg-type]
    assert (tmp_project / ".agents/skills").is_dir()


@pytest.mark.parametrize(
    "escape_value",
    [
        "../escape/skills",
        "../../etc/foo",
        "a/../../escape",
    ],
)
def test_generic_setup_rejects_skills_dir_escaping_project_root(
    escape_value: str,
    tmp_project: Path,
    minimal_manifest: Manifest,
) -> None:
    """R4 — ``--skills-dir`` whose resolved target escapes ``project_root`` is rejected.

    ``resolve_skills_dir`` still returns a not-absolute path; containment is
    enforced one layer down in ``setup()`` where the absolute join happens.
    """

    with pytest.raises(MalformedOptionError) as exc_info:
        GenericIntegration().setup(tmp_project, minimal_manifest, {"skills_dir": escape_value})

    payload = exc_info.value.to_dict()
    assert payload["code"] == "malformed_option"
    assert payload["rule"] == "escapes_project_root"
    assert payload["value"] == escape_value
    # Default dir MUST NOT be created either.
    assert (tmp_project / ".agents/skills").exists() is False


@pytest.mark.parametrize(
    "integration_cls,expected_dir",
    [
        (ClaudeIntegration, ".claude/skills"),
        (GenericIntegration, ".agents/skills"),
    ],
)
def test_setup_marker_content_matches_key(
    integration_cls: type[ClaudeIntegration | GenericIntegration],
    expected_dir: str,
    tmp_project: Path,
    minimal_manifest: Manifest,
) -> None:
    """Marker content is determined by ``key`` alone — no timestamp, no version."""

    integration_cls().setup(tmp_project, minimal_manifest, None)
    marker = tmp_project / expected_dir / MARKER_NAME
    assert marker.read_text(encoding="utf-8") == _expected_marker_text(integration_cls.key)
