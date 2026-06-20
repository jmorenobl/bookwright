# Data Model: Narrative-structure continuity validator

No new persisted entity, no new ontology term. This feature **reads** the existing
narrative-structure layer and **produces** existing `Violation` findings. The
"model" here is therefore: the inputs it reads, the new in-process accessor, and
the shape of the two findings it emits.

## Read inputs (all existing)

### Derived graph (via `Indexer`, US1)

| Term | IRI | Role here |
|---|---|---|
| `G9_Narrative_Unit` | `golem:G9_Narrative_Unit` | the beat; orphan candidate |
| `G7_Narrative_Sequence` | `golem:G7_Narrative_Sequence` | the plot line |
| `dlp:proper-part` | `…DOLCE-Lite#proper-part` | sequence → member unit edge |
| `E13_Attribute_Assignment` + `P140`/`P16` | (provenance) | unit → `file:line` (`resolve_source`) |

A unit is **orphaned** ⇔ it is the object of no `dlp:proper-part` whose subject is
a `G7_Narrative_Sequence`. `NarrativeUnit` emits **no `rdfs:label`** — its name is
not in the graph (research D4); the orphan is named by its URI slug.

### Outline ingestion `MapResult` (via `ValidationContext.outline()`, US2)

| Field | Type | Role here |
|---|---|---|
| `unresolved_references` | `list[UnresolvedReference]` | the unresolved-role records |
| `mapped` | `list[MappedEntity]` | `NarrativeUnit` entities → `{name: uri}` map for `resolve_source` |

`UnresolvedReference(path: str, entity: str, name: str)` — `path` = card relpath,
`entity` = unit name, `name` = the unresolved role slug. **Shared** with bible
misses, so it is filtered to records whose `path` is under `"{outline}/units/"`
(research D6).

## New in-process accessor: `ValidationContext.outline()`

A cached, read-once-per-run accessor mirroring the existing `bible()`:

- **New field**: `_outline: Any = field(default=_UNSET, repr=False, compare=False)`.
- **Body**: run `map_bible(root, bible_dir, uri_base)` then
  `map_outline(root, root / paths.outline, uri_base, result)`; cache and return
  the combined `MapResult`. No vocabularies (they do not affect
  `unresolved_references` — research D5).
- **Invariants**: writes nothing; no card is parsed by the validator itself; a
  project without `outline/units/` yields a `MapResult` whose
  `unresolved_references` has no `outline/units/` entries → US2 inert (FR-009).

## New query helper: `queries.load_orphan_units`

```python
def load_orphan_units(indexer: Indexer) -> list[str]:
    """Sorted URIs of every G9 unit that is a member of no G7 sequence (FR-005)."""
```

- Requires adding `("dlp", str(DLP))` to `queries._PREFIXES` (import `DLP`).
- Returns URIs **sorted** for determinism (research D9).
- A graph with no `G9` units returns `[]` → US1 inert (FR-009).

## New validator: `NarrativeStructure`

```python
class NarrativeStructure:
    name: ClassVar[str] = "narrative_structure"
    severity_default: ClassVar[Severity] = Severity.warning

    def validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]:
        ...
```

Auto-discovered (research D1). Conforms to the `Validator` protocol. Deterministic,
read-only (FR-008).

### Finding: orphan beat (US1 / FR-005)

| Field | Value |
|---|---|
| `validator` | `"narrative_structure"` |
| `severity` | `Severity.warning` |
| `message` | e.g. `narrative unit '<slug>' belongs to no narrative sequence (orphan beat)` |
| `source` | `resolve_source(indexer, unit_uri)` → `relpath:line` (or `None` if unprovenanced) |
| `triples` | `()` |

One finding per orphan unit. `<slug>` = URI localname.

### Finding: unresolved role (US2 / FR-006)

| Field | Value |
|---|---|
| `validator` | `"narrative_structure"` |
| `severity` | `Severity.warning` |
| `message` | e.g. `narrative unit '<unit>' references role '<role>' which resolves to no character role` |
| `source` | `resolve_source(indexer, unit_uri)` for `ref.entity`, else `ref.path` |
| `triples` | `()` |

One finding per filtered `UnresolvedReference`. `<unit>` = `ref.entity`,
`<role>` = `ref.name`.

## What is NOT modelled (out of scope — research D8)

- **Order gap/duplicate** (rule b): `order:` is not graph-serialized and a gap is
  legitimate sparse numbering → no finding. A test asserts the non-finding (FR-007).
- **Empty sequence** (rule d): never minted by ingestion → no reachable input.
- **No new class/property**: nothing added to `golem.ttl` (FR-012, SC-007).

## Determinism & contract conformance

- Validator sorts its own outputs (orphans by URI; references by
  `(path, entity, name)`); the runner re-dedups and applies its total-order sort →
  byte-stable across runs (FR-008, SC-005).
- Findings serialize through the existing `Violation.to_json()` /
  `ValidationReport.to_json()` — **no** new top-level envelope key (FR-003, SC-003).
