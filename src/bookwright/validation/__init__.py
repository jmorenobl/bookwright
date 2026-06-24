"""Validation subsystem: deterministic coherence checks + the ``validate`` command.

The public surface a custom validator imports (``Severity``, ``Violation``) and the
engine seam the command wires together (discovery, the runner, the report).
"""

from __future__ import annotations

from bookwright.validation.base import (
    Abstention,
    EvalResult,
    NotEvaluated,
    NotEvaluatedResult,
    Severity,
    UnknownValidatorError,
    ValidationContext,
    Validator,
    ValidatorError,
    Violation,
)
from bookwright.validation.registry import discover_validators, resolve_active
from bookwright.validation.report import ScopeFilter, ValidationReport
from bookwright.validation.runner import run_validators

__all__ = [
    "Abstention",
    "EvalResult",
    "NotEvaluated",
    "NotEvaluatedResult",
    "ScopeFilter",
    "Severity",
    "UnknownValidatorError",
    "ValidationContext",
    "ValidationReport",
    "Validator",
    "ValidatorError",
    "Violation",
    "discover_validators",
    "resolve_active",
    "run_validators",
]
