"""FR-034 — `.bookwright/init-options.json` envelope shape and round-trip."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from bookwright import __version__ as _BOOKWRIGHT_VERSION
from bookwright.cli import app
from bookwright.commands._init_envelope import InitOptionsRecord, ResolvedInvocation

_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _load_options(project_root: Path) -> dict[str, Any]:
    return json.loads((project_root / ".bookwright" / "init-options.json").read_text())  # type: ignore[no-any-return]


def test_envelope_shape(runner: CliRunner, scaffold_in_tmp: Path) -> None:
    result = runner.invoke(app, ["init", "mi-libro", "--no-git", "--json"])
    assert result.exit_code == 0, result.stdout

    payload = _load_options(scaffold_in_tmp / "mi-libro")
    assert payload["schema_version"] == 1
    assert _ISO_UTC_RE.match(str(payload["created_at"]))
    assert payload["bookwright_version"] == _BOOKWRIGHT_VERSION

    record = InitOptionsRecord.model_validate(payload)
    assert isinstance(record.options, ResolvedInvocation)


@pytest.mark.parametrize(
    "argv,expected_fields",
    [
        (
            ["init", "mi-libro", "--no-git", "--json"],
            {"mode": "named", "project_slug": "mi-libro", "integration_key": "claude"},
        ),
        (
            ["init", "mi-libro", "--integration", "generic", "--no-git", "--json"],
            {"mode": "named", "integration_key": "generic"},
        ),
        (
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
            {
                "integration_key": "generic",
                "integration_skills_dir": ".cursor/skills",
            },
        ),
        (
            ["init", "--here", "--no-git", "--json"],
            {"mode": "here"},
        ),
        (
            ["init", "mi-libro", "--no-git", "--ai", "claude", "--json"],
            {"deprecated_flags_seen": ["--ai"]},
        ),
    ],
)
def test_options_round_trip(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    argv: list[str],
    expected_fields: dict[str, object],
) -> None:
    # `--here` needs a name on cwd; create a subdir and chdir into it.
    if "--here" in argv:
        target = scaffold_in_tmp / "my-here-project"
        target.mkdir()
        (target / ".bookwright_temp").write_text("temp", encoding="utf-8") if False else None
        # cd into the new dir
        import os as _os  # noqa: PLC0415

        _os.chdir(target)

    result = runner.invoke(app, argv)
    assert result.exit_code == 0, result.stdout

    # Find the generated project root.
    if "--here" in argv:
        project_root = Path.cwd()
    else:
        project_root = scaffold_in_tmp / "mi-libro"

    payload = _load_options(project_root)
    record = InitOptionsRecord.model_validate(payload)

    for field, value in expected_fields.items():
        actual = getattr(record.options, field)
        assert actual == value, f"{field}: expected {value!r}, got {actual!r}"


def test_options_json_committed_to_git(
    runner: CliRunner,
    scaffold_in_tmp: Path,
    git_available: None,
) -> None:
    """The init-options.json file is part of the initial commit (FR-034)."""

    result = runner.invoke(app, ["init", "mi-libro"])
    assert result.exit_code == 0

    completed = subprocess.run(
        ["git", "show", "HEAD", "--stat"],
        cwd=str(scaffold_in_tmp / "mi-libro"),
        capture_output=True,
        text=True,
        check=True,
    )
    assert "init-options.json" in completed.stdout
