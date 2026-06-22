# Feature Specification: Tri-valued validator result (`evaluated` / `not-evaluated(reason)`)

**Feature Branch**: `040-tri-valued-validator-result`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "Un validador de Bookwright devuelve `list[Violation]`, y una lista vacía `[]` es INDISTINGUIBLE entre 'evalué y está limpio' y 'no tuve forma de mirar'. Esta iteración convierte el resultado de un validador en TRI-VALOR — `evaluado` (con o sin hallazgos) frente a `no-evaluado(motivo)` — de modo que VERDE signifique 'evaluado y limpio', no 'no se miró'. Cierra el hito v0.5.0 (issue #1, facet B)."

## Why this matters (context, not a requirement)

For an authoring tool, **false confidence is a worse failure than noise**. DEBT-004 was, literally, a validator that was **asleep and green** for the entire `v0.4` line: `focalization` could not parse the narrative-voice declaration, so it returned `[]`, which read as "focalization OK." Today three early `[]` returns mean "I had nothing to look at," yet they are indistinguishable from a legitimate clean run:

- `focalization` returns `[]` when there is no constitution, no parseable voice declaration, the voice is still an unanswered `[PENDING: …]` placeholder, or a declaration is present but names no grammatical person — four distinct "could not look" paths.
- `setting_continuity` produces nothing to inspect when the manuscript is empty. `character_presence` is subtler: an empty manuscript still makes it emit `error`-level orphan findings (every defined character is then unmentioned), so it has truly "nothing to look at" only when *both* its inputs are empty — no prose and no roster.

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
4. **Given** a constitution that declares a narrative voice naming no grammatical person (e.g. `- **Voz narrativa**: narrador omnisciente`, neither first nor third), **When** `validate` runs, **Then** `focalization` is reported not-evaluated with a reason naming the unresolved grammatical person — its person-based rules cannot run, so it never reads as green.

---

### User Story 2 - Validators that had nothing to inspect say so, without ever hiding a finding (Priority: P1)

An author with an empty (or not-yet-written) manuscript runs `validate`. The prose-scanning validators must declare **not-evaluated** when (and only when) they genuinely had no input to look at — never by suppressing a finding they can still produce. Two validators, two honest triggers:

- `setting_continuity`'s only input is manuscript prose (it scans descriptors line by line); an empty manuscript means it has nothing to read, so it reports **not-evaluated** ("the manuscript is empty").
- `character_presence` has **two** inputs/directions: bible roster → manuscript (orphan check) and manuscript prose → bible (unknown-mention check). With an empty manuscript but a **non-empty roster** it still fully evaluates — it emits its existing `error`-level orphan findings ("a defined character is never mentioned"). It is therefore **not-evaluated only when it has no input for either direction**: no manuscript prose **and** an empty roster. An empty manuscript alone keeps it **evaluated**.

**Why this priority**: It is the second half of the same class. But the trigger must be derived from each validator's real preconditions — declaring `character_presence` not-evaluated on an empty manuscript would *suppress its error-level orphan findings and weaken the gate*, which is the very false-confidence failure this iteration exists to close (FR-004/FR-012).

**Independent Test**: (a) Run `validate` on a fixture with a populated bible (characters + settings) and an empty manuscript directory; assert `setting_continuity` appears in the not-evaluated channel with the empty-manuscript reason, **and** `character_presence` is reported **evaluated**, still emitting its orphan `error` findings byte-for-byte unchanged. (b) Run `validate` on an empty project (no roster, no prose); assert `character_presence` appears in the not-evaluated channel with the no-inputs reason. Neither run is reported as fully clean.

**Acceptance Scenarios**:

1. **Given** a project with a populated bible and an empty manuscript directory, **When** `validate` runs, **Then** `setting_continuity` is reported not-evaluated with an empty-manuscript reason, **and** `character_presence` is reported **evaluated**, still producing its existing orphan `error` findings unchanged.
2. **Given** a project with neither a bible character roster nor manuscript prose, **When** `validate` runs, **Then** `character_presence` is reported not-evaluated with a no-inputs reason (nothing to cross-check in either direction).
3. **Given** a project with manuscript prose present, **When** `validate` runs, **Then** both validators evaluate normally and any existing findings are produced **byte-for-byte unchanged** from today.

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
- **The verdict is whole-validator, never per-sub-check**: a validator is either evaluated (it ran its checks and returns its findings, possibly empty) or not-evaluated (it had no input for **any** of its checks). There is no partial / per-sub-check not-evaluated state — that would let a validator be simultaneously "evaluated with findings" and "not-evaluated," which the contract forbids. Consequence (resolved here, not deferred to planning): if even one of a validator's checks can run, the validator is **evaluated**. `character_presence` with a non-empty roster can run its orphan check even against an empty manuscript, so it is **evaluated** and emits those orphan findings; it is not-evaluated only when *both* directions lack input (no prose **and** empty roster). This is the rule that keeps an empty manuscript from suppressing `character_presence`'s `error`-level orphan findings (FR-009/FR-012).
- **A custom user validator** (loaded from `.bookwright/validators/*.py`) that still returns a plain `list[Violation]`: it MUST keep working and be treated as **evaluated** (backward compatible), never as not-evaluated.
- **The gate**: a run consisting solely of not-evaluated validators (no `error` findings) does **not** fail CI — not-evaluated is not a finding — yet it is **never** reported as a clean pass either.
- **Determinism**: the not-evaluated channel is emitted in a fixed, deterministic order (e.g. by validator name), like every other channel, so the report is byte-identical across runs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The validator contract (`validation/base.py`, design § 13.1) MUST be extended so a validator can declare, per run, that it **did-not-evaluate(reason)** in addition to (or instead of) its `Violation` list. The mechanism MUST keep a custom validator that returns a bare `list[Violation]` working unchanged and read as **evaluated** (FR-014), and MUST NOT leave the runner permanently sniffing the return type or carrying a dual-shape return contract as a justified smell (zero-debt doctrine §3 — eliminate the cause, do not contain it); if planning finds no mechanism that avoids that residue, it is recorded in `DEBT.md` with justification, never shipped silently. `bookwright-design.md § 13.1` MUST be updated to the new contract **before** the code diverges (plan § 7.3).
- **FR-002**: A not-evaluated result MUST carry the validator's name and a human-readable reason (e.g. "the constitution does not declare a narrative voice", "the narrative-voice declaration is still unanswered (`[PENDING]`)", "the manuscript is empty").
- **FR-003**: A validator that examined its inputs and found nothing MUST remain **evaluated with zero findings** (a legitimate green) — distinct from not-evaluated.
- **FR-004**: The new state MUST be **additive** and MUST NOT change the CI gate: only `Violation`s of `error` severity continue to fail CI. A not-evaluated result is **not** a gate failure (it is not a finding) but MUST be visible and MUST NOT be counted as clean.
- **FR-005**: not-evaluated MUST be a channel **distinct from `errors[]`**. `errors[]` remains for validators that could not be loaded or that raised (`ValidatorError`); not-evaluated is for a validator that ran without error and consciously chose not to evaluate.
- **FR-006**: The shape of `Violation` and of `ValidatorError` MUST NOT change.
- **FR-007**: The `bookwright validate --json` envelope MUST gain a channel for not-evaluated results (validator name + reason), a sibling of `violations` / `errors`. The human (non-JSON) report MUST also surface not-evaluated validators, distinct from both findings and a clean pass.
- **FR-008**: `focalization` MUST migrate **every** path by which it currently returns no findings for lack of a usable narrative-voice declaration to the not-evaluated state — covering all four early-return causes, each with a distinct reason: (i) no constitution, (ii) no parseable voice declaration, (iii) a voice still in `[PENDING]` (reusing the iteration-039 prose-seam placeholder detection), and (iv) a declaration that is present but resolves **no grammatical person** (neither first nor third — `focalization`'s person-based rules cannot run). A constitution that declares a usable narrative person (first or third) remains **evaluated**. The enumeration MUST be exhaustive over `focalization`'s `validate` early-return condition so no "could not look" path keeps reading as green.
- **FR-009**: `setting_continuity` (whose sole input is manuscript prose) MUST report not-evaluated when the manuscript has no readable prose, and remain evaluated when prose is present. `character_presence` MUST report not-evaluated **only** when it has no input for either of its checks — no manuscript prose **and** an empty bible character roster. An empty manuscript with a non-empty roster MUST keep `character_presence` **evaluated**, emitting its existing `error`-level orphan findings byte-for-byte unchanged: an empty manuscript alone is a fully-evaluated state for it, never not-evaluated, because making it not-evaluated would suppress those error findings and weaken the gate (FR-004/FR-012).
- **FR-010**: `bookwright status` MUST reflect the not-evaluated validators in its derived state and, where an actionable remedy exists, in `next_actions` (e.g. activating `focalization` by declaring the narrative voice).
- **FR-011**: The skill resource(s) that read `bookwright status` at session start (e.g. `resources/commands/bookwright-research.md`) MUST surface the not-evaluated validators among the raw `state.validation` facts in their startup / "Próximos pasos" block — verifiable because `status`'s derived state exposes the not-evaluated dimension (FR-010) and the skill resource references it. The not-evaluated facts are read from `state.validation`, not from `next_actions[]` (which stays a between-skills handoff, per the existing skill contract).
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
- **SC-002**: "Clean / green" is defined by a single documented predicate over the `bookwright validate --json` envelope (its exact form — e.g. `status == "ok" AND the not-evaluated channel is empty` — pinned in planning). For **every** run whose not-evaluated channel is non-empty, that predicate evaluates to **False**; a run that is entirely not-evaluated never satisfies it. Measured by asserting the predicate directly against the envelope on a not-evaluated fixture, and asserting it stays True on an evaluated-and-clean fixture.
- **SC-003**: **Zero edits** to existing finding oracles: the existing test suite's `Violation` counts are unchanged (byte-for-byte finding parity); only the not-evaluated state is added.
- **SC-004**: `bookwright status` on a project with a not-evaluated `focalization` yields a `next_actions` step that names the concrete remedy (declare the narrative voice in the constitution to activate `focalization`).
- **SC-005**: All four gates pass and `mypy --strict` is clean on the changed code; every changed/new source file stays ≤ 500 lines.

## Assumptions

- **Predecessor merged**: iteration 039 (the single prose/structure seam, `io/prose.py` with `is_placeholder` and the cached `manuscript_view()` / `constitution_view()` accessors) is on `main`; this iteration reuses its placeholder detection rather than re-implementing it.
- **Per-validator preconditions**: each validator decides its own evaluated/not-evaluated verdict from its own inputs; the runner/report/status layers are generic and do not know any validator's preconditions. The per-validator predicates are **resolved in this spec** (FR-008 for `focalization`, FR-009 for `setting_continuity`/`character_presence`; the verdict is whole-validator, never per-sub-check) — planning settles only the plumbing mechanism (FR-001) and the channel key, not whether a finding may be suppressed.
- **Backward-compatible contract**: the Protocol change is designed so a validator returning a bare `list[Violation]` still type-checks and is read as evaluated, protecting user-authored custom validators.
- **JSON channel naming**: the not-evaluated channel is a new sibling key in the envelope and the status payload; its exact key name is fixed in planning/design, but it is additive (no existing key changes shape).
- **Scope of the migration set**: only the three validators the user named (`focalization`, `character_presence`, `setting_continuity`) migrate in this iteration. `temporal` and `factual_anchor` are graph-driven and are not part of the "surface could-not-look" class; they are not touched beyond conforming to the (backward-compatible) contract.
- **Milestone close**: after this iteration merges, `v0.5.0` is released **once** for both iterations 039 + 040 via the `bookwright-release` skill (bump `__version__` to `0.5.0`, CHANGELOG section, CLAUDE.md / design status edits, release commit, annotated tag). The release itself is a separate manual step, not part of this iteration's code.

## Out of Scope

- The **surface-coupling seam** (iteration 039) — already merged; this iteration depends on it but does not re-open it.
- **LLM semantic judgment** for validators (issue #1, move 3) — parked in the demand-pulled horizon, activated only when a concrete heuristic is measured insufficient.
- **Adding new validators** — the validator roster is unchanged; this iteration only enriches the result contract of existing validators.
