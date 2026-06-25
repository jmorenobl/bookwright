# Phase 0 Research: Move 3 third dimension, judgment half (first-person break)

All Technical Context items resolved — there are **no** open NEEDS
CLARIFICATION. The five spec clarifications (Session 2026-06-25) already settled
the design questions; this file records the decisions and their grounding in the
current code.

## Decision 1 — Grounding: declared voice only, no roster, no POV calendar

**Decision**: The 6th axis reads **exactly one** grounding input — the declared
narrative voice in `bible/constitution.md` ("Voz narrativa: …"), already read by
the 5th (head-hopping) axis. It needs **neither** the roster **nor** the POV
calendar.

**Rationale**: A 1st-person break is a question of **grammatical person**
("does the narration slide into first person?"), not character identity
("which character's interiority is this?"). The roster and POV calendar exist to
resolve *identity* for head-hopping; the first-person axis has no identity to
resolve. Scope discipline (Constitution "Scope & Release Discipline"): inject
exactly what the dimension needs and nothing more.

**Note on design reconciliation**: `bookwright-design.md` § 20.6.2 decision 3
lumps "focalización / head-hopping / ruptura de 1ª persona" into one bullet that
names "la voz declarada + el personaje focal" as grounding. That phrasing is
accurate for head-hopping; for the **first-person** sub-dimension the focal
character is **not** consulted. The FR-018 design reconciliation must make this
explicit when it marks the dimension landed (the declared voice alone grounds the
1st-person axis). The DEBT-021 entry's older "voz declarada + roster + calendario
de POV" phrasing for the judgment half is superseded by the clarified
declared-voice-only grounding. The open `### DEBT-021` section is removed and the Track-C
bullet of the issue-#1 re-disposición closed-debt summary blockquote records the closure as a
struck-through `~~DEBT-021~~ (cerrada en la iteración 054 …)` entry stating the
declared-voice-only grounding, mirroring `~~DEBT-013~~` (FR-018) — so no stale forward-looking
reference survives.

**Alternatives considered**: (a) reuse the 5th axis's full grounding (voice + POV
calendar + roster) — rejected: it over-couples a grammatical-person check to
character identity and contradicts the clarification. (b) ingest grammatical
person into the graph — rejected: out of scope, no ontology change (Principle X),
and the declared voice is already authored prose the skill reads.

## Decision 2 — Scope: applies under all third person (limited OR non-limited)

**Decision**: The 6th axis applies under **any** declared third-person voice —
limited **and** non-limited (omniscient-but-third). Under a declared **first**
person it does **not** apply (the prose IS first person — nothing to report).

**Rationale**: This matches `focalization`'s 053 honesty half exactly: it emits
the `first_person_recall` abstention under **both** third-person branches
(`focalization.py:116-151` — `recall` is built once and returned in both the
`limited` `EvalResult` and the non-limited one). The 5th (head-hopping) axis is
**limited-only** because focalization only breaks under a *focalized* voice; a
1st-person slip breaks the third-person contract regardless of focalization. So
the nudge naturally fires wherever the abstention exists, and the skill axis must
mirror that scope (limited **or** non-limited).

**Alternatives considered**: limited-only (mirror the 5th axis literally) —
rejected: it would silently drop the non-limited third-person case the validator
already abstains on, re-introducing a coverage gap (the DEBT-019 class).

## Decision 3 — Discoverability: one new peer Rule, `_judges` unchanged

**Decision**: Add a `judge_first_person_recall` `Rule` with a `_judge_first_person_recall`
builder, `applies=_judges("focalization", "first_person_recall")`, inserted
**immediately after `judge_head_hopping` and before `define_focus`** in `RULES`.
`_judges` is **not** modified.

**Rationale**: Iteration 053 already generalized `_judges(validator)` →
`_judges(validator, code)` (`status/rules.py:155-173`) precisely so two
same-validator `focalization` abstentions stay distinguishable. The contract
plumbing is in place; this slice only **uses** it with a third peer rule. Placing
the rule between `judge_head_hopping` and `define_focus` keeps the three move-3
judge nudges adjacent and the emitted `next_actions` order deterministic
(`RULES` tuple order IS the priority order). The builder returns one fixed,
byte-identical `Action` (no minted data), distinct in `prompt`/`reason` from the
051 undeclared-character and 052 head-hopping actions (FR-010).

**Alternatives considered**: merging the first-person nudge into the head-hopping
one — rejected: FR-010/FR-011 require **distinct** actions, and the `code`
discriminator exists to keep them separate (a merged action would fire on the
wrong abstention and blur the two judgment tasks).

## Decision 4 — Description: fold the trigger, do not grow (1000/1024)

**Decision**: The description sits at **1000/1024** today (measured:
`uv run python -c "from bookwright.integrations.descriptions import
SKILL_DESCRIPTIONS as D; print(len(D['bookwright-continuity']))"` → `1000`).
The new 1st-person trigger is **folded** into the existing 5th-axis
voice/focalization phrase rather than appended — e.g. widen
«head-hopping / saltos de punto de vista / focalización rota» to also cover
«rupturas de voz / persona narrativa» (and the EN twin "head-hopping / POV
breaks" → "voice / narrative-person breaks") — staying ≤ 1024, mirrored
**verbatim** into `SKILL_DESCRIPTIONS["bookwright-continuity"]`.

**Rationale**: The hard cap (24 chars of slack) forbids a net-new ES/EN trigger
sentence. The 1st-person dimension is the **same** "voice/focalization" family as
head-hopping, so one widened trigger phrase covers both without growth. The
equality gate `tests/integrations/test_descriptions.py` requires the source
front-matter and the in-code mirror to be **byte-identical** — both must be
edited together (FR-015).

**Alternatives considered**: (a) append a new trigger — rejected: would exceed
1024. (b) compress unrelated prose to free room for a new sentence — allowed by
FR-006 as a fallback but riskier (could drop a 4th/5th trigger); folding is the
lower-risk primary. The final wording is fixed in `contracts/skill-sixth-axis.md`
and verified empirically by the lint + activation oracles.

## Decision 5 — Fixtures: reuse `tiny-historical`, no new fixture

**Decision**: The green-preserving e2e fixture is the **existing**
`tiny-historical` (third-person *limited*; since 053 it already carries the
`(focalization, pending_capability, first_person_recall)` abstention in
`expected-status.md`). This slice flips its `next_actions` skills list **5 → 6**
(a fourth `bookwright-continuity` nudge) while green stays. **No new fixture.**
The negative case (first-person voice → no nudge) lives at the pure
`test_rules.py` synthetic-state level (the rules module is `state → actions`,
no disk). `tiny-novel` / `tiny-memoir` stay GREEN.

**Rationale**: Scope discipline — no speculative fixture. `tiny-historical`
already exercises the full move-3 pipeline (it carries all three abstentions);
the only delta is that the first-person abstention now also fires a nudge. The
`expected-status.md` oracle is **co-located prose + YAML**: updating it is **not**
a YAML-only edit — the same edit MUST keep (i) the YAML `next_actions` 5 → 6,
(ii) the prose «cinco workstreams … tercer `bookwright-continuity`» → «seis … a
fourth», (iii) the convergence-frame «las acciones … (las tres) … sigue siendo
5» → «las cuatro … 6», and (iv) the inline `# nudge:` / iteration comments gain
the 054 first-person rule, all internally consistent (FR-017). Leaving any of
(ii)–(iv) stale is a forbidden internally-inconsistent oracle.

**Alternatives considered**: a new declared-first-person fixture for the negative
path — rejected: pure-unit coverage in `test_rules.py` (a synthetic
first-person-voice state has no `first_person_recall` abstention → no nudge)
covers it without disk, mirroring how 052 covered its negative path.

## Decision 6 — Existing `test_rules.py` move-3 tests flip from negative to positive

**Decision**: Two existing `test_rules.py` tests must update (they currently
assert the **pre-054** "no first-person nudge yet" state):

- `test_first_person_recall_alone_fires_no_judge_nudge` (line ~319) currently
  asserts a lone `(focalization, first_person_recall)` entry fires **no** nudge.
  Post-054 it fires **exactly one** `judge_first_person_recall` action → rename /
  rewrite to assert the positive (one `bookwright-continuity` first-person action,
  GREEN), and keep the **mis-fire negative** (it does **not** fire
  `judge_head_hopping`).
- `test_head_hopping_and_recall_together_fire_only_the_head_hopping_judge`
  (line ~329) currently asserts only the head-hopping nudge fires. Post-054
  **both** fire → rewrite to assert two distinct `bookwright-continuity` actions
  (head-hopping then first-person, table order), neither merged.
- The `_TRIGGER` dict (line ~91) gains a `judge_first_person_recall` entry
  (`make_state(not_evaluated=(_DORMANT_FOCAL_RECALL,))`) so every rule is
  exercised by its own synthetic state.

**Rationale**: These tests were written in 053 to pin the deliberate "honesty
without judgment" intermediate state; 054 is exactly the judgment half, so the
assertions invert. The new **negative** the spec requires (FR-011: the
first-person nudge never fires on `head_hopping`, and head-hopping never fires on
`first_person_recall`) is asserted explicitly — the `_DORMANT_FOCAL_CAP`
(head-hopping-only) state must yield **no** first-person action.

**Verification**: empirical — `uv run pytest` plus the four gates. No assertion
about LLM output (the skill body is prose).
