---
description: "Task list for iteration 029 — outline ingestion of narrative sequences (G7)"
---

# Tasks: Outline ingestion — narrative sequences (G7)

**Input**: Design documents from `/specs/029-narrative-sequences/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/sequence-ingestion.md, quickstart.md

**Tests**: Tests ARE requested — the spec mandates `tests/io/test_outline_sequences.py`
(five sequence-assembly scenarios), a parity flip, and a materialize check. Test
tasks are included and written before their implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete-task dependency)
- **[Story]**: US1 / US2 / US3 (Setup, Foundational, Polish carry no story label)
- Every task names an exact file path

## Path Conventions

Single project, src-layout: `src/bookwright/`, tests at repo root under `tests/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm a green baseline so every later delta is attributable.

- [ ] T001 Confirm the working tree is on branch `029-narrative-sequences` and the
  four gates are green at baseline: `uv run ruff check && uv run ruff format --check
  && uv run mypy --strict && uv run pytest` (records the pre-change state US2's
  byte-for-byte claim is measured against).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The recognised-key widening and the transient member record both
US1 (engine) and US2 (parity/fixture) build on. No ontology or model edit —
`golem/` stays frozen and untouched (Principle X, plan Constitution Check).

**⚠️ CRITICAL**: These two edits land before the assembly logic and the parity flip.

- [ ] T002 [P] Widen `UNIT_KEYS` to `frozenset({"name", "functions", "roles",
  "sequence", "order"})` in `src/bookwright/io/outline.py` and update the
  accompanying comment so any other key remains a soft `unknown_keys` warning
  (FR-001, data-model §Recognised keys). Adding the keys must NOT change any
  existing fixture's warning set (no current card carries them — D9).
- [ ] T003 [P] Add the transient `_SeqMember` `NamedTuple` (fields `seq_slug:str`,
  `seq_name:str`, `order:int|None`, `unit_slug:str`, `unit:NarrativeUnit`,
  `relpath:str`) to `src/bookwright/io/outline.py`, with a docstring stating it is
  internal/never serialized (data-model §Transient record).

**Checkpoint**: Keys recognised and the member record type exists — engine work can begin.

---

## Phase 3: User Story 1 - Plot beat order becomes queryable (Priority: P1) 🎯 MVP

**Goal**: Each distinct `sequence` name becomes exactly one `NarrativeSequence`
entity whose `dlp:proper-part` members are the naming units, ordered ascending by
`order` (missing/duplicate `order` resolved deterministically by slug).

**Independent Test**: Three `outline/units/*.md` cards, two with `sequence: Act I`
(`order: 1`/`order: 2`) and one with no `sequence`; build the graph; confirm exactly
one `NarrativeSequence` "Act I" with two ordered `dlp:proper-part` members and the
third unit in no sequence.

### Tests for User Story 1 (write first, ensure they FAIL) ⚠️

- [ ] T004 [US1] Create `tests/io/test_outline_sequences.py` covering the five
  quickstart scenarios against `map_outline` (or the assembly seam): (A) three
  ordered beats → one `Act I` sequence with member tuple `(Beat A, Beat B, Beat C)`
  in ascending `order` (SC-001/002/003); (C) duplicate `order: 1` on `"Zeta Beat"`
  /`"Alpha Beat"` → member tuple `(Alpha Beat, Zeta Beat)` by slug tie-break and
  identical across two builds (FR-006/SC-004); (D) single-member `Coda` sequence →
  one `dlp:proper-part` edge (US1 accept #2/#3); plus a missing-`order` case → the
  order-less member placed last, slug-ordered among order-less peers (FR-005). Assert
  on the **builder's `units` tuple order**, not RDF triple order (contract §2).
  Verify these tests FAIL before T005–T009.

### Implementation for User Story 1

- [ ] T005 [US1] Add `_coerce_sequence(value) -> str | None` to
  `src/bookwright/io/outline.py`, mirroring `_resolve_setting`: `None`/blank/
  whitespace → `None` (no membership, FR-004); non-string → `InvalidFrontmatterError`
  (card skipped, FR-007). (research D6, data-model §Validation.)
- [ ] T006 [US1] Add `_coerce_order(value) -> int | None` to
  `src/bookwright/io/outline.py`, mirroring `_coerce_year`: absent/`None` → `None`
  (FR-005); non-int incl. `bool`/float/str/list → `InvalidFrontmatterError` (card
  skipped, FR-007 — booleans MUST NOT be accepted as integers). Do NOT refactor the
  shared `_coerce_year` in `_bible_builders.py` (research D6, scope discipline).
- [ ] T007 [US1] Add `_member_sort_key(m: _SeqMember) -> tuple[int, int, str]` to
  `src/bookwright/io/outline.py` returning `(0, m.order, m.unit_slug)` when `order`
  is set and `(1, 0, m.unit_slug)` when `None` — a total order so the member tuple is
  byte-for-byte stable across builds (FR-005/FR-006, data-model §Member ordering, D2/D3).
- [ ] T008 [US1] Extend `_build_unit` in `src/bookwright/io/outline.py` to capture a
  `_SeqMember` into a caller-supplied accumulator: run `_coerce_sequence` and
  `_coerce_order` in the **up-front raising block** (with `_require_name`,
  `make_slug`, `_coerce_str_list`) BEFORE any state mutation so an unusable
  `sequence`/`order` skips the card with no partial membership and no stray note
  (skip-invariant, research D7); append the `_SeqMember` LAST, after the
  `NarrativeUnit` is built, only when a usable `sequence` is present; when `order` is
  usable but `sequence` is absent/blank, ignore the `order` and append a soft
  `UnknownKey(path=relpath, key="order")` (FR-008, research D8). Thread the
  accumulator via the builder lambda's closure (a `list` local to `map_outline`,
  research D1) — keep `_MapContext` free of an outline-only field.
- [ ] T009 [US1] Add the assembly step to `map_outline` in
  `src/bookwright/io/outline.py`, run AFTER `_map_single_dir` returns (the "second
  step", research D1): group the collected `_SeqMember`s by `seq_slug` into an
  insertion-ordered dict (insertion = sorted-glob order → deterministic); for each
  group, `ordered = sorted(group, key=_member_sort_key)`, `name = group[0].seq_name`
  (first card in glob order to name the slug, D4), `units = tuple(m.unit for m in
  ordered)`, construct `NarrativeSequence(uri_base=…, name=name, units=units)`, and
  append `MappedEntity(entity=seq, relpath=ordered[0].relpath, key_lines={})` to
  `result.mapped` — file-level provenance via the existing `build_provenance` →
  `crm:E13_Attribute_Assignment` path (FR-002/003/010, research D5). Empty
  accumulator → no groups → nothing appended (FR-011).

**Checkpoint**: `uv run pytest tests/io/test_outline_sequences.py` green; G7 is now
produced by the engine. US1 is independently functional.

---

## Phase 4: User Story 2 - Existing/unsequenced projects unchanged (Priority: P1)

**Goal**: A project with no `sequence` key builds byte-for-byte the pre-feature
graph (zero `NarrativeSequence`); the parity guard observes G7 alive against a real
build and the orphan set drops to `{RelationshipRole, PsychologicalState}`.

**Independent Test**: Build a project whose unit cards declare no `sequence`; confirm
the graph is identical to the pre-feature build with zero `NarrativeSequence`
entities; run the parity test green with `len(DEFERRED_CONCEPTS) == 2`.

### Tests for User Story 2 (write/adjust first) ⚠️

- [ ] T010 [US2] Add the no-sequence scenario (quickstart Scenario E / B) to
  `tests/io/test_outline_sequences.py`: units present, none with `sequence` → zero
  `NarrativeSequence` entities and a card's iteration-028 triples unchanged
  (FR-004/FR-011, SC-006). Confirm it FAILS only if assembly wrongly mints on an
  unsequenced unit.
- [ ] T011 [US2] Update `tests/golem/test_ingestion_parity.py` for the G7 flip
  (FR-013, research D10): move `"NarrativeSequence"` from `ORPHAN_NAMES` into
  `EXPECTED_REACHABLE`; drop its `EXPECTED_VERSIONS` key; change
  `len(DEFERRED_CONCEPTS) == 3` → `== 2`; update the module docstring count prose
  ("Ten of the thirteen … the other three" → "Eleven of the thirteen … the other
  two") and the reachable-set/orphan comments. Leave the three drift probes
  (`Character`, `NarrativeEvent`, `PsychologicalState`) UNCHANGED and confirm by
  inspection they name no now-fed concept (FR-013).

### Implementation for User Story 2

- [ ] T012 [US2] Edit `src/bookwright/golem/deferrals.py` (FR-013): remove the
  `"NarrativeSequence"` entry from `DEFERRED_CONCEPTS`; update the module docstring
  count prose ("Three of the thirteen" → "Two of the thirteen") and the trailing
  doc-comment ("Exactly three entries" → "Exactly two entries"). The remaining two
  entries (`RelationshipRole` G6, `PsychologicalState` G3) stay (Out of Scope: 032).
- [ ] T013 [US2] Edit the `parity-exercise` fixture so the live build observes G7
  (FR-014, research D11): add `sequence`/`order` to
  `tests/fixtures/parity-exercise/outline/units/opening.md` and add one more card in
  the same `outline/units/` directory sharing that `sequence` with a later `order`, so
  the build emits a `NarrativeSequence` `rdf:type` IRI with two ordered members.

**Checkpoint**: `uv run pytest tests/golem/test_ingestion_parity.py` green with G7
fed; backward-compat scenario green. US1 + US2 both hold.

---

## Phase 5: User Story 3 - Authoring surface guides sequence/order (Priority: P2)

**Goal**: The `bookwright-outline` skill instructs the optional `sequence`/`order`
unit keys (in both in-file enumerations), bilingual-safe, re-materialized for
`claude` and `generic`.

**Independent Test**: Materialize integrations; the regenerated `bookwright-outline`
`SKILL.md` (both targets) documents the optional keys in both enumerations and still
triggers on ES/EN prompts (passes `lint_skill_md`).

### Tests for User Story 3 ⚠️

- [ ] T014 [US3] Confirm/extend `tests/integrations/test_materialize.py` stays green
  on the edited source command and, if it asserts on `bookwright-outline` content,
  add an assertion that the regenerated `SKILL.md` mentions the `sequence`/`order`
  keys and still carries its ES/EN triggers (FR-012, SC-008).

### Implementation for User Story 3

- [ ] T015 [US3] Edit `src/bookwright/resources/commands/bookwright-outline.md`
  (FR-012, Spanish prose to match the file): document, on a unit card, the two
  additional optional keys `sequence` (the plot line a unit belongs to) and `order`
  (its position in that line) in **both** enumerations — the per-unit "what to
  create" instruction AND the "Archivos a escribir" summary that today reads
  `name`/`functions`/`roles` — so neither still claims only the iteration-028 trio.

**Checkpoint**: `uv run pytest tests/integrations/test_materialize.py` green; skill
documents the new keys.

---

## Phase 6: Polish & Cross-Cutting Concerns — present-tense docs sweep (FR-015)

**Purpose**: Sweep every present-tense statement that still calls G7 unfed or lists
`outline/units/` as carrying/feeding only the 028 trio (FR-015, SC-009). This is a
debt class swept in full, not one edit. Version-scoped historical/planning records
(roadmap, README "Planificado: v0.4", implementation-plan ledger) are deliberately
NOT touched.

- [ ] T016 [P] Update `src/bookwright/io/outline.py` module docstring (and the
  `map_outline` docstring) so it states the pass also assembles `NarrativeSequence`
  (G7) from the unit cards' `sequence`/`order` keys — no longer "G9/G10 only"
  (FR-015(implied)/SC-009).
- [ ] T017 [P] Update the `src/bookwright/io/manuscript.py` module docstring: the
  `outline/units/` cards now also drive `NarrativeSequence`, not only
  `NarrativeUnit`/`NarrativeFunction` (FR-015(d), SC-009).
- [ ] T018 [P] Update `bookwright-design.md` § 7.4 (Spanish): G7 now ingests
  unit-driven from `outline/units/` (no separate directory); add `sequence`/`order`
  to the documented unit front-matter keys; remove the present-tense "las secuencias
  narrativas G7 … siguen aplazadas" — mirror how § 7.2/§ 7.3 documented the
  locations/objects precedents (FR-015(c), SC-009).
- [ ] T019 [P] Update `docs/authoring.md`: the v0.4 note "alimentan unidades y
  funciones narrativas" gains "y secuencias" (FR-015(e), SC-009).
- [ ] T020 Run the full validation: `uv run ruff check && uv run ruff format --check
  && uv run mypy --strict && uv run pytest`, then walk quickstart.md Scenarios A–E and
  the skill-surface check; confirm SC-009's negative search (no remaining present-tense
  "G7 unfed" / "trio-only" statement in the swept surfaces) returns clean.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: after Setup. T002/T003 are [P] (independent edits, same
  file — sequence them if applied as raw patches). BLOCKS US1 and US2.
- **US1 (Phase 3)**: after Foundational. The engine; co-equal P1 with US2 but US2's
  parity flip (T011) only goes green once US1 produces G7.
- **US2 (Phase 4)**: after Foundational; its parity-test/fixture flip (T011/T013)
  requires the US1 engine (T009) to actually emit `NarrativeSequence`.
- **US3 (Phase 5)**: after Foundational; independent of US1/US2 engine (docs/skill
  only) — can proceed in parallel with US1 once Foundational lands.
- **Polish (Phase 6)**: after US1–US3 (the docstring/design/authoring claims it
  rewrites describe the now-shipped behaviour).

### Within Each User Story

- Tests written and failing before implementation (T004 before T005–T009; T010 before
  its assembly already exists from US1 — confirm it captures the no-mint guarantee).
- In US1: coercers (T005/T006) and the sort key (T007) before `_build_unit` capture
  (T008); capture before assembly (T009).
- In US2: registry/fixture edits (T012/T013) before the parity test goes green; the
  test edit (T011) lands with them.

### Parallel Opportunities

- T002 / T003 conceptually parallel (Foundational).
- T005, T006, T007 are independent helpers in `outline.py` — author together, though
  they share a file.
- US3 (T014/T015) runs in parallel with US1/US2 once Foundational is done.
- Polish T016–T019 are all [P] (distinct files).

---

## Parallel Example: Foundational + early US1

```bash
# Foundational edits (same file — apply in sequence if patching raw):
Task T002: "Widen UNIT_KEYS in src/bookwright/io/outline.py"
Task T003: "Add _SeqMember NamedTuple in src/bookwright/io/outline.py"

# US3 can start alongside US1 once Foundational lands:
Task T015: "Edit src/bookwright/resources/commands/bookwright-outline.md"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup → Phase 2 Foundational (UNIT_KEYS + `_SeqMember`).
2. Phase 3 US1: tests first (T004), then coercers/sort-key/capture/assembly.
3. **STOP and VALIDATE**: `pytest tests/io/test_outline_sequences.py` green — G7 is
   alive end-to-end. This is the deliverable core.

### Incremental Delivery

1. US1 → queryable ordered sequences (MVP).
2. US2 → parity flip + backward-compat fixture/test (the release gate).
3. US3 → authoring-surface guidance.
4. Polish → present-tense docs sweep + full-gate validation.

---

## Notes

- `golem/` is untouched: `NarrativeSequence` + its `units`/`dlp:proper-part`
  cross-ref already exist (data-model). This iteration only supplies the ordered
  member tuple. No ontology edit (Principle X), no new CLI subcommand (Principle IV).
- Determinism (SC-003/SC-004) rests on three things together: sorted-glob iteration,
  the total `_member_sort_key`, and insertion-ordered grouping — verify all three in
  T009.
- Out of scope and explicitly NOT touched: `E55_Type` tagging (030), continuity
  validators (031), the G6/G3 re-target (032), and version-scoped historical records.
