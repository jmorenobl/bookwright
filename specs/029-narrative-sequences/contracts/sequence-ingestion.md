# Contract: narrative-sequence ingestion

This feature exposes no new CLI subcommand and no new `--json` envelope. Its two
contracts are (1) the **authoring surface** — the unit-card front-matter keys —
and (2) the **observable graph shape** a SPARQL query sees after `graph build`.

## 1. Authoring contract — `outline/units/<unit>.md` front-matter

```yaml
---
name: "The Flood Arrives"        # required (unchanged, iter 028)
functions: [interdiction]        # optional list[str] (unchanged)
roles: [protagonist]             # optional list[str] (unchanged)
sequence: "Act I"                # NEW — optional str: the plot line this beat joins
order: 1                         # NEW — optional int: position within that sequence
---
Body prose (never indexed).
```

Recognised keys: `name`, `functions`, `roles`, `sequence`, `order`. Any other key
is a soft `unknown_keys` warning.

| Input | Outcome |
|---|---|
| `sequence` present (non-blank str) | the unit joins sequence `make_slug(sequence)` |
| `sequence` absent / blank | no membership; unit built exactly as iter 028 |
| `sequence` non-str | card **skipped** (recorded reason); build continues |
| `order` int (not bool) | member position within its sequence |
| `order` omitted | member placed last in its sequence, slug-ordered |
| `order` non-int (bool/float/str/list) | card **skipped** (recorded reason) |
| `order` present, `sequence` absent | `order` ignored (soft `UnknownKey "order"`) |

## 2. Graph contract — observable after `bookwright graph build`

For each distinct `sequence` slug named by ≥ 1 surviving card:

```turtle
<…/narrative-sequence/act-i>  a  golem:G7_Narrative_Sequence .
<…/narrative-sequence/act-i>  dlp:proper-part  <…/narrative-unit/the-flood-arrives> .
<…/narrative-sequence/act-i>  dlp:proper-part  <…/narrative-unit/the-levee-breaks> .
```

Guarantees:

- **Exactly one** `NarrativeSequence` per distinct slug (dedup, FR-002 / SC-001).
- **Exactly K** `dlp:proper-part` edges for a sequence named by K surviving cards,
  to those units and no others (FR-003 / SC-002).
- Members assembled in ascending `order` (FR-005/FR-006 rules for missing/dup
  `order`); the **builder member-tuple order** is the contract, not RDF triple
  order — RDF is unordered (FR-003).
- A second build is byte-for-byte identical (determinism, SC-004).
- Zero `NarrativeSequence` entities when no card declares `sequence` (FR-011 /
  SC-006).

### Verifying member order from a derived `bible/graph.ttl`

Because RDF triples are unordered, member order is verified by reading the
**builder's `units` tuple** (the unit-test seam), not by triple position. A
SPARQL consumer that needs order joins each member back to its unit's `order`
authoring value via the card — out of scope here (no `order` literal is emitted
onto the graph; only `dlp:proper-part` membership is). The contract this
iteration guarantees is membership + the assembled tuple order.

## 3. Provenance contract (FR-010)

Each sequence identity and each `dlp:proper-part` assertion is reified as a
`crm:E13_Attribute_Assignment` with **file-level** source (`relpath`, no `:line`),
the source being the first assembled member's card — consistent with minted
`NarrativeFunction` provenance.

## 4. Parity contract (FR-013)

After this feature, `tests/golem/test_ingestion_parity.py` observes the orphan
set as exactly `{RelationshipRole (G6), PsychologicalState (G3)}`,
`len(DEFERRED_CONCEPTS) == 2`, and `NarrativeSequence` in the reachable set —
read from a real build of the `parity-exercise` fixture, never hand-listed.

## 5. Skill contract (FR-012 / SC-008)

The re-materialized `bookwright-outline` `SKILL.md` (for `claude` and `generic`)
documents the optional `sequence`/`order` unit keys in **both** in-file
enumerations (the per-unit "what to create" step and the "Archivos a escribir"
summary) and still triggers on ES/EN prompts (passes `lint_skill_md`).
