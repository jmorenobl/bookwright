# Contract: `bookwright-verify` Skill

The behavioural contract for the `bookwright-verify` command source and the
`SKILL.md` it materializes. Authored against this contract; verified by the existing
data-driven test sweeps plus the roster gates. This is the acceptance reference for
`/speckit-tasks`.

## C1 — Source-file presence & format (FR-001)

- A file `src/bookwright/resources/commands/bookwright-verify.md` exists.
- It is the only addition to `commands/`; the tree still ships **only** `.md`
  (no `SKILL.md`, no `.py`) — `test_command_frontmatter.test_commands_tree_ships_only_markdown`.
- The inventory is exactly the 12 expected names —
  `test_command_frontmatter.test_exactly_the_expected_commands_exist` (after
  `EXPECTED_COMMANDS` += `bookwright-verify`).

## C2 — Frontmatter invariants (FR-003, FR-004)

- `name: bookwright-verify`, equal to the filename stem (`< 64` chars).
- `description`: the bilingual ES/EN string (research D3), `< 1024` chars, parses as
  valid YAML, no `scripts`/`handoffs` keys — `test_command_frontmatter.test_frontmatter_contract`.
- The description is bilingual (ES + EN markers) —
  `test_command_activation.test_description_is_bilingual`.

## C3 — Body contract (FR-006..FR-016)

- Non-empty, Spanish, with all eight required section headings (Rol, Input,
  Procedimiento, Output, Archivos a leer, Archivos a escribir, Información faltante,
  Qué NO hacer) — `test_command_body.test_body_required_sections_and_language`.
- States it writes nothing ("solo lectura" / "no escribe nada") —
  `test_command_body.test_report_only_states_no_writes` (after `REPORT_ONLY_COMMANDS`
  += `bookwright-verify`).
- Contains the inline `bookwright graph build` call (it builds then queries, FR-005)
  — `test_command_body.test_graph_build_is_inline` (parametrize extended to include
  `bookwright-verify`).
- Instructs `bookwright graph query <SPARQL>` that selects anchors as the
  `crm:E13_Attribute_Assignment` nodes carrying `bw:promotes` and traverses
  `anchor —bw:promotes→ finding (bw:claim) —bw:supportedBy→ source` for provenance —
  **not** a non-existent `bw:Anchor`/`bw:Source` `rdf:type`; sources are typed only via
  `crm:P2_has_type → crm:E55_Type` (FR-005, research D5 has the verified query).
- Names the three contradiction kinds: anachronisms, procedural errors,
  cultural/linguistic inaccuracies (FR-006).
- Specifies the report shape: grouped by chapter/scene; each finding = quoted
  passage + violated anchor + anchor source + severity (`error`/`warning`/`info`) +
  `file:line` where known (FR-007, FR-008).
- States read-only / no auto-fix (FR-010) and the boundary vs `bookwright-continuity`
  (FR-013) and vs `factual_anchor` (FR-012).
- Handles both absent-prerequisite branches (no manuscript → point to
  `bookwright-draft`; no anchors / `[research].enabled = false` → nothing to verify)
  (FR-015, FR-016).
- Cites no `references/` file that lacks a packaged source (a dangling citation
  aborts materialization). *(verify is not expected to need a new reference file;
  if it cites one, that file must exist under `commands/references/`.)*

## C4 — Materialization in both integrations (FR-002, FR-017, SC-001)

- `iter_command_sources()` includes `bookwright-verify` with no code edit —
  `test_materialize.test_iter_command_sources_is_exactly_the_roster` (after `_ROSTER`
  += `bookwright-verify`).
- `bookwright init` materializes `bookwright-verify/SKILL.md` under both
  `.claude/skills/` and `.agents/skills/`, each passing `lint_skill_md` —
  `test_setup_materialize`, `test_e2e_materialize` (rosters auto-derived).
- The `SKILL.md` frontmatter `name` equals its parent directory; `{ARGS}` is
  substituted to `$ARGUMENTS`; no residual token survives.

## C5 — Description table coherence (FR-004, SC-009)

- `SKILL_DESCRIPTIONS["bookwright-verify"]` exists and equals the source frontmatter
  description verbatim — `test_descriptions.test_v0_equality_gate_mirrors_source_frontmatter`,
  `test_all_roster_keys_present`, `test_get_description_returns_table_value_when_keyed`
  (after both `_ROSTER`s += `bookwright-verify`).
- The description is `< 1024` chars — `test_every_description_under_cap` +
  `get_description`'s runtime assert.

## C6 — Read-only & no new dependency (FR-010, FR-014, SC-005)

- Running the materialized skill writes nothing to the project (verifiable: working
  tree unchanged after a run).
- The command introduces no network call, no search engine, no runtime dependency;
  it instructs the agent, which reasons using its own tools + the graph + the
  manuscript.

## C7 — Behavioural acceptance (manual / agent run — SC-002, SC-003, SC-006, SC-007)

Exercised in `quickstart.md` (and by iteration 17's E2E):

- Against a project whose graph carries an anchor and a manuscript passage that
  violates it: the report names the anchor, quotes the passage, cites the source,
  assigns a severity (SC-002).
- Against a manuscript fully consistent with its anchors: zero contradictions
  (SC-003).
- Triggers on both a Spanish and an English author prompt (SC-006).
- On a project with no manuscript, and on one with no anchors /
  `[research].enabled = false`: reports the absent prerequisite, zero contradictions,
  no opaque failure (SC-007).

## C8 — Out of scope (must NOT appear)

- No `bookwright verify` CLI subcommand, no verifier Python module, no JSON envelope
  (FR-009).
- No auto-correction of the manuscript (FR-010).
- No structural anchor re-audit — that is iteration 014's `factual_anchor` (FR-012).
- No GOLEM ontology class, no new predicate, no new integration (Constitution V, X).
- No `docs/` edits and no `tiny-historical/` fixture — iteration 17's scope
  (research D8).
