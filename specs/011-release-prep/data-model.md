# Data Model: Release Prep — Fixtures, E2E Tests & Documentation

**Branch**: `011-release-prep` | **Date**: 2026-06-03 | **Phase**: 1

This iteration introduces **no new runtime domain types** — it adds no
Pydantic model, no GOLEM class, no manifest field. The "entities" here are
the *test- and release-time artifacts* the spec enumerates (Key Entities,
spec.md) plus the structural contract each fixture must satisfy to be a
valid Bookwright project. They are modeled below as artifact schemas, not
as code types.

---

## E1 — Fixture project

A self-contained, version-controlled minimal Bookwright project under
`tests/fixtures/<name>/`, usable both as automated-test input and as a
worked example. Three instances exist.

### Structure (mirrors the `bookwright init` scaffold)

```text
tests/fixtures/<name>/
├── manifest.toml                 # required; all built-in validators active (revised D3)
├── bible/
│   ├── constitution.md           # narrative-voice declaration (novel/memoir)
│   ├── characters/<slug>.md      # one Character per file (GOLEM)
│   ├── settings/<slug>.md        # one Setting per file (GOLEM)
│   ├── timeline.md               # events: list → NarrativeEvent (GOLEM)
│   ├── relationships.md          # optional
│   └── … (themes, glossary, …)   # filled prose, no PENDING sentinels
├── outline/
│   ├── synopsis.md  structure.md  arcs.md  scenes.md   # fully populated
├── manuscript/
│   └── <chapter>.md              # draft chapter(s)
└── (NO bible/graph.ttl — derived, rebuilt in tests; D2)
```

### Per-fixture invariants

| Fixture | Characters | Settings | Events | Manuscript | Validators on | Clean validate |
|---------|-----------|----------|--------|------------|---------------|----------------|
| `tiny-novel`  | exactly **3** | exactly **2** | exactly **5** | 1 draft chapter | all built-ins | exit 0 / zero error-severity |
| `tiny-essay`  | **0** fictional | n/a | n/a | 3 chapters + bibliography | all built-ins (none disabled) | exit 0 / zero error-severity |
| `tiny-memoir` | **1** (author) | ≥0 | ≥0 | autobiographical scenes | all built-ins (none disabled) | exit 0 / zero error-severity |

### Validation rules (derived from FR-001…FR-005, SC-001)

- **VR-1**: Every fixture is locatable by `find_project_root` (has a
  `manifest.toml`) and `graph build` reports **zero skips / zero
  unknown_keys** (authored to the iteration-6 mapper's recognized keys).
- **VR-2**: `tiny-novel` graph query returns **exactly** 3 `Character`,
  2 `Setting`, 5 `NarrativeEvent` (SC-001).
- **VR-3**: `bookwright validate` on each fixture in its shipped state
  exits 0 with **zero `error`-severity violations** (FR-004); heuristic
  `warning`s are permitted and non-gating (`ValidationReport.failed` keys
  on `error` only). No false-positive *error* on the non-fiction fixtures
  even with the fiction validators active (edge case).
- **VR-4**: No `[PENDING: …]` sentinel survives in any author-fill section
  of a shipped fixture (a fixture is a *finished* minimal project).
- **VR-5**: Fixtures contain plain text only (Markdown/TOML/Turtle-source);
  no materialized skills dir, no committed `graph.ttl` (Principle I, D2).
- **VR-6**: Character/setting **slugs** referenced by `timeline.md`
  `participants:` resolve to a real `bible/characters/<slug>.md`
  (no unresolved participants).

### State / lifecycle

A fixture has one shipped state ("clean / valid"). Tests that need a
*violating* variant derive it **in `tmp_path`** by copying the fixture and
injecting an inconsistency (e.g. an unmentioned character), never by
committing a second broken copy.

---

## E2 — E2E test

An automated test that drives the **real CLI** (in-process `CliRunner`,
D1) over a fixture or a freshly initialized `tmp_path` project and asserts
cross-component behavior. Three files, each a focused contract:

| File | Drives | Asserts | Maps to |
|------|--------|---------|---------|
| `test_full_workflow.py` | `init` → edit manifest+constitution → `graph build` → `graph query` → `validate` | each step's expected result; final state valid | FR-006, SC-002 |
| `test_skills_materialization.py` | `init` (materializes skills) | every `SKILL.md` passes the shipped linter `lint_skill_md` (valid YAML; `name == dir` & `< SKILL_NAME_MAX_LENGTH`; `description < SKILL_DESCRIPTION_MAX_LENGTH`) | FR-007, SC-002 |
| `test_integration_swap.py` | `init --integration claude` → `integration use generic` | skills correct under `.agents/skills/`; manifest records `generic`; **no** assertion about old `.claude/skills/` | FR-008, SC-002 |

### Validation rules

- **VR-7**: E2E tests run in the **default** `pytest` selection and
  therefore contribute to `--cov` (FR-009, D1) — they are not behind a
  `manual`/`slow` marker.
- **VR-8**: Each E2E test file stays **≤ 500 lines** (Constitution
  Principle IV applies to tests too).
- **VR-9**: Where a command exposes `--json`, the E2E assertions parse
  **stdout as a single JSON document** and treat human prose on stderr as
  out-of-band (Principle IX).

---

## E3 — Documentation site

The rendered, navigable set of pages generated from `docs/` by MkDocs
(`material` theme). Spanish-language (clarified 2026-06-03).

### Required page inventory (FR-011, SC-004)

| Page | Content | Notes |
|------|---------|-------|
| `index.md` | what Bookwright is, value prop | landing |
| `getting-started.md` | install + 5-min quickstart (mirrors README.es) | SC-003 |
| `architecture.md` | curated summary linking `bookwright-design.md § N.M` | FR-013, no wholesale dup |
| `commands/…` | one page **or clearly delineated section per shipped command** | FR-012, D4 parity |
| `validation.md` | the 4 built-in validators + how to add a custom one | M3 deliverable |
| `extending.md` | new integration / custom validator / vocabulary | mirrors CONTRIBUTING |
| `faq.md` | common questions | |

### Validation rules

- **VR-10**: `mkdocs build --strict` completes with **zero warnings**
  (FR-014, SC-004) — `strict: true` in `mkdocs.yml` (D5).
- **VR-11**: The documented command set **equals** the registered Typer
  command set (`init`, `check`, `version`, `validate`, `graph build`,
  `graph query`) — enforced by the D4 drift test (FR-015).
- **VR-12**: The architecture page **links** the design doc rather than
  copying it (FR-013).

---

## E4 — Release artifact & metadata

The distributable plus the metadata that constitutes publishable v0.1.0.

| Artifact | Requirement | Maps to |
|----------|-------------|---------|
| wheel + sdist (`uv build` → `dist/`) | buildable; wheel includes `resources/`; installable into clean env | FR-022, SC-007 |
| `CHANGELOG.md` | a `v0.1.0` entry enumerating **every** feature in this release (consolidates the current `[Unreleased]` + iterations 1–11) | FR-016, SC-008 |
| `CONTRIBUTING.md` | how to contribute **+ create a new integration + a custom validator + a vocabulary** | FR-017, SC-008 |
| `LICENSE` | Apache-2.0 present and referenced from `pyproject.toml` (already `license = "Apache-2.0"`) | FR-018, SC-008 |
| `README` | canonical `README.es.md` (qué es, install, 5-min quickstart, docs links); `README.md` may stay a short English pointer | FR-010 |

### Validation rules

- **VR-13**: Every quality gate green on the release branch — `pytest`
  (coverage **≥ 80%**, fail-closed with no round-up via `precision = 2`),
  `ruff check`, `ruff format --check`, `mypy --strict`, `pre-commit`,
  `mkdocs build --strict`, `uv build` (FR-019…FR-022, SC-005, SC-006).
- **VR-14**: The `CHANGELOG` v0.1.0 entry matches the actually-shipped
  command/feature set (Assumptions: `init`, `graph`, `validate`, `check`,
  `version` + the 10 authoring commands) — no feature listed that isn't
  on `main`, none shipped that isn't listed.
- **VR-15**: README/quickstart command names and flags match the shipped
  CLI (FR-015), and the existing draft files are **finalized, not
  regressed** (edge case: existing draft artifacts).

---

## Relationships

```text
E1 Fixture ──input──▶ E2 E2E test ──counts toward──▶ coverage gate (E4 VR-13)
E1 Fixture ──worked example──▶ E3 Docs (getting-started, commands)
E3 Docs ──drift-checked against──▶ shipped CLI (E2 D4 test)
E4 Release ──gated by──▶ E2 E2E pass + E3 strict build + coverage
```

No new code-level domain entity is introduced; all four are
artifact/contract schemas validated by tests and CI gates.
