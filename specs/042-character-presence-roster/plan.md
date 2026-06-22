# Implementation Plan: `character_presence` unknown-mention rule cross-checks settings, locations & objects

**Branch**: `042-character-presence-roster` | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/042-character-presence-roster/spec.md`

## Summary

Close **DEBT-010**: the `character_presence` unknown-mention rule (`warning`) suppresses a
proper-noun candidate only when its slug (or a token slug) is in the **character** roster,
so the capitalized tokens of a declared multi-word environment — e.g. `Real`, `Fábrica`,
`Paños` of the bible setting "la Real Fábrica de Paños" — each fire a spurious
"no bible entry" warning even though the entry exists under `bible/settings/`.

The fix widens the rule's "known names" set to the **union** of the character, setting,
**location** and **object** rosters, consistent with the issue #1 doctrine (per-class fix,
no semantic NER). Concretely:

1. `ValidationContext` gains two cached accessors — `location_names()` (GOLEM class
   `NarrativeLocation`, `bible/locations/`, G13) and `object_names()` (GOLEM class
   `Object`, `bible/objects/`, G16) — each a byte-for-byte mirror of the existing
   `setting_names()`: the same generic `_names_of(concept_cls)` helper and the same
   `_UNSET`-sentinel memoization, no new helper (FR-001).
2. `CharacterPresence.validate` keeps feeding `_orphans` from `character_names()` alone
   (the `error` gate is untouched, FR-004/FR-006), but builds the slug set
   `_unknown_mentions` consumes from the **concatenation** of all four rosters, reusing
   the existing module-level `_roster_slugs` helper unchanged (FR-002/FR-003).
3. The `NotEvaluated` guard stays clavado on `not roster and not files` (character roster
   only) with the identical reason string (FR-007); the `Violation` shape is untouched
   (FR-005/FR-008); the validator still emits zero triples and needs no graph (FR-009);
   the frozen ontology is untouched (FR-010).

No validator behavior other than which slugs suppress changes. The only pinned oracle that
shifts is `tests/fixtures/tiny-historical/expected-status.md`
(`validation.counts.warning` `4 → 1`, fixture manuscript/bible untouched, FR-012) — the
same shape of oracle-only correction iterations 041 (`5 → 4`) and 038 (`6 → 5`) made.

## Technical Context

**Language/Version**: Python 3.11+ (locked by Constitution II).

**Primary Dependencies**: stdlib only for the change (`re`, already imported); `rdflib`/
`pydantic` reached transitively through the existing bible-mapping path. **No new
dependency** (Constitution II; design § 13 — file-based, not SPARQL).

**Storage**: plain-text bible (`bible/{characters,settings,locations,objects}/*.md`) read
once per run through `ValidationContext.bible()` → `map_bible`. The graph is a derived
cache and is **not** consulted by this validator.

**Testing**: `pytest` with ≥80% coverage (Principle VIII). New coverage: seam-free
synthetic-project unit tests on `tests/validation/conftest.py`'s `write_project` /
`load_context` (extended with `locations` / `objects` knobs mirroring `settings`), plus
the `tiny-historical` E2E oracle correction.

**Target Platform**: CLI (`uv run bookwright validate` / `status`), cross-platform.

**Project Type**: single src-layout Python package (`src/bookwright/`).

**Performance Goals**: N/A (per-run, in-memory; two extra roster reads share the already
cached `bible()` map — no extra disk read).

**Constraints**: every changed file ≤ 500 lines (Principle IV); deterministic, no disk
writes, no graph mutation (validator contract); ES+EN prose handled by the existing
accent-aware candidate regex (unchanged).

**Scale/Scope**: ~4 source/test files touched + 1 oracle + `DEBT.md`. `validation/base.py`
322 → ~350 lines; `character_presence.py` 215 → ~218 lines.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I — Plain-text source of truth**: ✅ rosters derive from `bible/**/*.md` via the
  existing mapping path; the graph stays a derived cache and is not read here. DEBT-010
  is removed from the plain-text `DEBT.md` (FR-013).
- **II — Locked stack**: ✅ no new dependency; stdlib `re` only; no Markdown parser.
- **IV — File size / one subcommand per module**: ✅ both changed source files stay well
  under 500 lines (FR-014); no module gains a second subcommand.
- **V — Plugin shapes, no monolith dispatcher**: ✅ N/A — no integration/indexer change.
- **VI — Agent Skills only**: ✅ N/A — no skill or `commands/` change.
- **VIII — Test discipline ≥80%**: ✅ both new accessors and both new union arms are
  exercised by synthetic-project tests so nothing ships as untested dead plumbing
  (FR-015); the full suite is the empirical regression gate (FR-011).
- **IX — `--json` over stdout**: ✅ N/A — the `Violation`/envelope shapes are byte-stable
  (FR-005/FR-008); only suppressed-slug membership changes.
- **X — Frozen GOLEM ontology**: ✅ no class added, no `.ttl` edited; the validator's
  `triples` stay `()` (FR-009/FR-010, SC-007). `NarrativeLocation`/`Object` are existing
  frozen concepts, only *read*.
- **Scope & release discipline**: ✅ one observable delta (declared environments stop
  being mis-flagged); no plumbing justified only by "future X". DEBT-011 (paired leading
  quotes) is explicitly **not** swept here — it is a distinct design, already recorded.

**Result: PASS** (no violations; Complexity Tracking table left empty).

## Project Structure

### Documentation (this feature)

```text
specs/042-character-presence-roster/
├── plan.md              # This file (/speckit-plan output)
├── spec.md              # Feature spec (already hardened)
├── research.md          # Phase 0 output (this command)
├── data-model.md        # Phase 1 output (this command)
├── quickstart.md        # Phase 1 output (this command)
├── contracts/
│   └── validation-context-accessors.md   # the two new accessor contracts + union contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── validation/
│   ├── base.py                       # + location_names()/object_names() accessors
│   │                                 #   + _location_names/_object_names cache fields
│   └── validators/
│       └── character_presence.py     # validate(): union roster_slugs feeds _unknown_mentions
└── golem/
    └── modules/{setting,character}.py  # NarrativeLocation / Object — READ ONLY, unchanged

tests/
├── validation/
│   ├── conftest.py                   # write_project: + locations=/objects= knobs (mirror settings)
│   ├── test_validation_context.py    # + location_names()/object_names() accessor tests (or new file)
│   └── test_character_presence.py    # + union-suppression + still-fires + orphan-untouched tests
└── fixtures/
    └── tiny-historical/
        └── expected-status.md        # validation.counts.warning 4 → 1 (oracle only; manuscript untouched)

DEBT.md                               # remove DEBT-010 entry (FR-013)
```

**Structure Decision**: single src-layout package (the only option this repo uses). The
change is two new memoized accessors on `ValidationContext` and a one-line widening of the
slug set in `character_presence.validate`; everything else is test/oracle/debt bookkeeping.

## Complexity Tracking

> No Constitution Check violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
