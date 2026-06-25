# Implementation Plan: Move 3 third dimension, second half (judgment) — judge first-person breaks in `bookwright-continuity`; close DEBT-021

**Branch**: `054-move3-first-person-judgment` | **Date**: 2026-06-25 | **Spec**: [`spec.md`](./spec.md)

**Input**: Feature specification from `/specs/054-move3-first-person-judgment/spec.md`

## Summary

The **judgment half** of move 3's **third dimension** — the 1st-person break /
pro-drop recall ceiling (**DEBT-021**) — landing as the exact **mirror of
iteration 052** (head-hopping) over the **other** `focalization` abstention.
Iteration 053 already made `focalization` *honest*: under **any** declared
third-person voice it emits `Abstention(_FIRST_PERSON_RECALL_PENDING,
pending_capability, code="first_person_recall")` in both branches, and the
`code` discriminator + `_judges(validator, code)` keying are already in place.
This iteration is therefore a **skill + status** change with **zero diff under
`validation/`**:

1. **Skill** — `bookwright-continuity` gains a **sixth axis** ("1st-person break
   / voice slip") in its `## Procedimiento` + `## Output`, grounded **only** in
   the declared narrative voice (`bible/constitution.md`, already read by the 5th
   axis) — **no roster, no POV calendar** (a 1st-person break is grammatical
   person, not character identity). It applies under **all** declared third
   person (limited **or** non-limited), unlike the limited-only 5th axis, and
   **adds** the pro-drop morphological recall (`Caminé`, `Me senté`) on top of —
   never suppressing — `focalization`'s explicit-pronoun core.
2. **Description** — the trigger is **folded** under the existing 5th-axis
   voice/focalization phrase **without growing** (the description sits at
   **1000/1024**, 24 chars of slack), mirrored **verbatim** into
   `SKILL_DESCRIPTIONS["bookwright-continuity"]`.
3. **Status** — one new `judge_first_person_recall` `Rule` keyed via the
   **existing** `_judges("focalization", "first_person_recall")`, inserted
   **immediately after `judge_head_hopping` and before `define_focus`**.
   Informative, never degrades green; precisely separated from the head-hopping
   nudge by `code`.

This **completes the first wave of move 3** (051 undeclared characters + 052
head-hopping + 053/054 first-person break) and **closes DEBT-021**.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II — unchanged).

**Primary Dependencies**: none added (Constitution II). Touched modules import
only what they already import — `bookwright.validation.base.NotEvaluatedKind`
(in `status/rules.py`, already imported) and the static description table.

**Storage**: N/A — plain-text source of truth. The skill is materialized from
`resources/commands/bookwright-continuity.md`; the graph stays a derived cache;
**no** new `bible/` or `references/` file is created (FR-016).

**Testing**: `pytest` (≥ 80 % coverage, single-sourced `fail_under`), plus
`ruff check`, `ruff format --check`, `mypy --strict`. The skill is LLM-judged
prose: its judgment quality is **not** unit-asserted (consistent with
`bookwright-verify` today) — only materialization, lint, trigger, and the
keyed nudge are testable (FR-017).

**Target Platform**: CLI (`uv run bookwright`), offline-capable; **no LLM in CI**
(§ 20.6.2 decision 4 — judgment, not gate).

**Project Type**: single project (src-layout `src/bookwright/`, `tests/` at root).

**Performance Goals**: N/A — `status` rule evaluation is pure `state → actions`,
no I/O; one extra `Rule` row is O(1) per report.

**Constraints**: each changed file ≤ 500 lines (all touched files stay well
under); description ≤ 1024 chars (lint Rule 3); the iteration-044 green predicate
stays byte-for-byte identical; `activate_dormant_validators` stays
`missing_input`-only; **no `error` is born from an LLM**.

**Scale/Scope**: 3 source files (`bookwright-continuity.md`, `descriptions.py`,
`status/rules.py`) + `DEBT.md` + `bookwright-design.md` + `CHANGELOG.md` /
`CLAUDE.md` (release-time) + the oracle/test updates. Zero files under
`validation/`.

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1 design. No violations →
Complexity Tracking left empty.*

- **I. Plain Text as Source of Truth (NON-NEGOTIABLE)** — ✅ the skill, the
  description mirror, and the rule table are all plain text; the only grounding
  input (declared voice) is authored prose; no graph becomes a source of truth.
- **II. Modern Python Stack** — ✅ no dependency added; no stack change.
- **III. src-layout** — ✅ edits stay within `src/bookwright/` and `tests/`.
- **IV. Modular Command Surface** — ✅ no new CLI subcommand; `status/rules.py`
  gains one `Rule` + one builder, staying ≤ 500 lines.
- **V. Plugin-Based Integrations** — ✅ untouched (no integration change beyond
  the re-materialized skill body / description).
- **VI. Agent Skills Only — No Legacy Commands (NON-NEGOTIABLE)** — ✅ the 6th
  axis lives in the `SKILL.md` source under `resources/commands/`; nothing is
  written to `.claude/commands/`.
- **VII. agentskills.io Compliance** — ✅ `name` unchanged (≤ 64, equals its
  directory); `description` stays ≤ 1024 (folded, non-growing); YAML
  front-matter stays valid (`lint_skill_md` gate).
- **VIII. Test Discipline (NON-NEGOTIABLE)** — ✅ ≥ 80 % coverage preserved; the
  skill is tested like `bookwright-verify` (materialization + lint + trigger +
  grounding doc), **not** by asserting LLM output; the new nudge is unit-tested
  by synthetic state and the e2e oracle.
- **IX. JSON-over-stdout** — ✅ `status` already emits the `--json` envelope; the
  new `next_action` rides the existing `next_actions` array.
- **X. Design Document Axioms / Frozen Ontology** — ✅ no ontology class added,
  no validator created or modified; `focalization` and everything under
  `validation/` are untouched; § 16 axioms unreopened.

**Scope & Release Discipline** — ✅ no plumbing-for-future-X: the `code` contract
and `_judges(validator, code)` already shipped in 053 and are only **used** here.
This iteration adds exactly one observable delta (the first-person judgment +
its nudge) and closes DEBT-021 (the debt entry is **removed**, not deferred).

## Project Structure

### Documentation (this feature)

```text
specs/054-move3-first-person-judgment/
├── plan.md              # This file (/speckit-plan output)
├── spec.md              # Already created (/speckit-specify)
├── research.md          # Phase 0 output (this command)
├── data-model.md        # Phase 1 output (this command)
├── quickstart.md        # Phase 1 output (this command)
├── contracts/
│   ├── skill-sixth-axis.md      # The 6th-axis skill-body + description contract
│   └── status-nudge.md          # The judge_first_person_recall rule contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── resources/commands/
│   └── bookwright-continuity.md      # FR-001..FR-005, FR-016: add 6th axis to
│                                     #   ## Procedimiento + ## Output; fold the
│                                     #   1st-person trigger into the 5th-axis
│                                     #   voice/focalization phrase (FR-006); the
│                                     #   front-matter `description` mirrors descriptions.py
├── integrations/
│   └── descriptions.py               # FR-006/FR-015: SKILL_DESCRIPTIONS["bookwright-continuity"]
│                                     #   mirrored VERBATIM with the source front-matter; ≤ 1024
└── status/
    └── rules.py                      # FR-009..FR-012: add `_judge_first_person_recall`
                                      #   builder + a `judge_first_person_recall` Rule keyed on
                                      #   `_judges("focalization", "first_person_recall")`,
                                      #   inserted AFTER judge_head_hopping, BEFORE define_focus

# UNTOUCHED (FR-013): zero diff under src/bookwright/validation/ — focalization.py
# already emits the first_person_recall abstention (053); the `code` contract and
# `_judges` helper are not changed.

tests/
├── resources/
│   ├── test_command_body.py          # FR-017: a 6th-axis assertion mirroring
│   │                                 #   test_continuity_carries_the_fifth_head_hopping_axis
│   └── test_command_activation.py    # FR-006/SC-002: the folded 1st-person trigger fires
│                                     #   ES+EN; the 4th/5th triggers still fire
├── integrations/
│   ├── test_descriptions.py          # FR-015: the equality gate stays green (verbatim mirror)
│   ├── test_skill_capabilities.py    # lint: name/description/front-matter
│   └── test_materialize.py           # the skill materializes with the new body
├── status/
│   └── test_rules.py                 # FR-009..FR-012: positive (focalization,
│                                     #   first_person_recall) → nudge; NEGATIVE
│                                     #   (head_hopping-only → no first-person nudge; the
│                                     #   first-person nudge never fires on head_hopping);
│                                     #   all-three co-fire in table order; green preserved
├── commands/
│   └── test_status.py                # the new action surfaces through the command envelope
├── fixtures/tiny-historical/
│   └── expected-status.md            # FR-017: next_actions skills 5 → 6 (a 4th continuity),
│                                     #   with the co-located prose + inline `# nudge:`/
│                                     #   iteration comments updated in the SAME edit
└── e2e/
    └── test_orchestration_workflow.py # reads the tiny-historical oracle (length 5 → 6, GREEN)

# Repo-root records:
DEBT.md                 # FR-018/SC-007: REMOVE DEBT-021 (the dimension is complete)
bookwright-design.md    # FR-018: § 20.6.2 / § 13.5 mark the 3rd dimension landed + first wave complete
CLAUDE.md / CHANGELOG.md # milestone prose + iteration index row 054 (release-time reconciliation)
```

**Structure Decision**: Single project, existing layout. The change is two thin
seams — the **skill prose** (`resources/commands/bookwright-continuity.md` + its
verbatim `descriptions.py` mirror) and the **status nudge** (`status/rules.py`).
There is deliberately **no** `validation/` change: the honesty/judgment split
(mirroring 045/050 → 052) put the contract work in 053 so the judgment half is a
clean skill + nudge addition. No new file under `bible/` or `references/`
(FR-016).

## Complexity Tracking

> No Constitution Check violations — this section is intentionally empty.
