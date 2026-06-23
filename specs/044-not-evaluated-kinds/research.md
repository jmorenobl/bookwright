# Phase 0 — Research: `not_evaluated` kinds

All decisions below are resolved (no open NEEDS CLARIFICATION). The iteration is
small and threads one closed vocabulary through the 040 `not_evaluated` path.

## D1 — How to represent the two kinds

- **Decision**: a `StrEnum NotEvaluatedKind` in `src/bookwright/validation/base.py`
  with exactly two members:
  - `missing_input = "missing_input"` — input-conditional (the 040 default).
  - `pending_capability = "pending_capability"` — permanent capability-gap.
- **Rationale**: mirrors the existing `Severity(StrEnum)` in the same module
  (lines 36–49) — same JSON-friendliness (`.value` is the wire string), same
  `mypy --strict` exhaustiveness, same "closed vocabulary as a typed enum" idiom
  the codebase already uses. A `Literal["missing_input", "pending_capability"]`
  was the alternative named in the hint; rejected because an enum gives a natural
  home for the human label map and matches the file's existing `Severity`
  precedent, keeping the module internally consistent.
- **Alternatives considered**: (a) a bare string field — rejected, untyped, no
  closed set; (b) a boolean `actionable` flag — rejected, it bakes the *policy*
  (does it deny green?) into the *category*; the spec wants the category named and
  the policy derived from it (FR-001/FR-004), and a third future kind would have
  nowhere to go.

## D2 — Preserving every existing raise byte-for-byte (FR-002)

- **Decision**: `kind` is the **last** parameter of `NotEvaluated.__init__` with a
  default of `NotEvaluatedKind.missing_input`, and the **last** field of the
  frozen `NotEvaluatedResult` dataclass with the same default.
- **Rationale**: every current raise (`raise NotEvaluated(reason)`) and every
  current construction (`NotEvaluatedResult(name, reason)`) keeps compiling and
  keeps producing the identical kind (`missing_input`) and identical behavior
  (denies green, fires the nudge) — that is FR-002 and the "custom third-party
  validator defaults to input-conditional" edge case, with zero edits to the four
  `focalization` raises, the `setting_continuity` raise, and the
  `character_presence` raise.
- **The complete default set** (audited, all stay `missing_input`):
  | Raise site | Reason (unchanged) |
  |---|---|
  | `focalization.py:74` | "there is no constitution to read the narrative voice from" |
  | `focalization.py:82` | "the narrative-voice declaration names no grammatical person (neither first nor third)" |
  | `focalization.py:167` | "the constitution does not declare a narrative voice" |
  | `focalization.py:170` | "the narrative-voice declaration is still unanswered ([PENDING])" |
  | `setting_continuity.py:49` | "the manuscript is empty" |
  | `character_presence.py:34` | "there is no manuscript prose and no bible character roster to cross-check" |
  | any custom third-party validator | (its own reason) |
- The **only** non-default raise is `character_unknown_mentions.py:32` →
  `pending_capability` (FR-003), reason string unchanged.

## D3 — The runner stamps the kind

- **Decision**: at `runner.py:69` the conscious-skip handler builds
  `NotEvaluatedResult(validator.name, skip.reason, skip.kind)` — the kind is
  stamped onto the recorded result exactly as the validator name and reason
  already are.
- **Rationale**: the validator is the only party that knows whether the gap is
  about *this* input or about the *approach* (Assumption in the spec). The runner
  is the single place that materializes the result, so the stamp lives there with
  the existing two stamps. No other runner logic changes; `not_evaluated` still
  sorts by validator name.

## D4 — The green predicate: documentation + test-helper, refined by kind

- **Decision**: keep the green predicate as a **documented definition** (the
  `report.py` `ValidationReport` docstring ~line 50 + `bookwright-design.md`
  § 13.4 quote) plus the `_is_green(payload)` **test helpers** that read the JSON
  — exactly the shape iteration 040 shipped. Refine all three to:
  > A run is **green/clean** ⟺ `status == "ok"` **and** there is no
  > `not_evaluated` entry whose `kind == "missing_input"`.
  Capability-gap entries do not deny green.
- **Rationale**: 040 did *not* introduce a code property for green; it documented
  the predicate and asserted it in tests via `_is_green(payload)` reading the
  `--json` envelope. Adding a code property now would be API the spec does not
  ask for. The refined predicate is observable from the JSON (the new `kind` key
  makes it readable without re-parsing the reason string — User Story 3) and is
  verified on `tiny-novel`/`tiny-memoir` (SC-001) and synthetically (SC-004).
- **Alternatives considered**: a `ValidationReport.clean` property — rejected as
  speculative API (YAGNI / scope discipline); the predicate has exactly two
  consumers (the docstring contract and the tests), both served by the helper.

## D5 — The render clean-line (report.py line 116) is NOT filtered by kind

- **Decision**: leave the render early-return
  `if not reported and not self.errors and not self.not_evaluated:` **unchanged**
  (both kinds keep the terse "no violations found" line suppressed). The kind
  change in the render is limited to **labeling** each entry inside the existing
  `not evaluated:` section.
- **Rationale**: the `/speckit-plan` hint suggested filtering line 116 by kind,
  but that contradicts the spec: **FR-010** ("MUST NOT print the 'no violations
  found' clean line when the only content is a not-evaluated entry of **either**
  kind") and the **Edge Case** "A run whose only content is a capability-gap entry
  must not print the 'no violations found' clean line … the entry stays visible in
  the `not evaluated:` section." Filtering line 116 by `missing_input` would make a
  capability-gap-only run print the clean line and early-return, **hiding** the
  entry — reintroducing the 040 silence. The spec governs; line 116 stays
  both-kinds. (Greenness is informative and lives in the predicate of D4; the
  render clean-line is about *visibility*, which is non-negotiable per issue #1.)

## D6 — The human kind label is generic to the kind (FR-007)

- **Decision**: a small `_KIND_LABEL: dict[NotEvaluatedKind, str]` map in
  `report.py`, e.g.
  - `missing_input` → `"input gap"`
  - `pending_capability` → `"known limitation — no action available yet"`
  The render line becomes `f"  {result.validator} [{label}]: {result.reason}"`.
- **Rationale**: FR-007 requires the kind label to read as a non-actionable known
  limitation (for the capability-gap) and to be **generic to the kind**, never
  hardcoding one validator's specifics — so the validator-specific "move 3"
  wording stays in the unchanged `reason`. The exact wording is a UX detail
  (Assumption); the constraint is "reads as a known limitation, not a silent
  pass". Holding the map in `report.py` keeps rendering concerns in the renderer;
  the JSON carries the raw `kind` value, not the human label (FR-008).

## D7 — `status` surfaces and the nudge

- **Decision**:
  - `ValidationSummary.to_payload` (status/model.py) already serializes each
    entry via `r.to_json()`, so the additive `kind` key flows into
    `state.validation.not_evaluated[]` **automatically** once
    `NotEvaluatedResult.to_json` includes it — verified, no edit (SC-003/FR-008
    for the status payload).
  - `_activate_dormant_validators` (status/rules.py) filters
    `dormant = [r for r in state.validation.not_evaluated if r.kind == NotEvaluatedKind.missing_input]`,
    and the rule's `applies` predicate likewise tests for any `missing_input`
    entry. The `_REMEDIES["character_unknown_mentions"]` clause added in 043 is
    removed (FR-006) — the validator is no longer nudged on.
- **Rationale**: this is the one behavioral status change (FR-005): only
  actionable gaps produce the "activate the dormant validators" recommendation. A
  capability-gap-only project (e.g. a clean `tiny-novel`, or `tiny-historical`
  whose only entry is the abstainer) produces **zero** such actions — SC-002,
  next_actions 4→3 on `tiny-historical`.

## D8 — How 040 tested the channel, and the extension

- **Observed**: 040 proved the channel with (a) unit tests in
  `tests/validation/test_report.py` (`test_to_json_carries_not_evaluated_sibling_key`,
  `test_green_predicate_false_for_solely_not_evaluated_run`,
  `test_green_predicate_true_for_evaluated_and_clean_run`,
  `test_render_prints_not_evaluated_section_instead_of_clean_line`) using a local
  `_is_green(payload)` helper, and (b) the e2e
  `tests/e2e/test_tri_valued_validation.py` over `tiny-undeclared-voice` with its
  own `_is_green`.
- **Extension**: refine both `_is_green` helpers to filter by `kind`; add the two
  discriminating cases (capability-gap → green; input-gap → not green) and assert
  `kind` is present and correct in `to_json`, the status payload, and the render.
  The `tiny-undeclared-voice` e2e stays **not green** (its `focalization` gap is
  `missing_input`). No new fixture is needed.

## D9 — Contract-before-code ordering (plan § 7.3)

- **Decision**: update `bookwright-design.md` § 13.1 (the `NotEvaluated`
  signature + a tri-valued-table note on the kind) and § 13.4 (the refined green
  predicate quote) **before** editing the validators — the same discipline 040
  used ("the concrete contract is updated *before* the code diverges").
- **Rationale**: Principle I + the spec Assumption ("re-documented where 040
  documented it" … "before the code diverges from the docs").
