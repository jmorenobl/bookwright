# Implementation Plan: Manifest Model

**Branch**: `002-manifest-model` | **Date**: 2026-05-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-manifest-model/spec.md`

## Summary

Deliver the typed in-memory representation of a Bookwright project's
`manifest.toml`: a Pydantic v2 model that parses, validates, builds, and writes
back the manifest with zero information loss (FR-001 → FR-024). Every other
v0 command — `init`, `graph`, `validate`, the skills layer — sits on top of
this model.

Technical approach (grounded in `bookwright-design.md` § 8 for the contract
and `bookwright-implementation-plan.md` iteration 2 for the module layout
hint, since `bookwright-design.md` § 14.5 does **not** exist — the design
doc stops at § 14.4):

- One core module — `src/bookwright/core/manifest.py` — exposing
  `Manifest` (Pydantic v2 `BaseModel`) plus `Manifest.load(path)`,
  `Manifest.dump(path, *, overwrite=False)`, and `Manifest.build(...)`.
- `tomlkit` for both read and write so comments, blank lines, and key order
  round-trip byte-for-byte (FR-018, FR-020). **No `tomli` / `tomli_w`** per
  the iteration 2 hint.
- Pydantic v2 model validators collect every offence in one pass via
  `ValidationError` and are mapped to the iteration's `ManifestValidationError`
  shape so the CLI/JSON layer (FR-024) can serialise field paths, rejected
  values, and rule ids.
- Two small support modules: `core/iso639_1.py` (frozenset of the ~184
  ISO 639-1 codes, bundled in-package, no network) and `core/errors.py`
  (the public `ManifestError` / `ManifestValidationError` / `ManifestWarning`
  hierarchy plus a JSON-encodable representation).
- A template file `src/bookwright/resources/templates/manifest.template.toml`
  loaded via `importlib.resources` is the source of truth for the
  human-readable, comment-preserving form emitted by `Manifest.build(...)`
  + `dump(...)`. This makes deterministic writes a property of the template
  rather than of an ad-hoc serialiser.
- PEP 440 version comparison (`cli_version_min` vs the installed CLI) uses
  `packaging.version.Version`. **This adds `packaging` to the runtime
  dependency list**, which is a constitutional Technical Constraints
  change requiring a MINOR amendment (see Complexity Tracking).

## Technical Context

**Language/Version**: Python 3.11+ (Constitution Principle II, Technical
Constraints).

**Primary Dependencies**:
- Runtime (already pinned in `pyproject.toml` from iteration 1):
  `pydantic>=2.5`, `tomlkit>=0.12`, plus stdlib `urllib.parse` for the
  `uri_base` rule and `importlib.resources` for the template.
- Runtime (added by this iteration, pending amendment):
  `packaging>=23.0` for PEP 440 parsing and ordering. See Complexity
  Tracking.

**Storage**: Plain-text TOML files on disk. No database, no cache. Round-trip
guarantee is provided by `tomlkit`.

**Testing**: `pytest` (with `pytest-cov`), already in the dev-deps group
from iteration 1. Fixtures: hand-crafted TOML files under
`tests/core/fixtures/`.

**Target Platform**: macOS + Linux developer CLIs (any platform Python 3.11
supports). No GUI.

**Project Type**: CLI / library (single project, `src/` layout, per
Constitution Principle III).

**Performance Goals**: Loading and validating a manifest MUST NOT touch the
network and MUST NOT touch any filesystem path other than the manifest
itself. No throughput target; correctness over speed.

**Constraints**:
- Atomic writes (FR-021): write to a sibling temp file in the destination
  directory, `fsync`, then `os.replace` for an atomic rename. Never leave
  a half-written manifest on disk.
- All validation errors for a single manifest surface together (FR-011);
  Pydantic v2's accumulating `ValidationError` is the mechanism.
- No filesystem checks against `.bookwright/vocabularies/` in this
  iteration (FR-023, explicit out-of-scope). Vocabulary existence is the
  downstream indexer's responsibility.
- No CLI subcommand wiring in this iteration. The spec's FR-024 is a
  *design constraint on error shapes* so that the iteration-4 `init`
  command and any later `--json` consumer can serialise validation errors
  and warnings without rework.

**Scale/Scope**: One manifest per project. No batch loading, no large-file
considerations. The 184-element ISO 639-1 frozenset is the largest in-memory
constant. The module budget is one Pydantic model and three helper modules,
each well under the 500-line ceiling (Principle IV).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain Text as Source of Truth (NON-NEGOTIABLE) | ✅ | Manifest is TOML, validation errors and warnings are structured data, no binary stores. |
| II. Modern Python Stack | ⚠️ | Adds `packaging>=23.0` for PEP 440. Per Technical Constraints, this is a MINOR amendment. See Complexity Tracking row 1. |
| III. src-layout | ✅ | New code lives under `src/bookwright/core/`; tests under `tests/core/`. |
| IV. Modular Command Surface | ✅ | No CLI command added in this iteration. The 500-line cap is comfortably respected — `manifest.py` is one model + load/dump/build; helpers split out. |
| V. Plugin-Based Integrations | ✅ | The `[integration]` block is read/written as opaque data only (FR-022). No dispatcher, no monolithic `AGENT_CONFIG`. |
| VI. Agent Skills Only — No Legacy Commands (NON-NEGOTIABLE) | ✅ | N/A — this iteration produces no skills and writes nothing to `.claude/commands/` or analogous directories. |
| VII. agentskills.io Standard Compliance | ✅ | N/A — no skills emitted. |
| VIII. Test Discipline (NON-NEGOTIABLE) | ✅ | Spec acceptance criterion is ≥ 90 % module coverage; CI gate is the existing 80 % global. Each FR maps to at least one test in Phase 1. |
| IX. JSON-over-stdout CLI Contract | ✅ | `ManifestValidationError` and `ManifestWarning` both expose a JSON form (FR-024); model layer never writes to stdout/stderr (SC-006). |
| X. Design Document Axioms | ✅ | Pydantic v2 + rdflib + plain text + Spec Kit usage are all honoured. No reopening of axioms. |

**Out-of-scope confirmations**:
- No preset system, no `GrafeoIndexer`, no integrations beyond `claude` /
  `generic` (the `[integration]` block stores the *recorded* key without
  validating it against a registry; that registry is iteration 3's job).
- No EPUB/PDF export plumbing.

**Gate decision**: PASS subject to the constitutional MINOR amendment
captured in Complexity Tracking. The amendment is small (one line under
Technical Constraints), motivated, and follows the procedure in the
Governance section. The implementation iteration MUST NOT begin until the
amendment lands (or until the team agrees on the hand-rolled alternative
in research.md).

**Post-design re-check (after Phase 1 artifacts)**:

| Principle | Re-check | Notes |
|---|---|---|
| All | ✅ | Phase 1 artifacts (`research.md`, `data-model.md`, `contracts/manifest_api.md`, `quickstart.md`) introduce no new dependencies or behaviours beyond what is listed above. Module count, test layout, JSON shapes, and atomic-write strategy are all consistent with the pre-design table. |

## Project Structure

### Documentation (this feature)

```text
specs/002-manifest-model/
├── plan.md                  # This file (/speckit-plan command output)
├── research.md              # Phase 0 output (/speckit-plan command)
├── data-model.md            # Phase 1 output (/speckit-plan command)
├── quickstart.md            # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── manifest_api.md      # Phase 1 output (/speckit-plan command)
├── checklists/              # existing (from /speckit-clarify session)
└── tasks.md                 # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── __init__.py                  # (iteration 1) — owns __version__
├── __main__.py                  # (iteration 1)
├── cli.py                       # (iteration 1) — untouched in this iteration
├── commands/                    # (iteration 1) — untouched in this iteration
│   ├── __init__.py
│   ├── check.py
│   └── version.py
├── core/                        # NEW in iteration 2
│   ├── __init__.py              # re-exports Manifest, errors, warnings
│   ├── manifest.py              # Pydantic v2 model + load/dump/build (≤500 LoC)
│   ├── errors.py                # ManifestError / ManifestValidationError / ManifestWarning + .to_json()
│   └── iso639_1.py              # frozenset[str] of the 184 ISO 639-1 codes
└── resources/                   # NEW in iteration 2 (declared package data)
    └── templates/
        └── manifest.template.toml

tests/
├── conftest.py                  # (iteration 1)
├── test_cli_*.py                # (iteration 1) — untouched
├── test_smoke_import.py         # (iteration 1)
└── core/                        # NEW in iteration 2
    ├── __init__.py
    ├── conftest.py              # shared fixtures + tmp_manifest helper
    ├── test_load_valid.py       # US1, FR-001–FR-003
    ├── test_load_invalid.py     # US2, FR-004–FR-011
    ├── test_version_gate.py     # US3, FR-012
    ├── test_build.py            # US4, FR-015–FR-017
    ├── test_write.py            # US4, FR-018–FR-021
    ├── test_future_version.py   # US5, FR-013–FR-014
    ├── test_json_shapes.py      # FR-024, SC-006
    └── fixtures/
        ├── valid_full.toml
        ├── valid_minimal.toml
        ├── invalid_*.toml       # one per FR-004…FR-010 rule
        └── future_version.toml
```

**Structure Decision**:

- **Library layer, not CLI layer.** This iteration adds `src/bookwright/core/`
  only. The 500-line ceiling (Principle IV) is respected by splitting the
  Pydantic model (`manifest.py`), the error types (`errors.py`), and the
  ISO 639-1 constant (`iso639_1.py`).
- **No new CLI subcommands.** Iteration 4 (`bookwright init`) is the first
  consumer; FR-024 only requires that the error/warning shapes are *ready*
  for `--json` consumption, not that a `--json` flag exists yet.
- **Resources are package data.** `pyproject.toml` `[tool.hatch.build]`
  already includes `src/bookwright`; the new `src/bookwright/resources/`
  subtree is captured by that include. The wheel-targets stanza
  (`packages = ["src/bookwright"]`) needs no change, but the template
  must be a regular file (not skipped by `.gitignore`) and accessed via
  `importlib.resources.files("bookwright.resources.templates")`.
- **Tests mirror sources.** `tests/core/` mirrors `src/bookwright/core/`,
  with one test file per User Story or rule cluster. Fixtures are small,
  hand-crafted TOML files so that the failing-rule under test is obvious
  from the file name.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Add `packaging>=23.0` to the runtime dependency list (constitutional Technical Constraints change → MINOR amendment to `.specify/memory/constitution.md`). | FR-012 mandates PEP 440 parsing and ordering for `cli_version_min`. The `packaging` library is the canonical PEP 440 implementation, ships with `pip`, and is universally trusted. The CLI's own `__version__` (`0.0.1` today) is also a valid PEP 440 string, so the comparison stays in one library. | A hand-rolled PEP 440 subset parser was considered (regex for `X.Y.Z[(a\|b\|rc)N]` plus tuple comparison with pre-release demotion). It is feasible but brittle: pre-release ordering (`1.0.0rc1 < 1.0.0`) is famously easy to get wrong, and a future bug there could silently let an underpowered CLI open a future-version manifest. The library cost — one well-maintained, transitive-of-`pip` dependency — is much cheaper than the maintenance cost of getting PEP 440 ordering right by hand. The amendment is mechanical (one line under Technical Constraints) and the right time to make it is *with* the iteration that first needs it. |
