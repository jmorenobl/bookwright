"""Unit tests for the bible mapper (data-model § 3, bible-format.md, FR-009/010/013)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from bookwright.golem import Character, NarrativeEvent, Setting, SocialRelationship
from bookwright.io.bible import map_bible
from bookwright.io.errors import SlugCollisionError

URI_BASE = "https://example.org/my-novel/"


def _bible(root: Path) -> Path:
    bible = root / "bible"
    (bible / "characters").mkdir(parents=True)
    (bible / "settings").mkdir(parents=True)
    return bible


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


def test_type_by_location(tmp_path: Path) -> None:
    bible = _bible(tmp_path)
    _write(bible / "characters" / "aparici.md", '---\nname: "Aparici"\n---\n')
    _write(bible / "settings" / "ayelo.md", '---\nname: "Ayelo"\n---\n')
    _write(bible / "timeline.md", '---\nevents:\n  - name: "Fundación"\n---\n')
    _write(bible / "relationships.md", '---\nrelationships:\n  - name: "Sociedad"\n---\n')

    result = map_bible(tmp_path, bible, URI_BASE)
    by_type = {type(e) for e in result.entities}
    assert by_type == {Character, Setting, NarrativeEvent, SocialRelationship}
    assert result.files_processed == 4


def test_character_frontmatter_construction(tmp_path: Path) -> None:
    bible = _bible(tmp_path)
    _write(
        bible / "characters" / "aparici.md",
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
        """,
    )
    result = map_bible(tmp_path, bible, URI_BASE)
    character = next(e for e in result.entities if isinstance(e, Character))
    assert character.born == 1828
    assert character.died == 1900
    assert character.features == ("ingeniero químico",)
    assert character.narrative_roles == ("protagonist",)


def test_unknown_keys_recorded(tmp_path: Path) -> None:
    bible = _bible(tmp_path)
    _write(
        bible / "characters" / "aparici.md",
        '---\nname: "Aparici"\nhairstyle: "beard"\n---\n',
    )
    result = map_bible(tmp_path, bible, URI_BASE)
    assert [(u.path, u.key) for u in result.unknown_keys] == [
        ("bible/characters/aparici.md", "hairstyle")
    ]


def test_unresolved_participant_omits_edge_but_keeps_event(tmp_path: Path) -> None:
    bible = _bible(tmp_path)
    _write(
        bible / "timeline.md",
        """\
        ---
        events:
          - name: "Duelo"
            participants: ["Nadie Conocido"]
        ---
        """,
    )
    result = map_bible(tmp_path, bible, URI_BASE)
    event = next(e for e in result.entities if isinstance(e, NarrativeEvent))
    assert event.participants == ()  # the dlp:participant edge was omitted
    assert [(u.entity, u.name) for u in result.unresolved_participants] == [
        ("Duelo", "Nadie Conocido")
    ]


def test_participant_resolves_to_built_character(tmp_path: Path) -> None:
    bible = _bible(tmp_path)
    _write(bible / "characters" / "aparici.md", '---\nname: "Manuel de Aparici"\n---\n')
    _write(
        bible / "timeline.md",
        """\
        ---
        events:
          - name: "Fundación"
            participants: ["Manuel de Aparici"]
        ---
        """,
    )
    result = map_bible(tmp_path, bible, URI_BASE)
    character = next(e for e in result.entities if isinstance(e, Character))
    event = next(e for e in result.entities if isinstance(e, NarrativeEvent))
    assert event.participants == (character.uri,)
    assert result.unresolved_participants == []


# --- FR-013: fault tolerance (skip malformed) -------------------------------


def test_skip_on_malformed_yaml(tmp_path: Path) -> None:
    bible = _bible(tmp_path)
    _write(bible / "characters" / "broken.md", "---\nname: : :\n  bad\n---\n")
    _write(bible / "characters" / "ok.md", '---\nname: "Aparici"\n---\n')
    result = map_bible(tmp_path, bible, URI_BASE)
    assert len(result.entities) == 1
    assert [s.path for s in result.skipped] == ["bible/characters/broken.md"]
    assert "malformed YAML" in result.skipped[0].reason


def test_skip_on_missing_name(tmp_path: Path) -> None:
    bible = _bible(tmp_path)
    _write(bible / "characters" / "noname.md", "---\nborn: 1828\n---\n")
    result = map_bible(tmp_path, bible, URI_BASE)
    assert result.entities == []
    assert "name" in result.skipped[0].reason


def test_skip_on_non_utf8_file(tmp_path: Path) -> None:
    """A non-UTF-8 source file is skipped, not fatal (FR-013): the build keeps going."""
    bible = _bible(tmp_path)
    # 0xE9 ("é" in Latin-1) is an invalid UTF-8 start byte → UnicodeDecodeError on read.
    (bible / "characters" / "latin1.md").write_bytes(b"---\nname: Jos\xe9\n---\n")
    _write(bible / "characters" / "ok.md", '---\nname: "Aparici"\n---\n')
    result = map_bible(tmp_path, bible, URI_BASE)
    assert len(result.entities) == 1
    skipped = next(s for s in result.skipped if s.path == "bible/characters/latin1.md")
    assert "unreadable" in skipped.reason


def test_unknown_keys_not_recorded_for_skipped_file(tmp_path: Path) -> None:
    """A file skipped (empty slug) never contributes `unknown_keys` warnings."""
    bible = _bible(tmp_path)
    _write(bible / "characters" / "punct.md", '---\nname: "!!!"\nhairstyle: "beard"\n---\n')
    result = map_bible(tmp_path, bible, URI_BASE)
    assert result.entities == []
    assert result.skipped  # rejected for an empty slug
    assert result.unknown_keys == []


def test_non_list_participants_recorded_as_unresolved(tmp_path: Path) -> None:
    """A scalar `participants` value is surfaced as unresolved, not dropped silently."""
    bible = _bible(tmp_path)
    _write(
        bible / "timeline.md",
        """\
        ---
        events:
          - name: "Duelo"
            participants: "Nadie"
        ---
        """,
    )
    result = map_bible(tmp_path, bible, URI_BASE)
    event = next(e for e in result.entities if isinstance(e, NarrativeEvent))
    assert event.participants == ()
    assert [(u.entity, u.name) for u in result.unresolved_participants] == [("Duelo", "Nadie")]


def test_skip_on_non_integer_born(tmp_path: Path) -> None:
    bible = _bible(tmp_path)
    _write(bible / "characters" / "bad.md", '---\nname: "Aparici"\nborn: "long ago"\n---\n')
    result = map_bible(tmp_path, bible, URI_BASE)
    assert result.entities == []
    assert "born" in result.skipped[0].reason


def test_slug_collision_is_fatal(tmp_path: Path) -> None:
    bible = _bible(tmp_path)
    _write(bible / "characters" / "a.md", '---\nname: "Aparici"\n---\n')
    _write(bible / "characters" / "b.md", '---\nname: "Aparici"\n---\n')
    with pytest.raises(SlugCollisionError) as excinfo:
        map_bible(tmp_path, bible, URI_BASE)
    assert excinfo.value.identifier == "aparici"
    assert set(excinfo.value.to_json()["details"]["sources"]) == {
        "bible/characters/a.md",
        "bible/characters/b.md",
    }
