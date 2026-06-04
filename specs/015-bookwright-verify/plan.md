# Implementation Plan: `bookwright-verify` Skill

**Branch**: `015-bookwright-verify` | **Date**: 2026-06-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/015-bookwright-verify/spec.md`

## Summary

Add a twelfth source command, `bookwright-verify.md`, to the packaged
`resources/commands/` tree. It is the **semantic** half of the § 20.6 two-layer
verification design: a read-only, post-draft LLM check that has the agent load the
project's research **anchors** (and the **sources** behind them) from the derived
graph, read the **manuscript**, and report passages that *contradict* what was
researched — anachronisms, procedural errors, and cultural/linguistic
inaccuracies — organised by chapter/scene, each finding carrying the quoted
passage, the violated anchor, the anchor's source, a severity
(`error`/`warning`/`info`), and a `file:line` reference where the location is
known. It writes nothing; the author decides what to fix.

The single load-bearing engineering fact (and the one the "zero technical debt"
directive turns on) is that **this iteration adds no new Python logic**. The
iteration-9 materializer (`integrations/materialize.py`) already discovers every
`*.md` under `resources/commands/` via `iter_command_sources()` and turns each into
a per-skill `SKILL.md` in both integrations, copying cited `references/`, enforcing
the agentskills.io caps via `lint_skill_md`, and routing the description through the
authoritative `SKILL_DESCRIPTIONS` table. So `bookwright init` scaffolds the new
skill in both integrations the moment the source file exists — *with no
special-casing* (FR-002, FR-017).

The work is therefore: (1) author one Spanish command-source `.md` modelled
structurally on `bookwright-continuity` (the analogous read-only post-draft report),
and (2) keep the **four manually-maintained command rosters** in lock-step so the
new command is admitted, described, and classified report-only. Three of those
rosters are hand-written set/tuple literals (not derived) and would otherwise fail
CI loudly; the other two roster sites are auto-derived from `iter_command_sources()`
and need no edit. That roster-coherence step is the whole risk surface and the plan
makes it explicit so `/speckit-tasks` cannot miss a site.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II / Technical Constraints). No
Python *behaviour* is added; the only `.py` edits are roster-literal additions and
the description-table entry.

**Primary Dependencies**: none new. The skill body cites `bookwright graph build`
and `bookwright graph query` (the iteration-6 indexer CLI) and reads `manuscript/`;
all reasoning is performed by the consuming agent. No network, no search engine, no
runtime dependency is introduced (FR-014, Constitution II — a new dep would need an
amendment; none is needed).

**Storage**: none. The command is read-only (FR-009, FR-010): the agent runs
`graph build` (refreshing the derived `bible/graph.ttl` cache — Constitution I),
queries it, reads the manuscript, and emits the report as its response. Nothing is
persisted to the project (SC-005).

**Testing**: `pytest`. The new command is **data**, exercised by the existing
data-driven sweeps that parametrize over `command_files()` /
`iter_command_sources()` (frontmatter contract, bilingual activation, body
sections, report-only statement, materialization into both integrations + lint).
Adding the source file extends every parametrized sweep to cover it; the four
roster sites are updated so the inventory/equality gates pass. Coverage gate ≥ 80 %
single-sourced in `[tool.coverage.report]` — unchanged (SC-008).

**Target Platform**: cross-platform CLI (`bookwright init` materializes the skill;
the skill itself runs inside any agentskills.io-compliant agent).

**Project Type**: single project, src-layout (`src/bookwright/`, `tests/`).

**Performance Goals**: N/A. Materialization writes one extra ~3 KB skill dir per
integration at `init` time; negligible.

**Constraints**: read-only (FR-010); Spanish body with the eight required sections
(the iteration-8 command-source contract); bilingual ES/EN trigger description
< 1024 chars matching its directory name (FR-003, FR-004, Constitution VII); adds
**no** GOLEM ontology class and no new integration (FR-012 assumptions, Constitution
V, X); the source file ≤ 500 lines (Principle IV — it is ~70 lines).

**Scale/Scope**: one new command-source `.md`, one `SKILL_DESCRIPTIONS` entry, two
test-roster literal additions, two `helpers` tuple additions, and one
inline-graph-build test tightened to include `bookwright-verify`. No CLI surface
change, no manifest schema change, no new vocabulary, no new module.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain text as source of truth | ✅ PASS | The command source is Markdown; it instructs the agent to refresh the derived `graph.ttl` cache (`graph build`) and query it. The graph stays a derived cache; the command writes nothing. |
| II. Modern Python stack | ✅ PASS | No new runtime dependency. The skill instructs; it does not fetch or import anything (FR-014). |
| III. src-layout | ✅ PASS | New data under `src/bookwright/resources/commands/`; test edits under `tests/`. No production module added or moved. |
| IV. Modular command surface | ✅ PASS | No new CLI subcommand. The new source `.md` is ~70 lines; the touched `.py` files (`descriptions.py` +1 entry; test rosters) stay well under 500 lines. |
| V. Plugin-based integrations | ✅ PASS | Materialized into the two shipped integrations (`claude`, `generic`) by the existing `SkillsIntegration` pipeline. No new integration, no dispatcher. |
| VI. Agent Skills only | ✅ PASS | The command materializes to exactly one `SKILL.md` per integration; nothing is written to `commands/`-style dirs. `commands/` ships only `.md` (frontmatter test guard). |
| VII. agentskills.io compliance | ✅ PASS | `name` == dir, `name`/`description` under caps, valid YAML, body within token budget — all enforced by the shipped `lint_skill_md` gate the materializer already runs (FR-003). |
| VIII. Test discipline (≥ 80 %) | ✅ PASS | Covered by the existing data-driven sweeps (materialization in both integrations + lint = the agentskills.io E2E mode the v1.3.0 amendment names for authoring skills) plus the roster equality/inventory gates. Coverage gate unchanged and single-sourced (SC-008). |
| IX. JSON-over-stdout | ✅ N/A | This is an LLM skill, not an agent-consumed `--json` subcommand; it adds no JSON envelope of its own (FR-009), exactly like `bookwright-continuity`. The `bookwright graph build`/`graph query` calls it cites already honour Principle IX. |
| X. Design-document axioms | ✅ PASS | No GOLEM class added; no axiom reopened. The skill reads the existing `bw:`/CIDOC vocabulary iterations 012–013 emit. |
| Scope & release discipline | ✅ PASS | This is the M4/v0.2 `bookwright-verify` iteration (design § 10.4, § 20.6). It deliberately adds **no** auto-fix, **no** structural anchor re-audit (that is iteration 014's `factual_anchor`), and **no** vector search (v0.3). Docs (`docs/authoring.md`, `docs/research.md`) and the historical E2E fixture are explicitly iteration 17's scope and are not pulled in here. No "future X" plumbing. |

**Result: PASS — no violations. Complexity Tracking left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/015-bookwright-verify/
├── plan.md              # This file
├── research.md          # Phase 0 — design decisions (D1..D8)
├── data-model.md        # Phase 1 — command-source + report-shape "entities"
├── quickstart.md        # Phase 1 — author + materialize + run the skill end-to-end
├── contracts/
│   └── bookwright-verify-skill.md   # The skill's behavioural contract
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── resources/commands/
│   └── bookwright-verify.md         # NEW: the source command (Spanish, 8 sections,
│                                    #      report-only; cites graph build + graph query)
└── integrations/
    └── descriptions.py              # EDIT: + "bookwright-verify" entry in SKILL_DESCRIPTIONS
                                     #       (verbatim mirror of the source frontmatter — SC-009)

tests/
├── resources/
│   ├── helpers.py                   # EDIT: + "bookwright-verify" in EXPECTED_COMMANDS
│   │                                #       and in REPORT_ONLY_COMMANDS
│   └── test_command_body.py         # EDIT: add "bookwright-verify" to the inline
│                                    #       graph-build parametrize (it builds + queries)
└── integrations/
    ├── test_descriptions.py         # EDIT: + "bookwright-verify" in _ROSTER literal
    └── test_materialize.py          # EDIT: + "bookwright-verify" in _ROSTER literal
```

**No-edit / auto-derived sites (called out so `/speckit-tasks` does not duplicate
work):** `integrations/materialize.py::iter_command_sources` globs the directory, so
it picks up the new file with no edit; `tests/integrations/test_setup_materialize.py`
and `tests/commands/init/test_e2e_materialize.py` derive their `_ROSTER` from
`iter_command_sources()` and so extend automatically; the frontmatter / activation /
body sweeps parametrize over `command_files()` and so cover the new file the moment
it lands (provided it satisfies their contract — that is what the source must be
authored to do).

**Structure Decision**: single project, src-layout. The command source follows the
*exact* shape of the four shipped report-only commands (`clarify`, `analyze`,
`continuity`, `checklist`), with `bookwright-continuity` as the structural template
per the spec and the § 20.6 analogy: same eight Spanish sections, same explicit
"solo lectura / no escribe nada" statement, same "prerrequisito ausente" handling,
same inline `bookwright graph build`. The only structural difference from continuity
is **what it reads against** (research anchors via `graph query`, not the bible) and
the **report shape** (anchor + source + severity per finding).

## Phase 0 — Research

See [research.md](research.md). The spec's two Clarifications (the
`error`/`warning`/`info` severity scale and the build-then-query graph access) are
already closed there; Phase 0 records the design decisions that turn the
requirements into an authored command source and a coherent roster edit — most
load-bearing being **D1** (no new Python logic; the iteration-9 pipeline carries it),
**D2** (the four manual roster sites and how each gate would fail), and **D3** (the
authoritative bilingual `description` string, drafted once so the source frontmatter
and the `SKILL_DESCRIPTIONS` table are byte-identical for the SC-009 equality gate).

## Phase 1 — Design & Contracts

- [data-model.md](data-model.md) — the command source as a structured document
  (the eight sections and what each must contain), the report shape (chapter/scene
  grouping; the four required parts per finding; the severity rubric), and the
  graph read surface (the `bw:Anchor`/`bw:Source` SPARQL projection the body cites).
- [contracts/bookwright-verify-skill.md](contracts/bookwright-verify-skill.md) —
  the skill's behavioural contract: the frontmatter invariants
  (`name`==dir, caps, forbidden keys), the materialization guarantee in both
  integrations, the bilingual trigger set, the procedure the body must instruct, the
  report contract, and the two absent-prerequisite branches (no manuscript / no
  anchors). Doubles as the acceptance reference for `/speckit-tasks`.
- [quickstart.md](quickstart.md) — author the source, run the targeted sweeps and
  `bookwright init`, confirm a valid `bookwright-verify/SKILL.md` in both
  `.claude/skills/` and `.agents/skills/`, then run the skill against a project with
  a violating manuscript and a clean one.

### Agent context update

The CLAUDE.md "current plan" pointer (between the `<!-- SPECKIT START -->` /
`<!-- SPECKIT END -->` markers) is updated to reference this plan.

## Complexity Tracking

> No Constitution Check violations — this section is intentionally empty.
