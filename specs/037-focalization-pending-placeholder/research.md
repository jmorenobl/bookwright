# Research: `focalization` `[PENDING]` placeholder suppression

All NEEDS CLARIFICATION are resolved (the spec carries two recorded clarifications;
the technical hint fixes the implementation site). The decisions below settle the
remaining design micro-choices.

## D1 — Where the guard lives

- **Decision**: Inside `_parse_declaration`, immediately after
  `body = match.group("body")` and **before** computing `person` / `limited` /
  `focal`. Return `None` (the exact value the function already returns when
  `_DECLARATION.match` finds nothing).
- **Rationale**: `_parse_declaration` is the single choke point that turns a
  constitution line into a `_Declaration | None`. `validate()` already short-circuits
  on `declaration is None or declaration.person is None` (line 72), so returning
  `None` reuses the established "no declaration → zero findings" path verbatim — no
  new branch in `validate()`, no new state. The technical hint pins this site
  exactly.
- **Alternatives considered**: (a) Guarding in `validate()` after the parse —
  rejected: it would need to re-inspect the body the parser already discarded, and
  duplicate the placeholder knowledge outside the parser. (b) Rewording the
  constitution template to drop "tercera persona"/"limitada" — rejected by spec
  clarification: the prompt must keep naming the person/distance options to stay
  useful, and rewording hides today's instance while leaving the parser bug latent
  for any future person-mentioning placeholder (zero-debt doctrine §3 "eliminate the
  cause" / §4 "debt is a class").

## D2 — The recognizer regex (what counts as "solely a placeholder")

- **Decision**: A module-level constant
  `_PENDING_ONLY = re.compile(r"(?i)^\s*\[pending\b[^\]]*\]\s*$")`, guarded as
  `if _PENDING_ONLY.match(body): return None`.
- **Rationale**: FR-002 requires the body to be *solely* a single `[PENDING: …]`
  token — square-bracketed, keyword `PENDING`, optional `: …` continuation,
  surrounding whitespace tolerated — and **MUST NOT** match a body that merely
  *contains* a `[PENDING]` fragment alongside real declared text. The regex anchors
  **both** ends (`^…$`): `\[pending\b` requires the open bracket + the keyword as a
  whole word at the start; `[^\]]*\]` consumes the single token's interior up to its
  closing bracket; `\s*$` forbids any trailing declared text. `(?i)` makes the
  keyword case-insensitive (FR-002: the `pending-protocol.md` mandates uppercase
  English, but leniency here can only ever suppress an *un*answered body, never a
  real one — the conservative direction, matching iteration 034's tolerance
  philosophy). Verified empirically against the live scaffold body and the edge
  cases below.
- **Why stricter than the illustrative hint**: the technical hint offered
  `^\s*\[PENDING\b` "p. ej." (for example) — start-anchored only. That would also
  suppress a body like `[PENDING: …] tercera persona` (real text *after* the token),
  contradicting FR-002's "solely" and the edge-case rule that any real declared text
  alongside the fragment makes the body real. The full `^…$` anchor is the faithful
  reading of "solely"; the hint's example was illustrative, the spec is the
  authority.
- **Alternatives considered**: (a) `^\s*\[pending\b` (start-anchored, per the hint
  example) — rejected as above (over-suppresses trailing-text bodies). (b) An exact
  string compare against the scaffold's literal placeholder — rejected: brittle (any
  edit to the question text would silently re-break suppression) and fails the
  whitespace/casing edge cases. (c) A shared repo-wide `[PENDING]` token module —
  rejected by spec clarification as speculative plumbing for validators this
  iteration does not touch; `references/pending-protocol.md` stays the prose source
  of truth this local constant mirrors.

### Verified recognizer behavior (empirical)

| Body (post markdown-normalization) | `_PENDING_ONLY.match` | Treated as |
|---|---|---|
| `[PENDING: ¿Quién narra … (primera/tercera persona, omnisciente/limitada)?]` (live scaffold) | ✅ match | no declaration → `None` |
| `  [pending: ¿x?]  ` (whitespace + lowercase keyword) | ✅ match | no declaration → `None` |
| `Tercera persona [PENDING: ¿focalizada en quién?]` (real text before token) | ✗ no match | real declaration |
| `Tercera persona limitada, focalizada en Halia` (real voice) | ✗ no match | real declaration |

## D3 — Interaction with iteration 034 markdown normalization

- **Decision**: The guard runs on `match.group("body")`, which is already produced
  from the markdown-normalized line (`_normalize_declaration_line` runs inside the
  `_parse_declaration` generator that feeds `_DECLARATION.match`). No ordering change.
- **Rationale**: FR-005 requires the placeholder check to see the *stripped* body so
  the scaffold's `- **Voz narrativa**: [PENDING: …]` bullet/emphasis form is
  recognized. Because normalization only strips markup *around the label* and never
  the body (034's invariant), the body the guard inspects is exactly
  `[PENDING: …]`. Confirmed: the live scaffold line's extracted body is
  `[PENDING: ¿Quién narra…?]`, which the regex matches.

## D4 — The existing `test_template_binding` assertion must flip (no regression escape)

- **Decision**: Update `tests/validation/test_focalization.py::test_template_binding`
  so it asserts the live scaffold voice line now parses to `None` (was: `is not
  None`). Keep its anti-drift purpose and its "exactly one narrative-voice line"
  guard.
- **Rationale**: Iteration 034 introduced this test asserting the placeholder line
  is *recognized* (non-`None`) but names no person, relying on `validate()` to drop
  it. This iteration changes the contract: an unanswered placeholder body now yields
  `None` at the parser. Leaving the old `is not None` assertion in place would turn
  the gate red (SC-003). The flip is the intended behavior change, and the test
  still binds template↔parser: mangling the template's voice line (removing the
  colon, breaking the label, or — newly — replacing the placeholder with a real
  voice) changes the parse result and fails the test, which is the durable
  anti-divergence guarantee the spec wants (FR-007 framing).
- **Alternatives considered**: deleting `test_template_binding` and relying only on
  the new end-to-end test — rejected: the unit-level template-line binding catches a
  template edit even when no manuscript fixture exercises it; keeping both layers is
  cheap and strictly stronger.

## D5 — Why the existing `test_pending_markdown_declaration_yields_nothing` is insufficient (and what the new FR-007 test must do)

- **Decision**: Add a new test that reads the **exact live scaffold constitution**
  (`importlib.resources` → `constitution.md.j2`, placeholder intact) as the project
  constitution, plus a manuscript with an interiority verb on a named character, and
  asserts **zero** `focalization` findings (FR-007 / SC-001).
- **Rationale**: the existing test (line 175) uses a hand-written
  `[PENDING: ¿quién narra?]` body that contains **no** person word, so it passes
  today merely because `person=None` — it does **not** reproduce DEBT-007. The real
  defect needs the *actual* scaffold body, whose text contains "tercera persona" and
  "limitada" and therefore drives `person="third", limited=True`. The new test must
  feed the real template body and use an interiority verb (head-hopping path), which
  is where the flood was observed. This ties template↔parser end-to-end through
  `validate()`, not just at the parse unit. (The old test stays — its assertion still
  holds and it covers the no-person path; its comment is refreshed to note the body
  is now suppressed as a placeholder rather than "names no person".)
- **Complement (FR-008 / SC-002)**: a second new test replaces only the placeholder
  body with a real third-person-limited voice focalized on a character, keeps a
  head-hopping manuscript, and asserts the previously-suppressed finding now fires —
  proving the fix does not over-correct (the validator wakes on a real declaration).

## D6 — Test fixture mechanics

- **Decision**: Reuse the existing `write_project` / `load_context` /
  `project_root` helpers from `tests/validation/conftest.py` (already imported by
  this test file). Load the scaffold template text via
  `importlib.resources.files("bookwright.resources.project.bible").joinpath("constitution.md.j2").read_text(...)`
  (the same accessor `test_template_binding` already uses) and pass it as the
  `constitution=` argument to `write_project`.
- **Rationale**: matches the file's established conventions (no new fixture
  machinery), and binds the test to the *live packaged template* rather than a copy,
  so a template edit is caught. The `.j2` is plain text with no Jinja in the voice
  section, so reading it raw is faithful to what `init` scaffolds for that line.
- **Note**: `write_project` writes the constitution under `bible/constitution.md`;
  `ValidationContext.constitution_text()` reads it back. Character names come from the
  `characters=` argument (e.g. `["Halia"]`), matching the existing head-hopping test.

## D7 — DEBT-007 removal

- **Decision**: Delete the entire `### DEBT-007 …` block from `DEBT.md`'s "Deuda
  abierta" section (FR-009), leaving the surrounding dogfooding-closure prose intact
  and the section header in place (it then reads as having no open entries, like the
  "Deuda aceptada" section's `_Ninguna por ahora._`).
- **Rationale**: the repo convention removes a debt entry when resolved (git keeps
  history); only `aceptada` (won't-fix) debt stays recorded. DEBT-007 is resolved by
  this iteration, so it is deleted, not archived.
- **Open question — empty "Deuda abierta" section wording**: after removal the
  "## Deuda abierta" section has no entries. Tasks should add a short
  `_Ninguna por ahora._` placeholder under it (mirroring the "Deuda aceptada"
  section) so the section does not read as truncated. This is a cosmetic
  doc-consistency touch, not a behavior change.
