# Feature Specification: `character_presence` unknown-mention rule cross-checks settings, locations & objects

**Feature Branch**: `042-character-presence-roster`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "Necesidad: el validador `character_presence` tiene dos reglas. La regla de huérfanos (severidad `error`, protege el gate) verifica que cada PERSONAJE de la bible se mencione en el manuscrito. La regla de menciones-desconocidas (severidad `warning`) marca todo nombre propio del manuscrito que «no tiene entrada en la bible» — pero solo cruza contra el roster de PERSONAJES. … Esta iteración cierra DEBT-010 …"

## Context

The `character_presence` validator is a prose continuity check with two rules split by
severity so a heuristic false positive can never fail CI:

- **Orphan rule** (`error`, protects the gate): every bible **character** must be
  mentioned somewhere in the manuscript; an unmentioned character is reported.
- **Unknown-mention rule** (`warning`, conservative heuristic): a proper-noun candidate
  in the prose that has **no bible entry** is flagged ("heuristic — may be a place or
  organization").

The unknown-mention rule cross-checks proper-noun candidates against the **character
roster only**. A book's settings, locations and objects are already declared in the
bible — under `bible/settings/`, `bible/locations/`, `bible/objects/` — yet their names
are invisible to this rule. A multi-word setting such as "la Real Fábrica de Paños"
(declared in `bible/settings/la-real-fabrica-de-panos.md`) therefore makes its capitalized
tokens `Real`, `Fábrica`, `Paños` each fire a spurious "no bible entry" warning, even
though the entry **exists** — it simply lives in `settings/` rather than `characters/`.
The warning text is honest, but on a novel whose environments are fully declared the
diagnosis is misleading and the noise is high. This was recorded as **DEBT-010**,
detected by the end-to-end `tiny-historical` dogfood after `v0.5.0`.

This iteration (042, `v0.5.2`) closes DEBT-010 by widening the unknown-mention rule's
"known names" set to the **union** of the character, setting, location and object
rosters. It is the per-class fix consistent with the issue #1 doctrine: the orphan rule
that protects the gate, and the `not-evaluated` guard from iteration 040, both stay
exactly as they are.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Declared settings stop being mis-flagged as unknown proper nouns (Priority: P1)

An author has a bible with characters **and** settings/locations/objects already declared,
and a manuscript that names those environments in prose. When they run validation, the
multi-word and single-word names of those declared environments must **not** be reported
as proper nouns "with no bible entry" — because they have one.

**Why this priority**: This is the entire defect (DEBT-010). On a finished novel the
environment-token noise drowns the genuine findings and makes the warning channel
untrustworthy. Fixing it is the iteration's reason to exist.

**Independent Test**: Run validation over a project whose bible declares a setting like
"la Real Fábrica de Paños" and whose manuscript names it. Confirm `Real`, `Fábrica` and
`Paños` produce **no** unknown-mention warning, where today each produces one.

**Acceptance Scenarios**:

1. **Given** a bible setting "la Real Fábrica de Paños" and a manuscript line that names
   it, **When** `character_presence` runs, **Then** no unknown-mention warning is emitted
   for `Real`, `Fábrica`, or `Paños`.
2. **Given** a bible location declared under `bible/locations/` whose name appears in the
   manuscript, **When** `character_presence` runs, **Then** that name (full phrase or any
   ≥3-letter token) produces no unknown-mention warning.
3. **Given** a bible object declared under `bible/objects/` whose name appears in the
   manuscript, **When** `character_presence` runs, **Then** that name (full phrase or any
   ≥3-letter token) produces no unknown-mention warning.

---

### User Story 2 - A genuinely off-bible name still fires (Priority: P1)

A proper noun that matches **no** entry anywhere in the bible — not a character, setting,
location, or object — must still be reported as an unknown mention, exactly as before.
Widening the roster must suppress only false positives, never silence a real one.

**Why this priority**: The warning's value is catching names that escaped the bible. If
the wider roster swallowed those too, the fix would trade noise for blindness.

**Independent Test**: Add a manuscript proper noun absent from every bible folder and
confirm it still produces one unknown-mention warning.

**Acceptance Scenarios**:

1. **Given** a manuscript proper noun with no entry in characters, settings, locations or
   objects, **When** `character_presence` runs, **Then** it is reported as an unknown
   mention (one finding, citing its first occurrence), unchanged from today.

---

### User Story 3 - The gate-protecting orphan rule is untouched (Priority: P1)

The orphan rule (`error`) keeps deriving exclusively from the **character** roster. A
setting, location or object that is declared but never mentioned is **not** a character
orphan and must produce neither an error nor a warning of absence. Every existing `error`
finding must come out byte-for-byte identical.

**Why this priority**: The orphan rule is what gates CI. Any change to its output would
be a behavior change to the gate, which is explicitly out of scope and dangerous.

**Independent Test**: Run validation over the existing fixtures and confirm the set of
`error` findings is byte-for-byte unchanged; confirm an unmentioned setting yields no new
finding of any severity.

**Acceptance Scenarios**:

1. **Given** the existing fixtures, **When** validation runs, **Then** the `error`-level
   orphan findings are byte-for-byte identical to before this change.
2. **Given** a declared setting/location/object that is never mentioned in the manuscript,
   **When** `character_presence` runs, **Then** no orphan error and no absence warning is
   produced for it.

---

### User Story 4 - The `not-evaluated` guard is unchanged (Priority: P2)

`character_presence` continues to declare itself *not-evaluated* under exactly the same
condition as iteration 040 — only when there is **no manuscript prose AND no character
roster** — with an identical textual reason. Declared settings/locations/objects with no
prose and no characters still leave nothing to cross-check.

**Why this priority**: The tri-valued result (iteration 040) is a load-bearing contract;
this iteration must not perturb when the validator abstains.

**Independent Test**: Run over a project with no manuscript prose and no characters
(settings present) and confirm the validator still reports the same not-evaluated reason
as before.

**Acceptance Scenarios**:

1. **Given** no manuscript prose and an empty character roster, **When**
   `character_presence` runs, **Then** it raises the same not-evaluated signal with the
   identical reason text as iteration 040, regardless of any declared
   settings/locations/objects.

---

### Edge Cases

- **Token vs. full-phrase matching**: the wider roster matches the same way the character
  roster already does — the full declared name **and** each of its ≥1-character tokens —
  so a single token of a multi-word setting (e.g. `Paños`) is suppressed. (Tokens that
  slugify to empty are skipped, as today.)
- **Accent/case folding**: matching is by slug, so accented and case variants of a
  declared name match (`Fábrica` ↔ the slug of "Fábrica"), consistent with the existing
  character behavior.
- **Empty or absent settings/locations/objects folders**: contribute no names; behavior
  is exactly as before this change (no new findings, no errors).
- **A name shared across rosters** (e.g. a character and a location with the same token):
  remains suppressed; union membership is monotonic — adding rosters can only suppress
  more, never re-introduce a finding.
- **Lowercase environment words** (e.g. "almacén", "viejo", the article "El") are not
  proper-noun candidates and were never flagged; unaffected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The validation context MUST expose cached accessors for the **location**
  roster and the **object** roster, mirroring the existing setting accessor exactly:
  the same generic name-extraction helper and the same memoization pattern, returning
  sorted `(name, bible-relpath)` pairs for the GOLEM location class (`bible/locations/`)
  and the GOLEM object class (`bible/objects/`).
- **FR-002**: The `character_presence` unknown-mention rule MUST build its set of "known
  names" from the **union** of the character, setting, location and object rosters —
  each contributing its full declared name and each of its tokens — exactly as the
  character roster already contributes.
- **FR-003**: A proper-noun candidate whose name (or any token) matches any entry in that
  union MUST NOT be reported as an unknown mention. Specifically, the tokens `Real`,
  `Fábrica`, `Paños` of the declared setting "la Real Fábrica de Paños" MUST stop being
  reported.
- **FR-004**: The orphan rule MUST continue to derive **exclusively** from the character
  roster. A declared setting/location/object that is never mentioned MUST NOT produce an
  orphan error or any absence warning.
- **FR-005**: A proper noun that matches **no** entry in any of the four rosters MUST
  still be reported as an unknown mention, with the same message, severity (`warning`),
  collapsing-per-distinct-name behavior, and first-occurrence locator as today.
- **FR-006**: Every existing `error`-level finding across the test suite MUST come out
  byte-for-byte identical (the gate is unchanged; only the `error` severity gates CI).
- **FR-007**: The `not-evaluated` (iteration 040) behavior MUST be unchanged:
  `character_presence` declares itself not-evaluated only when there is no manuscript
  prose **and** the character roster is empty, with an identical reason string.
  Settings/locations/objects do not affect this condition.
- **FR-008**: Severity assignments and the gate semantics (only `error` breaks CI) MUST
  NOT change.
- **FR-009**: The cross-check MUST remain file-based (via the bible-mapping path used by
  the existing setting/character accessors), not graph/SPARQL-driven. The validator MUST
  continue to emit no triples and require no built graph.
- **FR-010**: The frozen GOLEM ontology MUST remain untouched — no new classes, no
  ontology edits (Principle X).
- **FR-011**: Zero functional regression MUST be verified **empirically** by running the
  full test suite. Any oracle that counted a warning for an already-declared
  setting/location/object MUST be corrected downward, **without** editing fixture
  manuscripts or bibles.
- **FR-012**: The `tiny-historical` status oracle's `validation.counts.warning` MUST be
  corrected from `4` to `1` (the three setting-token warnings `Real`/`Fábrica`/`Paños`
  removed; the single `factual_anchor` warning remains), with the fixture manuscript and
  bible untouched and `validation.counts.error` left at `1` (byte-identical) — the same
  shape of oracle correction iteration 041 made (`5 → 4`) and 038 made (`6 → 5`).
- **FR-013**: The DEBT-010 entry MUST be removed from `DEBT.md` (git preserves history).
- **FR-014**: Every changed source file MUST stay within the 500-line limit (Principle IV).

### Out of Scope

- The leading dialogue dash (DEBT-009, iteration 041) — already shipped.
- Creating a separate "setting/object presence" validator — unnecessary; widening the
  cross-check roster suffices.
- Turning the proper-noun heuristic into semantic judgment (issue #1 move 3, demand-pulled).
- The paired leading-quote markers (DEBT-011) — recorded, future iteration.

### Key Entities *(include if feature involves data)*

- **Character roster**: sorted `(name, bible-relpath)` pairs for every bible character —
  the orphan rule's domain and one of the four unknown-mention rosters (existing).
- **Setting roster**: same shape, for every bible setting (existing accessor).
- **Location roster**: same shape, for every bible location under `bible/locations/`
  (new accessor, mirror of the setting one).
- **Object roster**: same shape, for every bible object under `bible/objects/` (new
  accessor, mirror of the setting one).
- **Known-names set**: the union of slugs (full name + tokens) across all four rosters,
  consulted by the unknown-mention rule to suppress declared names.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a project whose bible declares a setting/location/object and whose
  manuscript names it, the count of unknown-mention warnings attributable to that
  declared name's tokens is **0** (today it is one per capitalized token).
- **SC-002**: On `tiny-historical`, `character_presence` emits **0** warnings (today it
  emits 3: `Real`, `Fábrica`, `Paños`); the project-wide `validation.counts.warning`
  reported by status drops from **4** to **1**.
- **SC-003**: The set of `error`-level findings across the full test suite is byte-for-byte
  identical before and after the change (0 added, 0 removed, 0 changed).
- **SC-004**: A proper noun genuinely absent from all four rosters still produces exactly
  **1** unknown-mention warning.
- **SC-005**: The `not-evaluated` reason string for `character_presence` is unchanged
  (string-identical to iteration 040) in the no-prose/no-characters condition.
- **SC-006**: All four CI gates (lint, format, type-check, test suite with ≥80% coverage)
  pass; no fixture manuscript or bible content is edited; `DEBT.md` no longer contains a
  DEBT-010 entry.
- **SC-007**: `character_presence` still emits **0** triples and requires **no** built
  graph (FR-009), the frozen GOLEM ontology closure is byte-unchanged — no class added,
  no `.ttl` edited (FR-010), and every source file changed by this iteration is **≤500**
  lines (FR-014). All three are checkable directly: the validator's `triples` stay `()`,
  `git diff` over `resources/schemas/golem-1.1/` and `golem.ttl` is empty, and `wc -l`
  on each changed file is ≤500.

## Assumptions

- The GOLEM location class is the one backing `bible/locations/` (G13) and the GOLEM
  object class is the one backing `bible/objects/` (G16); both are already mappable
  through the bible-mapping path, exactly as the setting class is.
- "Mirror exactly" means the new location/object accessors reuse the same generic
  name-extraction helper and memoization sentinel pattern as the existing setting
  accessor, adding only the per-class wiring.
- The `tiny-historical` fixture's only setting-token warnings today are `Real`,
  `Fábrica`, `Paños` (empirically confirmed during specification); no other fixture
  pins a warning **count** that includes a declared setting/location/object token
  (`tiny-novel`/`tiny-memoir` assert only `error == 0`, warnings tolerated).
- Slug-based matching (the existing roster mechanism) is the correct comparison basis;
  no new matching algorithm is introduced.

## Dependencies

- Iteration 025 (locations G13 indexed) and 026 (objects G16 indexed) — already merged;
  the location and object concepts are mappable from the bible.
- Iteration 040 (tri-valued result / `not-evaluated`) — the guard this iteration must
  leave intact.
- The single prose seam (iteration 039) — the unknown-mention rule already consumes the
  normalized prose view; unchanged here.
