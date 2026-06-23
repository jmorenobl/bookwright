# Implementation Plan: `not_evaluated` distinguishes a capability-gap from an input-gap; green is reachable again

**Branch**: `044-not-evaluated-kinds` | **Date**: 2026-06-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/044-not-evaluated-kinds/spec.md`

## Summary

Iteration 043 made the open-set proper-noun rule honest by splitting out
`character_unknown_mentions`, a **pure abstainer** that raises `NotEvaluated`
**unconditionally**. As a side effect it broke the iteration-040 green contract:
because that abstainer is dormant in *every* project, the documented predicate
`status == "ok" AND not_evaluated == []` is now `False` everywhere (even a
flawless project), and the `_activate_dormant_validators` nudge fires in every
project — exactly the alarm fatigue issue #1 set out to kill, merely relocated to
the `not_evaluated` channel.

The root cause is that **two kinds** of `not_evaluated` entry now share one
channel that governs green: **(a) input-conditional** ("I could not evaluate
*your* project because an input is missing/malformed" — actionable, per-project,
transient) and **(b) permanent capability-gap** ("no deterministic run evaluates
this; it awaits move 3" — not author-actionable, identical everywhere,
permanent).

**Technical approach**: add a small closed `NotEvaluatedKind` vocabulary (a
`StrEnum`, mirroring the existing `Severity`) carried on the `NotEvaluated`
signal (default `missing_input`, so every existing raise is byte-for-byte
unchanged — FR-002) and stamped by the runner onto the recorded
`NotEvaluatedResult` (additive `kind` field, serialized in `to_json`).
`character_unknown_mentions` opts into `pending_capability` (FR-003). The green
predicate (a documentation + test-helper concept, exactly as 040 modelled it) and
the `_activate_dormant_validators` nudge are **refined to consider only
`missing_input` entries** (FR-004/FR-005). Capability-gap entries stay fully
visible in all three surfaces (`--json`, `status`, human report), labeled by a
**kind-generic** human tag (FR-007) — the validator-specific "move 3" detail
stays in the unchanged `reason`. The contract docs (`bookwright-design.md`
§ 13.1/§ 13.4 + the `report.py` docstring) are updated **before** the code
diverges (plan § 7.3 doctrine). The gate is untouched; only the informative green
predicate and the nudge change behavior.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II)

**Primary Dependencies**: stdlib only for this change — `enum.StrEnum`,
`dataclasses`. No new runtime dependency (FR-013, Constitution II). Existing
`typer`/`rich`/`rdflib` untouched.

**Storage**: N/A — the validation subsystem persists nothing; `not_evaluated`
records are in-memory only (base.py module docstring).

**Testing**: `pytest` (+ `pytest-cov`, ≥ 80 % `fail_under`); `mypy --strict`;
`ruff check` + `ruff format --check`. The four CI gates.

**Target Platform**: cross-platform CLI (`bookwright`).

**Project Type**: single src-layout Python package (`src/bookwright/`).

**Performance Goals**: N/A — one enum tag added to an existing in-memory record;
no new disk read, no new graph query, no SPARQL.

**Constraints**: every changed file ≤ 500 lines (Principle IV); prose validators
keep emitting `triples=()`; the frozen 17-class ontology (`golem.ttl` / `CLASS_IRI`)
is untouched (FR-013, Constitution X); additive across every serialized surface —
no pre-existing key renamed or retyped (SC-007); the CI gate is unchanged — only
`error` gates (FR-009).

**Scale/Scope**: ~6 source files touched, all small edits: `validation/base.py`
(new enum + two fields), `validation/runner.py` (stamp the kind),
`validation/validators/character_unknown_mentions.py` (pass the kind),
`validation/report.py` (refine docstring + label the kind in the render),
`status/rules.py` (filter the nudge by kind + drop the 043 remedy clause), plus
the `bookwright-design.md` § 13 contract and the `tiny-historical` oracle. No new
module, no new CLI verb, no fixture manuscript/bible edit.

## Constitution Check

*GATE: must pass before Phase 0 and re-checked after Phase 1.*

- **I — Plain-text source of truth**: PASS. The graph stays a derived cache; no
  source of truth moves. The contract is re-documented in the plain-text design
  spec **before** the code diverges (Assumption / plan § 7.3).
- **II — Locked stack**: PASS. stdlib `StrEnum` only; no dependency added.
- **III — Test discipline ≥ 80 %**: PASS by design. Every behavior change is
  reachable from synthetic state (SC-004): new unit tests for the kind on the
  signal/result/`to_json`, the refined green predicate (capability-gap green vs
  input-gap not-green), the kind-filtered nudge, and the kind in all three
  surfaces; the `tiny-historical` oracle + `tiny-undeclared-voice` e2e extend
  the existing `not_evaluated` tests. SC-001/SC-002 (the headline "clean fixture
  reads green / no nudge") additionally get an **automated fixture-level** guard
  over `tiny-novel`/`tiny-memoir` (not only synthetic state) — the regression
  guard 043 lacked, which is why this iteration exists.
- **IV — File size / one verb per module**: PASS. All edits are small additions;
  no file approaches 500 lines (base.py ~322, report.py ~135, rules.py ~213).
- **V — Plugin integrations / no monolith dispatcher**: N/A (no integration
  change).
- **VI/VII — Agent Skills only / agentskills limits**: N/A (no skill file edited;
  the `bookwright-continuity` skill already exists and is unchanged — only when it
  is *recommended* changes).
- **VIII — JSON-over-stdout (Principle IX)**: PASS. `kind` is an **additive** key
  on the `not_evaluated[]` element in both the `validate --json` envelope and the
  `status` payload; no existing key renamed/retyped (SC-007/FR-008).
- **IX — Single error envelope**: N/A — `NotEvaluated` is deliberately **not** a
  `BookwrightError` (it carries no error envelope); this is unchanged.
- **X — Frozen ontology**: PASS. No `.ttl`, no class, no triple touched.
- **Scope discipline**: PASS. No plumbing-for-future-X. The kind vocabulary is
  exactly two values, both used now (`missing_input` by every default raise,
  `pending_capability` by the one abstainer). `character_presence`/`io/prose.py`
  are explicitly out of scope (FR-013).

**Result: PASS — no violations, Complexity Tracking left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/044-not-evaluated-kinds/
├── plan.md              # This file
├── spec.md              # Feature spec (already present)
├── research.md          # Phase 0 — decisions (kind representation, render label, the line-116/hint reconciliation)
├── data-model.md        # Phase 1 — NotEvaluatedKind + the two fields + serialized shapes
├── contracts/
│   └── not-evaluated-kind.md   # The additive JSON delta across validate --json + status payload + human report
├── quickstart.md        # Phase 1 — runnable validation scenarios (clean → green; capability-gap → green; input-gap → not green)
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── validation/
│   ├── base.py                 # + NotEvaluatedKind(StrEnum); NotEvaluated.__init__ gains kind (default missing_input);
│   │                           #   NotEvaluatedResult gains kind field + serializes it in to_json
│   ├── runner.py               # stamp skip.kind onto NotEvaluatedResult (runner.py:69)
│   ├── report.py               # refine the green-predicate docstring (~line 50); label the kind in render (~line 130)
│   │                           #   — the line-116 clean-line early-return is UNCHANGED (see research.md)
│   └── validators/
│       └── character_unknown_mentions.py   # raise NotEvaluated(reason, kind=pending_capability)
├── status/
│   ├── rules.py                # _activate_dormant_validators filters kind == missing_input; drop the 043 remedy clause
│   └── model.py                # ValidationSummary.to_payload already delegates to r.to_json() → kind flows automatically (verify only)

bookwright-design.md            # § 13.1 (NotEvaluated signature + tri-valued note) and § 13.4 (refined green predicate quote) — updated FIRST

tests/
├── validation/test_report.py            # refine _is_green helper to filter kind; add capability-gap-green + input-gap-not-green cases; kind in render
├── validation/test_runner.py            # the runner stamps kind onto the result; default missing_input preserved
├── validation/test_character_unknown_mentions.py  # asserts kind == pending_capability on the raise
├── validation/test_setting_continuity.py / test_focalization.py / test_character_presence.py  # assert their raises keep kind == missing_input (default)
├── status/test_rules.py                 # nudge fires for missing_input, suppressed for pending_capability-only; remedy clause gone
├── commands/test_status.py              # status payload not_evaluated[] carries kind
├── e2e/test_tri_valued_validation.py    # _is_green helper refined (focalization input-gap stays not-green)
└── fixtures/tiny-historical/expected-status.md   # oracle: kind on the entry, next_actions 4→3, counts byte-identical
```

**Structure Decision**: single src-layout package (Option 1). No new module or
directory is introduced — the change is a closed two-value vocabulary threaded
through the existing `NotEvaluated` → `NotEvaluatedResult` → (`report` / `status`)
path that 040 already established.

## Phase 0 — research

See [research.md](./research.md). Key decisions resolved there:

1. **Kind representation** — a `StrEnum NotEvaluatedKind` in `validation/base.py`,
   mirroring the existing `Severity` StrEnum (JSON-friendly `.value`, typed,
   closed). Two members: `missing_input` (default) and `pending_capability`.
2. **Default placement** — `kind` is the *last* field on `NotEvaluatedResult`
   with a default, and the *last* parameter on `NotEvaluated.__init__` with a
   default, so every existing construction/raise compiles unchanged (FR-002,
   SC-007).
3. **The green predicate stays a docstring + test-helper concept** (no new code
   property), exactly as 040 modelled it — refined to "no `missing_input`
   entry". This avoids speculative API and keeps the single documented predicate
   in one prose place (report.py docstring + design § 13.4).
4. **The render clean-line early-return (report.py line 116) is NOT filtered by
   kind** — this resolves a divergence between the `/speckit-plan` hint and the
   spec: FR-010 + the "capability-gap-only" Edge Case forbid printing
   "no violations found" when the only content is a not-evaluated entry of
   *either* kind. The kind change in the render is limited to **labeling** each
   entry in the existing `not evaluated:` section (line ~130).
5. **The human kind label is generic to the kind** (FR-007), held in a small
   `_KIND_LABEL` map in `report.py` (the validator-specific "move 3" wording
   stays in `reason`).
6. **`status/model.py` needs no serialization edit** — `ValidationSummary.to_payload`
   already calls `r.to_json()`, so `kind` flows into the payload automatically
   once `NotEvaluatedResult.to_json` includes it. Verified, not edited.

## Phase 1 — design & contracts

- **data-model.md** — the `NotEvaluatedKind` enum, the two new fields, the
  serialized shapes (additive `kind` key), and the full inventory of the seven
  default (`missing_input`) raises vs the one `pending_capability` raise (FR-002/FR-003).
- **contracts/not-evaluated-kind.md** — the additive JSON delta on the
  `not_evaluated[]` element across `validate --json` and the `status` payload,
  plus the human-report rendering, with the refined green predicate and the
  refined nudge rule stated as observable contracts.
- **quickstart.md** — runnable scenarios proving SC-001..SC-006: a clean fixture
  reads green while carrying the capability-gap entry; an input-gap run is not
  green and still nudges; the gate is unchanged; the `tiny-historical` oracle
  matches.

**Agent context update**: the managed `<!-- SPECKIT -->` block in `CLAUDE.md` is
repointed to this plan.

## Complexity Tracking

> No Constitution violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
