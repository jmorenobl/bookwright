"""Unit tests for the outline units mapper (iteration 028, FR-003/005/006/007/008/009/010).

Drives ``map_outline`` after ``map_bible`` on a temp project, exercising the
``outline/units/*.md`` round-trip: ``NarrativeUnit`` (G9) entities, slug-deduped
``NarrativeFunction`` (G10) minting, role resolution against the character-scoped
role nodes, soft misses, malformed-card skips, slug collisions, the absent
directory, and the ``crm:E13`` provenance reification of a unit's cross-refs. See
contracts/outline-units-ingestion.md for the guarantees (C1-C9).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from bookwright.golem import NarrativeFunction, NarrativeUnit
from bookwright.golem.namespaces import REFERS_TO
from bookwright.io._bible_builders import MapResult
from bookwright.io.bible import build_provenance, map_bible
from bookwright.io.errors import SlugCollisionError
from bookwright.io.outline import map_outline

URI_BASE = "https://example.org/my-novel/"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


def _run(root: Path) -> MapResult:
    """Run the character pass then the units pass over ``root``, sharing one result."""
    bible = root / "bible"
    result = map_bible(root, bible, URI_BASE)
    map_outline(root, root / "outline", URI_BASE, result)
    return result


def _units(result: MapResult) -> list[NarrativeUnit]:
    return [e for e in result.entities if isinstance(e, NarrativeUnit)]


def _functions(result: MapResult) -> list[NarrativeFunction]:
    return [e for e in result.entities if isinstance(e, NarrativeFunction)]


def _refers_to_count(unit: NarrativeUnit) -> int:
    return sum(1 for s, p, _ in unit.to_triples() if s == unit.uri and p == REFERS_TO)


# --- (a) shared function deduped across cards; one edge per unit (C1/C2/C3) ---


def test_two_cards_share_one_function(tmp_path: Path) -> None:
    _write(
        tmp_path / "outline/units/opening.md", '---\nname: "Opening"\nfunctions: [departure]\n---\n'
    )
    _write(
        tmp_path / "outline/units/return.md", '---\nname: "Return"\nfunctions: [departure]\n---\n'
    )

    result = _run(tmp_path)

    assert len(_units(result)) == 2
    # `departure` is minted once and reused across both cards.
    assert len(_functions(result)) == 1
    for unit in _units(result):
        assert len(unit.functions) == 1
        assert _refers_to_count(unit) == 1


# --- (b) within-card repeated functions slug-deduped to K edges (C6) ---------


def test_within_card_functions_deduped(tmp_path: Path) -> None:
    _write(
        tmp_path / "outline/units/opening.md",
        """\
        ---
        name: Opening
        functions: [Departure, departure, "  departure  ", interdiction]
        ---
        """,
    )
    result = _run(tmp_path)

    (unit,) = _units(result)
    # Departure/departure/"  departure  " all slug to `departure`: 2 distinct functions.
    assert len(unit.functions) == 2
    assert len(_functions(result)) == 2
    assert _refers_to_count(unit) == 2


# --- (c) name but no functions → unit only, no edge, no error ----------------


def test_name_without_functions(tmp_path: Path) -> None:
    _write(tmp_path / "outline/units/opening.md", '---\nname: "Opening"\n---\n')
    result = _run(tmp_path)

    (unit,) = _units(result)
    assert unit.functions == ()
    assert _functions(result) == []
    assert _refers_to_count(unit) == 0
    assert result.skipped == []


# --- (d) prose body is not ingested (FR-003 / C8) ----------------------------


def test_prose_body_not_ingested(tmp_path: Path) -> None:
    _write(
        tmp_path / "outline/units/opening.md",
        """\
        ---
        name: Opening
        ---
        The hero is warned and then leaves home. This prose must contribute no triple.
        """,
    )
    result = _run(tmp_path)

    (unit,) = _units(result)
    # Only the rdf:type triple — no edge from prose, no extra entity.
    assert list(unit.to_triples()) == [next(iter(unit.to_triples()))]
    assert len(list(unit.to_triples())) == 1


# --- (e) no front-matter / malformed YAML → skipped, build continues (R1) ----


def test_no_frontmatter_skipped(tmp_path: Path) -> None:
    _write(tmp_path / "outline/units/opening.md", "Just prose, no front-matter.\n")
    _write(tmp_path / "outline/units/return.md", '---\nname: "Return"\n---\n')
    result = _run(tmp_path)

    assert [s.path for s in result.skipped] == ["outline/units/opening.md"]
    assert result.skipped[0].reason
    assert [u.name for u in _units(result)] == ["Return"]


def test_malformed_yaml_skipped(tmp_path: Path) -> None:
    _write(tmp_path / "outline/units/bad.md", "---\nname: [unclosed\n---\n")
    result = _run(tmp_path)

    assert [s.path for s in result.skipped] == ["outline/units/bad.md"]
    assert "YAML" in result.skipped[0].reason
    assert _units(result) == []


# --- (f) missing / empty / non-string name → skipped (FR-006) ----------------


@pytest.mark.parametrize(
    "frontmatter",
    [
        "---\nfunctions: [departure]\n---\n",  # missing name
        '---\nname: ""\n---\n',  # empty name
        "---\nname: 42\n---\n",  # non-string name
    ],
)
def test_bad_name_skipped(tmp_path: Path, frontmatter: str) -> None:
    _write(tmp_path / "outline/units/card.md", frontmatter)
    result = _run(tmp_path)

    assert [s.path for s in result.skipped] == ["outline/units/card.md"]
    assert _units(result) == []
    # R2: a skipped card leaks no partial function.
    assert _functions(result) == []


# --- (g) non-list functions → skipped, no partial function leaked (FR-007/R2) -


def test_non_list_functions_skipped_no_leak(tmp_path: Path) -> None:
    _write(
        tmp_path / "outline/units/card.md", '---\nname: "Opening"\nfunctions: "not-a-list"\n---\n'
    )
    result = _run(tmp_path)

    assert [s.path for s in result.skipped] == ["outline/units/card.md"]
    assert _units(result) == []
    assert _functions(result) == []


# --- (h) colliding unit name slugs → SlugCollisionError (FR-008) -------------


def test_colliding_unit_names_raise(tmp_path: Path) -> None:
    _write(tmp_path / "outline/units/a.md", '---\nname: "Opening"\n---\n')
    _write(tmp_path / "outline/units/b.md", '---\nname: "opening"\n---\n')

    with pytest.raises(SlugCollisionError):
        _run(tmp_path)


# --- (i) absent outline/units/ directory → no units, no error (FR-009/SC-006) -


def test_absent_units_dir_is_noop(tmp_path: Path) -> None:
    (tmp_path / "bible").mkdir()
    result = map_bible(tmp_path, tmp_path / "bible", URI_BASE)
    before = list(result.mapped)
    map_outline(tmp_path, tmp_path / "outline", URI_BASE, result)

    assert result.mapped == before
    assert _units(result) == []
    assert result.skipped == []


# --- role resolution against character-scoped role nodes (FR-005, SC-004) ----


def _character(root: Path, slug: str, name: str, roles: list[str]) -> None:
    role_list = "\n".join(f"  - {r}" for r in roles)
    _write(
        root / "bible/characters" / f"{slug}.md",
        f"---\nname: {name!r}\nnarrative_roles:\n{role_list}\n---\n",
    )


def _role_uris(unit: NarrativeUnit) -> tuple[object, ...]:
    return unit.roles


def test_role_resolves_to_character_role_node(tmp_path: Path) -> None:
    _character(tmp_path, "ada", "Ada", ["hero"])
    _write(tmp_path / "outline/units/opening.md", '---\nname: "Opening"\nroles: [hero]\n---\n')
    result = _run(tmp_path)

    (unit,) = _units(result)
    char = next(e for e in result.entities if str(e.uri).endswith("character/ada"))
    expected = next(iter(char._role_nodes)).uri  # type: ignore[attr-defined]
    assert _role_uris(unit) == (expected,)
    assert _refers_to_count(unit) == 1
    assert result.unresolved_references == []


def test_unknown_role_is_soft_miss(tmp_path: Path) -> None:
    _character(tmp_path, "ada", "Ada", ["hero"])
    _write(tmp_path / "outline/units/opening.md", '---\nname: "Opening"\nroles: [unknown]\n---\n')
    result = _run(tmp_path)

    (unit,) = _units(result)
    assert unit.roles == ()
    assert _refers_to_count(unit) == 0
    assert [(u.entity, u.name) for u in result.unresolved_references] == [("Opening", "unknown")]


def test_no_roles_key_no_warning(tmp_path: Path) -> None:
    _character(tmp_path, "ada", "Ada", ["hero"])
    _write(tmp_path / "outline/units/opening.md", '---\nname: "Opening"\n---\n')
    result = _run(tmp_path)

    (unit,) = _units(result)
    assert unit.roles == ()
    assert result.unresolved_references == []


def test_role_played_by_many_characters(tmp_path: Path) -> None:
    _character(tmp_path, "ada", "Ada", ["hero"])
    _character(tmp_path, "bram", "Bram", ["hero"])
    _write(tmp_path / "outline/units/opening.md", '---\nname: "Opening"\nroles: [hero]\n---\n')
    result = _run(tmp_path)

    (unit,) = _units(result)
    # One unit→role edge per matching character role node (C4).
    assert len(unit.roles) == 2
    assert _refers_to_count(unit) == 2
    assert len(set(unit.roles)) == 2


def test_repeated_roles_within_card_deduped(tmp_path: Path) -> None:
    _character(tmp_path, "ada", "Ada", ["hero"])
    _write(
        tmp_path / "outline/units/opening.md",
        '---\nname: "Opening"\nroles: [hero, Hero, "  hero  "]\n---\n',
    )
    result = _run(tmp_path)

    (unit,) = _units(result)
    # All slug to `hero`: deduped before resolution, so still one edge.
    assert len(unit.roles) == 1
    assert _refers_to_count(unit) == 1


def test_non_list_roles_skips_card(tmp_path: Path) -> None:
    _character(tmp_path, "ada", "Ada", ["hero"])
    _write(tmp_path / "outline/units/card.md", '---\nname: "Opening"\nroles: "hero"\n---\n')
    result = _run(tmp_path)

    assert [s.path for s in result.skipped] == ["outline/units/card.md"]
    assert _units(result) == []


# --- provenance: unit→function / unit→role reified as E13 with locators (FR-010/C7) ---


def test_unit_cross_refs_reified_as_e13_with_locators(tmp_path: Path) -> None:
    """A unit's identity, function and role assertions each reify as a
    ``crm:E13_Attribute_Assignment`` (via ``build_provenance``): identity carries
    file-level provenance, while ``functions``/``roles`` resolve to the card's
    ``relpath:line`` for their originating key — the same per-assertion provenance
    characters get, now proven for ``NarrativeUnit`` cross-refs (FR-010 / C7)."""
    _character(tmp_path, "ada", "Ada", ["hero"])
    _write(
        tmp_path / "outline/units/opening.md",
        """\
        ---
        name: Opening
        functions: [departure]
        roles: [hero]
        ---
        """,
    )
    result = _run(tmp_path)

    (unit,) = _units(result)
    (function,) = _functions(result)
    (role_uri,) = unit.roles
    (mapped,) = [m for m in result.mapped if m.entity is unit]

    provs = list(build_provenance(mapped, URI_BASE))
    triples = {(p.target, p.attribute, p.source) for p in provs}

    relpath = "outline/units/opening.md"
    # Identity is file-level (no line); the `functions:`/`roles:` keys are on
    # lines 3/4 of the card (line 1 is the fence).
    assert (unit.uri, unit.uri, relpath) in triples
    assert (unit.uri, function.uri, f"{relpath}:3") in triples
    assert (unit.uri, role_uri, f"{relpath}:4") in triples
    # Exactly those three reifications — no stray assignment from the prose body.
    assert len(provs) == 3
