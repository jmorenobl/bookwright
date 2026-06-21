# Contract — GOLEM public surface & ingestion-parity invariants (post-change)

This iteration's only external interfaces are (a) the GOLEM package's public
import surface and (b) the ingestion-parity test contract. Both are pinned here
so `/speckit-analyze`, `/speckit-tasks`, and review can check the implementation
against an explicit shape. No CLI command, JSON envelope, or `SKILL.md` contract
changes — those sections are intentionally absent.

## C1 — `bookwright.golem` public surface

**`CONCEPTS`** — exactly 12 keys; `"NarrativeRole"` absent:

```
Character, Object, SocialRelationship, RelationshipRole, NarrativeEvent,
PsychologicalState, Setting, NarrativeLocation, NarrativeUnit,
NarrativeFunction, NarrativeSequence, AttributeAssignment
```

**`__all__`** — `"NarrativeRole"` absent; every other current export retained
(`NarrativeFunction`, `NarrativeSequence`, `NarrativeUnit` stay). No import of
the deleted class remains anywhere in `src/` or `tests/`.

**`from bookwright.golem import NarrativeRole`** — MUST raise `ImportError`
after the change (the name is gone from the package surface).

**Module docstring** — "the thirteen GOLEM concept classes" → "the twelve GOLEM
concept classes".

## C2 — Frozen ontology (unchanged — Principle X)

```
len(CLASS_IRI) == 17                       # before AND after
"NarrativeRole" in CLASS_IRI               # KEY PRESERVED (carrier IRI)
golem.ttl                                  # byte-for-byte identical (no diff)
```

`CLASS_IRI` partitions as `12 concept IRIs + 5 carrier-only IRIs`
(`CharacterFeature, Dimension, Type, TimeInterval, NarrativeRole`).

## C3 — `CharacterRole` carrier (unchanged behaviour — FR-005)

```
CharacterRole.golem_class == CLASS_IRI["NarrativeRole"]
to_triples() emits, for a character role labelled L on character C:
    (C/role/slug(L), rdf:type, golem:G11_Narrative_Role)
    (C/role/slug(L), rdfs:label, Literal(L))
    (C/role/slug(L), crm:P2_has_type, <actant>)   # iff type_uri set
```

Only the docstring changes; output is identical ⇒ every `golem:G11_Narrative_Role`
triple in every built graph is preserved (SC-002).

## C4 — Ingestion-parity invariants (`tests/golem/test_ingestion_parity.py`)

Pinned module constants after the change:

```python
EXPECTED_REACHABLE = { 10 names }                      # NarrativeRole dropped
ORPHAN_NAMES       = {"PsychologicalState", "RelationshipRole"}   # unchanged
EXPECTED_VERSIONS  = {both → "demand-pulled"}          # unchanged
CARRIER_NAMES      = {"CharacterFeature", "Dimension", "Type",
                      "TimeInterval", "NarrativeRole"} # +NarrativeRole
```

New pure helper (no I/O, no registry mutation):

```python
def carrier_iri_collisions(concepts: set[str]) -> set[str]:
    """Concept names whose CLASS_IRI equals a carrier-only IRI (the DEBT-001
    pattern). Empty for a healthy registry."""
    carrier_iris = {str(CLASS_IRI[k]) for k in CARRIER_NAMES}
    return {c for c in concepts if str(CLASS_IRI[c]) in carrier_iris}
```

Invariants the test suite MUST assert:

1. **Reachable pin** — real build's reachable set `== EXPECTED_REACHABLE` (10);
   no orphan IRI leaks (FR-007).
2. **Registry well-formed** — `len(CONCEPTS) == 12`; `CARRIER_NAMES` disjoint
   from `CONCEPTS`; `set(DEFERRED_CONCEPTS) == ORPHAN_NAMES` with the version map
   `== EXPECTED_VERSIONS`; no `"undecided"` target.
3. **Carrier-IRI disjointness (new, FR-006)** —
   `carrier_iri_collisions(set(CONCEPTS)) == set()` for the real registry.
4. **Carrier-IRI collision drift (new, SC-004)** —
   `"NarrativeRole" in carrier_iri_collisions(set(CONCEPTS) | {"NarrativeRole"})`
   — re-introducing the dead concept is *named* as a failure.
5. **Live parity** — real-build orphan set `== set(DEFERRED_CONCEPTS)` (FR-007).
6. Existing drift sims (fed-but-deferred, undeclared-orphan, determinism) keep
   passing unchanged.

## C5 — Post-change `grep` contract (SC-007)

`grep -rn NarrativeRole src/ tests/` (excluding `__pycache__`) returns **only**:

- `golem/namespaces.py` — the `CLASS_IRI["NarrativeRole"]` key definition;
- `golem/modules/feature.py` — `CharacterRole.golem_class` + rewritten docstring;
- `tests/golem/test_character_attributes.py` — `CLASS_IRI["NarrativeRole"]` assert;
- `tests/golem/test_namespaces.py` — carrier-bucket membership;
- `tests/golem/test_ingestion_parity.py` — `CARRIER_NAMES`.

No occurrence references a *top-level `NarrativeRole` concept*: no class import,
no `CONCEPTS` / `__all__` / segment-table / `EXPECTED_REACHABLE` entry, no
"the top-level `NarrativeRole`" comment.
