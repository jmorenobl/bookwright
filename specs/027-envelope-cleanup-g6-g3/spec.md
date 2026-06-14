# Feature Specification: JSON success-envelope cleanup + G6/G3 deferral decision

**Feature Branch**: `027-envelope-cleanup-g6-g3`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "Necesidad: quedan dos cabos del tramo de endurecimiento. (1) El sobre JSON de éxito se single-sourcea en ok_payload() (iteración 020), pero check/focus/graph siguen construyendo el dict {\"status\":\"ok\",...} a mano — deuda de consistencia documentada como \"out of 020's scope\". (2) Dos conceptos huérfanos \"medios\" siguen sin decisión: RelationshipRole (G6) y PsychologicalState (G3); el registro de diferidos (024) los marca \"por decidir\". Hay que resolver ambos cabos para cerrar el tramo con el contrato de paridad limpio."

## Clarifications

### Session 2026-06-14

- Q: Iteration 025 reused the `UnresolvedParticipant` report type for an
  unresolvable location `setting:` and recorded across its spec/plan/research/tasks
  that "the neutral rename is deferred to iteration 027". Should this iteration
  include that rename? → A: Yes — add it as a third work item (User Story 3): the
  type, its public `--json` key, and the human stderr text all become neutral
  (`UnresolvedReference` / `unresolved_references` / "unresolved reference(s)").
- Q: Must the rename change the public `--json` key `unresolved_participants` of
  `graph build`, or only the internal Python symbols? → A: Full rename (class +
  `--json` key + stderr prose) — the zero-tech-debt choice; a class-only rename
  would leave a permanent model↔wire mismatch (type says `Reference`, key says
  `participants`). This deliberately changes the bytes of `graph build`'s one
  renamed key, so FR-004's byte-identical guarantee is relaxed for that key only
  (new pinned baseline); every other byte — key order, position, separators,
  trailing newline — stays identical, and no other command's bytes change.

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

### User Story 3 - The unresolved-reference warning is named for what it is (Priority: P2)

The `graph build` report's soft-warning type `UnresolvedParticipant` was, since
iteration 025, reused to surface *any* unresolved name reference — including a
location's unresolvable `setting:`, which is not a "participant". Iteration 025
recorded the neutral rename as explicitly deferred to this iteration. The maintainer
wants the type, its public `--json` key, and the human stderr summary all renamed to
a neutral `UnresolvedReference` / `unresolved_references` / "unresolved reference(s)",
so the model, the wire contract, and the prose describe the same general concept —
**eliminating** the model↔wire naming mismatch rather than relocating it.

**Why this priority**: It is the smallest tail of the closing patch and the one that
*deliberately* changes an observable byte (the renamed JSON key), so it is segregated
from User Story 1's byte-identical guarantee. Closing it fulfils the explicit
025→027 deferral and leaves zero naming debt behind the v0.3.x track.

**Independent Test**: Build the graph over a fixture that produces an unresolved
`setting:` (a location) and an unmatched `participants:` reference; assert the
`--json` envelope carries the key `unresolved_references` (not
`unresolved_participants`) in the same position, each item keeps its `{path, entity,
name}` shape, the stderr summary reads "unresolved reference(s)", and no symbol named
`UnresolvedParticipant` remains anywhere in `src/`.

**Acceptance Scenarios**:

1. **Given** a `graph build --json` over a build with an unresolved `setting:` and/or
   an unmatched `participants:` reference, **When** the report serializes, **Then**
   the envelope key is `unresolved_references` and the type is `UnresolvedReference`,
   with the `{path, entity, name}` item shape and the key's position unchanged.
2. **Given** FR-004's byte-identical guarantee for `graph build`, **When** the rename
   lands, **Then** that guarantee is relaxed for the renamed key only: a new pinned
   baseline replaces the old, and every other byte (key order, separators, trailing
   newline, all other field values) is unchanged.
3. **Given** a build with ≥ 1 unresolved reference, **When** the human summary prints
   to stderr, **Then** it reads "N unresolved reference(s)" (no "participant").
4. **Given** a search of `src/` and `docs/` after the iteration, **When** it runs,
   **Then** no `UnresolvedParticipant` identifier and no `unresolved_participants`
   key/attribute remains, and `docs/commands/graph-build.md` names the new key.

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
  (not a hand-built `{"status": "ok"}` literal); the success-envelope cleanup
  confirms it is already single-sourced. Its bytes change in exactly one place — the
  `unresolved_participants` → `unresolved_references` key rename (User Story 3,
  FR-016) — which keeps the key's position and every other byte intact.
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
- **FR-004**: `graph build`'s success document MUST stay byte-identical **except for
  the single key renamed by FR-016** (`unresolved_participants` →
  `unresolved_references`): it already routes through its report object's serializer
  rather than a hand-built literal, so the success-envelope cleanup confirms (and
  does not regress) that path. The rename changes only that key's string — its
  position, the surrounding key order, the compact separators, and the trailing
  newline are all preserved — and a new golden baseline replaces the old.
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

#### Unresolved-reference rename

- **FR-015**: The `graph build` report type `UnresolvedParticipant` (`io/report.py`)
  MUST be renamed to `UnresolvedReference`, with its `{path, entity, name}` fields
  unchanged and its docstring generalized to cover *any* unresolved name reference
  (an unmatched `participants:` member **or** an unresolvable `setting:`, the reuse
  introduced in iteration 025) — closing the rename iteration 025 explicitly deferred
  to this one.
- **FR-016**: The `graph build --json` envelope key `unresolved_participants` MUST be
  renamed to `unresolved_references`; the per-item shape (`path`, `entity`, `name`)
  and the key's position in the envelope are unchanged. This is a deliberate,
  documented public-contract change (recorded in the CHANGELOG).
- **FR-017**: FR-004's byte-identical guarantee for `graph build` is relaxed
  **solely** for the FR-016 key rename: a new golden baseline replaces the old, and
  every other byte of the envelope (key order, separators, trailing newline, all
  other field values) stays identical. No other command's bytes change.
- **FR-018**: The human stderr summary in `graph build` MUST read "N unresolved
  reference(s)" (replacing "N unresolved participant reference(s)" in
  `commands/graph/build.py`); stderr prose is not the `--json` envelope and is not
  byte-pinned.
- **FR-019**: After the rename, no identifier `UnresolvedParticipant` and no
  key/attribute `unresolved_participants` may remain in `src/`, and
  `docs/commands/graph-build.md` MUST name the `unresolved_references` key. The
  `{path, entity, name}` contract and the soft-warning semantics (it never changes
  the exit code) are preserved.

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
- **Unresolved reference** (formerly `UnresolvedParticipant`): the `graph build`
  soft-warning that a name (a `participants:` member or a location's `setting:`)
  matched no built entity; the owning node is still built and the exit code is
  unchanged. Renamed to `UnresolvedReference` with the `--json` key
  `unresolved_references`; its `{path, entity, name}` shape is unchanged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every command in the cleanup's scope, the JSON emitted on stdout
  after the change is byte-identical to the captured pre-change baseline for the
  same inputs — verified by a regression test that fails on any single-byte drift —
  with the **sole** exception of `graph build`'s `unresolved_references` key (FR-016),
  whose new baseline is pinned in place of the old `unresolved_participants` one.
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
- **SC-006**: The v0.3.x hardening track closes: no `"undecided"` verdict, no
  hand-rolled success-envelope literal, and no `UnresolvedParticipant` misnomer
  remain across the touched surface.
- **SC-007**: No symbol `UnresolvedParticipant` and no key/attribute
  `unresolved_participants` remains in `src/` or `docs/`; `graph build --json` emits
  `unresolved_references` with the unchanged `{path, entity, name}` item shape and in
  the same envelope position, and its stderr summary reads "unresolved reference(s)".

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
- **The neutral rename is the zero-debt resolution of the 025 deferral.** Iteration
  025 reused `UnresolvedParticipant` for an unresolvable `setting:` and recorded
  (its spec/plan/research/tasks) that the neutral rename belongs to iteration 027. A
  class-only rename would leave a permanent model↔wire mismatch (type says
  `Reference`, key says `participants`), so the full rename — class, `--json` key,
  and stderr prose — is taken. A maintainer/agent-facing JSON key rename is
  acceptable inside a `0.x` patch and is recorded in the CHANGELOG; no skill reads
  the key from `graph build --json`, so the blast radius is `src/`, the tests, and
  one doc page.

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
- The `bible.py` `__all__` re-export shim trim (iteration 025 review R2) — a
  separate behavior-preserving cleanup; not required here and carries no acceptance
  criterion (it may be done opportunistically).
- Any change to the renamed warning's item shape (`path`, `entity`, `name`) or its
  soft-warning semantics — User Story 3 is a name-only rename.

**Reference**: `bookwright-roadmap.md § 3`; `_envelope.py` (`ok_payload`, the "out
of 020's scope" note); the iteration-024 deferral registry
(`golem/deferrals.py`) and ingestion-parity test
(`tests/golem/test_ingestion_parity.py`); `bookwright-design.md § 4.2` (G6/G3 as
concepts and their URIs); the iteration-025 deferral of the neutral rename
(`specs/025-index-locations/{spec,plan,research,tasks}.md` — "the neutral rename is
deferred to iteration 027") and the report type and key it targets (`io/report.py`
`UnresolvedParticipant` / `unresolved_participants`, `commands/graph/build.py` stderr
summary, `docs/commands/graph-build.md`). Principle IX (`--json` single JSON
document), Principle X (frozen ontology).
