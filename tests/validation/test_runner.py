"""Runner — per-validator isolation (FR-014) + dedup of identical violations (D13.1).

Also covers the tri-valued signal path (iteration 040, FR-005/FR-013/FR-014): a
``NotEvaluated`` raise lands in the ``not_evaluated`` channel (never ``errors[]``); a
generic crash still lands in ``errors[]``; a bare-list validator stays evaluated.
"""

from __future__ import annotations

from pathlib import Path

from bookwright.indexers import Indexer, RdflibIndexer
from bookwright.validation.base import (
    Abstention,
    EvalResult,
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


class _Partial:
    """A synthetic form-(c) validator: one finding AND one abstention in the same run.

    Mirrors _Good/_Skip/_SkipCapability but returns the partial EvalResult shape, so the
    runner's three-shape contract is proven decoupled from `focalization` (FR-015).
    """

    name = "partial"
    severity_default = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> EvalResult:
        return EvalResult(
            [Violation("partial", Severity.warning, "partial finding", "manuscript/c.md:3")],
            [Abstention("partial abstains on one dimension", NotEvaluatedKind.pending_capability)],
        )


class _PartialEmpty:
    """A form-(c) validator with NO findings — the C5 observational-equivalence case."""

    name = "partial_empty"
    severity_default = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> EvalResult:
        return EvalResult([], [Abstention("nothing to look at")])


class _SkipEmptyTwin:
    """The raise-form twin of _PartialEmpty: same (reason) → must be wire-identical (C5)."""

    name = "partial_empty"
    severity_default = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        raise NotEvaluated("nothing to look at")


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


def test_partial_eval_result_routes_findings_and_abstention(project_root: Path) -> None:
    # FR-015/SC-008 (iteration 050): a form-(c) EvalResult routes its findings to
    # violations[] (deduped against `seen`, sorted by sort_key) and its abstention to
    # not_evaluated[] as a runner-STAMPED NotEvaluatedResult; it appears in `ran` and in
    # NEITHER errors[] nor — for its finding — the abstention channel. Proven with a
    # synthetic fake, decoupled from `focalization` (the general contract, not one site).
    ctx = _ctx(project_root)
    violations, errors, not_evaluated, ran = run_validators([_Partial()], ctx, RdflibIndexer())

    assert [v.message for v in violations] == ["partial finding"]  # finding → violations[]
    assert errors == []  # form (c) is not a crash
    assert len(not_evaluated) == 1
    entry = not_evaluated[0]
    assert entry.validator == "partial"  # runner-STAMPED, not self-named (C2)
    assert entry.reason == "partial abstains on one dimension"
    assert entry.kind is NotEvaluatedKind.pending_capability
    assert ran == ["partial"]


def test_partial_finding_is_deduped_against_seen(project_root: Path) -> None:
    # The form-(c) findings flow into the SAME shared dedup loop (C4): the identical
    # finding emitted by a bare-list validator AND the partial validator collapses to one.
    class _PartialDup:
        name = "dupv"
        severity_default = Severity.warning

        def validate(self, project: ValidationContext, indexer: Indexer) -> EvalResult:
            v = Violation("dupv", Severity.warning, "shared", "manuscript/c.md:9")
            return EvalResult([v], [Abstention("half", NotEvaluatedKind.pending_capability)])

    class _BareDup:
        name = "dupv"
        severity_default = Severity.warning

        def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
            return [Violation("dupv", Severity.warning, "shared", "manuscript/c.md:9")]

    ctx = _ctx(project_root)
    violations, _, _, _ = run_validators([_PartialDup(), _BareDup()], ctx, RdflibIndexer())
    assert len([v for v in violations if v.message == "shared"]) == 1  # one, not two


class _PartialCoded:
    """A form-(c) validator whose abstention carries a `code` discriminator (iter 053)."""

    name = "coded"
    severity_default = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> EvalResult:
        return EvalResult(
            [],
            [Abstention("coded gap", NotEvaluatedKind.pending_capability, code="some_code")],
        )


def test_runner_stamps_code_from_form_c_and_none_from_form_b(project_root: Path) -> None:
    # FR-003/FR-004/FR-005 (contract C2/C3): the runner stamps the returned abstention's
    # `code` (form (c)); a raised NotEvaluated has no code, so the recorded result is
    # `code=None` (form (b)). Every recorded entry carries the `code` attribute + JSON key.
    ctx = _ctx(project_root)
    _, _, not_evaluated, _ = run_validators([_PartialCoded(), _Skip()], ctx, RdflibIndexer())
    codes = {r.validator: r.code for r in not_evaluated}
    assert codes["coded"] == "some_code"  # stamped from the returned Abstention
    assert codes["skip"] is None  # raised path is code-less
    for entry in not_evaluated:
        payload = entry.to_json()
        assert "code" in payload  # additive key present on EVERY entry (FR-005)


def test_empty_partial_is_observationally_equal_to_raise(project_root: Path) -> None:
    # C5 invariant (FR-012): `EvalResult([], [Abstention(r, k)])` is indistinguishable on
    # the wire from `raise NotEvaluated(r, k)` — both yield ONE not_evaluated entry and
    # ZERO findings, with the same runner-stamped validator/reason/kind.
    ctx = _ctx(project_root)
    via_return = run_validators([_PartialEmpty()], ctx, RdflibIndexer())
    via_raise = run_validators([_SkipEmptyTwin()], ctx, RdflibIndexer())
    assert via_return[0] == via_raise[0] == []  # violations: none either way
    assert via_return[2] == via_raise[2]  # not_evaluated: byte-identical NotEvaluatedResult
    assert [r.to_json() for r in via_return[2]] == [r.to_json() for r in via_raise[2]]
