"""Unit coverage for the shared command-layer envelope (Principle IX).

``emit_json`` / ``emit_error`` are single-sourced in
:mod:`bookwright.commands._envelope`. This pins the branch that only the *human*
mode reaches: the ``stderr`` write in :func:`emit_error` when ``--json`` is off.
The error-body skeleton itself is single-sourced in ``BookwrightError.to_json``;
the ``ManifestError``→``invalid_manifest`` remap is covered alongside its callers.
"""

from __future__ import annotations

import pytest

from bookwright.commands._envelope import emit_error


def test_emit_error_human_mode_writes_prefixed_line_to_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    emit_error({"status": "error", "code": "x", "message": "boom"}, json_output=False)
    captured = capsys.readouterr()
    assert captured.out == ""  # nothing on stdout in human mode
    assert captured.err == "bookwright: error: boom\n"
