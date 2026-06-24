# Implementation Plan: a partial-evaluation contract — a validator may emit findings **and** abstain in the same run; `focalization` recovers its first-person-break check under limited-third

**Branch**: `050-partial-evaluation-contract` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/050-partial-evaluation-contract/spec.md`

## Summary

The validator contract is **all-or-nothing**: `validate()` either returns
`list[Violation]` (evaluated) or raises `NotEvaluated(reason, kind)` (a total
abstention). There is no way for a validator to deterministically check one
dimension **and** declare `not_evaluated` on another in the same run. Iteration
045 hit that wall: under a third-person-**limited/focalized** voice,
`focalization` `raise`s `NotEvaluated(pending_capability)` for head-hopping
**before** reaching `_first_person_breaks`, so the deterministic, high-precision
first-person-break check no longer runs for any focalized project — a real,
suite-invisible coverage regression (DEBT-019).

This iteration introduces a **general** partial-evaluation contract — a third
accepted return shape — and `focalization` is its first consumer.

- **Contract (`validation/base.py`)**: add a frozen `EvalResult(violations,
  not_evaluated)` carrier a validator MAY **return**, and a frozen `Abstention(reason,
  kind)` (the returned-not-raised sibling of `NotEvaluated`, carrying only
  `(reason, kind)` — the validator never names itself). Widen the `Validator`
  Protocol return to `list[Violation] | EvalResult`. Forms (a) `list[Violation]`
  and (b) `raise NotEvaluated` are untouched.
- **Runner (`validation/runner.py`)**: normalize **three** shapes through one
  single name-stamping point. The `except NotEvaluated` path and the `EvalResult`
  abstention loop both build `NotEvaluatedResult(validator.name, reason, kind)`
  via the **same** helper — the stamping authority does not fork (FR-002). Form
  (c)'s `violations` flow into the existing dedup+`sort_key` path; its abstentions
  merge into `not_evaluated[]` under `not_evaluated_sort_key`. The 4-tuple
  `RunResult` and both its consumers (`commands/validate.py`, `status/queries.py`)
  are unchanged.
- **`focalization` (`validators/focalization.py`)**: under `person == "third" and
  limited`, **return** `EvalResult(self._first_person_breaks(project.manuscript_view()),
  [Abstention(_HEAD_HOPPING_PENDING, NotEvaluatedKind.pending_capability)])` instead
  of raising. The four input-conditional `raise`s, the omniscient `list[Violation]`
  path, the first-person `[]` path, and `_first_person_breaks` itself are untouched.

The empty-`violations` `EvalResult` is observationally identical to a `raise
NotEvaluated` of the same `(reason, kind)`, so the three focalized fixtures stay
byte-identical (FR-012). No new dependency; stdlib only. Contract-before-code:
`bookwright-design.md` § 13.1 (the third return shape) and § 13.2/§ 13.5/§ 20.6.1
(focalization now runs the deterministic half **and** abstains on the semantic
half under limited-third) are updated before the code diverges; DEBT-019 is removed.

## Technical Context

**Language/Version**: Python 3.11+ (`StrEnum`, PEP 604 unions), `from __future__ import annotations`

**Primary Dependencies**: stdlib only for this change (`dataclasses`, `enum`,
`typing`). No new runtime dependency (Constitution II / FR-009).

**Storage**: N/A — the validation subsystem persists nothing (in-memory; design § 13.1).

**Testing**: `pytest` + `pytest-cov` (≥ 80% coverage, single-sourced in
`[tool.coverage.report]`); `mypy --strict` over `src` + `tests`; `ruff check` +
`ruff format --check`.

**Target Platform**: CLI (`bookwright validate`), cross-platform; deterministic,
byte-stable output (SC-003).

**Project Type**: Single project (src-layout `src/bookwright/`, `tests/` at root).

**Performance Goals**: N/A — no new pass; `_first_person_breaks` already runs the
same scan it always did, just reached via a new path.

**Constraints**: Every changed source file ≤ 500 lines (Principle IV); frozen
GOLEM ontology untouched (Principle X); `focalization` stays a prose validator
(`triples = ()`, no graph access — FR-008); `mypy --strict` clean across the
widened return union (FR-007).

**Scale/Scope**: ~3 source files (`validation/base.py`, `validation/runner.py`,
`validation/validators/focalization.py`) + the two validation test modules
(`tests/validation/test_runner.py`, `tests/validation/test_focalization.py`) +
docs (`bookwright-design.md`, `DEBT.md`) + the `CLAUDE.md` plan pointer. No other
validator, command, envelope, or ontology file changes (FR-016).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution **v1.4.0**. Relevant principles:

| Principle | Bearing on this iteration | Verdict |
|---|---|---|
| **I — plain-text source of truth** | The graph stays a derived cache; this change touches only the in-memory validator seam. DEBT and the contract live in plain text (`DEBT.md`, `bookwright-design.md`), updated **before** code (FR-010/FR-011). | ✅ PASS |
| **II — locked stack** | No new runtime dependency; `EvalResult`/`Abstention` are stdlib `@dataclass(frozen=True)`. | ✅ PASS |
| **IV — file size / one subcommand per module** | All changed files stay ≤ 500 lines (base.py 407 → ~440; runner.py 95 → ~115; focalization.py 159 → ~165). No CLI module touched. | ✅ PASS |
| **VIII — test discipline (NON-NEGOTIABLE)** | New runner-level form-(c) test (FR-015) + new focalization both-at-once test (FR-013) + retargeted limited-third tests (FR-014); ≥ 80% coverage held; the new runner branch is the heart of FR-001/FR-002 and is covered decoupled from `focalization`. | ✅ PASS |
| **IX — JSON-over-stdout / errors layering** | No envelope key added; `not_evaluated[]` and the `--json` contract are unchanged (form (c) routes into the **existing** channels). `NotEvaluated` stays a plain `Exception`, not a `BookwrightError`. | ✅ PASS |
| **X — frozen ontology** | No `.ttl` touched; `focalization` stays a prose validator with `triples = ()`. | ✅ PASS |

**Scope discipline**: the contract is **available, not mandated** — only
`focalization` adopts form (c). No "future X" plumbing: `EvalResult` exists
because `focalization` needs it **now** to recover a real check (DEBT-019). No
other total abstention is retrofitted (`character_unknown_mentions` stays total —
it has no deterministic half). **No violations to track.**

## Project Structure

### Documentation (this feature)

```text
specs/050-partial-evaluation-contract/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature spec (already present)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── validator-protocol.md   # Phase 1 — the three-shape validate() contract
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/validation/
├── base.py                    # + EvalResult, + Abstention; widen Validator.validate return
├── runner.py                  # normalize three shapes via one stamping point
└── validators/
    └── focalization.py        # limited-third: return EvalResult instead of raising

tests/validation/
├── test_runner.py             # + synthetic form-(c) validator test (FR-015)
└── test_focalization.py       # retarget limited-third tests to form (c) (FR-013/FR-014)

# Docs / debt (contract-before-code)
bookwright-design.md           # § 13.1 third return shape; § 13.2/13.5/20.6.1 focalization note
DEBT.md                        # remove DEBT-019; reconcile the track-A closed-list line
CLAUDE.md                      # plan pointer (Phase 1 agent-context step)
```

**Structure Decision**: Single project, existing `src/bookwright/validation/`
layout. The change is confined to the runner/contract seam and `focalization`
(FR-016); `RunResult` and its two consumers are unchanged.

## Complexity Tracking

> No Constitution violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
