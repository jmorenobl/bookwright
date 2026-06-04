# Phase 1 — Data Model: `bookwright-verify` Skill

This iteration adds no runtime data structures (no Pydantic model, no graph class).
The "entities" here are the *documents and shapes* the command source defines: the
command-source layout, the report shape it instructs the agent to emit, and the
graph read-surface it consumes. They exist so `/speckit-tasks` and `/speckit-analyze`
have a concrete target, and so the authored `.md` is checkable against a contract
rather than vibes.

## E1 — The command source `bookwright-verify.md`

A packaged Markdown document under `src/bookwright/resources/commands/`, in the
iteration-8 command-source format (design § 10.1), modelled structurally on
`bookwright-continuity.md`.

**Frontmatter** (YAML):

| Field | Value / rule |
|---|---|
| `name` | `bookwright-verify` — MUST equal the filename stem and the materialized directory (FR-003; `lint_skill_md` + materializer `name_frontmatter_mismatch` guard). |
| `description` | The bilingual ES/EN string from research D3, verbatim-identical to `SKILL_DESCRIPTIONS["bookwright-verify"]` (SC-009). < 1024 chars (FR-003). |
| (no `license`) | Omitted → materializer applies the design default `Apache-2.0`. |
| forbidden | MUST NOT contain `scripts` or `handoffs` keys (`test_command_frontmatter`). |

**Body** — Spanish prose, the **eight required sections** the body-sweep detects by
ES heading keyword (`test_command_body.REQUIRED_SECTION_KEYWORDS`):

| § | Heading (ES) | Required content |
|---|---|---|
| 1 | **Rol** | The agent is a verifier/editor of factual fidelity; it compares the drafted manuscript against the research anchors and reports contradictions, touching nothing. |
| 2 | **Input** | `{ARGS}` = optional focus (a chapter or topic); base = the manuscript read against the anchors (FR-018). |
| 3 | **Procedimiento** | (i) run `bookwright graph build` to refresh the cache, then `bookwright graph query <SPARQL>` to load the **anchors** (the `crm:E13_Attribute_Assignment` nodes carrying `bw:promotes`) and traverse each `anchor —bw:promotes→ finding (bw:claim) —bw:supportedBy→ source` for provenance — **not** a non-existent `bw:Anchor`/`bw:Source` class (FR-005, D4/D5); (ii) read `manuscript/`; (iii) hunt passages that **contradict** an anchor across the three § 20.6 kinds — anachronisms, procedural errors (illegal/impossible in the setting), cultural/linguistic inaccuracies (FR-006); (iv) handle the two absent-prerequisite branches (D7); (v) write findings as the report shape E2. |
| 4 | **Output** | The report (E2): grouped by chapter/scene, prose, writes nothing. |
| 5 | **Archivos a leer** | `manuscript/`; the graph (anchors + sources via `graph query`); the `[research]` block of `manifest.toml` (to detect `enabled = false`). |
| 6 | **Archivos a escribir** | *Ninguno* — explicit "solo lectura / no escribe nada" statement (FR-010; `test_report_only_states_no_writes`). |
| 7 | **Información faltante** | No manuscript → absent prerequisite, point to `bookwright-draft`; no anchors / research disabled → nothing to verify, zero contradictions (FR-015, FR-016, D7). No `[PENDING:]` marker (read-only). |
| 8 | **Qué NO hacer** | No editing/correcting any file; no re-auditing anchor structural integrity (that is `factual_anchor`, FR-012); no fetching/scraping/new deps (FR-014); no inventing contradictions to fill the report (US1 scenario 2); no checking against the bible (that is `bookwright-continuity`, FR-013). |

**Constraints**: ≤ 500 lines (Principle IV; it is ~70); body within the
< 5000-token budget (`SKILL_BODY_MAX_TOKENS`); the sole transformable token is
`{ARGS}` (→ `$ARGUMENTS` at materialize time) — no other `{…}`/`{SCRIPT}` token may
survive (`_RESIDUAL_TOKENS` guard).

## E2 — The verification report (emitted, never persisted)

The human-readable output the body instructs the agent to produce. Not a file, not
JSON (FR-009) — the agent's response.

**Structure**: grouped by **chapter/scene** (FR-007, US2 scenario 1). Under each
scene, zero or more findings. A clean manuscript yields zero findings, with no
fabricated problems (US1 scenario 2, SC-003).

**Each finding carries four required parts** (FR-007, US2 scenario 2) plus a
location:

| Part | Source | Rule |
|---|---|---|
| (a) quoted passage | the manuscript | the offending prose, quoted |
| (b) violated anchor | the anchor's `bw:claim` (its promoted finding) | the researched fact the passage breaks; a passage breaking N anchors lists all N (edge case) |
| (c) source / provenance | the source reached via `bw:supportedBy` (`bw:reference`/`bw:author`/`bw:reliability`/`bw:originalQuote`) | cited as the graph records it, including original-language references (foreign-source edge case) |
| (d) severity | the agent's judgement | one of `error` / `warning` / `info` (`error > warning > info`) — the validation `Severity` vocabulary (clarification) |
| location | frontmatter line tracking where known | `file:line` when available; otherwise chapter/scene without a fabricated line number (FR-008, US2 scenario 3) |

**Severity rubric** (FR-007, US2 scenario 4, research D6): definite/factual
contradictions (hard anachronism; illegal/impossible procedure) → `error`; soft
cultural/stylistic nuances → `warning`/`info`. An arguable contradiction is recorded
at lower severity rather than suppressed or overstated (edge case).

## E3 — The graph read surface (consumed, not defined here)

The anchors and sources the skill loads are **iteration-012 entities**, not
redefined by this iteration. Their **graph shape** (verified against
`golem/modules/provenance.py`) is what the SPARQL must target — there is no
`bw:Anchor`/`bw:Source` `rdf:type`:

- **Anchor** — a `crm:E13_Attribute_Assignment` node identified by its **`bw:promotes`**
  edge (the discriminator: findings reify on the *same* class but never carry
  `bw:promotes`). Carries `bw:constrains` (the narrative entity it binds; optional) and
  an optional `crm:P4_has_time-span`. Loaded via `graph query`.
- **Finding** — a `crm:E13_Attribute_Assignment` reached from the anchor via
  `bw:promotes`; carries the researched fact on **`bw:claim`** and its supporting
  sources on **`bw:supportedBy`**.
- **Source** — provenance behind a finding; **emits no `rdf:type`** (typed only via
  `crm:P2_has_type → crm:E55_Type`). Cited in the report (part c) through
  `bw:reference`/`bw:author`/`bw:reliability`/`bw:originalQuote`/`bw:translation`.
- the **anchor → finding → source** chain iteration 012 emits, traversed by the
  agent's SPARQL (`bw:promotes` then `bw:supportedBy`) to attach provenance to each
  contradiction. See research **D5** for the verified reference query.

This iteration adds **no** class to the frozen GOLEM closure (Constitution X) and no
predicate; it only reads the existing `bw:`/CIDOC vocabulary.

## E4 — Roster coherence (the wiring "data")

The command-inventory rosters that must include `bookwright-verify` after E1 lands
(see research D2 for the failing-gate mapping):

- `integrations/descriptions.py::SKILL_DESCRIPTIONS` — `+1` entry (= E1 frontmatter
  description, verbatim).
- `tests/integrations/test_descriptions.py::_ROSTER` — `+1`.
- `tests/integrations/test_materialize.py::_ROSTER` — `+1`.
- `tests/resources/helpers.py::EXPECTED_COMMANDS` — `+1`; `REPORT_ONLY_COMMANDS` —
  `+1`.

Auto-derived (no edit): `iter_command_sources()` and the two `_ROSTER`s derived from
it (`test_setup_materialize`, `test_e2e_materialize`); the parametrized frontmatter/
activation/body sweeps over `command_files()`.
