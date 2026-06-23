# Feature Specification: `validate` surfaces ingestion-skipped bible files

**Feature Branch**: `046-validate-skip-surfacing`

**Created**: 2026-06-23

**Status**: Draft

**Input**: User description: "Necesidad: cuando un fichero de la bible tiene front-matter inservible (YAML roto), `map_bible` lo OMITE … Esta iteración hace que `validate` propague los `skipped` de la ingestión a su canal `not_evaluated[]` … de modo que un corpus parcial deje de leerse como verde."

## Context

When a bible file has unusable front-matter (broken YAML), the ingestion step
(`map_bible`) **omits** it: the file is recorded in `MapResult.skipped` (a list
of `SkippedFile{path, reason}`) and that entity never enters the graph or any
validation.

The two agent-facing commands disagree about whether this matters:

- `bookwright status` treats a skip as **blocking**: it runs `build_project_graph`
  and, if `outcome.report.skipped` is non-empty, aborts with `code=skipped_sources`
  ("status will not report facts computed from a partial corpus", `commands/status.py:151`).
- `bookwright validate` — the CI gate — proceeds **silently** over the partial
  corpus: it emits `not_evaluated: []` and never mentions the skip.

So after a broken-YAML file is introduced, `validate` reads as fully green and
`not_evaluated: []` reads as "everything was evaluated" — when in fact a whole
file was excluded from the corpus. This is exactly the `[]`-lies-as-clean failure
iteration 040 set out to erase, and it is the `status`↔`validate` asymmetry that
DEBT-018 recorded. Verified: `bible/characters/rota.md` (broken YAML) → `status`
errors, `validate` runs clean with no mention.

This iteration makes `validate` **propagate** the ingestion `skipped` files into
its `not_evaluated[]` channel (the channel iteration 040 added, kind-categorized
since 044), so a partial corpus stops reading as green. It reuses the channels
040/044 already wired — no new channel, no predicate change.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A skipped bible file is no longer silently green (Priority: P1)

An author (or CI) runs `bookwright validate` on a project where one bible file
has broken YAML front-matter. Today the run reads as fully clean. After this
change, the run surfaces the skipped file in `not_evaluated[]` as an
input-conditional gap and no longer reads as green — matching the hard refusal
`status` already gives for the same project.

**Why this priority**: This is the whole feature — closing the silent-partial-corpus
hole in the CI gate (DEBT-018). Without it the rest does not exist.

**Independent Test**: Build a project with one bible character file whose
front-matter is broken YAML; run `validate --json`; assert (a) a `not_evaluated`
entry naming that file with `kind == "missing_input"` exists, and (b) the run is
not green under the 044 refined predicate.

**Acceptance Scenarios**:

1. **Given** a project whose `bible/characters/rota.md` has unusable YAML
   front-matter, **When** `bookwright validate --json` runs, **Then** the
   `not_evaluated[]` array contains one entry whose `reason` cites
   `bible/characters/rota.md` and the skip cause, and whose `kind` is
   `missing_input`.
2. **Given** the same project, **When** the run completes, **Then** it is **not**
   green (the 044 green predicate denies green because a `missing_input`
   `not_evaluated` entry is present).
3. **Given** the same project, **When** `validate` runs, **Then** the process
   exit code is unchanged from today (a skip is not an `error`-severity finding,
   so it does not break the CI gate / exit code).
4. **Given** a project with **no** skipped bible files, **When** `validate` runs,
   **Then** no skip-derived `not_evaluated` entry is produced and the result is
   byte-identical to today's (pinned fixtures unchanged).
5. **Given** a project with **two** broken-YAML bible files, **When** `validate
   --json` runs twice, **Then** both runs emit two skip-derived `not_evaluated`
   entries in the **same** order (byte-identical), proving the total-order key
   resolves the shared-`validator` tie (FR-009).

---

### User Story 2 - The skip is visible in both `validate` surfaces (Priority: P2)

An author reading the human report or the `--json` envelope of `bookwright
validate` can see *which* file was skipped and *why*, using the same
`not_evaluated[]` rendering 040/044 already wired (no second channel to learn).
`bookwright status` already refuses the same input outright (`skipped_sources`),
so the partial corpus is never silent on any surface.

**Why this priority**: Surfacing-everywhere is what makes the degraded-green
actionable; it rides on the P1 channel but is a distinct observable.

**Independent Test**: For the broken-YAML project, assert the skip entry appears
in (a) the `--json` `not_evaluated[]` with its `kind`, and (b) the human report's
`not evaluated:` section.

**Acceptance Scenarios**:

1. **Given** the broken-YAML project, **When** `validate --json` runs, **Then**
   the skip entry serializes in `not_evaluated[]` with `validator`, `reason`, and
   `kind` keys (the existing `NotEvaluatedResult` shape).
2. **Given** the broken-YAML project, **When** `validate` runs without `--json`,
   **Then** the human report's `not evaluated:` section lists the skip entry with
   its kind label.

---

### User Story 3 - `validate` and `status` agree that a skip is reportable (Priority: P2)

The two commands stop disagreeing about whether a skipped bible file is worth
reporting: `status` already refuses; after this change `validate` also surfaces
it (degrading green), so neither command reads a partial corpus as fully fine.

**Why this priority**: Resolving the `status`↔`validate` asymmetry is the framing
of DEBT-018; it is observable as a cross-command consistency property.

**Independent Test**: For the broken-YAML project, assert `status` still errors
with `skipped_sources` AND `validate` now surfaces the same file in
`not_evaluated[]` — the two no longer disagree about reportability.

**Acceptance Scenarios**:

1. **Given** the broken-YAML project, **When** both commands run, **Then**
   `status` aborts with `code=skipped_sources` (unchanged) and `validate`
   surfaces the same skipped file in `not_evaluated[]` (new) — both report it.

---

### Edge Cases

- **Multiple skipped files**: every skipped bible file produces its own
  `not_evaluated` entry; the entries are emitted in a deterministic order so the
  human report and JSON are byte-identical across runs (consistent with the
  existing `not_evaluated` total-order guarantee).
- **A skip plus a real `error` finding**: the exit code is still driven solely by
  `error`-severity violations; the skip entry degrades green and is visible but
  does not change the gate.
- **A skip on a project that also has `pending_capability` abstentions** (e.g.
  `focalization` under limited-third): both kinds coexist in `not_evaluated[]`;
  only the `missing_input` skip entry denies green.
- **`status` never reaches its embedded validation state on a skip** (it aborts
  earlier with `skipped_sources`), so this change does not require any edit to
  the `status` next-action nudge or remedy table — those are out of scope and
  untouched.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `validate` MUST read the bible files omitted during ingestion (the
  `skipped` list of the `MapResult`, available via `ValidationContext.bible().skipped`)
  while assembling its result.
- **FR-002**: For each skipped bible file, `validate` MUST add one entry to the
  `not_evaluated[]` channel with `kind = missing_input` (a skipped file is
  input-conditional: the author fixes the YAML and it is evaluated again).
- **FR-003**: Each such entry's `reason` MUST be a human-readable string that
  cites the skipped file path and the skip cause (e.g. `bible file
  'bible/characters/rota.md' skipped (unusable front-matter): <reason>`). The
  exact wording is fixed in `/speckit-plan`.
- **FR-004**: Each such entry's `validator` field MUST use a stable, readable
  identifier for the non-validator origin (the skipped file is not a validator);
  the recommended value is `ingestion`, with the path and cause carried in the
  `reason`. The exact identifier is fixed in `/speckit-plan`.
- **FR-005**: The presence of a `missing_input` `not_evaluated` entry MUST degrade
  green automatically via the **unchanged** 044 refined predicate (green ⟺
  `status == "ok"` AND no `not_evaluated` entry has `kind == "missing_input"`).
  The predicate MUST NOT be modified.
- **FR-006**: A skip MUST NOT be reported with `kind = pending_capability` (that
  would leave the partial corpus reading as green — the bug). It MUST be
  `missing_input`.
- **FR-007**: A skip MUST NOT be emitted as an `error`-severity violation and MUST
  NOT change the process exit code / CI gate. A skip degrades the informational
  green and becomes visible; the gate (only `error` breaks the exit code) is
  unchanged. (Hardening the gate so a skip breaks the exit code is a separate
  decision — out of scope; see Assumptions.)
- **FR-008**: The skip entries MUST be surfaced in **both** surfaces `validate`
  emits — the `--json` envelope and the human report — by reusing the
  `not_evaluated[]` channel 040/044 already wired (`kind` included). No new
  `skipped[]` channel may be added. `bookwright status` is **not** a third skip
  surface: it aborts on any skip with `code=skipped_sources` (`commands/status.py:151`)
  *before* it builds its embedded `state.validation`, so a skip never reaches
  `status`'s `not_evaluated` and `status` requires no edit. The skip is therefore
  surfaced by `validate` (degrading green) and refused by `status` independently —
  the two no longer disagree (FR / User Story 3), but they report it by **different**
  pre-existing mechanisms, not a shared third channel.
- **FR-009**: The `not_evaluated[]` list MUST be ordered by a **total-order** key so
  the JSON and human report are byte-identical across runs — including when multiple
  skipped files all carry the same `validator` identifier. The runner's current
  `not_evaluated` sort key (`lambda r: r.validator`, `validation/runner.py:80`) is
  only a *partial* order (ties broken by insertion order); it is safe today solely
  because each validator emits at most one entry, but the skip entries break that
  assumption (they share one identifier). This is one determinism class: the key
  MUST be promoted to a total order (e.g. `(validator, reason)`) and that **single**
  key MUST be applied at every site that sorts `not_evaluated` (the runner and the
  `validate` skip-merge), so the two sort sites cannot diverge. Promoting the key
  MUST NOT change any skip-free fixture (validator names are already unique, so no
  tie exists to reorder — FR-010).
- **FR-010**: A project with no skipped bible files MUST produce no skip-derived
  `not_evaluated` entry and MUST remain byte-identical to today's behavior; pinned
  fixtures without skips MUST NOT be edited.
- **FR-011**: The `not_evaluated[]` channel data model and the `kind` vocabulary
  MUST NOT change — this iteration only **consumes** what 040/044 delivered (no
  new field, no new kind, no predicate change).
- **FR-012**: The change MUST live in `commands/validate.py` (read
  `ValidationContext.bible().skipped` and merge one `not_evaluated` entry per skip
  into the report) plus `validation/runner.py` (the total-order sort-key promotion
  of FR-009). The `NotEvaluatedResult` model, the `kind` vocabulary, and the green
  predicate MUST NOT change (FR-011). No **validator** module may be touched, and
  the frozen ontology MUST remain intact.
- **FR-013**: The DEBT-018 entry MUST be removed from `DEBT.md` (git keeps the
  history); the cross-references to DEBT-018 in `DEBT.md` MUST be reconciled so no
  dangling pointer remains.

### Constitutional / scope constraints

- **FR-014**: No new runtime dependency (Constitution II); stdlib + existing deps
  only.
- **FR-015**: Each changed file MUST stay ≤ 500 lines (Principle IV).
- **FR-016**: Tests MUST verify the behavior **empirically** with `uv run pytest`;
  the four gates (`ruff check`, `ruff format --check`, `mypy --strict`, `pytest`
  with ≥ 80 % coverage) MUST stay green.

### Key Entities

- **`MapResult.skipped`**: the existing ingestion channel — a list of
  `SkippedFile{path, reason}`, already reachable from a validator/command via
  `ValidationContext.bible().skipped`. This iteration reads it; it does not change it.
- **`NotEvaluatedResult{validator, reason, kind}`**: the existing not-evaluated
  result record (frozen). A skipped file becomes one of these with
  `validator = ingestion` (recommended), a path+cause `reason`, and
  `kind = missing_input`. The model is unchanged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a project with exactly one broken-YAML bible file, `validate
  --json` produces exactly one skip-derived `not_evaluated` entry that names that
  file, and the run is not green — verified by an automated test.
- **SC-002**: For the same project, the process exit code from `validate` is
  identical to a no-skip run with the same findings (a skip alone does not break
  the gate) — verified by an automated test.
- **SC-003**: For a project with **no** skipped bible files, the `validate` output
  is byte-identical to before this change; no pinned skip-free fixture is edited —
  verified by the existing suite staying green with unmodified fixtures.
- **SC-004**: `validate` and `status` no longer disagree on a skipped bible file:
  `status` still aborts with `skipped_sources` and `validate` now surfaces the
  same file — verified by an automated cross-command test.
- **SC-005**: DEBT-018 is gone from `DEBT.md` and no remaining `DEBT.md` text
  points to it as open.

## Assumptions

- **Recommended posture (carried into `/speckit-plan`)**: surface + degrade green,
  do **not** harden the CI gate. The focus of DEBT-018 is the *silence*, not the
  exit code; breaking builds that pass today (by making a skip an `error`) is a
  separate decision that `/speckit-plan` may revisit but this spec excludes. The
  asymmetry with `status`'s hard refusal is resolved at the *reporting* level, not
  the exit-code level.
- The recommended `validator` identifier for a skip entry is `ingestion`; the
  recommended `reason` template is `bible file '<path>' skipped (unusable
  front-matter): <reason>`. Both exact forms are fixed in `/speckit-plan`.
- `ValidationContext.bible().skipped` is already populated by `map_bible` and is
  the read path; no ingestion change is needed.
- The 044 machinery (the green predicate, `NotEvaluatedKind`, the `not_evaluated[]`
  serialization, the `status` next-action nudge that already filters `missing_input`,
  the `_REMEDIES` table, the `_KIND_LABEL` render) is reused unchanged. Because
  `status` aborts on a skip before embedding validation state, no nudge/remedy edit
  is required.

## Out of Scope

- Hardening the CI gate so a skip breaks the exit code (separate decision; DEBT-018's
  focus is the silence).
- `outline` skips — DEBT-018 is about the bible. If outline skips matter, that is
  its own entry, not this iteration.
- The LLM semantic-judgment escalation (move 3).
- Any change to the green predicate or the `kind` channel (044 delivered both;
  here they are only consumed).
- `character_presence` / `character_unknown_mentions` and the `focalization`
  head-hopping abstention (043 / 045).
