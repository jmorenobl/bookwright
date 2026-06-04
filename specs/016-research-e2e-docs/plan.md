# Implementation Plan: Historical fixture, research E2E flow, and v0.2.0 documentation

**Branch**: `016-research-e2e-docs` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/016-research-e2e-docs/spec.md`

## Summary

The M4/v0.2.0 research mechanism is already built (provenance model, `bible/research/`
reader, `[research]` block, `factual_anchor` validator, `bookwright-research` /
`bookwright-verify` skills). This iteration ships **no new mechanism** — only the three
proofs the release is missing: a realistic worked example (`tiny-historical` fixture), an
automated regression that walks build → query → validate over it (plus inertness
guarantees for research-free / disabled projects), and a documentation set (research page,
skills + validator reference, v0.2.0 changelog).

The technical approach is to follow the **existing conventions verbatim**: a static fixture
under `tests/fixtures/` parallel to `tiny-novel` (loaded with `copy_fixture` into `tmp_path`
and driven through the real CLI in-process), an E2E test under `tests/e2e/` shaped like the
current ones, and MkDocs-Material pages wired into the existing Spanish, `strict: true`
site. The one design subtlety the spec forces is keeping **two anachronisms distinct**:

- a **manuscript-prose** anachronism (FR-006) — what the LLM `bookwright-verify` skill
  catches; exercised as a *documented manual step* whose preconditions the test asserts;
- a **graph-level time-span** anachronism (FR-007 error) — an anchor whose year-span is
  disjoint from the dated timeline event it `constrains`; this is what `factual_anchor`'s
  R5 rule reports as an **error**, deterministically, in CI.

plus one **under-reliable anchor** (FR-007 warning) — an anchor whose only supporting
source is below the manifest's `min_reliability_for_anchor`; it *parses* (so the build
succeeds) but `factual_anchor`'s R3 rule reports it as a **warning**.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II) — but this iteration adds essentially
no `src/` code; it is fixtures + tests + docs.

**Primary Dependencies**: none new. Consumes the existing surface: `bookwright` CLI
(`graph build`, `graph query`, `validate`, `integration use`), `bookwright.io.research`
(`map_research`, strict fault model), `bookwright.validation.validators.factual_anchor`
(R1–R5 rules), `bookwright.core._research_block.ResearchBlock`. Test stack: `pytest` +
`typer.testing.CliRunner`. Docs: `mkdocs` + `mkdocs-material` (docs group, never imported
by `src/`).

**Storage**: plain text only — the fixture is Markdown + TOML; the derived `bible/graph.ttl`
is rebuilt in a `tmp_path` copy, never committed (Constitution I; matches `tiny-novel`).

**Testing**: `pytest`. New static fixture `tests/fixtures/tiny-historical/` consumed via
`tests/conftest.py::copy_fixture`; new regression `tests/e2e/test_research_workflow.py`
following the in-process-CLI style of `tests/e2e/test_full_workflow.py` and
`tests/fixtures/test_fixtures.py`.

**Target Platform**: developer/CI (Linux + macOS), same as the rest of the suite.

**Project Type**: single project (src-layout CLI toolkit). No frontend/mobile split.

**Performance Goals**: N/A — a short fixture and a handful of in-process CLI invocations.

**Constraints**: deterministic CI (the planted findings must be exactly one warning + one
error, no flakiness); MkDocs `strict: true` (any broken link / orphan page / missing nav
target is a build error = the FR-021 "zero warnings" gate); global coverage stays ≥ 80 %
(the single enforced gate, no second `fail_under`); no vector search or any v0.3+ mechanism
(FR-022); every source file ≤ 500 lines (Constitution IV).

**Scale/Scope**: 1 fixture (~12–16 files), 1 new E2E test module, 1 new docs page +
edits to `docs/validation.md` / `docs/authoring.md` + a new `docs/changelog.md`, and the
`mkdocs.yml` nav. Roughly the footprint of iteration 011/012 minus new product code.

## Constitution Check

*GATE: must pass before Phase 0. Re-checked after Phase 1 — still passing.*

| Principle | Status | Note |
|---|---|---|
| I. Plain text as source of truth | ✅ | Fixture is Markdown/TOML; the expected-findings oracle is Markdown + YAML front-matter; `graph.ttl` and skills dirs are never committed (asserted, mirroring `test_fixtures.py`). |
| II. Modern Python stack | ✅ | No new runtime or dev dependency. `mkdocs`/`mkdocs-material` already in the docs group. |
| III. src-layout | ✅ | Fixtures + tests under `tests/`, docs under `docs/`. No production module imported from outside `src/bookwright/`. |
| IV. Modular command surface / ≤ 500 lines | ✅ | No CLI change. The new test module is self-contained and stays under 500 lines (split if it approaches it). |
| V. Plugin-based integrations | ✅ | No integration change; the test *uses* `integration use claude` to materialize the verify skill, it does not add an integration. |
| VI. Agent Skills only | ✅ | No `commands/` directory written. The two skills already ship as `SKILL.md`. |
| VII. agentskills.io compliance | ✅ | No skill authored or modified. |
| VIII. Test discipline (≥ 80 %) | ✅ | Adds an E2E regression + inertness tests; the global ≥ 80 % gate is the single enforced bar (FR-019). ≥ 85 % on M4 code is verified-at-review only — **no** new per-package `fail_under` (preserves "one source, no drift"). |
| IX. JSON-over-stdout | ✅ | The test consumes `--json` from existing commands; no new contract. |
| X. Design-document axioms | ✅ | None reopened. Verification reads research Markdown directly (no Grafeo, no vectors). |
| Scope & Release Discipline | ✅ | Pure consolidation; introduces no deferred (v0.3+) capability and no "future X" plumbing (FR-022). |

**Result: PASS, no violations.** Complexity Tracking is intentionally empty.

## Project Structure

### Documentation (this feature)

```text
specs/016-research-e2e-docs/
├── plan.md              # This file (/speckit-plan)
├── spec.md              # Feature spec (already present)
├── research.md          # Phase 0 — decisions (this run)
├── data-model.md        # Phase 1 — fixture entities + planted-defect model + oracle schema
├── quickstart.md        # Phase 1 — how to build/validate the fixture and the manual verify step
├── contracts/
│   ├── fixture-layout.md         # The tiny-historical tree + manifest contract
│   ├── expected-findings.md      # Schema of the co-located oracle file
│   └── e2e-test-contract.md      # What the regression must assert (FR-008..FR-014)
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

This iteration touches **no `src/` production code**. It adds fixtures, tests, and docs:

```text
tests/
├── fixtures/
│   └── tiny-historical/                 # NEW — the worked example (FR-001..FR-007)
│       ├── manifest.toml                #   [research] enabled, source_languages, min_reliability
│       ├── expected-findings.md         #   co-located oracle (FR-012): warning anchor, error anchor, prose anachronism
│       ├── bible/
│       │   ├── constitution.md
│       │   ├── timeline.md              #   ≥1 DATED event (gives R5 an interval to contradict)
│       │   ├── characters/*.md
│       │   ├── settings/*.md
│       │   └── research/                #   the provenance corpus (strict reader input)
│       │       ├── sources.md           #   several Sources, full provenance, ≥1 foreign-language (translation)
│       │       ├── <topic>.md           #   findings + anchors: the good anchors, the under-reliable one, the anachronistic one
│       │       └── _index.md            #   open question(s) + topic map
│       ├── outline/*.md
│       └── manuscript/NN-<slug>.md      #   chapter with the planted PROSE anachronism (for verify)
└── e2e/
    └── test_research_workflow.py        # NEW — build→query→validate + verify preconditions + inertness (FR-008..FR-014)

docs/
├── research.md          # NEW — the research page (FR-015/FR-017); also documents the two skills (FR-016)
├── validation.md        # EDIT — add `factual_anchor` to "Validadores integrados" (FR-016)
├── authoring.md         # EDIT — note bookwright-research / bookwright-verify in the skills reference (FR-016)
└── changelog.md         # NEW — v0.2.0 entry (+ retroactive v0.1.0) (FR-018)

mkdocs.yml               # EDIT — add research + changelog to nav (FR-017); keep strict: true (FR-021)
```

**Structure Decision**: Single-project, mirror the existing test/doc conventions exactly.
The fixture is **static** under `tests/fixtures/` (not packaged in `src/bookwright/resources/`)
because that is where every `tiny-*` example lives and how `copy_fixture` finds them — the
spec's word "packaged" is the loose sense of "shipped with the repo". The fixture is **kept
out of the clean-fixtures parametrization** in `tests/fixtures/test_fixtures.py`
(`FIXTURES = ["tiny-novel", "tiny-essay", "tiny-memoir"]`) because, unlike those, it
deliberately validates with one warning + one error; all of its assertions live in the new
E2E module instead. The two skills are documented in the **research page + authoring
reference**, never under `docs/commands/`, because that directory is gated by
`tests/e2e/test_docs_commands_match.py` to equal the live **CLI** leaf-command set — the
skills are not CLI verbs, so a page there would fail CI.

## Complexity Tracking

> No Constitution violations — this section is intentionally empty.
