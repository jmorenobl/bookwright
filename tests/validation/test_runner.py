"""Runner — per-validator isolation (FR-014) + dedup of identical violations (D13.1)."""

from __future__ import annotations

from pathlib import Path

from bookwright.indexers import Indexer, RdflibIndexer
from bookwright.validation.base import Severity, ValidationContext, Violation
from bookwright.validation.runner import run_validators
from tests.validation.conftest import load_context, write_project


class _Boom:
    name = "boom"
    severity_default = Severity.error

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        raise RuntimeError("kaboom")


class _Good:
    name = "good"
    severity_default = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        return [Violation("good", Severity.warning, "ok finding", "manuscript/c.md:1")]


class _Duplicator:
    name = "dup"
    severity_default = Severity.info

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        v = Violation("dup", Severity.info, "same", "manuscript/c.md:2")
        return [v, v, v]


def _ctx(project_root: Path) -> ValidationContext:
    write_project(project_root, characters=["A"], manuscript={"c.md": "A"})
    return load_context(project_root)


def test_raising_validator_is_isolated(project_root: Path) -> None:
    ctx = _ctx(project_root)
    violations, errors, ran = run_validators([_Boom(), _Good()], ctx, RdflibIndexer())

    assert [v.message for v in violations] == ["ok finding"]  # the good one still ran
    assert len(errors) == 1
    assert errors[0].validator == "boom"
    assert errors[0].phase == "run"
    assert "kaboom" in errors[0].message
    assert ran == ["boom", "good"]  # both invoked, sorted


def test_identical_violations_are_deduped(project_root: Path) -> None:
    ctx = _ctx(project_root)
    violations, errors, ran = run_validators([_Duplicator()], ctx, RdflibIndexer())
    assert len(violations) == 1
    assert errors == []
    assert ran == ["dup"]


def test_output_is_deterministically_sorted(project_root: Path) -> None:
    ctx = _ctx(project_root)
    a, _, _ = run_validators([_Good(), _Duplicator()], ctx, RdflibIndexer())
    b, _, _ = run_validators([_Duplicator(), _Good()], ctx, RdflibIndexer())
    # Same inputs (regardless of validator order) → byte-identical ordering (SC-003).
    assert [v.to_json() for v in a] == [v.to_json() for v in b]
