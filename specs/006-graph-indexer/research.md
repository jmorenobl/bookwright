# Phase 0 — Research & Decisions

Iteration 6 builds directly on delivered code (iteration-5 GOLEM model on the
current branch; iteration-2 `Manifest`). Research here reconciles the spec with
that delivered reality and pins the frontmatter→graph mapping against the
**frozen GOLEM ontology** (`src/bookwright/resources/schemas/golem-1.1/golem.ttl`).

> **Revision note.** An earlier draft of R1 chose to *drop* scalar character
> attributes (`born`/`died`/`features`) on the false premise that the frozen
> vocabulary had no home for them. Inspection of `golem.ttl` disproved that: the
> ontology models all of them explicitly. R1 below is the corrected decision.
> The earlier choice would have produced a near-empty graph, failed the spec's
> own motivating query ("characters born before 1850"), and blocked iteration
> 10's validators — a shortcut with a larger downstream cost.

---

## R1 — Frontmatter → triples, using only frozen GOLEM/CIDOC terms

**Decision**: Map every documented frontmatter key to the term the frozen
ontology already defines for it. Nothing is dropped; nothing new is minted.
SC-001 ("zero predicates or classes absent from the frozen GOLEM vocabulary")
holds because every class/predicate below is a member of `frozen_terms()`.

**Character (`bible/characters/<f>.md` → `golem:G1_Character`)**

| Key | Frozen modeling (all terms ∈ `frozen_terms()`) |
|---|---|
| `name` | identity: slug → URI (iteration-5), the `rdf:type` assertion |
| `narrative_roles[]` | one `golem:G11_Narrative_Role` per role; `Character —edns:plays→ role` |
| `features[]` (free text) | one `golem:G17_Character_Feature` per item; `Character —golem:GP0_has_feature→ feature`; text via `rdfs:label` |
| `born` / `died` (year) | biographical `golem:G17_Character_Feature`, `crm:P2_has_type` an `crm:E55_Type` individual (`birth`/`death`); year via `crm:P43_has_dimension → crm:E54_Dimension —crm:P90_has_value→ "YYYY"^^xsd:gYear` |

This is the ontology's own prescription: `G17_Character_Feature` is documented as
covering *"biographical (e.g., birth, death), physical, and psychological
features… specified using crm:E55_Type,"* and the `G1_Character` class carries
OWL restrictions on `edns:plays → G11_Narrative_Role` and `golem:GP0_has_feature →
G2_Feature`. `crm:P90_has_value` (the ontology's sole datatype property) is the
frozen literal carrier; its domain is `E54_Dimension`, hence the
feature→dimension→value chain.

**Events (`bible/timeline.md`) and relationships (`bible/relationships.md`)**
reuse the iteration-5 `NarrativeEvent` / `SocialRelationship` classes and their
existing `dlp:participant` edges (resolved to character URIs).

**Rationale**
- The whole reason design § 16 fixes GOLEM as the ontology is that it is a
  *narrative* ontology with exactly these affordances. Using them is the
  intended path, not an extension.
- Honors FR-010 ("frontmatter → the triples defined by the corresponding GOLEM
  module"), FR-011/SC-006 (real attributes now each carry provenance), and the
  spec's motivating queries (US2: "characters born before 1850" becomes
  answerable via the dimension value).
- Unblocks iteration 10: the temporal validator can read birth/death/event
  years; character-presence can read the role/feature graph.

**Alternatives considered**
- *Drop scalars (identity + provenance only)* — rejected: empties the graph of
  its narrative content, breaks US2's example query, and defers a model decision
  that iteration 10 hard-requires (the shortcut the user flagged).
- *Invent `golem:born` / literal triples outside the closure* — rejected:
  violates SC-001 and reintroduces the ad-hoc-vocabulary drift the frozen
  ontology exists to prevent. Unnecessary, since frozen terms already fit.

**Consequence (see R1a)**: the iteration-5 typed model had to grow to carry
these attributes.

---

## R1a — Extend the iteration-5 GOLEM typed model (DONE — completed in iteration 5, on `main`)

**Decision (resolved):** the model extension was implemented as a **completion of
iteration 5** (not in this branch), merged to `main`, and iteration 6 now
*consumes it as-is*. The typed model remains the single source of RDF emission.

**As shipped on `main`** (see data-model §0 for the consumed surface):
- `namespaces.py` gained the `EDNS` namespace
  (`…/ExtendedDnS.owl#`, distinct from the DOLCE-Lite `DLP`), the predicate
  constants `HAS_FEATURE`/`PLAYS`/`HAS_TYPE`/`HAS_DIMENSION`/`HAS_VALUE`, and
  `CLASS_IRI` entries for `G2_Feature`/`G17_Character_Feature`/`E54_Dimension`/
  `E55_Type` — all ∈ `frozen_terms()`.
- `modules/feature.py` added `CharacterFeature` (free-text **or** biographical),
  `CharacterRole` (G11, character-scoped — *not* the top-level `NarrativeRole`),
  and `Dimension` (E54, emitting `xsd:gYear` via a BCE/short-year-safe
  `gyear_literal`). These are excluded from the `CONCEPTS` registry.
- `Character` gained `born: int|None`, `died: int|None`,
  `features: tuple[str, ...]`, `narrative_roles: tuple[str, ...]`, and
  **materializes** the feature/role/dimension nodes at construction (deduped,
  character-scoped URIs). A character with none of the four emits only its
  `rdf:type` assertion — identity-only behaviour preserved.

**Verification (this branch, post-rebase on `main`)**: all four gates green —
`ruff`, `ruff format`, `mypy --strict` (100 files), `pytest` 437 passed, 98%
coverage. The iteration-5 closure test was extended to cover every new term.

**Implication for this iteration**: the bible mapper does **not** build
feature/role/dimension nodes — it passes frontmatter scalars/tuples to
`Character(...)` (and the other constructors) and lets the model emit. This is
simpler than the original sketch and is reflected in data-model §0/§3 and
`contracts/bible-format.md`.

---

## R2 — Bible directory layout (resolves FR-009 vs. design § 7 / init scaffold)

**Decision**: The parser reads exactly what `bookwright init` scaffolds (design
§ 7):

| Path | Cardinality | GOLEM concept |
|---|---|---|
| `bible/characters/*.md` | one entity per file | `Character` |
| `bible/settings/*.md` | one entity per file | `Setting` |
| `bible/timeline.md` | one collection file, many items | `NarrativeEvent` |
| `bible/relationships.md` | one collection file, many items | `SocialRelationship` |

**Rationale**: `bookwright init` already creates `bible/characters/` and
`bible/settings/` as directories and `bible/timeline.md` + `bible/relationships.md`
as single files
([resources/project/bible](../../src/bookwright/resources/project/)). FR-009's
"four directories" contradicts the toolkit's own output; the code is ground
truth, so FR-009 is corrected. Keeps the blast radius out of iterations 4 and 7.

**Alternative considered**: *All four as directories (FR-009 literal)* —
rejected: would force re-scaffolding `init` for no functional gain.

---

## R3 — Frontmatter parsing dependency

**Decision**: Add `pyyaml>=6.0` to `[project].dependencies`; parse frontmatter by
stripping a leading `---\n … \n---\n` fence and `yaml.safe_load`-ing the YAML
block, tracking each top-level key's 1-based line for provenance locators.

**Rationale**: No declared runtime dependency parses YAML. `pyyaml` is the
ubiquitous, audited choice and is already resolved transitively in `uv.lock`.
Per Principle II this is a **MINOR** constitution amendment (1.1.0 → 1.2.0) plus a
matching design § 14.1 update — the sanctioned path. A hand-rolled YAML parser is
rejected (author prose contains colons/quotes/unicode; partial parsing is a
correctness/security liability). `python-frontmatter` adds more surface than a
~10-line fence split needs.

**Prerequisite**: the amendment task lands before any code imports `yaml`;
`commands/check.py::RUNTIME_MODULES` gains `"yaml"`.

---

## R4 — Indexer Protocol & registry shape

**Decision**: `indexers/base.py` defines `Indexer` as a `typing.Protocol` with
the six design-§ 12.1 methods: `load`, `save`, `add_triple`, `query`,
`construct`, `count`. `add_triple` accepts rdflib terms
(`URIRef | Literal | str | int | float`) so typed `to_triples()` output is fed in
losslessly. `indexers/__init__.py` holds `INDEXER_REGISTRY` (`{"rdflib":
RdflibIndexer}`) and `resolve_indexer(name)`, which raises
`UnknownIndexerError(name, available=...)` for an unregistered engine.

**Rationale**: mirrors the delivered `INTEGRATION_REGISTRY` plugin pattern
(Principle V intent); satisfies FR-005/007/008. `GrafeoIndexer` stays deferred
(v0.3 / Principle X). `Protocol` over ABC per design § 12.1 — structural
conformance keeps a future engine decoupled.

---

## R5 — Where serialization lives

**Decision**: `RdflibIndexer` owns an internal `rdflib.Graph`, binds the short
prefixes via `golem.namespaces.bind_prefixes` at construction, and serializes in
`save()` (`format="turtle"`). The build command feeds `entity.to_triples()` into
`engine.add_triple` and calls `engine.save(graph_path)`. No separate
`io/turtle.py` (would duplicate `golem.serialize.to_turtle` and split
prefix-binding ownership).

**Rationale**: FR-006 (engine serializes + counts) and FR-015 (short prefixes)
are guaranteed inside the engine regardless of which engine is selected; DRY.

---

## R6 — Provenance granularity (FR-011, SC-006)

**Decision**: Emit one `AttributeAssignment` per derived **attribute assertion**
(each feature, each role, each birth/death feature, each event/relationship
participation), with `target = the character/entity URI`, `attribute = the
feature/role/event URI`, `source = "<relpath>"` or `"<relpath>:<line>"` when the
originating frontmatter key is locatable. The entity's own identity assertion
also carries a file-level assignment.

**Rationale**: under the corrected R1 there *are* real attribute nodes, so
provenance attaches to each one — satisfying SC-006 ("100% of derived attribute
assertions have an associated Attribute Assignment naming their source file")
with genuine granularity (one assignment per assertion, not per sub-triple). Line precision is best-effort from the
frontmatter reader's `key_lines`. `uuid7` identity reused from iteration 5.

---

## R7 — Build fault model & exit codes (FR-012/013/014, US5)

**Decision**:
- **Missing `bible/` or `manuscript/`** → `MissingDirectoryError`, fail before
  writing, exit non-zero, no partial output.
- **Invalid frontmatter** → skip the file, record `(path, reason)`, continue; a
  build with ≥ 1 skip exits with a distinct non-zero code (`4`) so it is not
  mistaken for clean. JSON report keeps `status:"ok"` with a non-empty `skipped`.
  Clean build exits `0`.
- **Slug collision within a type** → hard `SlugCollisionError` naming the
  identifier and both paths, exit non-zero, no graph written.
- **Unknown frontmatter key** → ignored, recorded in the report (not a failure).
- **Empty bible** → success, prefix-only `bible/graph.ttl`, zero entities.

**Rationale**: matches the spec edge-case table and US5; the dedicated skip exit
code operationalizes "signals this in its exit status / report." Collisions are
detected per `(type, slug)` before serialization using the iteration-5 slug.

---

## R8 — Query behaviour & project location (FR-016, edge cases)

**Decision**:
- Locate the project by walking up from `cwd` for `manifest.toml`
  (`io/project.py::find_project_root`); none → `ProjectNotFoundError`, non-zero.
- `graph query` with no `bible/graph.ttl` → `GraphNotBuiltError` ("run graph
  build first"), non-zero.
- **Valid query, no matches** → exit 0, `{"status":"ok","results":[],"count":0}`.
- **Invalid SPARQL** → `InvalidQueryError`, non-zero, **no partial rows**;
  `--json` emits `{"status":"error", ...}`.
- v0 supports `SELECT` at minimum; `ASK`/`CONSTRUCT` follow the same contract.

**Rationale**: encodes FR-016 and the query edge cases; walking up for
`manifest.toml` matches the "run from project root" assumption while tolerating a
nested cwd.

---

## Cross-cutting confirmations (no open questions)

- **Manuscript**: presence required (FR-012); v0 does **no** prose mining —
  extraction is bible-frontmatter-driven. Read only to confirm presence (and,
  later, resolve line locators). Matches Out-of-Scope / Assumptions.
- **Cache**: v0 always full-rebuilds; `.bookwright/cache/` is not written;
  `--force` is accepted as "ignore any cache" (a no-op today), preserving
  Principle I (no non-rebuildable store) and forward compatibility.
- **JSON contract**: reuse the single-line
  `json.dumps(payload, separators=(",", ":"))`-to-stdout pattern from
  [version.py](../../src/bookwright/commands/version.py) /
  [init/envelope.py](../../src/bookwright/commands/init/envelope.py); human
  progress to `Console(stderr=True)` (Principle IX; this feature's spec is
  explicit about stderr).
