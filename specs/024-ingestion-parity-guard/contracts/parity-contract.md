# Contract: deferral registry + ingestion-parity guard

The project exposes no new external/CLI surface this iteration. The "contracts" here are
the **module shape** of the deferral registry and the **assertion contract** of the
parity test — the two seams iteration 025+ will edit when wiring a concept.

## 1. Module contract — `bookwright.golem.deferrals`

```python
from typing import NamedTuple

class DeferralNote(NamedTuple):
    reason: str          # non-empty, short
    target_version: str  # non-empty; exactly "v0.3.x" | "v0.4" | "undecided"

DEFERRED_CONCEPTS: dict[str, DeferralNote]
```

**Invariants** (asserted by tests, not enforced at runtime):

- `set(DEFERRED_CONCEPTS) ⊆ set(CONCEPTS)` — every key is a known concept.
- `len(DEFERRED_CONCEPTS) == 7` and the key set is exactly
  `{NarrativeLocation, Object, NarrativeUnit, NarrativeFunction, NarrativeSequence,
  RelationshipRole, PsychologicalState}` (FR-002, SC-002).
- The full concept→`target_version` mapping is pinned exactly:
  `NarrativeLocation`/`Object` → `v0.3.x`; `NarrativeUnit`/`NarrativeFunction`/
  `NarrativeSequence` → `v0.4`; `RelationshipRole`/`PsychologicalState` →
  `undecided` (FR-002, SC-002). A wrong version fails the test.
- No carrier name (`CharacterFeature`, `Dimension`, `Type`, `TimeInterval`) appears
  (FR-010).
- Every `reason` is non-empty (SC-002).

**Import side effects**: none. Pure data; imports only `typing` (and optionally
`CONCEPTS` is *not* imported here to keep the module dependency-free — the test imports
both and reconciles them).

## 2. Assertion contract — `tests/golem/test_ingestion_parity.py`

**Liveness probe** (FR-003, research D2):

```
outcome  = build_project_graph(parity_exercise_root, manifest)   # the real pipeline
types    = { row["t"] for row in outcome.engine.query(
             "SELECT DISTINCT ?t WHERE { ?s a ?t }") }            # observed rdf:type IRIs
reachable = { name for name in CONCEPTS
              if CLASS_IRI[name] in types }                       # scoped to CONCEPTS
orphans  = set(CONCEPTS) - reachable
```

**The guard** (FR-005, SC-001):

```
assert orphans == set(DEFERRED_CONCEPTS)
```

**Derived sub-assertions** (so a failure is specific, SC-003):

| Failure mode | Condition | Message names |
|---|---|---|
| fed-but-still-deferred (FR-006/007) | `reachable ∩ set(DEFERRED_CONCEPTS) ≠ ∅` | each offending concept |
| undeclared orphan (FR-008) | `orphans − set(DEFERRED_CONCEPTS) ≠ ∅` | each offending concept |

**Reachable-set pin** (FR-004, US2): independently assert
`reachable == {Character, Setting, NarrativeEvent, SocialRelationship, NarrativeRole,
AttributeAssignment}` and that **none** of the seven orphan IRIs appears in `types`.

**Determinism** (FR-009, SC-004): the verdict is a pure function of the fixture corpus
and `DEFERRED_CONCEPTS`; running the build+verdict twice yields identical results. (The
probe queries `DISTINCT ?t`, set-valued, order-independent.)

## 3. Drift-simulation contract (research D5)

A pure helper drives the three FR-006/007/008 failure paths on perturbed *local copies*,
never mutating `DEFERRED_CONCEPTS`:

```
parity_diff(reachable, deferred) -> (fed_but_deferred: set[str], undeclared_orphans: set[str])
```

- `parity_diff(reachable, deferred_with_a_reachable_added)` → `fed_but_deferred` names it.
- `parity_diff(reachable, deferred_missing_a_real_orphan)` → `undeclared_orphans` names it.
- On the real inputs both returned sets are empty.

## 4. Documentation contract (FR-011, SC-005)

- [io/manuscript.py](../../../src/bookwright/io/manuscript.py) module docstring states
  `manuscript/` **and** `outline/` are author-only in v0.3 (presence/scaffold only, no
  ingestion).
- [docs/authoring.md](../../../docs/authoring.md) carries one Spanish line saying the
  same.
- **No** ingestion behavior changes: `manuscript_present` is byte-identical; no
  `outline/` reader is added; the full suite confirms no new directory is read and no new
  entity materializes.
