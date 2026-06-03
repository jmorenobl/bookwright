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

from bookwright.validation.base import Severity, ValidatorError, Violation, split_source

if TYPE_CHECKING:
    from rich.console import Console

__all__ = ["ScopeFilter", "ValidationReport"]


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
    """A full run: all (deduped, pre-filter) violations, run/load errors, run names."""

    violations: tuple[Violation, ...]
    errors: tuple[ValidatorError, ...]
    ran: tuple[str, ...]

    @property
    def failed(self) -> bool:
        """The gate: any violation at ``error`` severity, ignoring filters (FR-013)."""
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
        """Render the human report (grouped by validator) to ``console`` (FR-012)."""
        reported = self.reported(scope=scope, severity=severity)
        if not reported and not self.errors:
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
        if self.errors:
            console.print("validator errors:", markup=False)
            for error in self.errors:
                console.print(f"  {error.phase}: {error.validator}: {error.message}", markup=False)
