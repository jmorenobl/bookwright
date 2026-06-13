# Contract: `bible/locations/*.md` ingestion

The interface this feature exposes is the **front-matter contract** an author
writes and the **observable mapper outputs** the build produces. It mirrors the
existing `bible/settings/*.md` contract. There is no new CLI surface and no
`--json` envelope change.

## Input — location front-matter

```yaml
---
name: "The Harbor"        # required, non-empty string — identity source (slug derives from it)
setting: "The Old Crossing"   # optional string — names a sibling bible/settings/ setting
---

## Qué se ve / oye / huele / toca
…human prose, not ingested…

## Atmósfera dominante
…human prose, not ingested…
```

- File location determines type (one `NarrativeLocation` per
  `bible/locations/*.md`), exactly as `bible/settings/` determines `Setting`.
- Only `name` and `setting` are ingested; any other key is a soft `unknown_keys`
  warning (emitted only once an entity is produced).

## Output — observable mapper results (`MapResult`)

| Input case | `mapped` | Triples | Soft warning | `skipped` | FR / SC |
|---|---|---|---|---|---|
| `name` only | 1 `NarrativeLocation` node, slug from `name`, file-level identity provenance | `rdf:type G13` | — | — | FR-001, SC-001 |
| `name` + resolvable `setting` | 1 node | `rdf:type G13` + `dlp:generic-location → <setting>` (with `setting:` line provenance) | — | — | FR-003, SC-002 |
| `name` + unresolvable `setting` (string) | 1 node | `rdf:type G13` only (no edge) | 1 `UnresolvedParticipant` (`path`=file, `entity`=name, `name`=setting) | — | FR-004, SC-002 |
| `name` + absent / blank `setting` | 1 node | `rdf:type G13` only | — | — | FR-002 |
| missing / empty / non-string `name` | — | — | — | 1 `SkippedFile` | FR-007 |
| `setting` present but non-string | — | — | — | 1 `SkippedFile` | FR-007, Edge Cases |
| frontmatter-less v0 file | — | — | — | 1 `SkippedFile` | FR-009, SC-005 |
| two files → same slug | — (raises) | — | — | — | FR-006 |
| no `bible/locations/` dir | — | — | — | — (no-op) | FR-008, SC-005 |

- Every built location also enters `result.entity_index` (keyed by slug), so a
  research `bears_on:` / `constrains:` naming the location resolves to its node
  instead of a soft-miss (FR-005, SC-003).
- A slug collision raises `SlugCollisionError` (concept `"NarrativeLocation"`),
  carrying both source paths in its `--json` `details.sources` — identical shape
  to characters/settings.

## Invariants

- **No ontology growth** (Principle X): `G13_Narrative_Location` and
  `dlp:generic-location` already exist; nothing is added to the frozen closure.
- **No new report category**: the unresolved `setting:` rides the existing
  `unresolved_participants` list (Clarification 2026-06-14).
- **Behavior preservation**: for every input that does **not** involve
  `bible/locations/`, `MapResult` is byte-for-byte identical to before the change
  (the module split is invisible).
- **Determinism**: a second independent build of the same tree yields an identical
  graph and verdict (consistent with the parity test's determinism check).

## Parity guard (FR-012, SC-004)

After this iteration the live `parity-exercise` build observes
`golem:G13_Narrative_Location` among its `rdf:type`s, so:

- the deferral registry has exactly **6** entries (no `NarrativeLocation`);
- the parity reachable set has exactly **7** concepts (the prior six +
  `NarrativeLocation`);
- `tests/golem/test_ingestion_parity.py` stays green with G13 reachable.
