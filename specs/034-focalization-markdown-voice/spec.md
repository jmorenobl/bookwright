# Feature Specification: `focalization` tolerates markdown-prefixed voice declaration

**Feature Branch**: `034-focalization-markdown-voice`

**Created**: 2026-06-21

**Status**: Draft

**Input**: User description: "Necesidad: el validador `focalization` no reconoce la declaración de voz narrativa cuando viene con prefijos markdown, que es justo el formato que la plantilla de constitución del scaffold genera. … Queremos que `focalization` tolere los prefijos markdown habituales delante de la etiqueta «Voz narrativa»/«Narrative voice» … sin cambiar ninguna otra regla del validador. (DEBT-004)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The scaffold's own narrative-voice declaration wakes the validator (Priority: P1)

An author runs `bookwright init`, opens the generated `bible/constitution.md`, and fills
in the voice line exactly as the scaffold lays it out — a markdown bullet with the label in
bold: `- **Voz narrativa**: Tercera persona limitada, centrada en X`. They then write a few
chapters and run `bookwright validate`. The `focalization` validator reads that declaration,
infers the declared grammatical person (and focal character, if named), and reports any
prose that breaks it (first-person markers outside dialogue, head-hopping under
third-person-limited).

**Why this priority**: This is the entire defect. Today the validator silently returns zero
findings against the exact format its own scaffold emits, so it is dead for every author who
fills in the constitution as generated. Restoring this single behavior is the whole point of
the iteration; without it there is nothing to ship.

**Independent Test**: Author a constitution whose voice line is the scaffold's exact shape
(`- **Voz narrativa**: tercera persona …`) plus a manuscript with a first-person break, run
`focalization`, and confirm it now produces the expected finding(s) where before it produced
none.

**Acceptance Scenarios**:

1. **Given** a constitution containing `- **Voz narrativa**: Tercera persona limitada, centrada en X`, **When** `focalization` parses it, **Then** it reads person=third, limited=true, and focal=X — identical to the bare `Voz narrativa: …` form.
2. **Given** that same constitution and a manuscript line with a first-person marker outside dialogue, **When** `focalization` runs, **Then** it emits the first-person break finding (the validator is awake).
3. **Given** the English scaffold shape `- **Narrative voice**: third person limited, focused on X`, **When** `focalization` parses it, **Then** it behaves equivalently to the Spanish form.

---

### User Story 2 - Template and parser stay bound so they cannot silently diverge again (Priority: P1)

The defect exists because the constitution template and the validator's declaration parser
drifted apart with no test tying them together. A test must read the **exact** declaration
line the scaffold ships and prove the parser accepts it, so any future edit to either side
that breaks the contract fails CI immediately.

**Why this priority**: A point fix to the regex without binding the two artifacts would let
the same class of silent breakage recur on the next template tweak. The bound test is what
makes this a durable fix rather than a patch.

**Independent Test**: A test loads the narrative-voice line from the packaged scaffold
constitution template and asserts the parser extracts a non-empty declaration from it; mutate
the template's voice-line shape and the test fails.

**Acceptance Scenarios**:

1. **Given** the packaged scaffold constitution template, **When** a test feeds its rendered narrative-voice line to the parser, **Then** the parser returns a parsed declaration (not "no declaration").
2. **Given** a future change that makes the template's voice line unparseable, **When** the suite runs, **Then** the bound test fails (the contract is enforced, not aspirational).

---

### User Story 3 - The no-declaration edge case stays intact (Priority: P2)

When a constitution genuinely has no narrative-voice declaration, `focalization` must keep
returning zero findings. Loosening the parser to tolerate markdown prefixes must not turn
prose that merely mentions "voz narrativa" elsewhere, or omits the declaration entirely, into
a false positive.

**Why this priority**: Preserving the documented edge case (no parsable declaration → zero
findings) is a correctness guarantee that the loosening could plausibly erode; it must be
re-proven, but it is a guardrail on the P1 change rather than new behavior.

**Acceptance Scenarios**:

1. **Given** a constitution with no narrative-voice declaration line, **When** `focalization` runs, **Then** it returns zero findings (unchanged).
2. **Given** a constitution whose voice line is markdown-prefixed but declares neither first nor third person, **When** `focalization` runs, **Then** it returns zero findings (person is unknown, so no rule fires), as it does for the bare form today.

---

### Edge Cases

- **Bullet markers**: the parser tolerates `-`, `*`, `+`, and `>` as a line-leading list/quote marker before the label.
- **Emphasis markers**: the parser tolerates markdown emphasis (`*`, `**`, `_`) wrapping the label, e.g. `**Voz narrativa**`, `*Narrative voice*`, `_Voz narrativa_`, including the closing emphasis run before the colon (`**Voz narrativa**:`).
- **Combined prefix**: bullet + emphasis together — the scaffold's `- **Voz narrativa**: …` — parses.
- **Whitespace**: leading indentation and spaces between the marker and the label remain tolerated (as today).
- **Colon placement**: the colon may sit immediately after a closing emphasis run (`**Voz narrativa**:`) or after the bare label (`Voz narrativa:`).
- **No false widening**: the loosening only concerns markup *around* the recognized label "Voz narrativa" / "Narrative voice"; it does not introduce new label synonyms, and a line that does not contain that label still does not match.
- **First match wins**: if multiple candidate lines exist, the existing first-match behavior is preserved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `focalization` declaration parser MUST recognize the narrative-voice declaration when the label ("Voz narrativa" / "Narrative voice", case-insensitive, bilingual) is preceded by a single line-leading markdown list or blockquote marker drawn from `-`, `*`, `+`, `>` (optionally followed by whitespace).
- **FR-002**: The parser MUST recognize the declaration when the label is wrapped in markdown emphasis markers (`*`, `**`, `_`) on either side, with the colon permitted to follow the closing emphasis run.
- **FR-003**: The parser MUST recognize the scaffold's exact combined shape `- **Voz narrativa**: <body>` and extract the same declaration (person, limited flag, focal character) it would extract from the bare `Voz narrativa: <body>` form.
- **FR-004**: For the example `- **Voz narrativa**: Tercera persona limitada, centrada en X` (with X a named bible character), the parser MUST yield person=third, limited=true, focal=X.
- **FR-005**: When no narrative-voice declaration line is present (or the present line names no recognizable person), `focalization` MUST continue to return zero findings — the documented edge case is unchanged.
- **FR-006**: No other `focalization` rule, heuristic, or threshold MAY change: the first-person-outside-dialogue rule, the head-hopping/interiority rule, the pronoun and interiority lexicons, the dialogue-exemption prefixes, the bilingual person/limited keywords, and the one-finding-per-file behavior all stay exactly as they are.
- **FR-007**: A test MUST bind the scaffold constitution template to the parser by reading the template's actual narrative-voice line and asserting the parser accepts it, so the template and parser cannot silently diverge again.
- **FR-008**: When waking `focalization` changes the observed behavior of any existing fixture (notably `tiny-historical`, whose constitution uses the markdown-prefixed form), that fixture's oracle / expected output MUST be reconciled honestly to the validator's real, awake behavior — not suppressed or pinned to the old dormant counts.
- **FR-009**: The `DEBT-004` entry MUST be removed from `DEBT.md` (git retains the history), per the project's debt-cancellation convention.
- **FR-010**: The change MUST be confined to prose-level validation logic and test/fixture/debt artifacts; it MUST NOT alter the GOLEM ontology, emit or change any graph triples, or touch frozen schema (Principle X) — there is no graph change.

### Key Entities *(include if feature involves data)*

- **Narrative-voice declaration**: the single line in `bible/constitution.md` that states the book's narrating person and (optionally) focal character. Its recognized surface forms now include the markdown-prefixed shapes the scaffold emits. Its parsed result carries: declared person (first/third/none), a limited flag, and a focal bible character (if named).
- **Scaffold constitution template**: the packaged source (`bible/constitution.md.j2`) that generates each project's constitution; its narrative-voice line is the canonical surface form the parser must accept, and the binding test's fixture of truth.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An author who fills the generated constitution's voice line exactly as the scaffold lays it out gets a `focalization` validator that produces findings on voice-breaking prose — 0% silent self-deactivation for the scaffold format (currently 100%).
- **SC-002**: Both the Spanish (`- **Voz narrativa**: …`) and English (`- **Narrative voice**: …`) scaffold shapes parse to the same declaration as their bare equivalents.
- **SC-003**: A constitution with no narrative-voice declaration still yields exactly zero `focalization` findings (edge case preserved).
- **SC-004**: A single test reads the live scaffold template's voice line and asserts the parser accepts it; deliberately breaking the template's voice-line shape makes that test fail.
- **SC-005**: The full suite is green and all four gates pass (`ruff check`, `ruff format --check`, `mypy --strict`, `pytest` with ≥80% coverage), with every fixture oracle reconciled to the awake validator's real output.
- **SC-006**: `DEBT.md` no longer contains a `DEBT-004` entry.

## Assumptions

- The fix is achieved by loosening the declaration-recognition pattern (or normalizing the candidate line before matching) so common markdown prefixes/emphasis around the label are tolerated; the person/limited/focal extraction that runs on the declaration body is unchanged.
- "Common markdown prefixes" is scoped to the bullet markers `-`, `*`, `+`, `>` and the emphasis markers `*`, `**`, `_` named in the request; nested/exotic markup beyond these is out of scope and not required to parse.
- The `tiny-historical` fixture declares third-person-limited focused on a named character; waking `focalization` may add warning finding(s) over its manuscript, which will shift its project-wide `validation.counts` warning total in `expected-status.md`. The exact new count is determined during implementation by running the awake validator, and the oracle is updated to match honestly rather than the validator being tuned to preserve the old count.
- Other fixtures are checked for the same wake-up effect during implementation; any whose oracle/expectation shifts is reconciled the same honest way.
- No new label synonyms are introduced; only markup around the existing two labels is tolerated.

## Out of Scope *(do not reopen in clarify)*

- Changing any other `focalization` rule or its pronoun/interiority heuristics.
- Touching the frozen ontology (Principle X): no graph change — this is a validator over prose.
- The other dogfooding findings (DEBT-005 / DEBT-006): each is its own iteration (035 / 036).
