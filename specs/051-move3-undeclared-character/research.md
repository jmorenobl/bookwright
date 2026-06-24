# Phase 0 Research — Move 3 first slice (undeclared characters)

All unknowns resolved against the fixed design contract (`bookwright-design.md`
§ 20.6.2, § 13.5), the spec, and a read of the live codebase. No open
`NEEDS CLARIFICATION`.

## D1 — Surface: extend `bookwright-continuity`, don't add a new skill

- **Decision**: add a **fourth axis** to the existing `bookwright-continuity` skill.
- **Rationale**: § 20.6.2 decision 1 — the move-3 judgment ("does this prose name a
  person not in the roster?") is *manuscript vs. declared canon*, exactly continuity's
  POST-draft, read-only, graph-anchored mandate. Continuity already loads the roster
  (`bible/characters/`), the voice (`constitution.md`), and the graph
  (`graph build --json`). A separate skill would duplicate that grounding for a subset
  of the same concern and fragment "semantic continuity".
- **Alternatives considered**: a dedicated `bookwright-judge` skill wired 1-to-1 to the
  `not_evaluated` channel — more explicit but re-implements continuity's grounding;
  deferred (§ 20.6.2: re-evaluate only if semantic judgment grows beyond continuity).

## D2 — The person roster reads from the sheets, not from a graph label

- **Decision**: the skill reads person names from `bible/characters/*.md` `name:` field
  (and the URI slug), augmented with names from `bible/settings|locations|objects` so the
  agent knows which proper nouns are *already declared but are not persons*.
- **Rationale**: verified in the codebase — `G1_Character` carries **no** `rdfs:label`
  (the indexer derives identity from the slug; the human name lives only in the sheet's
  `name:` and the URI slug, per `references/golem-character.md` § "El slug"). So a SPARQL
  `?c rdfs:label ?name` would return nothing. `bookwright-verify` is the reference for a
  skill that *does* consume the graph (`graph build --json` + `graph query`), but the
  **person roster** must come from the sheets, not SPARQL.
- **Grounding doc**: extend the existing `references/golem-character.md` (reuse, don't add
  a new reference file — FR-005, Assumptions). It already explains `name:`/slug; add the
  "read the roster from the sheets, not from a graph label" note the procedure points to.

## D3 — Discoverability: a NEW status rule keyed on the abstaining source

- **Decision**: add a separate rule `judge_undeclared_characters` to `status/rules.py`,
  distinct from `activate_dormant_validators`. Its predicate fires when any `not_evaluated`
  entry has `validator == "character_unknown_mentions"` (a module-level source-set,
  today a single member). It emits exactly **one** `bookwright-continuity` action.
- **Rationale**: iteration 044 narrowed `activate_dormant_validators` to `missing_input`
  and **removed** the `character_unknown_mentions` remedy clause, because at the time
  nothing was actionable. Now running the skill **is** the action, so the nudge returns —
  but as a *separate* rule so the 044 `missing_input`-only filter that protects green stays
  byte-identical. Keying on the abstaining **source** (not the `pending_capability` *kind*)
  is the spec clarification (Session 2026-06-24): `focalization`'s head-hopping abstention
  is also `pending_capability` but this slice's skill does not judge it, so broad kind-keying
  would signpost a judgment the skill doesn't perform (a Scope/honesty violation). Future
  dimensions join the source-set as their skill judgment lands.
- **Table position**: after `activate_dormant_validators`, before `define_focus` — adjacent
  to the other dormant-related nudge, ahead of the focus catch-all. The `bootstrap_graph`
  short-circuit (research D5) still suppresses it on a degraded graph.
- **Alternatives considered**: (a) re-add the clause inside `activate_dormant_validators` —
  rejected: it would entangle the `pending_capability` nudge with the `missing_input` green
  filter, risking the 044 regression. (b) Key on the `pending_capability` kind broadly —
  rejected per the clarification (would fire for head-hopping the skill can't yet judge).

## D4 — The green predicate is byte-for-byte unchanged

- **Decision**: do not touch `validation/report.py`. The new action is purely additive in
  `status/rules.py`.
- **Rationale**: green lives in `ValidationReport` (`status == "ok"` AND no `not_evaluated`
  entry has `kind == missing_input`, iteration 044, SC-002/FR-010). A `pending_capability`
  entry already does not deny green. The nudge is a `next_action`, never a gate input — the
  44 green contract is reopened by nothing here.

## D5 — Widening the description carries a verbatim-mirror obligation

- **Decision**: widen the `description` in `bookwright-continuity.md` frontmatter to also
  trigger on "revisa si hay personajes sin declarar / mencionados pero sin ficha" and
  "check for undeclared / unbacked characters" (ES+EN), AND make the same verbatim edit to
  `SKILL_DESCRIPTIONS["bookwright-continuity"]` in `integrations/descriptions.py`.
- **Rationale**: `test_descriptions.py::test_v0_equality_gate_mirrors_source_frontmatter`
  (FR-016) asserts the table mirrors each source frontmatter `description` byte-for-byte.
  Editing one without the other fails CI. The current description is 551 chars; the widened
  one must stay < 1024 (Principle VII, `lint_skill_md` Rule 3). It must keep `post-draft`
  for the analyze↔continuity sibling disambiguation
  (`test_command_activation.py::test_sibling_disambiguation_keywords`) and stay bilingual.

## D6 — Judgment, not gate (no LLM in CI)

- **Decision**: the move-3 verdict is informative; the deterministic gate
  (`bookwright validate`, error-only) is unchanged and no `error` is born from an LLM. The
  skill's quality is NOT unit-asserted.
- **Rationale**: § 20.6.2 decision 4 + Principle VIII. The testable surface is
  materialization + lint + bilingual trigger + the status next_action without breaking green
  — exactly how `bookwright-verify`/`bookwright-continuity` are tested today. Offline, the
  permanent fallback is the `not_evaluated` the validator already emits; the skill *improves*
  the signal when it runs, its absence breaks nothing (Edge Cases).

## D7 — The deterministic validator does not change

- **Decision**: `validation/validators/character_unknown_mentions.py` stays a pure
  abstainer (`raise NotEvaluated(..., kind=pending_capability)`, unconditional). No
  detection logic added.
- **Rationale**: FR-011 — adding detection back would reopen the whack-a-mole issue #1
  closed. The only surface change is the discoverability `next_action`, which lives in
  `status`, not the validator. The validator's unconditional abstention is what makes the
  abstention (and thus the nudge) present on *every* validated project — so the oracles
  assert presence + green-preservation, never a presence/absence split (SC-004).
