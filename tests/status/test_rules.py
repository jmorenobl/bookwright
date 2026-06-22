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
from bookwright.status.rules import RULES, next_actions
from bookwright.validation.base import NotEvaluatedResult

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

#: One synthetic state per rule, exercising exactly it (SC-005).
_TRIGGER: dict[str, StatusState] = {
    "bootstrap_graph": make_state(graph=GraphFacts(available=False, entities=0, triples=0)),
    "research_queue": make_state(open_questions=(_QUESTION,)),
    "verify_findings": make_state(low_reliability_findings=(_LOW,)),
    "review_continuity": make_state(errors=2),
    "activate_dormant_validators": make_state(not_evaluated=(_DORMANT_FOCAL,)),
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


def test_activation_sits_between_continuity_and_focus() -> None:
    state = make_state(errors=1, not_evaluated=(_DORMANT_FOCAL,), focus_defined=False)
    actions = next_actions(state)
    reasons = [a.reason for a in actions]
    assert reasons == [
        "1 validation error",  # review_continuity
        "1 validator could not evaluate",  # activate_dormant_validators
        "no authored focus is defined",  # define_focus
    ]
