---
description: "Task list for the factual_anchor validator (iteration 014)"
---

# Tasks: `factual_anchor` Validator

**Input**: Design documents from `/specs/014-factual-anchor-validator/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅ (D1–D9), data-model.md ✅,
contracts/factual-anchor-validator.md ✅, quickstart.md ✅

**Tests**: REQUESTED. SC-006 mandates a unit suite covering each violation kind plus
the clean / inert / no-research cases, and FR-011 requires the existing
`test_temporal.py` to stay green as the behaviour-preservation oracle for the
extraction. Test tasks are therefore first-class, not optional.

**Organization**: by user story (P1 → P2 → P3), each independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable — different file, no dependency on an incomplete task.
- **[Story]**: US1 / US2 / US3 (Setup, Foundational and Polish carry no story label).
- Paths are repo-root-relative (single project, src-layout).

## Quality & Zero-Debt Guardrails (apply to every task)

These are the directive's "máxima calidad, deuda técnica nula" invariants. A task is
not done if it breaks one:

- **One source of truth for interval contradiction (FR-011).** `intervals_disjoint`
  is the *only* place that decides "two year ranges provably do not overlap";
  `temporal` and `factual_anchor` both call it. No second disjoint check anywhere.
- **One year parser.** `parse_gyear` (the promoted `_parse_year`) is the only gYear
  coercion; `load_anchors` reuses it, never re-parses.
- **Reliability scale is sourced from the ontology**, not re-spelled: the rank map is
  *derived by inverting* `golem.namespaces.RELIABILITY_IRI` (D6).
- **The mandatory-facet membership has one source: `provenance.Source.to_triples()`**
  (D5). The validator's facet tuple is built from the `golem.namespaces` predicate
  constants (the single source of the IRIs) and a **drift-guard test** asserts its
  predicate set equals a fully-populated `Source.to_triples()` emission. It is **not**
  aligned to `io/research._SOURCE_FACETS` — that tuple is field-names (includes `name`,
  omits `translation`), a different representation that must not be treated as a co-source.
- **Research defaults come from the manifest model**, not hardcoded literals in the
  validator: read `project.manifest.research.{enabled,min_reliability_for_anchor}`
  and let the `[research]` Pydantic model supply the documented defaults (FR-014).
- **No new dependency, no new GOLEM class, no CLI/manifest schema change** (Const. II,
  X; FR-005, FR-017). Every touched/new file stays ≤ 500 lines (Principle IV).
- **Pure & deterministic** (FR-003): no disk write, no network, no LLM, no graph
  mutation; iterate anchors and sources in sorted-URI order so output is byte-stable.
- **Violation locations come from `resolve_source`, never hardcoded** (D7, FR-013).
  Every emitted `Violation` sets `source=resolve_source(indexer, anchor_uri)` — today
  that returns `None` for anchors (iteration 12 emits no anchor locator), but writing
  it this way means locations light up automatically if anchor provenance is added
  later. Do **not** hardcode `source=None`. Consequence (SC-005): because anchor
  violations are location-less, a `--scope <path>` run reports **zero** `factual_anchor`
  violations — that is the correct, tested behaviour (like `temporal`'s location-less
  findings), not a regression.

---

## Phase 1: Setup

**Purpose**: pin the known-good baseline the FR-011 refactor must preserve.

- [X] T001 Establish the green baseline: run `uv run pytest tests/validation/`,
  `uv run ruff check`, `uv run ruff format --check`, and `uv run mypy --strict`, and
  confirm all pass — in particular `tests/validation/test_temporal.py` (including
  `test_open_interval_is_handled`, the disjoint-range oracle). Record that this is the
  behaviour the `intervals_disjoint` extraction in US2 must reproduce exactly. No code
  change in this task.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: shared substrate every user story needs — the anchor projection, the
discoverable inert-correct validator skeleton, and the research-aware test builder.

**⚠️ CRITICAL**: No user-story rule can be implemented until this phase is complete.

- [X] T002 [P] Add a research-aware graph builder to
  [tests/validation/conftest.py](../../tests/validation/conftest.py): a helper (e.g.
  `research_graph(...)`) that builds an `RdflibIndexer` by adding `bw:`/`crm:` triples
  directly (hand-built graph — defense-in-depth per spec edge cases), parametrized to
  emit an anchor with `BW_PROMOTES`→finding, optional `BW_SUPPORTED_BY`→source(s) with
  a selectable subset of the mandatory facet predicates, a selectable
  `bw:reliability`, an optional/absent `bw:constrains` target, and an optional
  `HAS_TIME_SPAN`→`E52_Time-Span` with `BEGIN_OF_BEGIN`/`END_OF_END`. Reuse the
  namespace constants from `golem.namespaces`; do not hardcode IRI strings.
- [X] T003 Promote the gYear parser in
  [src/bookwright/validation/queries.py](../../src/bookwright/validation/queries.py):
  rename `_parse_year` → `parse_gyear`, add it to `__all__`, and widen its docstring
  from "for the `temporal` validator" to "for the `temporal` and `factual_anchor`
  validators". Pure rename — behaviour unchanged; both internal call sites updated.
- [X] T004 Create
  [src/bookwright/validation/anchor_queries.py](../../src/bookwright/validation/anchor_queries.py)
  with the frozen `AnchorRecord` dataclass `(uri, promotes, constrains: str|None,
  span: EventInterval)` and `load_anchors(indexer) -> list[AnchorRecord]`: one record
  per anchor node, `constrains=None` when no `bw:constrains` triple exists, `span`
  read from `HAS_TIME_SPAN`→`E52_Time-Span` (`P82a`/`P82b`) into the reused
  `EventInterval` via `parse_gyear`, `(None, None)` when no span. Returned in sorted
  URI order. SPARQL only here — no reasoning. (depends T003)
- [X] T005 Create
  [src/bookwright/validation/validators/factual_anchor.py](../../src/bookwright/validation/validators/factual_anchor.py)
  with the `FactualAnchor` class: `name = "factual_anchor"`, `severity_default =
  Severity.warning` (FR-002), and `validate(project, indexer)` that (a) reads
  `project.manifest.research` and early-returns `[]` when `research.enabled is False`
  (FR-015, D8), (b) calls `load_anchors` and early-returns `[]` when empty (FR-016,
  D8), and (c) iterates anchors in sorted order dispatching to rule methods that
  initially return `[]`, collecting `Violation`s. No rules yet. This makes the
  validator auto-discovered by `registry._discover_builtins()` (FR-004) and
  inert-correct. (depends T004)

**Checkpoint**: `factual_anchor` appears in `bookwright validate` `ran[]`, is inert on
non-research / disabled-research projects, and emits nothing — verified later by US3.

---

## Phase 3: User Story 1 — Audit structural integrity of anchors (Priority: P1) 🎯 MVP

**Goal**: emit a **warning** for each anchor that is unsourced (R1/FR-006),
provenance-incomplete (R2/FR-007, one per facet), under-reliable (R3/FR-008), or
constrains a missing entity (R4/FR-009); stay silent on a well-formed anchor.

**Independent Test**: hand-build a graph with one well-formed anchor and one each of
unsourced / provenance-incomplete / under-reliable / missing-entity; run the
validator and confirm exactly the three malformed anchors warn (with the right
facet/reason) and the well-formed one is silent. No anachronism logic needed.

- [X] T006 [P] [US1] Create
  [tests/validation/test_factual_anchor.py](../../tests/validation/test_factual_anchor.py)
  with the US1 cases (write first; they MUST fail before T008–T011): unsourced anchor
  → 1 warning; source missing N facets → N distinct warnings each naming its facet,
  with `translation` flagged only when source language ≠ `book.language`; mixed-
  reliability support judged by the **best** source; an **unrated** source flagged
  once by R2 and **never** double-labelled under R3 (clarification); no rated source
  → under-reliable; dropped-`constrains` and dangling-URI both → missing-entity;
  promoted finding absent → missing-entity **only** (R1 suppressed — assert a single
  warning, not also unsourced; clarification 2026-06-04); and a fully well-formed
  anchor → **zero** violations (SC-001). Uses the T002 builder. **Plus a drift-guard test** (D5): assert
  the T007 mandatory-facet predicate set equals the predicate set emitted by a
  fully-populated `provenance.Source.to_triples()` (translation included) — so the facet
  membership cannot silently diverge from the `Source` model.
- [X] T007 [P] [US1] Extend
  [src/bookwright/validation/anchor_queries.py](../../src/bookwright/validation/anchor_queries.py)
  with the source/presence projections: reach `anchor —bw:promotes→ finding
  —bw:supportedBy→ source`, returning per-anchor the supporting source URIs, each
  source's present facet predicates, its `bw:originalLanguage` literal, its
  `bw:reliability` name (resolved by inverting `RELIABILITY_IRI`), and an
  `entity_present(indexer, uri)` check (uri is the subject of ≥1 triple, or is
  `timeline_uri(...)`) for FR-009. Define the mandatory facet→predicate tuple **once**
  here from the `golem.namespaces` predicate constants (D5); the single source of
  *membership* is `provenance.Source.to_triples()`, pinned by the T006 drift-guard test
  — do **not** source it from `io/research._SOURCE_FACETS` (field-names, not predicates:
  includes `name`, omits `translation`). SPARQL only. (depends T004)
- [X] T008 [US1] Implement rule **R1 unsourced** (FR-006) in `factual_anchor.py`: when
  the promoted finding **exists in the graph** and has no `bw:supportedBy` source, emit
  one `warning` naming the anchor, `triples=((anchor, bw:promotes, finding),)`
  (data-model V1). **Suppress** R1 when the promoted finding is absent from the graph —
  that case is reported once by R4 (T011), never double-labelled as unsourced
  (clarification 2026-06-04). (depends T007)
- [X] T009 [US1] Implement rule **R2 provenance-incomplete** (FR-007) in
  `factual_anchor.py`: for each supporting source, emit **one warning per missing
  mandatory facet**, each naming the source and facet; `translation` is mandatory only
  when the source's `bw:originalLanguage` ≠ `manifest.book.language` (D5, edge case).
  Uses the T007 facet tuple — does not re-list facets. The missing facet is named in
  `message`; `triples=((finding, bw:supportedBy, source),)` — the existing edge that
  locates the source, **never** a fabricated triple with an empty object (V2). (depends T008)
- [X] T010 [US1] Implement rule **R3 under-reliable** (FR-008) in `factual_anchor.py`:
  derive `_RELIABILITY_RANK` by inverting `RELIABILITY_IRI` (`baja<media<alta`),
  compute the **max** rank over **rated** supporting sources, and warn once when it is
  strictly below `rank(manifest.research.min_reliability_for_anchor)` **or** when no
  supporting source is rated (D6). An unrated source contributes nothing here and is
  not double-labelled (clarification). (depends T009)
- [X] T011 [US1] Implement rule **R4 missing-entity** (FR-009) in `factual_anchor.py`:
  warn when the promoted finding URI is absent from the graph, and warn when the
  anchor has no `bw:constrains` triple (dropped link) **or** names a target absent
  from the graph; the `timeline_uri(...)` target counts as present (D4). `triples`
  carries the `bw:constrains` edge when a target exists, else the `bw:promotes` edge
  (V4). (depends T010)

**Checkpoint**: the US1 suite (T006) is green; the MVP — deterministic structural
audit — works end to end and is shippable on its own.

---

## Phase 4: User Story 2 — Catch anchors that clash with the timeline (Priority: P2)

**Goal**: emit a hard **error** when an anchor's time-span and the interval of the
event (or timeline) it constrains are provably disjoint (R5/FR-010), **reusing** the
temporal validator's interval reasoning (FR-011) — the iteration's zero-debt core.

**Independent Test**: hand-build an anchor whose span is disjoint from its constrained
event's interval → **error**; a chronologically-consistent anchor → no error; a
time-spanned anchor constraining a non-temporal target (a character) → no error
(FR-012). Plus unit tests for `intervals_disjoint` and `load_timeline_bounds`, and
confirmation that `test_temporal.py` is still green after the rewire.

- [X] T012 [P] [US2] Create
  [tests/validation/test_queries.py](../../tests/validation/test_queries.py)
  unit-testing `intervals_disjoint` (disjoint in each direction → True;
  overlapping/touching → False; any open bound → False, never forces disjointness) and
  `load_timeline_bounds` (min-begin/max-end over events; both `None` when no event
  carries years), and extend
  [tests/validation/test_factual_anchor.py](../../tests/validation/test_factual_anchor.py)
  with R5 cases (disjoint span↔event → 1 `error` with the implicated triples;
  consistent → none; non-temporal target → none, FR-012; **event target that carries no
  year (absent from `load_intervals`) → none**, FR-012; open-ended span compares only
  the present bound; timeline target via overall bounds). Write first; MUST fail.
- [X] T013 [US2] Add `intervals_disjoint(a: EventInterval, b: EventInterval) -> bool`
  to [src/bookwright/validation/queries.py](../../src/bookwright/validation/queries.py)
  (exact predicate in research D1; open bounds never force disjointness) and add it to
  `__all__`. This is the single source of truth for interval contradiction (FR-011).
- [X] T014 [US2] Rewire the overlap-disjoint branch of `Temporal._numeric`
  ([src/bookwright/validation/validators/temporal.py](../../src/bookwright/validation/validators/temporal.py#L196-L213))
  so the **disjointness decision** is made by `intervals_disjoint` (the FR-011 single
  source of truth for the *decision*). The two directional `<` comparisons stay **only**
  to select which of the two distinct messages to emit — that is formatting, not a
  second contradiction check (D1). **Preserve both messages byte-for-byte**; do not
  collapse them into one. Re-run `tests/validation/test_temporal.py` and confirm it
  stays green — the behaviour-preservation proof for FR-011. (depends T013)
- [X] T015 [US2] Add `load_timeline_bounds(indexer) -> EventInterval` to
  [src/bookwright/validation/queries.py](../../src/bookwright/validation/queries.py) —
  a thin reduction over `load_intervals` returning `(min begin, max end)` across every
  `G5_Narrative_Event`, both bounds `None` when none carries years (D3) — and add it to
  `__all__`. No new interval reasoning.
- [X] T016 [US2] Implement rule **R5 anachronism** (FR-010/FR-012) in
  `factual_anchor.py`: only when the anchor carries a span, resolve `bw:constrains` —
  a `G5_Narrative_Event` → its `load_intervals` interval (an event **absent** from the
  `load_intervals` map because it carries no year → no comparable interval, emit nothing,
  FR-012); `timeline_uri(...)` → `load_timeline_bounds`; any other/absent target → no
  comparable interval, emit nothing (no false positive) — and emit one `error` when `intervals_disjoint(span,
  target_interval)` is True, message naming both ranges, `triples=((anchor,
  bw:constrains, target),)` (V5). (depends T013, T015)

**Checkpoint**: T012 green; `test_temporal.py` still green; `--severity error` keeps
only the anachronism and drops the structural warnings (US2 scenario 4).

---

## Phase 5: User Story 3 — Zero-config discovery, cost-free off-research (Priority: P3)

**Goal**: verify the validator plugs in with no wiring, obeys `[validators]`
enable/disable, reads `[research]` correctly, and is inert on non-research /
research-disabled projects. The behaviour was implemented in Foundational (T005); this
story pins it and removes any hardcoded default.

**Independent Test**: on a no-research project the validator runs and emits zero
violations; under `[validators].disabled=["factual_anchor"]` it does not appear in
`ran[]`; under an `[validators].enabled` allow-list including it, it runs; with
`[research].enabled=false` on a project that *has* anchors it emits zero violations.

- [X] T017 [P] [US3] Add the discovery/selection/inert tests to
  [tests/validation/test_factual_anchor.py](../../tests/validation/test_factual_anchor.py):
  `factual_anchor` is auto-discovered (present in `discover_validators`/`ran[]`),
  honored by `[validators].disabled` and an `[validators].enabled` allow-list
  (reuse the T002 builder + the `[validators]` block knobs in
  `conftest.write_project`), inert (zero violations) when `[research].enabled=false`
  even with anchors present, and zero violations on a graph with no anchors (SC-004,
  US3 scenarios 1–4). **Plus the `--scope` assertion (SC-005):** because anchor
  violations are location-less (`source=None`, D7), a report filtered by any
  `ScopeFilter` reports **zero** `factual_anchor` violations while the unscoped report
  carries them all — assert both directions via `report.reported(scope=…)` so the
  location-less contract is pinned (`ScopeFilter.matches(None) is False`).
- [X] T018 [US3] Confirm `factual_anchor.py` reads
  `project.manifest.research.enabled` and `min_reliability_for_anchor` straight from
  the `[research]` model and relies on that model's documented defaults
  ([src/bookwright/core/_research_block.py](../../src/bookwright/core/_research_block.py))
  — remove any literal default (e.g. a hardcoded `"media"`) so there is one source of
  truth for the threshold default (FR-014, zero-drift). (depends T016)

**Checkpoint**: all three stories independently functional and tested.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T019 [P] Run the full gate sweep: `uv run ruff check`, `uv run ruff format
  --check`, `uv run mypy --strict`, and `uv run pytest` — confirm green and coverage
  ≥ 80 % (single-sourced `fail_under`, SC-006). Do **not** add any `--cov-fail-under`.
- [X] T020 [P] Verify Principle IV: confirm `queries.py`, `anchor_queries.py`,
  `validators/factual_anchor.py`, and `validators/temporal.py` each stay ≤ 500 lines,
  and that `factual_anchor.py` contains no rdflib import (SPARQL lives only in
  `anchor_queries.py`/`queries.py`, mirroring `temporal`).
- [X] T021 Walk the [quickstart.md](quickstart.md) end to end on a real research
  project: build the graph, introduce one defect of each kind, run `bookwright
  validate` / `--json` / `--severity error` / `--scope <research-file>`, and confirm
  each expected warning/error, the inert/disabled behaviours, and that the `--scope`
  run reports **zero** `factual_anchor` violations (location-less, SC-005) all appear
  as documented.
- [X] T022 [P] If `docs/` (or the README) enumerates the built-in validators, add
  `factual_anchor` to that list in **Spanish** (language convention); otherwise note
  no docs change is required. No skill is emitted (FR-017, N/A to Principles VI/VII).

---

## Dependencies & Execution Order

### Phase order

- **Setup (T001)** → **Foundational (T002–T005)** → **US1 (T006–T011)** →
  **US2 (T012–T016)** → **US3 (T017–T018)** → **Polish (T019–T022)**.
- Foundational blocks all stories. US1 is the MVP and can ship before US2/US3 exist.

### Cross-task dependencies

- T003 → T004 (`load_anchors` uses `parse_gyear`) → T005 (skeleton loads anchors).
- T007 → T008 → T009 → T010 → T011 (R1–R4 share `factual_anchor.py`; sequential).
- T013 → T014 (rewire needs the predicate); T013, T015 → T016 (R5 needs both); both
  edit `queries.py` so T013 and T015 are sequential, not parallel.
- T016 → T018 (defaults task touches the now-complete validator).

### Within each user story

- The story's test task (T006 / T012 / T017) is written FIRST and must fail (red)
  before its implementation tasks turn it green.
- US1/US2 rules append to the same `factual_anchor.py` → strictly sequential; only the
  projection helper (different file) is parallel with the test task.

### Parallel opportunities

- **Foundational**: T002 (test file) ∥ T003 (queries.py) can start together; T004/T005
  then chain.
- **US1**: T006 (new test file) ∥ T007 (anchor_queries.py) run in parallel; T008–T011
  are sequential after T007.
- **US2**: T012 (test files) runs alongside the start of T013.
- **Polish**: T019, T020, T022 are independent of each other ([P]); T021 is manual.

---

## Parallel Example: User Story 1 kickoff

```bash
# After Foundational (T005) is complete, launch in parallel:
Task: "T006 [US1] Author the US1 test cases in tests/validation/test_factual_anchor.py"
Task: "T007 [US1] Add source/facet/reliability/presence projections to src/bookwright/validation/anchor_queries.py"
# Then implement R1→R4 sequentially in src/bookwright/validation/validators/factual_anchor.py.
```

---

## Implementation Strategy

### MVP first (User Story 1 only)

1. Setup (T001) → Foundational (T002–T005): a discovered, inert-correct validator.
2. US1 (T006–T011): the structural audit — the deterministic floor the later
   `bookwright-verify` LLM check builds on.
3. **STOP and validate** against the US1 independent test, then ship if desired.

### Incremental delivery

- US1 → structural warnings (MVP). US2 → anachronism error + the FR-011 single-source
  refactor. US3 → discovery/inert guarantees. Each adds value without regressing the
  prior (US2's temporal rewire is proven non-regressive by T001/T014).

---

## Notes

- `[P]` = different file, no incomplete-task dependency. Same-file rule tasks are
  intentionally **not** `[P]`.
- Out of scope (FR-017, do not pull in): the `bookwright-verify` LLM semantic check,
  any auto-fix, vector search, and any new GOLEM ontology class.
- Commit between logical groups via the optional Spec-Kit git hook; merge to `main`
  only when all four gates are green and `/speckit-analyze` reports no issues.
