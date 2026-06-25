"""``bookwright validate`` integration — baseline.

SC-001: a project with one inconsistency per built-in validator → the human report
names each (validator / rule / why) and exits 1. SC-002: a clean project → "no
violations found", exit 0. A temporal cycle renders its resolved timeline locator
(post-048: all four temporal rules carry a source).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookwright.cli import app
from tests.validation.conftest import (
    UnitSpec,
    build_and_save_graph,
    write_project,
)


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
    assert result.exit_code == 0  # SC-002 — no error-severity finding
    # A genuinely clean project no longer reads as "no violations found": the always-dormant
    # `character_unknown_mentions` abstainer (issue #1 track A) keeps the `not_evaluated`
    # channel non-empty on EVERY project, so the report shows the `not evaluated:` section
    # instead. Since iteration 044 its entry is a `pending_capability` (a permanent
    # capability-gap): it stays VISIBLE here (FR-010) but does NOT deny green — visibility
    # and the green predicate are decoupled. Its label reads as a known limitation, never
    # an actionable input gap.
    assert "no violations found" not in result.stdout
    assert "not evaluated:" in result.stdout
    assert (
        "character_unknown_mentions [known limitation — no action available yet]" in result.stdout
    )


def test_temporal_cycle_renders_with_resolved_location(
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
    # Post-048 the cycle resolves a source from the SCC's smallest event (FR-001/SC-002),
    # so it renders the timeline locator, not "(no specific location)".
    assert "bible/timeline.md" in result.stdout
    assert "(no specific location)" not in result.stdout


def test_no_project_exits_two(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 2
    assert "error:" in result.stderr


# --- --json, --scope, --severity, CI gate -----------------------------------


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
        "character_unknown_mentions",
        "setting_continuity",
        "focalization",
        "factual_anchor",
        "narrative_structure",
    }
    assert "{" not in result.stderr  # no JSON leaked to stderr


def test_orphan_error_and_abstainer_coexist_in_one_run(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Acceptance scenario 1 / contract C3: the orphan `error` (Fantasma, never mentioned)
    # and the open-set abstainer both surface in the SAME run — neither suppresses the
    # other (the per-run channel 040 created to avoid exactly this). The abstainer raised
    # NotEvaluated, so it lands in not_evaluated[], NOT errors[] (it is not a crash).
    root = _scaffold_bad(project_root)  # off-roster proper nouns + the Fantasma orphan
    monkeypatch.chdir(root)
    payload = json.loads(runner.invoke(app, ["validate", "--json"]).stdout)

    orphans = [
        v
        for v in payload["violations"]
        if v["validator"] == "character_presence" and v["severity"] == "error"
    ]
    assert len(orphans) == 1
    assert "Fantasma" in orphans[0]["message"]
    # No unknown-mention warning is ever emitted by either validator.
    assert all(v["validator"] != "character_unknown_mentions" for v in payload["violations"])
    # The abstainer surfaces ONLY through not_evaluated — never errors[].
    assert "character_unknown_mentions" in {r["validator"] for r in payload["not_evaluated"]}
    assert all(e["validator"] != "character_unknown_mentions" for e in payload["errors"])


def test_every_not_evaluated_entry_carries_the_code_key(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # FR-005 (iteration 053, contract C3): every serialized not_evaluated[] entry carries
    # the additive `code` key. The returned abstentions set it (undeclared_characters,
    # head_hopping, first_person_recall); a raised one serializes `code: null`.
    root = _scaffold_bad(project_root)
    monkeypatch.chdir(root)
    payload = json.loads(runner.invoke(app, ["validate", "--json"]).stdout)

    entries = payload["not_evaluated"]
    assert entries  # the abstainers are always present
    for entry in entries:
        assert "code" in entry  # additive key on EVERY entry
    codes = {r["validator"]: r.get("code") for r in entries}
    assert codes["character_unknown_mentions"] == "undeclared_characters"


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


# --- narrative_structure through the --json envelope (iteration 031) ---------


def test_narrative_structure_orphan_in_json_envelope(
    runner: CliRunner, project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # An orphan beat surfaces through the existing envelope as a warning: the gate
    # stays clean and no new top-level key appears (FR-003, SC-003).
    write_project(
        project_root,
        units=[
            UnitSpec("anchored", "Anchored Beat", sequence="Act I", order=1),
            UnitSpec("orphan", "Orphan Beat"),
        ],
    )
    build_and_save_graph(project_root, outline=True)
    monkeypatch.chdir(project_root)

    result = runner.invoke(app, ["validate", "--json"])
    payload = json.loads(result.stdout)

    # The envelope gains the additive `not_evaluated` sibling key (iteration 040); the
    # other keys keep their shape. narrative_structure (this test's subject) evaluated,
    # so it is NOT in the channel — regardless of which input-less validators are.
    assert set(payload) == {"status", "failed", "violations", "errors", "not_evaluated", "summary"}
    assert "narrative_structure" not in {r["validator"] for r in payload["not_evaluated"]}
    assert payload["failed"] is False  # warning-only run never gates CI
    assert result.exit_code == 0
    orphans = [v for v in payload["violations"] if v["validator"] == "narrative_structure"]
    assert len(orphans) == 1
    finding = orphans[0]
    assert set(finding) == {"validator", "severity", "message", "source", "triples"}
    assert finding["severity"] == "warning"
    assert "Orphan Beat" in finding["message"]  # the unit's human authored name (iter 049)
    assert finding["source"].startswith("outline/units/orphan.md")
    assert finding["triples"] == []


# --- [validators] config + custom validators --------------------------------

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
