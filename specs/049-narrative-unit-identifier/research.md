# Research: Unify the narrative-unit identifier (iteration 049, DEBT-017)

All decisions resolve cleanly from the existing code; there is no NEEDS
CLARIFICATION. The single open product question (format) was settled in the spec's
Clarifications (2026-06-24): the human authored name **alone**.

## D1 — Where does the human name come from? (FR-003)

**Decision**: Resolve the name from the **derived graph** via the
`(uri, rdfs:label, name)` triple iteration 035 emits
(`golem/modules/narrative.py:50`), queried with an `OPTIONAL` clause added to
`queries.load_orphan_units`.

**Rationale**: The orphan rule already runs SPARQL `NOT EXISTS` over the loaded
graph to detect orphans, so the graph is in hand; the label is one extra
`OPTIONAL` triple pattern on the **same** query — no second round trip, no rebuild,
no outline cross-reference. The spec forbids reconstructing the name from the slug
(slugification is lossy and irreversible) and forbids crossing to the outline.

**Alternatives considered**:
- *Reconstruct the name from the slug* — rejected: slugification (`'La fechoría en
  el muelle'` → `la-fechoria-en-el-muelle`) drops case, accents, and spaces; it is
  not invertible (FR-003 forbids it).
- *Cross-reference `ValidationContext.outline()` for the name* (the path
  `_unresolved_roles` uses) — rejected: the orphan rule has **no**
  `UnresolvedReference`; pulling in the outline `MapResult` just to read a name the
  graph already carries is gratuitous coupling. The graph is the right, already-open
  source (FR-003).
- *A separate `load_unit_label(indexer, uri)` lookup per orphan* — rejected as the
  primary path: it issues N extra queries for the N orphans and duplicates the
  prefix/seam boilerplate. Folding the label into the existing single query is
  strictly less code and one round trip. (The user hint allowed either; the
  single-query form wins on simplicity and determinism.)

## D2 — Shape of `load_orphan_units`'s return (FR-003/FR-004)

**Decision**: Change the return from `list[str]` to `list[tuple[str, str | None]]`
— each pair is `(unit_uri, label_or_None)`. `label` is `None` exactly when the unit
carries no `rdfs:label` (the defensive FR-004 floor). Determinism is preserved:
results are sorted by URI; when (defensively) a unit carries multiple labels, the
lexicographically smallest is taken so the pair is byte-stable.

**Rationale**: `load_orphan_units` is called from **one** site
(`narrative_structure._orphan_beats`) — verified by grep, no other caller in `src/`
or `tests/` — so widening its return type is safe and local. Pairing keeps the URI
(needed for `resolve_source` and for the slug fallback) alongside the label in one
ordered structure.

**Alternatives considered**:
- *Keep `list[str]`, add a second helper* — rejected (D1): more queries, more
  boilerplate.
- *Return `list[OrphanUnit]` dataclass* — rejected: a two-field tuple at one call
  site does not earn a named type; the existing module returns plain tuples/sets
  (`load_relations`, `EventInterval` is the only dataclass and it carries three
  fields with behavior). YAGNI.

## D3 — The single shared formatting point (FR-005)

**Decision**: A module-level pure function in `narrative_structure.py`:

```python
def _unit_identifier(name: str | None, slug: str) -> str:
    """The printed identifier for a G9 unit: the human name when present, else the slug."""
    return name if name else slug
```

Both rules call it:
- `_orphan_beats`: `_unit_identifier(label, slug)` where `slug = unit_uri.rsplit("/", 1)[-1]`.
- `_unresolved_roles`: `_unit_identifier(ref.entity, slug)` where `slug` is derived
  the same way from the unit URI. `ref.entity` is always present, so the result is
  `ref.entity` — the rule's output is **unchanged** (FR-002), now flowing through the
  one shared point.

**Rationale**: FR-005 requires structural consistency — divergence impossible by
construction, not asserted. One helper, two call sites mirrors the iteration-048
`anchor_handle` precedent (`factual_anchor`/`status` cannot drift, DEBT-015). Both
call sites live in `narrative_structure.py`, so a module-level function there is the
minimal "single point"; no new module is justified (Scope discipline).

**Alternatives considered**:
- *Format independently in each rule and assert equality in a test* — rejected:
  FR-005 explicitly forbids "two independently-built strings that merely happen to
  match"; consistency must be structural.
- *Put the helper in `queries.py` or a new `_narrative_identity.py`* — rejected: the
  consumers are both in `narrative_structure.py`; a cross-module helper for one
  file's two private methods is premature extraction (contrast 048, where
  `anchor_handle` is shared across *two different modules* `factual_anchor` and
  `status`, which justified `io/_research_identity.py`). Here one module owns both
  call sites.

## D4 — Why `name if name else slug` (not `name is not None`) (FR-004)

**Decision**: Treat an empty-string label the same as a missing one — fall back to
the slug. `name if name else slug` covers both `None` and `""`.

**Rationale**: An empty `rdfs:label` is as useless an identifier as no label; the
defensive floor should never print an empty `''`. Iteration 035 guarantees a
non-empty authored name in the normal path, so this only ever bites the
impossible-by-construction case — exactly what FR-004 calls a defensive floor.

## D5 — Which oracles change, verified empirically (FR-008)

**Decision**: Exactly the orphan-beat *message identifier* oracles flip from slug to
human name; counts, severities, sources, and the gate stay byte-identical (SC-003).

Concretely (to be confirmed by `uv run pytest`, FR-008):
- `tests/validation/test_narrative_structure.py:51` —
  `assert "orphan-beat" in finding.message` → assert the human **name** `"Orphan
  Beat"` (the `UnitSpec("orphan", "Orphan Beat")` card; the URI tail is
  `orphan-beat`, the name is `Orphan Beat`). Line 55's negative assertion
  (`"anchored-beat" not in`) still holds for the non-orphan and needs no change.
- `tests/fixtures/tiny-quest/expected-narrative.md:70` —
  `orphan_beats[0].unit: omen-beat` → `unit: "Omen Beat"` (the human name). The E2E
  `test_validate_reports_the_orphan_beat` asserts `entry["unit"] in match["message"]`
  and rides the oracle, so flipping the oracle value carries the assertion. The
  comment "the unit slug, as it appears in the message" updates to "the unit's human
  name".
- A **new** unit test pins FR-004: an orphan unit whose graph carries no
  `rdfs:label` falls back to the slug in the message (built by injecting a `G9`
  type triple without the label, or asserting `_unit_identifier(None, slug) == slug`
  / `_unit_identifier("", slug) == slug` directly).

**Outline fixtures are NOT edited** (FR-008): the authored `06-omen.md` card already
carries `name: "Omen Beat"`; only the *expected* oracle value changes.

**Rationale**: The empirical sweep is mandatory because the slug↔name equality for
"happens to equal its slug" units (spec Edge Cases) means some oracles might not move;
`uv run pytest` is the authority on which assertions actually change.

## D6 — Scope confirmation (Assumptions sweep)

The debt class — *one validator naming a single entity-kind two ways across its
rules* (doctrine §4) — has one remaining instance: `narrative_structure`. `temporal`
and `factual_anchor` were unified in iteration 048 (DEBT-015, closed); the prose
validators each name their entity one consistent way. No other instance is left
unswept. This iteration touches neither `factual_anchor`/`temporal` locators
(iteration 048), the move-3 semantic work, nor any message outside
`narrative_structure`.
