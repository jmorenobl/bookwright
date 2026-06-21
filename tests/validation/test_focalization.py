"""``focalization`` — narrative-voice breaks, bilingual declaration parsing."""

from __future__ import annotations

import importlib.resources
from pathlib import Path

import pytest

from bookwright.indexers import RdflibIndexer
from bookwright.validation.base import Severity, Violation
from bookwright.validation.validators.focalization import Focalization, _parse_declaration
from tests.validation.conftest import load_context, write_project


def _run(root: Path) -> list[Violation]:
    return Focalization().validate(load_context(root), RdflibIndexer())


def test_first_person_outside_dialogue_warns(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="# Constitución\n\nVoz narrativa: tercera persona\n",
        manuscript={"cap-01.md": "Aparici caminaba.\nYo no entendía nada.\n"},
    )
    findings = _run(project_root)
    assert any(f.severity == Severity.warning and "first-person" in f.message for f in findings)


def test_head_hopping_on_non_focal_character_warns(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici", "Peña"],
        constitution="Voz narrativa: tercera persona limitada, focalizada en Aparici\n",
        manuscript={"cap-01.md": "Aparici observó la sala.\nPeña pensó que todo acababa.\n"},
    )
    findings = _run(project_root)
    hops = [f for f in findings if "head-hopping" in f.message]
    assert len(hops) == 1
    assert "Peña" in hops[0].message
    assert hops[0].source == "manuscript/cap-01.md:2"


def test_english_declaration_parses_equivalently(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Narrative voice: third person limited, focused on Aparici\n",
        manuscript={"cap-01.md": "Aparici walked on.\nI did not understand.\n"},
    )
    findings = _run(project_root)
    assert any("first-person" in f.message for f in findings)


def test_dialogue_line_is_exempt(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Voz narrativa: tercera persona\n",
        manuscript={"cap-01.md": "Aparici asintió.\n—Yo me marcho —dijo.\n"},
    )
    # The first-person pronoun sits in dialogue (em-dash opener) → not a break.
    assert all("first-person" not in f.message for f in _run(project_root))


def test_no_parsable_declaration_yields_nothing(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="# Constitución\n\nSin declaración de punto de vista.\n",
        manuscript={"cap-01.md": "Yo llegué tarde.\n"},
    )
    assert _run(project_root) == []


# --- markdown-prefixed declarations parse identically to the bare form ---

# The body shared by every parity case; `Elena Vidal` is the named focal character.
_BODY = "Tercera persona limitada, centrada en Elena Vidal"
_NAMES = ["Elena Vidal"]
_BARE = _parse_declaration(f"Voz narrativa: {_BODY}", _NAMES)


@pytest.mark.parametrize(
    "marker",
    ["-", "*", "+", ">"],  # FR-001: one line-leading bullet/blockquote marker
)
def test_bullet_marker_parses_like_bare_form(marker: str) -> None:
    # Acceptance Scenario 4 / contract C2-C5: each bullet marker (+ space) is stripped.
    parsed = _parse_declaration(f"{marker} Voz narrativa: {_BODY}", _NAMES)
    assert parsed == _BARE
    assert parsed is not None and parsed.person == "third"


@pytest.mark.parametrize(
    "line",
    [
        "**Voz narrativa**: ",  # C6 bold, balanced
        "*Voz narrativa*: ",  # C7 italic, balanced
        "_Voz narrativa_: ",  # C8 underscore, balanced
        "**Voz narrativa: ",  # C10 single-sided emphasis (FR-002, no balance guard)
        "Voz narrativa**: ",  # C10 single-sided emphasis on the closing side
    ],
)
def test_emphasis_run_parses_like_bare_form(line: str) -> None:
    # Acceptance Scenario 4 / contract C6-C8, C10: each emphasis run is stripped
    # independently on each side of the label.
    parsed = _parse_declaration(line + _BODY, _NAMES)
    assert parsed == _BARE


def test_scaffold_shape_parses_to_concrete_values() -> None:
    # FR-003 / FR-004 / contract C9: the exact shape the scaffold emits.
    parsed = _parse_declaration(f"- **Voz narrativa**: {_BODY}", _NAMES)
    assert parsed is not None
    assert parsed.person == "third"
    assert parsed.limited is True
    assert parsed.focal == "Elena Vidal"


def test_english_scaffold_shape_parses() -> None:
    # SC-002 / contract C11: the English label under the scaffold markup.
    parsed = _parse_declaration(
        "- **Narrative voice**: third person limited, focused on Elena Vidal", _NAMES
    )
    assert parsed is not None
    assert parsed.person == "third"
    assert parsed.limited is True
    assert parsed.focal == "Elena Vidal"


def test_indented_scaffold_shape_parses() -> None:
    # contract C12: leading indentation before the bullet is tolerated.
    parsed = _parse_declaration(f"   - **Voz narrativa**: {_BODY}", _NAMES)
    assert parsed == _BARE


def test_scaffold_shape_wakes_validator_through_validate(project_root: Path) -> None:
    # Acceptance Scenario 2 / FR-010: the scaffold shape, end-to-end through
    # `validate`, fires the third-person rule — and emits NO graph triples.
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="# Constitución\n\n- **Voz narrativa**: tercera persona\n",
        manuscript={"cap-01.md": "Aparici caminaba.\nYo no entendía nada.\n"},
    )
    findings = _run(project_root)
    assert any("first-person" in f.message for f in findings)
    assert all(f.triples == () for f in findings)  # Principle X — prose validator only


# --- the live scaffold template and the parser stay bound (FR-007) ---

# The EXACT live scaffold constitution, read once and shared by every binding test
# below (placeholder intact — its body really contains "tercera persona"/"limitada").
_SCAFFOLD_CONSTITUTION = (
    importlib.resources.files("bookwright.resources.project.bible")
    .joinpath("constitution.md.j2")
    .read_text(encoding="utf-8")
)


def test_template_binding() -> None:
    # FR-007 / SC-004: read the live scaffold constitution template and assert the
    # parser recognizes its narrative-voice line. Mangling that line in the
    # template (e.g. removing the colon, or changing the label) MUST fail this test
    # — it is the durable anti-drift guarantee against template↔parser divergence.
    voice_lines = [ln for ln in _SCAFFOLD_CONSTITUTION.splitlines() if "Voz narrativa" in ln]
    assert len(voice_lines) == 1, "expected exactly one narrative-voice line in the template"
    # The live placeholder line parses to None BY DESIGN (DEBT-007): its body is
    # *solely* an unanswered `[PENDING: …]` token, so it is no declaration. This still
    # binds the live template body to the parser — mangling that line (e.g. removing
    # the colon, or answering it with a real voice) flips this assertion and fails the
    # test, the durable anti-drift guarantee against template↔parser divergence.
    assert _parse_declaration(voice_lines[0], []) is None


def test_live_scaffold_constitution_yields_nothing(project_root: Path) -> None:
    # FR-007 / SC-001 / contract C2, V1: the EXACT live scaffold constitution
    # (placeholder intact — its body really contains "tercera persona"/"limitada",
    # unlike `test_pending_markdown_declaration_yields_nothing` which simplifies it)
    # plus a manuscript scene with an interiority verb on a named character yields
    # zero findings. This is DEBT-007: before the guard, the placeholder text parsed
    # as third-person-limited and flooded head-hopping warnings.
    write_project(
        project_root,
        characters=["Halia"],
        constitution=_SCAFFOLD_CONSTITUTION,
        manuscript={"cap-01.md": "Halia pensó que el faro callaba.\n"},
    )
    assert _run(project_root) == []


def test_live_scaffold_first_person_yields_nothing(project_root: Path) -> None:
    # Acceptance scenario 2: the same untouched scaffold constitution + a first-person
    # line outside dialogue. No person is declared ⇒ neither the first-person nor the
    # head-hopping rule may fire.
    write_project(
        project_root,
        characters=["Halia"],
        constitution=_SCAFFOLD_CONSTITUTION,
        manuscript={"cap-01.md": "Yo no entendía nada.\n"},
    )
    assert _run(project_root) == []


@pytest.mark.parametrize(
    ("text", "expected_person"),
    [
        ("Voz narrativa:   [pending: ¿x?]  ", None),  # C3 — whitespace + lowercase keyword
        ("Voz narrativa: Tercera persona [PENDING: ¿focal?]", "third"),  # C4 — text BEFORE
        ("Voz narrativa: [PENDING: …] tercera persona", "third"),  # C5 — text AFTER
        ("Narrative voice: [PENDING: who narrates?]", None),  # FR-004 — EN label, suppressed
    ],
)
def test_pending_recognition_boundary(text: str, expected_person: str | None) -> None:
    # FR-002 / FR-004 / contract C3-C5: the recognition boundary `_PENDING_ONLY` draws.
    # A body that is *solely* the token is suppressed (→ None); a body that merely
    # *contains* the token alongside real declared text stays a real declaration. The
    # over-match guard the real-voice wake-up (FR-008) depends on.
    parsed = _parse_declaration(text, _NAMES)
    if expected_person is None:
        assert parsed is None
    else:
        assert parsed is not None and parsed.person == expected_person


def test_replacing_placeholder_with_real_voice_wakes_validator(project_root: Path) -> None:
    # FR-008 / SC-002 / contract V2, V4: start from the scaffold but answer ONLY the
    # placeholder with a real voice; a non-focal character with an interiority verb now
    # fires head-hopping (the validator wakes) and the finding emits no graph triples.
    constitution = _SCAFFOLD_CONSTITUTION.replace(
        "[PENDING: ¿Quién narra y desde qué distancia "
        "(primera/tercera persona, omnisciente/limitada)?]",
        "Tercera persona limitada, focalizada en Halia",
    )
    write_project(
        project_root,
        characters=["Halia", "Peña"],
        constitution=constitution,
        manuscript={"cap-01.md": "Halia observó la sala.\nPeña pensó que todo acababa.\n"},
    )
    findings = _run(project_root)
    hops = [f for f in findings if "head-hopping" in f.message]
    assert len(hops) == 1
    assert "Peña" in hops[0].message
    assert all(f.triples == () for f in findings)  # Principle X / FR-010 — prose only


# --- loosening recognition keeps the no-finding edge cases intact ---


def test_pending_markdown_declaration_yields_nothing(project_root: Path) -> None:
    # FR-005 / SC-003 / contract N3: a markdown-prefixed voice line whose body names
    # no recognizable person yields zero findings even with first-person prose.
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="# Constitución\n\n- **Voz narrativa**: [PENDING: ¿quién narra?]\n",
        manuscript={"cap-01.md": "Yo llegué tarde.\n"},
    )
    assert _run(project_root) == []


def test_label_mid_sentence_is_not_a_declaration() -> None:
    # contract N4: a line merely mentioning the label with no colon-delimited body
    # is not a declaration (no false widening, R2).
    assert _parse_declaration("La voz narrativa de la obra es lírica.", _NAMES) is None
