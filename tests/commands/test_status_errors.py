"""``bookwright status`` failure modes (020, research D4).

Every contract error row: envelope code + exit under ``--json``, the
human-mode channel discipline, per-corpus exit parity with ``graph build``
(clarification #3), and the previous-cache-untouched guarantee on failure.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from tests.commands.graph.conftest import scaffold_project


def _status(runner: CliRunner, *, json_output: bool = True) -> tuple[int, str]:
    result = runner.invoke(app, ["status", *(["--json"] if json_output else [])])
    return result.exit_code, result.stdout


def _envelope(stdout: str) -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(stdout)  # one document on stdout (FR-011)
    assert payload["status"] == "error"
    return payload


def _build_exit(runner: CliRunner) -> int:
    """``graph build``'s exit on the same corpus — the parity oracle (D4)."""
    return runner.invoke(app, ["graph", "build", "--json"]).exit_code


@pytest.fixture()
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A research-carrying tiny-novel project, cwd inside it."""
    root = scaffold_project(tmp_path / "my-novel", research="minimal")
    monkeypatch.chdir(root)
    return root


# --- exit 2: configuration faults --------------------------------------------


def test_not_a_project_json(outside_project: Path, runner: CliRunner) -> None:
    exit_code, stdout = _status(runner)
    assert exit_code == 2 == _build_exit(runner)
    payload = _envelope(stdout)
    assert payload["code"] == "no_project"
    assert payload["details"]["start"]


def test_not_a_project_human_mode_keeps_stdout_empty(
    outside_project: Path, runner: CliRunner
) -> None:
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr.startswith("bookwright: error: ")


def test_invalid_manifest(project: Path, runner: CliRunner) -> None:
    (project / "manifest.toml").write_text("not toml [", encoding="utf-8")
    exit_code, stdout = _status(runner)
    assert exit_code == 2 == _build_exit(runner)
    assert _envelope(stdout)["code"] == "invalid_manifest"


def test_unknown_indexer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    root = scaffold_project(tmp_path / "my-novel", indexer="grafeo")
    monkeypatch.chdir(root)
    exit_code, stdout = _status(runner)
    assert exit_code == 2 == _build_exit(runner)
    assert _envelope(stdout)["code"] == "unknown_indexer"


def test_malformed_research_corpus(project: Path, runner: CliRunner) -> None:
    (project / "bible" / "research" / "sources.md").write_text(
        "---\nsources: [unbalanced\n---\n", encoding="utf-8"
    )
    exit_code, stdout = _status(runner)
    assert exit_code == 2 == _build_exit(runner)
    # The research error's own code, exactly as graph build emits it (D4).
    assert _envelope(stdout)["code"] == "invalid_research"


# --- exit 3: slug collision ----------------------------------------------------


def test_slug_collision(project: Path, runner: CliRunner) -> None:
    (project / "bible" / "characters" / "dup.md").write_text(
        '---\nname: "Manuel de Aparici"\n---\n', encoding="utf-8"
    )
    exit_code, stdout = _status(runner)
    assert exit_code == 3 == _build_exit(runner)
    assert _envelope(stdout)["code"] == "slug_collision"


# --- exit 4: skipped bible files (corrupt corpus) --------------------------------


def test_skipped_bible_file_is_a_hard_error(project: Path, runner: CliRunner) -> None:
    (project / "bible" / "characters" / "broken.md").write_text(
        "---\nname: : :\n  bad\n---\n", encoding="utf-8"
    )
    exit_code, stdout = _status(runner)
    # graph build exits 4 with a partial graph; status hardens the partial
    # success into a full error while the exit stays aligned per-corpus (D4).
    assert exit_code == 4 == _build_exit(runner)
    payload = _envelope(stdout)
    assert payload["code"] == "skipped_sources"
    skipped = payload["details"]["skipped"]
    assert any("broken.md" in item["path"] and item["reason"] for item in skipped)


# --- failures leave any previous cache untouched ---------------------------------


def test_failure_leaves_the_previous_cache_untouched(project: Path, runner: CliRunner) -> None:
    cache = project / ".bookwright" / "cache" / "status.json"
    ok = runner.invoke(app, ["status", "--json"])
    assert ok.exit_code == 0
    healthy_bytes = cache.read_bytes()

    (project / "bible" / "characters" / "broken.md").write_text(
        "---\nname: : :\n  bad\n---\n", encoding="utf-8"
    )
    exit_code, _stdout = _status(runner)
    assert exit_code == 4
    assert cache.read_bytes() == healthy_bytes  # FR-012: failure leaves the cache alone
