# Phase 0 Research: Outline ingestion — narrative units & functions

The spec arrives fully clarified (Clarifications, Session 2026-06-19): role
multiplicity and within-card role dedup are resolved, the ontology is frozen, and
the parity contract is pinned. There are **no open `NEEDS CLARIFICATION`**. This
document records the two real engineering decisions the spec deliberately left to
the plan, plus the smaller resolved questions, each with the alternatives weighed.

## D1 — Where the outline wiring lives: sibling `io/outline.py`

**Decision**: A new sibling module `io/outline.py` exposing
`map_outline(project_root, outline_dir, uri_base, result) -> None`, which **appends**
into the `MapResult` that `map_bible` already produced. The `_graph` pipeline calls
`map_bible` then `map_outline` on the same result. `io/outline.py` imports the generic
dir-walking engine (`_DirSpec`, `_map_single_dir`) from `io.bible` and the
context/coercers (`_MapContext`, `MappedEntity`, `_require_name`, `_coerce_str_list`,
`_Collisions`) from `io._bible_builders`. Nothing imports `io.outline` except the
`_graph` pipeline.

**Rationale**:
- The spec's Assumptions bless either an extended `map_bible` or a sibling
  `map_outline`; `map_bible` discovers **named** concept directories under `bible_dir`
  (`characters`, `settings`, …), not generic directories, and `outline/` is a *sibling*
  tree (`manifest.paths.outline`). A sibling module is the honest fit and keeps the
  bible mapper focused.
- **Appending into the same `MapResult`** (rather than returning a second result the
  pipeline must merge) means `_graph.build_project_graph` changes by exactly one call:
  it keeps iterating `result.mapped` for triples + `build_provenance`, and the
  `BuildReport` counters (`files_processed`, `entities`, `skipped`, `unknown_keys`,
  `unresolved_references`) already aggregate the unit/function additions for free. No
  merge code, no double-counting risk.
- **No import cycle**: `io.outline` → `io.bible` / `io._bible_builders` is one-way.
  Were we instead to have `map_bible` call into `io.outline`, and `io.outline` import
  `_map_single_dir` from `io.bible`, that would be a cycle (Principle IX). The chosen
  direction avoids it without relocating the engine.
- File sizes stay within Principle IV: `io/outline.py` ≈ 140 lines; `io/bible.py`
  399 → ~420; `io/_bible_builders.py` 269 → ~275.

**Alternatives considered**:
- *Extend `map_bible` to also walk `outline/units/`*: keeps one function but misnames
  it (it would map outline too) and grows `bible.py` toward the 500-line limit with an
  unrelated concern. Rejected for cohesion.
- *Return a second `MapResult` and merge in `_graph`*: forces merge/aggregation logic
  into the pipeline and risks counter drift. Rejected; appending into one result is
  strictly simpler.
- *Relocate the dir-walking engine into a third shared module both import*: a larger
  refactor than this iteration warrants; the one-way sibling import achieves the same
  decoupling with no churn. Recorded as a possible future tidy, not done now.

## D2 — Building the role-resolution index from public Character API

**Decision**: After the character `_map_single_dir` pass, `map_bible` runs a small
`_index_character_roles(ctx)` helper that iterates the just-mapped `Character` entities
and populates `ctx.roles_index: dict[str, list[URIRef]]` keyed by `make_slug(label)`,
appending each character-scoped role node's URI. The role node's URI is read from the
already-built `Character` rather than recomputed, by narrowing with `isinstance(entity,
Character)` and reading its materialized role nodes — the single source of truth for the
`{character.uri}/role/{slug}` shape (`CharacterRole.model_post_init`). The index is
published on `MapResult.roles_index` so `map_outline` consumes it.

**Rationale**:
- FR-005 mandates a role index that "does not exist today" and must be populated **by
  the character pass before the units pass runs" — the order mirrors
  settings-before-locations. Building it from the already-mapped characters (the first
  pass) guarantees that ordering with no new traversal.
- Reading the built role node's URI (single source of truth) avoids re-deriving the
  `/role/{slug}` URI scheme in a second place, so a future change to `CharacterRole`'s
  URI cannot silently desync the index.
- The index is **many-valued** (`dict[str, list[URIRef]]`): one role slug (e.g. `hero`)
  may be played by several characters, each with its own character-scoped role node.
  This is exactly the multiplicity the clarification pins (one unit→role edge per
  matching character role; zero matches = one soft miss).
- **Zero `golem/` edits**: the role nodes and their URIs already exist; we only read
  them. Honors "no toques golem/".

**Alternatives considered**:
- *Recompute `URIRef(f"{character.uri}/role/{make_slug(label)}")` in the io layer from
  the public `narrative_roles` tuple*: avoids touching the built role nodes but
  duplicates the URI scheme, inviting silent drift. Rejected for DRY/robustness.
- *Add a public `role_index_entries()` helper to `Character`*: cleaner encapsulation but
  edits `golem/`, which the prompt asks us to leave untouched. Rejected.
- *A single canonical top-level `NarrativeRole` node per slug, or minting one on miss*:
  explicitly rejected in the spec's Clarifications — both add an identity space the
  frozen ontology does not need (Principle X) or resolve non-deterministically.

## D3 — Function minting & dedup (resolved by the spec, recorded for the plan)

**Decision**: `_build_unit` mints each `functions` name into a `NarrativeFunction`
(identity-only, `narrative-function/<slug>`), deduplicated across **all** units via
`ctx.functions_index: dict[str, NarrativeFunction]`. The first unit to introduce a slug
appends one `MappedEntity` for that function into `result.mapped` (so its `rdf:type`
triple is emitted); later units reuse the same entity. The unit references the function
entities through its existing `CrossRef("functions", REFERS_TO, multi=True)` — **not**
`owned`, so the function's own triples are emitted via its separate `MappedEntity`, not
chained by the unit. Within a single card, repeated `functions`/`roles` names are
slug-deduplicated before processing (SC-002 / the roles clarification).

**Rationale**: matches SC-001/002 edge and entity counts deterministically; reuses the
declarative cross-ref + `derived_assertions` provenance machinery already in
`golem/base.py` (no override needed — the field names `functions`/`roles` equal the
front-matter keys, so the base tags each assertion's `source_field` correctly).

**Ordering invariant**: `_build_unit` validates `name` (and slugs it) and coerces
`functions`/`roles` to string-lists **before** minting any function or resolving any
role. So a card that is unusable front-matter (missing/empty/non-string `name`, or a
non-list `functions`/`roles`) raises `InvalidFrontmatterError`/`EmptySlugError` and is
skipped by `_map_single_dir` **before** leaking any partially-minted function — keeping
the report invariant "a skipped file appears only under `skipped`".

## D4 — Deferral-registry & parity-test edits (resolved, recorded)

**Decision**: Remove the `NarrativeUnit` and `NarrativeFunction` entries from
`DEFERRED_CONCEPTS`, leaving exactly three orphans
(`{NarrativeSequence, RelationshipRole, PsychologicalState}`). In
`tests/golem/test_ingestion_parity.py`: move `NarrativeUnit`/`NarrativeFunction` from
`ORPHAN_NAMES` into `EXPECTED_REACHABLE`, drop them from `EXPECTED_VERSIONS`, and change
`len(DEFERRED_CONCEPTS) == 5` to `== 3`. Update the prose counts in both module
docstrings ("Five of the thirteen" / "Exactly five entries" → three; "Eight of the
thirteen … the other five are orphans" → ten fed / three orphans). The
`parity-exercise` fixture gains an `outline/units/*.md` card declaring ≥ 1 `functions`
name so the **live build** observes G9/G10 as reachable (the test reads reachability
from a real build, never a hand-list).

**Confirmed unchanged**: the three drift-simulation tests probe `Character`,
`NarrativeEvent`, and `PsychologicalState` — none names a removed concept, so they keep
passing verbatim. The plan asserts this rather than editing them (FR-013).

## D5 — Authoring surface & documentation sweep (resolved, recorded)

- **Source command**: add a step + write-target to `resources/commands/bookwright-outline.md`
  (Spanish prose, the command's existing language) instructing one card per narrative
  unit under `outline/units/` with `name`/`functions`/`roles` front-matter. Keep the
  `description` bilingual and < 1024 chars; the existing materializer regenerates each
  `SKILL.md` and the `lint_skill_md` gate verifies compliance — no manual regeneration.
- **Scaffold**: add `resources/project/outline/units/` with a `.gitkeep`, mirroring
  `bible/settings/` (which seeds a bare `.gitkeep`).
- **Author-only note sweep (present-tense only, FR-014)**: amend `io/manuscript.py`'s
  iteration-024 note (English), `docs/authoring.md`'s v0.3 note (Spanish), and
  `deferrals.py`'s "no builder over `bible/*.md`" framing; add `outline/units/` to the
  design § 7 project tree and a new § 7.4 ingestion subsection (Spanish, mirroring
  § 7.2/§ 7.3). The roadmap's "author-only *en v0.3*" is a historical record left
  unchanged by design.
