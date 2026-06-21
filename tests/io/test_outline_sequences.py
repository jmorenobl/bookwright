"""Unit tests for narrative-sequence assembly (iteration 029, FR-002..FR-011).

Drives ``map_outline`` over ``outline/units/*.md`` cards carrying the optional
``sequence``/``order`` keys and asserts the assembled :class:`NarrativeSequence`
(G7) set: one entity per distinct sequence slug, its ``dlp:proper-part`` members
ordered ascending by ``order`` (missing/duplicate ``order`` resolved
deterministically by unit slug), single-member sequences, the soft handling of a
lone ``order``, and the byte-for-byte-identical graph when no card declares a
``sequence``. Order is asserted on the **builder's ``units`` tuple**, not RDF
triple order (contract § 2). See contracts/sequence-ingestion.md (C1-C5).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from rdflib.namespace import XSD
from rdflib.term import Literal, URIRef

from bookwright.golem import NarrativeSequence, NarrativeUnit
from bookwright.golem.namespaces import BW_SEQUENCE_ORDINAL, PROPER_PART
from bookwright.io._bible_builders import MapResult
from bookwright.io.bible import map_bible
from bookwright.io.outline import map_outline

URI_BASE = "https://example.org/my-novel/"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


def _run(root: Path) -> MapResult:
    """Run the character pass then the units pass over ``root``, sharing one result."""
    result = map_bible(root, root / "bible", URI_BASE)
    map_outline(root, root / "outline", URI_BASE, result)
    return result


def _sequences(result: MapResult) -> list[NarrativeSequence]:
    return [e for e in result.entities if isinstance(e, NarrativeSequence)]


def _member_names(sequence: NarrativeSequence) -> list[str]:
    """The assembled member units' names, in tuple order (the ordering contract)."""
    return [u.name for u in sequence.units if isinstance(u, NarrativeUnit)]


def _proper_part_count(sequence: NarrativeSequence) -> int:
    return sum(1 for s, p, _ in sequence.to_triples() if s == sequence.uri and p == PROPER_PART)


def _ordinals(sequence: NarrativeSequence) -> list[tuple[str, URIRef | Literal]]:
    """Each ``bw:sequenceOrdinal`` triple as ``(subject-uri, object-literal)``, in
    emitted order — the subject is the **member unit** URI, never the sequence."""
    return [(str(s), o) for s, p, o in sequence.to_triples() if p == BW_SEQUENCE_ORDINAL]


def _card(root: Path, stem: str, name: str, *, sequence: str | None, order: int | None) -> None:
    lines = [f"name: {name!r}"]
    if sequence is not None:
        lines.append(f"sequence: {sequence!r}")
    if order is not None:
        lines.append(f"order: {order}")
    body = "---\n" + "\n".join(lines) + "\n---\n"
    _write(root / "outline/units" / f"{stem}.md", body)


# --- Scenario A: three ordered beats → one ordered sequence (SC-001/002/003) --


def test_three_ordered_beats_one_sequence(tmp_path: Path) -> None:
    _card(tmp_path, "a", "Beat A", sequence="Act I", order=1)
    _card(tmp_path, "b", "Beat B", sequence="Act I", order=2)
    _card(tmp_path, "c", "Beat C", sequence="Act I", order=3)

    result = _run(tmp_path)

    (sequence,) = _sequences(result)
    assert str(sequence.uri).endswith("narrative-sequence/act-i")
    assert _member_names(sequence) == ["Beat A", "Beat B", "Beat C"]
    assert _proper_part_count(sequence) == 3


# --- Scenario C: duplicate `order` tie-breaks by unit slug (FR-006/SC-004) ----


def test_duplicate_order_tie_breaks_by_slug_and_is_stable(tmp_path: Path) -> None:
    _card(tmp_path, "zeta", "Zeta Beat", sequence="Act I", order=1)
    _card(tmp_path, "alpha", "Alpha Beat", sequence="Act I", order=1)

    first = _run(tmp_path)
    (seq_first,) = _sequences(first)
    # Both share `order: 1`; the unit slug (`alpha-beat` < `zeta-beat`) breaks the tie.
    assert _member_names(seq_first) == ["Alpha Beat", "Zeta Beat"]

    # Determinism: a second independent build yields the identical member tuple.
    second = _run(tmp_path)
    (seq_second,) = _sequences(second)
    assert _member_names(seq_second) == _member_names(seq_first)


# --- missing `order` → placed last, slug-ordered among order-less peers (FR-005) ---


def test_missing_order_placed_last_then_slug(tmp_path: Path) -> None:
    _card(tmp_path, "mid", "Middle Beat", sequence="Act I", order=5)
    _card(tmp_path, "zeta", "Zeta Beat", sequence="Act I", order=None)
    _card(tmp_path, "alpha", "Alpha Beat", sequence="Act I", order=None)

    result = _run(tmp_path)

    (sequence,) = _sequences(result)
    # Explicit-`order` member first; the two order-less members last, by unit slug.
    assert _member_names(sequence) == ["Middle Beat", "Alpha Beat", "Zeta Beat"]


# --- materialized ordinal: subject=unit, contiguous 1..k under gap/dup/missing ---


def test_member_ordinals_are_contiguous_and_subject_is_unit(tmp_path: Path) -> None:
    """FR-003/FR-004 (C4): under a gap, a duplicate, and a missing ``order:``, the
    emitted ``bw:sequenceOrdinal`` objects are contiguous ``1..k`` ``xsd:integer``
    whose subject is each member unit URI, reproducing ``_member_sort_key`` order."""
    _card(tmp_path, "mid", "Middle Beat", sequence="Act I", order=5)  # gap (1 → 5)
    _card(tmp_path, "first", "First Beat", sequence="Act I", order=1)
    _card(tmp_path, "dup", "Dup Beat", sequence="Act I", order=5)  # duplicate order
    _card(tmp_path, "tail", "Tail Beat", sequence="Act I", order=None)  # missing → last

    result = _run(tmp_path)
    (sequence,) = _sequences(result)

    members = [u for u in sequence.units if isinstance(u, NarrativeUnit)]
    expected = [(str(u.uri), Literal(i, datatype=XSD.integer)) for i, u in enumerate(members, 1)]
    # The ordinal triples reproduce the assembled total order, subject = the unit URI.
    assert _ordinals(sequence) == expected
    # Contiguous 1..4 regardless of the authored gap/duplicate/missing values.
    assert [o for _, o in _ordinals(sequence)] == [
        Literal(i, datatype=XSD.integer) for i in range(1, 5)
    ]


# --- Scenario D: single-member sequence → exactly one proper-part edge ---------


def test_single_member_sequence(tmp_path: Path) -> None:
    _card(tmp_path, "coda", "The Coda", sequence="Coda", order=1)

    result = _run(tmp_path)

    (sequence,) = _sequences(result)
    assert str(sequence.uri).endswith("narrative-sequence/coda")
    assert _member_names(sequence) == ["The Coda"]
    assert _proper_part_count(sequence) == 1


# --- raw casing/spacing variants slug to one sequence, first card names it (D4) ---


def test_casing_variants_dedup_to_one_sequence(tmp_path: Path) -> None:
    _card(tmp_path, "a", "Beat A", sequence="Act I", order=1)
    _card(tmp_path, "b", "Beat B", sequence="ACT I", order=2)

    result = _run(tmp_path)

    (sequence,) = _sequences(result)
    # One slug `act-i`; the first card in glob order (`a.md`) supplies the display name.
    assert sequence.name == "Act I"
    assert _member_names(sequence) == ["Beat A", "Beat B"]


# --- a non-string `sequence` / non-int `order` skips the card, no partial member ---


def test_non_string_sequence_skips_card(tmp_path: Path) -> None:
    _write(tmp_path / "outline/units/bad.md", "---\nname: Bad\nsequence: [not, a, string]\n---\n")
    result = _run(tmp_path)

    assert [s.path for s in result.skipped] == ["outline/units/bad.md"]
    assert _sequences(result) == []


def test_non_int_order_skips_card(tmp_path: Path) -> None:
    _write(
        tmp_path / "outline/units/bad.md", '---\nname: Bad\nsequence: "Act I"\norder: true\n---\n'
    )
    result = _run(tmp_path)

    assert [s.path for s in result.skipped] == ["outline/units/bad.md"]
    assert _sequences(result) == []


# --- `order` without `sequence` is a soft note, no membership (FR-008/D8) ------


def test_lone_order_is_soft_note(tmp_path: Path) -> None:
    _card(tmp_path, "lone", "Lone Beat", sequence=None, order=3)
    result = _run(tmp_path)

    assert _sequences(result) == []
    assert [(u.path, u.key) for u in result.unknown_keys] == [("outline/units/lone.md", "order")]
    # The unit itself is still built, unsequenced.
    assert [e.name for e in result.entities if isinstance(e, NarrativeUnit)] == ["Lone Beat"]


# --- a blank/whitespace-only `sequence` is no membership at all (FR-004) -------


def test_blank_sequence_mints_nothing(tmp_path: Path) -> None:
    _write(tmp_path / "outline/units/blank.md", '---\nname: Blank\nsequence: "   "\n---\n')
    result = _run(tmp_path)

    # Whitespace-only `sequence` coerces to no membership; the unit is still built.
    assert _sequences(result) == []
    assert result.skipped == []
    assert [e.name for e in result.entities if isinstance(e, NarrativeUnit)] == ["Blank"]


# --- Scenario E/B: no card declares `sequence` → zero G7, iter-028 unchanged ---


def test_no_sequence_keys_mints_nothing(tmp_path: Path) -> None:
    # A unit with functions/roles but no `sequence` builds exactly as iteration 028.
    _write(
        tmp_path / "outline/units/opening.md",
        '---\nname: "Opening"\nfunctions: [departure]\n---\n',
    )
    result = _run(tmp_path)

    assert _sequences(result) == []
    (unit,) = [e for e in result.entities if isinstance(e, NarrativeUnit)]
    # Its iteration-028 triples are untouched (no proper-part edge anywhere).
    assert all(p != PROPER_PART for _, p, _ in unit.to_triples())
    assert result.unknown_keys == []
