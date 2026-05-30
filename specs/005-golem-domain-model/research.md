# Phase 0 Research: GOLEM Domain Model

All decisions below are resolved — there are no remaining `NEEDS CLARIFICATION`
markers. The three clarification questions in the spec (slug rule, per-concept
segments, reified-entity naming) are already settled; this document resolves the
*technical* unknowns the plan surfaced.

---

## D1 — Model representation: frozen Pydantic v2 vs dataclasses

**Decision**: Frozen Pydantic v2 `BaseModel` (`model_config =
ConfigDict(frozen=True, extra="forbid", strict=True)`) for every concept,
subclassing a shared `GolemEntity` base.

**Rationale**:
- The repo already standardizes on Pydantic v2 with `extra="forbid",
  strict=True` (`core/manifest.py`). Matching it keeps validation behavior and
  mypy-strict ergonomics uniform.
- `frozen=True` makes FR-007 (identifier immutability) structural rather than
  defensive: attempting to reassign `name` raises `ValidationError`, and because
  the URI is computed once at construction it can never drift. US1 scenario 5
  ("attempt to change the canonical name → identifier does not change") is
  satisfied by construction.
- Validators (`field_validator`) give a clean home for the empty-slug rejection
  (FR-006) at construction time.

**Alternatives considered**:
- *Plain `@dataclass(frozen=True)`*: lighter, but loses the field validation,
  the `extra="forbid"` strictness, and consistency with `core/`. Rejected.
- *Mutable model + cached `uri`*: would require guarding against post-hoc name
  edits. Frozen is simpler and safer. Rejected.

---

## D2 — Slug generation

**Decision**: `make_slug(name)` in `golem/slug.py` calls `python-slugify`'s
`slugify()` in its **default** mode (lowercase, ASCII transliteration, single-hyphen
separators, trimmed). If the result is empty, raise `EmptySlugError`.

**Rationale**: Default `python-slugify` already implements exactly the rule the
spec fixed in clarification and design § 4.5 documents: `José Peña → jose-pena`,
`La caída → la-caida`, runs of separators collapse, edges trimmed, output is
lowercase ASCII. Relying on the library default keeps the rule deterministic
(FR-005) and avoids re-implementing transliteration. Empty output is the only
failure mode and is rejected loudly (FR-006, edge case).

**Alternatives considered**: hand-rolled `unicodedata.normalize('NFKD', …)` +
regex — more code, same outcome, more bug surface. Rejected. Preserving accents
(percent-encoded IRIs) was explicitly rejected in design § 4.5 for SPARQL/FS
portability.

**Verification**: `tests/golem/test_slug.py` asserts the spec's worked examples,
idempotence, and that a punctuation-only name raises `EmptySlugError`.

---

## D3 — Identity token for Attribute Assignment

**Decision**: `AttributeAssignment` uses `uuid_utils.uuid7()` rendered as its
canonical string for the `{base}assertion/{uuid}` token. The UUID is generated
once at construction and frozen.

**Rationale**: FR-013 requires time-ordered, collision-free tokens that sort in
creation order. UUIDv7 embeds a millisecond timestamp prefix, so lexical/temporal
ordering coincides (US3 scenario 4). `uuid-utils` is the approved package
(Constitution II; CLAUDE.md notes `uuid-utils`, **not** `uuid7`).

**Alternatives considered**: monotonic counter (not stable across processes),
UUIDv4 (no ordering). Rejected.

---

## D4 — URI composition

**Decision**: `uri = URIRef(f"{uri_base}{segment}/{token}")`, where `uri_base`
is the caller-supplied project namespace base (guaranteed by iteration 2 to be an
absolute http/https URI ending in `/`), `segment` is a class-level constant per
the FR-004 table, and `token` is the slug (named concepts) or the uuid7
(assertions). No re-validation of `uri_base` (Assumptions). Concatenation is
direct after the trailing slash.

**Per-concept segment + token** (FR-004, matches design § 4.5):

| Concept | GOLEM class local name | Segment | Token |
|---|---|---|---|
| Character | `G1_Character` | `character` | slug |
| Object | `G16_Object` | `object` | slug |
| Event | `G5_Narrative_Event` | `event` | slug |
| Psychological State | `G3_Psychological_State` | `psychological-state` | slug |
| Setting | `G12_Setting` | `setting` | slug |
| Narrative Location | `G13_Narrative_Location` | `location` | slug |
| Social Relationship | `G4_Social_Relationship` | `relationship` | slug |
| Relationship Role | `G6_Relationship_Role` | `relationship-role` | slug |
| Narrative Unit | `G9_Narrative_Unit` | `narrative-unit` | slug |
| Narrative Function | `G10_Narrative_Function` | `narrative-function` | slug |
| Narrative Role | `G11_Narrative_Role` | `narrative-role` | slug |
| Narrative Sequence | `G7_Narrative_Sequence` | `narrative-sequence` | slug |
| Attribute Assignment | `E13_Attribute_Assignment` (CIDOC-CRM) | `assertion` | uuid7 |

---

## D5 — Namespaces and the frozen ontology IRI

**Decision** (confirmed by inspecting the upstream Turtle):

| Prefix | IRI | Source |
|---|---|---|
| `golem` | `https://w3id.org/golem/ontology#` | ontology `@prefix :` / `gc:` |
| `crm` | `http://www.cidoc-crm.org/cidoc-crm/` | hosts `E13_Attribute_Assignment` & the P-properties |
| `dlp` | `http://www.ontologydesignpatterns.org/ont/dlp/` | the ontology's DOLCE layer (DOLCE-Lite-Plus) |
| `rdf` | `http://www.w3.org/1999/02/22-rdf-syntax-ns#` | rdflib built-in |
| `rdfs` | `http://www.w3.org/2000/01/rdf-schema#` | rdflib built-in |
| `xsd` | `http://www.w3.org/2001/XMLSchema#` | for typed literals (e.g. source paths) |

**Note on "DOLCE/DUL"**: the spec/FR-010 names "DOLCE/DUL", but the frozen GOLEM
ontology actually imports the **DOLCE-Lite-Plus** layer under
`http://www.ontologydesignpatterns.org/ont/dlp/` (prefix `dlp`), not the newer
`DUL.owl#` namespace. We bind the namespace the *frozen ontology itself
declares* (the source of truth for FR-008/SC-003); the registry is documented as
covering "the DOLCE namespace the frozen ontology uses." This is a labeling
detail, not a semantic divergence, and does not require a spec change.

**Rationale**: `golem/namespaces.py` defines these as `rdflib.Namespace`
constants, a `bind_prefixes(graph)` helper that binds all of them, and a
`CLASS_IRI: dict[type, URIRef]` (or per-class attribute) so each concept knows
its rdf:type target. Hard-coding the IRIs (rather than parsing them out of the
TTL at import time) keeps construction cheap and import side-effect-free; the
frozen TTL is loaded only by the term-closure test and the optional
`validate_terms()` helper.

---

## D6 — Cross-reference predicates (FR-015)

**Decision**: Cross-references between entities are emitted as triples whose
predicates are read from the frozen ontology, never invented. The implementer
greps `golem.ttl` for the relevant object properties and records the chosen IRI
for each link in `data-model.md`. Concretely, the in-scope links and their
predicate source:

- **Social Relationship ↔ participants / roles**: GOLEM relationship properties
  (`G4_Social_Relationship` domain/range properties in the ontology).
- **Narrative Unit ↔ Narrative Sequence / Function / Role**: GOLEM narrative
  properties.
- **Attribute Assignment → target / attribute / premise / source**: CIDOC-CRM
  `P140_assigned_attribute_to` (target), `P141_assigned` (asserted attribute),
  and the GOLEM/CRM "used"/source property for the source reference; premise via
  the property the ontology provides for relating one assignment to a prior one.

**Rationale**: FR-008 mandates closure over the frozen vocabulary. The exact
local names are confirmed against the vendored TTL during implementation (the
file is committed in this same iteration, so this is a deterministic lookup, not
an open question). The term-closure test (SC-003) is the backstop: any predicate
not present in the frozen ontology fails the suite.

**Modeling note**: where a concept needs to *reference* others, fields accept
`GolemEntity` instances or bare `rdflib.URIRef`s and serialize to the linking
triple by the referenced entity's `.uri`. The model does **not** require the
target to be materialized in the same batch (edge case: assignment referencing
an entity with no triples yet).

---

## D7 — Source reference & premise on Attribute Assignment (FR-009)

**Decision**: The source reference (`bible/characters/aparici.md`,
`manuscript/cap-04.md:42`) is stored and serialized **verbatim** as a typed
literal (`xsd:string`) object of the ontology's source/"used" property. The line
locator (`:42`) is part of the opaque path string — the model does not parse or
interpret it (FR-014). `premise` is optional; when `None` it is simply omitted
from the triples (US3 scenario 3).

**Rationale**: The spec treats the source as a path string, not a resolvable
resource. Keeping it a literal preserves it byte-for-byte (US3 scenario 2) and
keeps the model from reaching into the filesystem.

---

## D8 — Serialization & round-trip

**Decision**: `golem/serialize.py` exposes `to_turtle(entities) -> str`: build an
`rdflib.Graph`, call `namespaces.bind_prefixes(graph)`, add every triple from each
entity's `to_triples()`, and `graph.serialize(format="turtle")`. Each entity's
`to_triples()` yields `rdflib` triples directly (an iterable of `(s, p, o)`).

**Round-trip test**: serialize a graph → `Graph().parse(data=…, format="turtle")`
→ assert the parsed graph `isomorphic` to the original (or that every original
triple is present). This proves FR-012/SC-004 (well-formed RDF) and that prefix
binding is lossless (FR-010, US2 scenario 4 — output uses short prefixes).

**Rationale**: rdflib is the approved graph library (Constitution II, design § 16).
Letting rdflib own both serialize and parse guarantees well-formedness and gives
us a free isomorphism check.

---

## D9 — Frozen ontology vendoring & provenance (FR-011, US4)

**Decision**: Vendor the upstream Turtle once, committed into the package:

- **Upstream repo**: `github.com/GOLEM-lab/golem-ontology`
- **File**: `golem/golem_v1-1.ttl`
- **Commit pinned**: `f666128a9a29f39c9f23c96ae1c48023cc8e7898` (the latest commit
  on `main` carrying the machine-readable Turtle; pushed 2026-01-30)
- **Ontology self-version**: `owl:versionIRI https://w3id.org/golem/ontology/v1.1`,
  `owl:versionInfo "1.1"`
- **Destination**: `src/bookwright/resources/schemas/golem-1.1/golem.ttl`
- **Provenance**: `version.json` records `{repository, commit, file,
  version_iri, version_info, retrieved}`; a sibling `VERSION` holds the short
  selector label (`golem-1.1`).

**Selector named after the upstream version (decision)**: the selector,
directory, and manifest default all use `golem-1.1`, matching the ontology's own
`owl:versionInfo "1.1"`. Design § 4.3 establishes that the `golem-{n}/` directory
tracks the *upstream GOLEM version*, so a directory named `golem-1.0` holding
GOLEM 1.1 bytes would be permanent confusion. The earlier `golem-1.0` label
(design § 6/§ 15.2 and the iteration-2 manifest default) was based on the
mistaken assumption that the published version was 1.0; design § 4.3/§ 6/§ 15.2
have been corrected to `golem-1.1`.

**Provenance note (record for reviewers)**: the published GitHub *release tag*
`v1.0` predates the Turtle file — at that tag `golem/` contains only `index.html`,
no machine-readable ontology. The only Turtle serialization lives on `main`. We
freeze the `main` blob at the exact commit above and record it in `version.json`,
satisfying SC-005 (a reviewer can reproduce the exact source bytes from the
record alone).

**Acquisition**: a dev-only `scripts/update-golem-schema.py` performs the fetch +
pin (deterministic generator preferred over hand-copying); the runtime never
fetches over the network (Assumptions).

---

## D11 — Rename `golem-1.0` → `golem-1.1` in iteration-2 artifacts (in scope)

**Decision**: This iteration updates the manifest's `schema_version` default and
the iteration-2 test artifacts that hard-code `golem-1.0`:
- `src/bookwright/resources/templates/manifest.template.toml` → `golem-1.1`.
- `tests/core/test_load_valid.py` (assert + inline TOML) and
  `tests/core/test_build.py` (assert) → expect `golem-1.1`.
- The `tests/core/fixtures/*.toml` that carry `schema_version = "golem-1.0"` as
  filler → `golem-1.1`, for repo-wide consistency (these fixtures exercise *other*
  fields; `schema_version` is an unvalidated free-text stamp per spec 002, so the
  change is mechanical and risk-free).

**Rationale**: keeping the default at `golem-1.0` while the bundled ontology is
`golem-1.1` would reintroduce the exact selector↔content mismatch this decision
exists to remove. Spec 002 explicitly treats `schema_version` as a non-validated
stamp ("serves as a stamp for the GOLEM schema generation"), so no validation
logic changes — only string values and two equality asserts.

**Scope note**: this is the one place the iteration reaches into already-merged
iteration-2 artifacts. It is bounded (one template + a set of test fixtures +
two asserts), purely textual, and leaves spec-002 behavior unchanged. `/speckit-tasks`
must emit explicit tasks for it.

---

## D10 — `version.py` integration

**Decision**: Update `commands/version.py::_read_golem_schema_version()` to read
`resources/schemas/golem-1.1/VERSION` (today it reads a non-existent
`schemas/golem/VERSION` and returns the `"unknown"` fallback). Update the two
tests that currently assert `golem_schema_version == "unknown"`
(`tests/test_cli_version.py`, `tests/test_cli_subprocess.py`) to expect the real
label.

**Rationale**: The ontology becomes present this iteration, so the `"unknown"`
stub is no longer the correct answer. This is a minimal, in-scope wiring change
(US4 makes the bundled ontology observable); it touches no CLI contract beyond
the value of one JSON field, which still emits a single JSON document (Principle IX).

**Scope guard**: outside `golem/` and `resources/`, this iteration modifies only
`commands/version.py` (this wiring) and the iteration-2 test/template artifacts
covered by D11 (the `golem-1.0` → `golem-1.1` rename). Nothing here reads the
bible/manuscript or validates coherence (FR-014).
