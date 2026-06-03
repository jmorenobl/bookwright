"""C1 / FR-006 — the full new-user path, driven in-process over a fresh project.

empty dir → ``init`` → author one character + chapter → edit manifest + constitution
→ ``graph build`` → ``graph query`` → ``validate``. Every ``--json`` invocation must
put a single JSON document on stdout and nothing else (Principle IX / VR-9), and the
run includes a deliberately broken query to prove the structured fault model end to
end (malformed SPARQL → exit 3). ``--no-git`` keeps the run hermetic (no git binary
dependency); the workflow under test is the content pipeline, not the git step.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app

CHARACTER_MD = """\
---
name: "Aurora Vidal"
born: 1990
narrative_roles:
  - protagonist
---

Aurora Vidal observa la ciudad desde la azotea.
"""

CHAPTER_MD = """\
# Capítulo 1

Aurora subió a la azotea cuando la ciudad empezaba a encenderse.
"""

CONSTITUTION_MARKER = "## Voz y registro\n\n- **Voz narrativa**: Primera persona.\n"

COUNT_CHARACTERS = "SELECT (COUNT(?c) AS ?n) WHERE { ?c a golem:G1_Character }"


def _init_project(cli: CliRunner, workdir: Path) -> Path:
    """Run ``init`` in ``workdir`` and return the created project directory."""
    result = cli.invoke(app, ["init", "mi-novela", "--integration", "claude", "--no-git", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    project = workdir / "mi-novela"
    assert project.is_dir()
    return project


def test_init_scaffolds_the_expected_tree(cli: CliRunner, workdir: Path) -> None:
    """``init`` creates the manifest and the four content roots incl. the skills dir."""
    project = _init_project(cli, workdir)
    assert (project / "manifest.toml").is_file()
    assert (project / "bible").is_dir()
    assert (project / "outline").is_dir()
    assert (project / "manuscript").is_dir()
    assert (project / ".claude" / "skills").is_dir()


def test_full_workflow(cli: CliRunner, workdir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """init → author → edit → build → query → validate, asserting each step (C1)."""
    project = _init_project(cli, workdir)
    monkeypatch.chdir(project)

    # Author one character + a chapter that names it (so validate stays clean).
    (project / "bible" / "characters" / "aurora.md").write_text(CHARACTER_MD, encoding="utf-8")
    (project / "manuscript" / "01.md").write_text(CHAPTER_MD, encoding="utf-8")

    # Edit manifest.toml and bible/constitution.md; assert the plain-text edits persist.
    manifest_path = project / "manifest.toml"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8").replace('status = "idea"', 'status = "drafting"'),
        encoding="utf-8",
    )
    assert 'status = "drafting"' in manifest_path.read_text(encoding="utf-8")
    constitution = project / "bible" / "constitution.md"
    constitution.write_text(CONSTITUTION_MARKER, encoding="utf-8")
    assert "Primera persona" in constitution.read_text(encoding="utf-8")

    # graph build: exit 0, clean, graph.ttl written.
    build = cli.invoke(app, ["graph", "build", "--json"])
    assert build.exit_code == 0, build.stdout
    build_payload = json.loads(build.stdout)
    assert build_payload["skipped"] == []
    assert build_payload["unknown_keys"] == []
    assert (project / "bible" / "graph.ttl").is_file()

    # graph query: a single JSON doc on stdout with the expected count.
    query = cli.invoke(app, ["graph", "query", COUNT_CHARACTERS, "--json"])
    assert query.exit_code == 0
    query_payload = json.loads(query.stdout)  # stdout is exactly one JSON document
    assert query_payload["status"] == "ok"
    assert int(query_payload["results"][0]["n"]) == 1

    # validate: human form (exit 0) and --json (single doc, zero error-severity).
    assert cli.invoke(app, ["validate"]).exit_code == 0
    validate = cli.invoke(app, ["validate", "--json"])
    assert validate.exit_code == 0
    validate_payload = json.loads(validate.stdout)
    assert validate_payload["failed"] is False
    assert validate_payload["summary"]["by_severity"]["error"] == 0


def test_malformed_query_fails_with_structured_error(
    cli: CliRunner, workdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A broken SPARQL string is a structured exit-3 fault, not a traceback (C1 negative)."""
    project = _init_project(cli, workdir)
    monkeypatch.chdir(project)
    assert cli.invoke(app, ["graph", "build", "--json"]).exit_code == 0

    result = cli.invoke(app, ["graph", "query", "SELECT ?c WHERE {{{", "--json"])
    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["code"] == "invalid_query"
