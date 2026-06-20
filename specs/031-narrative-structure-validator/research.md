# Research: Narrative-structure continuity validator

All open questions were resolved in the spec's clarification session
(2026-06-20); this file records the **technical** decisions the plan rests on,
each grounded in the existing code read during planning.

## D1 — Discovery & registration: nothing to register by hand

**Decision**: place the validator class at module level in
`src/bookwright/validation/validators/narrative_structure.py`; it is discovered
automatically.

**Rationale**: `registry._discover_builtins()` iterates the `validators` package
with `pkgutil` and collects every module-level object that has `name`,
`severity_default`, and `validate` (`_looks_like_validator_class`). A new
conforming class is picked up with **zero** edits to `registry.py` — FR-002's
"no hand-registration" is the actual mechanism. (The `/speckit-plan` hint's
"regístralo en registry.py" is loose phrasing; the registry is auto-discovery.)
`resolve_active` then includes it in the default set and honours
`[validators] enabled/disabled` by name → US3 / FR-010 for free.

**Alternatives rejected**: an `entry_points` or manual map — explicitly out
(research D2 of the original validation subsystem; FR-002).

## D2 — Validator name & severity

**Decision**: `name = "narrative_structure"`, `severity_default = Severity.warning`.

**Rationale**: snake_case named for what it checks, like every built-in
(`setting_continuity`, `temporal`, `focalization`) — fixed in spec Clarifications
(drives FR-001/FR-010). `warning` matches every LLM-free heuristic structural
check (`setting_continuity` is `Severity.warning`, never gates CI) — spec
Clarifications, FR-013. The runner gate (`ValidationReport.failed`) trips only on
`error`, so `warning` findings never break CI.

## D3 — Rule a (orphan beat): SPARQL `NOT EXISTS` over the graph

**Decision**: add `load_orphan_units(indexer) -> list[str]` to
`validation/queries.py`, returning the URIs of every `G9_Narrative_Unit` with no
incoming `dlp:proper-part`:

```sparql
SELECT ?unit WHERE {
  ?unit a golem:G9_Narrative_Unit .
  FILTER NOT EXISTS {
    ?seq a golem:G7_Narrative_Sequence .
    ?seq dlp:proper-part ?unit .
  }
}
```

**Rationale**: `NarrativeSequence` emits exactly one `dlp:proper-part` triple per
member unit (`golem/modules/narrative.py`; `PROPER_PART = DLP["proper-part"]`), so
"member of some sequence" is precisely "has an incoming `dlp:proper-part`".
`queries.py` already centralises read-only graph projections behind `indexer.query`
and its `_PREFIXES`; the validator never touches rdflib directly (matches the
`temporal` precedent). The `_PREFIXES` block lacks `dlp`, so the only edit is to
add `("dlp", str(DLP))` (import `DLP` from `golem.namespaces`) — embedding the full
IRI would also work but the prefix keeps the query readable like the others.

**Alternatives rejected**: enumerating sequences in Python and diffing member sets
— re-implements what one `NOT EXISTS` states declaratively and bypasses the
`Indexer` seam.

## D4 — Naming the orphan unit in the message (graph-derived, no `outline()` dependency)

**Decision**: name the orphan by the **slug** taken from its URI localname; cite
the card via `resolve_source(indexer, unit_uri)`.

**Rationale**: a `NarrativeUnit` is a plain `SluggedEntity` — `to_triples()` emits
only `rdf:type` + its `cross_refs` (`functions`/`roles`), **no `rdfs:label`** (only
`CharacterFeature`/`CharacterRole` override to emit a label — `golem/base.py`).
So the graph carries no display name; the URI localname (the slug) is the only
graph-native identifier. Keeping US1 to **SPARQL + provenance only** preserves its
status as the independently-shippable P1 MVP that does **not** depend on the US2
`outline()` accessor (spec: US1 is "answered purely by SPARQL over the derived
graph"). The `file:line` locator points at the card, where the author reads the
full authored name, so no information is lost.

**Alternatives rejected**: (a) reading the name from `outline()` — would couple
the P1 rule to the P2 accessor, weakening "purely SPARQL"; (b) adding `rdfs:label`
to unit emission — changes existing ingestion (out of scope) and is unnecessary.

## D5 — Rule c (unresolved role): the cached `ValidationContext.outline()` accessor

**Decision**: add `outline() -> MapResult` to `ValidationContext`, mirroring
`bible()`, memoised on a new `_outline` sentinel field:

```python
def outline(self) -> MapResult:
    if self._outline is _UNSET:
        from bookwright.io.bible import map_bible
        from bookwright.io.outline import map_outline
        bible_dir = self.root / self.manifest.paths.bible
        result = map_bible(self.root, bible_dir, self.uri_base)
        map_outline(self.root, self.root / self.manifest.paths.outline, self.uri_base, result)
        self._outline = result
    return cast("MapResult", self._outline)
```

**Rationale**: `map_outline._resolve_roles` appends a structured
`UnresolvedReference(path, entity=unit-name, name=role)` for every `roles:` slug
that matches no character role node (`io/outline.py`) — the single source of truth
for "does this role resolve". But `ValidationContext.bible()` runs `map_bible`
**only**, whose `unresolved_references` never contains the outline pass's role
misses; only the combined `map_bible`→`map_outline` pipeline (as in
`commands/_graph.py build_project_graph`) produces them, and `map_outline` needs
the character pass's `result.roles_index`, so it cannot run standalone. The
accessor runs that exact combined pipeline once per run and returns the combined
`MapResult`. This reuses the established read-once-per-run accessor pattern (no new
mechanism), keeps one source of truth for role resolution, re-reads no cards by
hand (FR-006), adds no class/property (Principle X), and writes nothing (FR-008).

**Vocabularies omitted on purpose**: `outline()` calls `map_bible`/`map_outline`
without `greimas`/`propp`. The active vocabularies only add `crm:P2_has_type`
typing triples (iteration 030); they do **not** affect `unresolved_references`. So
omitting them keeps the accessor identical-in-effect to `bible()` (which also omits
`greimas`) for the data US2 reads, with no behavioural difference. Documented so a
future reader does not "fix" it by threading vocabularies through.

**Alternatives rejected**: (a) re-parsing cards in the validator — forks role
resolution, violates FR-006's single-source rule; (b) reading the on-disk graph
for unresolved refs — impossible, the graph carries no edge for a soft-miss (spec
Assumptions); (c) calling `map_outline` on the cached `bible()` result in place —
would mutate the shared bible `MapResult` other validators read; a fresh result is
clean.

## D6 — Discriminating outline role misses from bible misses

**Decision**: filter `outline().unresolved_references` to records whose `path` is
under `"{outline}/units/"` (where `outline = manifest.paths.outline.rstrip("/")`).

**Rationale**: `UnresolvedReference` is shared — `map_bible` also emits it for a
`participants:` member naming no character or a location `setting:` naming no
setting (`io/report.py`). The validator must report **only** the outline role
misses. The path prefix is a collision-free discriminator: `_resolve_roles` is
only reached from `_build_unit` in the outline pass, whose cards are walked from
`outline_dir/"units"` and carry relpaths like `outline/units/foo.md`; no bible miss
ever carries that prefix. (Filtering by "entity is a built unit name" is a weaker
discriminator — a character and a unit could share a name — so the path prefix is
preferred.)

## D7 — Naming the card location for an unresolved-role finding (FR-004)

**Decision**: recover `file:line` via `resolve_source(indexer, unit_uri)`, where
`unit_uri` comes from a `{name: uri}` map built from `outline().mapped`
(`NarrativeUnit` entities); fall back to the `UnresolvedReference.path` (the card
relpath, no line) when the unit is absent from the graph.

**Rationale**: FR-004 mandates the existing `E13`→source provenance path, not a
re-derived path. `commands/_graph.py` runs `build_provenance` over **all**
`result.mapped` including outline units, so the unit's identity assertion (and its
`file:line`) is in `graph.ttl`. Mapping unit **name** (`ref.entity`) → unit URI via
`outline().mapped` (whose URIs match the graph by construction — same `uri_base`,
same slug) lets `resolve_source` return the card locator. The fallback to
`ref.path` (a real authored relpath, never invented) keeps the finding useful if
the graph is stale/unbuilt — still satisfying "never a bare or invented path".

## D8 — Rules (b) and (d): not implemented (assert the non-finding)

**Decision**: emit no order-coherence finding and no empty-sequence finding; add a
test asserting a sequence with an `order:` gap/duplicate yields **no** order-related
finding (FR-007).

**Rationale**: per spec Clarifications/Edge Cases/Out of Scope — the per-card
`order:` is consumed at sequence assembly and **not** serialized to the graph
(`io/outline.py _member_sort_key`: member order is a tuple, no queryable ordinal),
so it is not SPARQL-citable; and a *gap* in `order:` is legitimate sparse numbering
(10/20/30), not an incoherence. A memberless sequence is never minted by
`_assemble_sequences` (it only mints a `G7` for a non-empty group), so rule (d) has
no reachable input. Implementing either would validate against a state the system
never produces or false-positive on ordinary authoring.

## D9 — Determinism (FR-008 / SC-005)

**Decision**: rely on the runner's existing total-order sort + dedup; within the
validator, iterate orphan URIs and unresolved references in a sorted order.

**Rationale**: `runner.sort_key` already imposes a byte-stable total order
(validator, severity desc, source, message, triples) and dedups identical
`Violation`s. The validator additionally sorts its own outputs (orphan units by
URI; unresolved references by `(path, entity, name)`) so the pre-sort list is
itself stable, matching the `setting_continuity`/`temporal` precedent.

## D10 — Test graph builder (outline-aware)

**Decision**: extend `tests/validation/conftest.py` additively — a `units=` knob on
`write_project` (writes `outline/units/*.md` cards) and an outline-aware indexer
builder that runs `map_bible`→`map_outline`→`build_provenance` (mirroring
`build_project_graph`) into a fresh `RdflibIndexer`.

**Rationale**: the existing `build_indexer` runs `map_bible` only, so it produces no
`G9/G7` triples and no outline provenance — US1's SPARQL would find nothing and
US2's `resolve_source` would have no locator. The new builder is the test analogue
of the real pipeline, keeping fixtures faithful to what `bookwright graph build`
writes to `graph.ttl`. Additive so every existing validator test is untouched
(FR-011).
