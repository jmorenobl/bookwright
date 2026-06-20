# Contract — the fixture oracle (`tiny-quest/expected-narrative.md`)

The co-located oracle's **YAML front-matter** is the single source of truth for every
fact the workflow test asserts. The test loads it once
(`parse_frontmatter(path.read_text(encoding="utf-8")).metadata`) and asserts against
it — **no count or identifier is hard-coded in the test** (FR-005, FR-008, FR-009;
mirrors `tiny-historical/expected-status.md` ↔ `test_orchestration_workflow.py`).

## Front-matter schema

```yaml
units:                       # G9 NarrativeUnit (build, Group A)
  count: <int>               #   exact number of unit cards that build (skipped cards excluded)
  slugs: [<str>, ...]        #   the G9 unit slugs (derived from `name`), sorted or insertion-order

functions:                   # G10 NarrativeFunction (build, Group A)
  count: <int>               #   distinct function slugs across all cards (slug-deduped)
  typed:                     #   function slug -> matched Propp term (last URI path segment)
    <slug>: <propp-term>     #   present only for names that resolve to a propp.ttl E55_Type
  # a function whose name matches no Propp term is omitted from `typed` (untyped)

sequence:                    # G7 NarrativeSequence (build, Group A)
  name: <str>                #   the sequence display name (first card in glob order to name it)
  members: [<slug>, ...]     #   ordered G9 unit slugs (ascending `order`, slug tie-break)

roles_resolved:              # unit -> resolved role cross-refs (build, Group A)
  <unit-slug>: [<role-slug>, ...]

narrative_structure:         # validator findings (validate, Group B) — EXACT, not lower bound
  orphan_beats:              #   Rule a: G9 units in no G7 sequence
    - unit: <unit-slug>
      source: <path-or-path:line>
  unresolved_roles:          #   Rule c: roles: slug resolving to no character role
    - unit: <unit-name>      #   the UnresolvedReference.entity (the unit's `name`, not slug)
      role: <role-slug-or-raw>
      source: <path-or-path:line>
  counts:                    #   scoped to validator == "narrative_structure"
    warning: <int>           #   == len(orphan_beats) + len(unresolved_roles)
    error: 0                 #   the validator is warning-only (031)
```

## Field rules

- **Determinism**: every value must be byte-for-byte stable across rebuilds (FR-011).
  `slugs`/`members`/`typed` come from deterministic minting + the total member order
  (`_member_sort_key`); `source` strings come from the `E13`-resolved `file:line` and
  are pinned **after** a real build confirms them (data-model D3). If a `source` line
  number is volatile, record the file path only (`split_source` tolerates both); the
  validator falls back to the card relpath when provenance is absent.
- **Exactness**: `orphan_beats` and `unresolved_roles` enumerate the **complete** set —
  the test asserts equality, so any extra or missing finding fails (edge case "exact,
  unambiguous set"). The fixture must therefore be built so the *only* orphan is the
  one `sequence`-less card and the *only* unresolved role is the one planted slug.
- **`typed` ↔ Propp activation**: `typed` records the typings present **with Propp
  active**. The non-regression assertion (Group C) rebuilds with `active=[]` and
  requires `typed` to be entirely absent from the graph while `units`/`functions.count`/
  `sequence`/`roles_resolved` stay identical.
- **No oracle field may be derived from the test's own expectations** — the oracle is
  authored to describe the planted fixture, and the test reads it; the fixture and
  oracle are reviewed together so they cannot silently disagree.

## Validator finding shape (for Group B cross-check)

Each `narrative_structure` violation in `validate --json` `violations[]` has
(`Violation.to_json`):

```json
{ "validator": "narrative_structure", "severity": "warning",
  "message": "...", "source": "outline/units/<card>.md[:<line>]", "triples": [] }
```

- **orphan beat** message contains the unit slug and the phrase `orphan beat`.
- **unresolved role** message names the unit and the role and the phrase
  `resolves to no character role`.

The test matches each oracle entry to a `violations[]` element by (`unit`/`role`,
`source`) and asserts `severity == "warning"`; it also asserts the
`summary.by_severity` / scoped counts equal `narrative_structure.counts`.
