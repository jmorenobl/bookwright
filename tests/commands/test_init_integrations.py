"""US3 — `--integration` and `--integration-options`."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.core.manifest import Manifest

from .conftest import dirhash


def test_default_integration_is_claude(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["integration"]["key"] == "claude"
    assert payload["integration"]["skills_dir"] == ".claude/skills"
    assert (scaffold_in_tmp / "mi-libro" / ".claude" / "skills").is_dir()


def test_integration_generic(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    result = runner.invoke(
        app, ["init", "mi-libro", "--integration", "generic", "--no-git", "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["integration"]["key"] == "generic"
    assert payload["integration"]["skills_dir"] == ".agents/skills"

    project_root = scaffold_in_tmp / "mi-libro"
    assert (project_root / ".agents" / "skills").is_dir()
    assert not (project_root / ".claude").exists()


def test_integration_generic_with_skills_dir_override(
    runner: CliRunner, scaffold_in_tmp: Path
) -> None:
    result = runner.invoke(
        app,
        [
            "init",
            "mi-libro",
            "--integration",
            "generic",
            "--integration-options",
            "--skills-dir .cursor/skills",
            "--no-git",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["integration"]["skills_dir"] == ".cursor/skills"

    project_root = scaffold_in_tmp / "mi-libro"
    assert (project_root / ".cursor" / "skills").is_dir()

    manifest = Manifest.load(project_root / "manifest.toml")
    assert manifest.integration.skills_dir == ".cursor/skills"
    assert manifest.integration.options == {"skills_dir": ".cursor/skills"}


def test_unknown_integration_fails(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    snapshot = dirhash(scaffold_in_tmp)

    result = runner.invoke(
        app, ["init", "mi-libro", "--integration", "copilot", "--no-git", "--json"]
    )
    assert result.exit_code == 5, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "unknown_integration"
    assert payload["details"]["value"] == "copilot"
    assert payload["details"]["valid"] == ["claude", "generic"]

    assert dirhash(scaffold_in_tmp) == snapshot


def test_unknown_option_fails(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    snapshot = dirhash(scaffold_in_tmp)

    result = runner.invoke(
        app,
        [
            "init",
            "mi-libro",
            "--integration",
            "generic",
            "--integration-options",
            "--cursor-dir x",
            "--no-git",
            "--json",
        ],
    )
    assert result.exit_code == 5, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "unknown_option"
    assert payload["details"]["value"] == "--cursor-dir"
    assert "--cursor-dir" in payload["message"]

    assert dirhash(scaffold_in_tmp) == snapshot


def test_malformed_missing_value(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    snapshot = dirhash(scaffold_in_tmp)

    result = runner.invoke(
        app,
        [
            "init",
            "mi-libro",
            "--integration",
            "generic",
            "--integration-options",
            "--skills-dir",
            "--no-git",
            "--json",
        ],
    )
    assert result.exit_code == 5, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "malformed_option"
    assert payload["details"]["value"] == "--skills-dir"
    assert "--skills-dir" in payload["message"]

    assert dirhash(scaffold_in_tmp) == snapshot


def test_malformed_shell_syntax(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    snapshot = dirhash(scaffold_in_tmp)

    raw = '"--skills-dir'
    result = runner.invoke(
        app,
        [
            "init",
            "mi-libro",
            "--integration",
            "generic",
            "--integration-options",
            raw,
            "--no-git",
            "--json",
        ],
    )
    assert result.exit_code == 5, result.stdout
    payload = json.loads(result.stdout)
    assert payload["code"] == "malformed_option"
    assert payload["details"]["value"] == raw
    assert raw in payload["message"]

    assert dirhash(scaffold_in_tmp) == snapshot


def _filter_diverging(entries: list[tuple[str, str]]) -> dict[str, str]:
    """Remove paths that legitimately differ between integrations."""

    keep: dict[str, str] = {}
    for rel, digest in entries:
        if rel in {".claude", ".agents"}:
            continue
        if rel.startswith(".claude/") or rel.startswith(".agents/"):
            continue
        if rel == "manifest.toml":
            continue
        if rel == ".bookwright/init-options.json":
            continue
        keep[rel] = digest
    return keep


def test_sc008_tree_independent_of_integration(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    """SC-008 — non-integration files identical across integrations."""

    claude_root = scaffold_in_tmp / "claude-project"
    generic_root = scaffold_in_tmp / "generic-project"
    claude_root.mkdir()
    generic_root.mkdir()

    import os as _os  # noqa: PLC0415

    _os.chdir(claude_root)
    r1 = runner.invoke(app, ["init", "mi-libro", "--integration", "claude", "--no-git", "--json"])
    assert r1.exit_code == 0, r1.stdout

    _os.chdir(generic_root)
    r2 = runner.invoke(app, ["init", "mi-libro", "--integration", "generic", "--no-git", "--json"])
    assert r2.exit_code == 0, r2.stdout

    claude_filtered = _filter_diverging(dirhash(claude_root / "mi-libro"))
    generic_filtered = _filter_diverging(dirhash(generic_root / "mi-libro"))
    assert claude_filtered == generic_filtered
