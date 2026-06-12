"""Unit coverage for the shared command-layer envelope (Principle IX).

``emit_json`` / ``emit_error`` are single-sourced in
:mod:`bookwright.commands._envelope`. This pins the branch that only the *human*
mode reaches: the ``stderr`` write in :func:`emit_error` when ``--json`` is off.
The error-body skeleton itself is single-sourced in ``BookwrightError.to_json``;
the ``ManifestError``→``invalid_manifest`` remap is covered alongside its callers.
"""

from __future__ import annotations

import pytest

from bookwright.commands._envelope import emit_error, ok_payload


def test_emit_error_human_mode_writes_prefixed_line_to_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    emit_error({"status": "error", "code": "x", "message": "boom"}, json_output=False)
    captured = capsys.readouterr()
    assert captured.out == ""  # nothing on stdout in human mode
    assert captured.err == "bookwright: error: boom\n"


# --- ok_payload (020 research D6) --------------------------------------------


def test_ok_payload_emits_the_status_ok_literal_first() -> None:
    payload = ok_payload(focus=None, state={"phase": "drafting"})
    assert payload == {"status": "ok", "focus": None, "state": {"phase": "drafting"}}
    # "status" leads the document — key order is insertion order, and the
    # serialized envelope must be byte-stable across runs.
    assert next(iter(payload)) == "status"


def test_ok_payload_with_no_fields_is_the_bare_skeleton() -> None:
    assert ok_payload() == {"status": "ok"}


def test_ok_payload_passes_fields_through_without_mutating_them() -> None:
    state = {"graph": {"available": True}}
    actions = [{"skill": "bookwright-research"}]
    payload = ok_payload(state=state, next_actions=actions)
    assert payload["state"] is state  # passthrough, not a copy
    assert payload["next_actions"] is actions
    assert state == {"graph": {"available": True}}  # inputs untouched
    assert ok_payload() is not ok_payload()  # a fresh dict every call
