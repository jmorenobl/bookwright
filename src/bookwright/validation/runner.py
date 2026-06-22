"""Run the active validators with per-validator isolation (FR-014, D8/D9).

A validator that raises is caught and recorded as a ``ValidatorError(phase="run")``
without aborting the others (FR-014). Identical findings are deduped and the
combined set is sorted by an explicit total-order key so the emitted list is
byte-identical across runs and platforms (SC-003), not merely "stably sorted".
"""

from __future__ import annotations

from bookwright.indexers import Indexer
from bookwright.validation.base import (
    _RANK,
    NotEvaluated,
    NotEvaluatedResult,
    ValidationContext,
    Validator,
    ValidatorError,
    Violation,
)

__all__ = ["RunResult", "run_validators", "sort_key"]

RunResult = tuple[
    list[Violation],
    list[ValidatorError],
    list[NotEvaluatedResult],
    list[str],
]
"""``(violations, errors, not_evaluated, ran)`` — findings, run errors, conscious
skips (sorted by validator name), run names."""


def sort_key(violation: Violation) -> tuple[str, int, str, str, tuple[tuple[str, str, str], ...]]:
    """The explicit total order (D8): validator, severity desc, source, message, triples."""
    return (
        violation.validator,
        -_RANK[violation.severity],
        violation.source or "",
        violation.message,
        violation.triples,
    )


def run_validators(
    active: list[Validator], project: ValidationContext, indexer: Indexer
) -> RunResult:
    """Run every validator in ``active``, isolating failures (FR-014).

    Collects each validator's ``Violation`` list, deduplicates identical findings
    across the whole run (D8), and returns them sorted by :func:`sort_key`. A
    validator that raises :class:`NotEvaluated` contributes a ``NotEvaluatedResult``
    (and no findings) to the ``not_evaluated`` channel; any other exception
    contributes a ``ValidatorError(phase="run")`` (FR-005). The rest still run.
    ``not_evaluated`` is sorted by validator name (FR-013); ``ran`` lists every
    invoked validator name, sorted.
    """
    seen: set[Violation] = set()
    violations: list[Violation] = []
    errors: list[ValidatorError] = []
    not_evaluated: list[NotEvaluatedResult] = []
    ran: list[str] = []

    for validator in active:
        ran.append(validator.name)
        try:
            found = validator.validate(project, indexer)
        except NotEvaluated as skip:  # conscious skip → not_evaluated channel (FR-005)
            not_evaluated.append(NotEvaluatedResult(validator.name, skip.reason))
            continue
        except Exception as exc:  # per-validator isolation (FR-014) — never abort the run
            errors.append(ValidatorError(validator.name, f"{type(exc).__name__}: {exc}", "run"))
            continue
        for violation in found:
            if violation not in seen:
                seen.add(violation)
                violations.append(violation)

    violations.sort(key=sort_key)
    not_evaluated.sort(key=lambda r: r.validator)
    return violations, errors, not_evaluated, sorted(ran)
