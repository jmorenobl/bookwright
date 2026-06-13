# Phase 0 Research: Index locations (G13) + `bible.py` split

All unknowns were resolvable from the existing code and the spec's Clarifications
/ Assumptions; none required external research. The decisions below pin the
implementation so `/speckit-tasks` has no open questions.

## D1 — Module split shape (FR-013, Principle IV)

**Decision**: Extract into a new sibling `src/bookwright/io/_bible_builders.py`:

- The coercers and concrete builders: `_require_name`, `_coerce_year`,
  `_coerce_str_list`, `_build_character`, `_resolve_interval`, `_build_event`, the
  resolution helpers `_resolve_refs` and the new `_resolve_setting` / `_build_location`.
- The context/result dataclasses they operate on: `_Collisions`, `_MapContext`,
  `_ItemContext`, `MappedEntity`, `MapResult`, and the `_Builder` / `_ItemBuilder`
  type aliases.

Keep in `bible.py`: `map_bible` and the orchestration helpers (`_map_single_dir`,
`_map_collection`, `_map_collection_item`, `_build_item_index`, `_safe_parse`,
`_relpath`, `_slug_of`, `_record_unknown_keys`), the spec dataclasses `_DirSpec` /
`_CollectionSpec`, the `*_KEYS` constants, and `build_provenance`. `bible.py`
imports the moved names from `_bible_builders` and **re-exports** the public ones
(`MapResult`, `MappedEntity`) so `from bookwright.io.bible import …` is unchanged.

**Rationale**: The dependency direction is one-way — `_bible_builders` imports only
`golem`, `io.errors`, `io.report`, and stdlib; it imports **nothing** from
`bible.py` — so there is no import cycle. The builders and their context types form
one cohesive leaf; the orchestration that wires specs and walks the filesystem
stays on top. This lands `bible.py` well under 500 lines and creates the new module
under it, with no observable behavior change (the existing
[tests/io/test_bible.py](../../tests/io/test_bible.py) is the guard).

**Alternatives rejected**:
- *Move only `_DirSpec`/`_CollectionSpec`*: too few lines relieved and it severs a
  builder from the coercers it calls, hurting legibility.
- *A third `io/_bible_types.py` for the dataclasses*: more files than the
  one-sibling instruction warrants; the dataclasses belong with the builders that
  mutate them.

## D2 — Settings-scoped resolution index (FR-003, FR-004, Assumptions)

**Decision**: Add `settings_index: dict[str, URIRef]` to `_MapContext` and a
boolean `into_settings_index: bool = False` to `_DirSpec`. The **settings**
`_DirSpec` sets `into_settings_index=True` (alongside its existing
`into_entity_index=True`); `_map_single_dir`, after a setting entity is built,
records `ctx.settings_index[slug] = entity.uri`. The locations builder resolves
`setting:` against `ctx.settings_index` only.

**Rationale**: Resolution must be scoped to `G12_Setting` siblings (a location's
`setting` is a setting, not a character/event/research target). The existing
indices are wrong scopes: `slug_index` is characters-only (participant resolution),
`entity_index` is characters + settings + events (research targets). A dedicated
settings index is the minimal correct seam and mirrors how the participant
`slug_index` is fed for one concept and consumed by another. Settings are processed
**before** locations in `map_bible`, so the index is fully populated when a location
resolves (mirrors events resolving participants against already-built characters).

**Alternatives rejected**: reusing `slug_index` (would never resolve, settings
aren't in it) or `entity_index` (would wrongly resolve a `setting:` naming a
character or event — contradicts the Edge Cases).

## D3 — Soft-miss channel for an unresolved `setting:` (FR-004, Clarification 2026-06-14)

**Decision**: An unresolvable but well-formed `setting:` appends one
`UnresolvedParticipant(path=<location file>, entity=<location name>, name=<setting>)`
to `result.unresolved_participants`, and the location node is still built (no abort,
no edge). No new report category is introduced.

**Rationale**: `UnresolvedParticipant` already models *any* unresolved name
reference — the timeline's temporal-relation targets ride it via `_resolve_refs`.
Reusing it keeps one "unresolved reference" contract and avoids a parallel category.
The only blemish (the `Participant`-flavored name) is left untouched; the neutral
rename to `UnresolvedReference` touches the public `--json` envelope and other
commands' tests, so it is deferred to iteration 027 (out of scope here).

## D4 — `setting:` value handling (FR-002, FR-007, Edge Cases)

**Decision** — `_resolve_setting(ctx, raw, location_name, relpath) -> URIRef | None`:

| `setting:` value | Behavior |
|---|---|
| absent / YAML `null` | return `None` → no edge, no warning |
| blank / whitespace-only string | return `None` → treated as absent (no edge, no warning) |
| non-string (int, list, mapping, bool) | raise `InvalidFrontmatterError` → file **skipped** |
| present, resolves in `settings_index` | return the setting URI → `dlp:generic-location` edge emitted |
| present, does not resolve | append `UnresolvedParticipant`, return `None` → node built, no edge |

**Rationale**: `name` is required (reuses `_require_name`); `setting` is optional.
Treating a non-string as unusable front-matter mirrors how `born`/`features` reject
the wrong type and matches the Edge Case "`setting` present but not a string is
treated as unusable front-matter for that file". A blank string is most naturally
"absent" rather than a skip or a spurious soft-miss. The soft-miss path appends
**only** when the entity will build (after `_require_name`), keeping the report
consistent (a skipped file shows up only under `skipped`, never under
`unresolved_participants`).

## D5 — `NarrativeLocation` construction & provenance (FR-001, FR-005, SC-001)

**Decision**: `_build_location(uri_base, ctx, metadata, relpath)` builds
`NarrativeLocation(uri_base=uri_base, name=_require_name(metadata),
setting=_resolve_setting(...))`. The locations `_DirSpec` uses
`builder=lambda meta, rp: _build_location(uri_base, ctx, meta, rp)`,
`allowed_keys=LOCATION_KEYS` (`{"name", "setting"}`), `index=False`,
`into_entity_index=True`.

**Rationale**: The frozen `NarrativeLocation` already declares
`cross_refs = (CrossRef("setting", GENERIC_LOCATION),)` and a `setting` field, so
`to_triples()` emits the `rdf:type G13` triple plus the `dlp:generic-location` edge
when `setting` is set (omitted when `None`) — no golem change. Because the model
field name (`setting`) equals the front-matter key, `derived_assertions()` /
`build_provenance` resolve `key_lines["setting"]` to a `file:line` locator for the
cross-ref, and the identity assertion carries file-level provenance — all reused
machinery. `into_entity_index=True` feeds the research target index (the same one
characters/settings/events feed), so a research `bears_on:`/`constrains:` to a
location resolves instead of a soft-miss (FR-005); `index=False` keeps locations
out of participant resolution (locations are not event participants in v0).

## D6 — Materialization of the source-command change (FR-010, FR-011)

**Decision**: Edit only `resources/commands/bookwright-bible.md`. The location
contract stays **inline** in step 4 (settings have no separate `references/` file
either), prescribing `name:` (required) + `setting:` (optional) front-matter and
removing the "no se indexa en v0 / sin frontmatter ingerido" wording and the
`(opcional)` framing.

**Rationale**: `SKILL.md` is generated at `init`/`integration` time by
`generate_skill_md` from the packaged source command — it is not committed. The
existing integration tests ([tests/integrations/](../../tests/integrations/))
re-materialize and re-lint the skill for both `claude` and `generic`, preserving
its bilingual triggers, so the source edit is the whole change. No new reference
file is needed; the body must keep `references/…` citations resolvable and stay
within agentskills.io limits (the `lint_skill_md` gate).

## D7 — Deferral registry + parity-test pins (FR-012, SC-004)

**Decision**: Remove the `NarrativeLocation` entry from
[golem/deferrals.py](../../src/bookwright/golem/deferrals.py) `DEFERRED_CONCEPTS`
(7 → 6 entries) and update its module docstring ("Seven" → "Six"). In
[tests/golem/test_ingestion_parity.py](../../tests/golem/test_ingestion_parity.py):
add `NarrativeLocation` to `EXPECTED_REACHABLE` (6 → 7), drop it from `ORPHAN_NAMES`
(7 → 6) and `EXPECTED_VERSIONS`, change the `test_registry_well_formed` length
assertion `7` → `6`, and refresh the module docstring's reachable/orphan counts.
Add `bible/locations/` files to the `parity-exercise` fixture so the live build
observes G13 as reachable.

**Rationale**: The parity test asserts the observed orphan set equals the registry
keys; once a builder feeds G13, the test stays green only if the registry no longer
claims it deferred and the pinned sets move in lockstep (the test's own docstring
prescribes exactly this edit for "iteration 025+"). The fixture gains locations so
G13's `rdf:type` actually appears in the live build.

## D8 — Fixture additions (Assumptions, SC-001/002/003)

**Decision**: Add to `tests/fixtures/parity-exercise/bible/locations/`:
- `harbor.md` — `name: "The Harbor"`, `setting: "The Old Crossing"` (resolves
  against the existing `settings/the-old-crossing.md`) → exercises the node + the
  `dlp:generic-location` edge.
- a second location with **no** `setting:` → exercises the no-edge path and keeps
  N ≥ 2 for SC-001.

Mapper-level cases (round-trip ±setting, unresolved soft-miss, no-`locations/`-dir,
frontmatter-less skip, non-string-`setting` skip, slug collision, research
resolution via `entity_index`) are exercised as unit tests in
[tests/io/test_bible.py](../../tests/io/test_bible.py) with `tmp_path` bibles,
matching the existing test style — no new committed fixture beyond `parity-exercise`.

**Rationale**: The parity fixture must show G13 reachable through the real
pipeline; the fine-grained behavioral cases are cheaper and clearer as `tmp_path`
unit tests, consistent with how characters/settings/events are already tested.
