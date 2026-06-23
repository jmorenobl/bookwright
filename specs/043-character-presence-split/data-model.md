# Phase 1 — Data Model

This iteration adds **no** GOLEM entity, no triple, and no ontology class. The "data" here is
the validator set and the existing `not_evaluated` record. Nothing is persisted (validators are
in-memory, FR-013/Principle X).

## Entities (validator-layer, in-memory)

### `CharacterPresence` (orphan validator — **modified**, name unchanged)

| Field | Value | Note |
|-------|-------|------|
| `name` | `"character_presence"` | **unchanged** — keeps every `error` finding byte-stable (FR-003, D2) |
| `severity_default` | `Severity.error` | unchanged |
| inputs | `character_names()`, `manuscript_files()` | character roster **only** (the union is deleted) |
| `NotEvaluated` guard | `not roster and not files` | unchanged predicate **and** reason string (FR-004) |
| output | `list[Violation]` of orphan `error`s | byte-for-byte identical to today (FR-003, SC-003) |
| `triples` | `()` | prose validator (FR-013) |

Retained internals: `_orphans`, `_is_mentioned`, `_MIN_TOKEN_LEN`. **Deleted** internals (D4):
`_CANDIDATE`, `_SENTENCE_END`, `_STOP_WORDS`, `_is_sentence_initial`, `_roster_slugs`,
`_unknown_mentions`, and the imports `make_slug`, `ProseView`.

### `CharacterUnknownMentions` (open-set abstainer — **new**)

| Field | Value | Note |
|-------|-------|------|
| `name` | `"character_unknown_mentions"` | new, distinct built-in name (FR-003 implication) |
| `severity_default` | `Severity.warning` | cosmetic — it never emits a finding (Protocol requires the attr) |
| inputs | none | reads nothing — abstains by approach, not input (D3) |
| `validate` body | `raise NotEvaluated(<reason>)` | **unconditional** (FR-005, D3) |
| reason | `"open-set proper-noun discovery requires semantic judgment (move 3); the deterministic heuristic was measured insufficient on real prose"` | names open-set/NER cause + move 3 (FR-005) |
| `triples` | n/a (no finding) | — |

Discovery: dropped into `validation/validators/`, auto-discovered by `registry.py`
(`_discover_builtins`) like every built-in; disable-able via `[validators] disabled` (FR-002,
edge case "Custom-validator config"). No hand-registration.

### `NotEvaluatedResult` (existing — iteration 040, **reused unchanged**)

`(validator, reason)` record. The runner stamps `validator="character_unknown_mentions"` and
`reason=<the abstainer's reason>` and appends it to the `not_evaluated` channel
(`runner.py:68-70`). Serialized by its existing `to_json()`. No change to the type.

## Removed entities / fields (dead-code sweep, D5)

| Removed | Where | Last consumer (removed by this iteration) |
|---------|-------|-------------------------------------------|
| `ValidationContext.location_names()` + `_location_names` field | `validation/base.py` | `character_presence.py` union line + `test_base.py` |
| `ValidationContext.object_names()` + `_object_names` field | `validation/base.py` | same |
| `NarrativeLocation` / `Object` imports (inside those accessors) | `validation/base.py` | the two accessors |
| `write_project(locations=, objects=)` knobs + scaffold loops | `tests/validation/conftest.py` | `test_base.py` + migrated `test_character_presence.py` |

**Retained** (still consumed): `setting_names()` + `_setting_names` (→ `setting_continuity`);
`_names_of`, `_UNSET`, `Character`/`Setting` imports; the `settings=` knob.

## Derived-state impact (status layer)

| Derived field | Before | After |
|---------------|--------|-------|
| `state.validation.not_evaluated` | per-project (often `[]`) | **always** includes `character_unknown_mentions` (FR-008) |
| `state.validation.ran` | 6 built-ins | **7** built-ins (adds `character_unknown_mentions`) |
| `state.validation.counts` | unchanged | **unchanged** (abstainer emits no finding; FR-007, SC-005) |
| `next_actions` | `activate_dormant_validators` fired only when something was dormant | **always** fires → one extra `bookwright-continuity` action per project (D6) |
| green predicate `status == "ok" AND not_evaluated == []` | could be `True` | **`False`** on every project (FR-008, SC-006) |

## Invariants

- **I1**: the set of `error`-level findings is identical before/after, including each finding's
  `validator` field (SC-003).
- **I2**: the CI gate (only `error` gates) has identical pass/fail on every fixture (SC-004,
  FR-007).
- **I3**: `triples == ()` for both validators; no `.ttl`/ontology byte changes (SC-008).
- **I4**: SC-009 grep over `src/` + `tests/` finds **0** occurrences of `_unknown_mentions`,
  `_roster_slugs`, `_CANDIDATE`, `_STOP_WORDS`, `_is_sentence_initial`, `location_names`,
  `object_names`, and the `locations=`/`objects=` knobs; `setting_names` keeps exactly its
  `setting_continuity` consumer.
