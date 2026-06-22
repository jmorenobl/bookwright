# Feature Specification: Tri-valued validator result (`evaluated` / `not-evaluated(reason)`)

**Feature Branch**: `040-tri-valued-validator-result`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "Un validador de Bookwright devuelve `list[Violation]`, y una lista vacía `[]` es INDISTINGUIBLE entre 'evalué y está limpio' y 'no tuve forma de mirar'. Esta iteración convierte el resultado de un validador en TRI-VALOR — `evaluado` (con o sin hallazgos) frente a `no-evaluado(motivo)` — de modo que VERDE signifique 'evaluado y limpio', no 'no se miró'. Cierra el hito v0.5.0 (issue #1, facet B)."

## Why this matters (context, not a requirement)

For an authoring tool, **false confidence is a worse failure than noise**. DEBT-004 was, literally, a validator that was **asleep and green** for the entire `v0.4` line: `focalization` could not parse the narrative-voice declaration, so it returned `[]`, which read as "focalization OK." Today three early `[]` returns mean "I had nothing to look at," yet they are indistinguishable from a legitimate clean run:

- `focalization` returns `[]` when there is no constitution, no parseable voice declaration, or the voice is still an unanswered `[PENDING: …]` placeholder.
- `character_presence` / `setting_continuity` produce nothing to inspect when the manuscript is empty.

This iteration closes that **class** of defect (issue #1, move 2 / facet B). It is the second of the two `v0.5.0` iterations and the one that **closes the milestone**; iteration 039 (the single prose/structure seam) is its predecessor and is already merged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A dormant validator can no longer read as green (Priority: P1)

An author runs `bookwright validate` (or reads `bookwright status`) on a project whose constitution has not yet declared a narrative voice (or still carries the `[PENDING: …]` placeholder a fresh `bookwright init` emits). Instead of `focalization` silently reporting "clean," the author sees `focalization` reported as **not-evaluated**, with a human-readable reason ("the constitution does not declare a narrative voice"). The author now knows the check did not run and what to do to activate it.

**Why this priority**: This is the entire point of the iteration — eliminating the false-confidence reading that hid DEBT-004 for a whole minor version. Without it, the feature delivers nothing.

**Independent Test**: Point `validate` at a fixture whose constitution lacks (or `[PENDING]`-holds) the voice declaration and assert the `--json` envelope lists `focalization` in the not-evaluated channel with a reason, and that the run is **not** reported as fully clean. Delivers value standalone: the dormant-validator blind spot is closed.

**Acceptance Scenarios**:

1. **Given** a project with no constitution file, **When** `bookwright validate --json` runs, **Then** `focalization` appears in the not-evaluated channel with a legible reason and is **not** counted among the validators that evaluated cleanly.
2. **Given** a constitution whose narrative voice is still `- **Voz narrativa**: [PENDING: …]`, **When** `validate` runs, **Then** `focalization` is reported not-evaluated with a reason naming the unanswered placeholder, reusing the placeholder detection introduced by the iteration-039 prose seam.
3. **Given** a constitution that **does** declare a third-person narrative voice and a manuscript with no breaks, **When** `validate` runs, **Then** `focalization` is reported **evaluated with zero findings** (a legitimate green), distinct from the not-evaluated state.

---

### User Story 2 - The empty-manuscript validators declare they could not look (Priority: P1)

An author with an empty (or not-yet-written) manuscript runs `validate`. `character_presence` and `setting_continuity` — whose work is scanning manuscript prose — report **not-evaluated** ("the manuscript is empty") rather than an empty findings list that reads as "manuscript is clean."

**Why this priority**: It is the second half of the same class. Closing only `focalization` would leave the identical false-confidence hole in the two manuscript-scanning validators.

**Independent Test**: Run `validate` on a fixture with a populated bible but an empty manuscript directory; assert `character_presence` and `setting_continuity` appear in the not-evaluated channel with the empty-manuscript reason, and the run is not reported as fully clean.

**Acceptance Scenarios**:

1. **Given** a project whose manuscript directory has no readable prose, **When** `validate` runs, **Then** `character_presence` and `setting_continuity` are reported not-evaluated with an empty-manuscript reason.
2. **Given** a project with manuscript prose present, **When** `validate` runs, **Then** both validators evaluate normally and any existing findings are produced **byte-for-byte unchanged** from today.

---

### User Story 3 - The third state is visible everywhere green is read (Priority: P2)

A skill (or a human) that reads `bookwright status` at the start of a session sees the not-evaluated validators reflected in the derived state, and — where an actionable remedy exists — a `next_actions` entry telling the author how to activate the dormant check (e.g. "declare the narrative voice in the constitution to activate `focalization`").

**Why this priority**: The tri-value is only useful if it propagates to the surfaces authors and skills actually read. It depends on US1/US2 producing the state, hence P2.

**Independent Test**: Run `bookwright status --json` on a fixture with a not-evaluated `focalization`; assert the derived state exposes the not-evaluated validator(s) and that `next_actions` contains the activation step, and that the same fact is surfaced by a status-reading skill's "Next steps" block.

**Acceptance Scenarios**:

1. **Given** a project where `focalization` is not-evaluated, **When** `bookwright status --json` runs, **Then** the derived validation state distinguishes not-evaluated validators from those that evaluated, and `next_actions` includes a step to activate `focalization`.
2. **Given** a project where every active validator evaluated, **When** `status` runs, **Then** no not-evaluated entries and no activation `next_actions` appear (no false positives).

---

### Edge Cases

- **A validator that crashes vs. one that consciously skips**: a validator that raises while loading or running is still reported through the existing `errors[]` channel as a `ValidatorError` (its shape unchanged). "not-evaluated" is a **third, distinct channel** for a validator that ran without error but consciously decided it had nothing to inspect — the two must never be conflated.
- **Partial evaluability**: a validator may have inputs for some of its checks but not others (e.g. `character_presence` faces an empty manuscript while the bible roster is non-empty). The verdict is **per-run and per-validator**, decided by the validator itself from its own preconditions; the planning phase must define, per validator, whether "empty manuscript" yields not-evaluated for the whole validator or only suppresses the manuscript-scanning sub-check. The chosen rule MUST NOT regress any existing finding (FR-012).
- **A custom user validator** (loaded from `.bookwright/validators/*.py`) that still returns a plain `list[Violation]`: it MUST keep working and be treated as **evaluated** (backward compatible), never as not-evaluated.
- **The gate**: a run consisting solely of not-evaluated validators (no `error` findings) does **not** fail CI — not-evaluated is not a finding — yet it is **never** reported as a clean pass either.
- **Determinism**: the not-evaluated channel is emitted in a fixed, deterministic order (e.g. by validator name), like every other channel, so the report is byte-identical across runs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `Validator` Protocol contract (`validation/base.py`, design § 13.1) MUST grow so that a validator declares, per run, whether it **evaluated** or **did-not-evaluate(reason)**, in addition to its `Violation` list. `bookwright-design.md § 13.1` MUST be updated to the new contract **before** the code diverges (plan § 7.3).
- **FR-002**: A not-evaluated result MUST carry the validator's name and a human-readable reason (e.g. "the constitution does not declare a narrative voice", "the narrative-voice declaration is still unanswered (`[PENDING]`)", "the manuscript is empty").
- **FR-003**: A validator that examined its inputs and found nothing MUST remain **evaluated with zero findings** (a legitimate green) — distinct from not-evaluated.
- **FR-004**: The new state MUST be **additive** and MUST NOT change the CI gate: only `Violation`s of `error` severity continue to fail CI. A not-evaluated result is **not** a gate failure (it is not a finding) but MUST be visible and MUST NOT be counted as clean.
- **FR-005**: not-evaluated MUST be a channel **distinct from `errors[]`**. `errors[]` remains for validators that could not be loaded or that raised (`ValidatorError`); not-evaluated is for a validator that ran without error and consciously chose not to evaluate.
- **FR-006**: The shape of `Violation` and of `ValidatorError` MUST NOT change.
- **FR-007**: The `bookwright validate --json` envelope MUST gain a channel for not-evaluated results (validator name + reason), a sibling of `violations` / `errors`. The human (non-JSON) report MUST also surface not-evaluated validators, distinct from both findings and a clean pass.
- **FR-008**: `focalization` MUST migrate its "could not look" early returns to the not-evaluated state, covering: no constitution, no parseable voice declaration, and a voice still in `[PENDING]` — reusing the iteration-039 prose-seam placeholder detection. A constitution that declares a usable narrative person remains evaluated.
- **FR-009**: `character_presence` and `setting_continuity` MUST report not-evaluated when the manuscript is empty (nothing to inspect), and remain evaluated when manuscript prose is present.
- **FR-010**: `bookwright status` MUST reflect the not-evaluated validators in its derived state and, where an actionable remedy exists, in `next_actions` (e.g. activating `focalization` by declaring the narrative voice).
- **FR-011**: Skills that read `status` at session start MUST surface the not-evaluated validators (the third state) in their "Next steps" / startup block.
- **FR-012**: **Zero functional regression** in existing findings: every fixture that produces a `Violation` today MUST keep producing it byte-for-byte. The only behavioral change is that "could not look" stops reading as green.
- **FR-013**: The not-evaluated channel MUST be emitted in a deterministic order (by validator name), consistent with the determinism of `violations[]` / `errors[]`.
- **FR-014**: Backward compatibility — a custom validator that returns a plain `list[Violation]` MUST be treated as **evaluated**, so existing custom validators keep working without edits.
- **FR-015**: Prose validators MUST stay graph-free, LLM-free, with `triples=()` and the frozen ontology untouched (Principle X). Severities and the `error`-only CI gate are unchanged.
- **FR-016**: The full quality bar MUST stay green: `mypy --strict` and the four CI gates (`ruff check`, `ruff format --check`, `mypy --strict`, `pytest` with ≥ 80 % coverage).

### Key Entities *(include if feature involves data)*

- **Validator verdict (tri-value)**: the per-run result of one validator — `evaluated` (carrying its `Violation` list, possibly empty) or `not-evaluated` (carrying a reason). Replaces the implicit "empty list ⇒ clean" reading at the Protocol seam.
- **Not-evaluated record**: a `(validator name, human-readable reason)` pair, surfaced as a channel sibling to findings and errors. It is not a finding (no severity, never gates) and not a load/run error.
- **Validation envelope (`--json`)**: the `bookwright validate` Principle-IX document; gains the not-evaluated channel alongside `violations` and `errors`, plus a clear summary that distinguishes evaluated-clean from not-evaluated.
- **Derived validation state (`status`)**: the status subsystem's validation summary; gains the not-evaluated dimension so `status` and `next_actions` can drive the author to activate a dormant validator.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the DEBT-004 scenario (no parseable narrative-voice declaration), `bookwright validate` reports `focalization` as not-evaluated with a reason and does **not** include it among the validators that passed clean — the dormant-validator-reads-green defect is reproducibly closed.
- **SC-002**: "Clean / green" now means **evaluated-and-clean only**: in any run, the set of validators reported as a clean pass excludes every not-evaluated validator. A run that is entirely not-evaluated is never reported as a clean pass.
- **SC-003**: **Zero edits** to existing finding oracles: the existing test suite's `Violation` counts are unchanged (byte-for-byte finding parity); only the not-evaluated state is added.
- **SC-004**: `bookwright status` on a project with a not-evaluated `focalization` yields a `next_actions` step that names the concrete remedy (declare the narrative voice in the constitution to activate `focalization`).
- **SC-005**: All four gates pass and `mypy --strict` is clean on the changed code; every changed/new source file stays ≤ 500 lines.

## Assumptions

- **Predecessor merged**: iteration 039 (the single prose/structure seam, `io/prose.py` with `is_placeholder` and the cached `manuscript_view()` / `constitution_view()` accessors) is on `main`; this iteration reuses its placeholder detection rather than re-implementing it.
- **Per-validator preconditions**: each validator decides its own evaluated/not-evaluated verdict from its own inputs; the runner/report/status layers are generic and do not know any validator's preconditions. The exact predicate for "empty manuscript" (whole-validator not-evaluated vs. sub-check suppression) is settled in planning under the FR-012 no-regression constraint.
- **Backward-compatible contract**: the Protocol change is designed so a validator returning a bare `list[Violation]` still type-checks and is read as evaluated, protecting user-authored custom validators.
- **JSON channel naming**: the not-evaluated channel is a new sibling key in the envelope and the status payload; its exact key name is fixed in planning/design, but it is additive (no existing key changes shape).
- **Scope of the migration set**: only the three validators the user named (`focalization`, `character_presence`, `setting_continuity`) migrate in this iteration. `temporal` and `factual_anchor` are graph-driven and are not part of the "surface could-not-look" class; they are not touched beyond conforming to the (backward-compatible) contract.
- **Milestone close**: after this iteration merges, `v0.5.0` is released **once** for both iterations 039 + 040 via the `bookwright-release` skill (bump `__version__` to `0.5.0`, CHANGELOG section, CLAUDE.md / design status edits, release commit, annotated tag). The release itself is a separate manual step, not part of this iteration's code.

## Out of Scope

- The **surface-coupling seam** (iteration 039) — already merged; this iteration depends on it but does not re-open it.
- **LLM semantic judgment** for validators (issue #1, move 3) — parked in the demand-pulled horizon, activated only when a concrete heuristic is measured insufficient.
- **Adding new validators** — the validator roster is unchanged; this iteration only enriches the result contract of existing validators.
