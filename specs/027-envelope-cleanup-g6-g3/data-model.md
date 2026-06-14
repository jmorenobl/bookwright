# Phase 1 Data Model: envelope cleanup + G6/G3 decision

This iteration introduces **no new** persisted entity and **no** ontology change.
It edits the shape of two existing in-memory models and one registry's data. The
"entities" below are the affected structures, with their before/after.

## 1. Success envelope (no model — a shape contract)

The success document a `--json` command emits. The skeleton `{"status": "ok", …}`
is single-sourced in `ok_payload(**fields)` (`commands/_envelope.py`); `check`'s
`{"ok": <bool>, "checks": […]}` is a deliberate variant **without** a top-level
`status` key.

| Command | Envelope (unchanged bytes) | Construction after |
|---|---|---|
| `check` | `{"ok": <bool>, "checks": [{"name","status"[,"detail"]}, …]}` | hand-built dict (kept — no `status` key) |
| `focus show` | `{"status":"ok","focus":{…}\|null}` | `ok_payload(focus=…)` |
| `focus set` | `{"status":"ok","focus":{…}}` | `ok_payload(focus=…)` |
| `focus clear` | `{"status":"ok","cleared":<bool>}` | `ok_payload(cleared=…)` |
| `graph query` | `{"status":"ok","results":[…],"count":N}` | `ok_payload(results=…, count=…)` |
| `graph build` | `{"status":"ok", …metrics…, "unresolved_references":[…], …}` | `BuildReport.to_json()` (key renamed) |

**Validation rule**: stdout bytes identical to the captured pre-change baseline
for every row except the single `graph build` key (US3); exit codes unchanged.

## 2. `DeferralNote` registry (`golem/deferrals.py`)

`NamedTuple(reason: str, target_version: str)`. **No shape change** — only the
contract on `target_version`'s allowed values and two data rows change.

| Concept | Before `target_version` | After `target_version` | After `reason` |
|---|---|---|---|
| `NarrativeUnit` (G9) | `v0.4` | `v0.4` | unchanged |
| `NarrativeFunction` (G10) | `v0.4` | `v0.4` | unchanged |
| `NarrativeSequence` (G7) | `v0.4` | `v0.4` | unchanged |
| `RelationshipRole` (G6) | `undecided` | **`v0.4`** | **"requires a typed roles/states model with attributes and an authoring surface"** |
| `PsychologicalState` (G3) | `undecided` | **`v0.4`** | **"requires a typed roles/states model with attributes and an authoring surface"** |

**Contract change**: the `DeferralNote` docstring's enumerated `target_version`
values drop `"undecided"`. After this iteration **no** entry may carry
`"undecided"` (FR-011); enforced by a new assertion in `test_registry_well_formed`.

**Invariants preserved**: still exactly 5 entries; keys ⊆ `CONCEPTS`; keys equal
`ORPHAN_NAMES`; every `reason` non-empty; orphan/reachable sets unchanged.

## 3. `UnresolvedReference` (was `UnresolvedParticipant`) — `io/report.py`

Frozen Pydantic model, `extra="forbid"`. **Fields unchanged**:

| Field | Type | Meaning |
|---|---|---|
| `path` | `str` | source file relative path |
| `entity` | `str` | the owning built entity's name |
| `name` | `str` | the unresolved reference text (a `participants:` member **or** a `setting:` location) |

**Changes**: class name `UnresolvedParticipant` → `UnresolvedReference`; docstring
generalized to any unresolved name reference (not only participants). Soft-warning
semantics unchanged: the owning entity is still built; the exit code never changes.

### `BuildReport` (`io/report.py`) field + serializer

| Member | Before | After |
|---|---|---|
| field | `unresolved_participants: tuple[UnresolvedParticipant, …]` | `unresolved_references: tuple[UnresolvedReference, …]` |
| `to_json()` key | `"unresolved_participants"` | `"unresolved_references"` (same position) |

### `BuildResult` (`io/_bible_builders.py`) intermediate field

| Member | Before | After |
|---|---|---|
| field | `unresolved_participants: list[UnresolvedParticipant]` | `unresolved_references: list[UnresolvedReference]` |
| append sites (×3) | `UnresolvedParticipant(...)` | `UnresolvedReference(...)` |

### `commands/_graph.py` mapping

`unresolved_participants=tuple(result.unresolved_participants)` →
`unresolved_references=tuple(result.unresolved_references)`.

### `commands/graph/build.py` stderr summary

`f"{len(report.unresolved_participants)} unresolved participant reference(s)"` →
`f"{len(report.unresolved_references)} unresolved reference(s)"`.

## State transitions

None. All edits are static shape/data/name changes; no runtime state machine is
involved.
