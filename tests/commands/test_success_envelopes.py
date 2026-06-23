"""Byte-pinning regression for the ``--json`` success envelopes (iteration 027, FR-005).

Every agent-facing success document must be one compact JSON line (``,``/``:``
separators) plus a single trailing ``\\n``, with a fixed key order — the shape
:func:`bookwright.commands._envelope.ok_payload` + :func:`emit_json` and the
``BuildReport`` serializer single-source. These tests pin the **stdout bytes** and
exit codes of ``check``, ``focus show/set/clear``, ``graph query`` and
``graph build`` so any drift in separators, key order, or the trailing newline
fails CI — the guarantee that routing every success document through the single
source is byte-neutral, and that the ``unresolved_references`` key keeps its
envelope slot (FR-016/FR-017).

The two deterministic-by-construction commands (``check``, ``graph build``) carry
environment-dependent values (interpreter version, triple counts), so their pins
assert the *encoding* (compact round-trip + single trailing newline) and the exact
key order rather than a frozen integer; the fully deterministic commands pin the
literal bytes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from bookwright.commands._envelope import render_json
from tests.commands.graph.conftest import scaffold_project
from tests.fixtures.manifests import MINIMAL_MANIFEST, with_focus


def _is_compact_one_line_doc(stdout: str) -> bool:
    """True iff ``stdout`` is exactly one compact JSON document + a single ``\\n``."""
    return (
        stdout.endswith("\n")
        and stdout.count("\n") == 1
        and stdout == render_json(json.loads(stdout))
    )


# --- check (no top-level "status" key, encoding pinned) ----------------------


def test_check_envelope_is_compact_without_status_key(runner: CliRunner) -> None:
    result = runner.invoke(app, ["check", "--json"])
    assert result.exit_code == 0  # every declared dep importable in the test env
    payload = json.loads(result.stdout)
    assert set(payload) == {"ok", "checks"}  # deliberately no top-level "status"
    assert payload["ok"] is True
    assert _is_compact_one_line_doc(result.stdout)


# --- focus show / set / clear (literal byte pins) ----------------------------


def _focus_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, block: str | None) -> Path:
    root = tmp_path / "my-novel"
    root.mkdir()
    text = MINIMAL_MANIFEST if block is None else with_focus(block)
    (root / "manifest.toml").write_text(text, encoding="utf-8")
    monkeypatch.chdir(root)
    return root


def test_focus_show_present_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _focus_project(
        tmp_path, monkeypatch, 'target = "cap-04"\nnotes = "n"\nupdated_at = "2026-06-11"\n'
    )
    code, out = runner_invoke(["focus", "show", "--json"])
    assert code == 0
    assert out == (
        '{"status":"ok","focus":{"target":"cap-04","notes":"n","updated_at":"2026-06-11"}}\n'
    )


def test_focus_show_absent_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _focus_project(tmp_path, monkeypatch, None)
    code, out = runner_invoke(["focus", "show", "--json"])
    assert code == 0
    assert out == '{"status":"ok","focus":null}\n'


def test_focus_set_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _focus_project(tmp_path, monkeypatch, None)
    # Pin the date seam so the stamped `updated_at` is deterministic (research D5).
    monkeypatch.setattr("bookwright.commands.focus.set_._today", lambda: "2026-06-14")
    code, out = runner_invoke(["focus", "set", "--target", "cap-05", "--notes", "n", "--json"])
    assert code == 0
    assert out == (
        '{"status":"ok","focus":{"target":"cap-05","notes":"n","updated_at":"2026-06-14"}}\n'
    )


def test_focus_clear_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _focus_project(
        tmp_path, monkeypatch, 'target = "cap-04"\nnotes = "n"\nupdated_at = "2026-06-11"\n'
    )
    code, out = runner_invoke(["focus", "clear", "--json"])
    assert code == 0
    assert out == '{"status":"ok","cleared":true}\n'


def test_focus_clear_noop_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _focus_project(tmp_path, monkeypatch, None)
    code, out = runner_invoke(["focus", "clear", "--json"])
    assert code == 0
    assert out == '{"status":"ok","cleared":false}\n'


# --- graph query (literal byte pin via a deterministic empty-result query) ----


def test_graph_query_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    scaffold_project(tmp_path / "my-novel")
    monkeypatch.chdir(tmp_path / "my-novel")
    assert runner_invoke(["graph", "build", "--json"])[0] == 0  # graph.ttl must exist
    # A query that matches nothing → a stable {"status":"ok","results":[],"count":0}.
    code, out = runner_invoke(
        ["graph", "query", "SELECT ?x WHERE { ?x a <https://example.org/none> }", "--json"]
    )
    assert code == 0
    assert out == '{"status":"ok","results":[],"count":0}\n'


# --- graph build (encoding + exact key order, incl. renamed key slot) --------


def test_graph_build_envelope_encoding_and_key_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scaffold_project(tmp_path / "my-novel")
    monkeypatch.chdir(tmp_path / "my-novel")
    code, out = runner_invoke(["graph", "build", "--json"])
    assert code == 0
    assert _is_compact_one_line_doc(out)
    payload = json.loads(out)
    assert payload["status"] == "ok"
    # The full key order is the frozen contract; `untyped_vocab_terms` (iteration 047)
    # sits between `unresolved_references` and `sources` (FR-017).
    assert list(payload) == [
        "status",
        "files_processed",
        "entities",
        "triples",
        "skipped",
        "unknown_keys",
        "unresolved_references",
        "untyped_vocab_terms",
        "sources",
        "findings",
        "anchors",
        "research_warnings",
        "graph_path",
    ]


# --- a single CliRunner driving the in-process app ---------------------------

_RUNNER = CliRunner()


def runner_invoke(args: list[str]) -> tuple[int, str]:
    """Invoke the CLI in-process, returning ``(exit_code, stdout)``."""
    result = _RUNNER.invoke(app, args)
    return result.exit_code, result.stdout
