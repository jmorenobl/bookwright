# Implementation Plan: Actionable research-source error messages

**Branch**: `036-actionable-source-errors` | **Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/036-actionable-source-errors/spec.md`

## Summary

Close DEBT-006: two research-source load errors blind the author. **(F1)** an
out-of-vocabulary `type`/`reliability` names the bad value but not the accepted
set — fix by enumerating the closed vocabulary (`one of: v1, v2, …`, in the
vocabulary's own declaration order) in `_reject_unknown_vocab`. **(F2)** a
per-source validation failure (e.g. a quoted `access_date`) does not say *which*
source failed — fix by wrapping the per-source loop body in `_map_sources` with a
**single** locator point that prefixes every `ResearchError` raised while
processing one source with `source <id>: …`, where `<id>` is the `name`
single-quoted when usable else `#<n>` (1-based). The two existing inline
self-locators (translation-rule, duplicate-name) are reconciled so a source is
named **once** as a locator (FR-011). The SPARQL empty-result footgun is
**documented** (command help + docs page), not fixed. The `{status, code,
message[, details]}` envelope is byte-unchanged — only `message` text improves
(FR-007). All production change is in `src/bookwright/io/research.py` plus the
`graph query` help string and `docs/commands/graph-query.md`; DEBT-006 is deleted.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: `pydantic` v2 (the `Source` model + `ValidationError`),
`rdflib` (URIRef vocab maps), `pyyaml` (front-matter), `typer` (the `graph query`
help surface). No new dependency.

**Storage**: plain text — `bible/research/sources.md` front-matter in, GOLEM
entities out; the graph is a derived cache (Constitution I). N/A here (no new I/O).

**Testing**: `pytest` (`tests/io/test_research.py` for the loader messages;
`tests/commands/graph/test_query.py` + a docs check for the SPARQL note).

**Target Platform**: CLI (`bookwright graph build` / `graph query`), cross-platform.

**Project Type**: single project, src-layout (Constitution III).

**Performance Goals**: N/A — string construction on an already-fatal path; no
hot-loop or allocation concern.

**Constraints**: error JSON envelope must stay byte-compatible (same
`status`/`code`/`details` keys, FR-007/SC-005); message content only. No schema,
vocabulary, fault-model, or error-code change. Every source file ≤ 500 lines
(`research.py` is 463 today — the change is net-near-zero, see Structure).

**Scale/Scope**: one production module (`io/research.py`), one help string, one
docs page, one DEBT entry; ~3 new/extended tests. ~6–8 tasks expected.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Plain text as source of truth** — ✅ no storage change; errors are text.
- **II. Modern Python stack** — ✅ no new dependency; pure stdlib string work over
  existing pydantic/rdflib structures.
- **III. src-layout** — ✅ production change under `src/bookwright/io/`, tests under
  `tests/`.
- **IV. Modular command surface / ≤500 lines** — ✅ `research.py` stays one module;
  the F1/F2 edits are roughly size-neutral (enumeration strings replace short
  literals; the loop wrapper adds one small helper). It is at 463/500 — confirm the
  final file is ≤ 500; if a helper would push it over, extract the identifier
  helper to the existing `io/_research_identity.py` companion (already imported).
- **V / VI / VII. Integrations / Agent Skills** — N/A (no integration or skill
  surface touched).
- **VIII. Test discipline (≥80 %)** — ✅ both improved messages get assertions
  (FR-010/SC-003); coverage non-regressing. Four gates green is the exit bar.
- **IX. JSON-over-stdout** — ✅ **central gate.** The envelope contract is
  unchanged; we only enrich the human `message`. No new code/field/type. The
  per-source prefix is built into `message`, not a new `details` key.
- **X. Design axioms** — ✅ none reopened. The closed vocabularies, GOLEM ontology,
  and strict research fault model (D7) are untouched; a bad source still aborts.

**No violations. Complexity Tracking is empty.**

## Project Structure

### Documentation (this feature)

```text
specs/036-actionable-source-errors/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (vocab enumeration, prefix point, FR-011 reconciliation)
├── data-model.md        # Phase 1 — Source-error reporting shape (message grammar; envelope unchanged)
├── quickstart.md        # Phase 1 — runnable validation of F1, F2, and the SPARQL note
├── contracts/
│   └── error-messages.md  # Phase 1 — the exact message-string contracts a test can assert
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── io/
│   ├── research.py            # PRIMARY: F1 (_reject_unknown_vocab enumerates) +
│   │                          #          F2 (_map_sources wraps each source, single prefix point) +
│   │                          #          FR-011 reconcile (translation-rule / duplicate-name inline locators)
│   ├── _research_identity.py  # OPTIONAL home for the name-or-index identifier helper if research.py nears 500 lines
│   └── errors.py              # UNCHANGED — ResearchError keeps code/details; we only pass a richer message
├── golem/
│   └── namespaces.py          # READ-ONLY — SOURCE_TYPE_IRI / RELIABILITY_IRI provide the enumerated keys (declaration order)
└── commands/graph/
    └── query.py               # the `sparql` Argument help string gains the empty-result note (FR-008, English)

docs/commands/
└── graph-query.md             # the Spanish docs page gains the same note (FR-008)

tests/
├── io/test_research.py        # F1 enumeration assertions + F2 per-source prefix assertions (FR-010)
└── commands/graph/test_query.py  # assert the help text carries the note (+ a docs-content check)

DEBT.md                        # remove the DEBT-006 entry (FR-009/SC-006)
```

**Structure Decision**: Single project (Constitution III). The whole behavioural
change is confined to `io/research.py`; everything else is text (help string, docs,
DEBT). No new module is required unless the ≤500-line guard forces extracting the
identifier helper into the existing `io/_research_identity.py`.

## Complexity Tracking

> No Constitution violations — section intentionally empty.
