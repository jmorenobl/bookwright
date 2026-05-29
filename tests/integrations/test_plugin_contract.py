"""US5 — plugin extensibility contract (FR-031, SC-007, research R8).

Two assertions:
    1. A ``FakeIntegration`` declared inline + inserted into the registry
       satisfies the public surface (lookup, listing, option parsing,
       ``resolve_skills_dir``, ``setup()``) WITHOUT any edit to the
       existing integration sources.
    2. The content hashes of ``base.py``, ``claude/__init__.py``, and
       ``generic/__init__.py`` are byte-for-byte what they were when this
       test was pinned — the test fails loudly if anyone touches them.

Updating any of the three pinned files MUST accompany an explicit hash
update in this test, making the change visible in code review.
"""

from __future__ import annotations

import hashlib
import pathlib
from pathlib import Path
from typing import ClassVar

import pytest

from bookwright.core import Manifest
from bookwright.integrations import (
    SKILL_PLACEHOLDER_MARKER_NAME,
    IntegrationOption,
    SkillsIntegration,
    UnknownOptionError,
    _register,
    get,
    list_keys,
    parse_options,
)

_SRC_ROOT = pathlib.Path(__file__).resolve().parents[2] / "src" / "bookwright" / "integrations"

# If you intentionally edit any of these files, recompute its sha256 and
# update the value below; the diff makes the change auditable.
_PINNED_FILE_HASHES: dict[str, str] = {
    # base.py refreshed in R6: setup() now also rejects `target == project_root`
    # (empty / `.` / `./` skills_dir values) with rule `resolves_to_project_root`.
    "base.py": "ab33fc0c08485bddcbe449de0a5fcfe6bc64593bb1c7daca4997dfedf7875847",
    "claude/__init__.py": "cd981edd40b5a2cf2de33600f4935accc07d3d77f06241e6740e8f95e0d39ab5",
    "generic/__init__.py": "eff8e531d559ac3c9512c1987593fd07a6ea777cd2b2ed768659642a2ea3c359",
}


def _read_hashes() -> dict[str, str]:
    return {
        rel: hashlib.sha256((_SRC_ROOT / rel).read_bytes()).hexdigest()
        for rel in _PINNED_FILE_HASHES
    }


# ---------- FakeIntegration smoke test ----------


class FakeIntegration(SkillsIntegration):
    """Inline plugin used to prove FR-031 mechanically."""

    key: ClassVar[str] = "fake"
    default_skills_dir: ClassVar[str] = ".fake/skills"
    config: ClassVar[dict[str, str | bool]] = {
        "name": "Fake",
        "install_url": "https://example.org/fake",
        "requires_cli": False,
    }


class FakeWithOptionsIntegration(SkillsIntegration):
    """Second plugin proving ``parse_options`` is generic over ``options()``."""

    key: ClassVar[str] = "fake-with-opts"
    default_skills_dir: ClassVar[str] = ".fake-opts/skills"
    config: ClassVar[dict[str, str | bool]] = {
        "name": "Fake With Options",
        "install_url": "https://example.org/fake-opts",
        "requires_cli": False,
    }

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(flag="--scope", type="string", default="all", help="scope"),
        ]


def test_fake_integration_registers_and_satisfies_surface(
    registry_snapshot: dict[str, type[SkillsIntegration]],
    tmp_project: Path,
    minimal_manifest: Manifest,
) -> None:
    del registry_snapshot  # fixture restores teardown
    # R17 — go through `_register` rather than direct dict assignment so
    # the FR-005 / R13 guards exercise the same path real integrations do.
    _register(FakeIntegration)

    # Lookup and listing.
    assert get("fake") is FakeIntegration
    keys = list_keys()
    assert "fake" in keys
    assert keys == sorted(keys), "list_keys must always be alphabetic"

    # resolve_skills_dir uses base default since no options declared.
    instance = FakeIntegration()
    assert instance.resolve_skills_dir(None) == Path(".fake/skills")

    # setup() materializes the same way Claude/Generic do.
    instance.setup(tmp_project, minimal_manifest, None)
    skills_dir = tmp_project / ".fake/skills"
    assert skills_dir.is_dir()
    assert (skills_dir / SKILL_PLACEHOLDER_MARKER_NAME).read_text(
        encoding="utf-8"
    ) == "bookwright integration: fake — SKILL.md materialization deferred to iteration 9\n"


def test_parse_options_is_generic_over_options(
    registry_snapshot: dict[str, type[SkillsIntegration]],
) -> None:
    del registry_snapshot
    _register(FakeWithOptionsIntegration)

    assert parse_options("--scope wide", FakeWithOptionsIntegration) == {"scope": "wide"}

    with pytest.raises(UnknownOptionError) as exc_info:
        parse_options("--bogus x", FakeWithOptionsIntegration)
    payload = exc_info.value.to_dict()
    assert payload["valid"] == ["--scope"]


# ---------- Pinned-file hash assertion ----------


def test_pinned_files_unchanged() -> None:
    """FR-031 — adding a new integration MUST NOT modify these files."""

    actual = _read_hashes()
    drifted = {
        rel: (expected, actual[rel])
        for rel, expected in _PINNED_FILE_HASHES.items()
        if actual[rel] != expected
    }
    assert not drifted, (
        "The following pinned files have changed since the plugin contract "
        "was last reviewed. If the change is intentional, recompute the "
        "sha256 in `_PINNED_FILE_HASHES` and explain the edit in the commit "
        f"message:\n{drifted}"
    )
