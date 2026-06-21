# Implementation Plan: `character_presence` does not flag the first word of a markdown heading

**Branch**: `038-character-presence-heading` | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/038-character-presence-heading/spec.md`

## Summary

The `character_presence` proper-noun heuristic excludes a capital that opens a
line or follows sentence-ending punctuation (`_SENTENCE_END`) as grammatical, but
does not recognize ATX markdown heading syntax: the first word of `# Capítulo 1`
is preceded by the `# ` marker, so `_is_sentence_initial` sees a non-empty,
non-terminal prefix and the word is reported as an unknown proper noun. Every
manuscript with chapter headings hits this on the first `validate`, flooding
`proper noun 'Capítulo' …` warnings (DEBT-008).

**Technical approach**: in `_unknown_mentions`, normalize each scanned line by
stripping a leading ATX heading marker (`^#{1,6}\s+`) **before** running the
existing `_CANDIDATE`/`_is_sentence_initial` heuristic. After the marker is
removed the heading's first content word sits at offset 0, so the *existing*
empty-prefix branch of `_is_sentence_initial` exempts it — no new exemption rule.
The rest of the line is analyzed unchanged, so a real out-of-roster name later in
the title (`Elena` in `# La caída de Elena`) is still flagged. The line number for
the locator comes from `enumerate`, not from the match offset, so stripping the
marker cannot shift any reported `relpath:line`. One module-level compiled regex
plus one inline `_HEADING_MARKER.sub(...)` call inside the existing loop (no new
helper function — the deletable form is preferred, zero-debt doctrine §3); the
inverse (bible→manuscript) direction, the stop-set, the per-name collapsing, and
the `warning` severity are untouched.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II).

**Primary Dependencies**: stdlib `re` only — no new dependency. The change lives
entirely in `src/bookwright/validation/validators/character_presence.py` (203
lines today; well under the 500-line cap, Principle IV).

**Storage**: N/A — prose-level validator. No graph access; `triples=()` on every
emitted `Violation` (FR-009 / Principle X, the frozen GOLEM ontology is untouched).

**Testing**: `pytest`; new cases in `tests/validation/test_character_presence.py`
using the existing `write_project` / `load_context` / `RdflibIndexer` helpers
(`tests/validation/conftest.py`), synthetic in-test manuscripts (Clarifications
2026-06-21 — the scaffold ships an empty manuscript, so there is no live artifact
to bind to).

**Target Platform**: CLI toolkit, cross-platform.

**Project Type**: Single project (`src/bookwright/`, `tests/`), src-layout.

**Performance Goals**: N/A — one extra `re.match` per manuscript line, negligible.

**Constraints**: All four gates green (`ruff check`, `ruff format --check`,
`mypy --strict`, `pytest` ≥ 80 % coverage). Source file ≤ 500 lines.

**Scale/Scope**: One validator module + one test module + one DEBT.md edit. No
new modules, classes, CLI surface, or ontology change.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I — Plain text source of truth | ✅ PASS | No storage change; validator reads plain-text manuscript, graph stays a derived cache. |
| II — Modern Python stack | ✅ PASS | stdlib `re`; no new runtime dependency. |
| III — src-layout | ✅ PASS | Edit under `src/bookwright/`, tests under `tests/`. |
| IV — Modular command surface, ≤ 500 lines | ✅ PASS | One module touched; ~205 lines after the change (one regex + one inline `.sub()` call, no new function). |
| V — Plugin integrations | ✅ N/A | No integration change. |
| VI — Agent Skills only | ✅ N/A | No skill change. |
| VII — agentskills.io compliance | ✅ N/A | No SKILL.md change. |
| VIII — Test discipline ≥ 80 % | ✅ PASS | Two new unit tests (heading-initial exempt; in-heading-body name flagged); existing fixtures unchanged (FR-003 parity). |
| IX — JSON-over-stdout | ✅ N/A | No CLI output shape change; `Violation` fields byte-identical. |
| X — Design axioms / frozen ontology | ✅ PASS | Prose validator, no graph write, `CLASS_IRI`/`golem.ttl` untouched (FR-009). |

**Scope discipline**: the heading-marker recognizer stays **local** to
`character_presence.py` — no shared markdown-stripping utility, no parallel
exemption rule. Building either would be plumbing whose only justification is a
hypothetical future consumer (Scope & Release Discipline; zero-debt doctrine §2).
The recognizer handles only the ATX `^#{1,6}␠` form that causes the defect; setext
and indented forms are out of scope (their first word is already line-initial or
analyzed-as-prose, so they do not trigger the bug).

**Result**: PASS — no violations, Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/038-character-presence-heading/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

(No `contracts/` — the `--json` validate envelope and the `Violation` shape are
unchanged, so there is no new interface contract to document.)

### Source Code (repository root)

```text
src/bookwright/validation/validators/
└── character_presence.py        # MODIFIED: add `_HEADING_MARKER` regex + an
                                 #   inline `.sub()` to strip it before the
                                 #   heuristic in `_unknown_mentions` (no new
                                 #   helper function). No other change.

tests/validation/
└── test_character_presence.py   # MODIFIED: + heading-initial-exempt test
                                 #   (FR-006) and in-heading-body-name-flagged
                                 #   test (FR-007).

DEBT.md                          # MODIFIED: remove DEBT-008; "Deuda abierta"
                                 #   becomes "_Ninguna por ahora._" (FR-008).
```

**Structure Decision**: Single project, src-layout. The change is confined to one
validator module and its test module, plus the debt-ledger edit — matching the
per-iteration patch shape the v0.4.x track established.

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
