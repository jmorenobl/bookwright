# Feature Specification: Narrative-structure continuity validator

**Feature Branch**: `031-narrative-structure-validator`

**Created**: 2026-06-20

**Status**: Draft

**Input**: User description: "Necesidad: la capa estructural narrativa ya está en el
grafo (unidades, funciones, secuencias, tipado Propp/Greimas), pero nada la
consume todavía: su valor es ser citable por SPARQL para detectar incoherencias.
Queremos añadir un validador de continuidad estructural narrativa que aproveche la
nueva capa, demostrando que es citable y útil al autor. Incoherencias candidatas
(afinar en clarify): (a) beat huérfano; (b) hueco/duplicado en el `order` de una
secuencia; (c) `roles:` con rol no resuelto; (d) secuencia vacía. El validador
respeta el contrato de los demás (runner.py, sobre `--json`, activable/desactivable)
y un proyecto sin `outline/units/` no produce findings ni regresa nada. Fuera de
scope: reglas con inferencia LLM; cambiar validadores existentes; clases/propiedades
nuevas (Principio X)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The author is told which beats are not placed in any plot line (Priority: P1)

An author has broken their plot into beats (`outline/units/*.md`, iteration 028)
and grouped some of them into plot lines via the `sequence:`/`order:` keys that
assemble narrative sequences (iteration 029). Some beats, though, were written but
never joined to any sequence — they sit in the outline as orphans the author has
lost track of. When the author runs validation, the new structural-continuity
validator reports each orphan beat as a finding that names the unit and cites the
unit card's location (`file:line`), so the author can either fold the beat into a
plot line or confirm it is intentionally standalone.

**Why this priority**: This is the headline payoff of the whole v0.4 layer — it is
the first thing that *consumes* the narrative structure that iterations 028–030
put into the graph, and it does so exactly as the layer was designed to be used:
by **querying the graph with SPARQL**. The orphan-beat rule is the one candidate
incoherence that is wholly answerable from the derived graph (a `G9` unit with no
incoming `dlp:proper-part` from any `G7`), so it is both the clearest authorial
signal and the cleanest demonstration that the structural layer is citable. It is
independently shippable and is the MVP.

**Independent Test**: Build the graph for a project that has at least one unit card
joined to a sequence and at least one unit card naming no sequence; run validation;
confirm exactly the unsequenced unit is reported as a finding, with its `file:line`
locator, and the sequenced unit is not.

**Acceptance Scenarios**:

1. **Given** a project with a unit card that declares no `sequence:` (and that no
   other card pulls into a sequence), **When** validation runs, **Then** the
   validator emits one finding naming that narrative unit and citing the unit
   card's `file:line`.
2. **Given** a project where every unit card belongs to some sequence, **When**
   validation runs, **Then** the structural-continuity validator emits no finding.
3. **Given** a project with no `outline/units/` directory at all, **When**
   validation runs, **Then** the validator emits no finding and contributes
   nothing to the report (no error, no `errors[]` entry).

---

### User Story 2 - The author is told which beat references a role that does not exist (Priority: P2)

An author writing a unit card lists the actantial roles in play on that beat
(`roles:`), naming character-scoped role nodes by slug. If a name matches no role
that any character actually plays, ingestion already drops the reference silently
(a soft-miss, no graph edge). Today the author has no surfaced signal that the beat
points at a non-existent role. The structural-continuity validator re-surfaces that
soft-miss as a continuity finding: it names the offending beat and the unresolved
role name and cites the unit card's `file:line`, so a typo or a deleted character
no longer silently severs the beat from its actantial structure.

**Why this priority**: It turns an already-detected-but-invisible ingestion
soft-miss (the prompt's "ya soft-miss en ingesta, ahora reportado como continuity
finding") into an author-facing finding, closing a real gap. It is genuinely
independent of US1 (a project can have orphan beats but no bad role refs, or vice
versa). It is P2 rather than P1 because, unlike the orphan-beat rule, the **graph**
carries no edge for an unresolved reference — the finding is derived from the
outline ingestion's already-emitted `UnresolvedReference` records, not by querying
the cache — so it is a smaller, more ingestion-coupled demonstration of "the layer
is citable" than US1.

**Independent Test**: Build a project with one unit card whose `roles:` names a slug
that no character plays and another card whose `roles:` all resolve; run validation;
confirm exactly the bad reference is reported with the beat name, the unresolved
role name, and the card's `file:line`, and the good card is not.

**Acceptance Scenarios**:

1. **Given** a unit card whose `roles:` includes a name that resolves to no
   character role, **When** validation runs, **Then** the validator emits one
   finding naming the beat and the unresolved role and citing the card's
   `file:line`.
2. **Given** a unit card whose every `roles:` entry resolves to an existing
   character role, **When** validation runs, **Then** the validator emits no
   finding for that card.
3. **Given** a project with no `outline/units/` directory, **When** validation
   runs, **Then** no unresolved-role finding is produced.

---

## Clarifications

### Session 2026-06-20

- Q: Should the validator include candidate rule (b) — a gap or duplicate in a
  sequence's member `order:` values? → A: **No — excluded from this iteration.**
  The per-card `order:` is consumed when the sequence is assembled and is **not**
  serialized to the graph (member order is a tuple, no queryable ordinal — see
  `io/outline.py` `_member_sort_key`), so it is not SPARQL-citable; and a *gap* in
  `order:` is a legitimate sparse-numbering convention (e.g. 10, 20, 30 to leave
  insertion room), not an incoherence, so the rule as posed would false-positive on
  ordinary authoring. Detecting only a *duplicate* `order:` is a narrower, separable
  candidate. The iteration's observable delta — "the structural layer is now
  consumed by a validator" — is fully delivered by US1 (orphan beat, SPARQL) plus
  US2 (unresolved role). Recorded under Out of Scope as an unselected candidate
  feature rule, **not** deferred debt (it is not a dirty edge of work this iteration
  touches). Drives FR-007.
- Q: What default severity do the validator's findings carry? → A: **`warning`**,
  matching the precedent every LLM-free heuristic structural check sets
  (`setting_continuity` is `Severity.warning`, never gates CI): the findings are
  advisory nudges, not build failures. Drives FR-013.
- Q: Where does the unresolved-role finding (US2) get its data — does the graph
  record the soft-miss? → A: The **graph** records no edge for an unresolved role,
  but the outline ingestion **already** emits a structured `UnresolvedReference`
  record for it (`io/outline.py` `_resolve_roles` → `MapResult.unresolved_references`,
  carrying the offending unit name and the unresolved role name). The validator MUST
  reuse those existing records rather than re-implement role resolution, so there is
  a single source of truth for "does this role resolve". The finding's `file:line`
  locator is still recovered through the existing `E13`→source path on the offending
  unit (FR-004). Drives FR-006.
- Q: *How* does the validator reach those `UnresolvedReference` records (FR-006)? The
  validator seam passes only the `ValidationContext` and the graph `Indexer`, and
  `ValidationContext.bible()` runs `map_bible` **only** — its `unresolved_references`
  never contains the outline pass's role misses, which today only `build_project_graph`
  (map_bible → `map_outline` on one `MapResult`) produces. → A: Add a **cached
  `outline()` accessor** to `ValidationContext`, mirroring the existing `bible()`
  accessor, that runs the **same** `map_bible`→`map_outline` pipeline the graph build
  uses (`commands/_graph.py` `build_project_graph`; `map_outline` requires the
  character pass's `roles_index`, so it cannot run standalone) and returns that
  combined `MapResult`. The validator reads `outline().unresolved_references`. This
  reuses the established read-once-per-run accessor pattern (no new mechanism), keeps
  one source of truth for role resolution, re-reads no cards by hand (FR-006), adds no
  class/property (Principle X) and writes nothing (FR-008). Drives FR-006 and the
  Dependencies note.
- Q: What stable `name` does the validator carry — the `[validators]` enable/disable
  key the US3 acceptance and SC-006 assert against? → A: **`narrative_structure`** —
  snake_case, named for what it checks like every existing built-in
  (`setting_continuity`, `temporal`, `focalization`), and echoing the v0.4
  narrative-structure layer it consumes. Fixing the name now removes test/config
  churn and gives the disable-by-name tests a concrete target. Drives FR-001/FR-010
  and Key Entities.

### User Story 3 - The author can turn the validator off like any other (Priority: P3)

The new validator behaves like every existing continuity check: it is discovered by
name, runs through the same runner, emits findings through the same `--json`
envelope, and can be enabled/disabled via the project's existing `[validators]`
configuration. An author who does not want structural-continuity checks disables it
by name and it stops contributing findings, exactly as `temporal` or
`setting_continuity` would.

**Why this priority**: Contract conformance is what makes the validator a
first-class member of the suite rather than a bolt-on. It is P3 because it is a
property of the integration, not a new authorial capability — but it is a hard
requirement, not optional polish.

**Independent Test**: List the active validators for a default project and confirm
the new validator appears; add its name to the `[validators] disabled` list and
confirm it no longer runs and produces no findings; confirm its findings serialize
through the existing `--json` report shape with no new top-level keys.

**Acceptance Scenarios**:

1. **Given** a default project, **When** the active validators are resolved,
   **Then** the structural-continuity validator is among them.
2. **Given** the validator's name in `[validators] disabled`, **When** validation
   runs, **Then** the validator does not run and emits no findings.
3. **Given** any finding the validator produces, **When** the report is serialized
   with `--json`, **Then** the finding appears in the existing findings array with
   the existing finding shape (validator name, severity, message, source, triples)
   and the envelope gains no new structure.

---

### Edge Cases

- **No structural layer (the default / baseline)**: a project without
  `outline/units/` produces zero findings from this validator and changes nothing
  else in the report — same output as before this feature (FR-009).
- **Empty sequence**: a narrative sequence with no member units **cannot occur**
  from ingestion — sequence assembly only mints a sequence that has at least one
  member — so the candidate rule (d) "secuencia vacía" has no reachable input and
  is intentionally not implemented. Reporting it would require fabricating an input
  the system never produces. (See Out of Scope.)
- **Order gap / duplicate** (candidate rule (b)): the per-card `order:` value is
  consumed when the sequence is assembled and is **not** serialized into the graph
  (RDF carries no ordinal; member order is a tuple, not a queryable number), so a
  gap or duplicate in `order:` is not visible to a SPARQL query over the graph.
  **Excluded from this iteration** (see Clarifications / Out of Scope): a *gap* is a
  legitimate sparse-numbering convention rather than an incoherence, so the rule as
  posed would false-positive; the validator emits no order-related finding (FR-007).
- **A unit both orphaned and bad-role-referencing**: each rule fires independently;
  the unit yields one orphan finding and one unresolved-role finding (deduped only
  if byte-identical, which they are not).
- **A validator-internal failure** (e.g. a malformed graph): isolated by the
  runner as a `ValidatorError(phase="run")` exactly as for any other validator;
  the rest of the suite still runs (existing contract, not changed here).
- **Severity of a structural finding**: a heuristic, LLM-free structural finding is
  advisory (it never blocks CI), consistent with `setting_continuity`'s `warning`
  default — confirmed in Clarifications and FR-013.

## Requirements *(mandatory)*

> The functional requirements below implement the **selected rule subset**: US1
> (orphan beat, SPARQL over the graph) as the firm core, plus US2 (unresolved role,
> re-surfaced from ingestion's `UnresolvedReference` records). Candidate rule (b)
> order-gap/duplicate and rule (d) empty-sequence are both excluded — (b) because
> `order:` is not graph-serialized and a gap is legitimate sparse numbering rather
> than an incoherence, (d) because a memberless sequence is structurally unreachable
> (see Clarifications, Edge Cases, and Out of Scope).

### Functional Requirements

- **FR-001**: A new continuity validator named **`narrative_structure`** (the stable
  `[validators]` enable/disable key, snake_case like the other built-ins) MUST be
  added that examines the narrative structural layer (narrative units, sequences,
  functions, roles) and reports structural incoherencies as findings, joining the
  existing validator suite.
- **FR-002**: The validator MUST be discovered and run through the **same**
  mechanism as the existing built-in validators (no hand-registration, no new
  runner): it MUST appear in the resolved active set for a default project and run
  via the existing runner with per-validator isolation.
- **FR-003**: The validator MUST emit each incoherency as a finding in the
  **existing** finding shape (validator name, severity, message, optional
  `source` locator, triples), serializable through the existing `--json` report
  envelope (Principle IX) with **no** new top-level report structure.
- **FR-004**: When a finding pertains to a specific authored location, the finding
  MUST carry a `file:line` locator pointing at the originating unit card, recovered
  through the **existing** structural-provenance path (the `E13` assertion → source
  locator already used by other validators), never a bare or invented path.
- **FR-005** *(Rule a — orphan beat, firm core)*: The validator MUST report every
  narrative unit that is a member of **no** narrative sequence, determined by a
  SPARQL query over the graph (a `G9` unit with no incoming `dlp:proper-part`
  from any `G7`). Each such unit yields exactly one finding naming the unit and
  citing its unit-card locator.
- **FR-006** *(Rule c — unresolved role)*: The validator MUST report every unit
  card whose `roles:` list references a role slug that resolves to no
  character-scoped role node. It MUST do so by **reusing** the structured
  `UnresolvedReference` records the outline ingestion already emits
  (`io/outline.py` `_resolve_roles` → `MapResult.unresolved_references`) — it MUST
  NOT re-implement role resolution, so "does this role resolve" has one source of
  truth. It MUST reach those records through a **cached `outline()` accessor on
  `ValidationContext`** (mirroring the existing `bible()` accessor) that runs the
  same `map_bible`→`map_outline` pipeline the graph build uses
  (`build_project_graph`) — sans the optional Propp/Greimas typing args, which add
  only `crm:P2_has_type` triples and do **not** affect `unresolved_references`
  (research D5); the validator MUST NOT re-parse cards or build its own
  mapping. Each unresolved reference yields one finding naming the beat and the
  unresolved role name and citing the unit card's locator (recovered via the
  FR-004 path on the offending unit).
- **FR-007** *(Rule b — order gap/duplicate, excluded)*: The validator MUST NOT
  emit any order-coherence finding. The per-card `order:` is consumed at sequence
  assembly and is not serialized to the graph, and a gap in `order:` is a legitimate
  sparse-numbering convention rather than an incoherence; a sequence whose members
  have a gap or a duplicate in their `order:` values therefore produces no finding
  (see Clarifications / Out of Scope). A test MUST assert that such a sequence
  yields no order-related finding.
- **FR-008**: The validator MUST be deterministic and read-only: the same source
  produces the same findings on every run (byte-stable after the runner's sort),
  and it MUST NOT write to disk or mutate the graph (existing validator contract).
- **FR-009**: A project with no narrative structural layer (no `outline/units/`)
  MUST produce **zero** findings from this validator and MUST NOT add anything to
  the report — no regression to the pre-feature output for such projects.
- **FR-010**: The validator MUST be enable/disable-able by its name
  (`narrative_structure`) through the existing `[validators]` configuration, exactly
  like the other built-ins; when disabled it does not run and emits nothing.
- **FR-011**: The validator MUST NOT change the behavior, findings, names, or
  severities of any existing validator.
- **FR-012**: The validator MUST NOT add any class or property to the frozen GOLEM
  ontology (Principle X); it only queries/reads the already-modelled structural
  layer.
- **FR-013**: The validator MUST be purely deterministic/SPARQL/heuristic with **no**
  LLM inference; it carries a fixed default severity consistent with the other
  heuristic structural checks: it MUST default to `warning` — advisory, never
  gating CI — matching `setting_continuity` (`Severity.warning`).

### Key Entities *(include if feature involves data)*

- **Structural-continuity validator**: the new built-in continuity check. Has the
  stable name `narrative_structure` (used in `[validators]` enable/disable config)
  and a default severity (`warning`); consumes the narrative structural layer and
  produces findings.
- **Orphan-beat finding**: a finding stating that a named narrative unit belongs to
  no sequence, located at the unit card.
- **Unresolved-role finding**: a finding stating that a named beat references a role
  that resolves to nothing, located at the unit card.
- **Narrative structural layer** *(existing, not introduced here)*: the
  units (`G9`), functions (`G10`), roles (`G11`), and sequences (`G7`) with their
  `crm:P67_refers_to` / `dlp:proper-part` edges and `E13` provenance — read, not
  redefined, by this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a project with N orphan beats (units in no sequence), the
  validator reports exactly N orphan-beat findings — 100% of orphans flagged, 0%
  of sequenced units flagged.
- **SC-002**: In a project with M unresolved `roles:` references, the validator
  reports exactly M unresolved-role findings, each carrying the beat name, the
  unresolved role name, and the unit card's `file:line`.
- **SC-003**: Every finding the validator produces appears in the existing
  `--json` findings array with the existing finding shape and adds no new key to
  the envelope.
- **SC-004**: A project without `outline/units/` produces zero findings from this
  validator and a report otherwise identical to the pre-feature output.
- **SC-005**: Repeated validation runs over the same source produce an identical
  set of findings every time (byte-for-byte stable after the runner's sort).
- **SC-006**: Disabling the validator by name in `[validators]` removes all of its
  findings and leaves every other validator's findings unchanged.
- **SC-007**: The frozen ontology's class closure is unchanged by this feature (no
  class or property added to `golem.ttl`).

## Assumptions

- **Graph citability is the design intent, but not every candidate rule is in the
  graph**: the orphan-beat rule (FR-005) is answered purely by SPARQL over the
  derived graph and is the clean demonstration of "the structural layer is
  citable". The unresolved-role rule (FR-006) cannot be answered from the graph —
  the graph carries **no** edge for an unresolved reference — but ingestion already
  records each one as a structured `UnresolvedReference` in the outline `MapResult`,
  so the validator reuses those records rather than re-resolving roles (and rather
  than re-parsing cards by hand). This split is deliberate and is what makes US1 the
  firmer P1.
- **Rule subset (selected)**: ship US1 (orphan beat) + US2 (unresolved role);
  exclude rule (d) empty-sequence as structurally unreachable and rule (b)
  order-gap/duplicate as both non-citable (the graph does not serialize `order:`)
  and ill-posed (a gap is legitimate sparse numbering, not an incoherence). The FRs
  are written against this final subset, not a pending default.
- **Empty sequence is excluded on technical grounds, not preference**: sequence
  assembly never mints a memberless sequence, so candidate rule (d) has no
  reachable input; implementing it would mean validating against a state the system
  cannot produce. Recorded as Out of Scope, not as deferred debt.
- **Severity**: structural-continuity findings are advisory (`warning`-level,
  never gating CI), matching the other LLM-free heuristic checks
  (`setting_continuity`). The author treats them as nudges, not build failures.
- **Locator provenance**: findings reuse the existing `E13`-assertion → source
  locator resolution that other graph-querying validators already use, so the
  `file:line` points at the same unit card the entity's identity was provenanced
  from (Principle I — plain-text source of truth).
- **Configuration surface**: the validator is selected through the existing
  `[validators]` block (enabled/disabled/custom lists); this feature introduces no
  new configuration mechanism.
- **References**: `bookwright-design.md § 4.2` (Narrative module) and the
  validation section; the existing validators in `validation/validators/` and their
  SPARQL/graph helpers in `validation/queries.py` are the precedent reused as-is.

## Out of Scope

- **Rule (b) order gap/duplicate**: not implemented — `order:` is consumed at
  sequence assembly and not serialized to the graph (so it is not SPARQL-citable),
  and a *gap* in `order:` is a legitimate sparse-numbering convention rather than an
  incoherence (the rule as posed would false-positive). Detecting only a *duplicate*
  `order:` is a narrower, separable candidate. This is an **unselected candidate
  feature rule recorded in plain text here**, not deferred debt — no `DEBT.md` entry,
  because the iteration does not touch and leave a dirty edge of this work; should
  demand for a duplicate-only check arise, it is its own future iteration.
- **Rule (d) empty sequence**: not implemented — a memberless sequence is never
  produced by ingestion, so there is no authorial input to validate. Not deferred
  debt; structurally unreachable.
- **Rules requiring LLM inference**: this validator is deterministic
  SPARQL/heuristic only; any semantic/judgement rule belongs elsewhere.
- **Changing existing validators**: their behavior, names, severities, and findings
  are untouched.
- **New ontology classes/properties** (Principle X): the validator only reads the
  already-modelled `G7/G9/G10/G11` layer; it adds nothing to `golem.ttl`.
- **Serializing `order:` into the graph**: this feature does not change ingestion to
  persist ordinals; since order coherence (rule b) is out of scope, no card
  re-reading for raw `order:` values is introduced either.
- **Surfacing the typing (Propp/Greimas) as a validation rule**: iteration 030
  produces the typing; validating *against* type coverage (e.g. "this Propp project
  has a beat with no recognized function") is not part of this iteration's selected
  rule subset.

## Dependencies

- The narrative-structure ingestion of iterations 028 (units `G9` / functions
  `G10`), 029 (sequences `G7`), and 030 (Propp/Greimas typing) is on `main`; the
  structural layer already enters the graph. This feature is the first consumer of
  it.
- The existing validation subsystem (`validation/runner.py`, `registry.py`,
  `base.py`, `queries.py`, `validators/*`) provides the validator seam, discovery,
  runner isolation, `--json` envelope, and the `E13`→locator provenance helper
  (`queries.resolve_source`), all reused unchanged. US2 additionally requires a new
  cached **`ValidationContext.outline()` accessor** (sibling of the existing
  `bible()`), running the same `map_bible`→`map_outline` pipeline as
  `build_project_graph` (without the optional Propp/Greimas typing args, which do
  not affect `unresolved_references` — research D5), so the validator reads outline
  ingestion's
  `unresolved_references` without re-resolving roles — the only addition to the
  reused subsystem (see Clarifications, FR-006).
- Reference: `bookwright-design.md § 4.2` (Narrative module) and the validation
  section; Constitution Principle I (plain-text source of truth), Principle IX
  (`--json`), Principle X (frozen ontology).
