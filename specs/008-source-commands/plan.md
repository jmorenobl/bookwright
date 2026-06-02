# Implementation Plan: The 10 Bookwright Command Source Prompts

**Branch**: `008-source-commands` | **Date**: 2026-06-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-source-commands/spec.md`

## Summary

Author the **10 command source prompts** under `src/bookwright/resources/commands/<name>.md`
(constitution, bible, outline, scenes, draft, synopsis, clarify, analyze, continuity,
checklist) plus the `references/` directory holding the heavy domain context they cite.
Each command is a self-contained Markdown instruction set (English YAML frontmatter +
Spanish body) that an AI agent executes verbatim against an initialized Bookwright
project — the creative interface of the toolkit.

This iteration is **prompt authoring, not code**: no production Python ships, no
per-integration `SKILL.md` is materialized (iteration 9), no helper scripts are written.
The technical approach: start from the annotated `bookwright-design.md` § 10.1 example,
adapt it to the § 10.4 contract for each of the 10 commands, offload domain depth to
`references/*.md` (tier-3 progressive disclosure), and ship an automated validation suite
that gates the agentskills.io format constraints (parseable frontmatter, `description`
< 1024 chars, non-empty body < 5000 tokens, required body sections, no dangling references,
zero out-of-scope artifacts).

## Technical Context

**Language/Version**: No production code. Deliverables are Markdown documents
(`src/bookwright/resources/commands/*.md` + `references/*.md`). Validation tests are
Python 3.11+ / pytest.

**Primary Dependencies**: Test-side only — `pytest` (already dev-dep) and the shipped
`bookwright.io.frontmatter.parse_frontmatter` (iteration 6) to validate frontmatter.
No new **runtime** dependency (Constitution II). `tiktoken` is **not** added; token
counting uses a char-based approximation, opportunistically upgrading to `tiktoken`
only if it is already importable in the environment (FR-015).

**Storage**: Plain-text Markdown under the packaged resource tree. No binary store
(Constitution I).

**Testing**: `pytest` parametrized over the 10 command sources + the references roster,
asserting FR-030 format gates and FR-029 reference resolution. Activation precision
(US3 / SC-003) is a hand-run A/B battery, backstopped by a lightweight keyword-presence
test.

**Target Platform**: Cross-agent (the sources are integration-agnostic; materialization
to a specific agent is iteration 9).

**Project Type**: Single project (CLI toolkit). Resources live under `src/bookwright/resources/`.

**Performance Goals**: N/A (static documents). The only quantitative bars are the format
budgets: `description` < 1024 chars, body < 5000 tokens.

**Constraints**: agentskills.io tier-2 budget (body < 5000 tokens), `description` < 1024
chars, `name` = base filename = future parent-directory name (Constitution VII). Bodies in
Spanish; frontmatter keys + the `[PENDING: …]` token in English (bilingual convention).
No `scripts:` block, no `handoffs:` block in source (FR-005, FR-006).

**Scale/Scope**: 10 command source files + a `references/` roster (~6 files) + one
validation test module group. Each body targets well under the 5000-token ceiling (aim
≤ ~3500 tokens) to leave headroom.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Relevance | Status |
|---|---|---|
| I. Plain Text as Source of Truth | All deliverables are Markdown. | ✅ PASS |
| II. Modern Python Stack | No new runtime dep; `tiktoken` deliberately not added (test-side, optional). | ✅ PASS |
| III. src-layout | Sources under `src/bookwright/resources/commands/`; tests under `tests/`. | ✅ PASS |
| IV. Modular Command Surface | No CLI module added; 500-line rule N/A to prompts (but each body ≪ 500 lines anyway). | ✅ PASS |
| V. Plugin-Based Integrations | Sources are integration-agnostic; no integration code touched. | ✅ PASS |
| VI. Agent Skills Only — No Legacy Commands | This iteration writes **no** `SKILL.md` and **nothing** under any `skills_dir`; it produces the *source* the materializer (iter 9) consumes. Writing to `.claude/commands/` etc. is forbidden and explicitly out of scope (FR-031). | ✅ PASS |
| VII. agentskills.io Compliance | The validation suite enforces `name`=basename, `description`<1024, tier-2 body budget, references offload — the exact constraints (FR-002, FR-004, FR-015, FR-028). | ✅ PASS |
| VIII. Test Discipline | Format/reference validation suite ships with the sources; no production code → no coverage delta to defend, but the deliverables are themselves asserted. | ✅ PASS |
| IX. JSON-over-stdout | Bodies that invoke the CLI call `bookwright graph build --json` inline and consume the JSON (FR-017); they never assume a wrapper. | ✅ PASS |
| X. Design Document Axioms | Honors § 16 (Agent Skills only, no shell scripts, plain text). No axiom reopened. | ✅ PASS |

**Scope & Release Discipline**: All deliverables are M2 (iteration 8). No deferred
capability (presets, Grafeo, extra integrations, export) is pulled forward. The
`handoffs`/`scripts` blocks from the § 10.1 illustration are intentionally **excluded**
from the source (deferred to iter-9 materialization) — see FR-006, clarifications.

**Result**: PASS — no violations, Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/008-source-commands/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (command-source + reference entities)
├── quickstart.md        # Phase 1 output (how to author + validate one command)
├── contracts/
│   ├── command-source.md     # Frontmatter + body-section schema (FR-003..FR-014)
│   └── validation.md         # The FR-030 automated gate contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/resources/commands/
├── bookwright-constitution.md   # generative   → bible/constitution.md
├── bookwright-bible.md          # generative   → full bible set (one pass)
├── bookwright-outline.md        # generative   → outline/{arcs,structure,synopsis}.md
├── bookwright-scenes.md         # generative   → outline/scenes.md
├── bookwright-draft.md          # generative   → manuscript/cap-NN.md (scene section)
├── bookwright-synopsis.md       # generative   → outline/synopsis.md (short+long)
├── bookwright-clarify.md        # report-only  → question list
├── bookwright-analyze.md        # report-only  → pre-draft cross-artifact report
├── bookwright-continuity.md     # report-only  → post-draft report (builds graph)
├── bookwright-checklist.md      # report-only  → artifact completeness report
└── references/
    ├── golem-character.md            # G1_Character fields + frontmatter contract
    ├── golem-relationships.md        # G4 social relationships / roles (reified)
    ├── golem-events-timeline.md      # G5 events + timeline.md frontmatter contract
    ├── propp-functions.md            # Propp functions + dramatis personae
    ├── greimas-actants.md            # Greimas actantial model
    └── pending-protocol.md           # shared [PENDING:…]-vs-ask + YAML-quoting rule

tests/resources/
├── helpers.py                   # EXTEND: add COMMANDS_DIR + command/reference enumerators
├── test_command_frontmatter.py  # FR-003/004/005/006: parseable, name=basename, <1024, no scripts/handoffs
├── test_command_body.py         # FR-007..FR-014: required sections present, non-empty, Spanish
├── test_command_budget.py       # FR-015: body < 5000 tokens (tiktoken-if-present else char approx)
├── test_command_references.py   # FR-028/FR-029: references/ exists, every cited path resolves
└── test_command_activation.py   # SC-003 backstop: each description carries ES+EN triggers
```

**Structure Decision**: Single-project layout. The 10 sources and their `references/`
subtree live under the existing `src/bookwright/resources/` packaged tree (already
force-included into the wheel via `pyproject.toml [tool.hatch.build.targets.wheel.force-include]`).
Validation extends the existing `tests/resources/` suite (iteration 7's template-validation
home) rather than introducing a new top-level test package, reusing its `helpers.py`
enumerator pattern and the shipped `parse_frontmatter` reader.

## Complexity Tracking

> No Constitution violations. Section intentionally empty.

## Phase 0: Outline & Research

See [research.md](research.md). Resolved decisions:

1. **Token measurement** — char-based approximation (`len/4`, asserted < 5000) as the
   deterministic default; `tiktoken` used only if already importable. No new dependency.
2. **Reference roster** — six files (above), each cited by ≥1 body; FR-029 (no dangling
   references) is the binding rule, the roster may consolidate during implementation as
   long as every cited path resolves.
3. **`[PENDING: …]` vs stop-and-ask** — extract the shared rule into
   `references/pending-protocol.md`; every generative body links to it (keeps bodies under
   budget, single source of truth, matches iteration-7 marker convention).
4. **Description authoring for activation precision** — bilingual, intent-led, with explicit
   sibling-disambiguation phrasing (constitution≠bible, analyze≠continuity, clarify≠checklist).
5. **No `handoffs`/`scripts`** — confirmed by clarification; "next step" hints appear as body
   prose, not frontmatter.

## Phase 1: Design & Contracts

- **[data-model.md](data-model.md)** — the *Command source*, *Reference file*, *Description*,
  and *`[PENDING]` marker* entities, their fields and validation rules (derived from the
  spec's Key Entities + FR-003..FR-016a).
- **[contracts/command-source.md](contracts/command-source.md)** — the authored-document
  contract: required frontmatter keys, forbidden keys, the eight required body sections,
  the inline-CLI rule, the marker rule.
- **[contracts/validation.md](contracts/validation.md)** — the FR-030 automated gate: what
  each test asserts, the token-budget method, the reference-resolution check.
- **[quickstart.md](quickstart.md)** — author-and-validate loop for one command end-to-end.
- **Agent context update** — repoint the plan reference in `CLAUDE.md` (between the
  `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->` markers) to this plan.

**Output**: research.md, data-model.md, contracts/*, quickstart.md, updated CLAUDE.md.
