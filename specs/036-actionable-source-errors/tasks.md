# Tasks: Actionable research-source error messages

**Input**: Design documents from `/specs/036-actionable-source-errors/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/error-messages.md ✅, quickstart.md ✅

**Tests**: INCLUDED — explicitly required by the spec (FR-010, SC-003: both improved
messages must be covered by assertions). Tests live beside the code they exercise
(`tests/io/test_research.py`, `tests/commands/graph/test_query.py`).

**Organization**: grouped by the three user stories (US1 = F1 vocab enumeration,
US2 = F2 per-source locator + FR-011 reconcile, US3 = SPARQL footgun note). US1 and
US2 both edit `src/bookwright/io/research.py` (so they serialize against each other);
US3 edits independent files and can run fully in parallel with both.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: US1 / US2 / US3
- Exact file paths are included in every task

## Path Conventions

Single project, src-layout (Constitution III): `src/bookwright/`, `tests/` at repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a clean, green baseline before touching the loader.

- [X] T001 Confirm the working branch is `036-actionable-source-errors` and capture a green baseline by running `uv run pytest tests/io/test_research.py tests/commands/graph/test_query.py` (no code change — record that the existing `test_out_of_vocabulary_aborts_naming_value` and the success-path tests pass before edits).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None. This iteration is message-content-only; there is no shared schema,
model, or migration to build first. Both P1 stories are independent edits to
`src/bookwright/io/research.py`, and the envelope contract (`ResearchError` in
`src/bookwright/io/errors.py`, exposing `.relpath`/`.message`/`.value`) already exists
unchanged. **No foundational tasks** — proceed directly to the user stories.

**Checkpoint**: Foundation ready (trivially) — user story implementation can begin.

---

## Phase 3: User Story 1 - Out-of-vocabulary `type` tells the author the accepted values (Priority: P1) 🎯 MVP

**Goal**: An out-of-vocabulary `type` or `reliability` error names the offending
value **and** enumerates the complete accepted set in declaration order, so the author
fixes it without leaving the terminal (FR-001/002/003, SC-001).

**Independent Test**: Build (or unit-load) a `sources.md` with `type: primario` and a
separate one with `reliability: altísima`; assert each error contains
`one of: <comma-space list>` equal to `", ".join(SOURCE_TYPE_IRI)` /
`", ".join(RELIABILITY_IRI)` and still names the offending value.

### Implementation for User Story 1

- [X] T002 [US1] In `src/bookwright/io/research.py`, update `_reject_unknown_vocab` (currently lines ~222–233) so both raises append the enumeration: type → `unknown source type {value!r} in {relpath}; one of: {", ".join(SOURCE_TYPE_IRI)}`, reliability → `unknown reliability {value!r} in {relpath}; one of: {", ".join(RELIABILITY_IRI)}`. Keep the existing `value=str(...)` third argument and `relpath` unchanged (envelope byte-stable, FR-007). Derive the enumeration from the imported `SOURCE_TYPE_IRI` / `RELIABILITY_IRI` maps (already imported at line 37) — never a hardcoded copy — so it can never drift (per contract C1).

### Tests for User Story 1

- [X] T003 [US1] In `tests/io/test_research.py`, extend/add assertions on the F1 path (alongside `test_out_of_vocabulary_aborts_naming_value`): assert the `type` error message contains `", ".join(SOURCE_TYPE_IRI)` and the literal substring `one of: primaria, secundaria, oficial, académica, periodística, testimonial`; assert the `reliability` error contains `", ".join(RELIABILITY_IRI)` and `one of: alta, media, baja`; assert the offending value is still present and `code == "invalid_research"`. Compute the expected list from the map itself (drift-proof, contract C1).

**Checkpoint**: US1 fully functional and independently testable. MVP shippable.

---

## Phase 4: User Story 2 - A per-source load error names which source failed (Priority: P1)

**Goal**: Every `ResearchError` raised while processing one source is prefixed with
that source's locator — `source '<name>': ` when the `name` is usable, else
`source #<n>: ` (1-based) — preserving the underlying reason; and the two errors that
already self-named the source inline (translation-rule, duplicate-name) are reconciled
so the source is named **once** (FR-004/005/006/011, SC-002).

**Independent Test**: A `sources.md` with two valid sources + one with a quoted
`access_date` → error starts `source '<name>': ` and still carries
`Input should be a valid date`; a source missing its `name` facet → error starts
`source #<n>: ` with the correct 1-based position; a duplicate name → name once in the
prefix, slug retained in the body; a translation-rule violation → name once.

### Implementation for User Story 2

- [X] T004 [US2] In `src/bookwright/io/research.py`, add a small helper that computes a source's locator `<id>`: return `f"'{name}'"` when `raw["name"]` is a non-empty `str` that `make_slug` accepts (catch `EmptySlugError`), else `f"#{n}"` (1-based loop index). Keep it in `research.py` if the file stays ≤ 500 lines; if it would exceed 500, move it to the existing companion `src/bookwright/io/_research_identity.py` and import it (per plan Structure / Constitution IV).
- [X] T005 [US2] In `src/bookwright/io/research.py`, wrap the `for raw in raw_sources` loop **body** in `_map_sources` (lines ~188–200) in a single `try/except ResearchError`: on catch, compute `<id>` via the T004 helper using the 1-based index and `raw`, then `raise ResearchError(exc.relpath, f"source {id}: {exc.message}", exc.value) from exc`. This is the **single** locator point (FR-004) — covers `_build_source`, vocab, validation, empty-name, duplicate-name, and translation-rule faults uniformly. Do **not** add per-`raise` prefixes anywhere else.
- [X] T006 [US2] In `src/bookwright/io/research.py`, apply the FR-011 reconciliation so no message names the same source twice: in `_apply_translation_rule` (lines ~244–249) change the inner message to `needs a translation (language {source.original_language!r} ≠ book {acc.book_language!r}) in {relpath}` (drop the leading `source {source.name!r}`); in the duplicate-name raise in `_map_sources` (lines ~194–198) change it to `duplicate source name (slug {slug!r}) in {relpath}` (drop the human `{source.name!r}`, **retain** the `slug` as the semantic subject). Leave the `value=` arguments as-is.

### Tests for User Story 2

- [X] T007 [US2] In `tests/io/test_research.py`, add F2 named-source case: a `sources.md` with ≥2 valid sources and one named source whose `access_date` is quoted (`"1937-04-26"`); assert the error `message` starts with `source '<name>': ` **and** still contains the pydantic reason `Input should be a valid date` (FR-006), with `code == "invalid_research"` and `details` keys `relpath`, `value` unchanged (contract C2/C5).
- [X] T008 [US2] In `tests/io/test_research.py`, add F2 index-fallback case: a source that fails before a usable `name` is available (drop the `name` facet, or make it empty/unsluggable); assert the error `message` starts with `source #<n>: ` carrying the correct 1-based position (edge cases: empty/unsluggable name → index; failure before name read → index).
- [X] T009 [US2] In `tests/io/test_research.py`, add FR-011 single-locator cases: (a) duplicate name → assert `source '<name>':` appears exactly once and the body contains `slug '<slug>'`; (b) translation-rule violation (book language ≠ source language, no translation) → assert `source '<name>': needs a translation (language 'fr' ≠ book 'es')` with the name appearing exactly once (contract C3).

**Checkpoint**: US1 AND US2 both work independently; DEBT-006's two blinding messages are fixed.

---

## Phase 5: User Story 3 - The SPARQL empty-result footgun is documented (Priority: P3)

**Goal**: Both the `graph query` command help (English, in-product) and the
`docs/commands/graph-query.md` page (Spanish) carry a note that a query referencing a
non-existent / misspelled IRI returns an empty result set, not an error (FR-008,
SC-004). **No** IRI validation is added (out of scope).

**Independent Test**: `uv run bookwright graph query --help` shows the English note;
the docs page contains the Spanish note.

### Implementation for User Story 3

- [X] T010 [P] [US3] In `src/bookwright/commands/graph/query.py`, extend the `sparql` `typer.Argument` `help=` string (line ~37) with an English note that a query referencing a non-existent / misspelled IRI returns an empty result set, not an error (combine `non-existent`/`misspelled` + `IRI` + `empty`/`zero` result + `not an error`, per contract C4).
- [X] T011 [P] [US3] In `docs/commands/graph-query.md`, add a short Spanish note with the same meaning (e.g. *"un IRI inexistente o mal escrito devuelve cero resultados, no un error"*) — language conventions: docs stay Spanish.

### Tests for User Story 3

- [X] T012 [US3] In `tests/commands/graph/test_query.py`, add a test asserting the `graph query --help` output (English) contains the empty-result-for-unknown-IRI note substring; and a test (or docs-content check reading `docs/commands/graph-query.md`) asserting the Spanish note is present (contract C4).

**Checkpoint**: All three user stories independently functional and verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Discharge the remaining FR/SC obligations and prove no regression.

- [X] T013 Confirm `src/bookwright/io/research.py` is ≤ 500 lines (`wc -l`); if T004 pushed it over, the helper must already have moved to `src/bookwright/io/_research_identity.py` (Constitution IV) — verify it did.
- [X] T014 Remove the DEBT-006 entry (line ~52) from `DEBT.md` (FR-009/SC-006); verify `grep -c DEBT-006 DEBT.md` → 0.
- [X] T015 Run `specs/036-actionable-source-errors/quickstart.md` scenarios 1–5 end to end and confirm each expected substring appears (F1 enumeration, F2 named + index prefixes, FR-011 single locator, SPARQL note, non-regression).
- [X] T016 Run the four gates green (the exit bar, SC-005): `uv run pytest` (≥80% coverage), `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict`. Confirm the error JSON envelope stayed byte-compatible (`status`/`code=invalid_research`/`details={relpath,value}`).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — run first to capture the baseline.
- **Foundational (Phase 2)**: empty — nothing blocks the stories.
- **User Stories (Phase 3–5)**: US1 and US2 both edit `research.py`, so do US1 then US2 (or interleave carefully) — they are not [P] against each other. US3 edits `query.py` + docs + `test_query.py` only, so US3 is fully [P] against US1/US2.
- **Polish (Phase 6)**: depends on all stories being complete.

### User Story Dependencies

- **US1 (P1)**: independent. MVP.
- **US2 (P1)**: independent of US1 in behaviour, but shares the file `research.py` — sequence after US1 to avoid edit conflicts.
- **US3 (P3)**: fully independent (different files) — can be done any time, in parallel.

### Within Each User Story

- US1: T002 (impl) → T003 (test).
- US2: T004 (helper) → T005 (wrap) → T006 (FR-011 reconcile) → T007/T008/T009 (tests).
- US3: T010 & T011 in parallel → T012 (test).

### Parallel Opportunities

- US3 (T010, T011, T012) runs entirely in parallel with US1/US2 — different files.
- T010 [P] and T011 [P] (query help vs docs page) run together.
- Within US2, the three test tasks T007/T008/T009 touch the same test file — sequence or merge to avoid conflicts.

---

## Parallel Example

```bash
# US3 can proceed alongside the research.py work (no shared files):
Task: "Add English empty-result note to the sparql help in src/bookwright/commands/graph/query.py"   # T010
Task: "Add Spanish empty-result note to docs/commands/graph-query.md"                                 # T011
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 baseline → 2. T002/T003 (F1 enumeration) → 3. validate US1 independently. F1 alone is a shippable improvement.

### Incremental Delivery

1. Baseline → 2. US1 (F1) → 3. US2 (F2 + FR-011) — DEBT-006's two error fixes complete → 4. US3 (docs note) → 5. Polish (remove DEBT-006, gates). Ships as `v0.4.4`.

---

## Notes

- [P] = different files, no dependency. US1/US2 share `research.py`; only US3 is [P] against them.
- Message content only: no schema, vocabulary, error code, or envelope change (FR-007).
- The `ResearchError` envelope (`code=invalid_research`, `details={relpath, value}`) is byte-stable — every enriched message reuses `exc.relpath`/`exc.value`.
- Commit after each logical group; the four gates (T016) are the hard exit bar.
