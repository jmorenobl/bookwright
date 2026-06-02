"""US1 — `bookwright init <NAME>` default path."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.core.manifest import Manifest

from .conftest import dirhash

pytestmark = pytest.mark.usefixtures("git_available")


def _read_options(project_root: Path) -> dict[str, Any]:
    payload = (project_root / ".bookwright" / "init-options.json").read_text(encoding="utf-8")
    return json.loads(payload)  # type: ignore[no-any-return]


def test_default_scaffold_named_mode(
    runner: CliRunner,
    scaffold_in_tmp: Path,
) -> None:
    """Acceptance Scenario 1 — `bookwright init mi-libro` default path."""

    t0 = time.monotonic()
    result = runner.invoke(app, ["init", "mi-libro", "--json"])
    t1 = time.monotonic()

    assert result.exit_code == 0, result.stdout
    assert (t1 - t0) < 60.0, "SC-001 wall-clock budget exceeded"

    project_root = scaffold_in_tmp / "mi-libro"
    assert project_root.is_dir()
    assert (project_root / "manifest.toml").is_file()
    assert (project_root / "README.md").is_file()
    assert (project_root / "bible" / "constitution.md").is_file()
    assert (project_root / "outline" / "scenes.md").is_file()
    assert (project_root / "manuscript" / ".gitkeep").is_file()
    assert (project_root / ".bookwright" / "vocabularies" / "propp.ttl").is_file()
    assert (project_root / ".bookwright" / "vocabularies" / "greimas.ttl").is_file()
    assert (project_root / ".claude" / "skills" / "bookwright-bible" / "SKILL.md").is_file()
    assert not (project_root / ".claude" / "skills" / ".bookwright-skills-placeholder").exists()

    manifest = Manifest.load(project_root / "manifest.toml")
    assert manifest.book.title == "mi-libro"
    assert manifest.book.authors  # non-empty
    assert manifest.book.type == "novel"
    assert manifest.book.status == "idea"
    assert manifest.integration.key == "claude"
    assert manifest.integration.skills_dir == ".claude/skills"
    assert manifest.integration.options == {}

    completed = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Initial commit from bookwright init" in completed.stdout

    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.strip() == ""


def test_named_mode_preserves_user_casing(
    runner: CliRunner,
    scaffold_in_tmp: Path,
) -> None:
    """Acceptance Scenario 3 — title preserves casing, dir is slugified."""

    result = runner.invoke(app, ["init", "Mi Libro", "--json", "--no-git"])
    assert result.exit_code == 0, result.stdout

    project_root = scaffold_in_tmp / "mi-libro"
    assert project_root.is_dir()

    manifest = Manifest.load(project_root / "manifest.toml")
    assert manifest.book.title == "Mi Libro"


def test_named_mode_reuses_empty_target(
    runner: CliRunner,
    scaffold_in_tmp: Path,
) -> None:
    """FR-027 — an empty pre-existing target reuses without prompting."""

    target = scaffold_in_tmp / "mi-libro"
    target.mkdir()

    result = runner.invoke(app, ["init", "mi-libro", "--json", "--no-git"])
    assert result.exit_code == 0, result.stdout
    assert (target / "manifest.toml").is_file()


def test_named_mode_force_overwrites_collisions(
    runner: CliRunner,
    scaffold_in_tmp: Path,
) -> None:
    """FR-026 — `--force` overwrites name collisions but keeps unrelated files."""

    target = scaffold_in_tmp / "mi-libro"
    target.mkdir()
    (target / "manifest.toml").write_text("# pre-existing", encoding="utf-8")
    (target / "notes.txt").write_text("USER NOTES", encoding="utf-8")

    result = runner.invoke(app, ["init", "mi-libro", "--force", "--json", "--no-git"])
    assert result.exit_code == 0, result.stdout

    manifest = Manifest.load(target / "manifest.toml")
    assert manifest.book.title == "mi-libro"
    assert (target / "notes.txt").read_text(encoding="utf-8") == "USER NOTES"

    backup_root = target / ".bookwright" / "cache" / "backup"
    assert not backup_root.exists() or not any(backup_root.rglob("*"))


def test_default_no_writes_outside_project_root(
    runner: CliRunner,
    scaffold_in_tmp: Path,
) -> None:
    """FR-014 — nothing is written outside ``project_root``."""

    sibling = scaffold_in_tmp / "sibling.txt"
    sibling.write_text("untouched", encoding="utf-8")

    snapshot_before = dirhash(scaffold_in_tmp)

    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])
    assert result.exit_code == 0, result.stdout

    # Filter the snapshot to siblings that pre-existed (exclude mi-libro/).
    project_root = scaffold_in_tmp / "mi-libro"

    def _filter_outside_project(entries: list[tuple[str, str]]) -> list[tuple[str, str]]:
        root_rel = project_root.relative_to(scaffold_in_tmp).as_posix()
        prefix = root_rel + "/"
        return [(rel, h) for rel, h in entries if rel != root_rel and not rel.startswith(prefix)]

    snapshot_after = dirhash(scaffold_in_tmp)
    assert _filter_outside_project(snapshot_after) == snapshot_before
