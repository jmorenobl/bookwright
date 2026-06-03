"""Shared fixtures for the ``graph`` command tests — the ``tiny-novel`` project.

Scaffolds a minimal but realistic project (a manifest with ``uri_base``, one
character, one setting, a timeline, a relationships file, and a ``manuscript/``
directory) and ``chdir``s into it. Reused across the ``graph`` command tests.
"""

from __future__ import annotations

import textwrap
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

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

# --- Research fixtures (iteration 012, off by default) -----------------------
# One `oficial`/`alta` Spanish source — book language is "es", so no translation
# (SC-004). See contracts/research-format.md and quickstart §0.
RESEARCH_SOURCES_MD = textwrap.dedent(
    """\
    ---
    sources:
      - name: "Registro TIP"
        reference: "https://www.interior.gob.es/tip"
        author: "Ministerio del Interior (España)"
        original_language: es
        type: oficial
        reliability: alta
        reliability_justification: "Fuente oficial primaria del organismo regulador."
        access_date: 2026-05-30
        original_quote: "El detective privado requiere la TIP expedida por el Ministerio."
    ---
    Notas sobre el registro de detectives.
    """
)

# One finding citing the source and bearing on the character, plus an anchor that
# promotes it, constrains the character, and carries a time-span.
RESEARCH_TOPIC_MD = textwrap.dedent(
    """\
    ---
    findings:
      - id: tip-required
        claim: "Un detective privado en España necesita la licencia TIP."
        asserted_by: agent
        bears_on: "Manuel de Aparici"
        sources: ["Registro TIP"]
    anchors:
      - promotes: tip-required
        constrains: "Manuel de Aparici"
        begin: 1995
        end: 2026
    ---
    Prosa legible sobre el tema de la licencia.
    """
)

# A single global open question (no claim/source — a truly open finding).
RESEARCH_INDEX_MD = textwrap.dedent(
    """\
    ---
    open_questions:
      - id: q-archivo-tip
    ---
    Mapa de temas y preguntas abiertas globales.
    """
)


def write_manifest(root: Path, *, indexer: str | None = None) -> None:
    """Write a valid ``manifest.toml`` at ``root`` (optionally pinning an engine)."""
    indexer_line = f'indexer = "{indexer}"' if indexer is not None else ""
    (root / "manifest.toml").write_text(
        _MANIFEST.format(uri_base=URI_BASE, indexer_line=indexer_line), encoding="utf-8"
    )


def scaffold_project(
    root: Path,
    *,
    with_bible: bool = True,
    with_manuscript: bool = True,
    with_research: bool = False,
    indexer: str | None = None,
) -> Path:
    """Create a tiny-novel project tree under ``root`` and return ``root``.

    ``with_research`` (off by default, so the research-free ``tiny_novel`` and the
    10-E13 count in ``test_provenance.py`` stay byte-stable) adds a
    ``bible/research/`` directory with one source, one topic file (finding +
    anchor) and an ``_index.md`` open question — per ``contracts/research-format.md``.
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
    if with_research:
        research = root / "bible" / "research"
        research.mkdir(parents=True, exist_ok=True)
        (research / "sources.md").write_text(RESEARCH_SOURCES_MD, encoding="utf-8")
        (research / "detective-licencia.md").write_text(RESEARCH_TOPIC_MD, encoding="utf-8")
        (research / "_index.md").write_text(RESEARCH_INDEX_MD, encoding="utf-8")
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

    def _make(**kwargs: object) -> Path:
        root = scaffold_project(tmp_path / "my-novel", **kwargs)  # type: ignore[arg-type]
        monkeypatch.chdir(root)
        return root

    return _make


@pytest.fixture()
def outside_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A directory with no ``manifest.toml`` in it or any ancestor under tmp."""
    here = tmp_path / "nowhere"
    here.mkdir()
    monkeypatch.chdir(here)
    yield here
