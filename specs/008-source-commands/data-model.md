# Phase 1 Data Model: The 10 Bookwright Command Source Prompts

This iteration ships **documents, not Python types**. The "entities" below are the
structural shapes the authored Markdown must satisfy and that the validation suite asserts.
They are derived from the spec's Key Entities and FR-003..FR-016a.

## Entity: Command source

One authored `.md` at `src/bookwright/resources/commands/<name>.md`. The source-of-truth
for one slash command's logic.

| Field | Type | Rule |
|---|---|---|
| *file basename* | string | MUST equal the command `name` and the future parent-dir name (FR-002, Constitution VII). The 10 names are fixed by FR-001. |
| `name` (frontmatter) | string | Required; `name` == basename; < 64 chars (FR-003, VII). |
| `description` (frontmatter) | string | Required; < 1024 chars; bilingual ES+EN trigger phrasing; sibling-disambiguating (FR-004, US3). |
| *frontmatter — forbidden keys* | — | No `scripts:` (FR-005); no `handoffs:` or other agent-specific keys (FR-006). |
| body | Markdown (Spanish prose) | Non-empty; < 5000 tokens (FR-015); contains the eight required sections below (FR-007..FR-014). |

**Classification** (single source of truth — spec "Command classification"; mirrored as
`helpers.GENERATIVE_COMMANDS` / `helpers.REPORT_ONLY_COMMANDS` for the tests):
- *Generative* (constitution, bible, outline, scenes, draft, synopsis): write project
  files; MUST carry the marker rule (FR-016) and the update-in-place rule (FR-016a).
  `synopsis` regenerates its short/long blocks to track current state (FR-023).
- *Report-only* (clarify, analyze, continuity, checklist): MUST state they write nothing
  to the project (FR-012).

### Required body sections (FR-007..FR-014) — order is advisory, presence is required

1. **Rol / contexto del agente** (FR-007) — who the agent is for this command.
2. **Input esperado** (FR-008) — what it consumes, incl. any positional arg
   (`<scene_id>`, `<artifact>`) via the neutral `{ARGS}` placeholder (not `$ARGUMENTS`).
3. **Procedimiento** (FR-009) — a numbered step-by-step.
4. **Output esperado** (FR-010) — report shape and/or files produced.
5. **Archivos a leer** (FR-011) — concrete project paths consumed.
6. **Archivos a escribir** (FR-012) — concrete project paths produced, **or** an explicit
   "report-only, no escribe nada" statement.
7. **Regla de información faltante** (FR-013) — `[PENDING: …]`-and-continue vs stop-and-ask
   (generative commands link `references/pending-protocol.md`).
8. **Qué NO hacer** (FR-014) — the command's anti-goals.

## Entity: Description (activation surface)

A < 1024-char bilingual string. Both invites the correct request and disambiguates against
sibling commands. The *only* signal driving implicit activation (US3). Validation: present,
< 1024 chars, contains ES and EN markers, contains the sibling-disambiguating keyword for
the four documented pairs (SC-003).

## Entity: Reference file

An auxiliary `.md` under `src/bookwright/resources/commands/references/` holding extended
domain context, linked from bodies for tier-3 progressive disclosure.

| Field | Rule |
|---|---|
| location | `references/<topic>.md` |
| content | Spanish prose; domain depth (GOLEM module, Propp, Greimas, the PENDING protocol). |
| reachability | Every reference MUST be cited by ≥1 body (no orphans by intent); every body citation MUST resolve to a shipped file (FR-029, hard gate). |

Planned roster (R2): `golem-character.md`, `golem-relationships.md`,
`golem-events-timeline.md`, `propp-functions.md`, `greimas-actants.md`,
`pending-protocol.md`.

## Entity: Fill-marker `[PENDING: <question>]`

The stable English token + Spanish question a generative command writes wherever the brief
left a field unsupplied.

| Rule | Detail |
|---|---|
| Spelling | Exactly `[PENDING: <pregunta>]` (FR-016). `[PENDIENTE]` is superseded. |
| YAML quoting | In a string-typed frontmatter field: `name: "[PENDING: …]"` — quoted, else parsed as a list and the file is discarded. |
| vs stop-and-ask | Mark+continue when a field is merely absent; stop+ask only when proceeding would invent load-bearing canon (Edge Cases, R3). |

## Entity: Project artifacts (read/write targets)

The paths in an initialized project the commands consume/produce — `bible/`, `outline/`,
`manuscript/` — produced by `init` (iter 4) and the iteration-7 molds. **Consumed, not
created here.** Each command body names concrete targets (per FR-018..FR-027), e.g.:

| Command | Reads | Writes |
|---|---|---|
| constitution | brief + constitution mold | `bible/constitution.md` (+ `graph build --json`) |
| bible | constitution + brief + molds | full bible set; `bible/pov-structure.md` only if multi-POV |
| outline | constitution + bible | `outline/{arcs,structure,synopsis}.md` |
| scenes | outline + bible | `outline/scenes.md` |
| draft `<scene_id>` | outline + scene + bible | `manuscript/cap-NN.md` (scene section) |
| synopsis | current state | `outline/synopsis.md` (short 250–350w + long 1000–2000w) |
| clarify | any artifact | — (report-only) |
| analyze | constitution+bible+outline+scenes | — (report-only) |
| continuity | manuscript+bible (+`graph build --json`) | — (report-only) |
| checklist `<artifact>` | one named artifact | — (report-only) |
