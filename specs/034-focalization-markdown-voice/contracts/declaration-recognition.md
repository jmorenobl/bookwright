# Contract: narrative-voice declaration recognition

The interface this iteration touches is the **parser-recognition contract** of
the `focalization` validator — what surface forms of the narrative-voice line are
recognized, and what each yields. It is exercised through the validator's public
`validate(...)` and (for unit precision) the module-internal `_parse_declaration`.

## Inputs

- `text`: the full `bible/constitution.md` content (plain text).
- `character_names`: the bible's character names (for focal-character matching).

## Recognized surface forms → parsed `_Declaration`

Let `B` be any declaration body (e.g. `Tercera persona limitada, centrada en X`).
For each row, the parser MUST return a `_Declaration` **equal** to the one parsed
from the bare canonical form `Voz narrativa: B`.

| # | Surface line                                   | Recognized | Parsed parity with bare form |
|---|------------------------------------------------|------------|------------------------------|
| C1 | `Voz narrativa: B` (canonical, today)         | yes        | — (reference)                |
| C2 | `- Voz narrativa: B`                           | yes        | equal                        |
| C3 | `* Voz narrativa: B`                           | yes        | equal                        |
| C4 | `+ Voz narrativa: B`                           | yes        | equal                        |
| C5 | `> Voz narrativa: B`                           | yes        | equal                        |
| C6 | `**Voz narrativa**: B`                          | yes        | equal                        |
| C7 | `*Voz narrativa*: B`                            | yes        | equal                        |
| C8 | `_Voz narrativa_: B`                            | yes        | equal                        |
| C9 | `- **Voz narrativa**: B` (scaffold shape, FR-003) | yes     | equal                        |
| C10 | `**Voz narrativa: B` (single-sided emphasis, FR-002) | yes  | equal                        |
| C11 | `- **Narrative voice**: B` (English scaffold)  | yes        | equal                        |
| C12 | `   - **Voz narrativa**: B` (indented)         | yes        | equal                        |

## Non-recognized / edge forms

| # | Surface line / situation                            | Result                         |
|---|-----------------------------------------------------|--------------------------------|
| N1 | No line contains the label                          | `None` (no declaration) → 0 findings |
| N2 | `Sin declaración de punto de vista.`                | `None` → 0 findings            |
| N3 | Recognized line whose body names no person (`[PENDING: …]`) | `_Declaration(person=None,…)` → 0 findings |
| N4 | A line merely *mentioning* "voz narrativa" mid-sentence with no colon-delimited body | not a declaration (no match) |

## Concrete value contract (FR-004)

Given `character_names` containing `Elena Vidal` and the line
`- **Voz narrativa**: Tercera persona limitada, centrada en Elena Vidal.`:

- `person == "third"`
- `limited is True`
- `focal == "Elena Vidal"`

## Behavioral guarantees (frozen — FR-006)

- Down-stream rule set, lexicons, dialogue-exemption prefixes, and
  one-finding-per-file behavior are unchanged.
- All emitted `Violation`s have `severity == warning` and `triples == ()`
  (no graph change, FR-010).
- First-match-wins ordering is preserved.

## Template-binding contract (FR-007)

The packaged scaffold template
`bookwright/resources/project/bible/constitution.md.j2` ships a voice line of
shape C9. A test reads that line from the live template and asserts the parser
returns a non-`None` `_Declaration` (recognition, per N3 the person may be
`None`). Changing the template's voice-line shape to an unparseable form MUST
fail this test.
