# Contract: `bookwright-research` source command → `SKILL.md`

The authoring contract for `resources/commands/bookwright-research.md` and the
`SKILL.md` it materializes (via the unchanged iteration-9 pipeline) into both
`.claude/skills/bookwright-research/` and `.agents/skills/bookwright-research/`.

## Materialization invariants (enforced by `generate_skill_md` + `lint_skill_md`)

| ID | Invariant | FR / Principle |
|---|---|---|
| SK-1 | filename is `bookwright-research.md`; front-matter `name: bookwright-research` (== stem) | FR-001; materializer `name_frontmatter_mismatch` |
| SK-2 | front-matter `description` ≤ 1024 chars, valid YAML | FR-003; Principle VII; lint Rule 3 |
| SK-3 | materializes for **both** `claude` and `generic` and passes `lint_skill_md` | FR-002; SC-001 |
| SK-4 | every cited `references/<file>.md` exists in packaged resources | materializer `dangling_reference` |
| SK-5 | body uses only `{ARGS}` (→ `$ARGUMENTS`); no `{SCRIPT}` or other residual token | materializer `residual_token` |
| SK-6 | `description` identical to `SKILL_DESCRIPTIONS["bookwright-research"]` | SC-009 mirror gate (R2) |

## `description` (bilingual triggers — FR-004)

Must carry ES **and** EN trigger phrases plus a negative boundary, in the shape
of the ten shipped descriptions. Triggers to cover (illustrative, not literal):

- ES: "investiga <tema>", "documenta <tema> con fuentes", "preséntame fuentes
  sobre <tema>", "research <tema>".
- EN: "research <topic>", "find sources on <topic>", "document <topic> with
  provenance".
- Negative boundary: NOT for verifying already-written prose against sources
  (that is a later `bookwright-verify`); NOT for populating character/location
  sheets (that is `bookwright-bible`).

## Body: the seven-step protocol (FR-005)

The `## Procedimiento` MUST encode exactly these steps, in order:

1. **Descomponer** el tema en sub-preguntas concretas y verificables.
2. **Buscar fuentes autorizadas**, con preferencia explícita por **fuentes
   primarias y oficiales en su lengua original** (consulta
   `[research].source_languages` como guía — FR-016).
3. Para temas **nacionalmente sensibles**, contrastar deliberadamente fuentes de
   **varias procedencias**, no una sola.
4. Registrar cada hallazgo con **procedencia completa**, incluida la **cita en
   lengua original** (y traducción cuando la lengua difiera del libro).
5. Cuando las fuentes discrepen, registrar **cada versión con su procedencia**;
   nunca colapsar en una sola "verdad".
6. Marcar qué hallazgos son **anclas** (binding) y a qué **entidad narrativa**
   (personaje, escenario, evento o `timeline`) restringen — promoviendo a ancla
   **solo** si la mejor fuente alcanza `[research].min_reliability_for_anchor`
   (FR-015).
7. Dejar **abiertas** las sub-preguntas no resueltas (no rellenar con afirmaciones
   sin fuente).

## Output & persistence steps the body MUST instruct

- Write/merge `bible/research/<topic>.md` (slug from the topic title; human title
  kept as heading), updating `bible/research/_index.md` (topic map + global open
  questions) and `bible/research/sources.md` — in the **exact** front-matter the
  reader parses (cite `references/research-format.md`). FR-006, FR-008.
- **Re-run safety** (FR-017): read existing files first; merge; never discard
  prior findings/provenance.
- If `[research].enabled = false`: tell the author the research system is inert;
  do not produce graph-bound findings (edge case).
- **Final step** (FR-018): run `bookwright graph build --json` so findings and
  anchors land in `bible/graph.ttl`.

## Out of scope in the skill (FR-007)

- No source fetching, no bundled search engine, no network/runtime dependency.
  The agent's own tools do the searching; the skill **instructs** and writes
  plain text. No new dependency is added anywhere (Constitution II).

## `references/research-format.md` (NEW reference, cited by SK-4)

A packaged reference doc giving the agent the precise front-matter contract —
the content of [research-file-format.md](research-file-format.md) rendered as
author-facing guidance (vocab tables, required facets, the translation rule, the
finding/anchor shapes, soft-vs-fatal notes). It is copied alongside the skill by
`_copy_references`.
