# Feature Specification: Unify the narrative-unit identifier across `narrative_structure`'s two rules

**Feature Branch**: `049-narrative-unit-identifier`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Unify the unit identifier printed by the two `narrative_structure` rules — the orphan-beat rule prints the slug, the unresolved-role rule prints the human authored name — onto the human name, consistently (DEBT-017)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One species of unit identifier, not two (Priority: P1)

An author runs `bookwright validate` on a project whose narrative outline has both
an orphan beat (a `G9` narrative unit belonging to no `G7` sequence) and a unit
that references a role slug resolving to no character role. Today the two findings
name the *same kind of thing* — a narrative unit — two different ways: the
orphan-beat finding prints the opaque slug
(`narrative unit 'el-recuerdo-de-la-primera-marea' belongs to no narrative
sequence (orphan beat)`), while the unresolved-role finding prints the human
authored name (`narrative unit 'La fechoría en el muelle' references role
'informante' …`). The author sees two "species" of identifier for the same
concept and cannot tell at a glance that both refer to a unit they authored by
name. After this change, both findings name the unit the **same** way — by the
human authored name the author wrote and recognizes — so the report reads as one
consistent surface.

**Why this priority**: This is the entire feature. It is the single observable
delta the iteration ships (DEBT-017): presentation/UX consistency within one
validator, no functional change. Without it there is nothing to deliver.

**Independent Test**: Author a project (or use the existing E2E fixture) that
triggers both rules, run `bookwright validate`, and confirm both messages
identify the unit by its human authored name in an identical format. Fully
testable on its own and delivers the complete value.

**Acceptance Scenarios**:

1. **Given** a project with an orphan `G9` narrative unit authored as
   "El recuerdo de la primera marea", **When** `bookwright validate` runs,
   **Then** the orphan-beat finding names the unit by that human authored name
   (e.g. `narrative unit 'El recuerdo de la primera marea' belongs to no
   narrative sequence (orphan beat)`), not by its slug.
2. **Given** the same project, **When** both the orphan-beat rule and the
   unresolved-role rule fire, **Then** both findings present the unit identifier
   in the identical chosen format (human name, plus a trace suffix if the format
   includes one — applied the same way in both rules).
3. **Given** a project with an orphan unit, **When** validate runs, **Then** the
   finding's `relpath:line` locator, severity, and the gate/exit-code outcome are
   exactly what they were before this change (only the printed identifier
   differs).

---

### Edge Cases

- **A unit carries no `rdfs:label` in the derived graph** (should not occur —
  iteration 035 guarantees every `G9` unit emits `(uri, rdfs:label, name)`): the
  orphan-beat rule falls back to the slug rather than emitting an empty or broken
  identifier. This is a defensive floor, not an expected path.
- **A unit name that happens to equal its slug** (e.g. an author who wrote a
  lowercase-hyphenated title): both rules still print that string identically;
  there is no observable change for that unit, which is correct.
- **The derived `graph.ttl` is stale or unbuilt**: out of scope for the new
  behavior — the orphan rule already depends on a built graph to detect orphans
  at all, so label resolution rides the same already-loaded graph.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both `narrative_structure` rules — orphan-beat (`_orphan_beats`)
  and unresolved-role (`_unresolved_roles`) — MUST identify a narrative unit by
  the **same** identifier: the human authored name (the `name` the author wrote).
- **FR-002**: The orphan-beat rule MUST change from printing the unit slug to
  printing the unit's human authored name. The unresolved-role rule already
  prints the human name and its behavior MUST remain the human name.
- **FR-003**: The orphan-beat rule MUST resolve the human name **from the derived
  graph** — the `G9` unit already emits `(uri, rdfs:label, name)` (iteration 035),
  so the name is SPARQL-queryable. It MUST NOT reconstruct the name from the slug
  and MUST NOT cross-reference the outline to obtain it.
- **FR-004**: If (defensively) a unit has no `rdfs:label` in the graph, the
  orphan-beat rule MUST fall back to the slug so a finding is still emitted.
- **FR-005**: The two rules MUST format the narrative-unit identifier through a
  **single shared point** — one helper that takes the unit's `(name, slug)` and
  returns the printed identifier, called by *both* `_orphan_beats` and
  `_unresolved_roles`. Two independently-built strings that merely *happen* to
  match are forbidden: consistency MUST be structural (divergence impossible by
  construction), not asserted. This mirrors the iteration-048 precedent
  (`anchor_handle` shared between `factual_anchor` and `status` so the surfaces
  cannot drift, DEBT-015). The exact rendered format (human name alone, or human
  name plus a parenthetical slug for URI traceability) is a `/speckit-plan`
  decision, but because both rules render through the one helper, whatever format
  is chosen — including any trace suffix — is applied identically by construction.
- **FR-006**: Only the **printed identifier** changes. The locator
  (`resolve_source` / `relpath:line`), the severity, the gate behavior, and
  **what each rule detects** MUST NOT change.
- **FR-007**: The change MUST NOT add or modify any class or property in the
  frozen ontology (Principle X), and MUST NOT introduce any new dependency
  (Constitution II). Each changed source file MUST stay ≤ 500 lines.
- **FR-008**: Affected oracles — any `expected-*` fixture artifact or test that
  asserts the orphan-beat message with the slug — MUST be updated to the human
  name (plus trace suffix if the chosen format includes one), verified
  **empirically** with `uv run pytest`. Outline fixtures (the authored input
  cards) MUST NOT be edited to accommodate the change.
- **FR-009**: The DEBT-017 entry MUST be removed from `DEBT.md` (git preserves the
  history); the track-B index line and any narrative referencing DEBT-017 as open
  MUST be reconciled to reflect closure.

### Key Entities *(include if feature involves data)*

- **`G9` narrative unit**: the entity both rules report on. Carries an authored
  human `name` (emitted to the derived graph as `rdfs:label`), a stable slug
  (the URI tail), and `relpath:line` provenance (via the existing `E13` path).
  The feature concerns only *which* of name/slug is printed, not the entity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every finding emitted by either `narrative_structure` rule, the
  narrative-unit identifier is the human authored name (or the agreed
  name-plus-trace format), in a format identical between the two rules — verified
  by running `bookwright validate` on a project that triggers both rules.
- **SC-002**: 0 findings from `narrative_structure` identify a unit by a slug-only
  identifier when that unit has a label (the prior orphan-beat behavior is fully
  gone).
- **SC-003**: Finding count, severity, `relpath:line` locator, and the
  gate/exit-code outcome are unchanged on every existing fixture — only the
  printed identifier text differs. Verified empirically with `uv run pytest`.
- **SC-004**: The four CI gates (`ruff check`, `ruff format --check`,
  `mypy --strict`, `pytest` with ≥80% coverage) are green.
- **SC-005**: `DEBT.md` no longer contains a DEBT-017 entry, and no plain-text
  record still describes DEBT-017 as open.
- **SC-006**: Both rules render the unit identifier through one shared formatting
  point (FR-005): no second, independent identifier-formatting expression exists in
  `narrative_structure.py` — verified by the diff (one helper, two call sites).

## Assumptions

- The exact printed format — human name alone (e.g. `'El recuerdo de la primera
  marea'`) versus human name with a parenthetical slug for URI traceability
  (e.g. `'El recuerdo de la primera marea' (el-recuerdo-de-la-primera-marea)`) —
  is deferred to `/speckit-plan`. The spec mandates only that whatever format is
  chosen is applied **consistently** across both rules.
- Iteration 035's guarantee holds: every `G9_Narrative_Unit` emits a single
  `(uri, rdfs:label, name)` triple, so the human name is always SPARQL-queryable
  from the derived graph in the normal path; the slug fallback (FR-004) is a
  defensive floor for an impossible-by-construction missing-label case.
- The unresolved-role rule's current human-name identifier (sourced from
  `ref.entity`) is the canonical form to converge on; the orphan-beat rule is the
  only one whose *resolution* changes (slug → graph `rdfs:label`). Both still feed
  the one shared formatting helper (FR-005). The two name *sources* differ by
  necessity — the orphan rule reads `rdfs:label` from the graph (it has no
  `UnresolvedReference`), the unresolved rule already holds `ref.entity` — but the
  values are byte-identical by construction: iteration 035 emits
  `(uri, rdfs:label, name)` where `name` is the same authored `NarrativeUnit.name`
  that `_unit_uri_index` keys on to produce `ref.entity`. So "the same identifier"
  (FR-001) is true in value, not merely in label, and is testable as such.
- A repo-wide sweep of the debt class (a single validator naming one entity-kind
  two different ways across its rules, doctrine §4) confirms `narrative_structure`
  is the **sole** remaining instance: `temporal` and `factual_anchor` were unified
  in iteration 048 (DEBT-015, closed), and the prose validators each name their
  entity one consistent way. No other instance is left unswept.
- This is a single-validator presentation polish (issue #1 track B, deterministic
  polish). It does not touch `factual_anchor`/`temporal` locators (DEBT-015 /
  iteration 048, already closed), the move-3 semantic-judgment work, or any
  message normalization outside `narrative_structure`.
