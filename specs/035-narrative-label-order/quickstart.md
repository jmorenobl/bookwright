# Quickstart — verify G9 labels + queryable sequence order

Prerequisites: `uv sync`. All commands from the repo root.

## 1. Run the targeted tests

```bash
# The two demonstrative SPARQL queries (find-by-label, list-in-order)
uv run pytest tests/golem/test_narrative_label_order.py -q

# Emission + term-closure (now bw:-aware) + ordinal provenance
uv run pytest tests/golem/test_triples.py tests/golem/test_derived_assertions.py -q

# Sequence assembly reinforcement (ordinal subject=unit, contiguous 1..N)
uv run pytest tests/io/test_outline_sequences.py -q

# E2E: build → validate over tiny-quest; _ordered_members now queries the graph
uv run pytest tests/e2e/test_narrative_workflow.py -q

# Closure list unchanged + green (SC-005)
uv run pytest tests/golem/test_namespaces.py -q
```

## 2. See the labels and ordinals in a real graph

```bash
cd tests/fixtures/tiny-quest          # source-only worked example
uv run bookwright graph build --json  # writes bible/graph.ttl
```

Find a beat by name (US1):
```bash
uv run bookwright graph query --json \
  'SELECT ?u WHERE { ?u a <https://w3id.org/golem/ontology#G9_Narrative_Unit> ;
     <http://www.w3.org/2000/01/rdf-schema#label> "Interdiction Beat" }'
```

List the Quest sequence in declared order (US2):
```bash
uv run bookwright graph query --json \
  'SELECT ?u ?n WHERE {
     ?s a <https://w3id.org/golem/ontology#G7_Narrative_Sequence> .
     ?s <http://www.ontologydesignpatterns.org/ont/dlp/DOLCE-Lite.owl#proper-part> ?u .
     ?u <https://bookwright.dev/vocab/bw#sequenceOrdinal> ?n } ORDER BY ?n'
```
Expected member order: `interdiction-beat, departure-beat, villainy-beat, struggle-beat,
return-beat` (matches `expected-narrative.md`’s `sequence.members`).

> Clean up: `rm bible/graph.ttl` — the committed fixture is source-only (Group D).

## 3. The four gates

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest                 # full suite, ≥80% coverage
```

## Expected outcomes (mapped to success criteria)

- SC-001 — a name→unit query that returned 0 rows before now returns the unit.
- SC-002 — the order query returns members in declared order, including gaps/missing/dups.
- SC-003 — both demonstrative queries pass as automated tests.
- SC-004 — full suite + four gates green; `narrative_structure` and all validators green.
- SC-005 — `golem.ttl`/`CLASS_IRI`/`test_namespaces.py` closure unchanged.
- SC-006 — labels + ordinals + membership are byte-identical across rebuilds.
- DEBT-005 removed from `DEBT.md`.
