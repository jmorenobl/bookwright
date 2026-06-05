# Implementation Plan: Traceability Tag Cleanup

**Branch**: `017-traceability-tag-cleanup` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/017-traceability-tag-cleanup/spec.md`

## Summary

Cancel the traceability-tag debt that CONTRIBUTING.md § "Traceability tags in
code" forbids: every `T0xx` (a `tasks.md` task ID) and `US-x` / `USx` / `+USx`
(user-story / backlog tag) under `src/` and `tests/` is removed, and a single
`pytest` gate pins the count at zero forever.

The deterministic sweep
(`grep -rnIE '\bT0[0-9]{2}\b|\bUS-?[0-9]+\b|\+US[0-9]+' src/ tests/`) finds
**73 occurrences on 67 lines across 48 files** (46 `.py` + 2 `.toml`
fixtures). Every hit is in a `#` comment or a `"""docstring"""` — **none in a
test name, assertion, or string literal** — so the comment-only mandate
(FR-008) and the reach-zero mandate (FR-001/FR-002) never collide.

The central planning finding (see [research.md](research.md)): **no hit
requires inventing a durable reference by reading an owning spec.** Every tag
that carried genuine traceability already co-locates its durable `FR`/`SC`/`D`
ref on the same line, so the conversion is a pure *strip-token* (delete only
the forbidden token, freeze the surrounding refs per FR-007). The remainder
are decorative section markers / docstring headers (→ *relabel* to a
behaviour description, FR-005) or bare bookkeeping parentheticals (→ *remove*,
FR-004). This collapses the whole iteration into four mechanical edit classes
applied comment-by-comment, with `git diff` confirming only comments/docstrings
change.

**Approach**: classify all 67 lines into {strip-token, relabel, remove,
neutral-prose}, edit file-by-file, then add `tests/meta/test_no_traceability_tags.py`
— a gate that re-runs the same regex over `src/`+`tests/` and asserts zero
matches, excluding only itself. The gate rides `uv run pytest` and therefore
CI (Principle VIII); no pre-commit hook, no ruff rule (per Clarifications).

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: none added. Gate uses stdlib `re` + `pathlib` only.

**Storage**: N/A — no data model, no manifest, no graph change.

**Testing**: `pytest` (the gate is itself one test; existing suite must stay
green with coverage unchanged).

**Target Platform**: developer machines + GitHub Actions CI (Linux).

**Project Type**: single project — Python CLI (`src/bookwright/`, `tests/`).

**Performance Goals**: N/A. The gate walks ~250 text files once; sub-second.

**Constraints**: edits MUST be confined to comments/docstrings (FR-008);
observable behaviour and coverage MUST be unchanged (FR-009, SC-003);
no file under `specs/` may be touched and no existing `FR`/`SC`/`D` number
renumbered (FR-007, FR-012, SC-005).

**Scale/Scope**: 67 lines / 48 files to edit + 1 new test file. No `src/`
*logic* change (the only `src/` edits are two comment/docstring lines:
`core/_research_block.py:1` and `integrations/base.py:11`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Verdict | Note |
|---|---|---|
| I. Plain text as source of truth | ✅ Pass | No storage/cache change. |
| II. Modern Python stack | ✅ Pass | No new dependency; gate uses stdlib `re`/`pathlib`. |
| III. src-layout | ✅ Pass | New gate lives under `tests/`; no prod code added. |
| IV. Modular command surface (≤500 lines) | ✅ Pass | Gate is a single small test module; no CLI verb touched. |
| V. Plugin-based integrations | ✅ Pass | No integration change. |
| VI. Agent Skills only | ✅ Pass | No skill change; no `commands/` dir written. |
| VII. agentskills.io compliance | ✅ Pass | No `SKILL.md` change. |
| VIII. Test discipline (≥80%, CI) | ✅ Pass | Gate *is* a test on `uv run pytest`/CI; comment-only edits leave executed lines and coverage unchanged (SC-003). |
| IX. JSON-over-stdout | ✅ Pass | No CLI command added/changed. |
| X. Design-document axioms | ✅ Pass | No axiom reopened. |
| Scope & Release discipline | ✅ Pass | Hygiene/debt cleanup enforcing CONTRIBUTING.md; adds no deferred-capability plumbing. |

**Result**: no violations. Complexity Tracking left empty.

A note on Scope discipline: this is a maintenance iteration (it ships no new
user-facing capability), justified directly by the CONTRIBUTING.md policy it
enforces. It is not speculative generality — the gate exists to keep an
already-stated rule true, not to enable a future feature.

## Project Structure

### Documentation (this feature)

```text
specs/017-traceability-tag-cleanup/
├── plan.md              # This file (/speckit-plan)
├── research.md          # Phase 0 — full per-line classification + decisions
├── data-model.md        # Phase 1 — the four edit classes + gate entities
├── quickstart.md        # Phase 1 — how to run the sweep + gate locally
├── contracts/
│   └── no-regression-gate.md   # Phase 1 — the gate's behavioural contract
├── spec.md
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── core/_research_block.py        # 1 docstring line edited (strip-token)
└── integrations/base.py           # 1 comment line edited (remove)

tests/
├── meta/
│   └── test_no_traceability_tags.py   # NEW — the no-regression gate (FR-010)
├── commands/        # init/* + graph/* docstring headers + markers
├── core/            # manifest test docstrings + 2 .toml fixtures
├── e2e/             # research-workflow group markers
├── golem/           # provenance section markers
├── integrations/    # materialization test docstrings
├── io/              # research reader test markers
├── resources/       # command-body test docstring
└── validation/      # validator test docstrings + markers
```

**Structure Decision**: Single-project Python CLI; unchanged. The gate is
placed at `tests/meta/test_no_traceability_tags.py` — a new `meta/` package for
repo-hygiene tests that assert *about the tree* rather than about a `src/`
unit. `pytest` discovers it with no config change. The gate excludes exactly
one path from its scan (its own `__file__`); the forbidden patterns, stored as
a compiled regex, provably do not match their own source (verified — the
`[0-9]` character classes break the digit run), so self-exclusion is
belt-and-suspenders, not load-bearing.

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
