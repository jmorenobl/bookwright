# Contract: `outline/units/` ingestion (units pass)

The interface this feature exposes is the **graph the build pipeline produces** from
`outline/units/*.md`, consumed by SPARQL and by the existing `graph build` / `status`
JSON envelopes. No new CLI verb, flag, or JSON field is added; the contract is the set
of triples and report entries the units pass contributes.

## Entry point

```python
# src/bookwright/io/outline.py
def map_outline(
    project_root: Path,
    outline_dir: Path,          # = root / manifest.paths.outline
    uri_base: str,
    result: MapResult,          # the MapResult map_bible already produced
) -> None:
    """Append NarrativeUnit/NarrativeFunction entities + soft warnings into `result`,
    resolving `roles` against `result.roles_index` (populated by the character pass)."""
```

Called by `commands/_graph.build_project_graph` immediately after `map_bible`:

```python
result = map_bible(root, bible_dir, uri_base)
map_outline(root, root / manifest.paths.outline, uri_base, result)
# unchanged below: iterate result.mapped → to_triples + build_provenance; build report
```

## Graph contract (per built project)

Given `outline/units/` with N well-formed cards declaring M distinct function slugs and
referencing roles:

| Guarantee | Detail |
|---|---|
| C1 | Exactly N `?u a golem:G9_Narrative_Unit` for N well-formed cards (SC-001). |
| C2 | Exactly M `?f a golem:G10_Narrative_Function` (slug-deduplicated across all cards) (SC-001). |
| C3 | A card with K distinct function slugs → exactly K `?u crm:P67_refers_to ?f` edges (SC-002). |
| C4 | A `roles` name whose slug is played by C characters → exactly C `?u crm:P67_refers_to ?role` edges, one per character-scoped role node (SC-004). |
| C5 | A `roles` name matching no character role → 0 role edges + exactly one unresolved-reference warning; the unit is still present (SC-004). |
| C6 | Repeated function/role names within one card are slug-deduplicated before counting (SC-002, SC-004). |
| C7 | Identity + every unit→function / unit→role assertion is reified as a `crm:E13_Attribute_Assignment` resolving the `functions`/`roles` field to `relpath:line` where locatable (FR-010). |
| C8 | The unit's prose body contributes no triple (FR-003). |
| C9 | A project with no `outline/units/` directory produces a byte-for-byte identical graph to before this feature (SC-006). |

## Report / skip contract

Routed through the existing `BuildReport` (no new fields):

| Guarantee | Detail |
|---|---|
| R1 | Malformed cards (no front-matter, bad YAML, unreadable, missing/empty/non-string `name`, non-list `functions`/`roles`) appear under `skipped` with a reason; the build continues, exit 0 (SC-003). |
| R2 | A skipped card contributes **only** a `skipped` entry — no partial function entity, no `unknown_keys`, no `unresolved_references`. |
| R3 | A unit-`name` slug collision raises `SlugCollisionError` → `graph build` exits non-zero with the standard `--json` error envelope (FR-008, Principle IX). |
| R4 | `files_processed`, `entities`, and `unresolved_references` counters include the units pass automatically (one shared `MapResult`). |

## Authoring-surface contract

| Guarantee | Detail |
|---|---|
| A1 | The materialized `bookwright-outline` `SKILL.md` for **both** `claude` and `generic` instructs creating `outline/units/` cards with `name`/`functions`/`roles` front-matter and still triggers on ES + EN prompts; passes `lint_skill_md` (SC-007). |
| A2 | `bookwright init` scaffolds an `outline/units/` directory (mirrors `bible/settings/`) (FR-012). |

## Non-goals (unchanged contracts)

- No new ontology class/property; `golem.ttl` frozen (FR-015, Principle X).
- `graph build` / `status` JSON schemas unchanged (Principle IX).
- `outline/arcs.md`, `structure.md`, `synopsis.md`, `scenes.md` remain author-only prose.
