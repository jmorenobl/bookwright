# Implementation Plan: Move 3 third dimension, first half — `focalization` first-person-recall honesty + the abstention `code` discriminator

**Branch**: `053-move3-first-person-honesty` | **Date**: 2026-06-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/053-move3-first-person-honesty/spec.md`

## Summary

`focalization` today runs its deterministic first-person-break check
(`_first_person_breaks`, matching only the closed set `yo`/`nosotros`/`nosotras`/`i`/`we`)
under a declared third-person voice and is **silent** about everything that closed set
cannot see — Spanish pro-drop verbal morphology (`Caminé`, `Me senté`), an open set
no regex captures (**DEBT-021**). That silence is the `[]`-means-clean lie issue #1
banished, at the sub-check level.

This iteration is the **honesty half** of the third move-3 dimension (mirroring how
head-hopping was split into honesty in 045/050 and judgment in 052). `focalization`
**declares the ceiling honestly** with a `pending_capability` `Abstention`
(`code="first_person_recall"`) under **both** third-person branches, while preserving the
explicit-pronoun `warning`s byte-for-byte. Because `focalization` now emits **two**
`pending_capability` abstentions under limited-third (head-hopping + first-person-recall),
the post-052 `status` keying (`_judges(validator)` = validator-name + `pending_capability`)
can no longer tell them apart and would mis-fire the head-hopping nudge. So this iteration
also lands the **contract plumbing the honesty half forces**: a short stable `code`
discriminator on `Abstention`/`NotEvaluatedResult` (additive, exactly as 044 added `kind`),
threaded end-to-end through the runner's single naming point, and re-points the existing
move-3 nudges (051, 052) to key on `(validator, code)`. **No first-person nudge is added**
— that destination (the sixth `bookwright-continuity` axis) is iteration 054, which closes
DEBT-021.

Technical approach: a faithful replay of the 044 `kind` precedent. `code` is added as an
optional `str | None = None` field on the two frozen dataclasses, stamped by the runner's
shared `_record`, serialized additively in `NotEvaluatedResult.to_json`, and flows for
free into `status` (which holds the runner's `NotEvaluatedResult` tuples directly). Three
behavior edits ride the contract: `focalization` declares the recall abstention,
`character_unknown_mentions` converts from a raised total abstention (form (b)) to a
returned partial abstention (form (c)) so it can carry `code="undeclared_characters"`, and
`_judges` gains a `code` argument. The CLI stays fully deterministic, no `error` is born,
and the 044 green predicate is byte-identical.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: none added (Constitution II). Touches `rdflib`-free pure-Python
layers only (`validation/base.py`, `validation/runner.py`, two validators, `status/rules.py`,
`status/model.py`, `commands/validate.py`).

**Storage**: N/A — the validation subsystem persists nothing (`base.py` docstring, FR-020).
The `code` is in-memory + on-the-wire (JSON) only.

**Testing**: `pytest` (≥ 80 % coverage, single-sourced in `[tool.coverage.report]`), plus
`ruff check`, `ruff format --check`, `mypy --strict` — the four CI gates.

**Target Platform**: CLI (`bookwright validate` / `bookwright status`), cross-platform.

**Project Type**: single project (src-layout, Constitution III).

**Performance Goals**: N/A — no new traversal; `code` is one extra optional string per
abstention.

**Constraints**: each changed file ≤ 500 lines (Principle IV); additive contract only (no
field renamed/retyped); the 044 green predicate (`report.py`) byte-identical; the
explicit-pronoun regex/`_first_person_breaks` byte-identical (FR-010/FR-011); no `error`
born from this change (FR-017); frozen ontology untouched (Principle X); `focalization`
stays a prose validator (`triples=()`).

**Scale/Scope**: ~7 source files, ~6 test files, 1 fixture oracle, the e2e tri-valued + orchestration
tests, plus contract-before-code doc reconciliation (DEBT-021, design §§ 13.4/13.5 + 20.6.x,
CLAUDE.md milestone prose + iteration index row 053).

## Constitution Check

*GATE: re-checked after Phase 1 design — still passing.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain text as source of truth | ✅ | No binary store; `code` is JSON/in-memory; the derived graph cache is untouched. |
| II. Modern Python stack | ✅ | **No new dependency.** Pure `dataclasses`/`enum`/`re` edits within the locked stack. |
| III. src-layout | ✅ | All edits under `src/bookwright/`, all tests under `tests/`. |
| IV. Modular command surface (≤ 500 lines) | ✅ | Every changed file stays well under 500 (largest, `base.py`, is 450; the additions are a few lines). |
| V. Plugin-based integrations | ✅ | No integration change in this slice. |
| VI. Agent Skills only | ✅ | **No skill change** (the judgment half, with its skill axis, is 054). |
| VII. agentskills.io compliance | ✅ | No `SKILL.md` touched. |
| VIII. Test discipline (≥ 80 %, pyramid) | ✅ | Unit (`base`/`runner`/validators), command (`status`/`validate`), e2e (tri-valued + orchestration). |
| IX. JSON-over-stdout contract | ✅ | `code` is an **additive** key in the existing `not_evaluated[]` envelope; no field renamed; stdout stays one JSON document. |
| X. Design-document axioms (§ 16, frozen ontology) | ✅ | Ontology untouched; `focalization` stays `triples=()`; no § 16 axiom reopened. |

**Scope & Release Discipline**: the `code` field has a concrete consumer **in this same
iteration** (the re-pointed `_judges`), so it is not speculative plumbing — it is forced by
`focalization` emitting a second `pending_capability` abstention (doctrine § 3: no plumbing
without a consumer; here the consumer ships alongside). No closed `code` enum is introduced
(only three values exist; a registry would be speculative — Assumptions). No first-person
nudge is added (no destination yet → no signposted dead-end). DEBT-021 stays open. **No
gate** — the verdict is informative; the CLI stays LLM-free.

**Result: PASS — no violations, no Complexity Tracking entries required.**

## Project Structure

### Documentation (this feature)

```text
specs/053-move3-first-person-honesty/
├── plan.md              # This file
├── spec.md              # Already authored + hardened
├── research.md          # Phase 0 output (this command)
├── data-model.md        # Phase 1 output (this command)
├── quickstart.md        # Phase 1 output (this command)
├── contracts/
│   ├── abstention-code.md       # The `code` field contract (base + runner + serialization)
│   └── status-code-keying.md    # The `_judges(validator, code)` predicate contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── validation/
│   ├── base.py                 # +code on Abstention & NotEvaluatedResult; +code in to_json (FR-001/002/005)
│   ├── runner.py               # _record gains code=None; form (c) passes abstention.code, form (b) None (FR-003/004)
│   ├── report.py               # UNCHANGED — the 044 green predicate is byte-identical (FR-016)
│   └── validators/
│       ├── focalization.py     # _FIRST_PERSON_RECALL_PENDING; recall Abstention in both 3rd branches;
│       │                       #   head-hopping Abstention gains code="head_hopping" (FR-006/007/008/014)
│       └── character_unknown_mentions.py  # form (b) → form (c) EvalResult([], [Abstention(..., code="undeclared_characters")]) (FR-013)
├── status/
│   ├── rules.py                # _judges(validator, code); re-point judge_undeclared_characters & judge_head_hopping (FR-012/013/014)
│   └── model.py                # ValidationSummary.not_evaluated already holds NotEvaluatedResult → code flows free (verify only)
└── commands/
    └── validate.py             # ingestion skip NotEvaluatedResult: code defaults None — verify positional call still valid

tests/
├── validation/
│   ├── test_base.py            # +code field + default + to_json key
│   ├── test_report.py          # green unchanged with a code-bearing pending_capability entry; key-set assertion +code
│   ├── test_runner.py          # code stamped from form (c); None from form (b)
│   ├── test_command.py         # every serialized not_evaluated[] entry carries the code key
│   ├── test_focalization.py    # recall abstention both 3rd branches; warnings byte-identical; 1st/missing_input untouched
│   └── test_character_unknown_mentions.py  # form (b) → form (c); reason/kind unchanged, +code="undeclared_characters"
├── status/test_rules.py        # keying by code: positive head_hopping; NEGATIVE first_person_recall-only & missing_input
├── commands/
│   ├── test_status.py          # code surfaces in status payload; key-set assertion +code
│   └── test_validate_skipped.py  # ingestion missing_input skip serializes code: null; key-set assertion +code (doctrine §4 sweep)
├── fixtures/tiny-historical/expected-status.md  # +first_person_recall entry, +code keys, next_actions still 5
└── e2e/test_tri_valued_validation.py + test_orchestration_workflow.py  # +code, +first_person_recall in 3rd-person fixtures
```

**Structure Decision**: single project, existing layout. The change is a thin additive
contract field plus three localized behavior edits — no new module, package, or seam.

## Phase 0: Research

See [research.md](./research.md). All decisions resolved from the spec + the 044 `kind`
precedent; **no NEEDS CLARIFICATION** remains (the spec's Clarifications session already
pinned every open question).

## Phase 1: Design & Contracts

- [data-model.md](./data-model.md) — the `Abstention` / `NotEvaluatedResult` / `code`
  entities and the `character_unknown_mentions` form (b)→(c) transition.
- [contracts/abstention-code.md](./contracts/abstention-code.md) — the field contract:
  type, default, runner stamping authority, serialization, sort invariance.
- [contracts/status-code-keying.md](./contracts/status-code-keying.md) — the
  `_judges(validator, code)` predicate, the two re-pointed rules, the negative cases.
- [quickstart.md](./quickstart.md) — runnable validation scenarios.

Agent context: the managed CLAUDE.md plan reference is repointed to this plan.

## Complexity Tracking

> No Constitution Check violations — this section is intentionally empty.
