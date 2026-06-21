# Changelog

All notable changes to Bookwright are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project aims to follow semantic versioning.

## [0.4.3] — 2026-06-21

Second patch of the **v0.4.x post-dogfooding hardening track** (iteration 035) —
pure hardening that makes the v0.4 narrative-structure layer queryable by content
and by order. The dogfooding run measured two structural-recall gaps: a
`G9_Narrative_Unit` carried no `rdfs:label`, so its human name lived only in the
URI slug and no SPARQL query could find a beat by name; and a sequence's declared
`order:` was consumed at assembly and never materialized, so under unordered RDF
no query could walk a `G7_Narrative_Sequence` in author order (DEBT-005). This
release emits a single `rdfs:label` on every unit and function (reusing the
`CharacterRole`/`CharacterFeature` one-triple shape, riding the identity
assertion — no new provenance node), and materializes each member's resolved
position as a per-unit `bw:sequenceOrdinal` triple (`xsd:integer`, 1-based
contiguous rank over the already-sorted members, so it is total and gap-free
under missing/duplicate/absent `order:`). No new CLI surface and no new runtime
dependency. The GOLEM ontology stays **frozen** — `bw:sequenceOrdinal` is
declared in `resources/vocabularies/sources.ttl` (the `bw:reference` home),
outside `golem.ttl`/`CLASS_IRI` and the `test_namespaces.py` closure (Principle
X); the graph remains a derived cache reconstructible from the plain-text source
(Principle I).

### Added

- **`G9`/`G10` `rdfs:label` emission**
  (`src/bookwright/golem/modules/narrative.py`): `NarrativeUnit.to_triples()` and
  `NarrativeFunction.to_triples()` each yield one `(uri, rdfs:label,
  Literal(name))` carrying the authored name verbatim (accents/casing preserved),
  so beats and functions are name-queryable. The function is minted once per slug,
  so exactly one label triple exists even when several fiches name it.
- **`bw:sequenceOrdinal` queryable order**
  (`src/bookwright/golem/modules/narrative.py`,
  `src/bookwright/golem/namespaces.py`): `NarrativeSequence.to_triples()` emits a
  per-member `(unit, bw:sequenceOrdinal, Literal(rank, xsd:integer))` triple, and
  `derived_assertions()` reifies each ordinal as its own file-level
  `crm:E13_Attribute_Assignment` (target = unit, attribute = sequence, keyed to
  `order`). A single SPARQL `ORDER BY ?n` now recovers the declared order from the
  graph alone.
- **`bw:sequenceOrdinal` vocabulary declaration**
  (`src/bookwright/resources/vocabularies/sources.ttl`): declared as an
  `rdf:Property` with `rdfs:label`/`rdfs:comment`, outside the frozen GOLEM
  closure.
- **Two demonstrative SPARQL queries as tests**
  (`tests/golem/test_narrative_label_order.py`): Q1 resolves a unit by its
  `rdfs:label`; Q2 lists a sequence's members in declared order via the ordinal,
  proving the query isolates one sequence line. The E2E
  `tests/e2e/test_narrative_workflow.py` `_ordered_members` is rewritten to read
  member order from the graph by `ORDER BY` — overturning its prior "the graph
  carries no member ordinal" assumption — and a new test asserts every unit/
  function label against the `tiny-quest` oracle.

### Changed

- **Term-closure test exempts the one new `bw:` term**
  (`tests/golem/test_triples.py`): the frozen-ontology closure check now exempts
  `bw:sequenceOrdinal` specifically — *not* the whole `bw:` namespace — so any
  other stray `bw:` emission still fails the gate. The `test_namespaces.py`
  closure list is **unmodified** and `golem.ttl`/`CLASS_IRI` are untouched.

### Removed

- **DEBT-005 entry** (`DEBT.md`): the narrative-recall gap is closed and removed
  (git keeps the history); the dogfooding-intro count drops to one entry and
  DEBT-006's cross-reference is repointed to "the narrative-recall gap of
  iteration 035".

## [0.4.2] — 2026-06-21

First patch of the **v0.4.x post-dogfooding hardening track** (iteration 034) —
pure hardening that wakes a validator the toolkit's own scaffold had been
silently disabling. The `focalization` validator anchored its narrative-voice
declaration pattern at line start, so it never matched the
`- **Voz narrativa**: …` shape that `constitution.md.j2` itself emits — leaving
the check dormant on every voice-bearing fixture and on every real project
scaffolded by `bookwright init` (DEBT-004, surfaced by the 2026-06-21 dogfooding
run). This release normalizes the candidate line before matching — stripping one
line-leading bullet/blockquote marker and the emphasis markers around the label —
so the scaffold shape parses byte-identically to the bare form. No new CLI
surface, no new runtime dependency, and the GOLEM ontology stays **frozen** —
this is a prose validator that emits `triples=()` and touches no graph.

### Changed

- **`focalization` tolerates markdown-prefixed voice declarations**
  (`src/bookwright/validation/validators/focalization.py`): a new
  `_normalize_declaration_line` helper strips, per candidate line and each
  independently (no balance guard), one line-leading bullet/blockquote marker
  (`-`/`*`/`+`/`>` + whitespace), then a leading emphasis run, then an emphasis
  run anchored between the label and its colon (`*`/`**`/`_`). The
  person/limited/focal body-extraction is untouched, so `- **Voz narrativa**:
  Tercera persona limitada, centrada en Elena Vidal.` now parses to the same
  `_Declaration(person="third", limited=True, focal="Elena Vidal")` as the bare
  form. The validator is now awake on the scaffold shape (ES + EN).

### Added

- **Template↔parser anti-drift binding test**
  (`tests/validation/test_focalization.py`): a test reads the live
  `constitution.md.j2` voice line and asserts the parser accepts it, so the
  scaffold and the validator can never again silently diverge; plus
  marker-by-marker recognition coverage and the no-false-positive edge cases
  (no declaration / `[PENDING:…]` / mid-sentence label). Suite reconciliation
  confirmed every fixture oracle stays honest: the awakened validator yields
  **0 findings** on `tiny-historical`'s clean third-person prose, so its
  project-wide `validation.counts` stays `{error:1, warning:6}` — read from the
  awake validator, not back-fitted.

### Removed

- **DEBT-004 entry** (`DEBT.md`): the silently-disabled-validator debt is closed
  and removed (git keeps the history); the intro count drops `tres → dos` and
  DEBT-006's cross-reference is repointed from `DEBT-004/005` to `DEBT-005`.

## [0.4.1] — 2026-06-21

First patch on the **v0.4 line** (iteration 033) — pure hardening that removes a
dead concept and closes the structural loophole that let it hide. The top-level
`NarrativeRole` Python concept was unreachable: `G11_Narrative_Role` is
materialized solely by the character-scoped `CharacterRole` carrier (the design
defines G11 as *a character's role*, `bookwright-design.md` line 1603), so the
standalone concept minted nothing yet still counted toward the registry. This
release deletes it and hardens the ingestion-parity contract so a dead concept
that shares a carrier's class IRI can never again be silently counted reachable
(DEBT-001, closed). No new CLI surface, no new runtime dependency, and the GOLEM
ontology stays **frozen** — the 17-class closure is untouched (now 12 concept +
5 carrier IRIs), `golem.ttl` and `golem:G11_Narrative_Role` unchanged, and the
graph emits byte-identical triples.

### Removed

- **Dead `NarrativeRole` concept** (`src/bookwright/golem/modules/narrative.py`
  and its import / `CONCEPTS` entry / `__all__` entry in
  `src/bookwright/golem/__init__.py`): the unreachable standalone concept is
  deleted, dropping `CONCEPTS` from **13 → 12** and the parity reachable set from
  **11 → 10**. G11 continues to be materialized — with identical triples — by the
  `CharacterRole` carrier, which was never in `CONCEPTS`.

### Changed

- **Ingestion-parity contract hardened against carrier-IRI collision**
  (`tests/golem/test_ingestion_parity.py`): `NarrativeRole` joins `CARRIER_NAMES`
  (→ 5), `EXPECTED_REACHABLE` drops to 10, and a new pure `carrier_iri_collisions`
  invariant plus a drift simulation assert that no `CONCEPTS` member may share a
  class IRI with a carrier-only entry — closing the DEBT-001 loophole by
  construction.
- **G11 triple/URI coverage relocated onto the real carrier** (`test_triples.py`,
  `test_uri.py`, `test_namespaces.py`): coverage that referenced the deleted
  concept now exercises `CharacterRole`; `test_namespaces.py` reclassifies the
  G11 IRI from the concept bucket to the carrier bucket (`12 + 5 == 17`), so the
  closure count is preserved, not lowered.
- **Stale "thirteen concepts" counts swept** to "twelve" across live source and
  tests (`golem/__init__.py`, `golem/deferrals.py`, the parity test, the
  `parity-exercise/manifest.toml` header, the `CharacterRole` docstring);
  released `CHANGELOG.md` history is left intact (Principle I).
- **DEBT-001 retired** (`DEBT.md`, `bookwright-roadmap.md` §4): the ledger entry
  is removed and the roadmap decision reconciled to *Resuelto (iteración 033)*.
  The G6/G3 deferrals are untouched.

## [0.4.0] — 2026-06-21

The **narrative-structure layer** (iterations 028–032), shipped once as a minor
release at the close of the milestone — like M4→`v0.2.0` and M5→`v0.3.0`, the
five iterations accumulated on `main` and carry no per-iteration patch tag. This
release brings Propp/Greimas narrative structure (the modelled-but-unfed
`G7`/`G9`/`G10` closure) alive end to end: `outline/units/*.md` now ingests, the
graph assembles narrative sequences from it, the Propp/Greimas vocabularies type
the result, and a new continuity validator consumes the layer. With it the
**ingestion-parity north star is reached** — every authorable concept now has an
ingestion path. No new runtime dependency, and the GOLEM ontology stays
**frozen** (the 17-class closure is untouched; the `G7`/`G9`/`G10`/`G11` classes
already existed — only their ingestion and typing paths are new).

### Added

- **`outline/units/*.md` ingestion → `G9_Narrative_Unit` + `G10_Narrative_Function`**
  (iteration 028, `bookwright-design.md § 7.4`): outline beats now map into the
  graph as narrative units carrying their narrative function, the third ingested
  mirror of the `bible/` pattern after locations (G13) and objects (G16). Takes
  `G9`/`G10` out of the deferral registry's observed-orphan set.
- **`G7_Narrative_Sequence` assembly** (iteration 029): units' optional
  `sequence`/`order` front-matter keys assemble into ordered narrative sequences
  via `dlp:proper-part`, completing the `G7`/`G9`/`G10` ingestion closure.
- **Propp/Greimas vocabularies as `crm:E55_Type`** (iteration 030,
  `resources/vocabularies/propp.ttl` + `greimas.ttl`): 31 Propp functions and 6
  Greimas actants with ES+EN labels. When the manifest's new `[vocabularies]
  active` list turns a vocabulary on, narrative functions (G10) and character
  roles (G11) are typed via `crm:P2_has_type`, the link reified through the
  existing `E13` provenance path — with zero regression when no vocabulary is
  active.
- **`narrative_structure` validator** (iteration 031,
  `src/bookwright/validation/validators/narrative_structure.py`): the first
  *consumer* of the layer — an auto-discovered, `warning`-default, LLM-free check
  with two rules: **orphan beat** (a `G9` unit in no `G7` sequence, via SPARQL
  `NOT EXISTS` over `dlp:proper-part`) and **unresolved role** (re-surfaced from
  outline ingestion's `UnresolvedReference` records). Both findings are cited via
  the existing `E13` provenance path; no ontology change.
- **Narrative-structure E2E + docs** (iteration 032): a source-only
  `tests/fixtures/tiny-quest/` fixture with a co-located oracle (Propp active, a
  deliberate orphan beat and unresolved role), the build→validate E2E
  `tests/e2e/test_narrative_workflow.py`, and the Spanish
  `docs/narrative-structure.md`.

### Changed

- **`ValidationContext.outline()` accessor** (iteration 031): a new cached
  accessor exposes outline ingestion's `UnresolvedReference` records to the
  validation layer, so the `narrative_structure` validator can re-surface
  unresolved roles without re-parsing.
- **G6/G3 deferral re-targeted to `demand-pulled`** (iteration 032,
  `src/bookwright/golem/deferrals.py`, the ingestion-parity parity test's
  `EXPECTED_VERSIONS`, and `DEBT.md`): `RelationshipRole` (G6) and
  `PsychologicalState` (G3), previously stamped target `"v0.4"`, are honestly
  re-pointed at the first-class `"demand-pulled"` sentinel — they ship when an
  activation condition is met, not on a pre-assigned version. The two remain
  observed as orphans by the ingestion-parity build.

## [0.3.4] — 2026-06-15

Fourth and **closing** patch of the **v0.3.x hardening track** (iteration 027).
It ties off the three loose ends the track left behind: the success-envelope
single-sourcing deferred "out of 020's scope", the two "undecided" orphan
verdicts the iteration-024 deferral registry still carried, and the
`UnresolvedParticipant` misnomer iteration 025 explicitly deferred to here.
After this patch the deferral registry holds **zero** `"undecided"` entries,
no `focus`/`graph` command hand-builds a `{"status": "ok", …}` literal, and no
`UnresolvedParticipant` symbol survives in `src/` or `docs/`. No new CLI
surface, no new runtime dependency, no ontology change — pure hardening, with
one **deliberate** public-contract byte change (see *Changed*).

### Added

- **Success-envelope regression suite**
  (`tests/commands/test_success_envelopes.py`): pins the exact stdout bytes of
  every command in the cleanup's scope (`check`, `focus` show/set/clear, `graph
  query`, `graph build`) so any future single-byte drift in a success document
  fails CI.

### Changed

- **Success documents single-sourced** (`src/bookwright/commands/focus/{show,set_,clear}.py`,
  `src/bookwright/commands/graph/query.py`, `src/bookwright/commands/_envelope.py`):
  the `focus` and `graph query` commands now build their success envelope through
  the shared `ok_payload()` helper + `emit_json` instead of a hand-rolled
  `{"status": "ok", …}` dict. Output is **byte-identical** to before — same keys,
  order, compact separators, and trailing newline. `check`'s intentional
  `{"ok": <bool>, "checks": […]}` envelope (no top-level `status`) is left exactly
  as-is.
- **G6/G3 deferral confirmed** (`src/bookwright/golem/deferrals.py`):
  `RelationshipRole` (G6) and `PsychologicalState` (G3), previously stamped
  `"undecided"`, are now firmly deferred to **`v0.4`** with the reason "requires a
  typed roles/states model with attributes and an authoring surface". Neither is
  wired (each carries a mandatory cross-ref and has no `bible/` authoring surface,
  so an identity-only node would be semantically degenerate); both stay observed as
  orphans by the ingestion-parity build. The registry now contains **no**
  `"undecided"` verdict — every remaining entry names a firm reason and a concrete
  target version.
- **`UnresolvedParticipant` → `UnresolvedReference`** (`src/bookwright/io/report.py`,
  `src/bookwright/commands/graph/build.py`, `docs/commands/graph-build.md`): the
  `graph build` soft-warning type — reused since iteration 025 to also surface an
  unresolvable location `setting:`, not just an unmatched `participants:` member —
  is renamed to describe what it actually reports. **This renames the public
  `graph build --json` key `unresolved_participants` → `unresolved_references`** (a
  deliberate `0.x` maintainer-facing contract change): the key's position, its
  `{path, entity, name}` item shape, and every other byte of the envelope are
  unchanged; only that one key string and a new pinned golden baseline differ. The
  stderr summary now reads "N unresolved reference(s)".



Third patch of the **v0.3.x hardening track** (iteration 026). It wires the
second orphaned GOLEM concept into the ingestion pipeline: `bible/objects/*.md`
files — narrative-world objects (a weapon, a relic, a document), ignored
entirely in v0 — now become first-class `G16_Object` nodes, a faithful mirror of
how `bible/settings/` already feeds `G12_Setting`. This shrinks the deferral
registry from six orphans to five and turns the ingestion-parity guard's
reachable set from seven fed concepts to eight. No new CLI surface, no new
runtime dependency, no ontology change (G16 already exists in the frozen
closure, identity-only) — pure hardening.

### Added

- **Object ingestion** (`src/bookwright/io/_bible_builders.py`,
  `src/bookwright/io/bible.py`): the bible mapper now processes
  `bible/objects/*.md` as a one-entity-per-file directory (a sixth `_DirSpec` in
  the existing data-driven loop). Each file builds an `Object` (G16) from `name:`
  front-matter — the identity source, required — exactly as `Setting` does. The
  v0 class is identity-only. Absence of `bible/objects/` changes nothing; a file
  without front-matter is skipped without crashing; a slug collision is rejected
  as in characters/settings.
- **Project scaffold** (`src/bookwright/resources/project/bible/objects/`): the
  `bookwright init` tree now includes `bible/objects/` alongside `settings/` and
  `locations/`.

### Changed

- **`Object` removed from the deferral registry**
  (`src/bookwright/golem/deferrals.py`, 6 → 5 entries); the ingestion-parity test
  (`tests/golem/test_ingestion_parity.py`) now pins eight reachable concepts.
- **`/bookwright-bible` source command** teaches authoring each object as
  `bible/objects/<slug>.md` with `name:` (required) front-matter. The skill
  re-materializes for both `claude` and `generic` integrations with its bilingual
  (ES/EN) triggers preserved.
- Recorded G16 as wired in `bookwright-design.md` § 7.3 and added `bible/objects/`
  to the project-tree diagram (no axiom reopened).

## [0.3.2] — 2026-06-14

Second patch of the **v0.3.x hardening track** (iteration 025). It wires the
first orphaned GOLEM concept into the ingestion pipeline: `bible/locations/*.md`
files — ignored entirely in v0 — now become first-class
`G13_Narrative_Location` nodes, mirroring how `bible/settings/` already feeds
`G12_Setting`. This shrinks the deferral registry from seven orphans to six and
turns the ingestion-parity guard's reachable set from six fed concepts to seven.
No new CLI surface, no new runtime dependency, no ontology change (G13 and
`dlp:generic-location` already exist in the frozen closure) — pure hardening.

### Added

- **Location ingestion** (`src/bookwright/io/_bible_builders.py`,
  `src/bookwright/io/bible.py`): the bible mapper now processes
  `bible/locations/*.md` as a one-entity-per-file directory. Each file builds a
  `NarrativeLocation` (G13) from `name:` front-matter (identity source) plus an
  optional `setting:` that resolves against the sibling settings index and emits
  the already-modelled `dlp:generic-location` cross-ref. An unresolvable
  `setting:` is surfaced through the existing `unresolved_participants` channel
  (no new warning category); the node is still built, the build never aborts.
  Built locations feed the research target index, so a `bears_on:` / `constrains:`
  link to a location now resolves instead of degrading to a soft-miss.

### Changed

- **`io/bible.py` split** (behavior-preserving): the concrete builders, coercers,
  resolution helpers, and the context/result dataclasses moved to the new sibling
  module `src/bookwright/io/_bible_builders.py`, bringing `bible.py` back under the
  500-line Principle IV ceiling (it was exactly at 500). `bible.py` re-exports the
  moved public names, so every `from bookwright.io.bible import …` keeps resolving;
  the existing mapper tests pass unchanged.
- **`NarrativeLocation` removed from the deferral registry**
  (`src/bookwright/golem/deferrals.py`, 7 → 6 entries); the ingestion-parity test
  (`tests/golem/test_ingestion_parity.py`) now pins seven reachable concepts.
- **`/bookwright-bible` source command** teaches authoring each concrete location
  as `bible/locations/<slug>.md` with `name:` (required) and `setting:` (optional)
  front-matter; the "no se indexa en v0" shortcut wording is retired. The skill
  re-materializes for both `claude` and `generic` integrations with its bilingual
  (ES/EN) triggers preserved.
- Recorded G13 as wired in `bookwright-design.md` § 7.2 (the v0 shortcut text is
  retired; no axiom reopened).

## [0.3.1] — 2026-06-13

First patch of the **v0.3.x hardening track** (iteration 024). It makes
*ingestion parity* — the gap between GOLEM concepts that are **modelled** (a
frozen class with a `CLASS_IRI` entry) and those actually **fed** from authored
`bible/*.md` — an explicit, tested contract instead of tribal knowledge. Of the
thirteen `CONCEPTS`, seven have no ingestion path today; this release names them
and guards the set so it can only shrink deliberately. No new CLI surface, no new
runtime dependency, no ontology change — pure hardening.

### Added

- **Deferral registry** (`src/bookwright/golem/deferrals.py`): `DEFERRED_CONCEPTS`,
  a pure-data map of the seven orphaned concepts (`NarrativeLocation`, `Object`,
  `NarrativeUnit`, `NarrativeFunction`, `NarrativeSequence`, `RelationshipRole`,
  `PsychologicalState`) to a `DeferralNote` recording *why* each is unfed and its
  `target_version` (`v0.3.x`, `v0.4`, or `undecided`). The module imports only
  `typing` — no I/O, no `CONCEPTS` import — so the gap is recorded independently of
  the code that fills it.
- **Ingestion-parity guard** (`tests/golem/test_ingestion_parity.py`): derives the
  orphan set from a *real* pipeline build over the new `parity-exercise` fixture and
  asserts it equals exactly `DEFERRED_CONCEPTS`'s keys. Wiring a concept later
  (iteration 025+) means **removing its registry entry**; the test stays green only
  if the registry no longer claims it deferred. Backed by the
  `parity-exercise` bible/manuscript fixture exercising every fed concept.

### Changed

- Documented the parity contract in `docs/authoring.md`; the `manuscript.py`
  reader gained a clarifying docstring (no behavior change).

## [0.3.0] — 2026-06-13

Context-orchestration milestone (M5, design § 21). This release adds the
**hilo conductor** — a three-layer work thread that answers "what am I working on
and what should I do next?" without a hand-written TODO that rots. The layers never
overlap: an **authored** `[focus]` block (your declared intent), a **derived**
`bookwright status` (the project state recomputed from the corpus, with
deterministic `next_actions`), and the **judgment** of the Agent Skills each action
invokes. Like the rest of Bookwright, the plan is a *function* of the plain text:
delete the graph, rebuild, get the same state. The system is **inert** for projects
that don't use it: no `[focus]` and no `bible/research/` means identical v0.2.0
behavior. This entry consolidates iterations 19–23.

### Added

- **Authored focus** (iteration 19): the optional `[focus]` manifest block
  (`target`, `notes`, CLI-stamped `updated_at`) and the `bookwright focus
  set`/`show`/`clear` commands. Plain-text authored state (Principle I); `focus
  set` preserves the rest of the manifest byte-for-byte (comments and order
  included).
- **`bookwright status`** (iteration 20): the derived-state command. Rebuilds the
  graph from the corpus on every run (recomputation *is* the freshness mechanism),
  aggregates the facts (phase, focus, open research questions, under-supported
  anchors, low-reliability findings, validation summary), and maps them through a
  pure, ordered rule table into `next_actions` — each carrying the skill to invoke,
  a paste-ready prompt, and the reason it fired. No LLM, no network: the same corpus
  yields byte-identical output. The rules recommend **per workstream, not per item**,
  so resolving one open question does not shorten the list — only its prompt/reason
  converge.
- **Status-consuming skills** (iterations 21–22): the authoring skills now read
  `bookwright status` at start, anchoring the judgment layer in the derived state
  rather than asking the author to restate it.
- **Orchestration fixture, E2E & docs** (iteration 23): the `tiny-historical`
  fixture extended into a worked orchestration example (a populated `[focus]`, a
  co-located `expected-status.md` oracle, and a pre-baked `_resolution/` answering
  finding outside the corpus dirs); `tests/e2e/test_orchestration_workflow.py`,
  which walks `focus → build → status → resolve → build → status` and asserts
  deterministic **state convergence** plus the inertness/degraded paths; and the
  Spanish `docs/orchestration.md` page wired into the nav. The M4
  `factual_anchor` expectations stay byte-stable (FR-006).

## [0.2.0] — 2026-06-05

Research & verification milestone (M4). This release adds a provenance-backed
research system on top of the v0.1.0 narrative graph: authors can record
external **Sources**, the **Findings** drawn from them, and the **Anchors** that
bind manuscript claims to evidence — all in plain text, all reconstructible into
the graph. Two new Agent Skills drive the loop, a new validator guards anchor
integrity, and an LLM-driven fidelity check flags claims the manuscript can't
support. The system is **inert** for projects that don't use it: no `[research]`
block or `bible/research/` means identical v0.1.0 behavior. This entry
consolidates iterations 12–18.

### Added

- **Research provenance model** (iteration 12): `Source`, `Finding`, and
  `Anchor` GOLEM-adjacent entities serialized through a new `sources.ttl`
  vocabulary (the frozen GOLEM ontology is untouched — Constitution X), with an
  `io/research.py` reader analogous to `bible.py` that maps `bible/research/*.md`
  into entities with `file:line` provenance.
- **`bookwright-research` Agent Skill** + **`[research]` manifest block**
  (iteration 13): the author-facing loop for gathering sources and recording
  findings, plus the `bible/research/` scaffold stamped by `init`. Triggers on
  both ES and EN prompts.
- **`factual_anchor` validator** (iteration 14): a continuity check that flags
  malformed anchors and time-span anachronisms against the graph, wired into the
  same error-only CI gate as the v0.1.0 validators.
- **`bookwright-verify` Agent Skill** (iteration 15): a post-draft LLM fidelity
  check that reads the manuscript against its anchored evidence and reports
  claims the sources don't support.
- **End-to-end research coverage & docs** (iteration 16): the `tiny-historical`
  fixture (a documented mini-novel with real anchors and a deliberate
  anachronism), `tests/e2e/test_research_workflow.py` exercising
  build → query → validate → verify, the Spanish `docs/research.md` page, and
  CHANGELOG/release metadata for this milestone.

### Changed

- **Unified error envelope** (iteration 18): every serializable error across the
  eight origins (`core`, `golem`, `io`, `indexers`, `validation`,
  `commands.validate`, `integrations`, `commands.init`) now subclasses the single
  `BookwrightError` base in `errors.py`, which owns the one canonical `--json`
  envelope (`{status, code, message[, details]}`) and its single `to_json()`.
  Per-class serializers were removed; the base imports nothing from other layers,
  so it sits below them with no cycle (Principle IX).

### Removed

- **Forbidden traceability tags** (iteration 17): purged all `T0xx` task IDs and
  `US-x`/`+USx` user-story tags from `src/` and `tests/` (~57 occurrences across
  ~40 files), converting each to a durable `FR`/`SC`/`D` or `bookwright-design.md
  § N.M` reference or to neutral prose. Added a non-regression test gate
  (`tests/meta/test_no_traceability_tags.py`) that fails CI if any reappear.
  Comments/docstrings only — no logic, signature, or behavior changes.

## [0.1.0] — 2026-06-03

First public release. Bookwright is a spec-driven authoring toolkit that turns a
small set of canonical plain-text documents into a validatable narrative graph.
This entry consolidates iterations 1–11.

### Added

- **CLI** (`typer` + `rich`, Python 3.11+): `bookwright init` (project
  scaffolding with conflict matrix, rollback ledger, and optional git init),
  `bookwright check`, `bookwright version`, `bookwright validate`,
  `bookwright graph build`, `bookwright graph query` (SPARQL over the GOLEM
  graph), and `bookwright integration use` (switch a project's active agent
  integration). Every agent-facing command accepts `--json` and emits a single
  JSON document on stdout (Principle IX).
- **GOLEM domain model** (`rdflib`): characters, settings, narrative events with
  temporal intervals and the five qualitative temporal relations, social
  relationships, and CIDOC-CRM provenance for every derived assertion, serialized
  to Turtle.
- **Graph indexer**: maps the project bible to GOLEM entities and answers SPARQL
  queries with the `golem:` prefix bound.
- **Bible / outline / constitution templates**: the Spanish narrative skeleton
  stamped by `init`, plus re-instanceable molds for the authoring commands.
- **10 authoring commands** materialized as agentskills.io-compliant Agent Skills
  (`bookwright-constitution`, `-bible`, `-outline`, `-synopsis`, `-scenes`,
  `-draft`, `-clarify`, `-analyze`, `-checklist`, `-continuity`).
- **Integrations**: `claude` (`.claude/skills/`) and `generic` (`.agents/skills/`)
  via a plugin registry — no monolithic dispatcher (Principle V).
- **Validation system**: four built-in validators — `character_presence`,
  `focalization`, `setting_continuity`, `temporal` — with an error-only CI gate.
- **Release layer (this iteration)**: three fully-valid fixture projects
  (`tiny-novel`, `tiny-essay`, `tiny-memoir`) under `tests/fixtures/`; an
  in-process E2E suite (`tests/e2e/`) covering the full workflow, skills
  materialization, the integration swap, and docs↔CLI drift; a Spanish MkDocs
  (`material`) documentation site that builds `--strict`; and finalized release
  metadata.

### Changed

- The integration swap is performed by the dedicated `bookwright integration use`
  command. The original plan (re-init with `init --here --force`) was incompatible
  with `init`'s ratified guard that refuses to re-initialize an existing project
  (`.bookwright/` present), so the swap is its own intention-revealing command;
  `init` is unchanged.
- The coverage gate threshold is single-sourced in `[tool.coverage.report]`
  (`fail_under = 80`, `precision = 2`) so it fails closed with no round-up.

### Added — Bible / Outline / Constitution templates

- Authored the real narrative skeleton stamped by `bookwright init`: the
  `bible/` documents (constitution, timeline, relationships, themes, glossary,
  research, subplots, POV structure) and the `outline/` documents (synopsis,
  structure, arcs, scenes), replacing the iteration-4 placeholder stubs. Each is
  Spanish literary-technical prose with HTML-comment craft guidance, worked
  examples inside comments, and `[PENDING: …]` prompts in author-fill sections.
- Authored the re-instanceable molds under `resources/templates/`
  (`character`, `setting`, `location`, `chapter`, `scene`) for the upcoming
  authoring commands (iterations 8–9). The `character` and `setting` molds carry
  frontmatter aligned exactly to the iteration-6 GOLEM mapper's recognized keys,
  so a fresh project indexes with zero skips and zero `unknown_keys`.
- Added a `tests/resources/` format / round-trip validation suite (sentinel
  sweep, frontmatter-contract round-trip via `map_bible`, filled-instance →
  GOLEM entity, Jinja2 `StrictUndefined` render, mold-structure and
  authoring-guidance lint).

### Attribution

- The template **structure** (the document inventory: short + long synopsis,
  themes with a motif registry, locations with sensory anchors, glossary,
  research, subplots, POV structure) is inspired by the
  [`fiction-book-writing`](https://github.com/adaumann/fiction-book-writing)
  preset by **adaumann** (MIT-licensed), whose license permits structural reuse
  with attribution. Bookwright's redaction is **original** prose under
  **Apache-2.0**, rewritten in Spanish and adapted to the **GOLEM** narrative
  model — no verbatim preset text is included.

### Changed — supersedes design § 6

- This iteration **supersedes** `bookwright-design.md` § 6's single unified
  `resources/templates/*.tmpl` layout with a four-layer `resolve_template()`
  resolver, in favor of a **lifecycle split**: stamped-once skeleton singletons
  live under `resources/project/` (rendered/byte-copied by the iteration-4
  walker) and re-instanceable molds live under `resources/templates/` (stamped
  many times by commands). The § 6 resolver only ever existed to serve presets
  (v0.2) and extensions (v0.5), which are out of v0 scope; building it now would
  be forbidden plumbing. § 6 is structural guidance, not a § 16 axiom, so the
  divergence is recorded here rather than litigated as a constitutional
  amendment.
