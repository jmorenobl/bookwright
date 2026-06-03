# Phase 0 — Research & Design Decisions

Provenance Model — Source / Finding / Anchor (iteration 012).

The spec left no `NEEDS CLARIFICATION` markers; this document resolves the
genuinely open *design* choices the spec deferred to `/speckit-plan`, grounding
each in the existing code and design § 20 / § 4.5. Every decision is checked
against Constitution X (no new GOLEM/ontology class) and the frozen-ontology
closure test (`tests/golem/test_namespaces.py` asserts `len(CLASS_IRI) == 17`,
exactly).

---

## D1 — Where the three entities live, and what they subclass

**Decision**: A new module `src/bookwright/golem/modules/provenance.py` holds three
frozen Pydantic models that subclass the existing `GolemEntity` base
(`golem/base.py`):

- `Source` extends `SluggedEntity` (token = ASCII slug of its name, segment
  `source`), like `Character`/`Setting`.
- `Finding` and `Anchor` extend `GolemEntity` directly, minting a `uuid_utils.uuid7()`
  token once in `model_post_init` and freezing it — the exact pattern
  `AttributeAssignment` already uses (segments `finding` / `anchor`).

**Rationale**: This is the established shape (`modules/inference.py`,
`modules/character.py`). Subclassing the base — not `AttributeAssignment` — keeps
the Finding/Anchor `cross_refs` independent of the inferred-attribute predicates
(P140/P141/P16) so the two uses of E13 stay distinguishable (FR-018).

**Alternatives rejected**: (a) Subclass `AttributeAssignment` and override its
`cross_refs` — fragile, couples research emission to inference internals.
(b) Plain dataclasses outside `golem/` — loses the deterministic-URI / frozen /
`to_triples()` machinery every other entity already shares.

---

## D2 — No new GOLEM class: how each entity is typed in RDF

**Decision**:

- **Finding** and **Anchor** emit `rdf:type crm:E13_Attribute_Assignment`
  (`CLASS_IRI["AttributeAssignment"]`, already frozen). Reification — explicitly
  permitted (FR-001, design § 20.3).
- **Source** emits **no `rdf:type` triple**. It is typed via the `E55_Type`
  pattern: `<source> crm:P2_has_type <source-type individual>`, where the
  individual (`bw:source-type/oficial`, …) is declared `a crm:E55_Type` in
  `sources.ttl`. A source is therefore identified in the graph by
  `?s crm:P2_has_type ?t . ?t a crm:E55_Type` from the source-type scheme.

**Rationale**: FR-001 mandates "reusing only `E13_Attribute_Assignment` and
`E55_Type` plus `bw:` properties … MUST NOT introduce any new GOLEM/ontology
class." A dedicated `bw:Source` *rdf:type* class — even in the Bookwright
namespace — is the kind of new typing class the spec forbids; the strict reading
types the Source purely through `P2_has_type → E55_Type`, exactly as design § 20.3
("Se tipa con `E55_Type` desde `sources.ttl`") states. `Source` therefore overrides
`to_triples()` (as `CharacterFeature`/`Dimension` already do) and does not yield a
`(uri, rdf:type, golem_class)` triple; its `golem_class` ClassVar is set to
`CRM["E55_Type"]` only as a documented, unemitted placeholder.

**Alternatives rejected**: (a) `<source> rdf:type bw:Source` — cleaner RDF but
introduces a new class, violating FR-001's literal text. (b) `<source> rdf:type
crm:E31_Document` — references a CRM class outside the frozen GOLEM closure and
still adds a typing class the spec didn't sanction. (c) `<source> rdf:type
crm:E55_Type` — semantically false (a source is not a Type).

**Note for `/speckit-analyze`**: this is the one spot where the spec's "only E13 +
E55" wording forced a judgement call. The chosen reading is the strict,
literally-compliant one and is consistent with design § 20.3/§ 20.8. If a future
review prefers an explicit `bw:Source` marker class, that is a spec amendment, not
a silent plan choice.

---

## D3 — The `bw:` namespace and property set

**Decision**: Add `BW = Namespace("https://bookwright.dev/vocab/bw#")` to
`golem/namespaces.py` (matching the existing `https://bookwright.dev/vocab/`
pattern used by `greimas.ttl`/`propp.ttl`), bind prefix `bw`, and declare the
properties below in `sources.ttl`. The properties are referenced from
`provenance.py` as module constants. They are **not** added to `CLASS_IRI` nor to
the closure-checked predicate lists in `test_namespaces.py` — they are
Bookwright's own terms, declared in `sources.ttl`, never in the frozen
`golem.ttl`. (Reused CIDOC-CRM predicates `P2_has_type`, `P140_assigned_attribute_to`,
`P4_has_time-span` and the `E52_Time-Span` class are likewise referenced directly
from the already-bound `CRM` namespace, not added to `CLASS_IRI`.)

| Concept | Predicate | Object | Notes |
|---|---|---|---|
| Source → type | `crm:P2_has_type` | E55 individual | one of the six source types |
| Source → reliability | `bw:reliability` | E55 individual | one of `alta`/`media`/`baja` |
| Source → reliability justification | `bw:reliabilityJustification` | `xsd:string` | required (FR-004) |
| Source → reference / URL | `bw:reference` | `xsd:string` | bibliographic ref or URL |
| Source → author | `bw:author` | `xsd:string` | |
| Source → original language | `bw:originalLanguage` | `xsd:string` | ISO 639-1 |
| Source → access date | `bw:accessDate` | `xsd:date` | |
| Source → original quote | `bw:originalQuote` | `xsd:string` | |
| Source → translation | `bw:translation` | `xsd:string` | emitted **iff** original language ≠ book language (D6) |
| Finding → claim | `bw:claim` | `xsd:string` | omitted when finding is open with no claim |
| Finding → asserter | `bw:assertedBy` | `xsd:string` | agent or author (default `"author"`) |
| Finding → entity it bears on | `crm:P140_assigned_attribute_to` | entity URI | reuse the E13 "is about" predicate |
| Finding → supporting source(s) | `bw:supportedBy` | source URI | one triple per source |
| Finding → open flag | `bw:open` | `xsd:boolean` | emitted **only** when `true` |
| Anchor → promoted finding | `bw:promotes` | finding URI | the Finding this Anchor derives from |
| Anchor → constrained entity | `bw:constrains` | entity URI | design § 20.5 name |
| Anchor → time-span | `crm:P4_has_time-span` | E52 sub-node | optional (D5) |

**Rationale**: Reusing `P140_assigned_attribute_to` for "the entity the finding
bears on" is the exact semantics of the GOLEM Inference module the spec wants to
reuse, and findings stay distinguishable from inferred assertions by the presence
of `bw:claim` / segment `finding` (FR-018, SC-007). `bw:constrains` and `bw:claim`
match the SPARQL in design § 20.5 verbatim.

**Alternatives rejected**: a bespoke `bw:bearsOn` instead of `P140` — would not
reuse the Inference module as the spec emphasises, for no gain.

---

## D4 — Source type & reliability as controlled `E55_Type` individuals

**Decision**: `sources.ttl` declares nine `E55_Type` individuals: six source
types and three reliability levels, each `a crm:E55_Type` with an `rdfs:label`.
The front-matter value is the accented Spanish word (FR-003 exact list:
`primaria`, `secundaria`, `oficial`, `académica`, `periodística`, `testimonial`;
FR-004: `alta`, `media`, `baja`). A code-level map (`SOURCE_TYPE_IRI`,
`RELIABILITY_IRI` in `provenance.py`) resolves each value to its ASCII-slugged
IRI (`bw:source-type/academica`, `bw:reliability/alta`, …). Enforcement is
**hard, at parse time**: the `Source` Pydantic model declares
`type: Literal[…six…]` and `reliability: Literal[…three…]`, so an out-of-vocabulary
value raises and the build aborts naming the offending value (FR-016, US1 §3).

**Rationale**: mirrors the existing "IRIs hard-coded in code, confirmed against the
vendored Turtle" pattern (`CLASS_IRI` vs `golem.ttl`). `sources.ttl` is the
human-readable canonical declaration; the Pydantic `Literal` is the enforcement
point — the same division `golem.ttl` ↔ `CLASS_IRI` already uses.

**Alternatives rejected**: parse `sources.ttl` at runtime to derive the allowed
set — adds import-time graph parsing the codebase deliberately avoids (research D5
in iteration 5: "the Turtle is never parsed at import time").

---

## D5 — Anchor time-span representation

**Decision**: When a topic file declares a time-span on an anchor, `Anchor` emits
`<anchor> crm:P4_has_time-span <anchor-uri/time-span>`, and the time-span sub-node
emits `rdf:type crm:E52_Time-Span` plus begin/end years as
`crm:P82a_begin_of_the_begin` / `crm:P82b_end_of_the_end` `xsd:gYear` literals
(`begin`/`end`, or a single `date` shorthand → begin == end, mirroring
`io/bible.py`'s event interval). An anchor with no time-span emits none (FR-010).

**Rationale**: `P4_has_time-span` is the predicate design § 20.3/§ 20.6 names; the
E52/P82a/P82b shape is standard CIDOC-CRM and gives the iteration-15
`factual_anchor` anachronism check the begin/end data it needs without coupling to
the validation system's internal `time-interval` model now. All terms are CRM/`bw:`
— none added to the frozen `CLASS_IRI` closure.

**Alternatives rejected**: (a) reuse the validation system's DLP `time-interval`
node — premature coupling to iter-15 internals. (b) a bare `xsd:gYear` literal on
`P4_has_time-span` — `P4` ranges over `E52_Time-Span`, not a literal; would be
malformed CRM.

---

## D6 — Translation-presence rule (book language)

**Decision**: `graph build` passes `manifest.book.language` into `map_research`.
For each Source, the translation triple (`bw:translation`) is emitted **iff** the
source's `original_language` differs from the book language. The rule is enforced:
when languages **differ**, a missing `translation` is a hard research error
(FR-002, FR-016, edge case "malformed front-matter"); when they **match**, any
supplied `translation` is dropped and never emitted (SC-004: "absent when it
matches"). The `Source` model itself stores `translation: str | None`; the
language comparison and enforcement live in `io/research.py`, which is where the
book language is known.

**Rationale**: keeps the entity model context-free (it doesn't know the book
language) and the policy in the reader — the same split `io/bible.py` uses for
provenance-locator resolution. SC-004 is satisfied by construction.

**Alternatives rejected**: store book language on the entity — leaks manifest
context into the frozen domain model.

---

## D7 — `bible/research/` layout, parsing, and the fault model

**Decision**: `io/research.py` mirrors `io/bible.py`'s collection/dir machinery:

- `bible/research/sources.md` — front-matter `sources:` list → `Source` entities.
- `bible/research/<topic>.md` (any `*.md` except `_index.md`/`sources.md`) —
  front-matter `findings:` and `anchors:` lists → `Finding` / `Anchor` entities.
  Findings reference sources by source name/slug; anchors reference a finding by
  its in-file `id` and a `constrains:` target (a narrative entity name resolved
  against the bible's `entity_index` (D11), or the literal `timeline`).
- `bible/research/_index.md` — topic map + global open questions; an optional
  `open_questions:` list emits open `Finding`s. Treated leniently — never required.

**Fault model** (deliberately *stricter* than the bible mapper, per spec US1 §3
and the "malformed front-matter" edge case): a vocabulary violation, a missing
required Source facet on a non-open finding, or a translation-rule violation
raises `ResearchError` and **aborts the build with no graph written** (explicit,
value-naming error via the existing error envelope, exit 2). This contrasts with
`io/bible.py`, which *soft-skips* an unusable file. An **open** finding with no
claim/source/target is valid and never aborts (FR-008, edge cases). An **absent or
empty** `bible/research/` yields zero entities and the build proceeds unchanged
(FR-015, SC-005).

**Rationale**: the spec is explicit that bad research is surfaced as an error,
"rather than a silently dropped triple" — the opposite of the bible mapper's
tolerance. Reusing the bible reader's `Frontmatter`/`key_lines`/collision
infrastructure keeps the new reader small and consistent.

**Alternatives rejected**: soft-skip research files like bible files — directly
contradicts US1 §3 and the malformed-front-matter edge case.

---

## D8 — Hooking the research pass into `graph build`

**Decision**: After the existing bible mapping/emission loop in `build.py:_build()`,
add a research pass: resolve `research_dir = bible_dir / "research"`, call
`map_research(project_root, research_dir, uri_base, manifest.book.language,
entity_index, timeline_uri(uri_base))` (the bible `entity_index` from D11; the
well-known timeline IRI from D10), and feed each entity's `to_triples()` through
`engine.add_triple(*triple)` into the same engine before `engine.save()`.
`ResearchError` is added to the command's existing `except` tuple and rendered
through the existing error envelope (exit 2). The `BuildReport` gains optional
research counters (sources/findings/anchors) plus the `ResearchWarning` list (D12)
for the human/`--json` summary, exit code unchanged; existing fields are unchanged so
current build tests still pass.

**Rationale**: one graph, one save — research and narrative triples land in the
same `bible/graph.ttl` (FR-013). No new command, no second serialization. Findings
are themselves E13 reifications, so the research pass does **not** run them through
`build_provenance` (which mints inferred-attribute E13s for *bible* entities) —
avoiding double reification.

**Alternatives rejected**: a separate `graph build-research` command — fragments
the graph and contradicts FR-013's "same `bible/graph.ttl`".

---

## D9 — Distinguishing the two uses of E13 (FR-018 / SC-007)

**Decision**: Findings and Anchors are told apart from inferred-attribute
assertions on two independent axes, either of which suffices:

1. **URI segment** — `finding` / `anchor` vs `assertion`
   (`{uri_base}{segment}/{uuid7}`), already distinct by design § 4.5.
2. **`bw:` predicates** — only findings carry `bw:claim`/`bw:open`; only anchors
   carry `bw:constrains`/`bw:promotes`. Inferred assertions carry
   `crm:P141_assigned` + `crm:P16_used_specific_object` (a verbatim source path),
   which findings/anchors never emit.

A discriminating query (`?f a crm:E13_Attribute_Assignment ; bw:claim ?c`) returns
findings and no inferred assertions. The existing `tests/commands/graph/test_provenance.py`
count (10 E13s in `tiny-novel`, which has no research) is unaffected because the
research fixture lives behind the off-by-default `with_research` scaffold flag — the
`tiny_novel` fixture `test_provenance.py` uses is `with_research=False`.

**Rationale**: satisfies FR-018/SC-007 with zero ambiguity and no schema churn.

---

## D10 — The `timeline` constraint target (`constrains: timeline`)

**Decision**: Define a well-known, conventional IRI `{uri_base}timeline` as the
target an Anchor points at when its front-matter says `constrains: timeline`
(FR-009, spec US3 §4). It is emitted **only** as the object of `bw:constrains`
(`<anchor> bw:constrains <{uri_base}timeline>`); it carries **no `rdf:type`** and is
produced by a tiny helper `timeline_uri(uri_base) -> URIRef` in
`golem/namespaces.py`. `graph build` passes `timeline_uri(uri_base)` into
`map_research`; the reader maps the literal `timeline` to it.

**Rationale**: GOLEM models the timeline as a *collection* of `NarrativeEvent`s
(`{uri_base}event/{slug}`), with **no single node** representing "the timeline"
(confirmed in `io/bible.py`: `timeline.md` yields only `event/{slug}` nodes).
FR-009 nonetheless lists "or the timeline" as a constraint target — era-level
anchors that bound the whole story and feed the iter-15 anachronism check. A plain
addressable IRI is the smallest durable surface that satisfies it **without
introducing a new GOLEM/ontology class** (Constitution X): like `Source` (D2), the
resource is *referenced*, not *typed*. A later iteration may add a typing triple for
it without breaking the URI.

**Alternatives rejected**: (a) link to every event node — wrong semantics (an era
anchor is not a claim about each event). (b) mint a `bw:Timeline` `rdf:type` class —
violates FR-001 / Constitution X. (c) drop the timeline target from v0 — breaks
FR-009 and US3 acceptance §4.

---

## D11 — Resolving narrative targets: a comprehensive bible entity index

**Decision**: `map_bible` (`io/bible.py`) exposes a new `entity_index` on
`MapResult` — `make_slug(name) → URI` for **every character, setting and event** —
and `graph build` passes it to `map_research` as the `bible_index` used to resolve
`findings[].bears_on` and `anchors[].constrains`. This is **separate** from the
existing participant-only `slug_index` (characters), which is left exactly as-is, so
event/relationship participant resolution is unchanged (no regression).

**Rationale**: FR-009 lets an Anchor (and a Finding's `bears_on`) target a
`G1_Character`, a `G12_Setting` or a `G5_Narrative_Event`, but today only characters
are indexed (`io/bible.py`: settings `index=False`; events live in a transient
per-file `item_index`) and `MapResult` exposes no index at all. From a bare target
name the reader cannot otherwise know the URI segment (`character/` vs `setting/` vs
`event/`). A single comprehensive name→URI index is the smallest durable surface
that makes every allowed target kind resolvable, and it doubles as the lookup later
iterations (validators, verify) will need.

**Alternatives rejected**: (a) flip settings/events into the participant `slug_index`
— silently changes participant-resolution semantics (a setting could resolve as an
event participant), masking real errors. (b) reconstruct the index in `build.py` by
re-slugging `result.entities` — duplicates `map_bible`'s own knowledge and drifts.
(c) require the author to spell the kind in front-matter — leaks graph structure into
the research plain text.

**Absent-target behaviour** is decided in **D12** (soft-skip + surfaced build warning).

---

## D12 — Unresolved narrative target: soft-skip with a surfaced warning

**Decision** (D.2): when `bears_on` / `constrains` names an entity **absent** from the
bible `entity_index` (D11) — and it is not the literal `timeline` (D10) — the reader
does **not** emit the `crm:P140_assigned_attribute_to` / `bw:constrains` triple. It
records the miss (`relpath`, field, name) as a `ResearchWarning` on `ResearchResult`;
`graph build` surfaces it in `BuildReport` (human stderr + `--json`). The build
**still succeeds** — exit code unchanged, *not* a `ResearchError`, *not* exit 4: a
missing target is never silently dropped, but enforcing that a target exists and is an
allowed kind stays the `factual_anchor` validator's job (iter-15).

**Rationale**: from a bare name with no kind the reader cannot compose a correct URI
segment (`character/` vs `setting/` vs `event/`), so "emit as declared" is not
actionable. Skipping the unresolvable triple keeps `§ 4.5` untouched and avoids
phantom `entity/{slug}` nodes that iter-15 would have to reconcile, while the surfaced
warning keeps the author informed now. This mirrors the bible reader's soft-skip
tradition without escalating exit status (existence checking is explicitly deferred to
iter-15 per the spec edge cases).

**Alternatives rejected**: (a) compose a neutral `{uri_base}entity/{slug}` and emit the
link — extends the load-bearing `§ 4.5` URI convention and creates dual URIs
(`entity/x` ↔ `character/x`) iter-15 must merge. (b) hard `ResearchError` — contradicts
the spec edge case (target existence is iter-15's concern, not a build-time rejection).
(c) silent drop — loses author feedback.

---

## Closure / regression safety check

- `CLASS_IRI` stays at exactly 17 entries → `test_class_iri_maps_thirteen_concepts_plus_attribute_carriers` stays green.
- `frozen_terms()` closure lists are untouched → `test_*_in_frozen_terms` stay green (bw:/research terms are intentionally outside the GOLEM closure).
- Binding the unused `bw` prefix on a research-free graph adds no `@prefix bw:` line (rdflib emits prefixes only when used) → `tiny-novel` Turtle output and `test_bind_prefixes_*` stay byte-stable.
- No runtime dependency added → `uv.lock` unchanged, Constitution II intact.
