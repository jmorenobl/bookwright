---
description: "Task list for iteration 021 — bookwright-research consumes the status research queue"
---

# Tasks: `bookwright-research` consumes the status research queue

**Input**: Design documents from `/specs/021-research-status-queue/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/research-skill.md, quickstart.md

**Tests**: One contract test is in scope (research.md D7 / contract RQ-1). It is
written **first** and made to fail before the body edit, per the constitution's
test-discipline principle (§ VIII) and the user's "máxima calidad / nula deuda
técnica" directive. No other test is added; the existing both-integration
materialize+lint, budget, and description-mirror tests are reused unchanged.

**Organization**: Tasks are grouped by user story (P1→P3). Because the entire
behavior is one conditional first step in a single Markdown source, all three
stories edit the **same file** (`src/bookwright/resources/commands/bookwright-research.md`)
and therefore run **sequentially, never `[P]` against each other**. Each story
remains independently *verifiable* via its own acceptance scenarios.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete-task dependency).
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories).
- Every task names an exact file path.

## Scope guard (zero technical debt)

This iteration is **prose-only** (plan.md Summary). It is a violation of scope
discipline to: touch any `src/bookwright/**/*.py`; edit `bookwright status`
(iteration 020, FR-009); change the `description` front-matter or
`integrations/descriptions.py` (research.md D4); add a `references/` file
(D5); or duplicate the iteration-9 materialization pipeline (D3, FR-010). The
only two files that may change are the command source and the one test file.

---

## Phase 1: Setup (baseline)

**Purpose**: Establish a known-good starting point so any regression is attributable.

- [ ] T001 Run the full gate suite from repo root to confirm a green baseline before editing: `uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest`; record the current `bookwright-research` body approx-token count reported by `tests/resources/test_command_budget.py` (≈1135, ceiling 5000) so the post-edit budget headroom can be confirmed.

---

## Phase 2: Foundational (blocking prerequisite for all stories)

**Purpose**: Pin the exact status fields the prose must cite, so the queue step is written against the frozen iteration-020 contract — not paraphrased.

**⚠️ CRITICAL**: Do this before any body edit; wrong field names would be silent debt the tests cannot catch.

- [ ] T002 From `specs/020-status-command/contracts/cli-status.md`, confirm and note the exact read-view field paths the prose will name: `state.open_questions.items[].{id,text,file}` and `state.unresolved_anchors.items[].{promotes,constrains,file,problems}`, each list carrying `count == len(items)` in corpus-stable order; confirm `state.graph.available` is the degraded-state flag (data-model.md "Read view"). The prose MUST cite these `state.*` facts and MUST NOT reference `next_actions[]` (clarification #1 / RQ-3).

**Checkpoint**: Field names pinned — body edits can begin.

---

## Phase 3: User Story 1 — Start from the project's own open research queue (Priority: P1) 🎯 MVP

**Goal**: A no-topic invocation surfaces the project's open research questions and unresolved anchors as a grouped, numbered queue and offers "research these N / a new topic", instead of a blank topic prompt.

**Independent Test**: On a project with ≥1 open question or ≥1 unresolved anchor, invoke research with no topic → the skill runs `bookwright status --json`, presents the grouped/numbered queue, and offers the choice (quickstart.md §3 "US1 — queue start").

### Tests for User Story 1 (write FIRST, must FAIL before T004) ⚠️

- [ ] T003 [US1] Add a failing contract test `test_body_consults_status_queue` to `tests/integrations/test_research_skill.py`, mirroring the existing `test_body_instructs_the_final_graph_build`. Assert, against **both** the source body (`parse_frontmatter(_source().read_text(...)).body`) and the materialized body for at least one integration via `generate_skill_md(... NullLedger())`: (a) `"bookwright status"` is present (RQ-1, the first-step consult); (b) both raw-fact names `"open_questions"` **and** `"unresolved_anchors"` are present (RQ-3/FR-002 — the queue is built from the raw facts). Run it; confirm it FAILS (the body does not yet mention `bookwright status`/the raw facts). This is RQ-1 + RQ-3 (FR-001 / FR-002 / SC-002). These are stable iteration-020 contract field names the prose must cite verbatim, so the assertions harden the contract without over-fitting to prose wording. **Deliberately do NOT assert `"next_actions"` is absent**: the prose legitimately names `next_actions` to forbid its use (T004), and `status --json` emits a `next_actions` entry addressed to `bookwright-research` at runtime — a presence/absence check on that token would either contradict T004 or be brittle. The "raw facts, not the handoff prompt" guarantee is verified by prose review (RQ-3).

### Implementation for User Story 1

- [ ] T004 [US1] In `src/bookwright/resources/commands/bookwright-research.md`, replace the current no-topic instruction — the sentence "Si no se da tema, pregunta cuál antes de continuar." in `## Input` (soft-wrapped across lines 28–29 in the source; it appears **only** there, not in `## Procedimiento`) — with a conditional **first step** for the no-topic path: instruct the agent to run `bookwright status --json`, read `state.open_questions.items[]` and `state.unresolved_anchors.items[]` (explicitly **not** `next_actions[]`), and present a research queue — grouped (open questions first, then unresolved anchors), each item numbered 1..N preserving the status corpus-stable order, with a soft cap of ≈10 combined and a "+M more (ejecuta `bookwright status` para la lista completa)" overflow note, never inventing placeholder items — then offer the author the explicit choice "investigar uno/varios de estos N / proponer un tema nuevo". Spanish prose to match the file (RQ-3, RQ-4; FR-002/FR-002a).

- [ ] T005 [US1] In the same step, specify the selection→topic transition: a single pick becomes one topic; **multiple** picks run the existing seven-step procedure **sequentially, once per item** (one determined topic per pass, clean per-topic provenance); a "tema nuevo: X" answer makes X the topic; an ambiguous/empty answer re-asks rather than guessing. State that once a topic is determined the seven steps run **unchanged** (RQ-5; FR-003/FR-007, clarifications #2/#3 edge case). Keep the body under the 5000-token budget.

- [ ] T006 [US1] Run `uv run pytest tests/integrations/test_research_skill.py -q`; confirm `test_body_consults_status_queue` now PASSES and `test_materializes_and_lints_for_both_integrations` (both `claude` and `generic` + `lint_skill_md`) stays green — the new step survived materialization for both integrations (RQ-1/RQ-9; SC-001/SC-002).

**Checkpoint**: MVP — the blank prompt is gone; the bottom-up queue is delivered and tested.

---

## Phase 4: User Story 2 — Explicit topic keeps the top-down path (Priority: P2)

**Goal**: With a topic given (`$ARGUMENTS`), the status step is skipped and the established procedure runs exactly as before — no added friction or latency.

**Independent Test**: Invoke with an explicit topic → the protocol goes straight into decomposition/search; the status-queue step is not required (quickstart.md §3 "US2 — top-down"; spec US2-AS1).

### Implementation for User Story 2

- [ ] T007 [US2] In the same `src/bookwright/resources/commands/bookwright-research.md` step (sequential after T004–T005; same file, not `[P]`), make the condition explicit and unambiguous: **only** when no topic is supplied does the status-queue step run; when `$ARGUMENTS` carries a topic, the skill skips the queue entirely and proceeds directly to step 1 of `## Procedimiento`. Ensure no wording makes the status consultation mandatory on the top-down path (RQ-2; FR-004/SC-004).

- [ ] T008 [US2] Prose review of the edited body against spec US2 acceptance scenario AS1 and SC-004: confirm the explicit-topic path reads identically to the pre-021 protocol (no status call, no queue), and that the seven steps and final `bookwright graph build --json` are untouched.

**Checkpoint**: Top-down behavior provably preserved; bottom-up addition is opt-in to the no-topic case only.

---

## Phase 5: User Story 3 — Graceful fallback when there is no pending work (Priority: P3)

**Goal**: A no-topic invocation on an empty/unavailable/degraded/errored status never breaks or blocks — it quietly falls back to asking which topic to research.

**Independent Test**: No-topic invocation on a project with an empty queue, and separately one where status can't be produced → both end in the topic-ask fallback, zero errors, no dead end (quickstart.md §3 "US3"; spec US3 acceptance).

### Implementation for User Story 3

- [ ] T009 [US3] In the same step (sequential after T007; same file, not `[P]`), add the degradation clause: treat **all** of {empty queue, `state.graph.available == false`, non-zero `status` exit, unparseable output} as "no queue" → fall back to asking the author which topic to research, without surfacing an error or blocking (research.md D6; FR-005/FR-006/SC-003). Explicitly preserve precedence of the existing `[research].enabled = false` inert-system notice over the queue step (spec Edge Cases; RQ-6).

- [ ] T010 [US3] Prose review against spec US3 acceptance scenarios AS1/AS2 and the "Partial queue" / "degraded state" / "ambiguous answer" / "resolved item" edge cases: confirm partial queues omit the empty group (no placeholders), the queue is read fresh each invocation (no skill-side cache), and no failure mode reaches the author as an error (RQ-6).

**Checkpoint**: All three entry behaviors (queue / top-down / fallback) coexist in the one conditional step.

---

## Phase 6: Polish & Cross-Cutting Concerns (binding gates + scope proof)

**Purpose**: Prove the change is green, in-budget, bilingual-intact, and confined to two files.

- [ ] T011 [P] Run `uv run ruff check && uv run ruff format --check` — lint/format clean (the new test included).
- [ ] T012 [P] Run `uv run mypy --strict` — type-clean across src + tests.
- [ ] T013 Run `uv run pytest` — full suite green at ≥80% coverage; since no `src/` line changed, confirm coverage is **not** regressed (RQ-9; SC-006).
- [ ] T014 [P] Run `uv run pytest tests/resources/test_command_budget.py -q` — `bookwright-research` body stays under the 5000-token tier-2 budget; compare against the T001 baseline to confirm the step added well under ~250 tokens (research.md D5; RQ-9).
- [ ] T015 [P] Run `uv run pytest tests/integrations/test_descriptions.py -q` — the bilingual `description` (ES + EN trigger phrasings) is preserved verbatim and the `SKILL_DESCRIPTIONS` mirror is unchanged (RQ-7; FR-008/SC-005). Confirm by inspection that `src/bookwright/integrations/descriptions.py` was **not** edited.
- [ ] T016 Run the quickstart manual spot-check (quickstart.md §2): in a scratch `bookwright init` project, materialize and `grep -n "bookwright status"` in both `.claude/skills/bookwright-research/SKILL.md` and `.agents/skills/bookwright-research/SKILL.md` — both reference the no-topic protocol (SC-001).
- [ ] T017 Prove scope confinement (FR-009 / RQ-8): `git diff --name-only main...021-research-status-queue` lists **only** `src/bookwright/resources/commands/bookwright-research.md` and `tests/integrations/test_research_skill.py` (plus this iteration's `specs/021-*` docs); no Python source, no `bookwright status`, no other skill changed.

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (T001)** → no deps; run first to capture the green/budget baseline.
- **Foundational (T002)** → after T001; BLOCKS all story work (the prose must cite the pinned `state.*` fields).
- **US1 (T003–T006)** → after T002. T003 (failing test) precedes T004–T005 (edit); T006 verifies. This is the MVP.
- **US2 (T007–T008)** → after US1's edit exists (same file, sequential).
- **US3 (T009–T010)** → after US2 (same file, sequential).
- **Polish (T011–T017)** → after all story edits land.

### Within / across stories

- All three stories edit the **same single file**, so US1→US2→US3 implementation tasks are strictly sequential — **no `[P]` across them**. Their *verification* tasks (T008, T010) and acceptance tests are independent.
- The contract test (T003) is in a **different file** (`tests/integrations/test_research_skill.py`) but is written first and gates the edit, so it is not parallel with T004.

### Parallel opportunities

- **None within implementation** (one production file).
- Polish gate tasks **T011, T012, T014, T015** are `[P]` — different commands/files, independent reads. T013 (full suite) and T016/T017 (manual/scope) run after edits but are quick to serialize.

```bash
# Polish — independent gates can run together:
uv run ruff check && uv run ruff format --check     # T011
uv run mypy --strict                                # T012
uv run pytest tests/resources/test_command_budget.py -q   # T014
uv run pytest tests/integrations/test_descriptions.py -q  # T015
```

---

## Implementation Strategy

### MVP first (User Story 1 only)

1. T001 baseline → T002 pin fields.
2. T003 failing test → T004–T005 add the conditional no-topic queue step → T006 verify both integrations.
3. **STOP and VALIDATE**: the blank prompt is replaced by the queue with the "these N / a new topic" choice. This alone closes the iteration's core pain (spec US1 "Why this priority").

### Incremental delivery

1. MVP (US1) → queue start works and is tested.
2. US2 → explicit-topic path provably unchanged (regression guard).
3. US3 → empty/unavailable status degrades cleanly.
4. Polish → all four gates green, budget/description intact, scope confined to two files.

---

## Notes

- `[P]` = different files, no incomplete-task dependency. Across US1/US2/US3 implementation there is **no** `[P]` — one shared Markdown source.
- Tests-first: T003 must FAIL before T004; no after-the-fact coverage.
- Zero-debt guard: never edit Python `src/`, `bookwright status`, the `description` front-matter, `descriptions.py`, or the materialization pipeline; never add a `references/` file. T017 proves it.
- Commit after each checkpoint per the repo's auto-git hooks.
