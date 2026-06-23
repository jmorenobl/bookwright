"""Runner — per-validator isolation (FR-014) + dedup of identical violations (D13.1).

Also covers the tri-valued signal path (iteration 040, FR-005/FR-013/FR-014): a
``NotEvaluated`` raise lands in the ``not_evaluated`` channel (never ``errors[]``); a
generic crash still lands in ``errors[]``; a bare-list validator stays evaluated.
"""

from __future__ import annotations

from pathlib import Path

from bookwright.indexers import Indexer, RdflibIndexer
from bookwright.validation.base import (
    NotEvaluated,
    NotEvaluatedKind,
    Severity,
    ValidationContext,
    Violation,
)
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


class _Skip:
    name = "skip"
    severity_default = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        raise NotEvaluated("nothing to look at")


class _SkipZ:
    name = "zskip"
    severity_default = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        raise NotEvaluated("also nothing")


class _SkipCapability:
    name = "abstainer"
    severity_default = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        raise NotEvaluated("awaits move 3", kind=NotEvaluatedKind.pending_capability)


def _ctx(project_root: Path) -> ValidationContext:
    write_project(project_root, characters=["A"], manuscript={"c.md": "A"})
    return load_context(project_root)


def test_raising_validator_is_isolated(project_root: Path) -> None:
    ctx = _ctx(project_root)
    violations, errors, not_evaluated, ran = run_validators(
        [_Boom(), _Good()], ctx, RdflibIndexer()
    )

    assert [v.message for v in violations] == ["ok finding"]  # the good one still ran
    assert len(errors) == 1
    assert errors[0].validator == "boom"
    assert errors[0].phase == "run"
    assert "kaboom" in errors[0].message
    assert not_evaluated == []  # a crash is NOT a conscious skip (FR-005)
    assert ran == ["boom", "good"]  # both invoked, sorted


def test_identical_violations_are_deduped(project_root: Path) -> None:
    ctx = _ctx(project_root)
    violations, errors, not_evaluated, ran = run_validators([_Duplicator()], ctx, RdflibIndexer())
    assert len(violations) == 1
    assert errors == []
    assert not_evaluated == []
    assert ran == ["dup"]


def test_output_is_deterministically_sorted(project_root: Path) -> None:
    ctx = _ctx(project_root)
    a, _, _, _ = run_validators([_Good(), _Duplicator()], ctx, RdflibIndexer())
    b, _, _, _ = run_validators([_Duplicator(), _Good()], ctx, RdflibIndexer())
    # Same inputs (regardless of validator order) → byte-identical ordering (SC-003).
    assert [v.to_json() for v in a] == [v.to_json() for v in b]


def test_not_evaluated_is_routed_to_its_own_channel(project_root: Path) -> None:
    # A NotEvaluated raise → not_evaluated[], NOT errors[] (FR-005).
    ctx = _ctx(project_root)
    violations, errors, not_evaluated, ran = run_validators([_Skip()], ctx, RdflibIndexer())
    assert violations == []
    assert errors == []  # not a crash
    assert [(r.validator, r.reason) for r in not_evaluated] == [("skip", "nothing to look at")]
    assert ran == ["skip"]


def test_bare_list_validator_is_evaluated(project_root: Path) -> None:
    # A custom validator returning a non-empty bare list is EVALUATED: its findings
    # flow into violations[] and it appears in NEITHER errors[] NOR not_evaluated[]
    # (FR-014 backward-compat, explicit).
    ctx = _ctx(project_root)
    violations, errors, not_evaluated, ran = run_validators([_Good()], ctx, RdflibIndexer())
    assert [v.message for v in violations] == ["ok finding"]
    assert errors == []
    assert not_evaluated == []
    assert ran == ["good"]


def test_not_evaluated_is_sorted_and_deduped(project_root: Path) -> None:
    # Sorted by validator name; each validator appears at most once (FR-013).
    ctx = _ctx(project_root)
    _, _, not_evaluated, ran = run_validators([_SkipZ(), _Skip()], ctx, RdflibIndexer())
    assert [r.validator for r in not_evaluated] == ["skip", "zskip"]  # sorted, not run order
    assert ran == ["skip", "zskip"]


def test_runner_stamps_kind_from_the_signal(project_root: Path) -> None:
    # The runner stamps each raise's kind onto the recorded result: a capability-gap
    # raise carries pending_capability; a default raise stays missing_input (D3).
    ctx = _ctx(project_root)
    _, _, not_evaluated, _ = run_validators([_SkipCapability(), _Skip()], ctx, RdflibIndexer())
    kinds = {r.validator: r.kind for r in not_evaluated}
    assert kinds["abstainer"] is NotEvaluatedKind.pending_capability
    assert kinds["skip"] is NotEvaluatedKind.missing_input  # default preserved
