---
description: "Task list — iteration 047: soft warning for unrecognized Propp/Greimas vocabulary terms"
---

# Tasks: Soft warning for unrecognized Propp/Greimas vocabulary terms

**Input**: Design documents from `/specs/047-vocab-term-warning/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/graph-build-envelope.md, quickstart.md

**Tests**: INCLUDED — the spec mandates empirical verification (SC-007, SC-008) and
the plan ships per-site oracles. Test tasks are first-class here.

**Organization**: Tasks are grouped by user story. US1 (Propp `functions:`) is the
MVP. US2 (Greimas `narrative_roles:`) is the class sweep. US3 is the
non-regression / determinism guard.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (Setup, Foundational, Polish carry no story label)

## Path Conventions

Single project, src-layout: `src/bookwright/`, `tests/` at repo root.

---

## Phase 1: Setup (Contract-before-code — docs reconcile BEFORE code diverges)

**Purpose**: Per the zero-debt doctrine (plan § "Contract-before-code"), the
canonical docs change first. These are plain-text edits with no code dependency and
can run in parallel.

- [X] T001 [P] Add the fatal-vs-warning principle paragraph (FR-012) to `bookwright-design.md` § 4.4 (Vocabularios controlados): research's invalid `reliability`/`type` is fatal because it breaks the `factual_anchor` gate; an absent `crm:P2_has_type` is descriptive metadata that breaks nothing, so an unrecognized Propp/Greimas term only warns and the node is still ingested untyped.
- [X] T002 [P] Reconcile `bookwright-design.md` § 13.5 move-3 item 3 from *planned* to *shipped in iteration 047*.
- [X] T003 [P] Remove the **DEBT-016** entry from `DEBT.md` and reconcile the track-B index line (DEBT-015, ~~DEBT-016~~, DEBT-017) per FR-013.

---

## Phase 2: Foundational (Shared channel plumbing — BLOCKS US1 and US2)

**Purpose**: The soft-warning channel that both Propp and Greimas typing sites feed,
plus the valid-term enumerator the render consumes. No user-story site can warn until
this exists.

**⚠️ CRITICAL**: US1 and US2 both depend on every task in this phase.

- [ ] T004 [P] Add the frozen `UntypedVocabTerm` Pydantic model (`model_config = ConfigDict(frozen=True, extra="forbid")`; fields `path`, `field`, `term`, `vocabulary`) to `src/bookwright/io/report.py`, sibling of `UnknownKey` / `UnresolvedReference` / `ResearchTargetWarning` (data-model.md §1; FR-006).
- [ ] T005 [P] Add `terms: tuple[str, ...]` to the frozen `VocabularyIndex` dataclass in `src/bookwright/io/vocabularies.py` and populate it in `_index_turtle` as `tuple(sorted(set(str(label) for every rdfs:label)))` (ES+EN, deduped, sorted → byte-stable); leave `resolve()` unchanged (data-model.md §4; FR-002, FR-016).
- [ ] T006 Add `untyped_vocab_terms: list[UntypedVocabTerm] = field(default_factory=list)` to the `MapResult` dataclass in `src/bookwright/io/_bible_builders.py` (data-model.md §2; depends on T004).
- [ ] T007 Add `untyped_vocab_terms: tuple[UntypedVocabTerm, ...] = ()` to `BuildReport` and emit one additive key in `to_json()` (`"untyped_vocab_terms": [w.model_dump() for w in self.untyped_vocab_terms]`) in `src/bookwright/io/report.py`; do NOT reference it in `exit_code` (data-model.md §3, contracts C-1/C-2; FR-004; depends on T004).
- [ ] T008 In `src/bookwright/commands/_graph.py`, copy the accumulator into the report: `BuildReport(..., untyped_vocab_terms=tuple(result.untyped_vocab_terms))` — verbatim, no translation (plan decision 1; depends on T006, T007).
- [ ] T009 In `src/bookwright/commands/graph/build.py` `_print_summary`/render, when `untyped_vocab_terms` is non-empty append one `  - {path}: {field} '{term}' is not a {vocabulary} term` line per entry (envelope order) and one `  valid {vocabulary} terms: …` line **per distinct vocabulary** via `load_vocabulary(vocabulary).terms`; stderr only, not in `--json` (contracts "Human-readable report"; FR-002, FR-006; depends on T007, T005).

**Checkpoint**: Channel exists end to end and renders; both typing sites can now emit.

---

## Phase 3: User Story 1 — Propp `functions:` typo is surfaced (Priority: P1) 🎯 MVP

**Goal**: An unrecognized `functions:` term under an active `propp` vocabulary emits a
non-fatal warning naming file/field/term/vocabulary; the node is still minted without
`crm:P2_has_type`; exit code unchanged.

**Independent Test**: Build a `tiny-quest`-derived project with one unit whose
`functions:` lists a non-Propp term plus a valid Propp function; assert exactly one
`untyped_vocab_terms` entry for the bad term, none for the valid one, the bad node has
no `crm:P2_has_type`, the valid node has it, and exit code is 0.

### Tests for User Story 1 ⚠️ (write first, ensure they FAIL)

- [ ] T010 [P] [US1] In a new `tests/commands/graph/test_untyped_vocab.py`, add the Propp oracle: copy `tiny-quest` (Propp active), edit one unit so `functions: [struggle, intimidacion]`, run `graph build --json`; assert exit 0, exactly one `untyped_vocab_terms` entry `{path: "outline/units/…", field: "functions", term: "intimidacion", vocabulary: "propp"}` and none for `struggle`; assert the graph has `narrative-function/intimidacion` WITHOUT and `narrative-function/struggle` WITH `crm:P2_has_type` (quickstart Scenario 1; SC-001/002/003/006).
- [ ] T010b [P] [US1] In `tests/commands/graph/test_untyped_vocab.py`, add the **human-render** oracle: run `graph build` **without `--json`** over the same unrecognized-Propp-term fixture and capture **stderr**; assert it contains the per-entry line `outline/units/…: functions 'intimidacion' is not a propp term` **and** the per-vocabulary enumeration line `valid propp terms: …` listing the sorted `rdfs:label`s. This exercises the `_print_summary` render branch (T009) — which the `--json` oracles bypass (`build.py` calls `_print_summary` only when `not json_output`) — closing the FR-002 "human-facing rendering MUST enumerate the valid terms" / SC-002 "lists the valid terms" coverage gap and guaranteeing the new render lines are covered for Principle VIII (contracts "Human-readable report"; FR-002, FR-006; depends on Phase 2 + T011).

### Implementation for User Story 1

- [ ] T011 [US1] In `src/bookwright/io/outline.py:_mint_functions`, inside `if function is None:`, append `UntypedVocabTerm(path=relpath, field="functions", term=raw, vocabulary="propp")` to `ctx.result.untyped_vocab_terms` when `ctx.propp is not None and type_uri is None` (inputs are already-sluggable `(slug, raw)` pairs; deduped across cards → warned once) (data-model.md §5; FR-001/003/007; depends on Phase 2).

**Checkpoint**: US1 fully functional and independently testable — MVP slice complete.

---

## Phase 4: User Story 2 — Greimas `narrative_roles:` actant is surfaced the same way (Priority: P1)

**Goal**: The identical silent `resolve()→None`-then-mint path for Greimas role typing
emits the same non-fatal enumerated warning — a uniform class sweep, not an instance
patch.

**Independent Test**: Build a character with `greimas` active whose `narrative_roles:`
includes a non-Greimas label plus a valid actant; assert one `untyped_vocab_terms`
entry (`field="narrative_roles"`, `vocabulary="greimas"`) for the bad label only, the
role node minted without `crm:P2_has_type`.

### Tests for User Story 2 ⚠️ (write first, ensure they FAIL)

- [ ] T012 [P] [US2] In `tests/commands/graph/test_untyped_vocab.py`, add the Greimas oracle: a character with `greimas` active and `narrative_roles:` containing a bad label + a valid actant; assert one entry `{field: "narrative_roles", vocabulary: "greimas", term: …}` for the bad label only and the role node untyped; add a blank/unsluggable-role case asserting NO warning (edge case; data-model.md §5; FR-007/010, SC-001/006).

### Implementation for User Story 2

- [ ] T013 [US2] In `src/bookwright/io/_bible_builders.py:_build_character`, add an `else:` branch to the existing `if greimas is not None:` loop; GUARD first with `try: make_slug(label) except EmptySlugError: continue` so a blank role mints no warnable node, then on `greimas.resolve(label) is None` append `UntypedVocabTerm(path=relpath, field="narrative_roles", term=label, vocabulary="greimas")` to `result.untyped_vocab_terms` (data-model.md §5; FR-001/003/007; edge case; depends on Phase 2).
- [ ] T014 [US2] Thread `relpath` + `ctx.result` into `_build_character` via the existing `src/bookwright/io/bible.py` character-builder lambda (`meta`, `rp`, and `ctx` are already in scope) — signature + call site only; do NOT touch the outline-unit `roles:`→character-role `_resolve_roles` path that already emits `unresolved_references` (FR-008; depends on T013).

**Checkpoint**: Both closed vocabularies handled uniformly; US1 and US2 both green.

---

## Phase 5: User Story 3 — No active vocabulary leaves everything unchanged (Priority: P2)

**Goal**: A vocabulary-free build is byte-identical to pre-feature output; no warning,
no typing. Plus the determinism guarantee (two builds byte-identical).

**Independent Test**: Build the same project with no active vocabulary; assert empty
`untyped_vocab_terms`, no `crm:P2_has_type`, and a byte-stable envelope; build any
warning-producing project twice and `diff` the envelopes.

### Tests for User Story 3 ⚠️

- [ ] T015 [P] [US3] In `tests/commands/graph/test_untyped_vocab.py`, add the non-regression oracle: build a project with `[vocabularies] active = []` (or absent) over units with `functions:` and characters with `narrative_roles:`; assert `untyped_vocab_terms == []` and no node typed (quickstart Scenario 3; FR-009, SC-005, contract C-5).
- [ ] T016 [P] [US3] In `tests/commands/graph/test_untyped_vocab.py`, add the determinism oracle: build a warning-producing project twice and assert the two `graph build --json` envelopes are byte-identical (entry order + enumerated valid terms) (quickstart Scenario 4; FR-016, SC-008, contract C-6).
- [ ] T017 [P] [US3] In `tests/io/test_vocabularies.py`, add a unit oracle for `VocabularyIndex.terms`: assert it is sorted, deduplicated, includes ES+EN `rdfs:label`s, and is stable across two `load_vocabulary` calls (data-model.md §4; FR-016).

**Checkpoint**: Non-regression and determinism pinned; full story set independently green.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify the whole slice against the gates and the quickstart.

- [ ] T018 [P] Run `tests/commands/graph/test_json_contract.py` / envelope tests and confirm the additive `untyped_vocab_terms` key is always present (C-1) and the `--json` doc on stdout stays sole (Principle IX); confirm T010b's non-`--json` run keeps human prose on stderr only (no stdout pollution); extend the existing contract test if it asserts an exact key set.
- [ ] T019 Run the `quickstart.md` walkthrough end to end (Scenarios 1–4) against a `tiny-quest`-derived project and confirm observed output matches.
- [ ] T020 Run all four gates: `uv run pytest` (≥ 80 % coverage), `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict`; confirm green and every changed file ≤ 500 lines (FR-015, SC-007).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No code dependency — doc reconciliations; do first per zero-debt contract-before-code. T001–T003 parallel.
- **Foundational (Phase 2)**: BLOCKS US1 and US2. T004 and T005 parallel; T006/T007 depend on T004; T008 depends on T006+T007; T009 depends on T007+T005.
- **US1 (Phase 3)**: Depends on Phase 2. T010 (envelope test) before T011; T010b (human-render test) asserts T009's stderr render and depends on T011 producing a warning.
- **US2 (Phase 4)**: Depends on Phase 2. T012 (test) before T013; T014 depends on T013.
- **US3 (Phase 5)**: Depends on Phase 2 (and meaningfully on US1/US2 sites existing to produce warnings to compare); tests T015–T017 parallel.
- **Polish (Phase 6)**: Depends on all user stories complete.

### User Story Dependencies

- **US1 (P1)** and **US2 (P1)** are independent of each other once Phase 2 is done — different typing sites (`outline.py` vs. `_bible_builders.py`/`bible.py`).
- **US3 (P2)** guards the contract; its determinism/non-regression tests assert against the channel built in Phase 2 and the sites from US1/US2.

### Parallel Opportunities

- Phase 1: T001, T002, T003 (different doc files / regions).
- Phase 2: T004 ∥ T005 (report.py vs. vocabularies.py).
- US1 ∥ US2 once Phase 2 lands (Developer A: T010–T011; Developer B: T012–T014).
- US3 tests T015 ∥ T016 ∥ T017.

---

## Parallel Example: Foundational kickoff

```bash
# After Phase 1 docs land, start the two independent model edits together:
Task: "Add UntypedVocabTerm model in src/bookwright/io/report.py"          # T004
Task: "Add VocabularyIndex.terms enumerator in src/bookwright/io/vocabularies.py"  # T005
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Phase 1 (docs) → Phase 2 (channel plumbing) → Phase 3 (Propp site + oracle).
2. **STOP and VALIDATE**: Propp typo surfaces, node still untyped, exit 0.

### Incremental Delivery

1. Setup + Foundational → channel ready.
2. US1 (Propp) → MVP, the dogfood-reported defect closed.
3. US2 (Greimas) → class sweep complete, both vocabularies uniform.
4. US3 → non-regression + determinism pinned.
5. Polish → gates green, quickstart verified.

---

## Notes

- [P] = different files, no incomplete-task dependency.
- The frozen ontology (`golem.ttl`, `propp.ttl`, `greimas.ttl`) is NOT edited (FR-014, Constitution X).
- No new validator, `Severity` value, module, or runtime dependency (FR-005/011/015).
- Reuse `tiny-quest` (Propp) fixture + `copy_fixture`; no new fixture tree needed beyond per-test edits.
- Commit after each task or logical group (auto-git hooks are advisory).
