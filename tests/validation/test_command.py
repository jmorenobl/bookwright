"""``bookwright validate`` integration — US1 baseline (T028).

SC-001: a project with one inconsistency per built-in validator → the human report
names each (validator / rule / why) and exits 1. SC-002: a clean project → "no
violations found", exit 0. A location-less finding still renders its rule.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from tests.validation.conftest import build_and_save_graph, write_project


def _dirhash(root: Path) -> list[tuple[str, str]]:
    """Sorted ``(relpath, sha256 | <DIR>)`` snapshot for an FR-020 byte-identity check."""
    entries: list[tuple[str, str]] = []
    for child in sorted(root.rglob("*")):
        rel = child.relative_to(root).as_posix()
        if child.is_file():
            entries.append((rel, hashlib.sha256(child.read_bytes()).hexdigest()))
        elif child.is_dir():
            entries.append((rel, "<DIR>"))
    return entries


CONSTITUTION = "# Constitución\n\nVoz narrativa: tercera persona\n"

# One deliberately injected inconsistency per built-in validator.
_TIMELINE_BAD = """\
---
events:
  - name: "Fundación"
    begin: 1885
    end: 1912
  - name: "Quiebra"
    date: 1884
    follows: ["Fundación"]
---
"""

_MANUSCRIPT_BAD = {
    "cap-01.md": "Aparici fundó la villa, que era coastal.\nYo lo vi todo con mis ojos.\n",
    "cap-02.md": "La villa, inland y polvorienta, decaía.\n",
}


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _scaffold_bad(root: Path) -> Path:
    write_project(
        root,
        characters=["Aparici", "Fantasma"],  # Fantasma is an orphan (error)
        settings=["La villa"],
        timeline=_TIMELINE_BAD,
        constitution=CONSTITUTION,
        manuscript=_MANUSCRIPT_BAD,
    )
    build_and_save_graph(root)
    return root


def test_reports_each_validator_and_exits_one(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _scaffold_bad(project_root)
    monkeypatch.chdir(root)

    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1  # error-severity findings present (SC-001)
    out = result.stdout
    for validator in ("temporal", "character_presence", "setting_continuity", "focalization"):
        assert f"{validator}:" in out, f"{validator} missing from report:\n{out}"


def test_clean_project_reports_none_and_exits_zero(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        settings=["La villa"],
        timeline="""\
        ---
        events:
          - name: "A"
            begin: 1880
            end: 1884
          - name: "B"
            begin: 1885
            follows: ["A"]
        ---
        """,
        constitution=CONSTITUTION,
        manuscript={"cap-01.md": "Aparici cruzó la villa al amanecer.\n"},
    )
    build_and_save_graph(project_root)
    monkeypatch.chdir(project_root)

    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0  # SC-002
    assert "no violations found" in result.stdout


def test_location_less_finding_still_renders(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici esperaba.\n"},
        timeline="""\
        ---
        events:
          - name: "A"
            follows: ["B"]
          - name: "B"
            follows: ["A"]
        ---
        """,
    )
    build_and_save_graph(project_root)
    monkeypatch.chdir(project_root)

    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1
    assert "temporal:" in result.stdout
    assert "(no specific location)" in result.stdout  # a cycle has no source (FR-003/012)


def test_no_project_exits_two(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 2
    assert "error:" in result.stderr


# --- User Story 2: --json, --scope, --severity, CI gate (T032) --------------


def test_json_is_single_document_with_prose_on_stderr(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _scaffold_bad(project_root)
    monkeypatch.chdir(root)

    result = runner.invoke(app, ["validate", "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)  # stdout is exactly one parseable doc (SC-004)
    assert result.stdout.strip().count("\n") == 0  # one line, nothing else on stdout
    assert payload["status"] == "violations"
    assert payload["failed"] is True
    assert set(payload["summary"]["ran"]) == {
        "temporal",
        "character_presence",
        "setting_continuity",
        "focalization",
    }
    assert "{" not in result.stderr  # no JSON leaked to stderr


def test_scope_narrows_report_but_gate_still_fails(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _scaffold_bad(project_root)
    monkeypatch.chdir(root)

    # cap-01 holds no error-severity source (errors are the orphan + the cycle/temporal),
    # so the reported set carries no error, yet the unfiltered gate fails → exit 1 (SC-006).
    result = runner.invoke(app, ["validate", "--scope", "manuscript/cap-01.md", "--json"])
    payload = json.loads(result.stdout)
    assert result.exit_code == 1
    assert payload["failed"] is True
    assert all(v["source"].startswith("manuscript/cap-01.md") for v in payload["violations"])
    assert all(v["severity"] != "error" for v in payload["violations"])


def test_severity_threshold_excludes_lower_levels(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _scaffold_bad(project_root)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["validate", "--severity", "error", "--json"])
    payload = json.loads(result.stdout)
    assert {v["severity"] for v in payload["violations"]} == {"error"}


def test_no_graph_project_exits_zero_with_zero_graph_findings(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # No graph.ttl built → empty indexer → temporal yields nothing (D13.2).
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici cruzó el patio.\n"},
    )
    monkeypatch.chdir(project_root)
    result = runner.invoke(app, ["validate", "--json"])
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["summary"]["by_severity"]["error"] == 0
    assert "temporal" in payload["summary"]["ran"]


def test_run_leaves_tree_byte_identical(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _scaffold_bad(project_root)
    monkeypatch.chdir(root)
    before = _dirhash(root)
    runner.invoke(app, ["validate"])  # human
    runner.invoke(app, ["validate", "--json"])  # machine
    assert _dirhash(root) == before  # FR-020 / D13.4 — writes nothing


def test_rerun_is_byte_identical_ordering(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _scaffold_bad(project_root)
    monkeypatch.chdir(root)
    first = runner.invoke(app, ["validate", "--json"]).stdout
    second = runner.invoke(app, ["validate", "--json"]).stdout
    assert first == second  # SC-003 — byte-identical violations[] ordering


def test_absent_scope_is_empty_scope_exit_two(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _scaffold_bad(project_root)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["validate", "--scope", "manuscript/missing.md", "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["code"] == "empty_scope"


def test_valid_scope_with_no_violations_exits_zero(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A valid in-project scope that simply matches no finding is NOT an error (D10).
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={
            "cap-01.md": "Aparici cruzó el patio.\n",
            "empty.md": "Nada relevante.\n",
        },
    )
    monkeypatch.chdir(project_root)
    result = runner.invoke(app, ["validate", "--scope", "manuscript/empty.md", "--json"])
    payload = json.loads(result.stdout)
    assert result.exit_code == 0
    assert payload["status"] == "ok"
    assert payload["violations"] == []


# --- User Story 3: [validators] config + custom validators (T036) -----------

_CUSTOM_NO_TODO = """
from bookwright.validation import Severity, Violation

class NoTodo:
    name = "no_todo"
    severity_default = Severity.warning
    def validate(self, project, indexer):
        out = []
        for relpath, text in project.manuscript_files():
            for i, line in enumerate(text.splitlines(), start=1):
                if "TODO" in line:
                    out.append(Violation(self.name, Severity.warning,
                                         "leftover TODO marker", f"{relpath}:{i}"))
        return out
"""


def _write_custom(root: Path, name: str, body: str) -> None:
    target = root / ".bookwright" / "validators"
    target.mkdir(parents=True, exist_ok=True)
    (target / name).write_text(body, encoding="utf-8")


def test_disabling_a_builtin_removes_its_findings(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_project(
        project_root,
        characters=["Aparici", "Fantasma"],  # Fantasma would be a character_presence orphan
        manuscript={"cap-01.md": "Aparici cruzó el patio.\n"},
        disabled=["character_presence"],
    )
    monkeypatch.chdir(project_root)
    payload = json.loads(runner.invoke(app, ["validate", "--json"]).stdout)
    assert "character_presence" not in payload["summary"]["ran"]  # SC-008
    assert all(v["validator"] != "character_presence" for v in payload["violations"])


def test_custom_validator_findings_appear(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici trabajó.\nTODO: revisar este capítulo.\n"},
    )
    _write_custom(project_root, "no_todo.py", _CUSTOM_NO_TODO)
    monkeypatch.chdir(project_root)
    payload = json.loads(runner.invoke(app, ["validate", "--json"]).stdout)
    assert "no_todo" in payload["summary"]["ran"]  # SC-007
    todos = [v for v in payload["violations"] if v["validator"] == "no_todo"]
    assert len(todos) == 1
    assert todos[0]["source"] == "manuscript/cap-01.md:2"


def test_malformed_custom_file_surfaces_in_errors_without_crashing(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici cruzó el patio.\n"},
    )
    _write_custom(project_root, "broken.py", "def : not valid python\n")
    monkeypatch.chdir(project_root)
    result = runner.invoke(app, ["validate", "--json"])
    payload = json.loads(result.stdout)
    assert result.exit_code == 0  # a load error never crashes or gates the run
    broken = [e for e in payload["errors"] if e["validator"].endswith("broken.py")]
    assert len(broken) == 1 and broken[0]["phase"] == "load"


def test_unknown_configured_name_exits_two(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Aparici cruzó el patio.\n"},
        enabled=["does_not_exist"],
    )
    monkeypatch.chdir(project_root)
    result = runner.invoke(app, ["validate", "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["code"] == "unknown_validator"
    assert payload["details"]["names"] == ["does_not_exist"]
