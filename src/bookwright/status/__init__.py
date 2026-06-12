"""Derived-state domain logic for ``bookwright status`` (design § 21.4-21.6).

Mirrors how :mod:`bookwright.validation` separates reasoning from its CLI verb:
the state model (:mod:`.model`), the graph aggregations (:mod:`.queries`), and
the pure rule table (:mod:`.rules`) live here so they are importable and
unit-testable with zero CLI or graph coupling; ``commands/status.py`` only
orchestrates.
"""

from bookwright.status.model import (
    AnchorGap,
    GraphFacts,
    LowReliabilityFinding,
    OpenQuestion,
    StatusState,
    ValidationSummary,
)
from bookwright.status.queries import (
    anchor_gaps,
    low_reliability_findings,
    open_questions,
    validation_summary,
)
from bookwright.status.rules import RULES, Action, Rule, next_actions

__all__ = [
    "RULES",
    "Action",
    "AnchorGap",
    "GraphFacts",
    "LowReliabilityFinding",
    "OpenQuestion",
    "Rule",
    "StatusState",
    "ValidationSummary",
    "anchor_gaps",
    "low_reliability_findings",
    "next_actions",
    "open_questions",
    "validation_summary",
]
