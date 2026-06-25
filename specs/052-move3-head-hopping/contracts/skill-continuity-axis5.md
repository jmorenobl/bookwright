# Contract — `bookwright-continuity` fifth axis (head-hopping / broken focalization)

The skill-body and description contract for the head-hopping axis. Verified by
materialization + lint + body/activation oracles — **not** by asserting LLM output
(Principle VIII split; § 20.6.2 decision 4).

## Source files

- `src/bookwright/resources/commands/bookwright-continuity.md` (frontmatter + body)
- `src/bookwright/integrations/descriptions.py` (`SKILL_DESCRIPTIONS["bookwright-continuity"]`
  — verbatim mirror, FR-015)

## C1 — Fifth axis present in `## Procedimiento`

The procedure MUST add a **fifth axis** ("head-hopping / saltos de punto de vista /
focalización rota") preserving the existing four (bible compliance, character-arc coherence,
timeline coherence, undeclared characters). The fifth-axis procedure MUST instruct the agent
to:

- **(a) Read the declared narrative voice** from `bible/constitution.md` ("Voz narrativa: …")
  and proceed **only** under a third-person *limited* / focalized voice. Under **omniscient**
  or **first person**, head-hopping does **not** apply — report nothing for this axis
  (Acceptance Scenario 2; Edge Cases).
- **(b) Read the focal POV per chapter** from `bible/pov-structure.md` (the "Calendario de
  POV" section).
- **(c) Read the character roster** (`bible/characters/*.md` `name:`, as the fourth axis does).
- **(d) Judge**, per chapter, whether the prose attributes **interiority** (verbs of
  thinking / feeling / perceiving, interior monologue) to a character who is **not** the
  focal POV of that chapter.
- **(e) Grounding-gap handling**: when the POV calendar is **absent**, has **no "Calendario
  de POV" section**, or is a **`[PENDING: …]` placeholder** (treated as no focal POV declared,
  consistent with how `focalization` treats a `[PENDING]` voice, iteration 037), **report the
  grounding gap and do NOT guess** the focal POV — a missing anchor is a judgment-input gap,
  never a fabricated head-hop (Acceptance Scenario 3; Edge Cases).

## C2 — Grounding cited

The procedure MUST cite the grounding (§ 20.6.2 decision 3): the **declared voice** + the
**POV calendar** (`bible/pov-structure.md`) + the **roster** — exactly what the deleted
deterministic heuristic could not resolve (FR-003).

## C3 — `## Output` reports head-hops as deviations

`## Output` MUST describe the head-hop report shape: each head-hop is **one more deviation**
— a manuscript **quote**, the phrase naming the **non-focal character's interiority under the
focal POV in the chapter** (e.g. "interiority of *Irene* under the POV of *Teo* in
*<chapter>*"), and a **suggestion** (FR-004). It is a **judgment, not an `error`**: no `error`
is born from this axis (FR-014).

## C4 — "Archivos a leer" gains `bible/pov-structure.md`

The "Archivos a leer" section MUST list `bible/pov-structure.md` (its "Calendario de POV"
section) as a newly-read source (FR-005). **No new `references/` file is created** (FR-016);
the grounding is documented inline in the body.

## C5 — Read-only, POST-draft

The skill MUST remain read-only and POST-draft (FR-008): it writes nothing to the project;
"Archivos a escribir: Ninguno" stays true.

## C6 — Widened bilingual `description` (≤ 1024), mirrored verbatim

- The frontmatter `description` MUST trigger on head-hopping prompts in **both ES and EN**:
  e.g. "revisa head-hopping / saltos de punto de vista / focalización rota" and "check for
  head-hopping / POV breaks" (FR-006), **without** exceeding **1024** characters (current
  length 822 — ~200 slack; if additions would exceed, compress existing axes' trigger
  phrasing **without losing any axis's trigger**).
- The existing triggers (bible coherence, undeclared/unbacked characters, and the
  POST-draft↔PRE-draft `bookwright-analyze` disambiguation) MUST all remain live (FR-006).
- The widened string MUST be mirrored **verbatim** into
  `SKILL_DESCRIPTIONS["bookwright-continuity"]` (FR-015); the equality gate
  `tests/integrations/test_descriptions.py` enforces it.

## C7 — Lint gate

The materialized skill MUST pass `lint_skill_md`: `name` ≤ 64 chars and equal to its parent
directory, `description` ≤ 1024 chars, valid YAML frontmatter (FR-007).

## Oracles

- `tests/resources/test_command_body.py` — C1–C5 (fifth-axis sections, grounding, output
  shape, "Archivos a leer" entry, read-only).
- `tests/resources/test_command_activation.py` — C6 bilingual head-hopping trigger keywords
  (plus the existing triggers still firing).
- `tests/integrations/test_descriptions.py` — C6 verbatim mirror.
- `tests/integrations/test_materialize.py` / `test_skill_capabilities.py` — C7 + materialization.
