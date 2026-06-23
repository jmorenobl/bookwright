# Implementation Plan: `focalization` head-hopping abstains as a permanent capability-gap

**Branch**: `045-focalization-headhop-abstain` | **Date**: 2026-06-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/045-focalization-headhop-abstain/spec.md`

## Summary

The `focalization` validator runs a deterministic, LLM-free head-hopping check under
a declared **third-person-limited / focalized** voice: it flags interiority verbs
attributed to a non-focal bible character. The 2nd dogfood (`sombra-en-el-puerto`)
measured that rule as **practically dormant** (a false negative): it only fires on a
character's **full bible name** on the **same physical line** as the verb, while real
prose names characters by first name / epithet across several lines (DEBT-014). Per
issue #1 (track A — honesty), a head-hop heuristic without semantic judgment has a
precision ceiling, so — exactly as iteration 043 did with the open-set unknown-mention
rule — the head-hopping rule **stops faking**: when a parseable limited-third voice is
declared, `focalization` raises `NotEvaluated(<reason>, kind=pending_capability)`
instead of running the near-null heuristic. The deterministic heuristic and everything
that fed it alone (`_head_hopping`, `_INTERIORITY`, `_Declaration.focal`, the focal-name
computation, the now-orphaned `character_names` threading) are **deleted** — zero dead
code, mirroring 043. The four input-conditional abstentions keep `missing_input`.

This iteration only **consumes** machinery 044 already shipped (`NotEvaluatedKind`,
the kind-stamped runner, the kind-refined green predicate / nudge, the `_KIND_LABEL`
render). No green-predicate, channel, status-rule, or render change is needed (FR-009).
The all-or-nothing `NotEvaluated` contract forces the whole validator to abstain under
limited-third — dropping the still-working first-person-break check for that case — a
genuine, currently-invisible coverage regression recorded as **DEBT-019** (FR-015).

## Technical Context

**Language/Version**: Python 3.11+ (`uv`, `hatchling`, src-layout) — Constitution II.

**Primary Dependencies**: none added — stdlib `re` only (FR-013). The change is a
*deletion* plus one `raise`; no new runtime import.

**Storage**: N/A. `focalization` is a prose validator: reads constitution +
manuscript views from the cached `ValidationContext`, writes nothing, emits no graph
triples (`triples=()`, FR-012, Constitution X).

**Testing**: `uv run pytest` (full suite, ≥80% coverage gate). The new behavior is
verified by `tests/validation/test_focalization.py` (unit), `tests/e2e/
test_tri_valued_validation.py` (clean-fixture green), and the `tiny-historical`
`expected-status.md` oracle (E2E).

**Target Platform**: CLI (`bookwright validate` / `bookwright status`), in-process.

**Project Type**: single project (src-layout CLI). No new directories.

**Performance Goals**: N/A — the change *removes* a per-line scan (the deleted
head-hopping loop), so it is strictly cheaper.

**Constraints**: every changed source file ≤ 500 lines (FR-013); `focalization.py`
is 190 lines today and shrinks. Deterministic (Validator contract). No frozen-ontology
edit.

**Scale/Scope**: one validator module, its design-doc contract, two test files, one
pinned oracle, and `DEBT.md` (remove DEBT-014; DEBT-019 already present).

## Constitution Check

*GATE: passes before Phase 0 research, re-checked after Phase 1 design.*

- **I — Plain-text source of truth**: ✅ Contract-before-code — `bookwright-design.md`
  (the `focalization` contract) is updated to document the new head-hopping
  `pending_capability` cause *and* the whole-validator abstention **before** the code
  diverges (FR-014, plan §7.3). The graph stays a derived cache; no source format
  changes.
- **II — Locked stack**: ✅ stdlib only, no new dependency (FR-013).
- **IV — File size / one concern**: ✅ `focalization.py` shrinks well under 500 lines;
  the single CLI subcommand boundary is untouched.
- **V — Plugin shapes / no monolithic dispatcher**: ✅ `focalization` stays a single
  auto-discovered validator (FR-006); it is **not** split as `character_presence` was.
- **VI/VII — Agent Skills**: N/A (no skill or integration change).
- **VIII — Test discipline ≥80%**: ✅ deleted code's tests are removed (a deleted
  heuristic has no behavior to assert, FR-016); the remaining/added tests keep coverage
  green (the abstention `raise` is exercised by unit + E2E).
- **IX — JSON envelope**: ✅ unchanged — the `not_evaluated[]` entry serializes through
  the existing `NotEvaluatedResult.to_json()` (`kind` already additive, 044). No
  envelope-shape edit.
- **X — Frozen ontology**: ✅ prose validator, `triples=()`, `golem.ttl` / `CLASS_IRI`
  untouched (FR-012).
- **Scope & release discipline**: ✅ the deleted heuristic is **not** parked "for move
  3" (move 3 is a distinct semantic approach, not this regex) — deleting it is the
  anti-speculative-plumbing rule (FR-007). Out-of-scope debt (the dropped
  first-person-break check) is recorded as DEBT-019, never dropped silently (FR-015).

**Result: PASS — no violations, no Complexity Tracking entries.**

## Project Structure

### Documentation (this feature)

```text
specs/045-focalization-headhop-abstain/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (deletion scope, oracle deltas, DEBT-019)
├── data-model.md        # Phase 1 — the validate() decision tree + deleted symbols
├── quickstart.md        # Phase 1 — runnable verification scenarios
├── contracts/
│   └── focalization-validator.md   # the validator's abstention contract
├── spec.md              # already present
└── tasks.md             # Phase 2 — created by /speckit-tasks, NOT here
```

### Source Code (repository root)

```text
src/bookwright/validation/
├── base.py                          # UNCHANGED — NotEvaluatedKind, runner stamp (044)
├── runner.py                        # UNCHANGED — stamps skip.kind (044)
└── validators/
    └── focalization.py              # CHANGED — limited-third → raise pending_capability;
                                     #   delete _head_hopping, _INTERIORITY, _Declaration.focal,
                                     #   the focal-name computation, the character_names threading

src/bookwright/validation/report.py  # UNCHANGED — _KIND_LABEL already covers the kind (044)
src/bookwright/status/rules.py        # UNCHANGED — nudge filters missing_input; remedy stays (044)

bookwright-design.md                  # CHANGED — § 13.2 row + § 13.5 note (FR-014, contract-first)
DEBT.md                               # CHANGED — remove DEBT-014 (FR-011); DEBT-019 already present

tests/validation/test_focalization.py            # CHANGED — see §7.4
tests/e2e/test_tri_valued_validation.py          # CHANGED — tiny-novel gains focalization entry
tests/fixtures/tiny-historical/expected-status.md# CHANGED — add focalization not_evaluated entry
```

**Structure Decision**: Single project, existing layout. The whole change is local to
`validators/focalization.py` plus its contract doc, its tests, and the pinned oracle —
mirroring how iteration 043 localized `character_unknown_mentions`.

## Phase 0 — Research (decisions)

See [research.md](./research.md). Headlines (all already settled by the spec /
issue #1, transcribed here, no open NEEDS CLARIFICATION):

- **D1 — Trigger precondition.** Abstain exactly under the precondition the deleted
  heuristic ran today: `person == "third" AND limited`, whether or not a focal bible
  character resolves (the focal field is being deleted anyway). The first-person-break
  check stays for `third AND NOT limited`.
- **D2 — Deletion scope (clarified).** Delete the *whole* head-hopping-only chain
  (grep-confirmed zero external consumers): `_head_hopping`, `_INTERIORITY`,
  `_Declaration.focal`, the focal-name computation in `_parse_declaration`, and the
  `character_names` parameter/computation in `validate`. `_parse_declaration`'s
  signature drops its `character_names` argument.
- **D3 — Reason string + kind.** Verbatim FR-002 reason, `kind=pending_capability`.
- **D4 — Four input-conditional abstentions unchanged** (`missing_input`, byte-identical
  reasons), including the 037 `_PENDING_ONLY` guard (FR-004/FR-005).
- **D5 — Oracle deltas are empirical.** Head-hopping emits nothing on `tiny-historical`
  today, so the only oracle delta is *adding* the `focalization` `not_evaluated` entry;
  no `warning` count drops anywhere (Assumptions).
- **D6 — Whole-validator abstention ⇒ DEBT-019.** Recorded (already in `DEBT.md`);
  the design note must state the over-claim plainly (FR-014).

## Phase 1 — Design & Contracts

- [data-model.md](./data-model.md) — the new `validate()` decision tree, the surviving
  `_Declaration(person, limited)` shape, and the exact symbols deleted.
- [contracts/focalization-validator.md](./contracts/focalization-validator.md) — the
  abstention contract: which precondition raises which `kind`, the reason strings, and
  the invariants (single validator, `triples=()`, no envelope change).
- [quickstart.md](./quickstart.md) — runnable verification scenarios.

### §7.3 Contract-before-code ordering (Constitution I)

The design edit lands **before** the validator diverges:

1. `bookwright-design.md` § 13.2 — annotate the `focalization` row: under a declared
   third-person-**limited** voice the validator now **abstains wholly**
   (`pending_capability`, head-hopping is move 3); the first-person-break check runs
   only under third-person **non-limited**.
2. `bookwright-design.md` § 13.5 — move 1 already names "el head-hopping de
   `focalization`" as declaring `NotEvaluated`; add a one-line note that the abstention
   is *whole-validator* (the deterministic first-person-break check no longer runs for
   the limited-third case — DEBT-019), so the written contract does not over-claim.

Only then edit `focalization.py`.

### §7.4 Test plan (FR-016 — no test left asserting a dead path)

- **Delete** (exercised the deleted heuristic):
  `test_head_hopping_on_non_focal_character_warns`.
- **Retarget to abstention** (asserted a finding under limited-third that is now an
  abstention):
  - `test_english_declaration_parses_equivalently` — declares *third limited focused on
    Aparici* with a first-person break; today asserts a first-person finding. Under 045
    the whole validator abstains, so it must assert `NotEvaluated(kind=pending_capability)`
    (this is the DEBT-019 drop made concrete).
  - `test_replacing_placeholder_with_real_voice_wakes_validator` — the wake-from-PENDING
    now produces a `pending_capability` abstention, not a head-hopping warning; retarget
    the assertion accordingly (the [PENDING]→real-voice transition is still proven).
- **Update parser tests** for `_parse_declaration`'s dropped `character_names` argument
  and the removed `.focal` field: `test_bullet_marker_parses_like_bare_form`,
  `test_emphasis_run_parses_like_bare_form`, `test_scaffold_shape_parses_to_concrete_values`
  (drop the `focal == "Elena Vidal"` assertion), `test_english_scaffold_shape_parses`,
  `test_indented_scaffold_shape_parses`, `test_pending_recognition_boundary`,
  `test_template_binding`, `test_label_mid_sentence_is_not_a_declaration`, and the
  module-level `_BARE = _parse_declaration(prose_view(...), _NAMES)` fixture — drop
  `_NAMES`. Keep them asserting `person`/`limited` (the retained parser surface).
- **Unchanged** (declare third-person **non-limited** or first-person, so still
  evaluate): `test_first_person_outside_dialogue_warns`, `test_dialogue_line_is_exempt`,
  `test_usable_third_person_is_evaluated_and_clean`,
  `test_usable_first_person_is_evaluated_and_clean`,
  `test_first_person_locator_is_source_line_over_raw`,
  `test_bullet_prefixed_line_stays_dialogue_exempt`, and the four `missing_input`
  not-evaluated tests + the live-scaffold `[PENDING]` tests.
- **Add** a unit test: a parseable third-limited focal voice → exactly one
  `NotEvaluated` with `kind == pending_capability` and the FR-002 reason; and (edge case)
  a third-limited voice with **no** named focal character likewise abstains.
- **E2E** `test_tri_valued_validation.py::test_clean_fixture_is_green_under_refined_predicate`
  — `tiny-novel` (third-limited) now carries `{character_unknown_mentions, focalization}`
  both `pending_capability`; `tiny-memoir` (first-person) still only
  `character_unknown_mentions`. The shared `entries == {...}` literal must become
  per-fixture (both must stay **green**). Confirm with `tests/e2e/test_narrative_workflow.py`
  (tiny-quest) that nothing else regresses.

### §7.5 Oracle delta (FR-010, empirical)

`tests/fixtures/tiny-historical/expected-status.md`: add a second `not_evaluated`
entry (`validator: focalization`, the FR-002 reason, `kind: pending_capability`),
keeping the list **sorted by validator name** (`character_unknown_mentions` then
`focalization`). `validation.counts` stay `{error: 1, warning: 1, info: 0}`;
`next_actions` length stays **3** (the entry is `pending_capability` → no nudge);
update the explanatory prose. Verified by `uv run pytest`, not hand-computed.

### §7.6 Agent context update

Update the managed plan pointer in `CLAUDE.md` (between the SPECKIT markers) to this
plan, via the `after_plan` agent-context hook.

## Complexity Tracking

No Constitution violations — section intentionally empty.
