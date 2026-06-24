# Implementation Plan: Move 3 first slice — judge undeclared characters in `bookwright-continuity`

**Branch**: `051-move3-undeclared-character` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/051-move3-undeclared-character/spec.md`

## Summary

This iteration lands the **first vertical slice of move 3** — the semantic-judgment
layer that is the north star of issue #1. The contract is already fixed in
`bookwright-design.md` § 20.6.2 (design pass of 2026-06-24, 3rd dogfood
`el-año-de-las-casas-vacías`). The slice is **two coordinated, deterministic edits**
plus their reconciliation — no LLM enters the CLI:

1. **Skill surface** — extend `bookwright-continuity` with a **fourth axis**
   ("open-set mentions / undeclared characters"). Its procedure reads the **authored
   person roster** from the sheets (`bible/characters/*.md` `name:` field — `G1_Character`
   carries no `rdfs:label`, so the name lives in the `name:` and the URI slug),
   augmented with names from `bible/settings|locations|objects`, scans the manuscript
   for proper nouns, and **judges** which name a *person used in the prose but absent
   from the bible* — separating the real signal (a character with no sheet, e.g.
   `Amelia`) from the noise (organizations, place names, vocatives, title words). It
   reports each as one more continuity deviation. The judgment is the agent's, at
   runtime; the CLI stays deterministic.

2. **Discoverability** — `bookwright status` gains **one** informative `next_action`
   pointing to `bookwright-continuity` whenever the validation report carries a
   `not_evaluated` entry whose **source validator** is `character_unknown_mentions`.
   This restores the nudge iteration 044 removed (now that *running the skill* is an
   actionable remedy). It is keyed on the abstaining **source**, never on the
   `pending_capability` *kind* (so `focalization`'s head-hopping abstention — also
   `pending_capability` — does not fire it in this slice), and it is **informative**:
   the iteration-044 green predicate stays byte-for-byte identical.

The deterministic validator `character_unknown_mentions` is **untouched** (it stays a
pure abstainer, `kind=pending_capability`). The `not_evaluated` channel is the
data-level contract between the two layers: the validator names the gap, the skill
closes it with the roster as grounding (§ 20.6.2 decision 2).

## Technical Context

**Language/Version**: Python 3.11+ (CLI surface unchanged; no LLM dependency added —
Constitution II).

**Primary Dependencies**: none new. The skill body is packaged Markdown read via
`importlib.resources`; the status rule consumes the existing
`ValidationSummary.not_evaluated` channel and `NotEvaluatedResult` (validator name +
reason + `NotEvaluatedKind`).

**Storage**: plain text only — the skill is `SKILL.md`-materialized Markdown, the
roster is read from `bible/*.md` sheets at agent runtime, never from a binary store
(Constitution I).

**Testing**: `uv run pytest`. The LLM judgment quality is **not** unit-asserted (as
with `bookwright-verify`/`bookwright-continuity` today); what is testable is
materialization + lint + bilingual trigger + the new `status` next_action without
breaking green. Plus the three description/body/activation gates and the
`tiny-historical` status oracle.

**Target Platform**: cross-platform CLI + Agent Skill.

**Project Type**: single project (`src/bookwright/`, `tests/` at root).

**Performance Goals**: N/A (no hot path touched).

**Constraints**: every changed file ≤ 500 lines (Principle IV); frozen ontology
untouched (Principle X); `description` ≤ 1024 chars (Principle VII); green predicate
byte-for-byte unchanged (FR-010); error-only CI gate unchanged, no `error` from an LLM
(FR-012, § 20.6.2 decision 4).

**Scale/Scope**: ~2 source-behavior edits (one resource skill body, one status rule),
2 mirror/reference edits surfaced by the existing gates (`descriptions.py`,
`references/golem-character.md`), the design + DEBT + index reconciliation, and the
named test/oracle updates.

## Constitution Check

*GATE: evaluated against constitution v1.5.0. Re-checked after design below.*

| Principle | Status | Note |
|---|---|---|
| I — Plain text as source of truth | ✅ PASS | Skill body is Markdown; roster read from `bible/*.md`; no binary store. |
| II — Modern Python stack | ✅ PASS | **No new runtime dependency.** No LLM in the CLI — the judgment runs in the agent at skill runtime (§ 20.6.2 decision 4). |
| III — src-layout | ✅ PASS | All edits under `src/bookwright/` and `tests/`. |
| IV — Modular command surface (≤500 lines) | ✅ PASS | `status/rules.py` (219 lines) gains ~20; the skill body and `descriptions.py` stay well under 500. |
| V — Plugin integrations | ✅ PASS | No integration touched; the skill materializes through the existing `SkillsIntegration` path. |
| VI — Agent Skills only | ✅ PASS | The slice **extends** an existing skill; emits no `commands/` directory. |
| VII — agentskills.io compliance | ✅ PASS | Widened `description` stays < 1024; `name` matches dir; valid YAML — asserted by `lint_skill_md` + `test_descriptions.py`. |
| VIII — Test discipline (≥80%) | ✅ PASS | LLM output **not** unit-asserted; the skill is verified by materialization/lint/trigger (the verify/continuity precedent, Principle VIII split); status behavior verified empirically. |
| IX — JSON-over-stdout | ✅ PASS | `status --json` envelope shape unchanged; the new action is one more entry in the existing `next_actions[]`. |
| X — Design-document axioms | ✅ PASS | Frozen ontology untouched; move 3 is the **skill layer**, not a new validator in `validation/` (no `triples=()` applies). |

**Scope & Release Discipline**: this is not speculative plumbing — it is the activated
move 3 (§ 13.5 decision 2: trigger met), landing its minimal proven slice. The other
two move-3 dimensions (head-hopping / 1st-person break, DEBT-021) are explicitly out of
scope (same pattern, later iterations). No deferred/cancelled capability is pulled in.

**Result**: PASS — no violations, Complexity Tracking table not required.

## Project Structure

### Documentation (this feature)

```text
specs/051-move3-undeclared-character/
├── spec.md              # Feature spec (already authored + hardened)
├── plan.md              # This file
├── research.md          # Phase 0 — decisions consolidated below
├── data-model.md        # Phase 1 — the entities and the layer contract
├── quickstart.md        # Phase 1 — runnable validation guide
├── contracts/
│   ├── skill-continuity-axis4.md   # the 4th-axis skill-body contract
│   └── status-undeclared-nudge.md  # the status next_action contract
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── resources/commands/
│   ├── bookwright-continuity.md            # EDIT: widen description; add 4th axis to
│   │                                        #       ## Procedimiento + ## Output; cite roster
│   └── references/
│       └── golem-character.md              # EDIT: document "person roster from the sheets,
│                                            #       not from a graph label" (FR-005)
├── integrations/
│   └── descriptions.py                     # EDIT: mirror the widened continuity description
│                                            #       (FR-016 verbatim-equality gate)
├── status/
│   └── rules.py                            # EDIT: add the `judge_undeclared_characters`
│                                            #       rule (keyed on the abstaining source)
└── validation/validators/
    └── character_unknown_mentions.py       # UNCHANGED — stays a pure abstainer (FR-011)

tests/
├── resources/test_command_body.py          # 4th-axis body assertions for continuity
├── resources/test_command_activation.py    # widened bilingual trigger keywords
├── integrations/test_descriptions.py        # FR-016 mirror gate (passes once descriptions.py mirrors)
├── integrations/test_skill_capabilities.py  # materialization/lint stays green for the longer body
├── integrations/test_materialize.py         # continuity materializes + lints
├── status/test_rules.py                     # the new rule + retarget the capability-gap test
├── commands/test_status.py                  # the new next_action surfaces in the envelope
└── fixtures/tiny-historical/expected-status.md  # oracle gains the continuity judge next_action

bookwright-design.md                         # § 20.6.2 (slice landed) + § 13.5 (reframe)
DEBT.md                                       # remove DEBT-013 (this slice is its cure)
CLAUDE.md                                     # milestone prose + iteration index row 051
```

**Structure Decision**: single project, no new module. The slice rides entirely on
existing seams — the packaged skill body, the `SKILL_DESCRIPTIONS` mirror, the
`references/` offload, and the pure `state → list[Action]` status rule table.

## Phase 0: Research — decisions

See [research.md](./research.md). All resolved; no open `NEEDS CLARIFICATION`.

Headline decisions (consolidated from spec + design § 20.6.2 + the codebase):

- **D1 — Surface = extend `bookwright-continuity`, not a new skill.** § 20.6.2 decision 1:
  the judgment is *manuscript vs. declared canon*, exactly continuity's mandate, which
  already loads the roster + voice + graph. A new skill would duplicate that grounding.
- **D2 — Person roster reads from the sheets, not the graph.** Verified: `G1_Character`
  carries no `rdfs:label`; the authored name lives in the `name:` field and the URI slug
  (`references/golem-character.md` § "El slug"). The skill scans `bible/characters/*.md`
  `name:` for persons and `bible/settings|locations|objects` to know which proper nouns
  are *already declared but not persons*. The grounding doc extends the existing
  `references/golem-character.md` (no new reference file).
- **D3 — Discoverability is a NEW status rule keyed on the abstaining source.** Not a
  revival of the 044-narrowed `activate_dormant_validators` (which stays `missing_input`-only
  so the green filter is intact). A separate rule matches the set of sources continuity
  judges — today the single member `character_unknown_mentions` — and emits exactly one
  action. Keying on the source (not the `pending_capability` kind) keeps `focalization`'s
  head-hopping abstention from firing a nudge for a judgment the skill does not yet perform
  (Clarifications, FR-009).
- **D4 — Green is byte-identical.** The green predicate lives in `validation/report.py`
  (`missing_input`-only filter). The new action lives in `status/rules.py` and never
  touches that predicate; a `pending_capability` entry does not degrade green (FR-010).
- **D5 — Widening the description has a mirror obligation.** `SKILL_DESCRIPTIONS` in
  `integrations/descriptions.py` must mirror the source frontmatter verbatim
  (`test_descriptions.py::test_v0_equality_gate_mirrors_source_frontmatter`, FR-016).
  Both edits are made together. Current length 551 → widened, must stay < 1024.
- **D6 — Judgment, not gate.** § 20.6.2 decision 4: the move-3 verdict is informative;
  the CI gate stays `bookwright validate` (deterministic, error-only); no `error` is born
  from an LLM. The skill's quality is therefore NOT unit-asserted.

## Phase 1: Design & Contracts

See [data-model.md](./data-model.md), [contracts/](./contracts/), and
[quickstart.md](./quickstart.md).

**Entities** (data-model.md): the *authored person roster* (read from sheets), the
*`not_evaluated` Abstention* (`kind=pending_capability`) as the inter-layer contract, the
*continuity deviation (undeclared-character)* the skill reports, and the *status
`next_action`* (informative, never degrades green).

**Contracts**:

- `contracts/skill-continuity-axis4.md` — the body contract: the 4th axis present in
  `## Procedimiento` and `## Output`, the roster cited as grounding, the report shape
  (quote + "no entry in `bible/characters/`" + suggestion), read-only/POST-draft, and the
  widened bilingual `description` < 1024 mirrored in `descriptions.py`.
- `contracts/status-undeclared-nudge.md` — the rule contract: a NEW `judge_undeclared_characters`
  rule, its predicate (any `not_evaluated` entry with `validator == "character_unknown_mentions"`),
  its single `Action` (skill `bookwright-continuity`, fixed English prompt + reason), its
  table position (after `activate_dormant_validators`, before `define_focus`), and the
  green-predicate invariant.

**The status rule, concretely** (`status/rules.py`): add a builder
`_judge_undeclared_characters(state)` returning one `Action` whose `skill` is
`bookwright-continuity`, a fixed-template `prompt` naming the *undeclared-character*
judgment ("scan the manuscript for proper nouns, read the authored roster …, report
each person used in the prose with no sheet in `bible/characters/`"), and a `reason`
("`character_unknown_mentions` abstained — semantic judgment is available via the skill").
Register a `Rule(name="judge_undeclared_characters", applies=…, build=…)` in `RULES`
**after** `activate_dormant_validators` and **before** `define_focus`. The predicate
matches on the source-validator set (a module-level frozenset, today
`{"character_unknown_mentions"}`) so future dimensions join by adding their source — never
on the kind. The `bootstrap_graph` short-circuit (research D5) still suppresses it on a
degraded graph, as it must.

**Test/oracle deltas** (verified by `uv run pytest`):

- `tests/status/test_rules.py`: add the new rule to `_TRIGGER` (so
  `test_every_rule_is_exercised_by_a_synthetic_state` stays exhaustive); add an exact-match
  test for the judge action; **retarget** `test_capability_gap_only_run_suppresses_the_dormant_nudge`
  — a `pending_capability` `character_unknown_mentions` entry now **does** produce the
  continuity judge action (while still producing no `activate_dormant_validators` action),
  which is the whole point of restoring the nudge. The `activate_dormant_validators` tests
  that use `_DORMANT_FOCAL` (focalization) are unaffected (focalization is not in the
  judge source-set in this slice).
- `tests/commands/test_status.py`: assert the new continuity judge `next_action` appears in
  the `--json` envelope on a project carrying the abstention.
- `tests/fixtures/tiny-historical/expected-status.md`: the oracle gains the continuity
  judge `next_action` (its `next_actions.skills` grows by one `bookwright-continuity`,
  emitted after `review_continuity`); `validation.counts`, the `not_evaluated` entries, and
  the GREEN status are byte-identical. Update the front-matter NOTE prose accordingly. The
  green controls `tiny-novel`/`tiny-memoir` stay GREEN and carry the same nudge.
- `tests/resources/test_command_body.py` + `test_command_activation.py`: continuity's body
  gains the 4th-axis sections and its description gains the widened bilingual trigger
  keywords (still bilingual, still carrying `post-draft` for the analyze↔continuity sibling
  disambiguation).
- `tests/integrations/test_descriptions.py`: passes once `descriptions.py` mirrors the
  widened frontmatter (FR-016).

**Agent context update**: the managed `<!-- SPECKIT START -->…END -->` block in
`CLAUDE.md` is re-pointed to this plan (Phase 1 step 4), done as part of this run.

## Re-evaluation (post-design)

Constitution Check re-run after the design above: **still PASS**. No new module, no new
dependency, no ontology change, no LLM in CI, green predicate untouched, every changed
file ≤ 500 lines. The only surface that "grows" is the skill body and a single status
rule — both within their seams.

## Complexity Tracking

No entries — Constitution Check passed with no violations.
