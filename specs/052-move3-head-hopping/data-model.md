# Phase 1 Data Model — Move 3 second slice: head-hopping judgment

This slice introduces **no new persistent types** and **no ontology change** (Principle X).
It rides existing structures: the packaged skill body, the `SKILL_DESCRIPTIONS` mirror, the
`NotEvaluatedResult` / `NotEvaluatedKind` abstention channel, and the pure
`StatusState → list[Action]` rule table. The "entities" below are the conceptual objects the
slice reasons over and the contract between the deterministic layer and the skill layer.

## 1. Declared narrative voice (scoping input)

- **Source**: `bible/constitution.md`, the "Voz narrativa: …" line (the same one
  `validation/validators/focalization.py` parses via `_parse_declaration`).
- **Shape (as the skill reads it)**: a grammatical person (first / third) and, for third, a
  *limited* / *omniscient* qualifier.
- **Role**: scopes the fifth axis. The head-hopping judgment applies **only** under
  third-person *limited* / focalized. Under omniscient or first person, head-hopping is
  undefined and the axis reports nothing.
- **Not modified**: read as prose by the skill; not ingested; no new field.

## 2. Focal POV calendar (grounding input — newly read)

- **Source**: `bible/pov-structure.md`, the **"Calendario de POV"** section (a Markdown
  table mapping chapter → focal POV character). Authored prose; **no indexed frontmatter**.
- **Shape**: rows of `(chapter, focal POV character, info this POV does not yet know)`.
- **States**:
  - *populated* — a focal POV per chapter; the agent anchors the judgment on it.
  - *absent / `[PENDING: …]` placeholder* — no focal POV declared. The template ships this
    section as `[PENDING]`, so this is the common early-stage state. Treated like a
    `[PENDING]` voice (iteration 037): **no anchor → report the grounding gap, do not guess**
    (FR-002 (e)).
- **Role**: tells the agent who *may* hold interiority in each chapter.
- **New behavior**: the skill begins reading this file (added to "Archivos a leer", FR-005).
  No graph ingestion in this slice (read as prose, like the constitution).

## 3. Authored character roster (grounding input)

- **Source**: `bible/characters/*.md`, the `name:` field (and the URI slug). `G1_Character`
  carries no `rdfs:label`; the name lives in `name:` (documented in
  `references/golem-character.md`, already cited by the fourth axis).
- **Role**: resolves whose interiority a passage attributes — to map "Irene sintió …" onto a
  declared character and check it against the chapter's focal POV.
- **Not modified**: already read by the fourth axis; reused.

## 4. Abstention — the inter-layer contract (existing, unchanged)

- **Type**: `NotEvaluatedResult` (validator name + reason + `NotEvaluatedKind`), surfaced in
  `ValidationSummary.not_evaluated`.
- **This slice's instance**: `validator="focalization"`,
  `kind=NotEvaluatedKind.pending_capability`, reason "head-hopping / interiority attribution
  requires semantic judgment (move 3); the deterministic heuristic was measured nearly
  dormant on real prose". Emitted by `focalization` under limited-third (iteration 050;
  `validation/validators/focalization.py:113-116`).
- **Role**: the data-level contract. The validator **names** the head-hopping gap; the skill
  **closes** it with voice + POV calendar + roster as grounding. **Unchanged by this slice**
  (FR-013).
- **Contrast (the negative case)**: `focalization` also emits
  `kind=NotEvaluatedKind.missing_input` abstentions (no constitution / no voice / `[PENDING]`
  voice / no grammatical person). Those are input gaps covered by `activate_dormant_validators`
  and **must not** fire the head-hopping nudge.

## 5. Continuity deviation — head-hopping (skill output, not a CLI type)

- **Producer**: the agent running the extended `bookwright-continuity` skill (runtime, LLM).
- **Shape**: one more deviation in the continuity report — a manuscript **quote**, the phrase
  naming the **non-focal character's interiority under the focal POV in the chapter** (e.g.
  "interiority of *Irene* under the POV of *Teo* in *<chapter>*"), and a **suggestion**.
- **Not a CLI/graph type**: it is prose in the skill's report. Never an `error`; no `error` is
  born from an LLM (FR-014). Its quality is **not** unit-asserted.

## 6. Status `next_action` — head-hopping nudge (existing `Action` type, new instance)

- **Type**: `status.rules.Action` (`skill`, `prompt`, `reason`) — unchanged dataclass.
- **New instance**: `skill="bookwright-continuity"`; a fixed-template head-hopping `prompt`
  (read the declared voice + the POV calendar + the roster; judge interiority attributed to a
  non-focal POV per chapter; report each head-hop as a deviation); a head-hopping `reason`
  (focalization abstained on head-hopping — the semantic judgment is available via the skill).
  **Distinct** from the 051 undeclared-character action (FR-011).
- **Trigger predicate**: `validator == "focalization" AND kind is pending_capability` in
  `ValidationSummary.not_evaluated` (the shared `_judges(...)` helper, D4).
- **Table position**: immediately after `judge_undeclared_characters`, before `define_focus`.
- **Invariant**: informative — never degrades green (FR-012). When both move-3 abstentions are
  present, `status` emits **both** judge actions, each coherent and distinct.

## State-transition / behavior matrix (status layer)

| `not_evaluated` content | `activate_dormant_validators` | `judge_undeclared_characters` | `judge_head_hopping` |
|---|---|---|---|
| `(character_unknown_mentions, pending_capability)` | ✗ | ✓ | ✗ |
| `(focalization, pending_capability)` | ✗ | ✗ | ✓ |
| `(focalization, missing_input)` | ✓ | ✗ | ✗ (negative case) |
| both `pending_capability` entries above | ✗ | ✓ | ✓ (both, distinct) |
| `(focalization, missing_input)` + `(character_unknown_mentions, pending_capability)` | ✓ (focalization) | ✓ | ✗ |
| empty | ✗ | ✗ | ✗ |

Green is unchanged in every row: only `missing_input` entries deny green
(`validation/report.py`), and no row adds or removes a `missing_input` entry.

## Mechanism delta (the only structural change vs. 051)

- **Removed**: `_JUDGE_SOURCES: frozenset[str]` (matched validator name only).
- **Added**: a shared predicate factory `_judges(validator)` requiring
  `validator == <name> AND kind is NotEvaluatedKind.pending_capability`.
- **Adopted by**: `judge_undeclared_characters` (`_judges("character_unknown_mentions")` —
  byte-identical behavior, since that validator is always `pending_capability`) and
  `judge_head_hopping` (`_judges("focalization")` — the new dimension).

No other type, field, or table shape changes.
