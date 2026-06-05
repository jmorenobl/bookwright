# Implementation Plan: Unified Error Envelope (shared `BookwrightError` base)

**Branch**: `018-unified-error-envelope` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/018-unified-error-envelope/spec.md`

## Summary

Bookwright hand-rolls the JSON-over-stdout error envelope (Principle IX) in six
independent exception hierarchies (`core`, `golem`, `io`, `indexers`,
`validation`, and a local `_UsageError` in `commands/validate.py`), each with its
own `to_json()`. Any change to the contract must be replicated N times (review
finding R3). This iteration introduces one shared base — `BookwrightError` — in a
new **root module** `src/bookwright/errors.py` that defines the canonical
envelope (`{"status":"error","code","message"[,"details"]}`) and its **single**
`to_json()`. Every serializable error inherits it and deletes its own `to_json()`.

The four already-canonical hierarchies (`io`, `indexers`, `validation`,
`_UsageError`) migrate **byte-identically**. The two legacy flat-shape
hierarchies (`core/errors.py`, `golem/errors.py`) are **normalized** onto the one
envelope (the former `"error"` value becomes `code`; remaining flat fields move
under `details`; codes/messages/exit codes preserved), per the 2026-06-05
clarifications. The four per-package roots (`ManifestError`, `IOError_`,
`IndexerError`, `GolemError`) stay as abstract intermediate classes that now
inherit `BookwrightError`, so every `except <PackageError>` catch site is
untouched.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: stdlib only for the base (`json`, `typing`); no new
runtime dependency. `pydantic` v2 unaffected (the touched errors are plain
`Exception` subclasses, not models).

**Storage**: N/A (no persistence; this is the error-serialization seam).

**Testing**: `pytest` with ≥ 80 % coverage gate; existing error-shape tests are
the safety net (`tests/core/test_json_shapes.py`, `tests/golem/test_slug.py`,
`tests/indexers/test_query_errors.py`, `tests/validation/test_base.py`,
`tests/validation/test_command.py`, plus `tests/io/test_*`).

**Target Platform**: CLI (cross-platform), agent `--json` consumers.

**Project Type**: Single project, src-layout (`src/bookwright/`).

**Performance Goals**: N/A (serialization of a single error object).

**Constraints**: No new import cycle (FR-010); the base module imports **nothing**
from `core/golem/io/indexers/validation/commands`. Codes, messages, and exit
codes frozen (FR-007/008/009). All four CI gates green (SC-007).

**Scale/Scope**: 1 new module (~30 lines), 6 files refactored, ~14 concrete error
classes migrated, 2 test files + 2 contract docs updated for the normalized
flat shapes. No behavior change for the four canonical hierarchies.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain text as source of truth | ✅ N/A | No storage change; errors are in-memory. |
| II. Modern Python stack | ✅ Pass | No new dependency; stdlib `typing`/`json` only. |
| III. src-layout | ✅ Pass | New module lives at `src/bookwright/errors.py`; tests stay under `tests/`. |
| IV. Modular command surface / ≤ 500 lines | ✅ Pass | New module ~30 lines; every touched file shrinks (deletes duplicated `to_json`). No `cli.py` change. |
| V. Plugin integrations | ✅ N/A | Integration registry untouched. |
| VI. Agent Skills only | ✅ N/A | No skill emission touched. |
| VII. agentskills.io compliance | ✅ N/A | No `SKILL.md` touched. |
| VIII. Test discipline (≥ 80 %) | ✅ Pass | Net code shrinks; existing tests are the net. New base is exercised by every migrated error's existing test; only the flat-shape assertions (core/golem) are updated. Coverage cannot drop. |
| IX. JSON-over-stdout contract | ✅ Pass — strengthened | The contract becomes single-sourced. The only observable change is the two legacy flat bodies → canonical envelope (intended, FR-005/006). |
| X. Design axioms | ✅ Pass | No § 16 axiom reopened. |

**Scope & Release Discipline**: This is a pure debt-paydown refactor of an
existing seam (R3) — no deferred-capability plumbing. ✅

**Gate result**: PASS. No violations; Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/018-unified-error-envelope/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (module location, code attr, normalization map)
├── data-model.md        # Phase 1 — BookwrightError + hierarchy + per-error code/details table
├── quickstart.md        # Phase 1 — how to add an error / how migration is verified
├── contracts/
│   └── error-envelope.md  # Phase 1 — canonical envelope schema + full code/details registry
├── spec.md              # Already present
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── errors.py            # NEW — BookwrightError base + canonical to_json() (the single source of truth)
├── core/
│   └── errors.py        # ManifestError(BookwrightError) abstract root; 4 concretes normalized, to_json() deleted
├── golem/
│   └── errors.py        # GolemError(BookwrightError) abstract root; EmptySlugError normalized, to_json() deleted
├── io/
│   └── errors.py        # IOError_(BookwrightError) abstract root; 5 concretes migrated byte-identical, to_json() deleted
├── indexers/
│   └── errors.py        # IndexerError(BookwrightError) abstract root; 4 concretes migrated byte-identical, to_json() deleted
├── validation/
│   └── base.py          # UnknownValidatorError(BookwrightError); to_json() deleted (Violation/ValidatorError untouched)
└── commands/
    └── validate.py      # _UsageError(BookwrightError), per-instance self.code; to_json() deleted

tests/
├── core/test_json_shapes.py   # UPDATED — flat→canonical assertions for the 4 manifest errors
└── golem/test_slug.py         # UPDATED — flat→canonical assertion for EmptySlugError
# All other error-shape tests pass UNCHANGED (byte-identical canonical output).
```

**Structure Decision**: Single project, src-layout. The base goes in a **root
module** `src/bookwright/errors.py` (not under any subpackage) — the lowest layer,
imported by every other layer with no back-import, so no cycle is possible
(FR-010). Each package keeps its own `errors.py`/`base.py`; only the base class
and the removal of duplicated `to_json()` are new.

## Complexity Tracking

> No Constitution Check violations. Section intentionally empty.
