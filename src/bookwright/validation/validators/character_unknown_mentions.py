"""``character_unknown_mentions`` — the open-set proper-noun rule, made honest.

This validator is a **pure abstainer**. The old deterministic heuristic — "is every
capitalized proper-noun candidate in some bible roster?" — is the NER problem without
NER: an open-set discovery a capitalization rule cannot do soundly. The second dogfood
(`sombra-en-el-puerto`, 2026-06-23) measured it as 100 % noise on real prose, so per
issue #1 (track A — honestidad) the rule **stops pretending**: instead of emitting a
``warning`` it raises :class:`NotEvaluated`, surfacing through the iteration-040
``not_evaluated[]`` channel.

It abstains by *approach*, not by *input* — no project state can make the deterministic
heuristic reliable — so :meth:`validate` abstains **unconditionally**, reading nothing.
The honest signal it can never deliver is the job of move 3 (LLM semantic judgment); see
``bookwright-design.md`` § 13.5.

It abstains via the **returned** partial-evaluation shape (form (c), ``EvalResult`` with
no findings and one :class:`Abstention`) rather than a raised total abstention (form (b)),
so it can carry the ``code="undeclared_characters"`` discriminator (iteration 053): the
raised path cannot carry a ``code``, and the ``status`` ``judge_undeclared_characters``
nudge now keys on ``(validator, code)``. The wire shape is observationally identical to
the old raise except for the additive ``code`` key (``null`` → ``"undeclared_characters"``);
``reason``, ``kind``, and the sort position are unchanged (contract C5).
"""

from __future__ import annotations

from typing import ClassVar

from bookwright.indexers import Indexer
from bookwright.validation.base import (
    Abstention,
    EvalResult,
    NotEvaluatedKind,
    Severity,
    ValidationContext,
)


class CharacterUnknownMentions:
    """Open-set proper-noun discovery — declared not-evaluated pending move 3."""

    name: ClassVar[str] = "character_unknown_mentions"
    severity_default: ClassVar[Severity] = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> EvalResult:
        return EvalResult(
            [],
            [
                Abstention(
                    "open-set proper-noun discovery requires semantic judgment (move 3); "
                    "the deterministic heuristic was measured insufficient on real prose",
                    kind=NotEvaluatedKind.pending_capability,
                    code="undeclared_characters",
                )
            ],
        )
