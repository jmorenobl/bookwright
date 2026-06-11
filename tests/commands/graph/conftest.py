"""Shared fixtures for the ``graph`` command tests — the ``tiny-novel`` project.

Scaffolds a minimal but realistic project (a manifest with ``uri_base``, one
character, one setting, a timeline, a relationships file, and a ``manuscript/``
directory) and ``chdir``s into it. Reused across the ``graph`` command tests.
"""

from __future__ import annotations

import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Literal, TypedDict, Unpack

import pytest

from tests.fixtures.research import (
    RESEARCH_INDEX_MD,
    RESEARCH_SOURCES_MD,
    RESEARCH_TOPIC_MD,
    write_research_fixture,
)

URI_BASE = "https://example.org/my-novel/"

_MANIFEST = """\
[bookwright]
cli_version_min = "0.0.1"
schema_version = "1.1"
manifest_version = "1"
uri_base = "{uri_base}"
{indexer_line}

[book]
title = "My Novel"
type = "novel"
language = "es"
authors = ["Jorge MB"]

[integration]
key = "claude"
skills_dir = ".claude/skills/"
"""

CHARACTER_MD = textwrap.dedent(
    """\
    ---
    name: "Manuel de Aparici"
    born: 1828
    died: 1900
    features:
      - "ingeniero químico"
    narrative_roles:
      - protagonist
    ---
    Manuel funda Destilerías Ayelo.
    """
)

SETTING_MD = textwrap.dedent(
    """\
    ---
    name: "Destilerías Ayelo"
    ---
    """
)

TIMELINE_MD = textwrap.dedent(
    """\
    ---
    events:
      - name: "Fundación de Destilerías Ayelo"
        participants: ["Manuel de Aparici"]
    ---
    """
)

RELATIONSHIPS_MD = textwrap.dedent(
    """\
    ---
    relationships:
      - name: "Sociedad Aparici-Ayelo"
        participants: ["Manuel de Aparici"]
    ---
    """
)


def write_manifest(root: Path, *, indexer: str | None = None) -> None:
    """Write a valid ``manifest.toml`` at ``root`` (optionally pinning an engine)."""
    indexer_line = f'indexer = "{indexer}"' if indexer is not None else ""
    (root / "manifest.toml").write_text(
        _MANIFEST.format(uri_base=URI_BASE, indexer_line=indexer_line), encoding="utf-8"
    )


class _ScaffoldKwargs(TypedDict, total=False):
    """The keyword-only surface of :func:`scaffold_project`.

    Mirrors that signature so :func:`project_factory` can splat ``**kwargs``
    into it under mypy ``--strict`` without a ``type: ignore`` escape hatch.
    """

    with_bible: bool
    with_manuscript: bool
    research: Literal["none", "minimal", "rich"]
    indexer: str | None


def scaffold_project(
    root: Path,
    *,
    with_bible: bool = True,
    with_manuscript: bool = True,
    research: Literal["none", "minimal", "rich"] = "none",
    indexer: str | None = None,
) -> Path:
    """Create a tiny-novel project tree under ``root`` and return ``root``.

    ``research`` selects the (single, shared) ``bible/research/`` fixture tier:

    * ``"none"`` (default, so the research-free ``tiny_novel`` and the 10-E13 count
      in ``test_provenance.py`` stay byte-stable) — no research directory.
    * ``"minimal"`` — the iteration-13 constants (one source, one topic file with a
      finding + anchor, one ``_index.md`` open question).
    * ``"rich"`` — the iteration-14 :func:`write_research_fixture` tree exercising
      SC-004/005/006 against the tiny-novel bible.

    Both tiers live in ``tests/fixtures/research.py`` — one source of truth.
    """
    root.mkdir(parents=True, exist_ok=True)
    write_manifest(root, indexer=indexer)
    if with_manuscript:
        (root / "manuscript").mkdir(exist_ok=True)
        (root / "manuscript" / ".gitkeep").write_text("", encoding="utf-8")
    if with_bible:
        characters = root / "bible" / "characters"
        settings = root / "bible" / "settings"
        characters.mkdir(parents=True, exist_ok=True)
        settings.mkdir(parents=True, exist_ok=True)
        (characters / "aparici.md").write_text(CHARACTER_MD, encoding="utf-8")
        (settings / "ayelo.md").write_text(SETTING_MD, encoding="utf-8")
        (root / "bible" / "timeline.md").write_text(TIMELINE_MD, encoding="utf-8")
        (root / "bible" / "relationships.md").write_text(RELATIONSHIPS_MD, encoding="utf-8")
    if research == "minimal":
        research_dir = root / "bible" / "research"
        research_dir.mkdir(parents=True, exist_ok=True)
        (research_dir / "sources.md").write_text(RESEARCH_SOURCES_MD, encoding="utf-8")
        (research_dir / "detective-licencia.md").write_text(RESEARCH_TOPIC_MD, encoding="utf-8")
        (research_dir / "_index.md").write_text(RESEARCH_INDEX_MD, encoding="utf-8")
    elif research == "rich":
        write_research_fixture(root / "bible" / "research")
    return root


@pytest.fixture()
def tiny_novel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fully scaffolded tiny-novel project with cwd set to its root."""
    root = scaffold_project(tmp_path / "my-novel")
    monkeypatch.chdir(root)
    return root


@pytest.fixture()
def project_factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[..., Path]:
    """Return a factory that scaffolds a (variant) project and chdirs into it."""

    def _make(**kwargs: Unpack[_ScaffoldKwargs]) -> Path:
        root = scaffold_project(tmp_path / "my-novel", **kwargs)
        monkeypatch.chdir(root)
        return root

    return _make
