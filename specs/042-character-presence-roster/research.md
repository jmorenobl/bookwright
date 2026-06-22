# Research: `character_presence` cross-checks settings/locations/objects (iteration 042)

All decisions below were resolved against the existing code and the spec's two
clarifications; there are **no** remaining NEEDS CLARIFICATION.

## D1 — Which GOLEM classes back the new accessors?

**Decision**: `location_names()` binds `NarrativeLocation`; `object_names()` binds `Object`.
Both are imported from `bookwright.golem` and resolved through the existing generic
`ValidationContext._names_of(concept_cls)` helper, exactly as `setting_names()` binds
`Setting`.

**Rationale**: verified empirically — `bookwright.golem.__init__` exports both
`NarrativeLocation` (from `golem/modules/setting.py`) and `Object` (from
`golem/modules/character.py`), and `io/bible.py`'s `map_bible` binds them to
`bible/locations/` (concept `"NarrativeLocation"`) and `bible/objects/` (concept
`"Object"`). There is **no** class literally named `Location`; using it would fail to
import. `_names_of` filters `self.bible().mapped` by `isinstance(entity, concept_cls)`, so
any `SluggedEntity` subclass already works — no helper change needed.

**Alternatives considered**: a single new helper taking a list of classes (rejected —
breaks the "mirror `setting_names()` exactly" contract and the per-class memoization
sentinel; `_names_of` already generalizes the extraction); SPARQL over the built graph
(rejected — FR-009 requires the cross-check stay file-based, and the validator must need no
built graph).

## D2 — How does the unknown-mention rule consume the wider roster?

**Decision**: in `CharacterPresence.validate`, keep `roster = project.character_names()`
feeding `_orphans`, but build the slug set for `_unknown_mentions` from the **concatenation**
of the four roster tuples, passed once through the existing module-level `_roster_slugs`:

```python
known = (
    roster
    + project.setting_names()
    + project.location_names()
    + project.object_names()
)
roster_slugs = _roster_slugs(known)
```

`_orphans(roster, files)` is unchanged (character-only); `_unknown_mentions(view,
roster_slugs)` is unchanged in signature and body — it simply receives a larger frozenset.

**Rationale**: `_roster_slugs` already turns each `(name, relpath)` pair into the slug of
the full name **and** each token slug, which is exactly the per-entity contribution the
spec requires for every roster (FR-002). Reusing it unchanged means the four rosters
contribute identically and no new matching algorithm is introduced (Assumptions). Tuple
concatenation is cheap and order-independent (the result is a `frozenset`).

**Alternatives considered**: merging four frozensets with `|` (equivalent, but requires
four `_roster_slugs` calls — concatenating the pairs first calls it once and is clearer);
adding settings/locations/objects to `_orphans` too (rejected — FR-004: the `error` orphan
rule must derive **exclusively** from characters; an unmentioned setting is not a gate
failure).

## D3 — Does the `NotEvaluated` guard change?

**Decision**: no. The guard stays `if not roster and not files:` where `roster` is
`character_names()` only, raising the identical reason string
`"there is no manuscript prose and no bible character roster to cross-check"`.

**Rationale**: FR-007 / SC-005 pin this contract from iteration 040. A project with
settings/locations/objects but no characters and no prose still has nothing to
cross-check in either direction — the orphan rule has no character roster and the
unknown-mention rule has no prose. Letting declared environments flip the abstain decision
would perturb a load-bearing tri-valued contract for no benefit.

**Alternatives considered**: widening the guard to `not (roster | settings | …) and not
files` (rejected — changes when the validator abstains, violating FR-007).

## D4 — Which oracles shift, and how is regression verified?

**Decision**: only `tests/fixtures/tiny-historical/expected-status.md`'s
`validation.counts.warning` shifts, `4 → 1`. Regression is verified **empirically** by
running the full suite (FR-011); no fixture manuscript or bible is edited.

**Rationale**: empirically confirmed during specification — on `tiny-historical` today the
unknown-mention rule emits exactly three setting-token warnings (`Real`, `Fábrica`,
`Paños`, all tokens of the declared setting "la Real Fábrica de Paños" under
`bible/settings/`), plus one `factual_anchor` warning, for the project-wide total of 4 that
status pins. Widening the roster suppresses the three setting tokens (their slugs now match
the setting roster), leaving `character_presence` at **0** warnings and the project total
at **1** (the surviving `factual_anchor` warning). `validation.counts.error` stays `1`
(byte-identical). `tiny-novel` / `tiny-memoir` assert only `error == 0` (warnings
tolerated, no pinned count), so they need no edit.

**Alternatives considered**: editing the fixture manuscript to remove the setting mention
(rejected — FR-011/SC-006 forbid fixture content edits; the point is that the *declared*
name should suppress, not that the prose should change).

## D5 — How are the location & object arms proven without editing a pinned fixture?

**Decision**: with synthetic-project unit tests on the existing
`tests/validation/conftest.py` `write_project` / `load_context` pattern, extending
`write_project` with `locations` and `objects` keyword arguments that mirror the existing
`settings` one byte-for-byte (write one `bible/<dir>/<slug>.md` card per name). The
`tiny-historical` E2E proves only the **setting** arm and the `4 → 1` correction.

**Rationale**: `tiny-historical` declares no `bible/locations/` or `bible/objects/`, and
FR-011 forbids editing any pinned fixture. Synthetic projects give the location and object
union arms (and both new context accessors) real, isolated coverage so neither ships as
untested dead plumbing (Principle VIII; FR-015). The new `write_project` knobs default to
`()`, so every existing caller builds a byte-identical project.

**Alternatives considered**: adding locations/objects to `tiny-historical` (rejected —
fixture edit, FR-011); skipping location/object tests and relying on the setting arm by
analogy (rejected — Principle VIII: the new accessors and union arms must be exercised).

## D6 — Frozen-ontology & file-size compliance

**Decision**: no `.ttl` edit, no class added; the validator's `triples` stay `()`; both
changed source files stay ≤ 500 lines.

**Rationale**: `NarrativeLocation` and `Object` are existing frozen concepts, only read via
`_names_of`. SC-007 is directly checkable: `git diff` over
`resources/schemas/golem-1.1/` and `golem.ttl` empty; `wc -l` on each changed file ≤ 500
(`base.py` ~350, `character_presence.py` ~218).
