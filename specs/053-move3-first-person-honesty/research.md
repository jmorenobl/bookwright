# Phase 0 Research — abstention `code` discriminator + first-person-recall honesty

No `NEEDS CLARIFICATION` markers remain: the spec's **Clarifications / Session 2026-06-25**
already pinned the open questions. This file records the design decisions, their rationale,
and the alternatives rejected, anchored in the **iteration-044 `kind` precedent** (the
closest, byte-for-byte template for adding an additive discriminator end-to-end).

## D1 — `code` is an optional `str | None = None`, not a closed enum

- **Decision**: add `code: str | None = None` to `Abstention` and `NotEvaluatedResult`;
  free-form short string owned by each validator (`"head_hopping"`,
  `"first_person_recall"`, `"undeclared_characters"`).
- **Rationale**: additive and backward-compatible — no existing field renamed or retyped;
  an abstention needing no discriminator leaves it `None`. Mirrors how 044 added `kind`,
  except `kind` was a closed `StrEnum` because it has a fixed two-member vocabulary that
  drives green/gating logic. `code` drives only nudge keying and there are exactly three
  values, each living with its validator.
- **Alternatives rejected**: a `CodeKind(StrEnum)` registry — speculative generality
  (Constitution Scope discipline; spec Assumptions). Only three values exist; a registry is
  its own change if ever warranted. Making `code` required — would force every existing
  `raise NotEvaluated` site and `NotEvaluatedResult` construction to supply a value,
  breaking the additive contract.

## D2 — only **returned** abstentions (form (c)) carry `code`; the **raised** exception (form (b)) does not

- **Decision**: the `NotEvaluated` exception keeps its `(reason, kind)` signature. The
  runner stamps `code=None` for the raised path and `abstention.code` for the returned
  path, through the same single `_record` naming authority.
- **Rationale**: a raised total abstention is one-per-validator and never needs
  intra-validator disambiguation; only a validator that **returns multiple** abstentions
  (form (c) `EvalResult`) needs the discriminator. Minimal contract surface (doctrine § 3:
  no plumbing without a consumer). Confirmed by spec clarification Q1.
- **Consequence**: a code-keyed predicate needs a `code` on the wire, and FR-004 keeps the
  raised path code-less. So `character_unknown_mentions` — today a raised total abstention —
  **must convert** to a returned partial abstention to carry `code="undeclared_characters"`
  (see D4). This is the only forced structural change beyond the additive field.

## D3 — the runner stamps `code` through the existing single naming point

- **Decision**: `_record(name, reason, kind)` → `_record(name, reason, kind, code=None)`.
  The `except NotEvaluated` arm calls `_record(validator.name, skip.reason, skip.kind)`
  (code defaults `None`); the `EvalResult` arm calls
  `_record(validator.name, abstention.reason, abstention.kind, abstention.code)`.
- **Rationale**: the stamping authority MUST NOT fork (FR-003, contract C2). `_record` is
  already the one place `validator` and `kind` are stamped; threading `code` through the
  same call site keeps a single source of truth. Exact replay of how 044 added `kind`.

## D4 — `character_unknown_mentions`: form (b) → form (c), observationally additive

- **Decision**: replace `raise NotEvaluated(reason, kind=pending_capability)` with
  `return EvalResult([], [Abstention(reason, kind=NotEvaluatedKind.pending_capability,
  code="undeclared_characters")])`. The `reason` text and `kind` are byte-identical.
- **Rationale**: `EvalResult([], [Abstention(r, k)])` is **observationally identical** on
  the wire to `raise NotEvaluated(r, k)` (design § 13.1, base.py docstring) — one
  `not_evaluated` entry, zero findings, same `(validator, reason)` sort position — **except**
  the additive `code` key moves from `null` to `"undeclared_characters"`. So the 051/052
  nudge fires in exactly the same states. The conversion is **mandated** by FR-004 (the only
  way the abstention can carry a `code`), not a gratuitous refactor.
- **Alternatives rejected**: keeping it raised and special-casing `_judges` to treat a
  `code`-less `character_unknown_mentions` abstention as `undeclared_characters` — that
  hard-codes a validator name into the predicate (the exact name-only coupling this
  iteration removes) and would not generalize. Adding `code` to the `NotEvaluated`
  exception — rejected by D2/FR-004.

## D5 — `status` keying generalizes from `_judges(validator)` to `_judges(validator, code)`

- **Decision**: predicate becomes `r.validator == validator AND r.kind is
  NotEvaluatedKind.pending_capability AND r.code == code`. Re-point
  `judge_undeclared_characters` → `_judges("character_unknown_mentions",
  "undeclared_characters")` and `judge_head_hopping` → `_judges("focalization",
  "head_hopping")`.
- **Rationale**: with `focalization` emitting two `pending_capability` abstentions, the
  052 validator-name keying would fire the head-hopping nudge on the first-person abstention
  and **mis-fire** under third-person-non-limited (first-person present, head-hopping
  absent). Keying by `code` is exactly what name-only keying cannot express. Confirmed by
  spec clarification Q3.
- **Note**: `judge_undeclared_characters` behavior stays byte-identical (that source emits
  only one abstention, now carrying `code="undeclared_characters"`).

## D6 — `code` does **not** enter the `not_evaluated` sort key

- **Decision**: `not_evaluated_sort_key` stays `(validator, reason)` unchanged.
- **Rationale**: `focalization`'s two abstentions carry **distinct `reason` strings**
  (`"full first-person recall requires…"` vs `"head-hopping / interiority…"`), so the
  existing key already totally orders them deterministically. Alphabetically `"full…"`
  sorts before `"head-hopping…"`, fixing their relative order byte-identically across runs.
  Adding `code` to the sort would change the runner's single shared sort literal for no
  correctness gain (doctrine § 3). Confirmed by spec clarification Q5.

## D7 — `code` flows into `status` for free

- **Decision**: no new plumbing in `status/model.py` or `status/queries.py` beyond what the
  field gives.
- **Rationale**: `ValidationSummary.not_evaluated` holds the runner's `NotEvaluatedResult`
  tuples directly (`status/queries.py:validation_summary` passes `run_validators`' output
  through unchanged), and `_judges` reads `r.code` off those records. Once the runner stamps
  `code`, `status` carries it with zero further edits (spec Assumptions). `to_payload`
  serializes via `NotEvaluatedResult.to_json`, which now includes `code` — so the `status`
  payload gains the key additively, same as `validate`.

## D8 — no new green/gate behavior

- **Decision**: `report.py` is **untouched**; the 044 green predicate
  (`status ok AND no not_evaluated entry has kind == missing_input`) is byte-identical;
  `activate_dormant_validators` stays `missing_input`-only; the CI gate stays error-only.
- **Rationale**: the new abstention is `pending_capability`, which never degrades green and
  is never author-actionable. No `error` is born from this change (FR-016/FR-017).

## D9 — fixtures by declared voice (what each oracle gains)

Surveyed every fixture constitution (`grep "Voz narrativa"`):

| Fixture | Declared voice | Effect of this iteration |
|---|---|---|
| `tiny-historical` | 3rd limited (Elena Vidal) | gains `focalization`/`first_person_recall` entry → **3** `not_evaluated` entries; all entries gain `code`; `next_actions` stays **5** (head-hop nudge still fires, no first-person nudge). |
| `tiny-novel` | 3rd limited (Ada Reyes) | gains `first_person_recall` + already-present head-hopping; both `pending_capability` → stays GREEN. |
| `tiny-quest` | 3rd limited (Liria) | same as `tiny-novel` (no dedicated oracle file). |
| `tiny-memoir` | 1st person | `return []` branch — **no** recall abstention; stays GREEN (only `character_unknown_mentions`, now code-bearing). |
| `tiny-essay` | 1st person | same as `tiny-memoir`. |
| `tiny-undeclared-voice` | `[PENDING]` | raises `NotEvaluated` (`missing_input`) — untouched; entry serializes `code: null`. |

The tri-valued e2e (`test_tri_valued_validation.py`) builds `{validator: kind}` dicts; both
`focalization` entries are `pending_capability`, so its existing assertions still hold — but
the test is **strengthened** to assert the new `first_person_recall` `code` for the
third-person fixtures (FR-019), so the masking of the second entry does not hide a
regression.

## D10 — contract-before-code documentation

- **Decision**: before code diverges, mark the contract in `bookwright-design.md`
  (§ 13.4: `not_evaluated` gains `code`, the discriminator, as 044 added `kind`; § 13.5 /
  § 20.6.x: move 3 distinguishes dimensions by `code`, the first-person-recall honesty
  landed, judgment deferred to 054), update **DEBT-021** (do not remove — honesty exists,
  judgment + closure is 054), and flip CLAUDE.md milestone prose + iteration index (row
  053).
- **Rationale**: the repo's contract-before-code doctrine (CLAUDE.md, zero-debt) — the
  design record is the source of truth the code realizes.
