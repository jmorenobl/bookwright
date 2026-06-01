# Implementation Plan: Bible / Outline / Constitution Templates

**Branch**: `007-project-templates` | **Date**: 2026-06-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-project-templates/spec.md`

## Summary

Replace iteration-4's placeholder stubs with the real authored narrative
templates and add the re-instanceable molds the authoring commands (iter 8–9)
will stamp. Each template is a **literary-technical artifact**: literary in its
Spanish prose, headings, HTML-comment craft guidance, and `[PENDING: …]`
prompts; technical where the iteration-6 indexer reads it — frontmatter aligned
exactly to the GOLEM mapper's recognized keys so a fresh project indexes with
zero skips and zero `unknown_keys`. No Python is written: the deliverable is
documents under `src/bookwright/resources/{project,templates}/` plus a
`CHANGELOG.md`, validated by **format / round-trip** tests (coverage gates N/A
per SC-007). The work conforms to two frozen upstream contracts — the iter-4
scaffold walker and the iter-6 frontmatter reader + bible mapper — and changes
neither (FR-023).

## Technical Context

**Language/Version**: No production Python. Deliverables are Markdown / Jinja2
(`.j2`) / mold (`.tmpl`) documents + `CHANGELOG.md`. Validation tests are
Python 3.11+ (`pytest`), reusing the already-shipped `bookwright.io` reader.

**Primary Dependencies** (test/validation only, all already in the locked set):
`pyyaml` (frontmatter parse), `jinja2` (render the `.j2` skeleton with the
scaffold context), `bookwright.io.frontmatter` / `bookwright.io.bible` (the
iter-6 contract under test). No new runtime dependency — no constitutional
amendment required.

**Storage**: Plain-text files only (Constitution I). Skeleton singletons in
`src/bookwright/resources/project/`; re-instanceable molds in
`src/bookwright/resources/templates/`; `CHANGELOG.md` at repo root.

**Testing**: `pytest` format/round-trip suite under `tests/resources/`:
(1) sentinel-absence sweep over every stamped file, (2) YAML-validity +
allowed-key lint over every authored template, (3) round-trip of a freshly
`init`-ed temp project through `map_bible` asserting zero skips / warnings,
(4) a filled-instance fixture asserting `character.md.tmpl` → one `Character`
and `setting.md.tmpl` → one `Setting`, (5) Jinja2 strict-render of every `.j2`
under the real scaffold context.

**Target Platform**: Cross-platform CLI (darwin/linux CI); files are UTF-8.

**Project Type**: Single project (`src/bookwright/…` + `tests/`), src-layout.

**Performance Goals**: N/A — authoring iteration; no runtime hot path touched.

**Constraints**:
- Files in `project/` keep `.md` (byte-copied) or `.j2` (StrictUndefined
  render); a `.tmpl` there would be stamped literally — forbidden (spec edge,
  walker `_target_relpath`/`render_resource_tree`).
- `.j2` files may reference **only** the scaffold context keys: `title`,
  `project_slug`, `author`, `language`, `integration_key` (StrictUndefined
  aborts otherwise).
- Indexer-ingested frontmatter must use only mapper-recognized keys and
  correctly-typed values (`born`/`died` int-or-omitted; `features`/
  `narrative_roles` string lists; `events:`/`relationships:` exactly the single
  top-level key) so `_coerce_year` / `_coerce_str_list` / `_record_unknown_keys`
  stay quiet.
- Human-facing prose Spanish; frontmatter keys + the `[PENDING]` token
  English (Clarification Q1). `manifest.template.toml` comments stay English
  (verify-only, FR-025).

**Scale/Scope**: ~12 skeleton documents (`project/`) rewritten from stub to real
content, 5 molds authored (`templates/`), 1 `CHANGELOG.md` created, 1 manifest
template verified (not re-authored). No `resolve_template()`, presets, or
extensions (FR-024).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain text as source of truth | ✅ PASS | Deliverables are Markdown/TOML; no binary store introduced. The templates *are* the plain-text artifacts the principle exists to protect. |
| II. Modern Python stack | ✅ PASS | No new runtime dependency. Tests use existing `pyyaml`/`jinja2`/`bookwright.io`. |
| III. src-layout | ✅ PASS | Resources stay under `src/bookwright/resources/…`; tests under `tests/resources/`. |
| IV. Modular command surface | ✅ N/A | No CLI subcommand added or modified (FR-023). |
| V. Plugin-based integrations | ✅ N/A | No integration code touched. |
| VI. Agent Skills only | ✅ PASS | Writes no `commands/` directory; molds are stamped *into* `bible/`/`manuscript/`, not into a skills dir. |
| VII. agentskills.io compliance | ✅ N/A | No `SKILL.md` generated this iteration (skills land in iter 9). |
| VIII. Test discipline (≥80%) | ✅ N/A — no new executable lines | This iteration adds **zero** production Python, so the global `src/bookwright/` coverage figure is mathematically unchanged — there is no deviation to except. Deliverables are prose; validation is by format/round-trip/completeness tests, which are real pytest and run in CI (SC-007). See Complexity Tracking for rationale. |
| IX. JSON-over-stdout | ✅ N/A | No CLI output contract changed. |
| X. Design-document axioms | ✅ PASS | Supersedes design § 6's unified-template layout in favor of the lifecycle split (FR-021, documented in CHANGELOG). § 6 is structural guidance, **not** a § 16 axiom, so no constitutional amendment is required; the divergence is recorded, not litigated. GOLEM/rdflib/plain-text axioms untouched. |

**Gate result**: PASS. No principle is violated. Principle VIII is N/A this
iteration (no executable lines added → global coverage unchanged); the
rationale is recorded in Complexity Tracking and ratified by spec SC-007.

## Project Structure

### Documentation (this feature)

```text
specs/007-project-templates/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output — frontmatter contract + template inventory
├── quickstart.md        # Phase 1 output — how to author/validate a template
├── contracts/           # Phase 1 output
│   ├── frontmatter-contract.md   # iter-6 mapper keys/types the templates must honor
│   ├── skeleton-walker-contract.md  # iter-4 walker rules (.md vs .j2, context keys)
│   └── template-format.md        # cross-cutting authoring rules (Spanish prose, HTML comments, sentinels)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/resources/
├── project/                         # stamped ONCE by `init` (walker: .j2 rendered, rest byte-copied)
│   ├── README.md.j2                 # FR-010 — rewrite guidance prose in Spanish, keep context keys
│   ├── .gitignore                   # FR-011 — review/extend, do not regress
│   └── bible/
│   │   ├── constitution.md.j2       # FR-001 — all § 9.2 sections + [PENDING] + HTML guidance
│   │   ├── timeline.md              # FR-002 — frontmatter `events: []` ONLY; per-event shape in body/comments
│   │   ├── relationships.md         # FR-003 — frontmatter `relationships: []` ONLY
│   │   ├── themes.md                # FR-004 — motif registry, symbol tracker, chapter thematic map
│   │   ├── glossary.md              # FR-005 — invented-terms register, capitalization rules, consistency log
│   │   ├── research.md              # FR-006 — open questions, source notes, resolved findings
│   │   ├── subplots.md              # FR-007 — beat sheets + intersection points
│   │   ├── pov-structure.md         # FR-008 — mode/schedule/voice/asymmetry; "multi-POV only"
│   │   ├── characters/.gitkeep      # (unchanged) destination for stamped character instances
│   │   └── settings/.gitkeep        # (unchanged) destination for stamped setting instances
│   └── outline/
│       ├── arcs.md                  # FR-009
│       ├── structure.md             # FR-009
│       ├── scenes.md                # FR-009
│       └── synopsis.md              # FR-009 — short (250–350w) + long (1000–2000w) sections
└── templates/                       # stamped MANY times by commands (iter 8–9); read directly in v0
    ├── manifest.template.toml       # FR-025 — VERIFY ONLY (already wired into Manifest.build)
    ├── bible/
    │   ├── character.md.tmpl         # FR-012 — frontmatter ⊆ {name,born,died,features,narrative_roles}
    │   ├── setting.md.tmpl           # FR-013 — frontmatter {name} only
    │   └── location.md.tmpl          # FR-014 — sensory anchors; NOT indexed in v0
    ├── manuscript/
    │   └── chapter.md.tmpl           # FR-015 — chapter drafting structure
    └── scenes/
        └── scene.md.tmpl             # FR-016 — scene drafting structure

CHANGELOG.md                         # FR-021 — preset credit + § 6 supersession note (NEW, repo root)

tests/resources/                     # NEW — format/round-trip validation (Python 3.11+, pytest)
├── test_no_stub_sentinels.py        # SC-001 / FR-022
├── test_frontmatter_contract.py     # SC-002 / SC-003 / FR-020 (round-trip via map_bible)
├── test_filled_instance_maps.py     # SC-004 (character/setting mold → GOLEM entity)
├── test_skeleton_renders.py         # FR-010 / spec edge (Jinja2 StrictUndefined render)
└── test_authoring_guidance.py       # SC-005 / FR-017 / FR-018 / FR-019 (lint prose+comments)
```

**Structure Decision**: Single project, src-layout (Constitution III).
Templates are organized by **lifecycle** — `resources/project/` for the
once-per-project skeleton the iter-4 walker stamps, `resources/templates/` for
the re-instanceable molds the commands stamp. This split is the permanent v0
architecture and supersedes design § 6's single `resources/templates/*.tmpl`
directory + 4-layer `resolve_template()` (which only ever existed to serve
presets/extensions that are not expected to ship). Recorded in `CHANGELOG.md`
per FR-021. No new package; molds live beside the existing
`manifest.template.toml`.

## Complexity Tracking

> Filled to record the rationale behind the § 6 layout divergence and to
> document why Principle VIII's coverage gate is N/A (not excepted) here.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle VIII ≥80% line coverage — N/A this iteration (no new executable lines, so the global figure is unchanged) | The deliverable is authored prose (Markdown/Jinja2/mold documents), which has no executable lines to cover. Line coverage would measure nothing real. | Writing throwaway Python to "host" the prose purely to generate coverage would be speculative generality (Scope & Release Discipline) and add a god-module. The honest gate for prose is format/round-trip/completeness — which this plan ships as real pytest, run in CI, asserting the parser-visible contract (SC-002/003/004) and the human-visible contract (SC-001/005). SC-007 pre-authorizes this exception. |
| Layout diverges from design § 6 (unified `templates/` + `resolve_template()`) | The 4-layer resolver's only consumers (presets v0.2, extensions v0.5) are out of v0 scope and not expected to ship; building it now is forbidden plumbing (FR-024, Scope & Release Discipline). | Keeping § 6's layout would require either dead resolver code or stamping literal `*.tmpl` files into every project (walker byte-copies non-`.j2`). The lifecycle split matches what iter-4 already does and needs no new code. Not a § 16 axiom, so no amendment — recorded in CHANGELOG per FR-021. |
