# Implementation Plan: Release Prep — Fixtures, E2E Tests & Documentation

**Branch**: `011-release-prep` | **Date**: 2026-06-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-release-prep/spec.md`

## Summary

Take Bookwright from "feature-complete on `main`" (iterations 1–11) to
"shippable as v0.1.0" without adding any runtime feature. Three deliverable
classes: (1) three minimal-but-coherent **fixture projects**
(`tiny-novel`, `tiny-essay`, `tiny-memoir`) under `tests/fixtures/`, each a
valid Bookwright project that builds, queries, and validates clean;
(2) an **E2E test suite** (`tests/e2e/`) that drives the real CLI
in-process over those fixtures and a fresh `init`, locking down the full
workflow, skills-materialization compliance, and the claude→generic
integration swap, all counting toward the ≥ 80% coverage gate; (3)
**user/contributor documentation** — a Spanish MkDocs (`material`) site that
builds with `--strict` (zero warnings), a finalized `README.es.md`,
`CHANGELOG.md` v0.1.0 entry, `CONTRIBUTING.md` (×3 extension how-tos), and
an Apache-2.0 `LICENSE` — plus CI gates for docs-build and artifact-build
and a manual packaged-install validation. Technical approach is recorded in
[research.md](research.md); the binding decisions are: in-process
`CliRunner` for coverage (D1), rebuild `graph.ttl` in `tmp_path` rather than
commit it (D2), the **full** built-in validator set on every fixture
(`[validators] disabled = []`) — non-fiction stays clean because off-genre
validators are inert, with **no validator code change and no masking config**
(revised D3), and a `docs` dependency group
so MkDocs needs **no constitutional amendment** (D6).

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II; `requires-python >= 3.11`).

**Primary Dependencies**: No new **runtime** dependency. Test/build tooling
only — `pytest` + `pytest-cov` + `typer.testing.CliRunner` (existing `dev`
group); **new `docs` group**: `mkdocs`, `mkdocs-material` (D6). Distribution
build via `uv build` (hatchling backend, existing).

**Storage**: Plain text (Markdown/TOML/Turtle) per Principle I. Fixtures are
source-only; `bible/graph.ttl` is a derived cache rebuilt in `tmp_path` (D2),
never committed.

**Testing**: `pytest` (in-process `CliRunner` E2E, D1) + one subprocess
smoke + a manual `pipx`/`uv tool` packaged-install check (D7).

**Target Platform**: Local CLI (macOS/Linux); CI on GitHub Actions
(ubuntu, Python 3.11 + 3.12 matrix).

**Project Type**: Single project (`src/bookwright/` + `tests/`), src-layout
(Principle III). This iteration adds `tests/fixtures/`, `tests/e2e/`,
`docs/`, and `mkdocs.yml`; touches `pyproject.toml` (docs group),
`.github/workflows/tests.yml` (docs + build gates), and the root metadata
files. No `src/bookwright/` runtime code changes.

**Performance Goals**: Manual packaged-install quickstart completes
init → edit → build → query → validate in **≤ 5 minutes** for a first-time
user (SC-003). No indexer perf work (out of scope).

**Constraints**: Docs site builds with **zero warnings** (`--strict`,
FR-014); coverage **≥ 80%**, fail-closed with no round-up (FR-019, SC-005); each new
test/source file **≤ 500 lines** (Principle IV); `--json` stdout stays a
single JSON document (Principle IX); generated `SKILL.md` files satisfy
agentskills.io (Principle VII).

**Scale/Scope**: 3 fixtures, 3 E2E test files (+ fixture-validity tests),
~7 docs page areas (one page/section per shipped command), 5 metadata files,
1 CI workflow update. No new CLI command, no new domain model.

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` v1.3.0. Must pass
before Phase 0 and re-checked after Phase 1.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Plain text as source of truth | ✅ | Fixtures are Markdown/TOML; no committed `graph.ttl` or skills dir — derived cache rebuilt in `tmp_path` (D2). |
| II. Modern Python stack | ✅ | **No runtime dependency added.** MkDocs/mkdocs-material go in a `docs` dev group, never imported by `src/` at runtime → no amendment (D6). |
| III. src-layout | ✅ | New work under `tests/` (`fixtures/`, `e2e/`) and `docs/` only; no production code moves. |
| IV. Modular command surface | ✅ | No new subcommand. Each new test file kept ≤ 500 lines (VR-8). |
| V. Plugin-based integrations | ✅ | Swap test exercises the existing `claude`/`generic` registry; no `AGENT_CONFIG`, no new integration. |
| VI. Agent Skills only | ✅ | Materialization test asserts SKILL.md only; negative assertion that no `*/commands/` dir is written. |
| VII. agentskills.io compliance | ✅ | `test_skills_materialization.py` reuses the shipped linter `lint_skill_md` — direct enforcement (name `< SKILL_NAME_MAX_LENGTH` & == dir, description `< SKILL_DESCRIPTION_MAX_LENGTH`, valid YAML); no re-encoded bounds. |
| VIII. Test discipline (≥ 80%) | ✅ | This iteration **is** the E2E layer; coverage gate stays **≥ 80%**, fail-closed with no round-up (CI-1, `precision=2`). Authoring-skill legs covered by materialization — see note below. |
| IX. JSON-over-stdout | ✅ | E2E assertions parse stdout as a single JSON doc; prose on stderr (VR-9). |
| X. Design axioms | ✅ | Architecture page **summarizes + links** the design doc; reopens nothing in § 16. |

**Note on Principle VIII (authoring-flow E2E)**: Constitution v1.3.0 clarifies
VIII for exactly this case. The authoring legs of the named workflow
(`constitution/bible/outline/scenes/draft`) are Agent **Skills** — LLM-driven
`SKILL.md` prompts, not executable CLI commands — so per the clarified
principle their E2E verification is satisfied by **materialization compliance**
(C2, `test_skills_materialization.py`): every authoring skill is generated and
passes the shipped agentskills.io linter (`lint_skill_md`, Principle VII),
while the executable surface (`init → graph build → graph query → validate`) is
exercised end-to-end by C1. No authoring step is left unverified; the
verification mode differs by artifact type (executable command vs. skill
prompt), and the ≥ 80% coverage bar is unchanged.

**Scope & Release Discipline**: deliverables map 1:1 to design § 15.4 (M3)
and the iteration-12 prompt. No deferred capability (presets v0.2, Grafeo
v0.3, extra integrations v0.4, extension system v0.5, export v1.0) is pulled
forward. The non-fiction fixtures stay clean under the **full** validator set
(`[validators] disabled = []`) because the off-genre validators are inert, so
no validator code and no masking config is added (revised D3).

**Result**: PASS — no violations. Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/011-release-prep/
├── plan.md              # This file
├── research.md          # Phase 0 — D1…D9 decisions
├── data-model.md        # Phase 1 — E1…E4 artifact schemas
├── quickstart.md        # Phase 1 — maintainer validation walkthrough
├── contracts/           # Phase 1
│   ├── e2e-tests.md     #   C1…C3 E2E test contracts
│   ├── fixture-shape.md #   per-fixture structural contract
│   └── docs-site.md     #   MkDocs nav + metadata + CI gates
└── tasks.md             # Phase 2 — created by /speckit-tasks (NOT here)
```

### Source Code (repository root)

```text
tests/
├── fixtures/
│   ├── tiny-novel/      # 3 chars, 2 settings, 5 events, 1 draft chapter
│   ├── tiny-essay/      # 3 chapters, no fictional chars, bibliography
│   ├── tiny-memoir/     # 1 protagonist (author), autobiographical scenes
│   └── test_fixtures.py # copies each → tmp_path, asserts build/query/validate
└── e2e/
    ├── __init__.py
    ├── conftest.py            # fixture-copy + CliRunner helpers
    ├── test_full_workflow.py  # init → edit → build → query → validate
    ├── test_skills_materialization.py
    └── test_integration_swap.py

docs/
├── index.md
├── getting-started.md
├── architecture.md      # summary + links into bookwright-design.md § N.M
├── commands/            # one page/section per shipped command
├── validation.md
├── extending.md
└── faq.md

mkdocs.yml               # theme: material; strict: true
pyproject.toml           # + [dependency-groups] docs = [mkdocs, mkdocs-material]
.github/workflows/tests.yml   # + mkdocs build --strict + uv build gates
README.es.md             # finalized canonical (status → v0.1.0)
README.md                # short English pointer (optional)
CHANGELOG.md             # + [0.1.0] entry enumerating shipped features
CONTRIBUTING.md          # + new integration / custom validator / vocabulary
LICENSE                  # Apache-2.0 (present)
```

**Structure Decision**: Single project, src-layout (Principle III). All new
artifacts are tests, docs, or root metadata; `src/bookwright/` is **not
modified** — this is consolidation, not feature work. Fixtures and E2E tests
live under `tests/` (Principle III); the docs site is a sibling `docs/` tree
driven by a root `mkdocs.yml`.

## Complexity Tracking

> No Constitution violations — section intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Phase 0 — Research

Complete. See [research.md](research.md): D1 (in-process `CliRunner` for
coverage), D2 (rebuild `graph.ttl` in `tmp_path`), D3 (full validator set,
`[validators] disabled = []`, clean off-genre, no code change), D4 (docs↔CLI drift test), D5
(MkDocs `material` + `strict`, curated architecture page), D6 (`docs`
dependency group → no amendment), D7 (manual packaged-install), D8 (CI docs
+ build gates), D9 (fixture shape to iter-6 mapper keys). All
`NEEDS CLARIFICATION`: none (spec fully clarified 2026-06-03).

## Phase 1 — Design & Contracts

Complete. Artifacts:
- [data-model.md](data-model.md) — E1 Fixture, E2 E2E test, E3 Docs site,
  E4 Release artifact/metadata (artifact schemas + VR-1…VR-15).
- [contracts/e2e-tests.md](contracts/e2e-tests.md) — C1…C3.
- [contracts/fixture-shape.md](contracts/fixture-shape.md) — per-fixture
  structure + shared invariants F1…F6.
- [contracts/docs-site.md](contracts/docs-site.md) — MkDocs nav, metadata
  files, CI gates CI-1…CI-6, manual MAN-1…MAN-3.
- [quickstart.md](quickstart.md) — maintainer validation walkthrough.
- Agent context: `CLAUDE.md` SPECKIT pointer updated to this plan.

## Phase 2 — Next

Run `/speckit-tasks` to generate `tasks.md` (dependency-ordered), then
`/speckit-analyze`, then `/speckit-implement`. Suggested task ordering
follows the priority slices: P1 fixtures → P1 E2E tests → P2 docs → P3
release metadata + CI gates → manual packaged validation.
