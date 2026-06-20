# Implementation Plan: v0.4 close — narrative-structure E2E fixture, workflow test, docs, honest deferrals, release

**Branch**: `032-v04-close` | **Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/032-v04-close/spec.md`

## Summary

Close milestone **v0.4** (the Propp/Greimas narrative-structure layer — G7/G9/G10
— plus `outline/units/` ingestion) exactly as M4 closed to `v0.2.0` (iteration 016)
and M5 to `v0.3.0` (iteration 023): **prove, explain, make the deferral contract
honest, and lay down the release metadata**. The mechanism is already merged
(028–031); this iteration adds **no new product mechanism and no ontology change**.

Five deliverables:

1. **A worked E2E fixture** — a new `tests/fixtures/tiny-quest/`, source-only, with a
   populated `outline/units/` (cards carrying `functions`/`roles`/`sequence`/`order`),
   `[vocabularies] active = ["propp"]`, and a **deliberate orphan beat + unresolved
   role**, plus a co-located oracle (`expected-narrative.md`) enumerating every
   asserted fact — modelled on `tiny-historical`'s `expected-findings.md` /
   `expected-status.md`.
2. **A workflow test** — `tests/e2e/test_narrative_workflow.py`, built on the
   `test_orchestration_workflow.py` (023) harness: in-process `CliRunner`, `--json`
   parsed off stdout, a `tmp_path` copy, every count/identifier oracle-sourced. It
   asserts the build's graph facts, the exact `narrative_structure` findings, the
   no-vocabulary-active non-regression, and determinism.
3. **Documentation** — a new Spanish `docs/narrative-structure.md` (+ nav entry) and a
   README touch covering `outline/units/` ingestion, unit frontmatter, Propp/Greimas
   activation, and the validator.
4. **An honest deferral registry** — re-point G6 (`RelationshipRole`) and G3
   (`PsychologicalState`) `target_version` from the now-shipped `"v0.4"` to the
   first-class **`"demand-pulled"`** sentinel (Clarifications 2026-06-21), swept
   across both holders (`deferrals.py` + the parity test's `EXPECTED_VERSIONS`) and
   the two stale `DEBT.md` target lines, keeping `test_ingestion_parity.py` green.
5. **Release metadata** — `__version__ = "0.4.0"`, a `v0.4.0` CHANGELOG section,
   `CLAUDE.md` / `bookwright-design.md` brought current, and `bookwright-roadmap.md`
   § 1 (v0.4 entregada) + the § 2 `← AQUÍ` marker advanced.

### Branch scope vs. release step (a load-bearing division)

Per the plan hint and CLAUDE.md ("the iteration branch … does **not** push, merge,
bump the version, or tag — merging to `main` stays a separate, manual step"), the
work splits in two:

| Phase | Owner | Files |
|---|---|---|
| **Branch work** (this `/speckit-implement`) | the iteration branch | the fixture + oracle, the workflow test, `docs/narrative-structure.md` + `mkdocs.yml` nav, README, `deferrals.py` + `test_ingestion_parity.py` re-target, `DEBT.md` target lines, `bookwright-roadmap.md` §1/§2 |
| **Release step** (the `bookwright-release` skill, after the branch is green + merged) | manual | bump `__version__`→`0.4.0`, the `v0.4.0` CHANGELOG section, the `CLAUDE.md` status-table flip + milestone prose, any `bookwright-design.md` status edits, the release commit, the annotated `v0.4.0` tag |

The spec lists FR-015/016/020 as requirements *of the closing iteration* because the
iteration **encompasses** the release; this plan satisfies them through the
`bookwright-release` skill at the closing step, not by hand-editing version/CHANGELOG
inside the branch commits. The branch's quality gates (FR-023/024) run against the
branch deliverables; the release skill re-runs the four gates before tagging.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II).

**Primary Dependencies**: no new runtime dependency. Test + fixture work only —
`typer.testing.CliRunner`, `pytest`, `rdflib` (already runtime), `pyyaml` front-matter
via `bookwright.io.frontmatter`. Docs: `mkdocs` + `mkdocs-material` (docs group).

**Storage**: plain text — fixture is Markdown + TOML; the derived `bible/graph.ttl` is
rebuilt in a `tmp_path` copy and **never committed** (Constitution I).

**Testing**: `pytest` (E2E under `tests/e2e/`, the parity test under `tests/golem/`);
coverage ≥ 80 % stays the single enforced gate (`fail_under` in
`[tool.coverage.report]`, no `--cov-fail-under` drift).

**Target Platform**: CLI / library, cross-platform (CI: Linux matrix).

**Project Type**: single project (src-layout `src/bookwright/`, `tests/` at root).

**Performance Goals**: N/A — deterministic CLI stages over a tiny fixture.

**Constraints**: deterministic assertions only (no LLM/judgment step in CI, FR-011);
every asserted field byte-for-byte stable across repeats (FR-011/SC-002); every
source file ≤ 500 lines (Principle IV); Spanish prose for docs, English identifiers.

**Scale/Scope**: one new fixture (~8–12 small Markdown files + 1 oracle + 1 manifest),
one new E2E test module, one new docs page, ~4 line-level edits to
`deferrals.py`/`test_ingestion_parity.py`, two `DEBT.md` line edits, two roadmap edits.
Release-step edits are out of the branch commit set (table above).

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1 (still passing).*

- **I. Plain text as source of truth** — ✅ fixture is Markdown/TOML; the graph is a
  rebuilt-in-`tmp_path` derived cache, never committed (mirrors every `tiny-*`
  fixture and the parity-exercise guard).
- **II. Modern Python stack** — ✅ no new dependency; test/fixture/docs only.
- **III. src-layout** — ✅ the only `src/` touch is `deferrals.py` (a data edit, no new
  module); tests live under `tests/`, fixtures under `tests/fixtures/`.
- **IV. Modular command surface / ≤ 500 lines** — ✅ no new CLI verb; the new test
  module and docs page stay well under 500 lines; `deferrals.py` stays ~50 lines.
- **V / VI / VII. Integrations, Agent Skills, agentskills.io** — ✅ untouched; no skill
  is added or changed (FR-021). The fixture ships **no** materialized `.claude/`/
  `SKILL.md` (source-only, asserted in the workflow test's Group D).
- **VIII. Test discipline (NON-NEGOTIABLE)** — ✅ this iteration *adds* an E2E
  regression and keeps coverage ≥ 80 %; the fixture is exercised through the real
  CLI (`graph build` → `validate`), the sanctioned E2E mode.
- **IX. JSON-over-stdout** — ✅ the test consumes `graph build --json` / `validate
  --json`, asserting a single JSON document per stdout (no contract change).
- **X. Design axioms** — ✅ no axiom reopened; rdflib/GOLEM/plain-text all unchanged.
  The frozen 17-class ontology is **not** touched (FR-021); the `"demand-pulled"`
  sentinel is a registry-data label, not an ontology class.
- **Scope & Release Discipline** — ✅ adds no deferred/cancelled capability and no
  speculative plumbing. It explicitly does **not** wire G6/G3 (FR-022) and adds no
  new mechanism (FR-021). (Note: `DEBT-002` records that the constitution's own
  Scope & Release Discipline prose is itself stale — corrected by the separate MINOR
  amendment the `v0.4.0` release carries, not on this branch; this branch only
  fixes DEBT-002's stale *target line*, FR-019b.)

**No violations — Complexity Tracking left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/032-v04-close/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (fixture shape, division of labour, sentinel)
├── data-model.md        # Phase 1 — the fixture entities, oracle schema, deferral data
├── quickstart.md        # Phase 1 — run the fixture + test + docs build + release handoff
├── contracts/
│   ├── fixture-oracle.md          # the expected-narrative.md front-matter schema
│   └── e2e-narrative-workflow.md  # the workflow test's asserted groups (A–D)
├── checklists/
│   └── requirements.md  # (existing) spec quality checklist
├── spec.md              # (existing)
└── tasks.md             # Phase 2 — created by /speckit-tasks, not here
```

### Source Code (repository root)

```text
src/bookwright/
└── golem/
    └── deferrals.py          # EDIT: target_version "v0.4" → "demand-pulled" (×2 + docstring)

tests/
├── fixtures/
│   └── tiny-quest/           # NEW source-only fixture (the worked example)
│       ├── manifest.toml     #   [vocabularies] active = ["propp"]
│       ├── expected-narrative.md   # NEW co-located oracle (front-matter = the truth)
│       ├── bible/
│       │   ├── constitution.md
│       │   └── characters/   #   characters declaring narrative_roles (role targets)
│       │       ├── *.md
│       ├── outline/
│       │   └── units/        #   unit cards: functions/roles/sequence/order
│       │       ├── *.md      #   incl. 1 deliberate orphan beat + 1 unresolved role
│       └── manuscript/
│           └── 01-*.md
├── e2e/
│   └── test_narrative_workflow.py   # NEW — build → validate, oracle-sourced (FR-007..011)
└── golem/
    └── test_ingestion_parity.py     # EDIT: EXPECTED_VERSIONS "v0.4" → "demand-pulled" (×2)

# Repo-root living documents
DEBT.md                       # EDIT: DEBT-001 / DEBT-002 stale "Target: v0.4" lines (FR-019b)
bookwright-roadmap.md         # EDIT: §1 (v0.4 entregada) + §2 "← AQUÍ" marker advanced
docs/
├── narrative-structure.md    # NEW Spanish page (ingestion, frontmatter, activation, validator)
mkdocs.yml                    # EDIT: nav entry for the new page
README.md                     # EDIT: reflect the v0.4 narrative-structure layer

# Release-step files (the bookwright-release skill, NOT this branch's commits):
#   src/bookwright/__init__.py (__version__), CHANGELOG.md, CLAUDE.md, bookwright-design.md
```

**Structure Decision**: single project, no new module. The fixture follows the
`tests/fixtures/tiny-*` convention (short-but-coherent narrative, Spanish prose,
English identifiers/structure) with a co-located oracle; the test follows
`tests/e2e/` (fixtures-as-input, `tmp_path` where mutated). The one `src/` change is
a data edit to `deferrals.py`. A **new** fixture (not an extension of
`parity-exercise` or `tiny-historical`) keeps the v0.4 demonstration — Propp active,
a deliberate orphan beat, a deliberate unresolved role — from polluting those pinned
oracles (spec Assumption; confirmed in research.md D1).

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
