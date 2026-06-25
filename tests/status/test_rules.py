"""The rule table in isolation: synthetic states → exact actions (020).

No graph, no disk, no project (SC-005): every state is hand-built. Prompts and
reasons are pinned with exact-match strings — determinism (FR-008/SC-002)
requires the templates be *fixed*, so any wording change must consciously
update these pins.
"""

from __future__ import annotations

from bookwright.status.model import (
    AnchorGap,
    GraphFacts,
    LowReliabilityFinding,
    OpenQuestion,
    StatusState,
    ValidationSummary,
)
from bookwright.status.rules import _REMEDIES, RULES, next_actions
from bookwright.validation.base import NotEvaluatedKind, NotEvaluatedResult

_FILE = "bible/research/tema.md"
_HEALTHY_GRAPH = GraphFacts(available=True, entities=5, triples=50)


def make_state(  # noqa: PLR0913 — one keyword knob per state fact, defaults healthy
    *,
    graph: GraphFacts = _HEALTHY_GRAPH,
    open_questions: tuple[OpenQuestion, ...] = (),
    unresolved_anchors: tuple[AnchorGap, ...] = (),
    low_reliability_findings: tuple[LowReliabilityFinding, ...] = (),
    errors: int = 0,
    not_evaluated: tuple[NotEvaluatedResult, ...] = (),
    focus_defined: bool = True,
) -> StatusState:
    """A healthy, focused state by default; each knob degrades one fact."""
    return StatusState(
        phase="drafting",
        focus_defined=focus_defined,
        graph=graph,
        open_questions=open_questions,
        unresolved_anchors=unresolved_anchors,
        low_reliability_findings=low_reliability_findings,
        validation=ValidationSummary(
            counts={"error": errors, "warning": 0, "info": 0},
            ran=("temporal",),
            not_evaluated=not_evaluated,
        ),
    )


_QUESTION = OpenQuestion(id="q-archivo", text="¿Dónde está el libro?", file=_FILE)
_GAP = AnchorGap(promotes="f-1", constrains="timeline", file=_FILE, problems=("under_reliable",))
_LOW = LowReliabilityFinding(id="f-1", best_reliability="baja", file=_FILE)
_DORMANT_FOCAL = NotEvaluatedResult(
    "focalization", "the constitution does not declare a narrative voice"
)
#: A permanent capability-gap entry (iteration 044): never nudged by the dormant rule,
#: never denies green. Since iteration 053 it carries `code="undeclared_characters"` (the
#: form (b)→(c) conversion), the discriminator `judge_undeclared_characters` now keys on.
_DORMANT_CAP = NotEvaluatedResult(
    "character_unknown_mentions",
    "open-set proper-noun discovery requires semantic judgment (move 3)",
    NotEvaluatedKind.pending_capability,
    code="undeclared_characters",
)
#: The focalization head-hopping capability-gap (iteration 045): `pending_capability`.
#: It must NOT fire the iteration-051 `judge_undeclared_characters` nudge (keyed on
#: `character_unknown_mentions`), but — since iteration 052 — it DOES fire the peer
#: `judge_head_hopping` nudge. Since iteration 053 the nudge keys on `(validator, code)`,
#: so the entry carries `code="head_hopping"` (FR-014).
_DORMANT_FOCAL_CAP = NotEvaluatedResult(
    "focalization",
    "head-hopping / interiority attribution requires semantic judgment (move 3)",
    NotEvaluatedKind.pending_capability,
    code="head_hopping",
)
#: The focalization first-person-recall capability-gap (iteration 053, honesty half).
#: A `pending_capability` `focalization` abstention like head-hopping, but with
#: `code="first_person_recall"`. Since iteration 054 (the judgment half) it fires the
#: peer `judge_first_person_recall` nudge — keyed on `(focalization, first_person_recall)`
#: — and NOT the head-hopping nudge (the `code` keying keeps the two apart). It models
#: third-person-NON-limited (recall present, head-hopping absent).
_DORMANT_FOCAL_RECALL = NotEvaluatedResult(
    "focalization",
    "full first-person recall requires semantic judgment (move 3)",
    NotEvaluatedKind.pending_capability,
    code="first_person_recall",
)

#: One synthetic state per rule, exercising exactly it (SC-005).
_TRIGGER: dict[str, StatusState] = {
    "bootstrap_graph": make_state(graph=GraphFacts(available=False, entities=0, triples=0)),
    "research_queue": make_state(open_questions=(_QUESTION,)),
    "verify_findings": make_state(low_reliability_findings=(_LOW,)),
    "review_continuity": make_state(errors=2),
    "activate_dormant_validators": make_state(not_evaluated=(_DORMANT_FOCAL,)),
    "judge_undeclared_characters": make_state(not_evaluated=(_DORMANT_CAP,)),
    "judge_head_hopping": make_state(not_evaluated=(_DORMANT_FOCAL_CAP,)),
    "judge_first_person_recall": make_state(not_evaluated=(_DORMANT_FOCAL_RECALL,)),
    "define_focus": make_state(focus_defined=False),
}


def test_every_rule_is_exercised_by_a_synthetic_state() -> None:
    assert {rule.name for rule in RULES} == set(_TRIGGER)  # the matrix covers the table
    for rule in RULES:
        assert rule.applies(_TRIGGER[rule.name]), rule.name
        action = rule.build(_TRIGGER[rule.name])
        # SC-004: every action carries all three components, none empty.
        assert action.skill and action.prompt and action.reason


def test_healthy_focused_state_yields_no_actions() -> None:
    assert next_actions(make_state()) == []


def test_repeat_calls_are_equal() -> None:
    state = make_state(open_questions=(_QUESTION,), unresolved_anchors=(_GAP,), errors=1)
    assert next_actions(state) == next_actions(state)  # repeat-call determinism (FR-008)


def test_degraded_graph_short_circuits_to_the_single_bootstrap_action() -> None:
    # Everything is "wrong" at once, but with no graph the bootstrap action is
    # the whole answer (research D5).
    state = make_state(
        graph=GraphFacts(available=False, entities=0, triples=0),
        open_questions=(_QUESTION,),
        low_reliability_findings=(_LOW,),
        errors=3,
        focus_defined=False,
    )
    actions = next_actions(state)
    assert len(actions) == 1
    assert actions[0].skill == "bookwright-bible"
    assert actions[0].reason == "the knowledge graph has no entities to reason over yet"


def test_empty_graph_with_entities_zero_also_short_circuits() -> None:
    state = make_state(graph=GraphFacts(available=True, entities=0, triples=0))
    [action] = next_actions(state)
    assert action.skill == "bookwright-bible"


def test_research_queue_action_exact_match() -> None:
    state = make_state(open_questions=(_QUESTION,), unresolved_anchors=(_GAP,))
    [action] = next_actions(state)
    assert action.skill == "bookwright-research"
    assert action.prompt == (
        "Work through the research queue. "
        "Open questions: q-archivo: ¿Dónde está el libro?. "
        "Anchors needing support: f-1 -> timeline. "
        "Record each finding with its sources under bible/research/."
    )
    assert action.reason == "1 open research question and 1 unresolved anchor"


def test_research_queue_pluralizes_and_lists_every_item() -> None:
    second = OpenQuestion(id="q-otro", text=None, file=_FILE)
    state = make_state(open_questions=(_QUESTION, second))
    [action] = next_actions(state)
    assert "q-archivo: ¿Dónde está el libro?; q-otro." in action.prompt
    assert action.reason == "2 open research questions and 0 unresolved anchors"


def test_verify_findings_action_exact_match() -> None:
    unrated = LowReliabilityFinding(id="f-2", best_reliability=None, file=_FILE)
    state = make_state(low_reliability_findings=(_LOW, unrated))
    [action] = next_actions(state)
    assert action.skill == "bookwright-verify"
    assert action.prompt == (
        "Verify the findings whose support is below the project threshold: "
        "f-1 (best support: baja); f-2 (unrated). "
        "Strengthen each with more reliable sources or revise its claim."
    )
    assert action.reason == "2 findings with low-reliability support"


def test_review_continuity_action_exact_match() -> None:
    [action] = next_actions(make_state(errors=1))
    assert action.skill == "bookwright-continuity"
    assert action.prompt == (
        "Review the continuity errors in the bible and manuscript; run "
        "`bookwright validate` for the detailed report, then fix each error "
        "at its source file."
    )
    assert action.reason == "1 validation error"


def test_define_focus_action_exact_match() -> None:
    [action] = next_actions(make_state(focus_defined=False))
    assert action.skill == "bookwright focus set"
    assert action.prompt == (
        "Define the current working focus: run `bookwright focus set "
        '--target "<what you are working on>" --notes "<why>"`.'
    )
    assert action.reason == "no authored focus is defined"


def test_actions_emit_in_table_priority_order() -> None:
    state = make_state(
        open_questions=(_QUESTION,),
        low_reliability_findings=(_LOW,),
        errors=1,
        focus_defined=False,
    )
    skills = [action.skill for action in next_actions(state)]
    assert skills == [
        "bookwright-research",
        "bookwright-verify",
        "bookwright-continuity",
        "bookwright focus set",
    ]


def test_activate_dormant_validators_names_the_focalization_remedy() -> None:
    # SC-004: a not-evaluated focalization yields a step naming its concrete remedy.
    [action] = next_actions(make_state(not_evaluated=(_DORMANT_FOCAL,)))
    assert action.skill == "bookwright-continuity"
    assert action.prompt == (
        "Activate the dormant validators: "
        "focalization — declare the narrative voice in the constitution."
    )
    assert action.reason == "1 validator could not evaluate"


def test_activate_dormant_validators_lists_every_dormant_remedy() -> None:
    # Multiple dormant validators → each remedy enumerated, count pluralized.
    dormant = (
        NotEvaluatedResult("character_presence", "no inputs"),
        _DORMANT_FOCAL,
    )
    [action] = next_actions(make_state(not_evaluated=dormant))
    assert action.prompt == (
        "Activate the dormant validators: "
        "character_presence — add a bible character roster and manuscript prose; "
        "focalization — declare the narrative voice in the constitution."
    )
    assert action.reason == "2 validators could not evaluate"


def test_activate_dormant_validators_falls_back_for_unmapped_validators() -> None:
    # A custom/unmapped dormant validator still appears in the prompt (generic clause)
    # and is counted — the prompt never drops a validator the reason counts.
    dormant = (
        NotEvaluatedResult("custom_check", "no inputs"),
        _DORMANT_FOCAL,
    )
    [action] = next_actions(make_state(not_evaluated=dormant))
    assert action.prompt == (
        "Activate the dormant validators: "
        "custom_check — investigate why it could not evaluate; "
        "focalization — declare the narrative voice in the constitution."
    )
    assert action.reason == "2 validators could not evaluate"


def test_no_dormant_validators_yields_no_activation_action() -> None:
    # Empty not_evaluated → the rule produces nothing (no false positives).
    skills = [action.skill for action in next_actions(make_state())]
    assert "bookwright-continuity" not in skills


def test_capability_gap_run_fires_the_judge_nudge_not_the_dormant_one() -> None:
    # Iteration 051 (move 3, first slice): a pending_capability
    # `character_unknown_mentions` entry now fires the `judge_undeclared_characters`
    # nudge (the skill can answer it) — producing exactly one `bookwright-continuity`
    # action — while STILL producing NO `activate_dormant_validators` action (the
    # permanent capability-gap remains non-actionable for the dormant nudge, 044).
    actions = next_actions(make_state(not_evaluated=(_DORMANT_CAP,)))
    assert [a.skill for a in actions] == ["bookwright-continuity"]
    [action] = actions
    assert not action.prompt.startswith("Activate the dormant validators")


def test_judge_undeclared_characters_action_exact_match() -> None:
    # The judge action is a fixed, byte-identical template (no minted data, SC-002).
    [action] = next_actions(make_state(not_evaluated=(_DORMANT_CAP,)))
    assert action.skill == "bookwright-continuity"
    assert action.prompt == (
        "Scan the manuscript for proper nouns, read the authored roster "
        "(bible/characters/ `name:` plus settings/locations/objects), and report "
        "each person used in the prose with no sheet in bible/characters/."
    )
    assert action.reason == (
        "character_unknown_mentions abstained — open-set proper-noun discovery is a "
        "capability gap; the skill provides the semantic judgment"
    )


def test_focalization_capability_gap_fires_the_head_hopping_judge_nudge() -> None:
    # Iteration 052 (move 3, second slice): a `(focalization, pending_capability)`
    # head-hopping abstention now fires EXACTLY ONE `bookwright-continuity` head-hopping
    # action (the whole point of this slice) — and NOT the iteration-051
    # `judge_undeclared_characters` nudge (which keys on `character_unknown_mentions`).
    actions = next_actions(make_state(not_evaluated=(_DORMANT_FOCAL_CAP,)))
    assert [a.skill for a in actions] == ["bookwright-continuity"]
    [action] = actions
    assert action.reason.startswith("focalization abstained on head-hopping")
    # It is the head-hop nudge, not the undeclared-character nudge.
    assert not action.reason.startswith("character_unknown_mentions abstained")


def test_judge_head_hopping_action_exact_match() -> None:
    # The head-hopping judge action is a fixed, byte-identical template (SC-002),
    # distinct from the iteration-051 undeclared-character action (FR-011).
    [action] = next_actions(make_state(not_evaluated=(_DORMANT_FOCAL_CAP,)))
    assert action.skill == "bookwright-continuity"
    assert action.prompt == (
        "Read the declared narrative voice (bible/constitution.md), the POV calendar "
        "(bible/pov-structure.md), and the roster; under a third-person-limited voice, "
        "judge per chapter whether the prose attributes interiority to a non-focal POV "
        "character, and report each head-hop as a continuity deviation."
    )
    assert action.reason == (
        "focalization abstained on head-hopping under limited-third — interiority "
        "attribution is a capability gap; the skill provides the semantic judgment"
    )


def test_first_person_recall_alone_fires_the_first_person_judge_nudge() -> None:
    # Iteration 054 (move 3, third dimension, judgment half): a lone `(focalization,
    # pending_capability, first_person_recall)` entry — third-person-NON-limited — now
    # fires EXACTLY ONE `bookwright-continuity` first-person action (the whole point of
    # this slice), GREEN. (Rewrite of the 053 `test_first_person_recall_alone_fires_no_
    # judge_nudge`, whose "no nudge yet" state is exactly what 054 closes.) The `code`
    # keying keeps it OFF the head-hopping nudge — the mis-fire it prevents.
    actions = next_actions(make_state(not_evaluated=(_DORMANT_FOCAL_RECALL,)))
    assert [a.skill for a in actions] == ["bookwright-continuity"]
    [action] = actions
    assert action.reason.startswith("focalization abstained on first-person recall")
    # It is the first-person nudge, NOT the head-hopping one (FR-011 keying).
    assert not action.reason.startswith("focalization abstained on head-hopping")


def test_judge_first_person_recall_action_exact_match() -> None:
    # The first-person judge action is a fixed, byte-identical template (SC-002), distinct
    # from the 051 undeclared-character and 052 head-hopping actions (FR-010). Its prompt
    # is grounded ONLY in the declared voice — it names NEITHER the POV calendar NOR the
    # roster (a 1st-person break is grammatical person, not character identity).
    [action] = next_actions(make_state(not_evaluated=(_DORMANT_FOCAL_RECALL,)))
    assert action.skill == "bookwright-continuity"
    assert action.prompt == (
        "Read the declared narrative voice (bible/constitution.md); under any "
        "third-person voice (limited or non-limited), judge per passage whether the "
        "prose slides into first person — including the pro-drop verbal morphology "
        "(Caminé, Me senté) the explicit-pronoun check cannot see — and report each "
        "slip as a continuity deviation."
    )
    assert action.reason == (
        "focalization abstained on first-person recall — the deterministic check only "
        "covers the explicit subject pronoun; the skill provides the semantic judgment"
    )
    # Grounded in the declared voice ONLY — no POV calendar, no roster (research D1).
    assert "bible/pov-structure.md" not in action.prompt
    assert "roster" not in action.prompt.lower()


def test_head_hopping_nudge_never_fires_on_the_first_person_recall_abstention() -> None:
    # FR-011 keying (negative): a `head_hopping`-only state yields the head-hopping nudge
    # and NO first-person action; the first-person nudge never fires on `head_hopping`.
    actions = next_actions(make_state(not_evaluated=(_DORMANT_FOCAL_CAP,)))
    assert [a.skill for a in actions] == ["bookwright-continuity"]
    assert all(
        not a.reason.startswith("focalization abstained on first-person recall") for a in actions
    )


def test_no_first_person_abstention_yields_no_first_person_nudge() -> None:
    # FR-011 negative (declared-first-person analogue): a state with NO `first_person_recall`
    # abstention gains NO first-person nudge. The undeclared-character abstention alone
    # fires only its own judge nudge.
    actions = next_actions(make_state(not_evaluated=(_DORMANT_CAP,)))
    assert all(
        not a.reason.startswith("focalization abstained on first-person recall") for a in actions
    )


def test_flawless_third_person_state_stays_green_with_no_first_person_nudge() -> None:
    # FR-012: a flawless third-person state (no abstentions at all) yields no actions —
    # the informative first-person nudge never invents work, and green is preserved.
    assert next_actions(make_state()) == []


def test_head_hopping_and_recall_together_fire_both_judges_in_table_order() -> None:
    # Iteration 054 (rewrite of the 053 `..._fire_only_the_head_hopping_judge`): limited-
    # third emits BOTH `focalization` abstentions. Now BOTH fire — `judge_head_hopping`
    # then `judge_first_person_recall`, in table order — each a distinct, coherent
    # `bookwright-continuity` action, never merged.
    actions = next_actions(make_state(not_evaluated=(_DORMANT_FOCAL_CAP, _DORMANT_FOCAL_RECALL)))
    assert [a.skill for a in actions] == ["bookwright-continuity", "bookwright-continuity"]
    head_hop, first_person = actions
    assert head_hop.reason.startswith("focalization abstained on head-hopping")
    assert first_person.reason.startswith("focalization abstained on first-person recall")
    assert head_hop.prompt != first_person.prompt


def test_all_three_move3_judge_nudges_co_fire_in_table_order() -> None:
    # Contract C5 (iteration 054): a report carrying ALL THREE move-3 abstentions
    # (`character_unknown_mentions` + `focalization` head-hopping + `focalization`
    # first-person-recall) emits all three continuity actions — undeclared → head-hopping
    # → first-person, in table order — each distinct, none merged. No
    # `activate_dormant_validators` fires (every entry is `pending_capability`).
    state = make_state(not_evaluated=(_DORMANT_CAP, _DORMANT_FOCAL_CAP, _DORMANT_FOCAL_RECALL))
    actions = next_actions(state)
    assert [a.skill for a in actions] == ["bookwright-continuity"] * 3
    undeclared, head_hop, first_person = actions
    assert undeclared.reason.startswith("character_unknown_mentions abstained")
    assert head_hop.reason.startswith("focalization abstained on head-hopping")
    assert first_person.reason.startswith("focalization abstained on first-person recall")
    assert len({undeclared.prompt, head_hop.prompt, first_person.prompt}) == 3  # all distinct
    assert all(not a.prompt.startswith("Activate the dormant validators") for a in actions)


def test_focalization_missing_input_does_not_fire_the_head_hopping_judge() -> None:
    # Negative case (SC-004, contract C5): a `(focalization, missing_input)` gap fires
    # `activate_dormant_validators` (it is input-conditional) and NOT `judge_head_hopping`
    # (which keys on `pending_capability`). The two kinds are kept distinct.
    actions = next_actions(make_state(not_evaluated=(_DORMANT_FOCAL,)))
    assert [a.skill for a in actions] == ["bookwright-continuity"]
    [action] = actions
    assert action.prompt.startswith("Activate the dormant validators")
    assert not action.reason.startswith("focalization abstained on head-hopping")


def test_removed_character_unknown_mentions_remedy_clause_is_gone() -> None:
    # FR-006: the 043 remedy clause for the abstainer is removed — the validator
    # is no longer nudged on, so it must not appear in the remedy table.
    assert "character_unknown_mentions" not in _REMEDIES


def test_both_kinds_at_once_nudges_only_the_missing_input_validator() -> None:
    # Edge case (SC-004): a run with one missing_input and one pending_capability
    # entry fires the dormant nudge naming ONLY the missing_input validator — AND,
    # since iteration 051, the judge nudge (the pending_capability entry is the
    # judge-source `character_unknown_mentions`). Two `bookwright-continuity` actions in
    # table order: activate_dormant_validators, then judge_undeclared_characters.
    state = make_state(not_evaluated=(_DORMANT_CAP, _DORMANT_FOCAL))
    dormant, judge = next_actions(state)
    assert dormant.skill == "bookwright-continuity"
    assert dormant.prompt == (
        "Activate the dormant validators: "
        "focalization — declare the narrative voice in the constitution."
    )
    assert dormant.reason == "1 validator could not evaluate"  # capability-gap excluded
    assert "character_unknown_mentions" not in dormant.prompt
    # The judge nudge is the second action (keyed on the abstaining source).
    assert judge.skill == "bookwright-continuity"
    assert judge.reason.startswith("character_unknown_mentions abstained")


def test_both_move3_judge_nudges_co_fire_in_table_order() -> None:
    # Contract C7 (iteration 052): a report carrying BOTH `(character_unknown_mentions,
    # pending_capability)` AND `(focalization, pending_capability)` emits BOTH judge
    # actions — the undeclared-character nudge then the head-hopping nudge, in table
    # order — each a distinct, coherent `bookwright-continuity` action. No
    # `activate_dormant_validators` fires (both entries are `pending_capability`).
    state = make_state(not_evaluated=(_DORMANT_CAP, _DORMANT_FOCAL_CAP))
    actions = next_actions(state)
    assert [a.skill for a in actions] == ["bookwright-continuity", "bookwright-continuity"]
    undeclared, head_hop = actions
    assert undeclared.reason.startswith("character_unknown_mentions abstained")
    assert head_hop.reason.startswith("focalization abstained on head-hopping")
    assert undeclared.prompt != head_hop.prompt  # distinct, not merged (FR-011)
    assert all(not a.prompt.startswith("Activate the dormant validators") for a in actions)


def test_activation_sits_between_continuity_and_focus() -> None:
    state = make_state(errors=1, not_evaluated=(_DORMANT_FOCAL,), focus_defined=False)
    actions = next_actions(state)
    reasons = [a.reason for a in actions]
    assert reasons == [
        "1 validation error",  # review_continuity
        "1 validator could not evaluate",  # activate_dormant_validators
        "no authored focus is defined",  # define_focus
    ]
