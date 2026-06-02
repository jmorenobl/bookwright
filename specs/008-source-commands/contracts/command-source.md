# Contract: Command-source document format

The authored-document contract every `src/bookwright/resources/commands/<name>.md` MUST
satisfy. This is the source format consumed by the iteration-9 materializer — it is *not*
a SKILL.md and carries no agent-specific affordances.

## Frontmatter

```yaml
---
name: <command-name>            # REQUIRED. == file basename == future parent dir. < 64 chars.
description: <bilingual string>  # REQUIRED. < 1024 chars. ES + EN triggers. Sibling-disambiguating.
---
```

- **REQUIRED keys**: `name`, `description`.
- **FORBIDDEN keys**: `scripts:` (FR-005), `handoffs:` and any other agent-specific key
  (FR-006). Other agentskills.io-valid keys are permitted only if genuinely needed.
- Frontmatter parses cleanly through `bookwright.io.frontmatter.parse_frontmatter`.

## Body (Spanish prose, < 5000 tokens)

Eight required sections — presence required, order advisory:

| # | Section (es) | Requirement |
|---|---|---|
| 1 | Rol / contexto del agente | FR-007 |
| 2 | Input esperado (`{ARGS}` placeholder, positional arg if any) | FR-008 |
| 3 | Procedimiento (numbered) | FR-009 |
| 4 | Output esperado | FR-010 |
| 5 | Archivos a leer | FR-011 |
| 6 | Archivos a escribir **or** "report-only, no escribe nada" | FR-012 |
| 7 | Regla de información faltante (`[PENDING:…]` vs preguntar) | FR-013 |
| 8 | Qué NO hacer | FR-014 |

## Inline-CLI rule (FR-017)

Any command needing the project graph writes the call inline in the procedure as
`bookwright graph build --json` and consumes the returned JSON. No wrapper script is
assumed. `bookwright-constitution` and `bookwright-continuity` MUST do this.

## Marker rule (FR-016, FR-016a) — generative commands

- Write the exact token `[PENDING: <pregunta en español>]`.
- Quote it in a string-typed YAML field: `name: "[PENDING: …]"`.
- Update-in-place: read any already-populated target, preserve human-authored content and
  resolved `[PENDING]` answers, fill only gaps and still-open markers, never overwrite or
  duplicate authored prose.
- Link `references/pending-protocol.md` rather than re-inlining the rule.

## References (FR-028, FR-029)

Heavy domain context is offloaded to `references/<topic>.md` and linked from the body.
Every `references/…` path a body cites MUST resolve to a shipped file.

## Per-command behavioral contract (FR-018..FR-027)

Each body encodes its § 10.4 row: role, exact read targets, exact write targets (or
report-only), procedure, and anti-goals — see [data-model.md](../data-model.md) read/write
table. `bookwright-draft` and `bookwright-checklist` MUST define behavior for an
unknown `<scene_id>` / `<artifact>` (report and ask, never fabricate). Checking commands
run on an empty project MUST report "prerequisite missing", not error opaquely.

## Argument placeholder (FR-008)

Commands that take a positional argument (`bookwright-draft <scene_id>`,
`bookwright-checklist <artifact>`) reference it in the body via the **neutral placeholder
`{ARGS}`** (single brace). The source MUST NOT hard-code an agent-specific token such as
`$ARGUMENTS`; iteration-9 materialization maps `{ARGS}` to each integration's substitution
syntax. The single brace is deliberate: it survives Jinja-based materialization untouched,
whereas `{{…}}` would be consumed by Jinja's delimiters.

## Executability rubric (SC-004)

The SC-004 acceptance read is checklist-gated, not a subjective impression. For each body
under review, confirm:

1. Every **read** path named is a real project path (`bible/…`, `outline/…`, `manuscript/…`).
2. Every **write** path is concrete, or the body declares itself report-only.
3. Each procedure step has an unambiguous action + object, in order; no step assumes
   context not read in an earlier step.
4. The `[PENDING: …]`-vs-stop-and-ask decision is stated explicitly (or links
   `references/pending-protocol.md`).
5. Any CLI call is literal (`bookwright graph build --json`) and the body says what to do
   with the JSON it returns.
6. The "Qué NO hacer" section bounds the behavior (names the anti-goals).
7. Any positional argument is referenced via `{ARGS}` and its unknown-value behavior is
   defined (`draft`, `checklist`).
