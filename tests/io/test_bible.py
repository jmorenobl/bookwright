"""Unit tests for the bible mapper (data-model § 3, bible-format.md, FR-009/010/013)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from rdflib.term import URIRef

from bookwright.golem import (
    Character,
    NarrativeEvent,
    NarrativeLocation,
    Object,
    Setting,
    SocialRelationship,
)
from bookwright.golem.namespaces import timeline_uri
from bookwright.io.bible import build_provenance, map_bible
from bookwright.io.errors import SlugCollisionError
from bookwright.io.research import map_research

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


def test_timeline_interval_and_relations_map(tmp_path: Path) -> None:
    """begin/end years and the five relation keys map onto the NarrativeEvent (D11)."""
    bible = _bible(tmp_path)
    _write(
        bible / "timeline.md",
        """\
        ---
        events:
          - name: "Fundación"
            begin: 1885
            end: 1912
          - name: "Quiebra"
            date: 1884
            follows: ["Fundación"]
        ---
        """,
    )
    result = map_bible(tmp_path, bible, URI_BASE)
    events = {e.name: e for e in result.entities if isinstance(e, NarrativeEvent)}
    funda, quiebra = events["Fundación"], events["Quiebra"]
    assert (funda.begin, funda.end) == (1885, 1912)
    assert (quiebra.begin, quiebra.end) == (1884, 1884)  # date shorthand → begin == end
    assert quiebra.follows == (funda.uri,)  # resolved against the event index


def test_timeline_date_with_begin_end_warns_and_ignores_date(tmp_path: Path) -> None:
    """Supplying `date` alongside `begin`/`end` is a soft warning; `date` is ignored."""
    bible = _bible(tmp_path)
    _write(
        bible / "timeline.md",
        """\
        ---
        events:
          - name: "Fundación"
            begin: 1885
            end: 1912
            date: 1700
        ---
        """,
    )
    result = map_bible(tmp_path, bible, URI_BASE)
    event = next(e for e in result.entities if isinstance(e, NarrativeEvent))
    assert (event.begin, event.end) == (1885, 1912)  # date ignored
    assert any(u.key == "date" for u in result.unknown_keys)


def test_timeline_unresolved_relation_is_soft_warning(tmp_path: Path) -> None:
    """A relation naming no sibling event is surfaced as unresolved, never fatal."""
    bible = _bible(tmp_path)
    _write(
        bible / "timeline.md",
        """\
        ---
        events:
          - name: "Quiebra"
            follows: ["No Existe"]
        ---
        """,
    )
    result = map_bible(tmp_path, bible, URI_BASE)
    event = next(e for e in result.entities if isinstance(e, NarrativeEvent))
    assert event.follows == ()
    assert [(u.entity, u.name) for u in result.unresolved_participants] == [
        ("Quiebra", "No Existe")
    ]


def test_timeline_non_integer_begin_skips_item(tmp_path: Path) -> None:
    """A non-integer `begin` makes the timeline item unusable (skipped, not fatal)."""
    bible = _bible(tmp_path)
    _write(
        bible / "timeline.md",
        '---\nevents:\n  - name: "Mal"\n    begin: "ayer"\n---\n',
    )
    result = map_bible(tmp_path, bible, URI_BASE)
    assert [e for e in result.entities if isinstance(e, NarrativeEvent)] == []
    assert any("begin" in s.reason for s in result.skipped)


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


# --- locations indexed as G13 (iteration 025) ------------------------------


def _location(result: object, slug: str | None = None) -> NarrativeLocation:
    locs = [e for e in result.entities if isinstance(e, NarrativeLocation)]  # type: ignore[attr-defined]
    return next(e for e in locs if slug is None or e.slug == slug)


def test_location_name_only_builds_g13_node(tmp_path: Path) -> None:
    """`name`-only → one G13 node, slug from name, no setting edge (FR-001, SC-001)."""
    bible = _bible(tmp_path)
    _write(bible / "locations" / "harbor.md", '---\nname: "The Harbor"\n---\n')
    result = map_bible(tmp_path, bible, URI_BASE)
    locs = [e for e in result.entities if isinstance(e, NarrativeLocation)]
    assert len(locs) == 1
    assert locs[0].slug == "the-harbor"
    assert locs[0].setting is None
    # File-level identity provenance: the only derived assertion is identity (source_field None).
    mapped = next(m for m in result.mapped if isinstance(m.entity, NarrativeLocation))
    assert [a.source_field for a in mapped.entity.derived_assertions()] == [None]


def test_location_resolvable_setting_emits_edge(tmp_path: Path) -> None:
    """`name` + resolvable `setting` → node + dlp:generic-location edge + prov (FR-003, SC-002)."""
    bible = _bible(tmp_path)
    _write(bible / "settings" / "old-crossing.md", '---\nname: "The Old Crossing"\n---\n')
    _write(
        bible / "locations" / "harbor.md",
        '---\nname: "The Harbor"\nsetting: "The Old Crossing"\n---\n',
    )
    result = map_bible(tmp_path, bible, URI_BASE)
    setting = next(e for e in result.entities if isinstance(e, Setting))
    loc = _location(result, "the-harbor")
    assert loc.setting == setting.uri  # the dlp:generic-location target
    assert result.unresolved_participants == []
    # The setting cross-ref carries `setting:`-line provenance (relpath:line).
    mapped = next(m for m in result.mapped if isinstance(m.entity, NarrativeLocation))
    assert [a.source_field for a in loc.derived_assertions()] == [None, "setting"]
    sources = {a.source for a in build_provenance(mapped, URI_BASE)}
    assert any(s.startswith("bible/locations/harbor.md:") for s in sources)


def test_location_absent_or_blank_setting_no_edge_no_warning(tmp_path: Path) -> None:
    """`name` + absent/blank `setting` → node, no edge, no soft warning (FR-002)."""
    bible = _bible(tmp_path)
    _write(bible / "locations" / "absent.md", '---\nname: "No Setting Place"\n---\n')
    _write(bible / "locations" / "blank.md", '---\nname: "Blank Place"\nsetting: "   "\n---\n')
    result = map_bible(tmp_path, bible, URI_BASE)
    assert _location(result, "no-setting-place").setting is None
    assert _location(result, "blank-place").setting is None
    assert result.unresolved_participants == []
    assert result.unknown_keys == []


def test_location_unresolved_setting_is_soft_miss(tmp_path: Path) -> None:
    """`setting` naming no built setting → node built, no edge, one soft miss (FR-004, SC-002)."""
    bible = _bible(tmp_path)
    _write(
        bible / "locations" / "harbor.md",
        '---\nname: "The Harbor"\nsetting: "Nowhere At All"\n---\n',
    )
    result = map_bible(tmp_path, bible, URI_BASE)
    loc = _location(result, "the-harbor")
    assert loc.setting is None  # the build was not aborted; only the edge is omitted
    assert [(u.path, u.entity, u.name) for u in result.unresolved_participants] == [
        ("bible/locations/harbor.md", "The Harbor", "Nowhere At All")
    ]


def test_location_unslugifiable_setting_is_soft_miss(tmp_path: Path) -> None:
    """A non-blank `setting` that slugs to nothing → node built, no edge, one soft miss (FR-004)."""
    bible = _bible(tmp_path)
    _write(
        bible / "locations" / "odd.md",
        '---\nname: "The Quay"\nsetting: "!!!"\n---\n',
    )
    result = map_bible(tmp_path, bible, URI_BASE)
    loc = _location(result, "the-quay")
    assert loc.setting is None  # EmptySlugError → soft miss, not a crash or an edge
    assert [(u.path, u.entity, u.name) for u in result.unresolved_participants] == [
        ("bible/locations/odd.md", "The Quay", "!!!")
    ]


def test_location_slug_collision_is_fatal(tmp_path: Path) -> None:
    """Two locations with the same slug raise SlugCollisionError (FR-006)."""
    bible = _bible(tmp_path)
    _write(bible / "locations" / "a.md", '---\nname: "The Harbor"\n---\n')
    _write(bible / "locations" / "b.md", '---\nname: "The Harbor"\n---\n')
    with pytest.raises(SlugCollisionError) as excinfo:
        map_bible(tmp_path, bible, URI_BASE)
    assert excinfo.value.identifier == "the-harbor"
    assert set(excinfo.value.to_json()["details"]["sources"]) == {
        "bible/locations/a.md",
        "bible/locations/b.md",
    }


def test_location_enters_entity_index_for_research_resolution(tmp_path: Path) -> None:
    """Each built location enters `entity_index` by slug so research resolves (FR-005, SC-003)."""
    bible = _bible(tmp_path)
    _write(bible / "locations" / "harbor.md", '---\nname: "The Harbor"\n---\n')
    result = map_bible(tmp_path, bible, URI_BASE)
    loc = _location(result, "the-harbor")
    assert result.entity_index.get("the-harbor") == loc.uri


# --- backward compatibility (skip unusable, absent dir) --------------------


def test_location_frontmatterless_or_invalid_is_skipped(tmp_path: Path) -> None:
    """Unusable location front-matter is skipped (no node, no crash) (FR-007/009, SC-005)."""
    bible = _bible(tmp_path)
    # A v0-style prose location with no ingestible front-matter at all.
    _write(bible / "locations" / "prose.md", "# The Harbor\n\nPure sensory prose.\n")
    _write(bible / "locations" / "noname.md", '---\nsetting: "Somewhere"\n---\n')
    _write(bible / "locations" / "empty.md", '---\nname: "   "\n---\n')
    _write(bible / "locations" / "intname.md", "---\nname: 42\n---\n")
    _write(bible / "locations" / "badsetting.md", '---\nname: "The Quay"\nsetting: 42\n---\n')
    result = map_bible(tmp_path, bible, URI_BASE)
    assert [e for e in result.entities if isinstance(e, NarrativeLocation)] == []
    assert {s.path for s in result.skipped} == {
        "bible/locations/prose.md",
        "bible/locations/noname.md",
        "bible/locations/empty.md",
        "bible/locations/intname.md",
        "bible/locations/badsetting.md",
    }
    # A skipped file contributes no soft warnings (report stays consistent).
    assert result.unknown_keys == []
    assert result.unresolved_participants == []


def test_no_locations_directory_builds_identically(tmp_path: Path) -> None:
    """No `bible/locations/` directory → build is clean, no location nodes (FR-008, SC-005)."""
    bible = _bible(tmp_path)  # creates characters/ and settings/ only — no locations/
    _write(bible / "characters" / "aparici.md", '---\nname: "Aparici"\n---\n')
    _write(bible / "settings" / "ayelo.md", '---\nname: "Ayelo"\n---\n')
    result = map_bible(tmp_path, bible, URI_BASE)
    assert [e for e in result.entities if isinstance(e, NarrativeLocation)] == []
    assert result.skipped == []
    assert {type(e) for e in result.entities} == {Character, Setting}


# --- objects indexed as G16 (iteration 026) --------------------------------


def _objects(result: object) -> list[Object]:
    return [e for e in result.entities if isinstance(e, Object)]  # type: ignore[attr-defined]


def test_object_name_only_builds_g16_node(tmp_path: Path) -> None:
    """`name`-only → one G16 node, slug from name, file-level prov (FR-001/002, C1)."""
    bible = _bible(tmp_path)
    _write(bible / "objects" / "excalibur.md", '---\nname: "Excalibur"\n---\n')
    result = map_bible(tmp_path, bible, URI_BASE)
    objs = _objects(result)
    assert len(objs) == 1
    assert objs[0].slug == "excalibur"
    assert objs[0].uri == URIRef(f"{URI_BASE}object/excalibur")
    # File-level identity provenance: the only derived assertion is identity
    # (source_field None → file-level `bible/objects/excalibur.md` source).
    mapped = next(m for m in result.mapped if isinstance(m.entity, Object))
    assert [a.source_field for a in mapped.entity.derived_assertions()] == [None]
    sources = {a.source for a in build_provenance(mapped, URI_BASE)}
    assert sources == {"bible/objects/excalibur.md"}


def test_object_enters_entity_index_for_research_resolution(tmp_path: Path) -> None:
    """Object enters `entity_index`; research `bears_on:` to it has no soft-miss (FR-003, C2)."""
    bible = _bible(tmp_path)
    _write(bible / "objects" / "excalibur.md", '---\nname: "Excalibur"\n---\n')
    result = map_bible(tmp_path, bible, URI_BASE)
    obj = _objects(result)[0]
    assert result.entity_index.get("excalibur") == obj.uri

    # A research finding whose `bears_on:` names the object resolves with no soft-miss.
    research = tmp_path / "bible" / "research"
    _write(
        research / "sources.md",
        textwrap.dedent(
            """\
            ---
            sources:
              - name: "Registro TIP"
                reference: "https://www.interior.gob.es/tip"
                author: "Ministerio del Interior"
                original_language: es
                type: oficial
                reliability: alta
                reliability_justification: "Fuente oficial primaria."
                access_date: 2026-05-30
                original_quote: "El detective privado requiere la TIP."
            ---
            """
        ),
    )
    _write(
        research / "espada.md",
        textwrap.dedent(
            """\
            ---
            findings:
              - id: espada-magica
                claim: "La espada es mágica."
                asserted_by: agent
                bears_on: "Excalibur"
                sources: ["Registro TIP"]
            ---
            """
        ),
    )
    rresult = map_research(
        tmp_path, research, URI_BASE, "es", dict(result.entity_index), timeline_uri(URI_BASE)
    )
    assert rresult.findings[0].bears_on == obj.uri
    assert [w for w in rresult.warnings if w.field == "bears_on"] == []


def test_object_frontmatterless_or_invalid_is_skipped(tmp_path: Path) -> None:
    """Unusable object front-matter is skipped (no node, no crash) (FR-005, SC-004, C3)."""
    bible = _bible(tmp_path)
    _write(bible / "objects" / "prose.md", "# Excalibur\n\nPure prose, no front-matter.\n")
    _write(bible / "objects" / "empty.md", '---\nname: "   "\n---\n')
    _write(bible / "objects" / "intname.md", "---\nname: 42\n---\n")
    result = map_bible(tmp_path, bible, URI_BASE)
    assert _objects(result) == []
    assert {s.path for s in result.skipped} == {
        "bible/objects/prose.md",
        "bible/objects/empty.md",
        "bible/objects/intname.md",
    }
    assert result.unknown_keys == []


def test_no_objects_directory_builds_identically(tmp_path: Path) -> None:
    """No `bible/objects/` directory → build is clean, no object nodes (FR-006, SC-004, C4)."""
    bible = _bible(tmp_path)  # characters/ and settings/ only — no objects/
    _write(bible / "characters" / "aparici.md", '---\nname: "Aparici"\n---\n')
    _write(bible / "settings" / "ayelo.md", '---\nname: "Ayelo"\n---\n')
    result = map_bible(tmp_path, bible, URI_BASE)
    assert _objects(result) == []
    assert result.skipped == []
    assert {type(e) for e in result.entities} == {Character, Setting}


def test_object_slug_collision_is_fatal(tmp_path: Path) -> None:
    """Two objects slugging to the same identity raise SlugCollisionError (FR-004, C5)."""
    bible = _bible(tmp_path)
    _write(bible / "objects" / "a.md", '---\nname: "Excalibur"\n---\n')
    _write(bible / "objects" / "b.md", '---\nname: "Excalibur"\n---\n')
    with pytest.raises(SlugCollisionError) as excinfo:
        map_bible(tmp_path, bible, URI_BASE)
    assert excinfo.value.identifier == "excalibur"
    assert set(excinfo.value.to_json()["details"]["sources"]) == {
        "bible/objects/a.md",
        "bible/objects/b.md",
    }
