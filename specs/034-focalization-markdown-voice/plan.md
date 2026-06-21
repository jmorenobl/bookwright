# Implementation Plan: `focalization` tolerates markdown-prefixed voice declaration

**Branch**: `034-focalization-markdown-voice` | **Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/034-focalization-markdown-voice/spec.md`

## Summary

The `focalization` validator's declaration regex (`_DECLARATION`,
`focalization.py:24`) anchors the label `voz narrativa|narrative voice` to the
start of line, so it never matches the **markdown-prefixed** form its own
scaffold emits (`- **Voz narrativa**: …`). The validator therefore silently
returns zero findings for every author who fills the constitution as generated
(DEBT-004), and is dormant on all five voice-bearing fixtures.

Technical approach: **normalize the candidate line before matching** rather than
bolt optional groups onto the existing pattern. The recognition step strips a
single line-leading bullet/blockquote marker (`-`, `*`, `+`, `>`) plus
surrounding whitespace, then strips the named emphasis markers (`*`, `**`, `_`)
independently from each side of the label region, and only then applies the
existing label-and-body pattern. The body-extraction logic (person / limited /
focal) is untouched, so the parsed `_Declaration` from the scaffold shape is
byte-identical to the bare form. A binding test reads the **live** scaffold
template (`constitution.md.j2`) and asserts the parser accepts its voice line, so
template and parser can never silently diverge again. Waking the validator is
reconciled across the whole fixture suite (only `tiny-historical`'s
`expected-status.md` count shifts). No GOLEM/ontology/graph change (Principle X).
DEBT-004 is deleted from `DEBT.md`.

## Technical Context

**Language/Version**: Python 3.11+ (locked by Constitution II)

**Primary Dependencies**: stdlib `re` only — no new dependency. The validator
already depends on `bookwright.indexers.Indexer` and
`bookwright.validation.base` (`Severity`, `ValidationContext`, `Violation`); the
binding test reads the packaged template via `importlib.resources`.

**Storage**: N/A — the validator reads `bible/constitution.md` (plain text) and
manuscript files; it emits no triples and touches no derived graph cache.

**Testing**: `pytest` (the existing `tests/validation/test_focalization.py`
unit suite, extended; the E2E `tests/e2e/test_orchestration_workflow.py` oracle
reconciled). Coverage gate ≥ 80 % (single-sourced in
`[tool.coverage.report]`).

**Target Platform**: CLI / library, OS-independent.

**Project Type**: Single project (src-layout `src/bookwright/`, `tests/` at
root) — Constitution II.

**Performance Goals**: N/A — line-level regex over a single constitution file and
the manuscript; the normalization adds one `str.strip`-class pass per candidate
line, negligible.

**Constraints**: No new GOLEM concept/class, no ontology edit, no graph triples
(Principle X / Constitution X). The change is confined to prose-level validation
logic + test/fixture/debt artifacts. Every source file ≤ 500 lines
(`focalization.py` is 153 lines; the delta is small). Spanish typography in the
existing lexicons is preserved verbatim.

**Scale/Scope**: One regex/normalization change in one validator module; one new
binding test + marker-by-marker unit coverage; one fixture oracle count update;
one DEBT entry removal.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution `v1.5.0`. Relevant principles:

- **I — Plain-text source of truth**: PASS. The validator continues to read
  plain-text `bible/constitution.md`; no derived artifact becomes a source of
  truth. The binding test reads the plain-text `.j2` template.
- **II — Locked stack**: PASS. No new dependency; stdlib `re` only.
- **IV — ≤ 500 lines / one subcommand per module**: PASS. `focalization.py`
  stays well under 500 lines; no new CLI verb.
- **V/VI — plugin integrations / Agent Skills only**: PASS. No integration,
  skill, or command surface touched.
- **VIII — test discipline ≥ 80 %**: PASS. New behavior is covered by new unit
  tests (marker-by-marker FR-001/FR-002, scaffold-shape FR-003/FR-004, edge
  cases FR-005) plus the binding test (FR-007); the no-declaration path stays
  covered.
- **IX — layering / `errors.py` below all layers**: PASS. No new error type, no
  import-cycle surface touched.
- **X — frozen ontology (17-class closure, `golem.ttl`, `CLASS_IRI`)**: PASS.
  This is a prose validator; it emits `Violation`s with empty `triples=()`.
  No class, no IRI, no `.ttl` change. FR-010 makes this explicit.

**Scope discipline**: PASS. The change cancels exactly DEBT-004 and adds no
plumbing for future work. DEBT-005/DEBT-006 are explicitly out of scope (their
own iterations 035/036). No "future X" justification appears anywhere.

No violations → **Complexity Tracking left empty**.

## Project Structure

### Documentation (this feature)

```text
specs/034-focalization-markdown-voice/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── declaration-recognition.md   # the parser-recognition contract
├── spec.md              # already present
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── validation/
│   └── validators/
│       └── focalization.py          # CHANGE: line-normalization before _DECLARATION
└── resources/
    └── project/
        └── bible/
            └── constitution.md.j2   # READ-ONLY (binding-test fixture of truth)

tests/
├── validation/
│   └── test_focalization.py         # EXTEND: marker-by-marker + scaffold-shape + binding test
├── e2e/
│   └── test_orchestration_workflow.py   # asserts tiny-historical counts (oracle reconciled)
└── fixtures/
    ├── tiny-historical/
    │   └── expected-status.md       # CHANGE: validation.counts → awake total
    ├── tiny-novel/                  # verify validate still exits 0 (no oracle)
    ├── tiny-quest/                  # narrative_structure-scoped oracle (unaffected)
    ├── tiny-essay/                  # first person → no focalization rule fires
    └── tiny-memoir/                 # first person → no focalization rule fires

DEBT.md                              # CHANGE: remove the DEBT-004 entry
```

**Structure Decision**: Single project, no new module. The whole behavioral
change lives in `focalization.py`'s recognition step; everything else is
test/fixture/debt reconciliation. The scaffold template is the binding test's
fixture of truth and is **read, not edited** — the template already emits the
shape we are teaching the parser to accept.

## Complexity Tracking

> No Constitution violations — table intentionally empty.
