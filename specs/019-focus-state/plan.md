# Implementation Plan: Authored focus state

**Branch**: `019-focus-state` | **Date**: 2026-06-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/019-focus-state/spec.md`

## Summary

Add an optional `[focus]` block to `manifest.toml` (the authored layer of the
v0.3 context-orchestration milestone, `bookwright-design.md § 21.3`) and a new
`bookwright focus` command group — `show`, `set`, `clear` — to read, write, and
remove it. The block records the author's current working intent (`target`,
`notes`, `updated_at`) in the project's canonical plain-text source of truth so
that later iterations (020 `status`, 021–022 skills) can consume it.

Technical approach: model the block as a `FocusBlock` Pydantic v2 model (mirroring
`ResearchBlock`) but attach it as `focus: FocusBlock | None = None` on `Manifest`
— `None` encodes the entirely-optional block, and `target`/`updated_at` are
required *when the block is present*. Writes go through two new comment-preserving
`Manifest` methods (`set_focus` / `clear_focus`) that mutate **both** the
validated model field and the backing `tomlkit` document, exactly as the existing
`set_integration` precedent does, so all other blocks, comments, and ordering
round-trip byte-for-byte. Each subcommand reuses the project's existing
`--json` success/error envelope (Principle IX). This iteration delivers only the
authored state and its three commands; derived state (`status`), `next_actions`,
and skill consumption are out of scope.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: `typer` (CLI), `pydantic` v2 (block model), `tomlkit`
(comment-preserving round-trip), `rich` (human output). No new runtime
dependency — all already locked (Constitution II).

**Storage**: plain-text `manifest.toml` (TOML); the `[focus]` block is authored
state, never a derived cache (Constitution I).

**Testing**: `pytest` + `pytest-cov`; unit tests for `FocusBlock` and the
`Manifest.set_focus`/`clear_focus` round-trip, integration tests for the three
CLI subcommands (human + `--json`), ≥ 80 % coverage (Constitution VIII).

**Target Platform**: cross-platform CLI (macOS/Linux/Windows), offline.

**Project Type**: single-project CLI (`src/bookwright/`, src-layout).

**Performance Goals**: N/A — interactive single-shot CLI on a small TOML file.

**Constraints**: Principle I (plain-text source of truth, comment-preserving
round-trip), Principle IV (one subcommand per module, ≤ 500 lines/file),
Principle IX (`--json` → exactly one JSON document on stdout, prose to stderr).

**Scale/Scope**: one optional manifest block, three CLI subcommands, one new
core model, one design-doc edit. No graph, no SPARQL, no skills.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain Text as Source of Truth | ✅ PASS | `[focus]` lives in `manifest.toml`; written via the existing comment-preserving `tomlkit` round-trip. No cache, no binary store. |
| II. Modern Python Stack | ✅ PASS | Uses `typer`/`pydantic`/`tomlkit`/`rich`. No new runtime dependency. |
| III. src-layout | ✅ PASS | New code under `src/bookwright/`; tests under `tests/`. |
| IV. Modular Command Surface | ✅ PASS | New `commands/focus/` sub-app with `show.py`/`set.py`/`clear.py` (one subcommand each); `FocusBlock` extracted to `core/_focus_block.py`. Every file stays well under 500 lines. |
| V. Plugin-Based Integrations | ✅ N/A | No integration touched. |
| VI. Agent Skills Only | ✅ N/A | No skills emitted this iteration (consumption deferred to 021–022). |
| VII. agentskills.io Compliance | ✅ N/A | No `SKILL.md` generated. |
| VIII. Test Discipline | ✅ PASS | Unit + integration tests planned; coverage gate unchanged (≥ 80 %). |
| IX. JSON-over-stdout CLI Contract | ✅ PASS | All three subcommands accept `--json`; success uses `{"status":"ok",…}`, failure uses the unified error envelope; prose to stderr. |
| X. Design Document Axioms | ✅ PASS | Implements `§ 21.3`, an *additive* extension that reopens no `§ 16` axiom; the design-doc edit is additive (`§ 8.1`). |

**Result**: no violations. Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/019-focus-state/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli-focus.md     # Phase 1 output — the focus CLI contract
├── spec.md              # /speckit-specify output
└── tasks.md             # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── cli.py                         # + app.add_typer(focus.app, name="focus")
├── core/
│   ├── __init__.py                # + re-export FocusBlock
│   ├── _focus_block.py            # NEW — FocusBlock Pydantic model (mirrors _research_block.py)
│   └── manifest.py                # + focus field, + set_focus()/clear_focus()
└── commands/
    ├── _envelope.py               # EDIT — promote emit_json/emit_error here (single-sourced; research D6)
    ├── graph/
    │   ├── envelope.py            # DELETE — emit_json/emit_error moved to _envelope.py
    │   ├── build.py               # EDIT — import emit_json/emit_error from .._envelope
    │   └── query.py               # EDIT — import emit_json/emit_error from .._envelope
    └── focus/                     # NEW sub-package (mirrors commands/graph/)
        ├── __init__.py            # Typer sub-app; imports show/set/clear for registration
        ├── _project.py            # NEW — load_manifest_or_exit() shared load+fault boundary (research D10)
        ├── errors.py              # FocusError + FocusTargetEmptyError (BookwrightError subclasses)
        ├── show.py                # @app.command("show")
        ├── set.py                 # @app.command("set")
        └── clear.py               # @app.command("clear")

tests/
├── core/
│   ├── test_focus_block.py        # NEW — FocusBlock validation (target/notes/updated_at)
│   └── test_manifest_focus.py     # NEW — set_focus/clear_focus round-trip preservation
└── commands/focus/
    ├── test_show.py               # NEW — human + --json, present + absent
    ├── test_set.py                # NEW — create/update, partial notes, empty-target reject
    └── test_clear.py              # NEW — remove + no-op

bookwright-design.md               # + [focus] block documented in § 8.1 (Spanish)
```

**Structure Decision**: single-project src-layout. The new command group follows
the established `commands/graph/` shape (a Typer sub-app whose subcommands live in
their own modules and self-register at import), and the new block model follows
the `core/_research_block.py` extraction pattern. Manifest mutation reuses the
`Manifest.set_integration` precedent (mutate model field + `tomlkit` document
together). Tests mirror the existing `tests/core/` and `tests/commands/` layout.
The `--json` envelope (`emit_json`/`emit_error`) is **single-sourced** in the
existing shared `commands/_envelope.py` — `focus` imports it from there rather
than copying `graph/envelope.py` into a third file, and `graph` is repointed to
the same shared module so the iteration nets *less* duplication (research D6).
The three subcommands share one thin `focus/_project.py::load_manifest_or_exit`
load+fault helper (research D10) instead of triplicating the load/except block.

**Note — reconciling the iteration hint.** The implementation-plan hint names
`src/bookwright/commands/focus.py` *and* "un módulo por subcomando (Principio IV)".
Those two readings conflict for a command group with three subcommands. We follow
the operative constraint ("one module per subcommand") and the existing codebase
precedent (`commands/graph/`, `commands/integration/` are both sub-packages with
one module per subcommand) by delivering a `commands/focus/` sub-package rather
than a single `focus.py`. A single file would also be acceptable under the 500-line
ceiling, but the sub-package is the consistent choice. All other hint specifics —
optional `FocusBlock`, tomlkit comment-preserving round-trip, `BookwrightError`
subclass errors, standard `--json` envelope, `date.today().isoformat()` for
`updated_at`, and the listed tests — are adopted verbatim.

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
