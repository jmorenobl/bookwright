"""``focalization`` — narrative-voice breaks, bilingual declaration parsing."""

from __future__ import annotations

import importlib.resources
from pathlib import Path

import pytest

from bookwright.indexers import RdflibIndexer
from bookwright.io.prose import prose_view
from bookwright.validation.base import (
    Abstention,
    EvalResult,
    NotEvaluated,
    NotEvaluatedKind,
    Severity,
    Violation,
)
from bookwright.validation.validators.focalization import Focalization, _parse_declaration
from tests.validation.conftest import load_context, write_project

# The verbatim reason the validator declares for the first-person recall ceiling under
# ANY third-person voice (iteration 053 honesty half, DEBT-021): pro-drop verbal
# morphology is an open set the deterministic check cannot see.
_REASON_FIRST_PERSON_RECALL = (
    "full first-person recall requires semantic judgment (move 3); "
    "the deterministic check only covers the explicit subject pronoun"
)


def _run(root: Path) -> list[Violation]:
    """Run focalization on a project that returns the bare-list shape (form (a)).

    Only the FIRST-PERSON branch returns a bare list now (`return []`); the raise tests
    short-circuit before the assert. Both third-person branches return an `EvalResult`
    (iteration 053), so they use `_run_third_nonlimited` / `_run_partial` instead.
    """
    result = Focalization().validate(load_context(root), RdflibIndexer())
    assert isinstance(result, list)
    return result


def _run_partial(root: Path) -> EvalResult:
    """Run focalization on a limited-third project — it returns the partial shape (c)."""
    result = Focalization().validate(load_context(root), RdflibIndexer())
    assert isinstance(result, EvalResult)
    return result


def _run_third_nonlimited(root: Path) -> list[Violation]:
    """Run focalization on a non-limited 3rd-person project (iteration 053).

    Returns the partial shape carrying EXACTLY the first-person-recall abstention (no
    head-hopping under non-limited third); asserts that and returns its `violations`.
    """
    result = Focalization().validate(load_context(root), RdflibIndexer())
    assert isinstance(result, EvalResult)
    assert len(result.not_evaluated) == 1
    recall = result.not_evaluated[0]
    assert recall.reason == _REASON_FIRST_PERSON_RECALL
    assert recall.kind is NotEvaluatedKind.pending_capability
    assert recall.code == "first_person_recall"
    return result.violations


def test_first_person_voice_carries_no_recall_abstention(project_root: Path) -> None:
    # FR-008/FR-009 (iteration 053): the recall abstention is declared ONLY under a
    # third-person voice. A first-person voice returns the bare `[]` (no EvalResult, no
    # abstention) — there is no third-person recall ceiling to declare.
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Voz narrativa: primera persona\n",
        manuscript={"cap-01.md": "Caminé despacio.\nMe senté a esperar.\n"},
    )
    result = Focalization().validate(load_context(project_root), RdflibIndexer())
    assert result == []  # bare list, no abstention


def test_first_person_outside_dialogue_warns(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="# Constitución\n\nVoz narrativa: tercera persona\n",
        manuscript={"cap-01.md": "Aparici caminaba.\nYo no entendía nada.\n"},
    )
    findings = _run_third_nonlimited(project_root)
    assert any(f.severity == Severity.warning and "first-person" in f.message for f in findings)


# The verbatim reason the validator returns/raises when a parseable limited-third voice
# is declared — head-hopping is a move-3 semantic judgment (iteration 045, FR-002).
_REASON_HEAD_HOPPING = (
    "head-hopping / interiority attribution requires semantic judgment (move 3); "
    "the deterministic heuristic was measured nearly dormant on real prose"
)


def _head_hop_and_recall(result: EvalResult) -> Abstention:
    """Assert the limited-third abstention list is EXACTLY the head-hop + recall pair.

    Iteration 053: under limited-third `focalization` declares TWO `pending_capability`
    abstentions — head-hopping (`code="head_hopping"`) AND first-person-recall
    (`code="first_person_recall"`). Both reasons/kinds/codes are pinned; the head-hop
    entry is returned (it is the one the 052 nudge keys on). Order-independent by `code`.
    """
    by_code = {a.code: a for a in result.not_evaluated}
    assert set(by_code) == {"head_hopping", "first_person_recall"}
    head_hop = by_code["head_hopping"]
    assert head_hop.reason == _REASON_HEAD_HOPPING
    assert head_hop.kind is NotEvaluatedKind.pending_capability
    recall = by_code["first_person_recall"]
    assert recall.reason == _REASON_FIRST_PERSON_RECALL
    assert recall.kind is NotEvaluatedKind.pending_capability
    return head_hop


def test_limited_third_runs_break_check_and_abstains_on_head_hop(project_root: Path) -> None:
    # FR-013/SC-001 (iteration 050): a parseable third-person-LIMITED focal voice whose
    # manuscript HAS a first-person marker outside dialogue now returns the PARTIAL shape
    # (form (c) EvalResult): the deterministic first-person-break check RUNS — exactly one
    # `focalization` warning citing the marker, with a `relpath:line` source — AND the
    # head-hopping abstention (pending_capability) is declared in the SAME run. This is
    # DEBT-019 closed: the break check no longer disappears under a focalized voice.
    write_project(
        project_root,
        characters=["Aparici", "Peña"],
        constitution="Voz narrativa: tercera persona limitada, focalizada en Aparici\n",
        manuscript={"cap-01.md": "Aparici observó la sala.\nYo no entendía nada.\n"},
    )
    result = _run_partial(project_root)
    # exactly one first-person-break warning, citing the marker, with a relpath:line source
    assert len(result.violations) == 1
    break_finding = result.violations[0]
    assert break_finding.validator == "focalization"
    assert break_finding.severity == Severity.warning
    assert "first-person" in break_finding.message and "'Yo'" in break_finding.message
    assert break_finding.source == "manuscript/cap-01.md:2"
    assert break_finding.triples == ()  # Principle X — prose validator only
    # …and exactly one head-hopping abstention (pending_capability) in the same EvalResult
    _head_hop_and_recall(result)


def test_limited_third_abstains_as_capability_gap(project_root: Path) -> None:
    # FR-001/FR-014: a parseable third-person-LIMITED focal voice still abstains on
    # head-hopping (pending_capability) — but now via the PARTIAL EvalResult shape, not a
    # whole-run `raise`. This manuscript has NO first-person break, so `violations` is
    # empty and the result is observationally identical to the old total abstention (C5).
    write_project(
        project_root,
        characters=["Aparici", "Peña"],
        constitution="Voz narrativa: tercera persona limitada, focalizada en Aparici\n",
        manuscript={"cap-01.md": "Aparici observó la sala.\nPeña pensó que todo acababa.\n"},
    )
    result = _run_partial(project_root)
    assert result.violations == []  # no first-person break in this fixture
    _head_hop_and_recall(result)


def test_limited_third_with_no_named_focal_abstains_identically(project_root: Path) -> None:
    # Edge case: a third-limited voice that names NO bible character abstains the same
    # way — the precondition is `third AND limited`, the focal field is gone (FR-007).
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Voz narrativa: tercera persona limitada\n",
        manuscript={"cap-01.md": "Aparici observó la sala.\n"},
    )
    result = _run_partial(project_root)
    assert result.violations == []
    _head_hop_and_recall(result)


def test_english_declaration_runs_break_check_and_abstains(project_root: Path) -> None:
    # FR-014 (retargeted, iteration 050): the English label parses equivalently
    # ("third person limited"), and the first-person break ("I did not understand") now
    # FIRES alongside the head-hopping abstention — the inverse of what 045 asserted
    # (that the break did NOT fire). The DEBT-019 coverage drop is recovered.
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Narrative voice: third person limited, focused on Aparici\n",
        manuscript={"cap-01.md": "Aparici walked on.\nI did not understand.\n"},
    )
    result = _run_partial(project_root)
    assert len(result.violations) == 1
    assert "first-person" in result.violations[0].message and "'I'" in result.violations[0].message
    _head_hop_and_recall(result)


def test_dialogue_line_is_exempt(project_root: Path) -> None:
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Voz narrativa: tercera persona\n",
        manuscript={"cap-01.md": "Aparici asintió.\n—Yo me marcho —dijo.\n"},
    )
    # The first-person pronoun sits in dialogue (em-dash opener) → not a break.
    assert all("first-person" not in f.message for f in _run_third_nonlimited(project_root))


# --- tri-valued: the four distinct "could not read a voice" reasons (FR-008) ---
#
# Each cause routes to NotEvaluated with its OWN reason (iteration 040), superseding
# the v0 "return []" reading. (i) and (ii) carry DIFFERENT reasons (the author's
# remedy differs: create the file vs. add the declaration), proving they are split.

_REASON_NO_CONSTITUTION = "there is no constitution to read the narrative voice from"
_REASON_NO_DECLARATION = "the constitution does not declare a narrative voice"
_REASON_PENDING = "the narrative-voice declaration is still unanswered ([PENDING])"
_REASON_NO_PERSON = (
    "the narrative-voice declaration names no grammatical person (neither first nor third)"
)


def test_no_constitution_is_not_evaluated(project_root: Path) -> None:
    # (i) no constitution file at all — distinct from (ii) below.
    write_project(
        project_root,
        characters=["Aparici"],
        manuscript={"cap-01.md": "Yo llegué tarde.\n"},
    )
    with pytest.raises(NotEvaluated) as excinfo:
        _run(project_root)
    assert excinfo.value.reason == _REASON_NO_CONSTITUTION
    # The gap is input-conditional (a missing constitution): kind defaults to
    # missing_input (FR-002, iteration 044) — focalization never opts into a capability-gap.
    assert excinfo.value.kind is NotEvaluatedKind.missing_input


def test_no_parsable_declaration_is_not_evaluated(project_root: Path) -> None:
    # (ii) a constitution present, but no line declares a voice — distinct reason from (i).
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="# Constitución\n\nSin declaración de punto de vista.\n",
        manuscript={"cap-01.md": "Yo llegué tarde.\n"},
    )
    with pytest.raises(NotEvaluated) as excinfo:
        _run(project_root)
    assert excinfo.value.reason == _REASON_NO_DECLARATION
    assert _REASON_NO_DECLARATION != _REASON_NO_CONSTITUTION  # (i) and (ii) really differ


def test_empty_constitution_is_no_declaration_not_no_constitution(project_root: Path) -> None:
    # A present-but-empty constitution has a file (so NOT cause (i)); it just declares
    # nothing → cause (ii), with the accurate reason.
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="",
        manuscript={"cap-01.md": "Yo llegué tarde.\n"},
    )
    with pytest.raises(NotEvaluated) as excinfo:
        _run(project_root)
    assert excinfo.value.reason == _REASON_NO_DECLARATION


def test_pending_placeholder_is_not_evaluated(project_root: Path) -> None:
    # (iii) the voice is still an unanswered `[PENDING: …]` placeholder.
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="- **Voz narrativa**: [PENDING: ¿primera/tercera persona?]\n",
        manuscript={"cap-01.md": "Yo llegué tarde.\n"},
    )
    with pytest.raises(NotEvaluated) as excinfo:
        _run(project_root)
    assert excinfo.value.reason == _REASON_PENDING


def test_declaration_without_person_is_not_evaluated(project_root: Path) -> None:
    # (iv) a declaration present, but it names no grammatical person.
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Voz narrativa: narrador omnisciente\n",
        manuscript={"cap-01.md": "Aparici caminaba.\n"},
    )
    with pytest.raises(NotEvaluated) as excinfo:
        _run(project_root)
    assert excinfo.value.reason == _REASON_NO_PERSON


def test_usable_third_person_is_evaluated_and_clean(project_root: Path) -> None:
    # A usable third person on a clean manuscript → evaluated, [] (a legitimate green) —
    # never raises (FR-003/FR-008).
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Voz narrativa: tercera persona\n",
        manuscript={"cap-01.md": "Aparici caminaba despacio.\n"},
    )
    # Non-limited third now returns the partial shape: violations empty, plus the honest
    # first-person-recall abstention (asserted inside the helper) — still a legitimate green.
    assert _run_third_nonlimited(project_root) == []


def test_usable_first_person_is_evaluated_and_clean(project_root: Path) -> None:
    # A usable first person likewise stays evaluated with zero findings — never raises.
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Voz narrativa: primera persona\n",
        manuscript={"cap-01.md": "Yo caminaba despacio.\n"},
    )
    assert _run(project_root) == []


# --- markdown-prefixed declarations parse identically to the bare form ---

# The body shared by every parity case; `Elena Vidal` is the named focal character.
_BODY = "Tercera persona limitada, centrada en Elena Vidal"
_BARE = _parse_declaration(prose_view(f"Voz narrativa: {_BODY}"))


@pytest.mark.parametrize(
    "marker",
    ["-", "*", "+", ">"],  # FR-001: one line-leading bullet/blockquote marker
)
def test_bullet_marker_parses_like_bare_form(marker: str) -> None:
    # Acceptance Scenario 4 / contract C2-C5: each bullet marker (+ space) is stripped.
    parsed = _parse_declaration(prose_view(f"{marker} Voz narrativa: {_BODY}"))
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
    parsed = _parse_declaration(prose_view(line + _BODY))
    assert parsed == _BARE


def test_scaffold_shape_parses_to_concrete_values() -> None:
    # FR-003 / FR-004 / contract C9: the exact shape the scaffold emits.
    parsed = _parse_declaration(prose_view(f"- **Voz narrativa**: {_BODY}"))
    assert parsed is not None
    assert parsed.person == "third"
    assert parsed.limited is True


def test_english_scaffold_shape_parses() -> None:
    # SC-002 / contract C11: the English label under the scaffold markup.
    parsed = _parse_declaration(
        prose_view("- **Narrative voice**: third person limited, focused on Elena Vidal"),
    )
    assert parsed is not None
    assert parsed.person == "third"
    assert parsed.limited is True


def test_indented_scaffold_shape_parses() -> None:
    # contract C12: leading indentation before the bullet is tolerated.
    parsed = _parse_declaration(prose_view(f"   - **Voz narrativa**: {_BODY}"))
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
    findings = _run_third_nonlimited(project_root)
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
    # The live placeholder line is NOT-EVALUATED BY DESIGN (DEBT-007, now tri-valued):
    # its body is *solely* an unanswered `[PENDING: …]` token, so the parser raises
    # NotEvaluated rather than returning a declaration. This still binds the live
    # template body to the parser — mangling that line (e.g. removing the colon, or
    # answering it with a real voice) flips this assertion and fails the test, the
    # durable anti-drift guarantee against template↔parser divergence.
    with pytest.raises(NotEvaluated) as excinfo:
        _parse_declaration(prose_view(voice_lines[0]))
    assert excinfo.value.reason == _REASON_PENDING


def test_live_scaffold_constitution_is_not_evaluated(project_root: Path) -> None:
    # FR-007 / SC-001 / contract C2, V1: the EXACT live scaffold constitution
    # (placeholder intact — its body really contains "tercera persona"/"limitada")
    # plus a manuscript scene with an interiority verb on a named character is
    # NOT-EVALUATED (the placeholder is no declaration). This is DEBT-007: before the
    # guard, the placeholder text parsed as third-person-limited and flooded
    # head-hopping warnings; now the run is honestly not-evaluated, never green.
    write_project(
        project_root,
        characters=["Halia"],
        constitution=_SCAFFOLD_CONSTITUTION,
        manuscript={"cap-01.md": "Halia pensó que el faro callaba.\n"},
    )
    with pytest.raises(NotEvaluated) as excinfo:
        _run(project_root)
    assert excinfo.value.reason == _REASON_PENDING


def test_live_scaffold_first_person_is_not_evaluated(project_root: Path) -> None:
    # Acceptance scenario 2: the same untouched scaffold constitution + a first-person
    # line outside dialogue. The placeholder is no declaration ⇒ not-evaluated; neither
    # the first-person nor the head-hopping rule may fire.
    write_project(
        project_root,
        characters=["Halia"],
        constitution=_SCAFFOLD_CONSTITUTION,
        manuscript={"cap-01.md": "Yo no entendía nada.\n"},
    )
    with pytest.raises(NotEvaluated) as excinfo:
        _run(project_root)
    assert excinfo.value.reason == _REASON_PENDING


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
    # A body that is *solely* the token is not-evaluated (raises NotEvaluated under the
    # tri-valued contract); a body that merely *contains* the token alongside real
    # declared text stays a real declaration. The over-match guard the real-voice
    # wake-up (FR-008) depends on.
    if expected_person is None:
        with pytest.raises(NotEvaluated) as excinfo:
            _parse_declaration(prose_view(text))
        assert excinfo.value.reason == _REASON_PENDING
    else:
        parsed = _parse_declaration(prose_view(text))
        assert parsed.person == expected_person


def test_replacing_placeholder_with_real_voice_wakes_validator(project_root: Path) -> None:
    # FR-008 / SC-002 / contract V2, V4: start from the scaffold but answer ONLY the
    # placeholder with a real voice. The [PENDING] → real-voice transition is still
    # proven — a limited-third voice now returns the PARTIAL EvalResult shape: it
    # abstains on head-hopping (pending_capability) while running the break check
    # (this manuscript has no first-person break, so `violations` is empty; iteration 050).
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
    result = _run_partial(project_root)
    assert result.violations == []
    _head_hop_and_recall(result)


# --- loosening recognition keeps the no-finding edge cases intact ---


def test_pending_markdown_declaration_is_not_evaluated(project_root: Path) -> None:
    # FR-005 / SC-003 / contract N3: a markdown-prefixed voice line whose body is solely
    # a `[PENDING]` placeholder is not-evaluated (raises) even with first-person prose.
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="# Constitución\n\n- **Voz narrativa**: [PENDING: ¿quién narra?]\n",
        manuscript={"cap-01.md": "Yo llegué tarde.\n"},
    )
    with pytest.raises(NotEvaluated) as excinfo:
        _run(project_root)
    assert excinfo.value.reason == _REASON_PENDING


def test_label_mid_sentence_is_not_a_declaration() -> None:
    # contract N4: a line merely mentioning the label with no colon-delimited body
    # is not a declaration — not-evaluated (no false widening, R2).
    with pytest.raises(NotEvaluated) as excinfo:
        _parse_declaration(prose_view("La voz narrativa de la obra es lírica."))
    assert excinfo.value.reason == _REASON_NO_DECLARATION


# --- the seam: per-line scans read RAW, locators are the source line number ---


def test_first_person_locator_is_source_line_over_raw(project_root: Path) -> None:
    # Story 3 / FR-010 / C6.2: the first-person scan reads `.raw` and the finding is
    # located by the line's 1-based source `number` — a leading heading shifts the
    # break to line 3, which the locator reflects exactly.
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Voz narrativa: tercera persona\n",
        manuscript={"cap-01.md": "# Capítulo 1\n\nYo no entendía nada.\n"},
    )
    findings = _run_third_nonlimited(project_root)
    breaks = [f for f in findings if "first-person" in f.message]
    assert len(breaks) == 1
    assert breaks[0].source == "manuscript/cap-01.md:3"


def test_bullet_prefixed_line_stays_dialogue_exempt(project_root: Path) -> None:
    # C6.2: reading `.raw` keeps the dialogue exemption byte-for-byte — a `- `-led
    # line is a dialogue prefix, so its first-person pronoun is NOT a break (unchanged).
    write_project(
        project_root,
        characters=["Aparici"],
        constitution="Voz narrativa: tercera persona\n",
        manuscript={"cap-01.md": "Aparici asintió.\n- Yo me marcho.\n"},
    )
    assert all("first-person" not in f.message for f in _run_third_nonlimited(project_root))
