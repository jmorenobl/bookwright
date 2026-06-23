# Implementation Plan: Split `character_presence` — orphan rule (`error`) stays; unknown-mention rule declares `not_evaluated`

**Branch**: `043-character-presence-split` | **Date**: 2026-06-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/043-character-presence-split/spec.md`

## Summary

The `character_presence` validator bundles two rules of opposite nature: an **orphan**
rule (`error`, closed-set, sound — every bible character must be mentioned) and an
**unknown-mention** rule (`warning`, open-set — is every capitalized proper-noun candidate
in a bible roster?). The second dogfood (`sombra-en-el-puerto`, 2026-06-23) measured the
unknown-mention rule on real prose as **100 % noise** (4 false positives, 0 signal). Per
issue #1 (track A — honestidad, design § 13.5), the open-set rule **stops pretending**: it
declares `not_evaluated` instead of emitting `warning`.

Because `NotEvaluated` (iteration 040) is **per-validator** — raising it aborts the *whole*
validator and would discard the orphan `error` findings — the two rules are **separated into
two auto-discovered built-in validators**:

1. **`character_presence`** (name **unchanged**) keeps the orphan rule **only**. Its `error`
   findings stay **byte-for-byte identical** (same `validator` field → the gate and every
   pinned `error` oracle are untouched). It retains its existing `NotEvaluated` guard
   (`not roster and not files`) with the **identical** reason string (FR-003/FR-004).
2. **`character_unknown_mentions`** (new module, new name) is a **pure abstainer**: its
   `validate` is solely `raise NotEvaluated(<open-set reason>)`, **unconditionally** —
   because the *approach*, not the inputs, is unreliable (FR-005, clarification Q3). It
   emits no findings ever; it surfaces through the existing 040 `not_evaluated[]` channel
   (FR-006). No new channel.

The **entire** deterministic unknown-mention heuristic is **deleted** (FR-016) — the
candidate scan, stop-set, sentence-initial exemption, roster-slug builder, the union-roster
construction (DEBT-010/042), and any imports they leave unused. The repo-wide dead-code
sweep (FR-017) also deletes the iteration-042 `ValidationContext.location_names()` /
`object_names()` accessors (now zero-consumer) and the `write_project` `locations=` /
`objects=` knobs. `setting_names()` and the `settings=` knob are **retained** (still consumed
by `setting_continuity`). `io/prose.py` is **not touched** (FR-009).

**The under-specified consequence this plan surfaces (design-significant).** Because
`character_unknown_mentions` is *always* dormant, the **existing** status rule
`activate_dormant_validators` (iteration 040, `status/rules.py`) — which fires whenever
`state.validation.not_evaluated` is non-empty — now fires on **every** project, contributing
one `bookwright-continuity` action. This is the visible form of FR-008 (the green predicate
is now `False` everywhere). It is **not** a new channel; it is the 040 channel doing exactly
what it was built to do. Its ripple is real and catalogued below (§ Source/Test ripple): the
`tiny-historical` `next_actions` goes 3 → 4 and `tiny-novel`'s B1 inertness assertion needs
reframing. We **accept** this (the alternative — special-casing the permanent abstainer out
of the channel — is rejected by FR-006 and the spec's "no special-casing" edge case).

The only pinned-**count** oracle delta is **none**: `tiny-historical`'s
`validation.counts` stay `{error: 1, warning: 1, info: 0}` because `character_presence`
already emitted **zero** on that fixture post-042 (verified empirically; clarification Q1).
The oracle gains a `not_evaluated` entry and a 4th `next_actions` action.

## Technical Context

**Language/Version**: Python 3.11+ (locked by Constitution II).

**Primary Dependencies**: stdlib only (`re` stays in `character_presence.py` for the orphan
matcher; the new abstainer imports nothing beyond `validation.base`). **No new dependency**
(Constitution II). File-based, not SPARQL (design § 13).

**Storage**: plain-text bible read once per run via `ValidationContext.bible()` → `map_bible`.
The orphan rule reads `character_names()` + `manuscript_files()`; the abstainer reads nothing.
The derived graph is **not** consulted by either validator.

**Testing**: `pytest` with ≥80 % coverage (Principle VIII). The existing
`test_character_presence.py` is **migrated** to the split shape (orphan/guard tests kept;
every unknown-mention/seam/union test deleted), a new `test_character_unknown_mentions.py`
proves the unconditional abstention, and the 040 `not_evaluated[]` channel test pattern
(`tests/e2e/test_tri_valued_validation.py`, `tests/status/test_queries.py`) is reused. The
full suite is the empirical zero-regression gate (FR-012).

**Target Platform**: CLI (`uv run bookwright validate` / `status`), cross-platform.

**Project Type**: single src-layout Python package (`src/bookwright/`).

**Performance Goals**: N/A. The abstainer returns before any I/O; the orphan rule reads one
fewer roster than before (no setting/location/object union).

**Constraints**: every changed file ≤ 500 lines (Principle IV); deterministic, no disk
writes, no graph mutation (validator contract); both validators emit `triples=()`
(Principle X). No `io/prose.py` edit (FR-009). No `golem.ttl`/ontology edit (FR-013).

**Scale/Scope**: 1 new source file, 3 source edits (`character_presence.py` shrinks ~223 →
~95; `base.py` ~340 → ~320; `status/rules.py` +1 remedy clause), 1 new test file, ~7 test
edits, 1 oracle edit, `DEBT.md`. Net **deletion**-heavy.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I — Plain-text source of truth**: ✅ rosters derive from `bible/**/*.md`; the graph stays
  a derived cache, not read here. DEBT-011/012 removed from the plain-text `DEBT.md` (FR-010).
- **II — Locked stack**: ✅ no new dependency; stdlib only; `io/prose.py` untouched.
- **IV — File size / one subcommand per module**: ✅ all changed files stay well under 500
  lines (`character_presence.py` *shrinks*); the new validator is its own module
  (FR-013/FR-002). No module gains a second subcommand.
- **V — Plugin shapes**: ✅ the new validator is auto-discovered by `registry.py` exactly like
  every built-in (no hand-registration, FR-002); no integration/indexer change.
- **VI — Agent Skills only**: ✅ N/A — no skill / `commands/` change.
- **VIII — Test discipline ≥80 %**: ✅ neither validator ships without coverage — the orphan
  rule keeps its migrated tests, the abstainer gets its own `NotEvaluated` test, and the
  full suite proves zero `error` regression (FR-014/FR-012).
- **IX — `--json` over stdout**: ✅ the `Violation`/envelope shapes are byte-stable; the
  `not_evaluated[]` channel is the existing 040 contract (FR-006). Exit codes unchanged
  (not-evaluated never gates, FR-007).
- **X — Frozen GOLEM ontology**: ✅ no class added, no `.ttl` edited; both validators'
  `triples` stay `()` (FR-013, SC-008). The deletion of `location_names()`/`object_names()`
  only removes *accessors*; the `NarrativeLocation`/`Object` concepts stay frozen and present.
- **Scope & Release Discipline**: ✅ one observable behavior delta (the open-set warning
  becomes an honest `not_evaluated`). The dead heuristic is **deleted, not parked** — keeping
  it "for move 3" would be the forbidden speculative plumbing the spec calls out (FR-016).
  Move 3, DEBT-014, DEBT-018, and any opt-in deterministic mode are **out of scope** (FR-015).

**Result: PASS** (no violations; Complexity Tracking table left empty).

## Source / Test ripple (the precise blast radius)

The split changes the **set** of validators, so every place that pins that set or the
`not_evaluated`/`next_actions` derived from it must move. Catalogued so `/speckit-tasks` and
`/speckit-implement` leave nothing red:

### Source (`src/`)

1. **NEW** `validation/validators/character_unknown_mentions.py` — `CharacterUnknownMentions`,
   `name = "character_unknown_mentions"`, `severity_default = Severity.warning` (cosmetic — it
   never emits); `validate` body is solely `raise NotEvaluated(<open-set reason>)`.
2. `validation/validators/character_presence.py` — keep `CharacterPresence` (name unchanged),
   `_orphans`, `_is_mentioned`, `_MIN_TOKEN_LEN`, the `not roster and not files` guard.
   **Delete** `_CANDIDATE`, `_SENTENCE_END`, `_STOP_WORDS`, `_is_sentence_initial`,
   `_roster_slugs`, `_unknown_mentions`, and the `setting/location/object` union line. **Remove
   now-unused imports** `make_slug` and `ProseView`. Trim the module/class docstring to the
   orphan-only rule. The `validate` body becomes: guard → `return self._orphans(roster, files)`.
3. `validation/base.py` — **delete** `location_names()`, `object_names()`, the
   `_location_names`/`_object_names` cache fields, and the `NarrativeLocation`/`Object` local
   imports inside those accessors. **Keep** `setting_names()`, `_names_of`, the `_UNSET`
   sentinel, and the `Character`/`Setting` imports.
4. `status/rules.py` — add a `_REMEDIES["character_unknown_mentions"]` clause so the
   always-firing `activate_dormant_validators` prompt is **honest** (e.g. *"awaiting LLM
   semantic judgment (move 3) — no manual action available yet"*) instead of the misleading
   generic *"investigate why it could not evaluate"*. This uses the **existing** dormant-prompt
   channel (FR-006, Story 4 legibility), adds no rule and no new channel.

### Tests (`tests/`)

5. `validation/test_character_presence.py` — **migrate**: keep the three orphan/guard tests
   (`test_no_prose_and_empty_roster_is_not_evaluated`,
   `test_empty_manuscript_with_roster_stays_evaluated_and_emits_orphans`,
   `test_orphan_bible_character_is_error`) and the clean-project test. **Delete** every
   unknown-mention / seam / union test (sentence-initial, heading, blockquote, dialogue-dash,
   mid-line, declared setting/location/object suppression, off-bible-still-fires, locator,
   guard-with-declared-environments) — the rule they exercised no longer exists.
6. **NEW** `validation/test_character_unknown_mentions.py` — assert
   `CharacterUnknownMentions().validate(...)` raises `NotEvaluated` with the exact open-set
   reason **regardless** of inputs (empty project, clean project, project with off-roster
   proper nouns), and that `severity_default` is set. Reuse `write_project`/`load_context`.
7. `validation/test_base.py` — delete `test_location_and_object_names_read_and_cache` and
   `test_location_and_object_names_empty_when_dir_absent`. Leave the `setting_names()` coverage
   in `test_context_accessors_cache_and_read` intact (it still consumes `settings=`).
8. `validation/conftest.py` — remove the `locations=` / `objects=` knobs from `write_project`
   and their two scaffold loops + dir creation. **Keep** `settings=`. Update the docstring.
9. `validation/test_registry.py` — add `"character_unknown_mentions"` to `_BUILTINS` (6 → 7).
10. `validation/test_command.py` — add `"character_unknown_mentions"` to the exact `ran` set
    assertion (`test_json_is_single_document_…`, 6 → 7). The line-85 subset loop needs no edit.
11. `commands/test_status.py` — `len(state["validation"]["ran"]) == 6` → `== 7`; in
    `test_known_state_yields_the_exact_next_actions`, append the 4th action
    `"bookwright-continuity"` (the dormant nudge) and update its comment (no longer "exactly
    three").
12. `status/test_queries.py` — `test_validation_summary_surfaces_not_evaluated_sorted`: the
    subset + `sorted` assertions still pass; update the "three validators" comment to four and
    (recommended) add `assert "character_unknown_mentions" in names`.
13. `e2e/test_orchestration_workflow.py` — Group A: `len(next_actions) == 3` → `== 4` (both
    `test_second_status_converges` frames); the 4th action is byte-identical across runs, so
    `_invariant_view` equality still holds. **Recommended**: assert the `not_evaluated` entry
    appears. Group B (`test_focus_free_project_recommends_no_research_workstream`): the
    `research_skills.isdisjoint(_skills(payload))` assertion **breaks** because
    `bookwright-continuity` is now in `_skills` (the always-dormant nudge) *and* in the oracle
    skill set. Reframe the disjoint set to the **research-derived** skills only —
    `{"bookwright-research", "bookwright-verify"}` — since `bookwright-continuity` is dual-purpose
    (`review_continuity` *and* `activate_dormant_validators`).

### Fixtures / docs

14. `tests/fixtures/tiny-historical/expected-status.md` — add a `not_evaluated` block
    (one entry: `character_unknown_mentions` + its reason); change `next_actions.skills` to the
    4-entry list `[bookwright-research, bookwright-verify, bookwright-continuity,
    bookwright-continuity]`; update the convergence prose ("tres workstreams"/`len == 3` → the
    4-action shape, with the dormant nudge explained). **Manuscript/bible untouched** (FR-011).
    `validation.counts` stays byte-identical (FR-011, SC-005).
15. `DEBT.md` — remove the **DEBT-011** and **DEBT-012** entries (subsumed, FR-010); keep
    DEBT-014/DEBT-018; update the track-A doctrine note so it no longer lists 011/012 as
    pending.

## Project Structure

### Documentation (this feature)

```text
specs/043-character-presence-split/
├── plan.md              # This file (/speckit-plan output)
├── spec.md              # Feature spec (already hardened)
├── research.md          # Phase 0 output (this command)
├── data-model.md        # Phase 1 output (this command)
├── quickstart.md        # Phase 1 output (this command)
├── contracts/
│   └── validator-split.md   # the two validators' contracts + the not_evaluated entry shape
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── validation/
│   ├── base.py                              # − location_names()/object_names() + cache fields + imports
│   └── validators/
│       ├── character_presence.py            # orphan-only; delete the entire unknown-mention heuristic
│       └── character_unknown_mentions.py    # NEW — pure abstainer: raise NotEvaluated(open-set reason)
└── status/
    └── rules.py                             # + _REMEDIES["character_unknown_mentions"] honest clause

tests/
├── validation/
│   ├── conftest.py                          # write_project: − locations=/objects= knobs (keep settings=)
│   ├── test_base.py                         # − location/object accessor tests
│   ├── test_character_presence.py           # migrate to orphan/guard-only
│   ├── test_character_unknown_mentions.py   # NEW — unconditional NotEvaluated
│   ├── test_registry.py                     # _BUILTINS 6 → 7
│   └── test_command.py                      # exact `ran` set 6 → 7
├── commands/test_status.py                  # ran 6→7; known-state next_actions 3→4
├── status/test_queries.py                   # comment/assert update (not_evaluated)
├── e2e/test_orchestration_workflow.py       # Group A len 3→4; Group B disjoint reframe
└── fixtures/tiny-historical/expected-status.md  # + not_evaluated entry; next_actions 3→4 (counts unchanged)

DEBT.md                                      # remove DEBT-011 + DEBT-012 (FR-010)
```

**Structure Decision**: single src-layout package (the only option this repo uses). The
behavioral core is two lines of intent — *the orphan validator keeps everything; a new
abstainer validator replaces the heuristic with one honest `raise`* — and the rest is the
mechanical dead-code sweep (FR-016/FR-017) plus the validator-set ripple (§ above).

## Complexity Tracking

> No Constitution Check violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
