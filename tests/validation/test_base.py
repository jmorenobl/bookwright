"""Core finding types + the cached context accessors (T008)."""

from __future__ import annotations

from pathlib import Path

from bookwright.validation.base import Severity, ValidationContext, Violation
from tests.validation.conftest import load_context, write_project


def test_severity_ordering_and_threshold() -> None:
    assert Severity.error.at_least(Severity.warning)
    assert Severity.warning.at_least(Severity.warning)
    assert not Severity.warning.at_least(Severity.error)
    assert Severity.info.at_least(Severity.info)
    assert not Severity.info.at_least(Severity.warning)


def test_violation_source_split_and_to_json() -> None:
    located = Violation(
        "temporal", Severity.error, "boom", "bible/timeline.md:5", (("a", "b", "c"),)
    )
    assert located.source_file() == "bible/timeline.md"
    assert located.source_line() == 5
    assert located.to_json() == {
        "validator": "temporal",
        "severity": "error",
        "message": "boom",
        "source": "bible/timeline.md:5",
        "triples": [["a", "b", "c"]],
    }


def test_violation_without_line_or_source() -> None:
    file_only = Violation("v", Severity.warning, "m", "manuscript/cap.md")
    assert file_only.source_file() == "manuscript/cap.md"
    assert file_only.source_line() is None

    location_less = Violation("v", Severity.error, "m", None)
    assert location_less.source_file() is None
    assert location_less.source_line() is None


def test_violation_is_hashable_for_dedupe() -> None:
    a = Violation("v", Severity.error, "m", "x:1", (("s", "p", "o"),))
    b = Violation("v", Severity.error, "m", "x:1", (("s", "p", "o"),))
    assert a == b
    assert len({a, b}) == 1


def test_context_accessors_cache_and_read(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici", "Peña"],
        settings=["Ayelo"],
        manuscript={"cap-01.md": "Aparici llega.\n"},
        constitution="Voz narrativa: tercera persona\n",
    )
    ctx = load_context(project_root)

    assert [n for n, _ in ctx.character_names()] == ["Aparici", "Peña"]
    assert [n for n, _ in ctx.setting_names()] == ["Ayelo"]
    assert ctx.manuscript_files() == (("manuscript/cap-01.md", "Aparici llega.\n"),)
    assert ctx.constitution_text() == "Voz narrativa: tercera persona\n"

    # Cached: a second call returns the identical object (read once per run).
    assert ctx.character_names() is ctx.character_names()
    assert ctx.manuscript_files() is ctx.manuscript_files()


def test_constitution_text_none_when_absent(project_root: Path) -> None:
    write_project(project_root, characters=["A"], manuscript={"c.md": "x"})
    ctx = load_context(project_root)
    assert ctx.constitution_text() is None


def test_context_is_a_dataclass_with_root_and_manifest(project_root: Path) -> None:
    write_project(project_root, characters=["A"])
    ctx = load_context(project_root)
    assert isinstance(ctx, ValidationContext)
    assert ctx.root == project_root
    assert ctx.uri_base.endswith("/")
