# Contract — `Indexer` Protocol & registry

Stable surface of `bookwright.indexers`. Build/query commands depend on this
contract, never on a concrete engine (FR-005/008).

## `Indexer` (typing.Protocol — `indexers/base.py`)

```python
class Indexer(Protocol):
    def load(self, ttl_path: Path) -> None: ...
    def save(self, ttl_path: Path) -> None: ...
    def add_triple(
        self,
        s: URIRef | str,
        p: URIRef | str,
        o: URIRef | Literal | str | int | float,
    ) -> None: ...
    def query(self, sparql: str) -> Iterable[dict[str, Any]]: ...
    def construct(self, sparql: str) -> "Indexer": ...
    def count(self) -> int: ...
```

| Method | Guarantees |
|---|---|
| `load` | Parses Turtle at `ttl_path` into the engine's graph. Raises if the file is missing or unparseable (caller maps to `GraphNotBuiltError` for the missing case). |
| `save` | Writes the graph as Turtle to `ttl_path`, **short prefixes bound** (FR-015), creating parent directories. Atomic enough for a single-writer CLI. |
| `add_triple` | Adds one triple. `str` subjects/predicates that look like IRIs are coerced to `URIRef`; objects keep their rdflib term type. |
| `query` | Executes SPARQL; yields one `dict` per `SELECT` row mapping projected variable name → `str(value)`. Empty iterable for zero matches. Raises `InvalidQueryError` on a malformed query (no partial yield). |
| `construct` | Executes `CONSTRUCT`; returns a fresh `Indexer` of the same concrete type wrapping the resulting sub-graph. |
| `count` | Returns the number of triples currently held. |

## Registry (`indexers/__init__.py`)

```python
INDEXER_REGISTRY: dict[str, type[Indexer]] = {"rdflib": RdflibIndexer}

def resolve_indexer(name: str) -> type[Indexer]: ...
```

- `resolve_indexer("rdflib")` → `RdflibIndexer`.
- Absent/empty manifest key → caller passes the default `"rdflib"` (FR-007).
- Unknown name → `UnknownIndexerError(name, available=sorted(INDEXER_REGISTRY))`
  whose message names the unknown engine and lists the available ones; exits
  non-zero (FR-007).
- Adding an engine = one `INDEXER_REGISTRY` entry; **no** change to build/query
  command code (FR-008). `GrafeoIndexer` is intentionally **not** registered
  (deferred to v0.3 — Principle X).

## Invariants (tested)
- `RdflibIndexer().count() == 0` on construction.
- save → load round-trips isomorphically; serialized Turtle uses short prefixes.
- `query` on a CharacterFeature/`xsd:gYear` value supports numeric/temporal
  filters (e.g. `FILTER(?year < "1850"^^xsd:gYear)`).
