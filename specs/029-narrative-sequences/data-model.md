# Data Model: Outline ingestion — narrative sequences (G7)

No ontology change. The GOLEM model classes are reused verbatim; the only new
type is an internal, transient member record used during assembly.

## Entities (GOLEM — unchanged classes)

### NarrativeSequence (G7) — `golem/modules/narrative.py` (untouched)

| Aspect | Value |
|---|---|
| `golem_class` | `CLASS_IRI["NarrativeSequence"]` (`golem:G7_Narrative_Sequence`) |
| `path_segment` | `narrative-sequence` → URI `…/narrative-sequence/<slug>` |
| identity | `make_slug(name)` (a `SluggedEntity`) |
| cross-ref | `CrossRef("units", PROPER_PART, multi=True)` → one `dlp:proper-part` triple per member, **in tuple order** |
| attributes | none beyond identity |

The model already exists and is **not** edited. This feature only constructs it
with an ordered `units` tuple.

### NarrativeUnit (G9) — entity unchanged

The `NarrativeUnit` entity gains **no** attribute. Its card's recognised
front-matter keys widen from `{name, functions, roles}` to
`{name, functions, roles, sequence, order}`; `sequence`/`order` drive sequence
assembly only and are never serialized onto the unit.

## Transient record (internal to `io/outline.py`)

### `_SeqMember` (a `NamedTuple`, not a GOLEM entity)

One record per surviving, sequence-naming unit card, collected during the
per-file pass and consumed by the assembly step. Never serialized.

| Field | Type | Meaning |
|---|---|---|
| `seq_slug` | `str` | `make_slug(sequence)` — the grouping/dedup key (FR-002) |
| `seq_name` | `str` | the raw `sequence` value — display-name candidate (D4) |
| `order` | `int \| None` | the `order` value; `None` when omitted (FR-005) |
| `unit_slug` | `str` | `make_slug(unit name)` — the tie-break key (FR-006) |
| `unit` | `NarrativeUnit` | the built member entity (becomes a `units` tuple item) |
| `relpath` | `str` | the card's project-relative path — provenance carrier (D5) |

A card with no usable `sequence` produces **no** `_SeqMember` (FR-004/FR-008).

## Recognised keys (FR-001)

```python
UNIT_KEYS = frozenset({"name", "functions", "roles", "sequence", "order"})
```

Any other key remains a soft `unknown_keys` warning, exactly as today.

## Validation & coercion rules

| Front-matter | Rule | On violation |
|---|---|---|
| `sequence` absent / `None` / blank / whitespace | no membership | unit built, no `_SeqMember` (FR-004) |
| `sequence` non-string | unusable | `InvalidFrontmatterError` → card **skipped**, reason recorded, build continues (FR-007) |
| `order` absent / `None` | member placed **last** in its sequence, slug-ordered | soft (FR-005) |
| `order` non-integer (incl. `bool`, float, str, list) | unusable | `InvalidFrontmatterError` → card **skipped** (FR-007) |
| `order` present, `sequence` absent | `order` ignored | soft `UnknownKey(path, "order")`, no membership (FR-008) |

`_coerce_sequence` mirrors `_resolve_setting`; `_coerce_order` mirrors
`_coerce_year` (rejects `bool`). Both raise **before** any state mutation (D7).

## Member ordering (FR-005 / FR-006) — the total sort key

```python
def _member_sort_key(m: _SeqMember) -> tuple[int, int, str]:
    if m.order is None:
        return (1, 0, m.unit_slug)        # order-less: last, by slug
    return (0, m.order, m.unit_slug)       # explicit: by order, ties by slug
```

Applied as `sorted(group, key=_member_sort_key)`. Total order → identical member
tuple across builds (SC-003/SC-004).

## Assembly algorithm (the "second step")

After `_map_single_dir` over `outline/units/` returns:

1. Group the collected `_SeqMember` list by `seq_slug` into an insertion-ordered
   dict (insertion order = sorted-glob order, so deterministic).
2. For each group:
   a. `ordered = sorted(group, key=_member_sort_key)`.
   b. `name = group[0].seq_name` (first card in glob order to name the slug — D4).
   c. `units = tuple(m.unit for m in ordered)`.
   d. `seq = NarrativeSequence(uri_base=…, name=name, units=units)`.
   e. append `MappedEntity(entity=seq, relpath=ordered[0].relpath, key_lines={})`
      to `result.mapped` (file-level provenance — D5).

Empty member list → no groups → no entity appended → identical graph (FR-011).

## Provenance (FR-010)

Each `NarrativeSequence` `MappedEntity` flows through the existing
`build_provenance` → `crm:E13_Attribute_Assignment` path unchanged:

- identity assertion (`source_field=None`) → file-level `relpath`.
- one assertion per member (`source_field="units"`); with `key_lines={}` each
  resolves to file-level `relpath` (no `:line`) — the minted-`NarrativeFunction`
  precedent (D5).

## State transitions

None — entities are immutable (frozen Pydantic). A build is a pure function of
the source tree.
