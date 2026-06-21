# Feature Specification: `focalization` treats an unanswered `[PENDING]` voice placeholder as no declaration

**Feature Branch**: `037-focalization-pending-placeholder`

**Created**: 2026-06-21

**Status**: Draft

**Input**: User description: "Un proyecto recién creado por `bookwright init`, con la constitución SIN rellenar, ya dispara avisos `focalization` de head-hopping contra TODOS los personajes en cuanto el manuscrito tiene un verbo de interioridad (pensó/supo/sintió/…). La causa: el placeholder por defecto de la plantilla de constitución es `- **Voz narrativa**: [PENDING: …(primera/tercera persona, omnisciente/limitada)?]`, cuyo TEXTO contiene literalmente «tercera persona» y «limitada»; el parser `_parse_declaration` lo acepta como una declaración real. Queremos que una declaración cuyo cuerpo sigue siendo un placeholder `[PENDING: …]` sin responder se trate como NO declaración (cero findings), sin cambiar ninguna otra regla del validador."

## Clarifications

### Session 2026-06-21

- Q: Eliminate the cause by rewording the constitution template (drop the trigger
  words "tercera persona"/"limitada") or by making the parser treat an unanswered
  `[PENDING]` body as no declaration? → A: Parser-level suppression. Rationale: the
  template prompt must keep naming the person/distance options to stay useful to the
  author; rewording only hides today's instance while the real cause — the parser
  accepting an unanswered prompt as data — stays latent and would re-trigger on any
  future placeholder mentioning a person. Suppressing at the parser eliminates the
  cause *class*, not the symptom (zero-debt doctrine §3 "eliminate the cause" / §4
  "debt is a class").
- Q: Should `[PENDING]` recognition become a shared, repo-wide token utility, or
  stay local to the `focalization` validator? → A: Local to `focalization.py`. A
  shared utility would be speculative plumbing for the other validators/sections
  this iteration explicitly does not touch (doctrine §2, scope discipline); the
  prose `references/pending-protocol.md` remains the single source of truth the
  local recognizer mirrors.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A freshly initialized project produces no spurious focalization warnings (Priority: P1)

An author runs `bookwright init`, gets the scaffolded `bible/constitution.md` with
its prompts still unanswered (every line is a `[PENDING: …]` token), and starts
drafting. As soon as a manuscript scene contains an interiority verb
(`pensó`, `supo`, `sintió`, `thought`, `felt`, `knew`, …) attached to a named
character, the `focalization` validator must stay silent — it has nothing to
check against, because the narrative voice has not been declared yet.

**Why this priority**: This is the entire defect. A brand-new project that the
author has not configured yet floods them with head-hopping warnings against
*every* character, training them to ignore the validator before they have written
a single real declaration. The validator's own docstring already promises the
correct behavior ("No parsable declaration → zero findings"); the placeholder
silently defeats that promise.

**Independent Test**: Start from the exact scaffold constitution
(`src/bookwright/resources/project/bible/constitution.md.j2`, placeholder
untouched) plus a manuscript scene containing an interiority verb and a named
character; run the `focalization` validator; assert it returns zero findings.

**Acceptance Scenarios**:

1. **Given** a project whose constitution still carries the scaffold line
   `- **Voz narrativa**: [PENDING: ¿Quién narra y desde qué distancia
   (primera/tercera persona, omnisciente/limitada)?]` and a manuscript scene
   `Halia pensó que el faro callaba.`, **When** `focalization` runs, **Then** it
   produces zero findings.
2. **Given** the same unanswered constitution and a manuscript scene containing a
   first-person marker outside dialogue (`Yo no entendía nada.`), **When**
   `focalization` runs, **Then** it produces zero findings (no person was
   declared, so neither the first-person nor the head-hopping rule may fire).

---

### User Story 2 - Answering the voice prompt wakes the validator (Priority: P1)

Once the author replaces the `[PENDING: …]` placeholder with a real narrative
voice (e.g. `Tercera persona limitada, focalizada en Halia`), the validator must
behave exactly as it does today: it parses the declared person, the limited
flag, and the focal character, and resumes flagging first-person breaks and
head-hopping.

**Why this priority**: The fix must not over-correct. The validator is only
meant to go quiet while the voice is *unanswered*; the moment a real declaration
exists, the guarantee returns. Without this scenario the fix could silence a real,
authored declaration.

**Independent Test**: Take the same project, replace only the placeholder body
with a real third-person-limited voice focalized on a character, keep the same
head-hopping manuscript, run `focalization`, and assert it produces the expected
head-hopping finding.

**Acceptance Scenarios**:

1. **Given** a constitution declaring `- **Voz narrativa**: Tercera persona
   limitada, focalizada en Halia` and a manuscript where a *non-focal* character
   is given an interiority verb, **When** `focalization` runs, **Then** it emits
   the head-hopping warning for that non-focal character (identical to current
   behavior).
2. **Given** any of the existing focalization fixtures (bare declaration,
   English declaration, markdown-prefixed declaration from iteration 034),
   **When** `focalization` runs, **Then** the findings are byte-identical to the
   pre-fix behavior (no regression).

---

### Edge Cases

- **Placeholder is only part of the body**: a body like `Tercera persona
  [PENDING: ¿focalizada en quién?]` mixes a real answer with a leftover prompt.
  The body is *not* solely an unanswered placeholder, so the declaration is
  treated as real (the author has begun answering) — only a body that is
  *entirely* an unanswered `[PENDING: …]` token is suppressed.
- **Bilingual label**: the suppression applies whether the declaration uses the
  Spanish `Voz narrativa` or the English `Narrative voice` label, since both feed
  the same parser.
- **Markdown-prefixed placeholder**: the scaffold emits the line as
  `- **Voz narrativa**: [PENDING: …]`; the markdown normalization from iteration
  034 still runs first, so the placeholder check sees the already-stripped body.
- **Whitespace / casing around the token**: a body of `  [pending: …]  ` (leading
  / trailing whitespace, any casing of the `PENDING` keyword) is still recognized
  as an unanswered placeholder.
- **No voice line at all**: unchanged — already returns zero findings.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When the parsed body of the narrative-voice declaration is *solely*
  an unanswered `[PENDING: …]` placeholder token, the validator MUST treat the
  declaration as absent — i.e. produce zero `focalization` findings, exactly as
  when no `Voz narrativa` / `Narrative voice` line exists at all.
- **FR-002**: The placeholder recognition MUST match the canonical marker defined
  in `src/bookwright/resources/commands/references/pending-protocol.md` (the single
  source of truth for the token): a body that is a single `[PENDING: …]` token
  (square-bracketed, keyword `PENDING`, optional `: …` continuation), allowing
  surrounding whitespace, and MUST NOT match a body that merely *contains* a
  `[PENDING]` fragment alongside real declared text. The protocol mandates the
  keyword in uppercase English; recognition is nonetheless case-insensitive on
  `PENDING`, deliberately matching iteration 034's tolerance philosophy — leniency
  here only ever suppresses an *un*answered body, never a real one, so it is the
  conservative direction.
- **FR-003**: A body containing a real declaration (any non-placeholder text, in
  Spanish or English) MUST continue to parse exactly as today — same declared
  person, same `limited` flag, same focal character — with no regression on the
  existing fixtures, including the markdown-prefixed declaration handled by
  iteration 034.
- **FR-004**: The suppression MUST apply identically to the Spanish
  (`Voz narrativa`) and English (`Narrative voice`) declaration labels.
- **FR-005**: The placeholder check MUST run on the same already-normalized
  (markdown-stripped) declaration body that iteration 034 produces, so the
  scaffold's markdown-prefixed bullet form is recognized.
- **FR-006**: No other `focalization` rule or heuristic (first-person pronoun
  detection, interiority-verb detection, markdown normalization, focal-character
  resolution) may change behavior. The only new behavior is suppression of an
  unanswered placeholder body.
- **FR-007**: A regression test MUST start from the exact scaffold constitution
  (`src/bookwright/resources/project/bible/constitution.md.j2`, placeholder
  intact) plus a manuscript containing an interiority verb on a named character,
  and assert zero `focalization` findings.
- **FR-008**: A complementary test MUST confirm that replacing the placeholder
  with a real voice wakes the validator (the previously-suppressed finding now
  fires).
- **FR-009**: The DEBT-007 entry MUST be removed from `DEBT.md` (git retains the
  history), per the repo's debt-cancellation convention.
- **FR-010**: The frozen GOLEM ontology (Constitution X) MUST NOT change — this is
  a prose-level validator that never touches the graph.

### Key Entities *(include if feature involves data)*

- **Narrative-voice declaration**: the single `Voz narrativa` / `Narrative voice`
  line read from the constitution. It yields a parsed declaration (declared
  person, `limited` flag, focal character) or, after this change, *nothing* when
  its body is still an unanswered `[PENDING: …]` placeholder.
- **Scaffold constitution placeholder**: the default template body
  `[PENDING: ¿Quién narra y desde qué distancia (primera/tercera persona,
  omnisciente/limitada)?]` whose literal text incidentally contains "tercera
  persona" and "limitada" — the root cause of the false positives.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A project initialized from the unmodified scaffold, with a
  manuscript containing one or more interiority verbs and named characters,
  produces exactly **0** `focalization` findings.
- **SC-002**: After the author replaces the placeholder with a real declaration,
  the validator produces the **same** findings it produces today for that
  declaration (100% parity on the existing focalization fixtures — no finding
  added, none removed).
- **SC-003**: All four quality gates pass: `ruff check`, `ruff format --check`,
  `mypy --strict`, and `pytest` at ≥ 80 % coverage.
- **SC-004**: `DEBT.md` no longer contains a DEBT-007 entry, and no new debt entry
  is introduced by this change.

## Assumptions

- The `[PENDING]` token is the single, canonical "unanswered prompt" marker across
  every scaffolded plain-text file in the project — its shape and rules are fixed
  once in `references/pending-protocol.md`, and the constitution template's own
  guidance instructs authors to "Responde cada prompt `[PENDING: …]`". Keying
  suppression on it is therefore faithful to an established repo-wide convention,
  not a new concept the validator invents.
- "Solely a placeholder" is judged on the parsed declaration *body* (the text after
  the `:` colon), after iteration 034's markdown normalization — not on the raw
  line.
- Mixed bodies (a real answer with a leftover `[PENDING]` fragment) are treated as
  real declarations; suppressing them would risk silencing partially-authored
  voices, which is out of scope and against the "wake on real declaration" intent.
- The fix lives at the parser, not in the template: the placeholder must keep naming
  the person/distance options to remain useful, so rewording it would degrade the
  scaffold while leaving the parser bug (accepting an unanswered prompt as a
  declaration) latent. Suppressing an unanswered body at parse time removes the
  cause class once, for any present or future person-mentioning placeholder.

## Out of Scope

- Changing any other `focalization` rule or its pronoun / interiority / markdown
  heuristics (iteration 034 already handled the markdown prefix).
- Reading the point-of-view character from a scene's front-matter (`pov:`); the
  focal character is declared in the constitution by design — not this iteration.
- Touching the frozen ontology (Constitution X); this is a prose validator that
  does not touch the graph.
- Generalizing `[PENDING]` suppression to other validators or constitution
  sections — this iteration scopes the recognizer to the narrative-voice
  declaration. The `[PENDING]` recognizer is therefore a local constant in
  `focalization.py`, not a new shared/repo-wide token module (which would be
  speculative plumbing); `references/pending-protocol.md` stays the prose source of
  truth it mirrors.
