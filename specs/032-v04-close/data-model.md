# Phase 1 — Data Model: v0.4 close (032)

This iteration introduces **no new domain entity, manifest field, or ontology
class**. The "data model" here is (1) the fixture's authored-text shape, (2) the
oracle's front-matter schema, and (3) the deferral-registry data edit. All three are
*existing* shapes; this document fixes the concrete instances.

## 1. The fixture project (`tests/fixtures/tiny-quest/`)

A valid, loadable Bookwright project (standard skeleton + populated
`outline/units/`), source-only — the derived `bible/graph.ttl` is rebuilt in a
`tmp_path` copy, never committed.

### 1.1 `manifest.toml`

Same shape as the other `tiny-*` manifests, with a **`[vocabularies]` block declaring
Propp active**:

```toml
[bookwright]
cli_version_min = "0.0.1"
schema_version  = "golem-1.1"
manifest_version = "1"
uri_base = "https://example.org/tiny-quest/"
indexer  = "rdflib"

[book]
title = "Tiny Quest"
type = "novel"
language = "es"            # Spanish prose; English identifiers/keys
authors = ["Bookwright Test Suite"]
status = "drafting"

[vocabularies]
active = ["propp"]         # FR-003 — turns on crm:P2_has_type typing for functions

[validators]
enabled  = []              # all built-ins active (narrative_structure auto-discovered)
disabled = []
custom   = []

[paths]
# manuscript/ bible/ outline/ graph=bible/graph.ttl constitution=bible/constitution.md
```

### 1.2 Characters (`bible/characters/*.md`) — the role-resolution targets

Each declares `narrative_roles` so a unit `roles:` slug **resolves** against the
character-scoped role index (`result.roles_index`). Suggested cast (final names fixed
during implement; the oracle is the source of truth):

| Card | `narrative_roles` | Purpose |
|---|---|---|
| `<hero>.md` | `[protagonist]` | resolves the `protagonist` role refs |
| `<villain>.md` | `[villain]` | resolves the `villain` role refs |
| `<helper>.md` | `[helper]` | resolves the `helper` role refs |

**No** character declares `dragon` (or whatever the planted unresolved slug is) — that
is the deliberate miss for Rule c (D3).

### 1.3 Unit cards (`outline/units/*.md`) — G9/G10/G7 + the two findings

Frontmatter keys recognised by `map_outline` (`UNIT_KEYS = {name, functions, roles,
sequence, order}`). Concrete plan:

| Card | `functions` (Propp) | `roles` | `sequence` | `order` | Notes |
|---|---|---|---|---|---|
| `01-interdiction.md` | `[interdiction]` | `[protagonist]` | `"Quest"` | 1 | sequenced; function typed by Propp |
| `02-departure.md` | `[departure]` | `[protagonist, helper]` | `"Quest"` | 2 | sequenced; two resolved roles |
| `03-villainy.md` | `[villainy]` | `[villain]` | `"Quest"` | 3 | sequenced |
| `04-struggle.md` | `[struggle, victory]` | `[protagonist, villain]` | `"Quest"` | 4 | two functions, dedup across cards if reused |
| `05-return.md` | `[return]` | `[protagonist]` | `"Quest"` | 5 | sequenced — closes the G7 |
| `06-omen.md` | `[interdiction]` | `[dragon]` | *(absent)* | — | **orphan beat** (no `sequence`) **and** carries the **unresolved role** `dragon` |

> The exact card set, function list, and which function names match canonical Propp
> labels are finalized in implement and recorded in the oracle (§ 2). The invariants
> the implementation MUST hold:
> - **Exactly one** unit has no `sequence` key → exactly one orphan beat (Rule a).
> - **Exactly one** `roles:` slug across all cards resolves to no character role →
>   exactly one unresolved-role finding (Rule c). (Co-locating it on the orphan card
>   is fine — the two findings are independent: one from SPARQL over the graph, one
>   from the `UnresolvedReference` records.)
> - Every other unit is a `dlp:proper-part` of the single `"Quest"` G7 sequence, and
>   every other `roles:` slug resolves.
> - All function names are canonical Propp terms (so each resolves to a
>   `crm:E55_Type` term and gains a `crm:P2_has_type` edge under active Propp).

### 1.4 Derived graph (rebuilt, never committed)

Building `tiny-quest` yields, deterministically:

- **G9 `NarrativeUnit`** — one per unit card (6 in the plan above).
- **G10 `NarrativeFunction`** — one per *distinct* function slug across all cards
  (slug-deduped via `ctx.functions_index`), each carrying a `crm:P2_has_type` edge to
  its Propp `crm:E55_Type` term (Propp active).
- **G7 `NarrativeSequence`** — one (`"Quest"`), with its sequenced units as ordered
  `dlp:proper-part` members (ascending `order`).
- **Role cross-refs** — one unit→character-role edge per resolved `roles:` slug.
- **No** typing/edge for the orphan card's `dragon` role (unresolved) and **no** G7
  membership for the orphan card (orphan beat).

## 2. The oracle (`tests/fixtures/tiny-quest/expected-narrative.md`)

YAML front-matter = the **single source of truth**; the body is Spanish explanation
(the `tiny-historical/expected-findings.md` precedent). Loaded once via
`parse_frontmatter(path.read_text()).metadata`. Full schema in
`contracts/fixture-oracle.md`; the shape:

```yaml
# Build-time graph facts (asserted in workflow Group A)
units:
  count: 6
  slugs: [interdiction-beat, departure-beat, ...]   # G9 unit slugs (stable, from name)
functions:
  count: 6                                           # distinct G10 function slugs
  typed:                                             # slug -> matched Propp term (last path segment)
    interdiction: "interdiction"
    departure: "departure"
    # ...
sequence:
  name: "Quest"
  members: [interdiction-beat, departure-beat, villainy-beat, struggle-beat, return-beat]  # ordered
roles_resolved:                                      # unit slug -> resolved role slugs
  interdiction-beat: [protagonist]
  # ...

# Validate-time findings (asserted in workflow Group B) — EXACT set
narrative_structure:
  orphan_beats:
    - unit: omen-beat                                # the one G9 in no G7
      source: "outline/units/06-omen.md"            # file or file:line (pinned)
  unresolved_roles:
    - unit: "Omen"                                   # the UnresolvedReference.entity (unit name)
      role: dragon
      source: "outline/units/06-omen.md"            # file or file:line (pinned)
  counts:
    warning: 2                                       # 1 orphan + 1 unresolved role
    error: 0
```

The test asserts **exact** sets/counts (FR-005/SC-002), never lower bounds. The
`source` strings are pinned after a real build confirms the `E13`-resolved
`file:line` (D3) — recorded verbatim so a future provenance/line drift fails loudly.

## 3. Deferral-registry data (the edit)

`src/bookwright/golem/deferrals.py` — pure-data edit, no structural change:

```python
DEFERRED_CONCEPTS: dict[str, DeferralNote] = {
    "RelationshipRole":   DeferralNote(reason="… (G6)", target_version="demand-pulled"),
    "PsychologicalState": DeferralNote(reason="… (G3)", target_version="demand-pulled"),
}
```

`DeferralNote` docstring extended to admit `"demand-pulled"` as a first-class state
(D7). Mirror in `tests/golem/test_ingestion_parity.py`:

```python
EXPECTED_VERSIONS: dict[str, str] = {
    "RelationshipRole":   "demand-pulled",
    "PsychologicalState": "demand-pulled",
}
```

### Invariants the parity test still enforces (must stay green)

- `set(DEFERRED_CONCEPTS) == ORPHAN_NAMES == {RelationshipRole, PsychologicalState}`
  (unchanged — the *set* does not move; D7).
- `{name: note.target_version …} == EXPECTED_VERSIONS` (now `"demand-pulled"` on both
  sides — FR-019/FR-019a).
- `all(note.target_version != "undecided")` — still holds (`"demand-pulled"` ≠
  `"undecided"`; FR-017).
- The live orphan set derived from the real `parity-exercise` build still equals the
  registry keys (unaffected — `parity-exercise` is untouched).

## 4. `DEBT.md` data (the two target-line edits, FR-019b)

| Entry | Old `Target:` | New `Target:` |
|---|---|---|
| DEBT-001 (`NarrativeRole` dead concept) | `v0.4` | a concrete later structural iteration / demand-pulled horizon (no shipped version) |
| DEBT-002 (constitution Scope & Release drift) | `v0.4 (cierre)` | the manual `v0.4.0` release/amendment step that owns the MINOR amendment |

Both entries stay **abierta** (open/deferred) — only the stale target string changes.

## 5. Release metadata (the `bookwright-release` step — not branch data)

Listed for completeness; produced by the release skill (D9), not committed on the
branch:

| Datum | Source of truth | Value |
|---|---|---|
| `__version__` | `src/bookwright/__init__.py` | `"0.4.0"` |
| CHANGELOG | `CHANGELOG.md` | `## [0.4.0] — <date>` consolidating 028–032 (+ "Design decisions revised during implementation" subsection iff any 028–032 divergences were recorded) |
| Status table / prose | `CLAUDE.md` | 032 ✅ merged; milestone prose → v0.4 released |
| Design status | `bookwright-design.md` | sections where shipped code diverged |
| Tag | git | annotated `v0.4.0` |
