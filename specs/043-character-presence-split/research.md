# Phase 0 — Research: split `character_presence`, the open-set rule declares `not_evaluated`

All unknowns are resolved against the live code (no NEEDS CLARIFICATION remains). Each
decision records what was chosen, why, and what was rejected.

## D1 — Two validators, not one validator with two channels

- **Decision**: Separate the rules into two **auto-discovered built-in** validators:
  `character_presence` (orphan, `error`) keeps its name; `character_unknown_mentions` (new
  module/name) is the open-set abstainer.
- **Rationale**: `NotEvaluated` (iteration 040) is **per-validator** — the runner catches it
  per `validator.validate()` call and routes that *whole* validator to `not_evaluated[]`
  (`validation/runner.py:64-70`). A single validator cannot both emit `error` findings **and**
  declare `not_evaluated`; raising would discard the orphans. Splitting makes each verdict
  **atomic**, which is exactly what 040 wanted (FR-002, spec User Story 3).
- **Alternatives rejected**: (a) a per-rule result object inside one validator — would require
  changing the `Validator` Protocol return type (`list[Violation]`), a frozen seam (design
  § 13.1); rejected. (b) keep emitting `info` instead of `warning` — still pretends to evaluate;
  contradicts the issue #1 decision (design § 13.5). Rejected.

## D2 — The orphan validator keeps the name `character_presence`

- **Decision**: The orphan rule stays in the class `CharacterPresence` with
  `name = "character_presence"` **unchanged**; the abstainer takes the new name.
- **Rationale**: `Violation.validator` is part of the JSON contract **and** of the runner's
  dedup/sort key (`runner.sort_key`) **and** of the CI gate's keying. Every pinned `error`
  oracle and the gate read this field. Only a name-preserving split keeps the `error` findings
  **byte-for-byte identical** (FR-003, clarification Q2, SC-003).
- **Alternatives rejected**: rename the orphan validator to e.g. `character_orphans` and give the
  abstainer the historical name — would change every `error` finding's `validator` field and
  the gate's keying. Rejected (would be a gate behavior change, explicitly out of scope).

## D3 — The abstainer is unconditional

- **Decision**: `character_unknown_mentions.validate` is solely
  `raise NotEvaluated(<open-set reason>)` — no input check, no branch.
- **Rationale**: the open-set proper-noun problem is unreliable **by approach**, not by missing
  input. Conditioning the abstention on "has prose" / "has roster" would falsely imply that with
  enough input it *could* evaluate (clarification Q3, FR-005). The permanent entry is the point:
  the green predicate is honestly `False` on every project until move 3 (FR-008).
- **Reason string (locked)**: `"open-set proper-noun discovery requires semantic judgment
  (move 3); the deterministic heuristic was measured insufficient on real prose"` — names the
  open-set/NER cause and references move 3 (FR-005, matches the spec's example verbatim-shape).
- **Alternatives rejected**: abstain only when prose is present (mirroring `setting_continuity`'s
  `"the manuscript is empty"`) — wrong: even a clean manuscript must abstain. Rejected.

## D4 — Delete the heuristic; do not park it

- **Decision**: Delete the **entire** deterministic unknown-mention heuristic from
  `character_presence.py` — `_CANDIDATE`, `_SENTENCE_END`, `_STOP_WORDS`, `_is_sentence_initial`,
  `_roster_slugs`, `_unknown_mentions`, the union-roster line — plus the imports they orphan
  (`make_slug`, `ProseView`).
- **Rationale**: FR-016 (eliminate-the-cause). Move 3 is a *different*, semantic approach that
  does **not** reuse this code; keeping it "for later" is the forbidden speculative plumbing the
  constitution's Scope & Release Discipline rejects. Git preserves the history.
- **Verification before deletion** (FR-017, repo-wide grep `src/` + `tests/`): `make_slug` in
  `character_presence.py` is used **only** by `_roster_slugs`/`_unknown_mentions`; `ProseView`
  only by `_unknown_mentions`'s signature; `_SENTENCE_END`/`_is_sentence_initial`/`_CANDIDATE`/
  `_STOP_WORDS` only by `_unknown_mentions`. `_is_mentioned` and `_MIN_TOKEN_LEN` are used by
  `_orphans` → **kept**. `re` stays (orphan matcher). All confirmed zero-consumer-after-removal.

## D5 — Repo-wide dead-code sweep: drop the iteration-042 accessors and knobs

- **Decision**: Delete `ValidationContext.location_names()` and `object_names()` (with their
  `_location_names`/`_object_names` fields and the `NarrativeLocation`/`Object` imports), and the
  `write_project` `locations=`/`objects=` knobs. **Keep** `setting_names()` and the `settings=`
  knob.
- **Rationale**: grep confirms the **only** consumers of `location_names`/`object_names` are
  `character_presence.py:123` (deleted) and the `test_base.py` accessor tests (deleted by this
  iteration). After the split they are zero-consumer → retaining them solely "for move 3" is
  speculative plumbing (FR-017). `setting_names()` is still consumed by
  `setting_continuity.py:52` (and its tests) → retained. The `locations=`/`objects=` knobs are
  consumed only by `test_base.py` and the union tests in `test_character_presence.py`, both
  removed/migrated here → removed. (`settings=` is consumed by `test_setting_continuity.py` and
  `test_command.py` → kept.)
- **Alternatives rejected**: keep the accessors as "harmless cached helpers" — they would be dead
  code by SC-009's grep, and the spec mandates their removal. Rejected.

## D6 — The always-dormant validator fires `activate_dormant_validators` on every project

- **Decision**: Accept that the existing `status/rules.py` rule `activate_dormant_validators`
  (predicate `bool(s.validation.not_evaluated)`) now fires on **every** project, contributing one
  `bookwright-continuity` action; add a tailored `_REMEDIES` clause so its prompt is honest.
- **Rationale**: This is the visible form of FR-008 (green predicate `False` everywhere) flowing
  through the **existing** 040 channel (FR-006 — "no new channel"). The spec's edge case forbids
  special-casing the built-in. The tailored remedy ("awaiting LLM semantic judgment (move 3)")
  serves Story 4's legibility; the generic fallback would mislead ("investigate why it could not
  evaluate" implies a fixable misconfiguration).
- **Consequence (the spec under-specified this)**: `next_actions` shifts on every fixture.
  `tiny-historical` goes 3 → 4 actions; `tiny-novel`'s B1 "no research workstream fires"
  assertion must be reframed because `bookwright-continuity` is dual-purpose. Catalogued in
  plan.md § Source/Test ripple. This is surfaced, not hidden (fix-defective-specs-properly).
- **Alternatives rejected**: (a) suppress permanent-abstainers from `next_actions` via a new
  predicate/flag — a new channel/special-case, violates FR-006 and the edge case. Rejected.
  (b) leave the generic remedy — dishonest for a known-permanent gap, contradicts the iteration's
  thesis. Rejected in favor of the tailored clause.

## D7 — Reuse the 040 `not_evaluated[]` test patterns

- **Decision**: Prove the abstainer with (1) a unit test that `validate` raises `NotEvaluated`
  with the exact reason across input shapes, and (2) the existing channel-level patterns —
  `tests/e2e/test_tri_valued_validation.py` (the `_is_green` predicate + `not_evaluated[]`
  envelope) and `tests/status/test_queries.py:231` (`validation_summary` surfacing). No new test
  harness.
- **Rationale**: 040 already wired and tested every channel (`--json`, report, `status`,
  `next_actions`); reusing them keeps the contract stable (FR-006) and avoids re-plumbing.

## D8 — No ontology / seam / dependency change

- **Decision**: Both validators emit `triples=()`, need no built graph, touch no `.ttl`, and add
  no dependency. `io/prose.py` is **not** modified.
- **Rationale**: FR-009/FR-013, Principle X, Constitution II. The seam still backs
  `setting_continuity` and `focalization`; the dialogue-dash stripping (DEBT-009/041) stays in
  effect for them. The DEBT-011 paired-quote seam is **not** added and the DEBT-012 title-body
  exemption is **not** applied — those false positives vanish because the rule abstains (FR-009).
