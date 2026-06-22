# Implementation Plan: Tri-valued validator result (`evaluated` / `not-evaluated(reason)`)

**Branch**: `040-tri-valued-validator-result` | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/040-tri-valued-validator-result/spec.md`

## Summary

A validator returns `list[Violation]` and an empty list is indistinguishable
between "evaluated and clean" and "had nothing to look at" — the false-confidence
bug that kept `focalization` asleep-and-green for the whole `v0.4` line (DEBT-004).
This iteration makes a validator's per-run verdict **tri-valued**: *evaluated*
(with or without findings) vs *not-evaluated(reason)*, so GREEN means "evaluated and
clean," never "did not look." It closes the second facet of issue #1 and the
`v0.5.0` milestone.

**Technical approach (the load-bearing decision).** A validator signals
not-evaluated by **raising a dedicated `NotEvaluated(reason)` signal** that the
runner — already the per-validator isolation boundary — catches in a clause
*before* its generic exception handler and records in a new `not_evaluated`
channel. The `Validator.validate` return type stays **`list[Violation]`,
unchanged**: there is no dual-shape return (`list | Outcome`) and the runner never
sniffs a return value, so the smell FR-001 forbids (and the doctrine's "eliminate
the cause, do not contain it") never materializes, while a custom validator that
returns a bare `list[Violation]` keeps working untouched and reads as **evaluated**
(FR-014). The new state flows additively through the runner → `ValidationReport`
→ the `--json` envelope (`not_evaluated[]`, sibling of `violations`/`errors`) → the
human report → `status`'s derived state (`state.validation.not_evaluated`) → a
`next_actions` activation rule → the status-reading skill resource. The CI gate is
untouched: only `error`-severity `Violation`s gate; not-evaluated is not a finding.

`bookwright-design.md § 13.1` is updated to the new contract **before** any code
diverges (T001 — plan § 7.3).

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: stdlib only for this change — `dataclasses`, `typing`,
`re` (no new dependency; Constitution II). No Markdown AST, no LLM, no graph.

**Storage**: N/A — validators stay in-memory; the not-evaluated channel persists
nothing (mirrors `Violation`/`ValidatorError`).

**Testing**: `pytest` (+ `pytest-cov`, ≥ 80 % gate, single-sourced in
`[tool.coverage.report]`). New `tests/validation/test_runner.py` coverage for the
signal path; extended validator tests; a new fixture for the dormant-green E2E.

**Target Platform**: CLI (`bookwright validate` / `bookwright status`), agent-facing
via `--json` (Principle IX).

**Project Type**: single project, src-layout (`src/bookwright/`, `tests/` at root).

**Performance Goals**: N/A — same single pass over the corpus; the prose seam's
cached views (iteration 039) mean no extra disk reads.

**Constraints**: every changed/new source file ≤ 500 lines (Principle IV); prose
validators stay graph-free, LLM-free, `triples=()`, frozen ontology untouched
(Principle X / FR-015); `--json` additive (no existing key changes shape, Principle
IX / FR-007); deterministic, byte-identical output across runs (FR-013).

**Scale/Scope**: 3 of 5 validators migrate (`focalization`, `setting_continuity`,
`character_presence`); `temporal` / `factual_anchor` only conform to the
backward-compatible contract (return lists; never not-evaluated).

## Constitution Check

*GATE: re-checked after Phase 1 design — still passing.*

| Principle | Status | Note |
|---|---|---|
| I — Plain text source of truth | ✅ | Graph is still a derived cache; no behavior reads from it for this state. Design § 13.1 updated in plain text before the code. |
| II — Modern Python stack | ✅ | No new dependency; stdlib only. |
| III — src-layout | ✅ | All edits under `src/bookwright/`, tests under `tests/`. |
| IV — Modular command surface (≤ 500 lines/file) | ✅ | `base.py` 284 → ~305; `runner.py` 66 → ~80; `report.py` 107 → ~125; `status/model.py` 158 → ~175; `status/rules.py` 177 → ~205; `validate.py`/`status.py` minor. All well under 500. No new CLI subcommand. |
| V — Plugin-based integrations | ✅ | Untouched. |
| VI — Agent Skills only | ✅ | One skill **resource** Markdown edited (`bookwright-research.md`); no `commands/` dir written. |
| VII — agentskills.io compliance | ✅ | No SKILL.md front-matter change. |
| VIII — Test discipline (≥ 80 %) | ✅ | New + extended tests; runner signal path and the activation rule fully covered. |
| IX — JSON-over-stdout | ✅ | `not_evaluated[]` is an additive sibling key in both the `validate` envelope and the `status` `state.validation` payload; no existing key changes shape. |
| X — Design document axioms / frozen ontology | ✅ | Prose validators keep `triples=()`; `golem.ttl` / `CLASS_IRI` untouched. Design § 13.1 is updated through the ratified channel (it is not a § 16 axiom). |

**No violations — Complexity Tracking is empty.**

## Project Structure

### Documentation (this feature)

```text
specs/040-tri-valued-validator-result/
├── spec.md              # complete (clarified)
├── plan.md              # this file
├── research.md          # Phase 0 — the contract-mechanism decision + alternatives
├── data-model.md        # Phase 1 — NotEvaluated signal, NotEvaluatedResult, envelope/state deltas
├── quickstart.md        # Phase 1 — runnable validation scenarios (US1/US2/US3 + SC predicate)
├── contracts/
│   ├── validator-protocol.md   # the tri-valued contract (signal + return type)
│   ├── validate-envelope.md    # the --json not_evaluated[] channel + green predicate (SC-002)
│   └── status-state.md         # state.validation.not_evaluated + activation next_action (SC-004)
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/validation/
├── base.py                 # + NotEvaluated(Exception) signal; + NotEvaluatedResult(frozen) record; __all__
├── runner.py               # RunResult gains not_evaluated; run_validators catches NotEvaluated before Exception
├── report.py               # ValidationReport.not_evaluated; to_json not_evaluated[]; render section; green predicate doc
├── __init__.py             # export NotEvaluated, NotEvaluatedResult
└── validators/
    ├── focalization.py      # 4 early "no usable voice" returns → raise NotEvaluated(reason) (FR-008 i–iv)
    ├── setting_continuity.py# empty manuscript → raise NotEvaluated("the manuscript is empty") (FR-009)
    └── character_presence.py# no prose AND empty roster → raise NotEvaluated(no-inputs reason) (FR-009)

src/bookwright/status/
├── model.py                # ValidationSummary gains not_evaluated: tuple[NotEvaluated record …]; to_payload
├── queries.py              # validation_summary consumes the 4-tuple, fills not_evaluated
└── rules.py                # + activate_dormant_validators rule + _REMEDIES map (SC-004)

src/bookwright/commands/
├── validate.py             # thread not_evaluated from run_validators into ValidationReport
└── status.py               # (no change beyond what model/queries provide; human report optional line)

src/bookwright/resources/commands/
└── bookwright-research.md  # startup step lists state.validation not-evaluated among raw facts (FR-011)

bookwright-design.md        # § 13.1 updated to the tri-valued contract (T001, BEFORE code diverges)

tests/
├── validation/test_runner.py             # signal caught → not_evaluated channel; crash still → errors[]
├── validation/test_report.py             # envelope not_evaluated[]; green predicate True/False
├── validation/test_focalization.py       # 4 not-evaluated reasons; usable decl still evaluated
├── validation/test_setting_continuity.py # empty manuscript → not-evaluated; prose present → evaluated
├── validation/test_character_presence.py # empty manuscript+roster → not-evaluated; roster-only → evaluated w/ orphans
├── status/test_rules.py                  # activation action names focalization remedy (SC-004)
├── status/test_queries.py                # validation_summary surfaces not_evaluated
└── e2e/ + fixtures/                       # dormant-focalization fixture: validate reports not-evaluated, not clean (SC-001/SC-002)
```

**Structure Decision**: single project, existing layout. The change is concentrated
at the `validation/` seam and propagates additively outward; no new module or
package is introduced.

## Complexity Tracking

> No Constitution violations — section intentionally empty.

## Phase notes (plan conventions)

- **§ 7.3 — design before code (T001).** `bookwright-design.md § 13.1` is rewritten
  to the tri-valued contract as the **first** task, before any `base.py` edit, so
  the design never lags the code (FR-001). The update keeps the `validate` signature
  (`-> list[Violation]`) and documents the `NotEvaluated` signal + the `not_evaluated`
  channel as the contract addition.
- **§ 7.2 — task split.** This iteration plausibly exceeds ~10 tasks (contract +
  three validators + runner/report + status + skill + fixtures/E2E). `/speckit-tasks`
  should group them by the user-story phases (US1 = focalization; US2 =
  setting_continuity + character_presence; US3 = status + skill) on top of the shared
  contract foundation (base/runner/report), so each story is independently testable
  and the shared plumbing lands once first.
