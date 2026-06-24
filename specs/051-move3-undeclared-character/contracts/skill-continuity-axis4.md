# Contract — `bookwright-continuity` 4th axis (undeclared characters)

The skill is **LLM-judged prose**; this contract pins the **deterministically
testable** surface (materialization, lint, body sections, bilingual trigger). The
quality of the judgment is NOT asserted (the verify/continuity precedent, Principle VIII,
§ 20.6.2 decision 4).

## Frontmatter `description` (widened)

- MUST keep the three existing concerns (bible compliance, character-arc, timeline) AND
  add the undeclared-character trigger.
- MUST trigger in **both** ES and EN, e.g. "revisa si hay personajes sin declarar /
  mencionados pero sin ficha" and "check for undeclared / unbacked characters".
- MUST stay `< 1024` chars (`lint_skill_md` Rule 3, Principle VII).
- MUST keep the `post-draft` keyword (analyze↔continuity sibling disambiguation,
  `test_command_activation.py::test_sibling_disambiguation_keywords`).
- MUST be mirrored **verbatim** into `SKILL_DESCRIPTIONS["bookwright-continuity"]`
  (`integrations/descriptions.py`) — the FR-016 equality gate
  (`test_descriptions.py::test_v0_equality_gate_mirrors_source_frontmatter`).

**Verification**: `test_descriptions.py` (cap + verbatim mirror),
`test_command_activation.py` (bilingual + sibling keyword).

## `## Procedimiento` — the 4th axis

The procedure MUST gain a fourth axis ("open-set mentions / undeclared characters")
alongside the existing three, instructing the agent to:

1. Read the **authored person roster** from `bible/characters/*.md` (`name:` field) —
   stating that the name comes from the **sheet**, not from a graph label
   (`G1_Character` has no `rdfs:label`; see `references/golem-character.md`).
2. Read the names from `bible/settings|locations|objects` to know which proper nouns are
   already declared (and are not persons).
3. Scan the manuscript for proper nouns and **judge** which name a *person used in the
   prose but with no sheet in the bible*, distinguishing them from organizations, place
   names, vocatives and title words (which need no sheet).
4. Cite the **roster as the grounding** that separates signal (a real character with no
   sheet) from noise (org / place name) — § 20.6.2 decision 3.

**Verification**: `test_command_body.py` (the eight required ES headings still present;
body non-empty + Spanish; report-only statement; inline `graph build`). The new axis
content rides inside `## Procedimiento`/`## Output` — no new required heading is added,
so the existing section-keyword gate still passes.

## `## Output` — reporting the deviation

The output section MUST state that each undeclared-person mention is reported as **one
more deviation**: a manuscript quote, the phrase "no entry in `bible/characters/`"
(ES/EN equivalent), and a suggestion (create the sheet, or confirm it is not a
character). No `error` is produced — this is a judgment report, not a gate.

## Invariants

- **Read-only / POST-draft**: the skill writes nothing to the project (FR-008); the
  "no escribe nada" / "solo lectura" statement stays
  (`test_command_body.py::test_report_only_states_no_writes`).
- **Inline graph build**: `bookwright graph build --json` stays present
  (`test_command_body.py::test_graph_build_is_inline`).
- **Lint**: `name` ≤ 64 and equals the directory; valid YAML; `description` < 1024
  (`test_materialize.py`, `test_skill_capabilities.py`).
- **No new dependency, no LLM in the CLI** (Constitution II).
