# Implementation Plan: Single prose/structure seam for prose validators

**Branch**: `039-prose-structure-seam` | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/039-prose-structure-seam/spec.md`

## Summary

Three prose validators (`character_presence`, `focalization`,
`setting_continuity`) each re-implement, locally, how to "see past" the Markdown
their own scaffolding emits — a single **class** of defect patched three times
(DEBT-004/007/008). This iteration closes the class at the root: one shared,
Markdown-aware **prose/structure seam** in `io/` (a new `io/prose.py`) that splits
a Markdown source into classified lines **once**, each carrying its 1-based source
number, its **raw** form, and a **normalized** form (the line with its leading
structural block prefix — ATX heading marker or bullet/blockquote marker —
removed, iteratively). `ValidationContext` gains two cached accessors
(`manuscript_view()`, `constitution_view()`) built on the existing `_UNSET`/memo
pattern. The three validators are rewritten on top of the seam and their local
strippers (`_HEADING_MARKER`; `_BULLET`, `_LEAD_EMPHASIS`, `_CLOSE_EMPHASIS`,
`_normalize_declaration_line`, `_PENDING_ONLY`) are **deleted** — no validator
calls `splitlines()` any longer. The decisive proof: a brand-new Markdown surface
(an off-roster name in a `> blockquote`) is handled correctly with **zero**
validator-code change.

Technical approach: a deterministic, regex-based line/block classifier (no
third-party Markdown parser — Constitution II), modelled on `io/frontmatter.py`'s
line-tracking precedent and consumed through `ValidationContext` accessors that
mirror `manuscript_files()` / `constitution_text()`. The seam stays generic
(block-level prefixes only, no validator vocabulary); the label-adjacent emphasis
the old `focalization` strippers handled is folded into `focalization`'s
declaration recognizer, not relocated into the shared seam. Design § 13.4 (issue
#1, facet A).

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II).

**Primary Dependencies**: stdlib `re` and `dataclasses` only — **no new runtime
dependency** (FR-012 / SC-005). Reuses `bookwright.io`, `bookwright.validation.base`.

**Storage**: N/A — the seam is in-memory; it persists nothing (validators stay
graph-free, `triples=()`).

**Testing**: `pytest` (+ `pytest-cov`, ≥ 80% coverage). New `tests/io/test_prose.py`;
extended `tests/validation/test_character_presence.py`,
`test_focalization.py`, `test_setting_continuity.py`. Existing oracles unchanged.

**Target Platform**: CLI library (`src-layout`, `src/bookwright/`).

**Project Type**: Single project (CLI toolkit).

**Performance Goals**: N/A beyond "split each source once per run" — the accessors
memoize, so the per-source split is shared across the three validators.

**Constraints**: byte-for-byte parity with the deleted strippers on every live
fixture (FR-004); locators unchanged (FR-010); every changed/new file ≤ 500 lines
(FR-014); no Markdown library / AST (FR-012).

**Scale/Scope**: One new ~80-line module, two new `ValidationContext` accessors,
three rewritten validators (all already < 210 lines), one new fixture/test for the
generalization surface. No ontology, CLI-surface, or `--json` envelope change.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I — Plain text as source of truth | ✅ Seam reads plain-text Markdown; writes nothing; graph stays a derived cache. The work *deepens* Principle I — validators couple to classified **structure**, not raw surface. |
| II — Modern Python stack / no new dep | ✅ stdlib `re`/`dataclasses` only; deterministic classifier, **not** a Markdown parser/AST (FR-012, SC-005). Dependency set byte-identical. |
| III — src-layout | ✅ New module under `src/bookwright/io/prose.py`; tests under `tests/io/`. |
| IV — Modular surface / ≤ 500 lines | ✅ New module ~80 lines; the three validators stay < 210 lines after the rewrite; `base.py` 256 → ~285 (FR-014). |
| V / VI / VII — integrations / skills | ✅ Untouched (no integration or SKILL.md change). |
| VIII — Test discipline ≥ 80% | ✅ New seam unit tests + extended validator tests; full existing suite stays green with zero oracle edits (SC-001, FR-015). |
| IX — JSON-over-stdout | ✅ No CLI/envelope change; `validate` output byte-identical on existing fixtures. |
| X — Frozen ontology / design axioms | ✅ Prose validators stay graph-free and LLM-free, emit `triples=()`, leave the 17-class GOLEM closure untouched (FR-013). Direction transcribed in design § 13.4. |
| Scope & Release Discipline | ✅ Iteration 039 of the v0.5.0 minor; no speculative plumbing — the seam exposes exactly what the three validators consume (no unused `kind` field, FR-002). Facet B (tri-valued result) is deferred to 040, explicitly out of scope. |

**Result: PASS.** No violations; Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/039-prose-structure-seam/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature spec (already present)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── prose-seam.md    # Phase 1 output — the seam's public contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── io/
│   ├── frontmatter.py        # line-tracking precedent (read-only reference)
│   └── prose.py              # NEW — the prose/structure seam
└── validation/
    ├── base.py               # + manuscript_view() / constitution_view() accessors
    └── validators/
        ├── character_presence.py   # rewritten on the seam; _HEADING_MARKER deleted
        ├── focalization.py         # rewritten; 4 strippers + _PENDING_ONLY deleted
        └── setting_continuity.py   # rewritten to iterate the view

tests/
├── io/
│   └── test_prose.py         # NEW — seam unit tests
└── validation/
    ├── test_base.py                # + manuscript_view()/constitution_view() accessor tests (FR-006)
    ├── test_character_presence.py  # + blockquote generalization surface (US2)
    ├── test_focalization.py        # parity over emphasis/placeholder via the seam
    └── test_setting_continuity.py  # parity over the view
```

**Structure Decision**: Single project, src-layout. The seam lives in `io/`
(alongside `frontmatter.py`) per FR-001 — it is plain-text-in, structure-out, the
same layer `frontmatter.py` occupies. It is consumed only through
`ValidationContext` accessors (FR-006), keeping `validation/` → `io/` the existing
dependency direction (no cycle).

## Complexity Tracking

> No Constitution Check violations. Section intentionally empty.
