# Implementation Plan: `bookwright-research` consumes the status research queue

**Branch**: `021-research-status-queue` | **Date**: 2026-06-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/021-research-status-queue/spec.md`

## Summary

When the `bookwright-research` skill is invoked **without** an explicit topic, it
must stop greeting the author with a blank "what shall we research?" and instead
surface the work the project already knows is pending — its open research
questions and its unresolved anchors — as a numbered queue, then let the author
pick from it or name a new topic. That queue is already computed by
`bookwright status` (iteration 020). This iteration teaches the skill's protocol
to consult it.

The change is **prose-only**: a single conditional first step is added to the
authoring protocol in `src/bookwright/resources/commands/bookwright-research.md`.
With a topic given, the step is skipped and the established top-down procedure
runs unchanged. With no topic, the step runs `bookwright status --json`, reads
the raw `state.open_questions` and `state.unresolved_anchors` facts (never the
`next_actions[]` prompt — clarification #1), presents them grouped and numbered
with a soft cap, and offers the "research these N / a new topic" choice; an
empty or unavailable queue degrades to today's ask-the-topic fallback. Once a
topic is determined the existing seven-step procedure runs unchanged, repeated
per item for a multi-item selection.

No Python source changes. The updated source is re-materialized into a
lint-passing `SKILL.md` for both `claude` and `generic` through the **unchanged**
iteration-9 pipeline (`generate_skill_md` / `iter_command_sources`). Verification
adds one contract test asserting the body now references `bookwright status`; the
existing `test_research_skill.py` already proves both-integration materialization
and lint compliance.

## Technical Context

**Language/Version**: Python 3.11+ (no code change; the artifact edited is a
packaged Markdown resource read at runtime via `importlib.resources`).

**Primary Dependencies**: none new. Touches only the existing materialization
seam (`bookwright.integrations.materialize`) and lint gate
(`bookwright.integrations.lint.lint_skill_md`) — both unchanged.

**Storage**: plain-text command source
(`src/bookwright/resources/commands/bookwright-research.md`); its cited
`references/research-format.md` is unchanged and travels with the skill.

**Testing**: `pytest`. New: a contract assertion that the materialized/source
body references `bookwright status`. Reused as-is:
`tests/integrations/test_research_skill.py` (both-integration materialize + lint),
`tests/resources/test_command_budget.py` (body < 5000-token budget),
`tests/integrations/test_descriptions.py` (description-table mirror,
bilingual trigger).

**Target Platform**: agent runtimes consuming agentskills.io `SKILL.md`
(Claude Code, generic).

**Project Type**: single CLI package + packaged Agent-Skill resources.

**Performance Goals**: N/A. The only added runtime cost is the agent issuing one
`bookwright status --json` call on the no-topic path; the top-down path adds
nothing (FR-004 / SC-004).

**Constraints**: body MUST stay < 5000 approx-tokens (current ~1135, ample
headroom); description MUST keep both ES and EN trigger phrasings (FR-008 /
SC-005); change confined to the `bookwright-research` source — no edit to
`bookwright status` or any other skill (FR-009); materialized `SKILL.md` MUST
stay within agentskills.io front-matter/length bounds so `lint_skill_md` passes
(FR-011 / SC-006).

**Scale/Scope**: one Markdown file edited; one test added. No new module, no
pipeline duplication.

## Constitution Check

*GATE: evaluated against constitution v1.4.0. Re-checked post-design.*

| Principle | Verdict | Notes |
|---|---|---|
| I — Plain text as source of truth | ✅ | The edit is Markdown; the queue is read fresh from `status` each run, never cached by the skill (spec assumption). No binary store. |
| II — Modern Python stack | ✅ | No dependency added; no code changed. |
| III — src-layout | ✅ | Edited file is under `src/bookwright/resources/`; tests under `tests/`. |
| IV — Modular command surface | ✅ | No CLI module touched; no file approaches 500 lines. |
| V — Plugin-based integrations | ✅ | Materialization uses the existing `SkillsIntegration` registry; no new integration. |
| VI — Agent Skills only | ✅ | Output remains a single `SKILL.md`; no `commands/` directory written. |
| VII — agentskills.io compliance | ✅ | `name`/`description` bounds unchanged; body grows by < ~250 tokens, far under budget; `lint_skill_md` gate enforced by reused test. |
| VIII — Test discipline (≥ 80 %) | ✅ | Behavior is prose; verification is the materialization-compliance + contract assertion the constitution names as the sound mode for Agent-Skill legs (§ VIII). No `src/` lines added ⇒ no coverage regression. |
| IX — JSON-over-stdout | ✅ | The skill instructs the agent to call the **existing** `bookwright status --json` contract (iteration 020); it adds no new CLI surface and parses the documented `state.*` facts. |
| X — Design-document axioms | ✅ | Reopens nothing in § 16; this is the § 21 context-orchestration line, iteration 021. |

**Scope & Release discipline**: squarely inside v0.3 / M5 (design § 21),
iteration 021 — the first status-consuming skill. No deferred/cancelled
capability is pulled in; no "future X" plumbing. **PASS.**

No violations → Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/021-research-status-queue/
├── plan.md              # This file
├── spec.md              # Feature spec (already present)
├── research.md          # Phase 0 — decisions below
├── data-model.md        # Phase 1 — the queue as the skill reads it
├── quickstart.md        # Phase 1 — manual validation script
├── contracts/
│   └── research-skill.md # Phase 1 — the added body-protocol invariants + test map
└── tasks.md             # Phase 2 (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
src/bookwright/resources/commands/
└── bookwright-research.md      # EDITED — the conditional status-queue first step

tests/integrations/
└── test_research_skill.py      # EXTENDED — assert body references `bookwright status`
                                #   (both-integration materialize + lint already covered here)
```

Everything else — the iteration-9 materialization pipeline
(`src/bookwright/integrations/materialize.py`), the lint gate
(`integrations/lint.py`), the description table (`integrations/descriptions.py`),
and the `bookwright status` command (`commands/status.py`) — is **read/reused,
not modified**.

**Structure Decision**: Single-package CLI with packaged skill resources. The
only production artifact in scope is the one Markdown command source; the only
test artifact is the contract extension. No structural change.

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
