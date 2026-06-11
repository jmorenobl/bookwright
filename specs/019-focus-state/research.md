# Phase 0 Research: Authored focus state

All Technical Context fields resolved from the existing codebase and
`bookwright-design.md § 21`. No external/library research was required (no new
dependency). The spec carried three resolved clarifications (notes semantics,
`updated_at` granularity, `--json` envelope shape); the decisions below cover the
remaining *implementation* choices.

## D1 — How to model an optional block whose fields are required when present

- **Decision**: Add `focus: FocusBlock | None = None` to `Manifest`. `FocusBlock`
  is a Pydantic v2 model (`extra="forbid", strict=True`) with `target: str`
  (non-empty), `updated_at: str` (ISO `YYYY-MM-DD`), and `notes: str = ""`.
  Absence of the block ⇒ `None`; presence ⇒ a fully-validated block.
- **Rationale**: `ResearchBlock` uses `default_factory` because *all* its fields
  carry defaults, so an absent block is indistinguishable from a default block.
  `[focus]` is different: when the block exists, `target` and `updated_at` are
  **required** (FR-001, FR-008, FR-011), so a defaulted block would be wrong.
  `FocusBlock | None = None` is the precise encoding — and `show --json` needs to
  distinguish "no focus" (`focus: null`, FR-005) from "focus present", which a
  defaulted block could not express.
- **Alternatives rejected**: (a) `default_factory=FocusBlock` with a defaulted
  `target=""` — would silently accept an empty target and cannot represent
  absence (breaks FR-005/FR-008). (b) A free `dict` in `extra` — loses
  validation (FR-011/FR-012).

## D2 — Storing `updated_at` as a string, validated on load

- **Decision**: Store `updated_at` as `str`, validated by a field validator that
  requires the exact shape `^\d{4}-\d{2}-\d{2}$` **and** that the value parses via
  `datetime.date.fromisoformat` (rejecting impossible dates like `2026-13-40`).
  Keep it a string in the model; never coerce to a `date` object.
- **Rationale**: Principle I — the manifest is hand-editable plain text; the
  stored form must be exactly what the author sees. Python 3.11's
  `date.fromisoformat` accepts several ISO 8601 spellings (e.g. `2026-W01-1`,
  basic format), so the regex pins the calendar-date form the clarification
  fixed (`YYYY-MM-DD`, no time/timezone) before the date-validity check. An
  invalid value raises a `PydanticCustomError` that `_translate_validation_error`
  renders as a normal `manifest_validation` failure naming `focus.updated_at`
  (FR-011) — no crash, no stack trace.
- **Alternatives rejected**: a `datetime.date` field — would reformat on
  round-trip and lose the author's exact bytes; bare `date.fromisoformat` without
  the regex — would accept non-`YYYY-MM-DD` ISO spellings the clarification ruled
  out.

## D3 — Comment-preserving writes: new `Manifest` methods, not raw tomlkit in the command

- **Decision**: Add `Manifest.set_focus(*, target, notes, updated_at)` and
  `Manifest.clear_focus()` to `manifest.py`. Each mutates **both** the validated
  `self.focus` field and the backing `self._document` `tomlkit` table, exactly
  like the existing `set_integration`. `set_focus` creates the `[focus]` table if
  absent (via `tomlkit.table()`, appended last) or updates the existing table in
  place; `clear_focus` removes the `[focus]` key from the document if present and
  sets `self.focus = None`. Both require a document-backed instance (from
  `load`/`build`) and raise `RuntimeError` otherwise — the same contract as
  `dump`/`set_integration`.
- **Rationale**: FR-009/SC-002 require byte-for-byte preservation of every other
  block, comment, and ordering. `set_integration` already proves the
  mutate-both-sides pattern preserves comments through `tomlkit`. Concentrating
  the mutation in the model keeps the command modules thin and keeps the
  round-trip guarantee testable at the unit level (`tests/core/`).
- **Alternatives rejected**: rebuilding the manifest via `Manifest.build` —
  would discard author comments/ordering (violates FR-009); editing `_document`
  directly inside each command module — scatters the round-trip invariant across
  three files and bypasses the model field, risking drift between document and
  model.

## D4 — Partial `notes` semantics resolved in the command, not the model

- **Decision**: The `focus set` command resolves the effective `notes` value
  **before** calling `set_focus`: `--notes` omitted ⇒ `None` at the CLI layer ⇒
  command reads the current `manifest.focus.notes` (or `""` when creating) and
  passes that; `--notes "X"` ⇒ pass `"X"`; `--notes ""` ⇒ pass `""` (clear).
  `set_focus` therefore always receives the final string and stays a pure writer.
  `target` and `updated_at` are always (re)written (FR-007).
- **Rationale**: keeps the "preserve vs clear" branch (the only stateful part) in
  one place at the CLI boundary where the `Optional[str]` `--notes` default
  cleanly encodes "omitted = None". The model method stays deterministic and
  trivially testable. Distinguish omitted (`None`) from empty (`""`) with
  Typer's `Optional[str] = typer.Option(None, "--notes")`.

## D5 — `updated_at` source: today's date, injectable for tests

- **Decision**: `focus set` stamps `updated_at` with the current local date as
  `date.today().isoformat()`. Wrap the read in a tiny module-level helper
  (`_today() -> str`) so tests can monkeypatch a deterministic date — the same
  indirection pattern as `manifest._installed_version()`.
- **Rationale**: FR-006 mandates auto-set on every write; SC-001 requires
  recovering the exact value; tests must assert a fixed date without freezing the
  system clock. The existing codebase already uses a thin function indirection
  for exactly this kind of test seam.

## D6 — Error surface: reuse the unified envelope; one new command-layer error

- **Decision**: Project/manifest faults reuse the existing remap
  (`invalid_manifest_payload` for caught `ManifestError`, `ProjectNotFoundError`
  for "not a project"). The one genuinely new failure — an empty/whitespace
  `--target` (FR-008) — is a `FocusTargetEmptyError(BookwrightError)` with code
  `focus_target_empty` in `commands/focus/errors.py`. The `emit_json` /
  `emit_error` pair is **single-sourced in the existing `commands/_envelope.py`**,
  not re-created per group: `focus` imports it from `.._envelope`, and **no
  `commands/focus/envelope.py` is created**.
- **Rationale**: Principle IX wants one canonical envelope; `BookwrightError`
  already owns `to_json()`, so the new error defines only a `code`. The empty
  target is a command-input concern (not an on-disk manifest concern), so the
  error belongs in the command layer, not `core`. `commands/_envelope.py` already
  exists for exactly this reason — review R1 created it to stop each command
  module hand-rolling the `{status,code,message}` skeleton, and it is already
  shared by `graph`, `integration`, and `validate`. Copying `graph/envelope.py`
  verbatim into a third file would be the precise drift that module exists to
  prevent.
- **Consolidation (the DRY fix, now in-scope)**: `emit_json`/`emit_error` move
  from `graph/envelope.py` into `commands/_envelope.py`; `graph/build.py` and
  `graph/query.py` are repointed to `from .._envelope import emit_json, emit_error`
  and `graph/envelope.py` is deleted. That is two import-line edits in
  fully-tested shipped modules plus one file removal — the entire "blast radius"
  the earlier draft cited — and the iteration ends with *less* envelope
  duplication than it started with, not more. (This was previously deferred as
  "widens blast radius for no behavioural gain"; that no longer holds once the
  shared module already exists and `focus` would otherwise birth a verbatim third
  copy. The graph refactor is verified by graph's existing tests + the T026 gate
  sweep; it is iteration-local cleanup, not speculative plumbing.)
- **Alternatives rejected**: a per-group `commands/focus/envelope.py` copy — the
  duplication just described. Validating the empty target inside `FocusBlock`
  instead — wouldn't fire, since the command rejects before constructing a block,
  and FR-008 requires the manifest be left *unchanged*.

## D7 — Exit codes

- **Decision**: `0` on success for all three subcommands — including
  `show`/`clear` when no `[focus]` exists (FR-005, FR-010 no-op). Any error
  (not a project, invalid manifest, empty `--target`) exits `2`. The structured
  distinction between error kinds lives in the JSON envelope's `code`, not the
  exit code.
- **Rationale**: exit `2` is the conventional usage/config error code (Typer/
  Click default and the `graph` group's `EXIT_CONFIG`). The agent contract is the
  `code` field (Principle IX), so collapsing error kinds to a single non-zero
  exit is consistent with the rest of the CLI while the envelope stays precise.

## D8 — Human-output channel discipline

- **Decision**: In non-`--json` mode the *content* of `show` (target, notes,
  date) prints to **stdout**; status/confirmation/empty notes ("no focus
  defined", "focus set", "no focus to clear") print to **stderr** via a
  `Console(stderr=True)`. In `--json` mode stdout carries exactly one JSON
  document and nothing else.
- **Rationale**: Principle IX — the deliverable goes to stdout, progress/prose to
  stderr; this matches `graph query`'s split (results to stdout, "(no results)"
  to stderr) and keeps `--json` stdout clean.

## D9 — Design-doc edit (FR-014)

- **Decision**: Add the `[focus]` block to the `manifest.toml` spec in
  `bookwright-design.md § 8.1` (the canonical TOML listing), in **Spanish**,
  consistent with the worked example already in `§ 21.3`. Document the three
  fields and that the block is optional and CLI-stamped.
- **Rationale**: FR-014 requires the canonical manifest spec document the block;
  `§ 8.1` is where every other block is specified; Spanish per the language
  convention for design docs. `§ 21.3` already shows the block — `§ 8.1` is the
  normative home it must also appear in.

## D10 — One project-load + fault boundary helper for the three subcommands

- **Decision**: Factor the shared `find_project_root()` + `Manifest.load(...)` +
  `--json` fault remap (`ManifestError → invalid_manifest_payload`,
  `ProjectNotFoundError → to_json()`, exit 2) into a single thin helper —
  `commands/focus/_project.py::load_manifest_or_exit(json_output) -> tuple[Path, Manifest]`
  — called by `show`/`set`/`clear`. The helper covers **only** the project/manifest
  load boundary; `set` keeps its own `FocusTargetEmptyError` rejection (FR-008) in
  the command body. It is created in US1 (the first consumer) and reused by US2/US3.
- **Rationale**: three sibling subcommands are created at once in a fresh package;
  triplicating the identical load+except block at birth is avoidable debt. Scoping
  the helper to the load boundary keeps each command's body to its own logic and
  keeps the empty-target branch — the only per-command fault — visible where it
  belongs. (`graph` repeats this block per command; `focus` does not, because all
  three are written together rather than extending an existing one.)
