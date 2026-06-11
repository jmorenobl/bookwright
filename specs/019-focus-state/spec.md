# Feature Specification: Authored focus state

**Feature Branch**: `019-focus-state`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Necesidad: un proyecto Bookwright no tiene hoy ningún sitio donde quede registrado «qué estoy trabajando ahora» ni los hilos o decisiones pendientes. Necesitamos un estado de foco pequeño, escrito por el autor, persistido en texto plano canónico, que cualquier skill o comando pueda leer. Bloque opcional `[focus]` en `manifest.toml` con `target`, `notes`, `updated_at`; comandos `bookwright focus show | set | clear`."

## Overview

A Bookwright project currently has no place to record *what the author is
working on right now* or the open threads and pending decisions in their head.
When a new working session starts, that intent is lost and skills have nothing
to orient themselves from. This feature introduces a small, **author-written**
focus state, persisted in the project's canonical plain-text manifest, that any
skill or command can later read.

The focus state lives in an optional `[focus]` block inside `manifest.toml`
(extending the manifest spec in `bookwright-design.md § 8`) and is managed
through a new `bookwright focus` command group. This iteration delivers only
the authored state and its read/write/clear commands; derived state, the
`status` command, and skill consumption are deferred to later iterations.

## Clarifications

### Session 2026-06-05

- Q: On `focus set` against an existing block, what happens to `notes` when `--notes` is omitted? → A: Partial update — omitting `--notes` preserves the existing `notes`; passing `--notes ""` clears it. `target` and `updated_at` always refresh. (`--notes` omitted = `None` = keep; `--notes ""` = clear; `--notes "X"` = set to `X`.)
- Q: What granularity should the auto-set `updated_at` use? → A: ISO 8601 *calendar date* `YYYY-MM-DD` (no time/timezone), matching the hand-editable plain-text manifest (Principle I).
- Q: How should `focus show --json` shape its output? → A: The project's standard success envelope — `{"status":"ok","focus":{…}}` when a block exists, `{"status":"ok","focus":null}` when absent — consistent with `graph query` and the unified error envelope (Principle IX).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record the current focus (Priority: P1)

As an author returning to my book, I want to write down what I am working on
right now — a target and a short log of open threads and pending decisions — so
that the intent survives between sessions and is captured in the project's
plain-text source of truth.

**Why this priority**: This is the core write path and the reason the feature
exists. Without the ability to record a focus, there is nothing to read, clear,
or later orient skills from. It is the minimum viable slice.

**Independent Test**: Run `bookwright focus set --target "arco de Berlín"
--notes "cerrar línea temporal del cap-04"` in a project, then open
`manifest.toml` and confirm a `[focus]` block exists with the given target,
notes, and a `updated_at` set to today's date, while all other manifest content
(comments, formatting, ordering) is unchanged.

**Acceptance Scenarios**:

1. **Given** a project whose manifest has no `[focus]` block, **When** the author
   runs `focus set --target "cap-04"`, **Then** a `[focus]` block is created with
   `target = "cap-04"` and `updated_at` set to the current date, and the command
   reports success.
2. **Given** a project that already has a `[focus]` block, **When** the author
   runs `focus set --target "arco de Berlín" --notes "decidir POV"`, **Then** the
   existing block's `target` and `notes` are updated and `updated_at` is refreshed
   to the current date.
3. **Given** any project, **When** the author runs `focus set` with an empty or
   whitespace-only `--target`, **Then** the command rejects the input with a clear
   error and the manifest is left unchanged.
4. **Given** a manifest with author comments and custom formatting, **When** the
   author runs `focus set`, **Then** every other block, comment, and formatting
   choice in the manifest is preserved byte-for-byte except for the `[focus]`
   block being written.

---

### User Story 2 - View the current focus (Priority: P2)

As an author (or a human reading the project), I want to see the current focus
in a readable form, and optionally as JSON, so I can quickly recall my intent or
let tooling consume it.

**Why this priority**: Reading the focus is the immediate payoff of recording
it and is needed for the human loop, but it depends on US1 having produced
something to read. The JSON form is the contract future skills will rely on.

**Independent Test**: In a project with a `[focus]` block, run
`bookwright focus show` and confirm it prints the target, notes, and last-updated
date legibly; run `bookwright focus show --json` and confirm it emits a single
JSON document with those fields. In a project without a `[focus]` block, run both
and confirm each clearly reports "no focus defined" without raising an error.

**Acceptance Scenarios**:

1. **Given** a project with a `[focus]` block, **When** the author runs
   `focus show`, **Then** the target, notes, and `updated_at` are displayed in a
   readable human form.
2. **Given** a project with a `[focus]` block, **When** the author runs
   `focus show --json`, **Then** a single JSON document containing the focus
   fields is emitted on stdout and nothing else.
3. **Given** a project with no `[focus]` block, **When** the author runs
   `focus show`, **Then** the command clearly states that no focus is defined and
   exits successfully (no error).
4. **Given** a project with no `[focus]` block, **When** the author runs
   `focus show --json`, **Then** an equivalent JSON document indicating the
   absence of focus is emitted and the command exits successfully.

---

### User Story 3 - Clear the focus (Priority: P3)

As an author who has finished a thread or wants to reset, I want to remove the
focus state entirely so the project returns to having no recorded focus.

**Why this priority**: A convenience for resetting state. Useful but not part of
the essential capture-and-read loop, and an author could otherwise overwrite the
focus instead.

**Independent Test**: In a project with a `[focus]` block, run
`bookwright focus clear` and confirm the `[focus]` block is removed from
`manifest.toml` while the rest of the manifest is preserved.

**Acceptance Scenarios**:

1. **Given** a project with a `[focus]` block, **When** the author runs
   `focus clear`, **Then** the `[focus]` block is removed from the manifest and
   all other content is preserved, and the command reports success.
2. **Given** a project with no `[focus]` block, **When** the author runs
   `focus clear`, **Then** the command succeeds as a no-op and clearly reports
   that there was no focus to clear (no error).

---

### Edge Cases

- **Empty target on set**: `focus set` with a missing, empty, or whitespace-only
  `--target` is rejected with a clear error; the manifest is not modified.
- **Notes omitted on create**: `focus set --target "X"` with no `--notes` creates
  the block with no notes (an empty or absent notes field).
- **Notes omitted on update**: `focus set --target "X"` with no `--notes` on an
  existing block leaves the existing `notes` unchanged (target and `updated_at`
  are updated). Passing `--notes ""` explicitly clears the notes. See FR-007.
- **Invalid `updated_at` on load**: a manifest whose `[focus].updated_at` is not a
  valid ISO 8601 date produces a clear manifest error (consistent with other
  manifest validation errors), never a crash or stack trace.
- **No focus block**: the absence of `[focus]` is fully normal — `show` and
  `clear` handle it gracefully and no other command (graph, validate, init, …) is
  affected.
- **Not a Bookwright project**: running any `focus` subcommand outside a project
  with a `manifest.toml` fails with the same clear "not a project" error other
  manifest-reading commands already produce.
- **Backward compatibility**: an existing v0.2 project with no `[focus]` block
  continues to load, validate, and run exactly as before.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The manifest MUST support an optional `[focus]` block with three
  fields: `target` (string), `notes` (free-text string), and `updated_at`
  (ISO 8601 calendar date, `YYYY-MM-DD`, with no time or timezone component).
- **FR-002**: The `[focus]` block MUST be entirely optional. Its absence MUST NOT
  affect the loading, validation, or behavior of any other command (graph,
  validate, init, etc.), and existing v0.2 projects MUST continue to work
  unchanged.
- **FR-003**: `bookwright focus show` MUST display the current focus (target,
  notes, last-updated date) in a readable human form when a `[focus]` block
  exists.
- **FR-004**: `bookwright focus show --json` MUST emit a single JSON document on
  stdout — and only that document (human prose and progress go to stderr), per
  Principle IX — using the standard success envelope:
  `{"status":"ok","focus":{"target":…,"notes":…,"updated_at":…}}`.
- **FR-005**: When no `[focus]` block exists, `bookwright focus show` MUST clearly
  report that no focus is defined and exit successfully; `--json` MUST emit
  `{"status":"ok","focus":null}` and exit successfully — in neither case an error.
- **FR-006**: `bookwright focus set --target "<text>"` MUST create the `[focus]`
  block if absent or update it if present, and MUST set `updated_at` to the
  current date automatically.
- **FR-007**: `bookwright focus set` MUST accept an optional `--notes "<text>"`
  argument with partial-update semantics: when `--notes` is **omitted**, an
  existing block's `notes` is preserved (and a newly created block has no notes);
  `--notes "<text>"` sets `notes` to that text; `--notes ""` clears `notes`. In
  all cases `target` and `updated_at` are (re)written.
- **FR-008**: `bookwright focus set` MUST reject an empty or whitespace-only
  `--target` with a clear error and leave the manifest unchanged.
- **FR-009**: Writing the `[focus]` block (via `set` or `clear`) MUST preserve the
  rest of the manifest, including author comments, formatting, and block ordering.
- **FR-010**: `bookwright focus clear` MUST remove the `[focus]` block from the
  manifest, preserving the rest of the manifest, and report success. When no
  block exists it MUST succeed as a no-op with a clear message.
- **FR-011**: On loading a manifest, an invalid `updated_at` (not a valid ISO 8601
  date) MUST produce a clear manifest error consistent with the project's existing
  manifest-error reporting — never an uncaught crash.
- **FR-012**: `target` and `notes` MUST be validated as strings on load; a
  non-string value MUST produce a clear manifest error.
- **FR-013**: Every `focus` subcommand MUST accept `--json` and, when given, emit
  a single JSON document on stdout following the project's standard success
  envelope (`{"status":"ok", …}`) and the unified `--json` error envelope on
  failure (Principle IX).
- **FR-014**: The canonical manifest specification (`bookwright-design.md § 8.1`)
  MUST be updated to document the `[focus]` block and its fields.

### Key Entities *(include if feature involves data)*

- **Focus state**: the author's current working intent, persisted as the optional
  `[focus]` block in `manifest.toml`. Attributes:
  - **target**: short text naming what is being worked on now (e.g.
    "arco de Berlín", "cap-04"). Required when the block exists.
  - **notes**: free-text log of open threads and pending decisions; a brief
    journal entry. Optional.
  - **updated_at**: ISO 8601 calendar date (`YYYY-MM-DD`) the CLI sets
    automatically whenever the block is written. Validated on load.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After running `focus set --target "X"`, an author can reopen the
  project in a new session and recover the exact target and notes via `focus show`
  with no information loss.
- **SC-002**: 100% of `focus set` / `focus clear` operations preserve all other
  manifest content (comments, formatting, ordering) unchanged, verified by diffing
  the manifest before and after.
- **SC-003**: An author can record their current focus in a single command
  invocation, and read it back in a single command invocation.
- **SC-004**: Every existing v0.2 project loads, validates, and runs every
  non-focus command with identical results whether or not a `[focus]` block is
  present (zero regressions).
- **SC-005**: A manifest with an invalid `updated_at` value yields a clear,
  human-readable manifest error in 100% of cases, with no uncaught exceptions or
  stack traces shown to the user.
- **SC-006**: Every `focus` subcommand, when invoked with `--json`, emits exactly
  one JSON document on stdout and nothing else on stdout.

## Assumptions

- **updated_at granularity** (resolved — see Clarifications): ISO 8601 calendar
  date `YYYY-MM-DD`, sufficient for the authoring loop; sub-day precision is not
  required.
- **Notes update semantics** (resolved — see Clarifications / FR-007): partial
  update — omitting `--notes` preserves existing notes, `--notes ""` clears them.
- **`focus clear` idempotency**: clearing when no `[focus]` block exists is a
  successful no-op, not an error, matching the principle that the block's absence
  is normal.
- **Error reporting**: focus commands reuse the project's existing manifest-error
  and `--json` error-envelope conventions rather than introducing a new error
  surface.
- **Scope of "preserve the manifest"**: preservation is guaranteed for all blocks,
  comments, and formatting other than the `[focus]` block itself, consistent with
  the manifest's existing comment-preserving round-trip behavior.

## Out of Scope

- **Derived state** (anchors, validation status, etc.) and the `bookwright status`
  command — deferred to iteration 020.
- **Next-step recommendations** (`next_actions`) — deferred to iteration 020.
- **Skills reading or writing the focus** — deferred to iterations 021–022.
- **An append-only history / versioned journal** of focus changes — out of this
  milestone (the current focus plus `notes` is sufficient for the loop;
  versioning would be over-engineering).

## Dependencies

- Extends the existing `manifest.toml` model and its comment-preserving
  round-trip (`bookwright-design.md § 8`).
- Reuses the project's manifest validation and `--json` error-envelope
  infrastructure (Principle IX).
