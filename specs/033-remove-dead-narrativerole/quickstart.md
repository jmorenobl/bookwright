# Quickstart — verifying the `NarrativeRole` removal

Runnable checks that prove the change is correct, information-preserving, and
debt-closing. Run from the repo root with the project env (`uv sync` once).

## Prerequisites

```bash
uv sync
```

## 1. The concept is gone from the surface (SC-001)

```bash
uv run python -c "from bookwright.golem import CONCEPTS; \
  assert len(CONCEPTS) == 12, len(CONCEPTS); \
  assert 'NarrativeRole' not in CONCEPTS; \
  print('CONCEPTS = 12, NarrativeRole absent ✓')"

# Importing the deleted class now fails:
uv run python -c "from bookwright.golem import NarrativeRole" 2>&1 \
  | grep -q ImportError && echo "import of NarrativeRole fails ✓"
```

## 2. The frozen ontology is unchanged (SC-003, Principle X)

```bash
uv run python -c "from bookwright.golem.namespaces import CLASS_IRI; \
  assert len(CLASS_IRI) == 17, len(CLASS_IRI); \
  assert 'NarrativeRole' in CLASS_IRI; \
  print('CLASS_IRI = 17, G11 key preserved ✓')"

# golem.ttl must have no diff:
git diff --quiet -- src/bookwright/resources/schemas && \
  echo "golem.ttl / schemas unchanged ✓"
```

## 3. G11 is still materialized via the carrier (SC-002 — zero regression)

```bash
uv run python -c "
from rdflib.namespace import RDF
from bookwright.golem.modules.character import Character
from bookwright.golem.namespaces import CLASS_IRI
c = Character(uri_base='https://x/', name='Aparici', narrative_roles=('protagonist',))
g11 = [t for t in c.to_triples() if t[1]==RDF.type and t[2]==CLASS_IRI['NarrativeRole']]
assert g11, 'G11 triple missing!'
print('G11 still emitted by CharacterRole ✓', g11[0])
"
```

For human assurance of *whole-graph* equivalence, build a fixture before and
after the change and diff the Turtle — they must be identical:

```bash
uv run bookwright graph build --root tests/fixtures/parity-exercise   # on a tmp copy
# (the parity test already does this build-and-observe automatically)
```

## 4. The hardened parity contract closes DEBT-001 (SC-004)

```bash
uv run pytest tests/golem/test_ingestion_parity.py -q
```

Expect green, including the new `carrier_iri_collisions` invariant (empty for the
real registry) and the drift sim that re-adds `"NarrativeRole"` to a local copy
and asserts it is **named** as a collision failure.

## 5. The grep contract holds (SC-007)

```bash
grep -rn NarrativeRole src/ tests/ --exclude-dir=__pycache__
# Every hit must be a CLASS_IRI key use or the CARRIER_NAMES set —
# NO top-level concept import / CONCEPTS / __all__ / EXPECTED_REACHABLE entry.
```

## 6. The ledger reflects reality (SC-005)

```bash
grep -q "DEBT-001" DEBT.md && echo "FAIL: DEBT-001 still present" || echo "DEBT-001 removed ✓"
```

## 7. All four gates (SC-006)

```bash
uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest
```

All green ⇒ the iteration is done.
