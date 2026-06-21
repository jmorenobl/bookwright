# Phase 0 Research: `focalization` markdown-prefixed voice declaration

All Technical Context items are concrete (no NEEDS CLARIFICATION); the single
clarification (emphasis-balance) is already resolved in `spec.md` §Clarifications.
This file records the design decisions that the plan depends on.

## D1 — Normalize the line, don't grow the regex

- **Decision**: Strip markdown prefixes from a candidate line *before* applying
  the label-and-body pattern, rather than embedding optional bullet/emphasis
  groups inside the single `_DECLARATION` regex.
- **Rationale**: The spec offers both options ("amplía `_DECLARATION` … o, más
  robusto, normaliza la línea"). Normalization is the more robust path the spec
  itself prefers: a regex that must tolerate an optional leading marker, optional
  whitespace, optional opening emphasis run, the label, optional closing emphasis
  run, and the colon — *independently* (no balance, per the clarification) —
  becomes hard to read and easy to break on the next tweak, which is exactly the
  fragility DEBT-004 is about. A small normalizer (`lstrip` a single
  bullet/blockquote marker + whitespace, then strip the named emphasis markers
  `**`/`*`/`_` from the label region) keeps the recognition obvious and keeps the
  *body* untouched so person/limited/focal extraction is provably identical.
- **Mechanism**: Iterate candidate lines (the search must still find the **first**
  matching line — FR "first match wins"). For each line: (1) drop one optional
  line-leading marker from `[-*+>]` plus following whitespace; (2) strip the
  emphasis markers independently from around the `Voz narrativa`/`Narrative voice`
  label; (3) match the residual against a label-anchored body pattern. The colon
  may sit immediately after the closing emphasis run (`**Voz narrativa**:`) or
  after the bare label — handled by stripping emphasis before the `\s*:\s*` step.
- **Alternatives considered**: (a) One mega-regex with optional groups —
  rejected as the fragile path the debt warns against. (b) A full markdown
  parser — rejected (heavy dependency, Constitution II; absurd for one line).

## D2 — Independent (unbalanced) emphasis, no balance guard

- **Decision**: Strip each named emphasis marker run independently on each side
  of the label; do **not** verify the opening and closing runs match.
- **Rationale**: Resolved in `spec.md` §Clarifications and FR-002. A balance
  check is a guard with zero author benefit and would risk rejecting a valid
  scaffold-adjacent edit — a direct violation of the zero-debt doctrine §3
  ("delete the cause, don't add a guard"). Single-sided forms parsing is a
  harmless, intended consequence, not a feature to police.

## D3 — Scope is markup *around* the existing label only

- **Decision**: Tolerate only the named markers (`-`, `*`, `+`, `>`, and `*`,
  `**`, `_`) around the two existing labels. Introduce **no** new label synonym;
  a line not containing `Voz narrativa`/`Narrative voice` still does not match.
- **Rationale**: FR-006 / "No false widening" / SC edge cases. The defect is
  purely surface markup; widening the label set would be unrequested scope and a
  new false-positive surface. The body grammar (`_THIRD`/`_FIRST`/`_LIMITED`,
  the focal-name scan) is frozen — FR-004's `person=third, limited=true,
  focal=X` must be produced unchanged.

## D4 — Bind the template to the parser with a live-template test

- **Decision**: Add a test that reads the packaged scaffold template
  `bookwright/resources/project/bible/constitution.md.j2` via
  `importlib.resources`, extracts its narrative-voice line, and asserts the
  parser returns a **non-None** `_Declaration` (the line is recognized) — not a
  rendered-Jinja round trip, just the raw template line.
- **Rationale**: FR-007 / US2. The template's body is the placeholder
  `[PENDING: …]`, which names no person, so the parsed `person` is `None`; the
  binding contract is therefore *recognition* (line matches), not person
  inference. Reading the template line directly (it is static text, not behind a
  Jinja variable) is sufficient and keeps the test independent of the Jinja
  render path. Mutating the template's voice-line shape must fail this test —
  that is the durable anti-drift guarantee.
- **Alternatives considered**: Rendering the `.j2` through Jinja first —
  rejected as unnecessary indirection; the voice line carries no template
  variables, so the raw line is the canonical surface form. A fixture that merely
  *replicates* the format — allowed by the spec as a fallback, but reading the
  **live** template is strictly stronger (it actually binds the shipped artifact),
  so we prefer it.

## D5 — Fixture-suite reconciliation (FR-008): determine the real awake counts

- **Decision**: After the parser change, run the awake validator over each
  voice-bearing fixture and reconcile every asserted/prose oracle to its **real**
  output — never back-fit to the old dormant `{error:1, warning:6}`.
- **Per-fixture analysis** (from `spec.md` Assumptions, verified against the
  fixtures during research):
  - `tiny-historical` — `- **Voz narrativa**: Tercera persona limitada, centrada
    en Elena Vidal.` → person=third, limited=true, focal="Elena Vidal". This is
    the **only** oracle that shifts: `expected-status.md`'s
    `validation.counts` (today `{error:1, warning:6, info:0}`) gains the
    focalization warnings (first-person breaks and/or head-hopping that the
    manuscript contains). The **exact** new `warning` total is read from the awake
    validator at implementation time and written into `expected-status.md` (and
    any prose count in its comments reconciled), with `test_orchestration_
    workflow.py` then green. `error` stays 1 (focalization emits only warnings).
  - `tiny-novel` — third-person-limited, focal "Ada Reyes"; no oracle file, only
    `test_fixture_validates_clean` (exit 0, warnings allowed). New warnings need
    no count reconciliation, but `validate` MUST still exit 0 — verify the awake
    validator emits only `warning` severity (it does, by construction).
  - `tiny-quest` — third-person-limited, focal "Liria"; `expected-narrative.md` /
    `test_narrative_workflow.py` assertions are scoped to
    `validator == "narrative_structure"`, so focalization warnings touch no
    asserted value. Verify scope holds.
  - `tiny-essay` (`Primera persona…`) and `tiny-memoir` (`Primera persona…`) —
    the awakened parser reads person=first, for which `focalization` fires no
    rule (only third-person rules exist), so they yield zero findings exactly as
    before. No oracle change; verify zero.
  - `tiny-historical/expected-findings.md` — read only for `factual_anchor`-scoped
    values by `test_research_workflow.py`; unaffected. If it states a project-wide
    count in prose, reconcile that prose honestly too.
- **Rationale**: FR-008 forbids suppressing the wake at any single point and
  requires the count be read from the validator, not pinned to the dormant value.
  The oracle is the *truth of the awake system*, so it follows the validator.

## D6 — No graph / ontology impact (Principle X)

- **Decision**: Confirmed no triple, class, IRI, or `.ttl` change. The validator
  emits `Violation`s with `triples=()`; the change is purely in line recognition.
- **Rationale**: FR-010 / Constitution X. `focalization` is a prose validator; it
  reads `constitution_text()` and manuscript text and produces warnings. Nothing
  in the GOLEM model or `golem.ttl` is involved.
