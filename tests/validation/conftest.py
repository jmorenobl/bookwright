"""Shared fixtures + scaffolding for the validation suite (T019).

A project-scaffold builder plus per-validator violation/clean helpers. Importable
by the test modules (``from tests.validation.conftest import ...``) so each story's
tests stay self-contained while sharing one realistic project shape.
"""

from __future__ import annotations

import textwrap
from collections.abc import Iterable, Mapping
from pathlib import Path

import pytest

from bookwright.core.manifest import Manifest
from bookwright.indexers import RdflibIndexer
from bookwright.io.bible import build_provenance, map_bible
from bookwright.validation.base import ValidationContext

URI_BASE = "https://example.org/novel/"

_MANIFEST = """\
[bookwright]
cli_version_min = "0.0.1"
schema_version = "1.1"
manifest_version = "1"
uri_base = "{uri_base}"

[book]
title = "Novel"
type = "novel"
language = "es"
authors = ["Autora"]

[integration]
key = "claude"
skills_dir = ".claude/skills/"
"""


def _validators_block(
    enabled: Iterable[str] | None,
    disabled: Iterable[str] | None,
    custom: Iterable[str] | None,
) -> str:
    if enabled is None and disabled is None and custom is None:
        return ""

    def _arr(values: Iterable[str] | None) -> str:
        items = ", ".join(f'"{v}"' for v in (values or ()))
        return f"[{items}]"

    return (
        "\n[validators]\n"
        f"enabled = {_arr(enabled)}\n"
        f"disabled = {_arr(disabled)}\n"
        f"custom = {_arr(custom)}\n"
    )


def write_project(  # noqa: PLR0913 — a flexible scaffold helper; keyword-only knobs
    root: Path,
    *,
    characters: Iterable[str] = (),
    settings: Iterable[str] = (),
    timeline: str | None = None,
    relationships: str | None = None,
    manuscript: Mapping[str, str] | None = None,
    constitution: str | None = None,
    enabled: Iterable[str] | None = None,
    disabled: Iterable[str] | None = None,
    custom: Iterable[str] | None = None,
) -> Path:
    """Create a project tree under ``root`` and return it.

    ``characters`` / ``settings`` are names (one bible file each); ``timeline`` /
    ``relationships`` / ``constitution`` are raw file bodies; ``manuscript`` maps a
    relpath (under ``manuscript/``) to its text. The ``manuscript/`` directory always
    exists so the layout is valid.
    """
    root.mkdir(parents=True, exist_ok=True)
    block = _validators_block(enabled, disabled, custom)
    (root / "manifest.toml").write_text(
        _MANIFEST.format(uri_base=URI_BASE) + block, encoding="utf-8"
    )

    manuscript_dir = root / "manuscript"
    manuscript_dir.mkdir(exist_ok=True)
    for relpath, text in (manuscript or {}).items():
        target = manuscript_dir / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(text), encoding="utf-8")

    bible = root / "bible"
    (bible / "characters").mkdir(parents=True, exist_ok=True)
    (bible / "settings").mkdir(parents=True, exist_ok=True)
    for name in characters:
        slug = name.lower().replace(" ", "-")
        (bible / "characters" / f"{slug}.md").write_text(
            f'---\nname: "{name}"\n---\n', encoding="utf-8"
        )
    for name in settings:
        slug = name.lower().replace(" ", "-")
        (bible / "settings" / f"{slug}.md").write_text(
            f'---\nname: "{name}"\n---\n', encoding="utf-8"
        )
    if timeline is not None:
        (bible / "timeline.md").write_text(textwrap.dedent(timeline), encoding="utf-8")
    if relationships is not None:
        (bible / "relationships.md").write_text(textwrap.dedent(relationships), encoding="utf-8")
    if constitution is not None:
        (bible / "constitution.md").write_text(textwrap.dedent(constitution), encoding="utf-8")

    return root


def load_context(root: Path) -> ValidationContext:
    """A :class:`ValidationContext` over a scaffolded project."""
    return ValidationContext(root=root, manifest=Manifest.load(root / "manifest.toml"))


def build_indexer(root: Path) -> RdflibIndexer:
    """Map the bible to GOLEM entities + provenance into a fresh in-memory engine."""
    manifest = Manifest.load(root / "manifest.toml")
    uri_base = manifest.bookwright.uri_base
    result = map_bible(root, root / manifest.paths.bible, uri_base)
    engine = RdflibIndexer()
    for mapped in result.mapped:
        for triple in mapped.entity.to_triples():
            engine.add_triple(*triple)
        for assignment in build_provenance(mapped, uri_base):
            for triple in assignment.to_triples():
                engine.add_triple(*triple)
    return engine


def build_and_save_graph(root: Path) -> Path:
    """Build the graph and serialize it to ``bible/graph.ttl`` (for command tests)."""
    manifest = Manifest.load(root / "manifest.toml")
    graph_path = root / manifest.paths.graph
    build_indexer(root).save(graph_path)
    return graph_path


@pytest.fixture()
def project_root(tmp_path: Path) -> Path:
    """An empty directory to scaffold a project into."""
    return tmp_path / "novel"
