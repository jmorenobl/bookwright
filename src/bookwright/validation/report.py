"""``ValidationReport`` — aggregation, the CI gate, filtering, and rendering.

The gate (:attr:`failed`) is computed from **all** violations before any filter, so a
display ``--scope`` / ``--severity`` can never hide an error from CI (FR-013). The
emitted order is fixed by the runner's total-order sort; ``reported`` only removes
entries, never reorders — so the human report and the JSON ``violations[]`` are
byte-identical across runs (SC-003).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from bookwright.validation.base import (
    NotEvaluatedKind,
    NotEvaluatedResult,
    Severity,
    ValidatorError,
    Violation,
    split_source,
)

if TYPE_CHECKING:
    from rich.console import Console

__all__ = ["ScopeFilter", "ValidationReport"]

#: Kind-generic human tag for a not-evaluated entry (iteration 044, FR-007). Generic to
#: the KIND, never a validator's specifics — the validator-specific "move 3" detail stays
#: in the unchanged ``reason``. ``missing_input`` reads as something the author can fix;
#: ``pending_capability`` reads as a non-actionable known limitation.
_KIND_LABEL: dict[NotEvaluatedKind, str] = {
    NotEvaluatedKind.missing_input: "input gap",
    NotEvaluatedKind.pending_capability: "known limitation — no action available yet",
}


@dataclass(frozen=True)
class ScopeFilter:
    """Limits reported findings to a file or directory under the project root."""

    rel: str  # project-relative posix path of the scope
    is_dir: bool

    def matches(self, source: str | None) -> bool:
        """Whether ``source`` falls within the scope. ``None`` never matches (FR-009)."""
        if source is None:
            return False
        path = split_source(source)[0] or source
        if self.is_dir:
            return path == self.rel or path.startswith(f"{self.rel}/")
        return path == self.rel


@dataclass
class ValidationReport:
    """A full run: all (deduped, pre-filter) violations, run/load errors, run names.

    A run is **green/clean** iff ``status == "ok"`` AND no ``not_evaluated`` entry has
    ``kind == "missing_input"`` — the single documented predicate, refined by kind in
    iteration 044 (SC-002). A ``pending_capability`` entry stays listed but does **not**
    deny green (FR-004): it is a permanent capability-gap identical in every project,
    not an actionable per-project gap. ``not_evaluated`` is the additive third state (a
    validator that consciously did not look); it never gates (FR-004) and is a channel
    distinct from ``errors`` (which is for validators that crashed, FR-005).
    """

    violations: tuple[Violation, ...]
    errors: tuple[ValidatorError, ...]
    ran: tuple[str, ...]
    not_evaluated: tuple[NotEvaluatedResult, ...] = ()

    @property
    def failed(self) -> bool:
        """The gate: any violation at ``error`` severity, ignoring filters (FR-013).

        ``not_evaluated`` never affects the gate (FR-004) — it is not a finding.
        """
        return any(v.severity == Severity.error for v in self.violations)

    def reported(self, *, scope: ScopeFilter | None, severity: Severity | None) -> list[Violation]:
        """Apply ``scope`` then the ``severity`` threshold, preserving order (D8)."""
        result: list[Violation] = []
        for violation in self.violations:
            if scope is not None and not scope.matches(violation.source):
                continue
            if severity is not None and not violation.severity.at_least(severity):
                continue
            result.append(violation)
        return result

    def to_json(self, *, scope: ScopeFilter | None, severity: Severity | None) -> dict[str, Any]:
        """The Principle-IX envelope (data-model / contracts/cli-validate.md)."""
        reported = self.reported(scope=scope, severity=severity)
        return {
            "status": "violations" if reported else "ok",
            "failed": self.failed,
            "violations": [v.to_json() for v in reported],
            "errors": [e.to_json() for e in self.errors],
            "not_evaluated": [r.to_json() for r in self.not_evaluated],
            "summary": {
                "ran": list(self.ran),
                "total": len(self.violations),
                "reported": len(reported),
                "by_severity": self._by_severity(),
            },
        }

    def _by_severity(self) -> dict[str, int]:
        """Counts over the unfiltered set; always all three keys, ``0`` when absent."""
        counts = {level.value: 0 for level in Severity}
        for violation in self.violations:
            counts[violation.severity.value] += 1
        return counts

    def render(
        self, console: Console, *, scope: ScopeFilter | None, severity: Severity | None
    ) -> None:
        """Render the human report (grouped by validator) to ``console`` (FR-012).

        The "no violations found" clean line prints **only** when there are no reported
        violations, no errors, AND no not-evaluated validators — so a run that is solely
        not-evaluated shows the ``not evaluated:`` section instead of reading as clean
        (SC-002). ``not_evaluated`` is unfiltered by ``--scope`` / ``--severity`` (it
        carries no location and no severity).
        """
        reported = self.reported(scope=scope, severity=severity)
        if not reported and not self.errors and not self.not_evaluated:
            console.print("no violations found", markup=False)
            return
        for validator in sorted({v.validator for v in reported}):
            console.print(f"{validator}:", markup=False)
            for violation in [v for v in reported if v.validator == validator]:
                location = violation.source or "(no specific location)"
                console.print(
                    f"  {violation.severity.value}: {violation.message} — {location}",
                    markup=False,
                )
        if self.not_evaluated:
            console.print("not evaluated:", markup=False)
            for result in self.not_evaluated:
                console.print(
                    f"  {result.validator} [{_KIND_LABEL[result.kind]}]: {result.reason}",
                    markup=False,
                )
        if self.errors:
            console.print("validator errors:", markup=False)
            for error in self.errors:
                console.print(f"  {error.phase}: {error.validator}: {error.message}", markup=False)
