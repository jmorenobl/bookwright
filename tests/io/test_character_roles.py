"""Greimas role typing on character-scoped role nodes (iteration 030, C9/C10/C11).

Drives ``map_bible`` with the Greimas vocabulary active: a character card's
``narrative_roles:`` name that matches an actant types the corresponding G11 role
node (``crm:P2_has_type`` + the term's ``crm:E55_Type``), reified as an E13 with a
real ``relpath:line`` locator; a non-matching role stays identity-only; with
Greimas inactive nothing is typed. See contracts/vocabulary-typing.md.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from bookwright.golem import Character
from bookwright.golem.namespaces import HAS_TYPE
from bookwright.io._bible_builders import MapResult
from bookwright.io.bible import build_provenance, map_bible
from bookwright.io.vocabularies import load_vocabulary

URI_BASE = "https://example.org/my-novel/"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


def _character(result: MapResult, slug: str) -> Character:
    return next(
        e
        for e in result.entities
        if isinstance(e, Character) and str(e.uri).endswith(f"character/{slug}")
    )


def _run_greimas(root: Path) -> MapResult:
    return map_bible(root, root / "bible", URI_BASE, greimas=load_vocabulary("greimas"))


def _role_type(char: Character, role_slug: str) -> object | None:
    role = next(r for r in char.role_nodes if str(r.uri).endswith(f"/role/{role_slug}"))
    for s, p, o in role.to_triples():
        if s == role.uri and p == HAS_TYPE:
            return o
    return None


def test_greimas_match_types_role(tmp_path: Path) -> None:
    """C9: a matching ``narrative_roles:`` name types the role node; a non-matching
    role is left untyped, no error."""
    _write(
        tmp_path / "bible/characters/ada.md",
        """\
        ---
        name: Ada
        narrative_roles: [sujeto, sidekick]
        ---
        """,
    )
    result = _run_greimas(tmp_path)
    char = _character(result, "ada")
    assert _role_type(char, "sujeto") == load_vocabulary("greimas").resolve("subject")
    assert _role_type(char, "sidekick") is None
    assert result.skipped == []


def test_greimas_role_typing_reified_with_line_locator(tmp_path: Path) -> None:
    """C10 (role side): the role typing link reifies as an E13 — target=role node,
    attribute=term, source = the card's ``narrative_roles:`` line."""
    _write(
        tmp_path / "bible/characters/ada.md",
        """\
        ---
        name: Ada
        narrative_roles: [sujeto]
        ---
        """,
    )
    result = _run_greimas(tmp_path)
    char = _character(result, "ada")
    role = next(r for r in char.role_nodes if str(r.uri).endswith("/role/sujeto"))
    term = load_vocabulary("greimas").resolve("subject")
    (mapped,) = [m for m in result.mapped if m.entity is char]
    triples = {(p.target, p.attribute, p.source) for p in build_provenance(mapped, URI_BASE)}
    # narrative_roles: is on line 3 of the card (line 1 is the opening fence).
    assert (role.uri, term, "bible/characters/ada.md:3") in triples


def test_greimas_inactive_does_not_type_role(tmp_path: Path) -> None:
    """C11: with Greimas inactive, a would-match role is not typed."""
    _write(
        tmp_path / "bible/characters/ada.md",
        """\
        ---
        name: Ada
        narrative_roles: [sujeto]
        ---
        """,
    )
    result = map_bible(tmp_path, tmp_path / "bible", URI_BASE)  # no vocab
    char = _character(result, "ada")
    assert _role_type(char, "sujeto") is None


def test_greimas_typing_independent_of_unit_reference(tmp_path: Path) -> None:
    """FR-005: role typing attaches at materialization — no unit card needed."""
    _write(
        tmp_path / "bible/characters/ada.md",
        "---\nname: Ada\nnarrative_roles: [destinador]\n---\n",
    )
    result = _run_greimas(tmp_path)  # bible only, no outline pass
    char = _character(result, "ada")
    assert _role_type(char, "destinador") == load_vocabulary("greimas").resolve("sender")
