# Quickstart: run the ingestion-parity guard

Runnable validation for iteration 024. Assumes `uv sync` has run and you are at the repo
root. Details live in [data-model.md](./data-model.md) and
[contracts/parity-contract.md](./contracts/parity-contract.md).

## Prerequisites

- iterations through 023 merged on `main` (v0.3.0).
- `uv sync` (deps + dev group).

## 1. The guard passes on current code (SC-001, SC-003)

```bash
uv run pytest tests/golem/test_ingestion_parity.py -v
```

**Expected:** all green. The live parity test builds the graph from
`tests/fixtures/parity-exercise/`, derives the orphan set, and confirms it equals the
seven keys of `DEFERRED_CONCEPTS`; the reachable-set pin confirms exactly
`{Character, Setting, NarrativeEvent, SocialRelationship, NarrativeRole,
AttributeAssignment}` materialized and none of the seven orphans did; the three
drift-simulation tests confirm a named-concept failure for each of FR-006/007/008.

## 2. The fixture really exercises every path (FR-004, US2)

```bash
cp -r tests/fixtures/parity-exercise /tmp/parity && cd /tmp/parity
uv run --project "$OLDPWD" bookwright graph build --json | python -m json.tool
# inspect the six concept types in the derived cache:
grep -E "G1_Character|G12_Setting|G5_Narrative_Event|G4_Social_Relationship|G11_Narrative_Role|E13_Attribute_Assignment" bible/graph.ttl | head
cd - && rm -rf /tmp/parity
```

**Expected:** clean build (exit 0); the six concept `rdf:type` IRIs are present in
`bible/graph.ttl`; none of the orphan IRIs (`G13/G16/G3/G6/G9/G10/G7`) appears.

## 3. The registry is well-formed (SC-002)

```bash
uv run python -c "
from bookwright.golem import CONCEPTS
from bookwright.golem.deferrals import DEFERRED_CONCEPTS
assert len(DEFERRED_CONCEPTS) == 7
assert set(DEFERRED_CONCEPTS) <= set(CONCEPTS)
assert all(n.reason and n.target_version for n in DEFERRED_CONCEPTS.values())
print('registry OK:', sorted(DEFERRED_CONCEPTS))
"
```

**Expected:** `registry OK: ['NarrativeFunction', 'NarrativeLocation', 'NarrativeSequence',
'NarrativeUnit', 'Object', 'PsychologicalState', 'RelationshipRole']`.

## 4. The author-only note is present, behavior unchanged (FR-011, SC-005)

```bash
grep -i "outline" src/bookwright/io/manuscript.py
grep -i "outline" docs/authoring.md
```

**Expected:** the manuscript-reader docstring and the Spanish authoring doc each state
`outline/` (and `manuscript/`) are author-only in v0.3, not ingested by the engine.

## 5. Determinism and the four CI gates (SC-004, SC-006)

```bash
uv run pytest tests/golem/test_ingestion_parity.py -v   # run twice — identical verdict
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest                                            # full suite ≥80% coverage
```

**Expected:** identical results across the two parity runs; all four gates green; no
class or property added to the frozen closure (`test_frozen_ontology.py` /
`test_namespaces.py` unchanged).
