# Implementation Plan: Integration Architecture

**Branch**: `003-integration-architecture` | **Date**: 2026-05-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-integration-architecture/spec.md`

## Summary

Deliver the plugin-based integration layer that materializes Agent Skills
artifacts into a Bookwright project for a chosen agent. The iteration ships
the contract end-to-end:

- A single in-process `INTEGRATION_REGISTRY` populated at import time by
  `_register_builtins()` with exactly two entries: `claude` and `generic`.
- A `SkillsIntegration` base class that owns the only `setup()` body in
  v0 (idempotent directory creation + placeholder marker), declares the
  three capability flags defaulting to `False`, exposes a default
  `options()` empty list, a default `resolve_skills_dir(...)` that returns
  `Path(default_skills_dir)`, and is the only class that subclasses
  inherit from.
- Two concrete subclasses, `ClaudeIntegration` and `GenericIntegration`,
  each in its own subpackage under `src/bookwright/integrations/<key>/`,
  declaring the locked metadata of FR-007/FR-008 and the capability
  matrix of FR-010.
- An `IntegrationOption` declarative descriptor plus a `parse_options(...)`
  function that turns the raw `--integration-options` string into a typed
  dict against the chosen integration's `options()`, raising structured
  `UnknownOptionError`, `MalformedOptionError`, or
  `InvalidOptionDeclarationError` (the last one on first-introspection
  detection of a malformed descriptor — FR-015).
- A structured exception family (`UnknownIntegrationError`,
  `UnknownOptionError`, `MalformedOptionError`, `DuplicateRegistrationError`,
  `InvalidOptionDeclarationError`) each carrying a stable `code` and a
  `to_dict()` JSON-safe serialization for the iteration-4 `--json`
  consumer (Principle IX).
- Two agentskills.io constants (`SKILL_NAME_MAX_LENGTH = 64`,
  `SKILL_DESCRIPTION_MAX_LENGTH = 1024`) exposed at an importable module
  location for iteration 9 to pin against.

Technical approach (grounded in `bookwright-design.md` § 11 for the class
shape, the iteration-3 prompt in `bookwright-implementation-plan.md` for
the stub-setup scope, and the iteration-2 module conventions for layout):

- One subpackage per integration: `src/bookwright/integrations/<key>/`,
  each `__init__.py` exporting exactly the integration class. The base
  class and the registry live one level up (`integrations/base.py`,
  `integrations/__init__.py`, `integrations/options.py`,
  `integrations/errors.py`, `integrations/constants.py`).
- `setup()` is implemented once on `SkillsIntegration`. No subclass needs
  to override it in v0 (FR-026 → FR-030, US5 contract). The marker file
  is `.bookwright-skills-placeholder` (FR-027), single line, idempotent
  via "write only if missing".
- Option parsing uses `shlex.split(raw, posix=True)` for tokenization
  (FR-017) and a small hand-rolled state machine that consults the
  integration's `options()` descriptors to validate flags, types,
  duplicates, and missing values. No `argparse` (it would print to
  stderr on error, violating FR-037, and its error surface is not
  structured enough for `to_dict()`).
- `default_skills_dir` becomes the single source of truth for per-key
  defaults across the codebase. The temporary `DEFAULT_SKILLS_DIR` dict
  living in `core/manifest.py` (placed there in iteration 2 as a shim
  because iteration 3's registry didn't exist yet) is re-rooted to
  derive from the registry via a late import inside `_build_manifest`,
  preserving the iteration-2 manifest contract while honouring the
  single-source-of-truth rule the user recently locked across enums
  (commit `9753ebf`, R1/R2/R4 closure).
- Tests live under `tests/integrations/`, one file per concern: registry
  lookup + listing, base-class `setup()` idempotency, each integration's
  metadata + `resolve_skills_dir` parametrized over `parsed_options`
  shapes, the option parser, the structured-error serialization, the
  Agent Skills constants, and a `FakeIntegration` plugin-extensibility
  smoke test that proves zero edits to `claude/`, `generic/`, or the
  base class are required (US5).

## Technical Context

**Language/Version**: Python 3.11+ (Constitution Principle II, Technical
Constraints).

**Primary Dependencies**:
- Runtime: stdlib only for this iteration's new code (`pathlib`, `shlex`,
  `dataclasses`, `typing`). The manifest model the layer accepts in
  `setup(..., manifest, ...)` is the iteration-2 Pydantic v2 model;
  importing it for type-checking is a normal cross-module dependency,
  not a new third-party requirement.
- Dev / test: `pytest` and `pytest-cov` already in the dev-deps group from
  iteration 1; no new dev dependency.

**Storage**: Plain-text only. The iteration writes a single one-line
marker file (`.bookwright-skills-placeholder`) under the resolved skills
directory. No database, no cache.

**Testing**: `pytest`. Fixtures: `tmp_path` for `setup()` integration-style
tests; parametrized inputs for option-parser tests; a stub
`FakeIntegration` declared inline in `tests/integrations/test_plugin_contract.py`
for the US5 contract.

**Target Platform**: macOS + Linux developer CLIs (any platform Python 3.11
supports). No GUI.

**Project Type**: CLI / library (single project, `src/` layout, per
Constitution Principle III).

**Performance Goals**: No throughput target. `setup()` MUST NOT touch the
network and MUST NOT touch any filesystem path outside the resolved
skills directory (FR-029). Registry lookup and option parsing are
O(number-of-options) on the integration's declared options — at most
one option in v0.

**Constraints**:
- No writes to `sys.stdout` or `sys.stderr` from any function in this
  layer (FR-037, SC-009). Errors are raised, never printed.
- `setup()` is idempotent (FR-028, SC-006). The marker is written only
  when missing; the directory uses `mkdir(parents=True, exist_ok=True)`.
- The structured-error `to_dict()` output MUST be `json.dumps`-able
  without a custom encoder (FR-036, SC-008).
- `_register_builtins()` runs at module-import time and MUST be safe to
  re-enter (FR-002). Duplicate-key registration MUST raise
  `DuplicateRegistrationError` (FR-005).
- The two agentskills.io constants MUST live in exactly one importable
  location (`integrations/constants.py`); every consumer (iteration 9
  and its tests) imports from there (FR-033, SC-010).
- No CLI subcommand wiring in this iteration. The integration layer is
  the dependency that iteration 4's `bookwright init` consumes.

**Scale/Scope**: Two integrations in the registry, one option total
across the two, one marker file written per `setup()` call. The
integration layer's total module budget is well under the Principle IV
500-line ceiling — each file is small and single-purpose.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain Text as Source of Truth (NON-NEGOTIABLE) | ✅ | The one file `setup()` writes is a single-line UTF-8 marker. No binary stores; no embedded database. |
| II. Modern Python Stack | ✅ | No new runtime dependency. Stdlib `shlex`, `pathlib`, `dataclasses`, `typing` only. |
| III. src-layout | ✅ | New code lives under `src/bookwright/integrations/`; tests under `tests/integrations/`. |
| IV. Modular Command Surface | ✅ | No CLI subcommand added in this iteration. Each integration is a subpackage (`integrations/<key>/`), each file ≤ 500 lines. |
| V. Plugin-Based Integrations | ✅ | This iteration **is** the plugin layer. `SkillsIntegration` + `INTEGRATION_REGISTRY` are exactly the shape the principle mandates; no `AGENT_CONFIG` dispatcher exists or is introduced. |
| VI. Agent Skills Only — No Legacy Commands (NON-NEGOTIABLE) | ✅ | `setup()` writes only `<skills_dir>/.bookwright-skills-placeholder`. No code path in this iteration writes to `.claude/commands/`, `.agents/commands/`, or any analogous legacy directory. `MarkdownIntegration` is not introduced (FR-032, design § 16.7). |
| VII. agentskills.io Standard Compliance | ✅ | No `SKILL.md` is generated in this iteration. The two structural constants (`SKILL_NAME_MAX_LENGTH = 64`, `SKILL_DESCRIPTION_MAX_LENGTH = 1024`) are exposed for iteration 9 (FR-033, FR-034, SC-010). |
| VIII. Test Discipline (NON-NEGOTIABLE) | ✅ | Every FR maps to at least one test in `tests/integrations/`. The CI gate (80 % global, ratcheting upward) and the spec's per-iteration target of ≥ 95 % slice coverage on `bookwright.integrations` are both honoured by the test plan in Project Structure below. |
| IX. JSON-over-stdout CLI Contract | ✅ | All structured errors expose a `to_dict()` JSON-safe payload (FR-035, FR-036). The layer itself never writes to stdout/stderr (FR-037, SC-009). The iteration-4 `init --json` consumer is the first caller; that wiring is iteration 4's job, not this iteration's. |
| X. Design Document Axioms | ✅ | The design § 11 class shape is followed exactly. No relitigation: `SkillsIntegration` is the only operative base class (axiom 7); `.agents/skills/` is the generic default (axiom 8); plugin-based integrations from day one (axiom 10). |

**Out-of-scope confirmations (Scope & Release Discipline)**:
- No preset system, no `GrafeoIndexer`, no third integration beyond
  `claude` / `generic` (Copilot / Cursor-specific / Codex-specific are
  v0.4; FR-031 ensures they land without modifying this iteration).
- No CLI subcommand. Iteration 4 (`bookwright init`) is the first
  consumer of this layer.
- No real `SKILL.md` rendering. That is iteration 9's body of work; the
  marker file is the stub that proves the contract.

**Gate decision**: PASS, no Complexity Tracking entries required. The
iteration adds no new runtime dependency and introduces no architectural
exception.

**Post-design re-check (after Phase 1 artifacts)**:

| Principle | Re-check | Notes |
|---|---|---|
| All | ✅ | Phase 1 artifacts (`research.md`, `data-model.md`, `contracts/integrations_api.md`, `quickstart.md`) introduce no new dependencies, no new modules, and no behaviours beyond what Phase 0 listed. Module count, test layout, JSON shapes, and the single-source-of-truth re-rooting of `DEFAULT_SKILLS_DIR` are all consistent with the pre-design table. |

## Project Structure

### Documentation (this feature)

```text
specs/003-integration-architecture/
├── plan.md                   # This file (/speckit-plan command output)
├── research.md               # Phase 0 output (/speckit-plan command)
├── data-model.md             # Phase 1 output (/speckit-plan command)
├── quickstart.md             # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── integrations_api.md   # Phase 1 output (/speckit-plan command)
├── checklists/               # existing (from /speckit-specify)
└── tasks.md                  # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── __init__.py                       # (iteration 1) — owns __version__
├── __main__.py                       # (iteration 1)
├── cli.py                            # (iteration 1) — untouched in this iteration
├── commands/                         # (iteration 1) — untouched in this iteration
│   ├── __init__.py
│   ├── check.py
│   └── version.py
├── core/                             # (iteration 2) — surgical edit: re-root DEFAULT_SKILLS_DIR
│   ├── __init__.py                   # untouched
│   ├── manifest.py                   # edit: derive DEFAULT_SKILLS_DIR from integrations registry
│   ├── errors.py                     # untouched
│   ├── iso639_1.py                   # untouched
│   ├── _build.py                     # may consume the re-rooted DEFAULT_SKILLS_DIR
│   └── _translate.py                 # untouched
├── integrations/                     # NEW in iteration 3
│   ├── __init__.py                   # INTEGRATION_REGISTRY, _register_builtins(), get(), list_keys()
│   ├── base.py                       # SkillsIntegration (single operative base, owns setup() body)
│   ├── constants.py                  # SKILL_NAME_MAX_LENGTH = 64, SKILL_DESCRIPTION_MAX_LENGTH = 1024, marker file name
│   ├── errors.py                     # UnknownIntegrationError, UnknownOptionError, MalformedOptionError,
│   │                                 #   DuplicateRegistrationError, InvalidOptionDeclarationError (+ to_dict())
│   ├── options.py                    # IntegrationOption dataclass + parse_options(raw, integration_cls)
│   ├── claude/
│   │   └── __init__.py               # ClaudeIntegration(SkillsIntegration)
│   └── generic/
│       └── __init__.py               # GenericIntegration(SkillsIntegration)
└── resources/                        # (iteration 2) — untouched in this iteration
    ├── __init__.py
    └── templates/
        └── manifest.template.toml

tests/
├── conftest.py                       # (iteration 1)
├── test_cli_*.py                     # (iteration 1) — untouched
├── test_smoke_import.py              # (iteration 1)
├── core/                             # (iteration 2) — untouched except possibly one assertion
│   └── ...                           #   confirming DEFAULT_SKILLS_DIR re-rooting did not regress FR-022
└── integrations/                     # NEW in iteration 3
    ├── __init__.py
    ├── conftest.py                   # tmp_project fixture, minimal-manifest factory
    ├── test_registry.py              # US1, FR-001–FR-005
    ├── test_setup_stub.py            # US2, FR-026–FR-030, SC-006
    ├── test_option_parser.py         # US3, FR-016–FR-021, SC-005
    ├── test_metadata.py              # US4, FR-006–FR-011
    ├── test_resolve_skills_dir.py    # FR-022–FR-025, SC-003, SC-004 (parametrized per integration)
    ├── test_errors_json.py           # FR-035, FR-036, SC-008
    ├── test_no_stdio.py              # FR-037, SC-009 (grep-style guard over the integrations package)
    ├── test_constants.py             # FR-033, FR-034, SC-010
    └── test_plugin_contract.py       # US5, FR-031, SC-007 (FakeIntegration smoke test)
```

**Structure Decision**:

- **Subpackage per integration.** Each concrete integration lives under
  `src/bookwright/integrations/<key>/` exactly as design § 11.1 prescribes.
  In v0 each subpackage is a single `__init__.py` exporting the
  integration class; future integrations may add `references/`,
  `templates/`, etc., without changing any sibling subpackage.
- **The base, the registry, the parser, the errors, and the constants
  live one level up** (`integrations/base.py`, `integrations/__init__.py`,
  `integrations/options.py`, `integrations/errors.py`,
  `integrations/constants.py`). They are the shared contract; each
  integration depends on the contract, never on a sibling.
- **`integrations/__init__.py` imports both built-ins eagerly**, registers
  them via `_register_builtins()`, and exposes `INTEGRATION_REGISTRY`,
  `get(key)`, and `list_keys()`. Importing the package is therefore the
  act of populating the registry (FR-002), so consumers (iteration 4,
  iteration 9) only need `from bookwright.integrations import get, ...`.
- **`DEFAULT_SKILLS_DIR` is re-rooted.** The constant dict added to
  `core/manifest.py` in iteration 2 was a shim because iteration 3 did
  not exist yet. This iteration replaces the literal dict with a
  derivation from the integrations registry, done via a late import
  inside `_build_manifest` to avoid load-order surprises. The manifest
  module continues to honour its FR-022 promise of treating the
  `[integration]` block as opaque data — the consultation is only for
  filling the per-key default when *building* a fresh manifest.
- **Tests mirror sources.** `tests/integrations/` mirrors
  `src/bookwright/integrations/`. One file per concern keeps any
  failing assertion immediately attributable to a single FR cluster.
  The `test_no_stdio.py` guard is a static check (AST or source-grep
  over the integrations package looking for `print(`, `sys.stdout`,
  `sys.stderr`) and is the mechanical enforcement of FR-037.
- **Plugin extensibility is exercised, not just claimed.**
  `test_plugin_contract.py` declares a `FakeIntegration(SkillsIntegration)`
  inline, inserts it into `INTEGRATION_REGISTRY`, runs lookup, listing,
  `resolve_skills_dir`, option parsing, and `setup()` against it, and
  asserts on git/file-state grounds that no source file under
  `integrations/claude/`, `integrations/generic/`, or `integrations/base.py`
  was modified. This locks FR-031 mechanically.

## Complexity Tracking

> No Constitution Check violations. This iteration introduces no
> architectural exception, no new runtime dependency, and no constitutional
> amendment. The table is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| _none_    | _n/a_      | _n/a_                                |
