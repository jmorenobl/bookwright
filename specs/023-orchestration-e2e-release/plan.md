# Implementation Plan: Orchestration loop fixture, E2E flow, docs, and v0.3.0 release

**Branch**: `023-orchestration-e2e-release` | **Date**: 2026-06-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/023-orchestration-e2e-release/spec.md`

## Summary

Closing iteration of M5 / v0.3.0 (context orchestration, design § 21). The
mechanism is already merged (focus block 019, `status` engine 020,
status-consuming skills 021–022); this iteration ships **proof and explanation
only** — no new product mechanism (FR-020). Three deliverables plus the release:

1. **Fixture** — extend the committed `tiny-historical` so the orchestration loop
   has something concrete to reason over: add a populated `[focus]` block to its
   `manifest.toml` (FR-002), keep its two `_index.md` open questions as the
   open-question set (FR-003), and ship a **pre-baked resolution** beside the
   fixture (a `_resolution/` answering-Finding file + the recorded `_index.md`
   edit) plus a co-located `expected-status.md` oracle (FR-004, FR-005). The
   committed tree stays inert to the M4 `factual_anchor` test (FR-006).
2. **E2E test** — `tests/e2e/test_orchestration_workflow.py`, built on the
   iteration-016 precedent (in-process `CliRunner`, `--json` parsed off stdout,
   oracle loaded once, `tmp_path` copy via `copy_fixture`). It walks
   focus → build → status → resolve → build → status and asserts a deterministic
   **state-convergence** result (FR-007..FR-010), plus inertness/degraded paths
   reusing `tiny-novel` (FR-011, FR-012).
3. **Docs & release** — new top-level `docs/orchestration.md` (FR-013, FR-014),
   verify-and-finalize the existing `status`/`focus` command pages (FR-015),
   a v0.3.0 changelog entry (FR-016), and bump `__version__` to `0.3.0` (FR-022).

The load-bearing design decision (clarification 2026-06-13, Q4): the merged
`status` engine recommends **workstreams per rule-category**, not per item — one
`research_queue` action bundles *all* open questions *and* all anchor gaps. So
resolving one open question does **not** shorten `next_actions`. The E2E asserts
**state convergence** instead: the resolved id leaves `state.open_questions`
(K→K−1) and the `research_queue` prompt/reason; every other asserted field is
byte-identical across the two runs. See [research.md](./research.md) D2 for how
the legitimately-moving `state.graph` counts are carved out of that comparison.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II/III, unchanged)

**Primary Dependencies**: No new runtime deps. Test/build only: `pytest` +
`typer.testing.CliRunner` (in-process), `mkdocs` + `mkdocs-material` (docs group).
Reuses merged `bookwright.status.{model,rules,queries}`, `bookwright.io.research`,
`bookwright.core.manifest` (`set_focus`) — all read-only from this iteration's view.

**Storage**: Plain text only (Constitution I). Fixture is Markdown + TOML + the
derived `bible/graph.ttl` rebuilt in the `tmp_path` copy, never committed.

**Testing**: `pytest`; the new E2E follows `tests/e2e/test_research_workflow.py`
1:1 (in-process `cli` fixture, `copy_fixture` over `tmp_path`, `--json` off stdout,
co-located oracle loaded once — never hard-coded values).

**Target Platform**: CLI / library (cross-platform; CI on GitHub Actions).

**Project Type**: Single-project src-layout CLI (`src/bookwright/`, `tests/`).

**Performance Goals**: N/A — a fixture, one E2E module, docs, a version bump.

**Constraints**: Determinism is the hard constraint (research D2): the asserted
`status` JSON must be byte-identical across repeated runs on an unchanged corpus
(no timestamps / minted-URI / ordering nondeterminism in asserted fields).
`mkdocs build` runs under `strict: true` → zero warnings (FR-019). Every source
file ≤ 500 lines (Principle IV). The ≥ 80 % coverage gate is the single enforced
threshold (FR-017); ≥ 85 % on new M5 code is report-only.

**Scale/Scope**: ~1 fixture extension (3 added files + 1 manifest edit), 1 E2E
test module (~5–8 tests), 1 new doc page, 3 doc/changelog touch-ups, 1 version
line. No `src/bookwright/` production change (FR-020).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Verdict | Note |
|---|---|---|
| I. Plain text as source of truth | ✅ PASS | Fixture is MD/TOML; `graph.ttl` rebuilt in `tmp_path`, never committed; resolution material is plain MD. |
| II. Modern Python stack | ✅ PASS | No new runtime dep; reuses the locked stack. |
| III. src-layout | ✅ PASS | Fixture under `tests/fixtures/`, test under `tests/e2e/`; no production module touched except the `__version__` line. |
| IV. Modular command surface / ≤500 lines | ✅ PASS | No new CLI module; new test/doc files stay well under 500 lines. |
| V. Plugin-based integrations | ✅ N/A | No integration change; E2E may invoke `integration use claude` as in 016 but adds no registry entry. |
| VI. Agent Skills only | ✅ PASS | No `commands/` dir written; docs only describe skills. |
| VII. agentskills.io compliance | ✅ N/A | No new SKILL.md authored here. |
| VIII. Test discipline (NON-NEGOTIABLE) | ✅ PASS | Adds an E2E regression for the orchestration loop + inertness/degraded coverage; overall ≥ 80 % held; CI four gates green. |
| IX. JSON-over-stdout | ✅ PASS | All assertions parse a single `--json` document off stdout; no new CLI surface to make compliant. |
| X. Design axioms (§ 16) | ✅ PASS | No axiom reopened; the hand-written-TODO alternative stays rejected (design § 21.2). |
| Scope & Release Discipline | ✅ PASS | Adds no deferred/cancelled capability; FR-020/FR-021 forbid new mechanism, vectors, export. |

**Initial Constitution Check: PASS.** No violations; Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/023-orchestration-e2e-release/
├── plan.md              # This file
├── spec.md              # Feature spec (already present)
├── research.md          # Phase 0 — design decisions (this run)
├── data-model.md        # Phase 1 — fixture/oracle/test entities (this run)
├── quickstart.md        # Phase 1 — runnable validation guide (this run)
├── contracts/
│   └── e2e-orchestration-contract.md   # Phase 1 — FR↔assertion map (this run)
└── tasks.md             # Phase 2 — /speckit-tasks (NOT this run)
```

### Source Code (repository root)

```text
src/bookwright/
└── __init__.py                         # EDIT: __version__ "0.2.0" → "0.3.0" (FR-022, single source)

tests/
├── conftest.py                         # reused as-is (copy_fixture, cli fixture)
├── e2e/
│   ├── test_research_workflow.py       # the 016 precedent this mirrors (untouched)
│   └── test_orchestration_workflow.py  # NEW — the focus→status→resolve→status regression
└── fixtures/
    └── tiny-historical/                # EXTENDED (the orchestration example)
        ├── manifest.toml               # EDIT: add a populated [focus] block (FR-002)
        ├── bible/research/_index.md    # unchanged (its 2 open questions are the pinned set)
        ├── expected-status.md          # NEW — the orchestration oracle (FR-004)
        └── _resolution/                # NEW — pre-baked resolution, OUTSIDE the corpus dirs
            └── q-libro-de-jornales.md  #        answering-Finding file (FR-005)

docs/
├── orchestration.md                    # NEW top-level page (FR-013/014) — like research.md
├── commands/status.md                  # verify-and-finalize (FR-015, exists)
├── commands/focus-set.md               # verify-and-finalize (FR-015, exists)
├── commands/focus-show.md              # verify-and-finalize (FR-015, exists)
├── commands/focus-clear.md             # verify-and-finalize (FR-015, exists)
└── changelog.md                        # EDIT: v0.3.0 entry (FR-016, mkdocs nav target)

CHANGELOG.md                            # EDIT: v0.3.0 entry (FR-016 — the root changelog too)
mkdocs.yml                              # EDIT: add `Orquestación: orchestration.md` to nav (FR-014)
```

**Structure Decision**: Single-project src-layout (Constitution III). This
iteration touches exactly one production line (`__version__`) and otherwise lives
in `tests/fixtures/`, `tests/e2e/`, and `docs/`. The fixture is the *extended*
`tiny-historical` (clarification 2026-06-13, Q1) rather than a new fixture, so the
existing M4 research-workflow test continues to bind it — hence the FR-006
inertness constraint runs through every fixture edit. The pre-baked resolution
lives in a top-level `_resolution/` directory **outside** `bible/`, `manuscript/`,
and `outline/`, so the project loader never reads it during the first `status`
(satisfying FR-005's "must NOT be present in the corpus the first status reads");
the test copies it into `bible/research/` on the `tmp_path` copy for the second
build.

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
