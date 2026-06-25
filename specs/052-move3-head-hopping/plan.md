# Implementation Plan: Move 3 second slice — judge head-hopping / broken focalization in `bookwright-continuity`

**Branch**: `052-move3-head-hopping` | **Date**: 2026-06-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/052-move3-head-hopping/spec.md`

## Summary

This iteration lands the **second vertical slice of move 3** — the semantic-judgment
layer that is the north star of issue #1. It **mirrors iteration 051 exactly in shape**;
only the judged *dimension* changes — from "undeclared characters" to **head-hopping
(broken focalization)**. The contract is the same one fixed in `bookwright-design.md`
§ 20.6.2 (design pass of 2026-06-24, 3rd dogfood `el-año-de-las-casas-vacías`). The slice
is **two coordinated, deterministic edits** plus their reconciliation — no LLM enters the
CLI:

1. **Skill surface** — extend `bookwright-continuity` with a **fifth axis**
   ("head-hopping / broken focalization"). Its procedure (a) reads the **declared
   narrative voice** from `bible/constitution.md` and proceeds **only** under a
   third-person *limited* / focalized voice (under omniscient or first person,
   head-hopping does not apply — report nothing); (b) reads the **focal POV per chapter**
   from `bible/pov-structure.md` (the "Calendario de POV" section — a prose file the
   skill does not read today); (c) reads the character roster; (d) **judges**, per
   chapter, whether the prose attributes interiority (thinking / feeling / perceiving,
   interior monologue) to a character who is **not** the focal POV of that chapter; and
   (e) when the POV calendar is absent or a `[PENDING: …]` placeholder, **reports the
   grounding gap and does not guess**. It reports each head-hop as one more continuity
   deviation. The judgment is the agent's, at runtime; the CLI stays deterministic.

2. **Discoverability** — `bookwright status` gains **one** informative `next_action`
   pointing to `bookwright-continuity` (for the head-hopping judgment) whenever the
   validation report carries a `not_evaluated` entry whose **source validator** is
   `focalization` **and** whose **kind is `pending_capability`**. This restores, for the
   second move-3 dimension, the same closed-loop discoverability 051 built. The keying
   mechanism is **generalized**: the iteration-051 `_JUDGE_SOURCES` frozenset (matched on
   validator *name* alone) is deleted and replaced by a shared predicate helper requiring
   `validator == <name> AND kind is pending_capability` — because `focalization`, unlike
   `character_unknown_mentions`, emits **both** `missing_input` and `pending_capability`
   abstentions, and the head-hopping nudge MUST fire only on the latter.

The deterministic validator `focalization` is **untouched** (it already declares the
head-hopping abstention — `Abstention(_HEAD_HOPPING_PENDING, kind=pending_capability)`,
iteration 050, under limited-third). The `not_evaluated` channel is the data-level
contract between the two layers: the validator names the gap, the skill closes it with
voice + POV calendar + roster as grounding (§ 20.6.2 decision 3).

## Technical Context

**Language/Version**: Python 3.11+ (CLI surface unchanged; no LLM dependency added —
Constitution II).

**Primary Dependencies**: none new. The skill body is packaged Markdown read via
`importlib.resources`; the status rule consumes the existing
`ValidationSummary.not_evaluated` channel and `NotEvaluatedResult` (validator name +
reason + `NotEvaluatedKind`).

**Storage**: plain text only — the skill is `SKILL.md`-materialized Markdown; the voice
is read from `bible/constitution.md`, the focal POV per chapter from
`bible/pov-structure.md` (its "Calendario de POV" section, as prose — no graph ingestion),
and the roster from `bible/characters/*.md` at agent runtime, never from a binary store
(Constitution I).

**Testing**: `uv run pytest`. The LLM judgment quality is **not** unit-asserted (as with
`bookwright-verify`/`bookwright-continuity` today); what is testable is materialization +
lint + bilingual trigger + the new `status` next_action without breaking green, **plus the
negative case** (a focalization-`missing_input`-only project gains no head-hopping nudge).
Plus the description/body/activation gates and the `tiny-historical` status oracle (4 → 5).

**Target Platform**: cross-platform CLI + Agent Skill.

**Project Type**: single project (`src/bookwright/`, `tests/` at root).

**Performance Goals**: N/A (no hot path touched).

**Constraints**: every changed file ≤ 500 lines (Principle IV); frozen ontology untouched
(Principle X); `description` ≤ 1024 chars (Principle VII; current 822, ~200 slack);
green predicate byte-for-byte unchanged (FR-012); error-only CI gate unchanged, no `error`
from an LLM (FR-014, § 20.6.2 decision 4).

**Scale/Scope**: ~2 source-behavior edits (one resource skill body, one status rule),
1 mirror edit surfaced by the existing gate (`descriptions.py`), the design + index
reconciliation (no DEBT removed), and the named test/oracle updates.

## Constitution Check

*GATE: evaluated against constitution v1.5.0. Re-checked after design below.*

| Principle | Status | Note |
|---|---|---|
| I — Plain text as source of truth | ✅ PASS | Skill body is Markdown; voice/POV-calendar/roster read from `bible/*.md`; no binary store. |
| II — Modern Python stack | ✅ PASS | **No new runtime dependency.** No LLM in the CLI — the judgment runs in the agent at skill runtime (§ 20.6.2 decision 4). |
| III — src-layout | ✅ PASS | All edits under `src/bookwright/` and `tests/`. |
| IV — Modular command surface (≤500 lines) | ✅ PASS | `status/rules.py` (251 lines) gains a peer rule + builder + helper (~25 lines, stays < 500); the skill body and `descriptions.py` stay well under 500. |
| V — Plugin integrations | ✅ PASS | No integration touched; the skill materializes through the existing `SkillsIntegration` path. |
| VI — Agent Skills only | ✅ PASS | The slice **extends** an existing skill; emits no `commands/` directory. |
| VII — agentskills.io compliance | ✅ PASS | Widened `description` stays < 1024; `name` matches dir; valid YAML — asserted by `lint_skill_md` + `test_descriptions.py`. |
| VIII — Test discipline (≥80%) | ✅ PASS | LLM output **not** unit-asserted; the skill is verified by materialization/lint/trigger (the verify/continuity precedent, Principle VIII split); status behavior verified empirically incl. the negative case. |
| IX — JSON-over-stdout | ✅ PASS | `status --json` envelope shape unchanged; the new action is one more entry in the existing `next_actions[]`. |
| X — Design-document axioms | ✅ PASS | Frozen ontology untouched; move 3 is the **skill layer**, not a new validator in `validation/` (no `triples=()` applies); `focalization` is unchanged. |

**Scope & Release Discipline**: this is not speculative plumbing — it is the activated
move 3 (§ 13.5 decision 2: trigger met), landing its second proven slice on the **same
pattern** as 051. The third move-3 dimension (1st-person break / pro-drop recall ceiling,
DEBT-021) is explicitly out of scope (it additionally needs a *new* `focalization`
abstention this slice does not add). No deferred/cancelled capability is pulled in.

**Result**: PASS — no violations, Complexity Tracking table not required.

## Project Structure

### Documentation (this feature)

```text
specs/052-move3-head-hopping/
├── spec.md              # Feature spec (already authored + hardened)
├── plan.md              # This file
├── research.md          # Phase 0 — decisions consolidated below
├── data-model.md        # Phase 1 — the entities and the layer contract
├── quickstart.md        # Phase 1 — runnable validation guide
├── contracts/
│   ├── skill-continuity-axis5.md     # the 5th-axis skill-body contract
│   └── status-headhopping-nudge.md   # the status next_action + generalized-keying contract
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── resources/commands/
│   └── bookwright-continuity.md           # EDIT: widen description (head-hopping ES/EN
│                                           #       trigger); add 5th axis to ## Procedimiento
│                                           #       + ## Output; add bible/pov-structure.md to
│                                           #       "Archivos a leer"; cite voice+POV+roster
├── integrations/
│   └── descriptions.py                    # EDIT: mirror the widened continuity description
│                                           #       VERBATIM (FR-015 equality gate)
├── status/
│   └── rules.py                           # EDIT: delete _JUDGE_SOURCES; add shared predicate
│                                           #       helper (validator + kind=pending_capability);
│                                           #       add the `judge_head_hopping` peer rule + builder
└── validation/validators/
    └── focalization.py                    # UNCHANGED — already declares the abstention (FR-013)
```

```text
tests/
├── resources/test_command_body.py          # 5th-axis body assertions for continuity
├── resources/test_command_activation.py    # widened bilingual head-hopping trigger keywords
├── integrations/test_descriptions.py        # FR-015 mirror gate (passes once descriptions.py mirrors)
├── integrations/test_skill_capabilities.py  # materialization/lint stays green for the longer body
├── integrations/test_materialize.py         # continuity materializes + lints
├── status/test_rules.py                     # the new rule + RETARGET the head-hopping negative test
├── commands/test_status.py                  # the new head-hopping next_action surfaces in the envelope
├── fixtures/tiny-historical/expected-status.md  # oracle next_actions 4 → 5 (gains head-hopping nudge)
└── e2e/test_orchestration_workflow.py       # reads the oracle; passes once the oracle is updated

bookwright-design.md                         # § 20.6.2 (2nd slice landed) + § 13.5 (reframe)
DEBT.md                                       # UNCHANGED — no entry removed; DEBT-021 stays open
CLAUDE.md                                     # milestone prose + iteration index row 052 (+ SPECKIT block)
```

**Structure Decision**: single project, no new module. The slice rides entirely on
existing seams — the packaged skill body, the `SKILL_DESCRIPTIONS` mirror, and the pure
`state → list[Action]` status rule table. The only structural shift from 051 is the
*generalization* of the keying mechanism (frozenset → shared predicate helper), forced
because `focalization` carries two abstention kinds.

## Phase 0: Research — decisions

See [research.md](./research.md). All resolved; no open `NEEDS CLARIFICATION` (the spec's
Clarifications session of 2026-06-25 closed the five design questions).

Headline decisions (consolidated from spec + design § 20.6.2 + the codebase):

- **D1 — Surface = extend `bookwright-continuity`, not a new skill** (§ 20.6.2 decision 1;
  identical to 051 D1). The judgment is *manuscript vs. declared canon* — continuity's
  mandate, which already loads roster + voice + graph. A fifth axis joins the existing four.
- **D2 — Grounding = voice + POV calendar + roster** (§ 20.6.2 decision 3). The voice
  (`bible/constitution.md`, parsed today by `focalization`) scopes the axis to limited-third;
  the focal POV per chapter (`bible/pov-structure.md`, "Calendario de POV") names who *may*
  hold interiority; the roster (`bible/characters/*.md`) resolves whose interiority a
  passage attributes. `bible/pov-structure.md` is a prose file the skill begins to read —
  added to "Archivos a leer". **No new `references/` file** (Clarification: none exists for
  focalization; `pov-structure.md` is itself the authored source — scope discipline, FR-016).
- **D3 — The validator is already done.** `focalization` declares
  `Abstention(_HEAD_HOPPING_PENDING, kind=pending_capability)` under limited-third
  (`validation/validators/focalization.py:113-116`, iteration 050). **Zero changes under
  `validation/`** (FR-013). This is the only structural difference from 051's source: there
  the abstainer was newly anchored; here it predates the slice.
- **D4 — Discoverability needs a GENERALIZED keying mechanism.** 051 keyed by validator
  *name* alone (`_JUDGE_SOURCES` frozenset), which is sound only because
  `character_unknown_mentions` is *always* `pending_capability`. `focalization` emits
  **both** kinds: `missing_input` (no constitution / no voice / `[PENDING]` / no grammatical
  person — already covered by `activate_dormant_validators`) **and** `pending_capability`
  (head-hopping under limited-third). The head-hopping nudge MUST fire on the latter only
  (Clarification Q1, FR-009/FR-010). Decision: **delete** the `_JUDGE_SOURCES` frozenset
  and introduce a shared predicate helper `_judges(validator)` →
  `lambda s: any(r.validator == validator and r.kind is NotEvaluatedKind.pending_capability
  for r in s.validation.not_evaluated)`, adopted by **both** `judge_undeclared_characters`
  and `judge_head_hopping`. This is **byte-identical in behavior** for
  `character_unknown_mentions` (which always abstains `pending_capability`), so the 051
  nudge is unaffected (doctrine §3: delete the ill-fitting frozenset rather than guard it).
- **D5 — Two distinct peer rules, not one merged / not a list-returning `Rule.build`**
  (Clarification Q2/Q3, FR-010/FR-011). The head-hopping dimension is a **second peer
  `Rule`** (`judge_head_hopping`) with its **own** builder, prompt and reason. `Rule.build`
  stays one-Rule-one-Action; the two move-3 judge nudges may both fire in the same run and
  each emits its own coherent action. Placed **immediately after `judge_undeclared_characters`
  and before `define_focus`** (Clarification Q4, FR-009) so emitted order stays deterministic.
- **D6 — Green is byte-identical.** The green predicate lives in `validation/report.py`
  (`missing_input`-only filter). The new action lives in `status/rules.py` and never touches
  that predicate; a `pending_capability` entry does not degrade green (FR-012).
  `activate_dormant_validators` stays `missing_input`-only.
- **D7 — Widening the description has a mirror obligation.** `SKILL_DESCRIPTIONS` in
  `integrations/descriptions.py:27` must mirror the source frontmatter verbatim
  (`test_descriptions.py`, FR-015). Both edits made together. Current 822 chars → widened,
  must stay < 1024 (Clarification: ~200 slack; the head-hopping trigger must be brief, or
  the existing axes' trigger phrasing is compressed without losing any axis's trigger).
- **D8 — Judgment, not gate.** § 20.6.2 decision 4: the move-3 verdict is informative; the
  CI gate stays `bookwright validate` (deterministic, error-only); no `error` is born from
  an LLM. The skill's quality is therefore NOT unit-asserted.
- **D9 — Reuse `tiny-historical`; the negative case is pure-unit.** `tiny-historical`
  already declares third-person *limited* and already carries the `(focalization,
  pending_capability)` abstention in its oracle — its `next_actions` flips **4 → 5** while
  green stays. **No new fixture** (scope discipline). The negative case (a
  focalization-`missing_input`-only project gains no head-hopping nudge) is covered at the
  pure `test_rules.py` synthetic-state level (FR-017, Clarification Q5). `tiny-historical`
  ships no `bible/pov-structure.md`, which is fine: the status nudge keys on the
  *validator abstention* (present), and the skill's runtime grounding-gap handling
  (FR-002 (e)) is exactly the absent-calendar path — exercised by the agent, not unit-asserted.

## Phase 1: Design & Contracts

See [data-model.md](./data-model.md), [contracts/](./contracts/), and
[quickstart.md](./quickstart.md).

**Entities** (data-model.md): the *declared narrative voice* (scopes the axis), the *focal
POV calendar* (`bible/pov-structure.md`, newly read), the *authored character roster*, the
*`not_evaluated` Abstention* (`validator=focalization`, `kind=pending_capability`) as the
inter-layer contract, the *continuity deviation (head-hopping)* the skill reports, and the
*status `next_action`* (informative, distinct from the 051 action, never degrades green).

**Contracts**:

- `contracts/skill-continuity-axis5.md` — the body contract: the 5th axis present in
  `## Procedimiento` and `## Output`; voice + POV calendar + roster cited as grounding;
  the limited-third scoping (omniscient/first-person → nothing); the grounding-gap clause
  (absent / `[PENDING]` calendar → report the gap, do not guess); the report shape (quote +
  "interiority of *X* under the POV of *Y* in *<chapter>*" + suggestion); read-only/POST-draft;
  `bible/pov-structure.md` added to "Archivos a leer"; the widened bilingual `description`
  < 1024 mirrored verbatim in `descriptions.py`.
- `contracts/status-headhopping-nudge.md` — the rule contract: the deletion of
  `_JUDGE_SOURCES`; the shared predicate helper (`validator == <name> AND kind is
  pending_capability`); the NEW `judge_head_hopping` peer rule, its single `Action` (skill
  `bookwright-continuity`, fixed English head-hopping prompt + reason, distinct from the 051
  action), its table position (after `judge_undeclared_characters`, before `define_focus`);
  the invariant that `judge_undeclared_characters` stays byte-identical in behavior; the
  green-predicate and `activate_dormant_validators`-`missing_input`-only invariants.

**The status rule, concretely** (`status/rules.py`):

1. **Delete** the `_JUDGE_SOURCES` frozenset and its comment block.
2. **Add** a shared predicate factory:
   `_judges(validator)` returns a predicate `lambda s: any(r.validator == validator and
   r.kind is NotEvaluatedKind.pending_capability for r in s.validation.not_evaluated)`.
3. **Retarget** `judge_undeclared_characters`'s `applies` to
   `_judges("character_unknown_mentions")` (byte-identical behavior; the builder
   `_judge_undeclared_characters` and its prompt/reason are unchanged).
4. **Add** a builder `_judge_head_hopping(state)` returning one `Action` whose `skill` is
   `bookwright-continuity`, with a fixed-template head-hopping `prompt` (read the declared
   voice + the POV calendar + the roster; judge interiority attributed to a non-focal POV
   per chapter; report each as a deviation) and a head-hopping `reason` (focalization
   abstained on head-hopping — semantic judgment available via the skill), **distinct** from
   the 051 undeclared-character action.
5. **Register** `Rule(name="judge_head_hopping", applies=_judges("focalization"),
   build=_judge_head_hopping)` in `RULES` immediately **after** `judge_undeclared_characters`
   and **before** `define_focus`.

The `bootstrap_graph` short-circuit (research D5) still suppresses it on a degraded graph,
as it must.

**Test/oracle deltas** (verified by `uv run pytest`):

- `tests/status/test_rules.py`: add `judge_head_hopping` to `_TRIGGER` (so
  `test_every_rule_is_exercised_by_a_synthetic_state` stays exhaustive) — its trigger state
  is `make_state(not_evaluated=(_DORMANT_FOCAL_CAP,))` (the existing
  `(focalization, pending_capability)` fixture constant). **Retarget**
  `test_focalization_capability_gap_does_not_fire_the_judge_nudge` — it currently asserts
  the `(focalization, pending_capability)` entry fires **nothing**; it must now assert it
  fires **exactly one** `bookwright-continuity` head-hopping action (the whole point of this
  slice). Add an exact-match test for the head-hopping action's prompt/reason. Add the
  **negative** test: `(focalization, missing_input)` (`_DORMANT_FOCAL`) fires
  `activate_dormant_validators` **and not** the head-hopping judge nudge. Update
  `test_both_kinds_at_once_*` / the priority-order tests if their action counts shift.
- `tests/commands/test_status.py`: assert the new head-hopping `next_action` appears in the
  `--json` envelope on a project carrying the `(focalization, pending_capability)` abstention,
  distinct from the 051 undeclared-character action.
- `tests/fixtures/tiny-historical/expected-status.md`: the oracle's `next_actions` grows
  **4 → 5** — a third `bookwright-continuity` (the head-hopping nudge), emitted after
  `judge_undeclared_characters` and before any focus action; `validation.counts`, the
  `not_evaluated` entries, and the GREEN status are byte-identical. Update the front-matter
  NOTE prose accordingly. The green controls `tiny-novel`/`tiny-memoir` stay GREEN.
- `tests/e2e/test_orchestration_workflow.py`: reads the oracle front-matter; passes once
  the oracle records the 5th action (no test-code change unless it hard-codes a count).
- `tests/resources/test_command_body.py` + `test_command_activation.py`: continuity's body
  gains the 5th-axis sections and the `bible/pov-structure.md` "Archivos a leer" entry; its
  description gains the widened bilingual head-hopping trigger keywords (still bilingual,
  still carrying the existing four axes' triggers + the `post-draft` analyze↔continuity
  disambiguation).
- `tests/integrations/test_descriptions.py`: passes once `descriptions.py` mirrors the
  widened frontmatter (FR-015).

**Agent context update**: the managed `<!-- SPECKIT START -->…END -->` block in `CLAUDE.md`
is re-pointed to this plan (Phase 1 step 4), done as part of this run.

## Re-evaluation (post-design)

Constitution Check re-run after the design above: **still PASS**. No new module, no new
dependency, no ontology change, no LLM in CI, green predicate untouched, `focalization`
untouched, every changed file ≤ 500 lines. The surfaces that "grow" are the skill body and
a single status rule (plus the keying generalization that *shrinks* the mechanism from a
frozenset to a shared predicate) — both within their seams.

## Complexity Tracking

No entries — Constitution Check passed with no violations.
