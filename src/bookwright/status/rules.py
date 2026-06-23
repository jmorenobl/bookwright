"""The static rule table mapping :class:`StatusState` to ``next_actions`` (020 D7).

A pure ``state → list[Action]`` function: no I/O, no graph, no clock — only the
already-aggregated facts. ``RULES`` is a module-level tuple whose **order is the
priority order** (FR-010); every prompt is a fixed English template (FR-008,
clarification #2) parameterized only by state facts, so the same state always
yields byte-identical actions (SC-002) and every rule is exercisable from a
synthetic state with nothing on disk (SC-005).

The degraded state short-circuits (research D5): with no graph to reason over,
recommending research/verification/continuity/focus work would be noise — the
single bootstrap action is the whole answer.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bookwright.validation.base import NotEvaluatedKind

if TYPE_CHECKING:
    from bookwright.status.model import StatusState

__all__ = ["RULES", "Action", "Rule", "next_actions"]


@dataclass(frozen=True)
class Action:
    """One recommendation: a skill to invoke, a paste-ready prompt, and why (SC-004)."""

    skill: str
    prompt: str
    reason: str

    def to_payload(self) -> dict[str, str]:
        return {"skill": self.skill, "prompt": self.prompt, "reason": self.reason}


@dataclass(frozen=True)
class Rule:
    """One row of the table: a stable name, a pure predicate, a pure builder."""

    name: str
    applies: Callable[[StatusState], bool]
    build: Callable[[StatusState], Action]


def _plural(count: int, noun: str) -> str:
    """``1 open question`` / ``2 open questions`` — fixed English, count-driven."""
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _bootstrap_graph(_state: StatusState) -> Action:
    return Action(
        skill="bookwright-bible",
        prompt=(
            "Author the story bible for this project (characters, settings, "
            "timeline), then run `bookwright graph build` to index it."
        ),
        reason="the knowledge graph has no entities to reason over yet",
    )


def _research_queue(state: StatusState) -> Action:
    questions = "; ".join(
        f"{q.id}: {q.text}" if q.text is not None else q.id for q in state.open_questions
    )
    anchors = "; ".join(
        f"{gap.promotes} -> {gap.constrains}" if gap.constrains is not None else gap.promotes
        for gap in state.unresolved_anchors
    )
    parts = ["Work through the research queue."]
    if questions:
        parts.append(f"Open questions: {questions}.")
    if anchors:
        parts.append(f"Anchors needing support: {anchors}.")
    parts.append("Record each finding with its sources under bible/research/.")
    return Action(
        skill="bookwright-research",
        prompt=" ".join(parts),
        reason=(
            f"{_plural(len(state.open_questions), 'open research question')} and "
            f"{_plural(len(state.unresolved_anchors), 'unresolved anchor')}"
        ),
    )


def _verify_findings(state: StatusState) -> Action:
    findings = "; ".join(
        f"{f.id} (best support: {f.best_reliability})"
        if f.best_reliability is not None
        else f"{f.id} (unrated)"
        for f in state.low_reliability_findings
    )
    return Action(
        skill="bookwright-verify",
        prompt=(
            f"Verify the findings whose support is below the project threshold: "
            f"{findings}. Strengthen each with more reliable sources or revise its claim."
        ),
        reason=(
            f"{_plural(len(state.low_reliability_findings), 'finding')} "
            "with low-reliability support"
        ),
    )


def _review_continuity(state: StatusState) -> Action:
    return Action(
        skill="bookwright-continuity",
        prompt=(
            "Review the continuity errors in the bible and manuscript; run "
            "`bookwright validate` for the detailed report, then fix each error "
            "at its source file."
        ),
        reason=_plural(state.validation.counts.get("error", 0), "validation error"),
    )


#: Concrete remedy clause per validator that can fall dormant (iteration 040, SC-004).
#: A validator absent here (e.g. a custom one) falls back to ``_GENERIC_REMEDY`` so it
#: still appears in the prompt — the migrated set all map.
_REMEDIES: dict[str, str] = {
    "focalization": "declare the narrative voice in the constitution",
    "setting_continuity": "add manuscript prose to validate",
    "character_presence": "add a bible character roster and manuscript prose",
}

#: Fallback clause for a dormant validator with no concrete remedy in ``_REMEDIES``.
_GENERIC_REMEDY = "investigate why it could not evaluate"


def _activate_dormant_validators(state: StatusState) -> Action:
    # Only input-conditional gaps are actionable (iteration 044, FR-005): a
    # `pending_capability` entry is a permanent capability-gap with no manual remedy,
    # so it is filtered out here and never nudged. Still sorted by validator name.
    dormant = [
        r for r in state.validation.not_evaluated if r.kind is NotEvaluatedKind.missing_input
    ]
    # One clause per dormant validator so the prompt always covers EVERY validator the
    # `reason` count names — no validator is silently dropped (mapped → its remedy,
    # unmapped → the generic clause).
    clauses = "; ".join(
        f"{r.validator} — {_REMEDIES.get(r.validator, _GENERIC_REMEDY)}" for r in dormant
    )
    return Action(
        skill="bookwright-continuity",
        prompt=f"Activate the dormant validators: {clauses}.",
        reason=f"{_plural(len(dormant), 'validator')} could not evaluate",
    )


def _define_focus(_state: StatusState) -> Action:
    return Action(
        skill="bookwright focus set",
        prompt=(
            "Define the current working focus: run `bookwright focus set "
            '--target "<what you are working on>" --notes "<why>"`.'
        ),
        reason="no authored focus is defined",
    )


#: The table. Tuple order IS the priority order (FR-010, data-model § 3.2).
RULES: tuple[Rule, ...] = (
    Rule(
        name="bootstrap_graph",
        applies=lambda s: not s.graph.available or s.graph.entities == 0,
        build=_bootstrap_graph,
    ),
    Rule(
        name="research_queue",
        applies=lambda s: bool(s.open_questions or s.unresolved_anchors),
        build=_research_queue,
    ),
    Rule(
        name="verify_findings",
        applies=lambda s: bool(s.low_reliability_findings),
        build=_verify_findings,
    ),
    Rule(
        name="review_continuity",
        applies=lambda s: s.validation.counts.get("error", 0) > 0,
        build=_review_continuity,
    ),
    Rule(
        name="activate_dormant_validators",
        applies=lambda s: any(
            r.kind is NotEvaluatedKind.missing_input for r in s.validation.not_evaluated
        ),
        build=_activate_dormant_validators,
    ),
    Rule(
        name="define_focus",
        applies=lambda s: not s.focus_defined,
        build=_define_focus,
    ),
)


def next_actions(state: StatusState) -> list[Action]:
    """The ordered recommendations for ``state`` (FR-008..FR-010).

    Walks :data:`RULES` in table order; the bootstrap rule short-circuits to a
    single action (research D5). An empty list is a healthy, focused project's
    valid answer — never padded.
    """
    actions: list[Action] = []
    for rule in RULES:
        if not rule.applies(state):
            continue
        action = rule.build(state)
        if rule.name == "bootstrap_graph":
            return [action]  # D5: a degraded graph suppresses every other rule
        actions.append(action)
    return actions
