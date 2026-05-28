"""CliRunner-based coverage of `bookwright check` in human and --json modes."""

import importlib
import json
from typing import Any

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.commands.check import RUNTIME_MODULES


def test_check_human(runner: CliRunner) -> None:
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "OK" in result.stdout


def test_check_json_byte_exact(runner: CliRunner) -> None:
    result = runner.invoke(app, ["check", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["ok"] is True
    python_version_checks = [c for c in parsed["checks"] if c["name"] == "python_version"]
    assert len(python_version_checks) == 1
    dependency_names = {c["name"] for c in parsed["checks"] if c["name"].startswith("dependency:")}
    expected_names = {f"dependency:{m}" for m in RUNTIME_MODULES}
    assert dependency_names == expected_names
    assert result.stdout == json.dumps(parsed, separators=(",", ":")) + "\n"


def test_check_failure_when_dependency_missing(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_import_module = importlib.import_module
    broken = next(iter(RUNTIME_MODULES))

    def fake_import_module(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == broken:
            raise ImportError(f"forced failure for {name}")
        return real_import_module(name, *args, **kwargs)

    monkeypatch.setattr("bookwright.commands.check.importlib.import_module", fake_import_module)
    result = runner.invoke(app, ["check", "--json"])
    assert result.exit_code == 1
    parsed = json.loads(result.stdout)
    assert parsed["ok"] is False
    failing = [c for c in parsed["checks"] if c["name"] == f"dependency:{broken}"]
    assert len(failing) == 1
    assert failing[0]["status"] == "fail"
    assert failing[0]["detail"]
