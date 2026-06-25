# Contract: `bookwright-continuity` sixth axis + folded description

The skill is **LLM-judged prose**: this contract specifies the **structure and
required content** the materialized skill must carry (FR-001..FR-006, FR-016),
**not** the LLM's output. What is testable is materialization, lint, the trigger,
the grounding documentation, and the deviation phrasing.

## C1 — Sixth axis in `## Procedimiento` (FR-001, FR-002, FR-003, FR-005)

`resources/commands/bookwright-continuity.md` gains a **sixth** numbered axis,
mirroring the fifth (head-hopping) axis's shape, that MUST:

1. **Name the dimension**: "1st-person break / voice slip" (ruptura de voz / de
   persona narrativa — la prosa se desliza a 1ª persona bajo una voz declarada en 3ª).
2. **Mark it semantic** (judged by the agent, anchored in the bible, not a
   heuristic) — same framing as the 5th axis.
3. **(a) Read the declared narrative voice** in `bible/constitution.md`
   ("Voz narrativa: …") and proceed **only** under a declared **third-person**
   voice — **limited OR non-limited** (state explicitly it differs from the 5th
   axis's limited-only scope). Under a declared **first-person** voice the axis
   does **not** apply (the prose IS first person — report nothing).
4. **(b) Walk the manuscript outside dialogue.**
5. **(c) Judge** whether the narration slides into first person, **including the
   pro-drop verbal morphology without an explicit pronoun** (`Caminé`, `Me senté`,
   `Escribí`) that the deterministic check (only `yo` / `nosotros`) cannot see.
6. **(d) Grounding gap**: when the declared voice is **absent / not declared /
   a `[PENDING]` placeholder**, **report the grounding gap and do NOT guess** the
   voice (mirror the 5th axis's `[PENDING]` handling).
7. **State the grounding explicitly**: the **declared voice**
   (`bible/constitution.md`) — and that this axis needs **neither the roster nor
   the POV calendar** (a 1st-person break is grammatical person, not character
   identity).
8. **Preserve, never suppress**: the axis **adds** the morphological recall **on
   top of** `focalization`'s explicit-pronoun `warning`s (`yo` / `nosotros`) — it
   never overrides the deterministic core (§ 20.6.1 principle 3).

The existing five axes (bible compliance, character-arc, timeline, undeclared
characters, head-hopping) MUST remain intact, and the `## Procedimiento` intro
line that enumerates the axes ("Revisa cinco ejes…") MUST be updated to **seis**.

## C2 — Sixth axis in `## Output` (FR-004)

The `## Output` section MUST report each first-person slip as **one more
deviation**: the **manuscript quote**, the phrase **"first-person voice under a
narration declared in third person"** (`voz de 1ª persona bajo una narración
declarada en 3ª`), and a **suggestion** (rewrite in third person, or confirm the
voice). The output enumeration of axes MUST include the 6th
(biblia, arcos, cronología, personajes sin declarar, head-hopping, **ruptura de
1ª persona**). It MUST restate "es un juicio, no una `error`" — no `error` is born.

## C3 — `## Archivos a leer` (FR-016)

The `bible/constitution.md` entry (already listed for the 5th axis as the
"Voz narrativa") is **reused** for the 6th axis — a short note that the declared
voice also grounds the 1st-person-break axis. **No new file** (no `references/`
file, no `bible/` file) is added. The roster / POV-calendar entries stay scoped
to the 4th/5th axes.

## C4 — Folded `description` trigger (FR-006, FR-007, FR-015)

The front-matter `description` MUST:

- **Trigger** on first-person prompts in **ES and EN** — e.g. "revisa rupturas de
  voz / persona narrativa", "check for voice / narrative-person breaks".
- Achieve this by **folding** the trigger into the existing 5th-axis
  voice/focalization phrase **without growing past 1024** — e.g. widen
  «head-hopping / saltos de punto de vista / focalización rota» to also name
  «rupturas de voz / persona narrativa» (and the EN twin "head-hopping / POV
  breaks" → "voice / narrative-person breaks"), or compress existing text
  **without losing any axis's trigger** (4th and 5th included).
- Stay **≤ 1024 chars** (measured; today 1000/1024).
- Be mirrored **VERBATIM** into `SKILL_DESCRIPTIONS["bookwright-continuity"]`
  (`integrations/descriptions.py:27`) in the **same** edit — the equality gate
  `tests/integrations/test_descriptions.py` MUST stay green.

## C5 — Read-only, POST-draft (FR-008)

The skill remains read-only and POST-draft; the `## Archivos a escribir` /
`## Qué NO hacer` sections are unchanged (writes nothing).

## Verification (empirical — `uv run pytest`)

- `tests/resources/test_command_body.py`: a **new** `test_continuity_carries_the_sixth_first_person_axis`
  mirroring `test_continuity_carries_the_fifth_head_hopping_axis` — asserts the
  6th axis is present in `## Procedimiento` / `## Output`, names the first-person /
  voice-slip judgment, cites the declared voice as grounding, and carries the
  exact deviation phrasing (C2). Quality of the LLM judgment is NOT asserted.
- `tests/resources/test_command_activation.py`: the folded 1st-person trigger
  fires in ES and EN; the 4th/5th triggers still fire (SC-002).
- `tests/integrations/test_descriptions.py`: the verbatim-mirror equality gate.
- `tests/integrations/test_skill_capabilities.py` + `test_materialize.py`: lint
  (`name` ≤ 64 = directory, `description` ≤ 1024, valid YAML) and materialization.
