"""Unit + CLI coverage for the ``graph`` JSON/error envelopes (Principle IX).

Complements ``test_json_contract.py`` (which exercises the ``--json`` happy and
error paths) by pinning the two branches that only the *human* mode reaches: the
``details`` field of :func:`error_payload` and the ``stderr`` write in
:func:`emit_error` when ``--json`` is off.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.commands.graph.envelope import emit_error, error_payload


def test_error_payload_omits_details_when_absent() -> None:
    payload = error_payload("invalid_query", "bad SPARQL")
    assert payload == {"status": "error", "code": "invalid_query", "message": "bad SPARQL"}


def test_error_payload_includes_details_when_present() -> None:
    payload = error_payload("slug_collision", "clash", {"identifier": "aparici"})
    assert payload["details"] == {"identifier": "aparici"}


def test_emit_error_human_mode_writes_prefixed_line_to_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    emit_error({"status": "error", "code": "x", "message": "boom"}, json_output=False)
    captured = capsys.readouterr()
    assert captured.out == ""  # nothing on stdout in human mode
    assert captured.err == "bookwright: error: boom\n"


def test_query_human_error_goes_to_stderr(tiny_novel: Path, runner: CliRunner) -> None:
    """``graph query`` without ``--json`` and no graph built → human error on stderr."""
    result = runner.invoke(app, ["graph", "query", "SELECT ?c WHERE { ?c a golem:G1_Character }"])
    assert result.exit_code == 2
    assert result.stdout.strip() == ""
    assert result.stderr.startswith("bookwright: error:")
