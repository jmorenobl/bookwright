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
    EvalResult,
    NotEvaluated,
    NotEvaluatedKind,
    NotEvaluatedResult,
    ValidationContext,
    Validator,
    ValidatorError,
    Violation,
)

__all__ = ["RunResult", "not_evaluated_sort_key", "run_validators", "sort_key"]

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


def _record(name: str, reason: str, kind: NotEvaluatedKind) -> NotEvaluatedResult:
    """Stamp the validator ``name`` onto one abstention (the single naming authority).

    The ONE place a ``not_evaluated`` entry is name-stamped — shared by BOTH the raised
    total abstention (form (b), ``except NotEvaluated``) and each returned partial
    abstention (form (c), an ``EvalResult``'s :class:`Abstention`). The validator never
    names itself; this authority MUST NOT fork (FR-002, contract C2).
    """
    return NotEvaluatedResult(name, reason, kind)


def not_evaluated_sort_key(result: NotEvaluatedResult) -> tuple[str, str]:
    """Total order for ``not_evaluated[]`` (FR-009): ``(validator, reason)``.

    A total order, not the old partial ``validator``-only key: ingestion-skip entries
    (iteration 046) all share ``validator="ingestion"``, so the ``reason`` tie-break
    (paths are unique) is what keeps multi-skip runs byte-identical. The single shared
    definition both the runner and the ``validate`` skip-merge import — no duplicated
    sort literal to drift. Skip-free runs are unaffected (validator names are already
    unique, so no tie exists — FR-010).
    """
    return (result.validator, result.reason)


def run_validators(
    active: list[Validator], project: ValidationContext, indexer: Indexer
) -> RunResult:
    """Run every validator in ``active``, isolating failures (FR-014).

    Collects each validator's ``Violation`` list, deduplicates identical findings
    across the whole run (D8), and returns them sorted by :func:`sort_key`. A
    validator that raises :class:`NotEvaluated` contributes a ``NotEvaluatedResult``
    (and no findings) to the ``not_evaluated`` channel; any other exception
    contributes a ``ValidatorError(phase="run")`` (FR-005). The rest still run.
    ``not_evaluated`` is sorted by the total order :func:`not_evaluated_sort_key`
    (``(validator, reason)``, FR-009); ``ran`` lists every invoked validator name,
    sorted.
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
        except NotEvaluated as skip:  # form (b): total abstention → not_evaluated (FR-005)
            not_evaluated.append(_record(validator.name, skip.reason, skip.kind))
            continue
        except Exception as exc:  # per-validator isolation (FR-014) — never abort the run
            errors.append(ValidatorError(validator.name, f"{type(exc).__name__}: {exc}", "run"))
            continue
        if isinstance(found, EvalResult):  # form (c): findings AND abstention(s) in one run
            findings: list[Violation] = found.violations
            for abstention in found.not_evaluated:
                not_evaluated.append(_record(validator.name, abstention.reason, abstention.kind))
        else:  # form (a): a bare list[Violation] — unchanged (FR-007)
            findings = found
        for violation in findings:
            if violation not in seen:
                seen.add(violation)
                violations.append(violation)

    violations.sort(key=sort_key)
    not_evaluated.sort(key=not_evaluated_sort_key)
    return violations, errors, not_evaluated, sorted(ran)
