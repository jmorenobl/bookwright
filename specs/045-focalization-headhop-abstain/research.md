# Research: `focalization` head-hopping abstention (iteration 045)

All decisions below were settled by the issue #1 reframe (2nd dogfood, 2026-06-23)
and the hardened spec. No open `NEEDS CLARIFICATION` remains; this file records the
*what / why* and the alternatives rejected, per the design's contract-first doctrine.

## D1 — Abstention trigger precondition

- **Decision**: abstain (raise `NotEvaluated(kind=pending_capability)`) under exactly
  the precondition the deleted head-hopping heuristic ran today —
  `declaration.person == "third" AND declaration.limited` — whether or not a focal
  bible character resolves. The first-person-break check is retained for
  `person == "third" AND NOT limited` (omniscient/non-limited third).
- **Rationale**: same precondition ⇒ exact swap of the dormant heuristic for an honest
  abstention. A limited-third declaration that names no focal character is still the
  limited-third precondition (Edge Cases / Assumptions); the heuristic that *would* have
  run is the deleted one, so it abstains identically.
- **Alternatives rejected**: (a) keep the rare full-name-same-line head-hop hits and
  abstain only "when uncertain" — a finding-conditional hack the zero-debt doctrine
  forbids; a 95%-dormant false green is worse than losing the rare hit. (b) Loosen the
  matcher (first names, cross-line coreference) — chasing a semantic problem with more
  regex; issue #1 already ruled this has a precision ceiling.

## D2 — Deletion scope (clarified in spec Session 2026-06-23)

- **Decision**: delete the *whole* head-hopping-only chain, leaving zero dead code:
  `_head_hopping`, `_INTERIORITY`, the `_Declaration.focal` field, the focal-name
  computation block in `_parse_declaration`, and the `character_names`
  parameter/computation in `validate` (now orphaned). `_parse_declaration` drops its
  `character_names` argument.
- **Evidence**: `grep -rn "_head_hopping\|_INTERIORITY\|\.focal"` over `src/` + `tests/`
  returns matches **only** inside `focalization.py` and `tests/validation/
  test_focalization.py`. The `focal` field and the `character_names` param feed
  head-hopping alone, so keeping them is the unused-field/param smell (zero-debt
  doctrine §3) the class-sweep (§4) must close in full.
- **Rationale**: mirrors iteration 043, which *deleted* its open-set heuristic rather
  than parking it. Move 3 is a distinct semantic approach that does not reuse this
  regex; parking it is the speculative plumbing scope discipline forbids (FR-007).
- **Alternative rejected**: abstract `_head_hopping` "for move 3" — speculative
  plumbing; move 3 will be designed against the LLM `bookwright-verify` path, not this
  matcher.

## D3 — Reason string and kind

- **Decision**: `raise NotEvaluated("head-hopping / interiority attribution requires
  semantic judgment (move 3); the deterministic heuristic was measured nearly dormant on
  real prose", kind=NotEvaluatedKind.pending_capability)` — verbatim FR-002.
- **Rationale**: the precedent `character_unknown_mentions.py` (043) uses the identical
  shape ("requires semantic judgment (move 3); … measured insufficient on real prose").
  `_KIND_LABEL[pending_capability]` already renders a kind-generic tag; the
  validator-specific "move 3 / dormant" detail lives in the `reason`, per 044's render
  contract.

## D4 — The four input-conditional abstentions are untouched

- **Decision**: causes (i) no constitution, (ii) no declared voice, (iii) `[PENDING]`
  placeholder, (iv) no grammatical person keep the **default** `missing_input` kind with
  byte-identical reason strings; the 037 `_PENDING_ONLY` guard is preserved byte-for-byte.
- **Rationale**: these are author-fixable (declare/answer the voice) — they must keep
  denying green and firing the dormant nudge (FR-004/FR-005). Mislabeling them
  `pending_capability` would silence genuinely fixable problems.

## D5 — Oracle deltas are purely additive and empirical

- **Decision**: the only fixture-oracle delta is *adding* a `focalization`
  `pending_capability` entry to `not_evaluated[]`; no `warning` count drops in any
  current fixture.
- **Evidence**: on `tiny-historical`, the head-hopping heuristic emits **nothing**
  today (its full-name-same-line precondition is not met by the fixture manuscript), so
  removing it removes no finding. The fixture's lone `warning` is a `factual_anchor`
  finding, unrelated to focalization (`expected-status.md` note). `counts` stay
  `{error:1, warning:1, info:0}`; `next_actions` length stays 3 (capability-gap ⇒ no
  nudge). All verified with `uv run pytest`, never hand-computed (FR-010).

## D6 — Whole-validator abstention is a real coverage regression ⇒ DEBT-019

- **Decision**: because `NotEvaluated` is all-or-nothing (no partial-evaluation
  contract), a limited-third declaration abstains the **whole** run, so the
  deterministic first-person-break check no longer runs for limited-third projects
  (it still runs under non-limited third). This is recorded as **DEBT-019** (already
  present in `DEBT.md`), and the design note states the over-claim plainly (FR-014).
- **Rationale**: containing it with a finding-conditional hack (return `[]` vs. abstain
  depending on whether `_first_person_breaks` found something) is exactly the smell the
  doctrine forbids. The real fix is a partial-evaluation contract (040/044-scale) or
  move 3 — out of scope here, which only *consumes* `pending_capability`.

## D7 — No 044 machinery change (FR-009)

- **Decision**: no edit to the green predicate, `NotEvaluatedKind`, the `not_evaluated[]`
  serialization, the `status` nudge rule, or the report render.
- **Evidence**: `status/rules.py` already filters the nudge to `missing_input`
  (`r.kind is NotEvaluatedKind.missing_input`); `report.py` `_KIND_LABEL` already maps
  `pending_capability`; `tests/conftest.py::is_green` already encodes the kind-refined
  predicate; `NotEvaluatedResult.to_json()` already emits `kind`. 045 only adds a new
  *raise site* that flows through all of it. The `_REMEDIES["focalization"]` clause
  **stays** — `focalization` still has `missing_input` causes that need the remedy.
