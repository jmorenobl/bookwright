# Feature Specification: JSON success-envelope cleanup + G6/G3 deferral decision

**Feature Branch**: `027-envelope-cleanup-g6-g3`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "Necesidad: quedan dos cabos del tramo de endurecimiento. (1) El sobre JSON de éxito se single-sourcea en ok_payload() (iteración 020), pero check/focus/graph siguen construyendo el dict {\"status\":\"ok\",...} a mano — deuda de consistencia documentada como \"out of 020's scope\". (2) Dos conceptos huérfanos \"medios\" siguen sin decisión: RelationshipRole (G6) y PsychologicalState (G3); el registro de diferidos (024) los marca \"por decidir\". Hay que resolver ambos cabos para cerrar el tramo con el contrato de paridad limpio."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Success envelopes route through the single source, byte-for-byte (Priority: P1)

The maintainer wants every agent-facing success document in `check`, `focus`, and
`graph` to be produced through the one shared success-envelope helper
(`ok_payload()` + `emit_json`), rather than each command hand-building its own
`{"status": "ok", …}` literal — closing the consistency debt the `_envelope.py`
docstring records as "out of 020's scope". The observable contract for every one
of these commands stays **exactly the same**: the same JSON document, the same
bytes on stdout, the same exit codes. An agent consuming any of these commands
sees no difference whatsoever.

**Why this priority**: This is the mechanical half of the closing iteration and
the one with a hard, machine-checkable guarantee (identical bytes). It removes the
last hand-rolled copies of the success skeleton so the envelope contract has a
single source of truth, finishing what iteration 020 deferred.

**Independent Test**: Capture the exact stdout bytes of `check --json`,
`focus`/`focus set`/`focus clear --json`, and `graph query --json` (and `graph
build --json`) on representative inputs before the change; after routing each
through the shared helper, assert the captured bytes are reproduced
character-for-character, and that exit codes are unchanged.

**Acceptance Scenarios**:

1. **Given** the `focus` show/set/clear commands and `graph query`, **When** their
   success documents are produced via `ok_payload(**fields)` + `emit_json` instead
   of a hand-built `{"status": "ok", …}` dict, **Then** the JSON emitted on stdout
   is byte-identical to the pre-change output for the same inputs.
2. **Given** the `check` command — whose success envelope is `{"ok": <bool>,
   "checks": […]}` (it carries no top-level `status` key by design) — **When** the
   cleanup is applied, **Then** its stdout remains byte-identical: its envelope
   shape is preserved exactly, and only its construction is single-sourced where it
   can be without changing any byte.
3. **Given** a regression test that pins the current stdout of every migrated
   command, **When** the suite runs after the change, **Then** no migrated
   command's output differs from its captured baseline.

---

### User Story 2 - Every deferred concept carries a firm reason and target version (Priority: P1)

The maintainer wants the two remaining "middle" orphan concepts —
`RelationshipRole` (G6) and `PsychologicalState` (G3), which the iteration-024
deferral registry currently stamps `"undecided"` — to receive an explicit,
documented decision. For each concept the outcome is one of: **(a)** it is wired
as a minimal identity-only builder (if that fits without touching the frozen
ontology and without inflating `bible.py`), leaving the deferral registry and
becoming a reachable concept; or **(b)** its deferral is confirmed with a concrete
reason and a firm target version. After this iteration the deferral registry
contains **no** `"undecided"` entries — every remaining entry names a concept with
a firm reason and a concrete target version — and the v0.3.x hardening track
closes.

**Why this priority**: This is the design half of the closing iteration. It is
what lets the ingestion-parity contract (iteration 024) be honest end-to-end: the
"deferred" set must mean "deliberately not yet fed, for a stated reason, by a
stated version", with no placeholder verdicts left.

**Independent Test**: Inspect the deferral registry and the ingestion-parity
test's pinned version mapping after the change: assert no entry's target version
is `"undecided"`; for any concept chosen for wiring, assert it is absent from the
registry and present in the reachable set the parity build observes; for any
concept confirmed deferred, assert it carries a non-empty reason and a concrete
target version. The full parity suite stays green.

**Acceptance Scenarios**:

1. **Given** the iteration-024 deferral registry, **When** the decision is applied,
   **Then** neither `RelationshipRole` nor `PsychologicalState` has target version
   `"undecided"`, and no other entry does either.
2. **Given** a concept decided **deferred**, **When** the registry and the parity
   test's version mapping are read, **Then** that concept has a non-empty reason
   and a concrete target version (e.g. `"v0.4"`), and the ingestion-parity test
   stays green with it still observed as an orphan.
3. **Given** a concept decided **wired**, **When** the parity build runs, **Then**
   that concept's class IRI is observed in the built graph (it is reachable), it is
   removed from the deferral registry, the reachable-set and orphan-set pins are
   updated to match, and the parity test stays green.
4. **Given** the closing of the v0.3.x track, **When** the deferral registry is
   read, **Then** the `"undecided"` literal is gone from the registry contract, and
   each remaining deferred concept (the narrative-structure layer G7/G9/G10 plus
   any of G6/G3 confirmed deferred) names a firm target version.

---

### Edge Cases

- The envelope cleanup must not silently alter key **order** within any success
  document: the shared helper preserves insertion order so the compact JSON
  (`separators=(",", ":")` + trailing newline) is reproduced exactly.
- `check`'s success envelope is intentionally `{"ok": <bool>, "checks": […]}` with
  no top-level `status` key; wrapping it in `ok_payload()` would inject a `status`
  key and change the bytes, so the cleanup must not do that. The per-check result
  dicts (`{"name": …, "status": "ok"|"fail", …}`) are domain sub-objects, not the
  Principle-IX envelope, and are left untouched.
- `graph build --json` already serializes through its report object's `to_json()`
  (not a hand-built `{"status": "ok"}` literal); the cleanup confirms it is already
  single-sourced and leaves its bytes unchanged.
- Error paths (manifest/config/collision faults) already route through
  `BookwrightError.to_json()` / `emit_error` and are out of this iteration's scope;
  only the success documents are touched.
- Wiring G6 or G3 identity-only would produce a node with no link to its mandatory
  cross-ref partner (`RelationshipRole.relationship`, `PsychologicalState.bearer`),
  i.e. a semantically degenerate node with no authoring surface — this is the
  decision input weighed in User Story 2, not a defect to silently ship.

## Requirements *(mandatory)*

### Functional Requirements

#### Success-envelope cleanup

- **FR-001**: The success documents of `focus` (show, set, clear) and `graph query`
  MUST be produced through the shared `ok_payload(**fields)` helper (the single
  place the `{"status": "ok", …}` skeleton lives) plus `emit_json`, replacing every
  hand-built `{"status": "ok", …}` literal in those command modules.
- **FR-002**: The stdout of each migrated command MUST be **byte-identical** to its
  pre-change output for the same inputs — same keys, same values, same key order,
  same compact separators, same trailing newline. No observable output may change.
- **FR-003**: `check`'s success envelope MUST remain byte-identical. Because its
  envelope is `{"ok": <bool>, "checks": […]}` (no top-level `status` key), the
  cleanup MUST NOT introduce a `status` key into it; `check`'s construction is
  single-sourced only insofar as that preserves every byte. The per-check result
  dicts are not the envelope and are left as-is.
- **FR-004**: `graph build`'s success document MUST stay byte-identical; it already
  routes through its report object's serializer rather than a hand-built literal,
  so the cleanup confirms (and does not regress) that path.
- **FR-005**: A regression test MUST pin the current stdout of every command in the
  cleanup's scope (`check`, `focus` show/set/clear, `graph query`, `graph build`)
  and assert byte-identical output after the change, failing if any byte drifts.
- **FR-006**: Exit codes for every migrated command MUST be unchanged across all
  paths (success and the pre-existing fault paths).
- **FR-007**: The cleanup MUST NOT touch any `--json` command outside `check`,
  `focus`, and `graph` (e.g. `init`, `integration`, `validate`, `version`,
  `status`), and MUST NOT alter the error-envelope path.

#### G6/G3 deferral decision

- **FR-008**: For each of `RelationshipRole` (G6) and `PsychologicalState` (G3), the
  iteration MUST record an explicit decision — either **wire** a minimal
  identity-only builder, or **confirm deferral** — and document the rationale.
- **FR-009**: A concept decided **deferred** MUST have its deferral-registry entry
  updated from `"undecided"` to a concrete target version (e.g. `"v0.4"`) with a
  non-empty, specific reason, and MUST remain observed as an orphan by the
  ingestion-parity build.
- **FR-010**: A concept decided **wired** MUST be removed from the deferral
  registry, MUST be observed as reachable (its class IRI present) in the
  parity-fixture graph build, and the parity test's reachable-set and orphan-set
  pins MUST be updated to match — with no change to the frozen ontology and no
  inflation of `bible.py` beyond the additive builder.
- **FR-011**: After the iteration, the deferral registry MUST contain **zero**
  entries whose target version is `"undecided"`; every remaining entry MUST carry a
  firm reason and a concrete target version.
- **FR-012**: The ingestion-parity test's pinned version mapping
  (`EXPECTED_VERSIONS`), reachable-set pin, and orphan-set pin MUST be updated to
  reflect the decision, and the full parity suite MUST stay green.
- **FR-013**: The decision MUST NOT add any class or property to the frozen GOLEM
  ontology (Principle X): both G6 and G3 already exist in `CLASS_IRI` and
  `CONCEPTS` and, if wired, are reused as-is identity-only.
- **FR-014**: The narrative-structure layer concepts (`NarrativeUnit` G9,
  `NarrativeFunction` G10, `NarrativeSequence` G7) MUST keep their existing firm
  deferral to v0.4 unchanged; this iteration only confirms them, it does not wire
  them or alter their entries.

### Key Entities *(include if feature involves data)*

- **Success envelope**: The single JSON document a `--json` command emits on
  stdout. The success skeleton `{"status": "ok", …}` is single-sourced in
  `ok_payload()`; `check`'s `{"ok": <bool>, "checks": […]}` is a deliberate
  variant without a top-level `status` key.
- **Deferral note**: A registry entry (`reason`, `target_version`) for a modelled-
  but-unfed GOLEM concept. `target_version` is one of the concrete versions (e.g.
  `"v0.4"`); the `"undecided"` literal is eliminated by this iteration.
- **RelationshipRole (G6)**: A functional role within a social relationship (friend,
  lover, rival). Modelled with a mandatory `relationship` cross-ref
  (`crm:P67_refers_to`); not identity-only in any useful sense.
- **PsychologicalState (G3)**: A character's mental/stative state. Modelled with a
  mandatory `bearer` cross-ref (`dlp:generically-dependent-on`); not identity-only
  in any useful sense.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every command in the cleanup's scope, the JSON emitted on stdout
  after the change is byte-identical to the captured pre-change baseline for the
  same inputs — verified by a regression test that fails on any single-byte drift.
- **SC-002**: Zero hand-built `{"status": "ok", …}` literals remain in the `focus`
  and `graph` command modules; their success documents are produced via
  `ok_payload()` + `emit_json`.
- **SC-003**: The deferral registry contains zero entries with target version
  `"undecided"`; every remaining entry has a non-empty reason and a concrete target
  version.
- **SC-004**: The ingestion-parity test suite is green, with its reachable-set,
  orphan-set, and version-mapping pins consistent with the G6/G3 decision.
- **SC-005**: All four CI gates (`ruff check`, `ruff format --check`, `mypy
  --strict`, `pytest` at ≥ 80 % coverage) pass, with > 85 % coverage on any new
  code; every pre-existing test passes with unchanged expected output.
- **SC-006**: The v0.3.x hardening track closes: no `"undecided"` verdict and no
  hand-rolled success-envelope literal remain across the touched surface.

## Assumptions

- **Byte-identical wins over uniformity.** Where a command's success document does
  not fit the `{"status": "ok", …}` skeleton (`check`'s `{"ok", "checks"}`, `graph
  build`'s report serializer), the requirement is single-sourcing **without
  changing any byte**, not forcing those documents into the `ok_payload()` shape.
  The prompt names `check`, but its envelope intentionally has no `status` key, so
  `check`'s migration is limited to whatever preserves its exact bytes.
- **Expected G6/G3 outcome is deferral to v0.4.** Both concepts carry a *mandatory*
  cross-ref (`RelationshipRole.relationship`, `PsychologicalState.bearer`) and have
  no `bible/` authoring surface; a bare identity-only node would be semantically
  degenerate, and making them useful requires a roles/states model with attributes
  plus an authoring path — that is v0.4 work. The informed default is therefore to
  **confirm deferral with reason "requires a typed roles/states model with
  attributes and an authoring surface" → v0.4** for both. The wire/defer evaluation
  is finalized in `/speckit-plan` against the "fits without touching the ontology
  and without inflating `bible.py`, and is meaningful" test; this spec's hard
  invariant (no `"undecided"`, parity green) holds under either branch.
- The existing regression-capture approach (golden stdout bytes) is the test
  mechanism for the envelope cleanup; no new framework is introduced.
- The deferral registry and parity test already pin a full concept→version mapping
  (iteration 024); this iteration edits those pins rather than restructuring them.

## Out of Scope

- The narrative-structure layer (G9/G10/G7) and `outline/` ingestion — these stay
  firmly deferred to v0.4; this iteration only confirms their existing entries, it
  does not wire them.
- Any envelope refactor beyond `check`, `focus`, and `graph` — `init`,
  `integration`, `validate`, `version`, and `status` are untouched.
- The error-envelope path (`BookwrightError.to_json()` / `emit_error`) — already
  single-sourced; not in scope.
- Any change to the frozen GOLEM ontology (Principle X) — no new class or property.
- Object/relationship/character cross-refs or attributes beyond what already exists
  — if G6/G3 are wired, it is identity-only with no new ontology.

**Reference**: `bookwright-roadmap.md § 3`; `_envelope.py` (`ok_payload`, the "out
of 020's scope" note); the iteration-024 deferral registry
(`golem/deferrals.py`) and ingestion-parity test
(`tests/golem/test_ingestion_parity.py`); `bookwright-design.md § 4.2` (G6/G3 as
concepts and their URIs). Principle IX (`--json` single JSON document), Principle X
(frozen ontology).
