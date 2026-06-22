# Data Model: iteration 042 (cross-check roster widening)

This iteration adds **no** new persisted entity and **no** ontology class. It adds two
in-memory cached accessors on `ValidationContext` and widens one in-memory derived set.

## Entities (all existing; read-only here)

| Entity | GOLEM class | Bible dir | Accessor | Status |
|--------|-------------|-----------|----------|--------|
| Character | `Character` | `bible/characters/` | `character_names()` | existing |
| Setting | `Setting` | `bible/settings/` | `setting_names()` | existing |
| Location | `NarrativeLocation` | `bible/locations/` (G13) | `location_names()` | **new accessor** |
| Object | `Object` | `bible/objects/` (G16) | `object_names()` | **new accessor** |

All four accessors return the identical shape: a sorted tuple of `(name, bible_relpath)`
pairs, produced by the shared generic `_names_of(concept_cls)`. No new helper; the only
additions are two memoized wrappers and their two cache sentinels.

### Roster pair (shape, unchanged)

- `name: str` — the entity's authored `name` from its bible card front-matter.
- `bible_relpath: str` — the project-relative posix path of the card (used only by the
  orphan rule's `source`; the unknown-mention rule consumes only the names).
- Ordering: `tuple(sorted(...))` for determinism (matches `setting_names()`).

## Derived set (widened)

### Known-names slug set

- **Producer**: module-level `_roster_slugs(roster)` in `character_presence.py` — unchanged.
  For each `(name, _)` pair it adds `make_slug(name)` and `make_slug(token)` for every
  whitespace token whose slug is non-empty.
- **Input (changed)**: was `character_names()` only; now the **concatenation**
  `character_names() + setting_names() + location_names() + object_names()`.
- **Consumer**: `_unknown_mentions` — a candidate token is suppressed when its slug is in
  this set (alongside the existing `first_seen` / `_STOP_WORDS` / sentence-initial guards).
- **Monotonicity**: union membership only grows, so widening can only **suppress** more
  candidates, never re-introduce a previously-suppressed finding (edge case in spec).

## Validation rules (behavioral invariants)

| Rule | Severity | Domain (after this change) | Changed? |
|------|----------|----------------------------|----------|
| Orphan (bible name never mentioned) | `error` | **character** roster only | **No** (FR-004/FR-006) |
| Unknown mention (prose proper noun, no bible entry) | `warning` | union of all four rosters | **suppression set widened** (FR-002/FR-003) |
| Not-evaluated guard | — | `not character_names and not files` | **No** (FR-007) |

## Memoization (mirrors `setting_names()`)

Two new `_UNSET`-sentinel fields on the `ValidationContext` dataclass:

```python
_location_names: Any = field(default=_UNSET, repr=False, compare=False)
_object_names: Any = field(default=_UNSET, repr=False, compare=False)
```

Each accessor lazily imports its concept class (`from bookwright.golem import …`), calls
`self._names_of(cls)` once, caches, and returns the cast tuple — byte-for-byte the
`setting_names()` body with the class swapped. `bible()` is shared, so the two extra
accessors add no disk read.
