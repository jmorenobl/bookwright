# Contract: `_parse_declaration` placeholder recognition

The internal contract this iteration changes. `_parse_declaration` is not a public
CLI surface (no `--json` envelope), but it is the single seam every focalization
finding flows through, so its recognition rules are pinned here as the contract the
tests assert against.

## Signature (unchanged)

```python
def _parse_declaration(text: str, character_names: list[str]) -> _Declaration | None
```

## Recognition rules

| ID | Input (constitution `text` contains a line whose normalized body is …) | Required result | Source FR |
|---|---|---|---|
| C1 | a body that is **solely** `[PENDING: …]` (open bracket, keyword `PENDING` as a word, optional `: …`, optional surrounding whitespace) | `None` | FR-001, FR-002 |
| C2 | the **exact live scaffold** body `[PENDING: ¿Quién narra y desde qué distancia (primera/tercera persona, omnisciente/limitada)?]` | `None` | FR-001, FR-005, FR-007 |
| C3 | `  [pending: ¿x?]  ` — surrounding whitespace, lowercase keyword | `None` | FR-002 |
| C4 | `Tercera persona [PENDING: ¿focal?]` — real declared text **before** a leftover token | `_Declaration(person="third", …)` (real) | FR-002, FR-003 |
| C5 | `[PENDING: …] tercera persona` — real declared text **after** the token (body not *solely* the token) | `_Declaration(person="third", …)` (real) | FR-002 |
| C6 | `Tercera persona limitada, focalizada en Halia` — real voice | `_Declaration(person="third", limited=True, focal="Halia")` (unchanged) | FR-003 |
| C7 | English `third person limited, focused on Halia` | `_Declaration(person="third", limited=True, focal="Halia")` (unchanged) | FR-003, FR-004 |
| C8 | markdown-prefixed real voice `- **Voz narrativa**: tercera persona` (iteration 034) | recognized, person `"third"` (unchanged) | FR-003, FR-005 |
| C9 | no `Voz narrativa` / `Narrative voice` line | `None` (unchanged) | FR-006 |
| C10 | a line mentioning the label with no colon-delimited body | `None` (unchanged) | FR-006 |

The recognizer for C1–C3:
`_PENDING_ONLY = re.compile(r"(?i)^\s*\[pending\b[^\]]*\]\s*$")`, applied to
`match.group("body")` (the already markdown-normalized body).

## Downstream guarantee (through `validate()`)

| ID | Setup | Result | Source |
|---|---|---|---|
| V1 | live scaffold constitution (placeholder intact) + manuscript with an interiority verb on a named character | **0** `focalization` findings | FR-001, FR-007, SC-001 |
| V2 | placeholder replaced with a real third-person-limited voice focalized on a character + head-hopping manuscript | head-hopping finding fires (validator wakes) | FR-008, SC-002 |
| V3 | all existing focalization fixtures (bare / English / markdown-prefixed) | findings byte-identical to pre-fix | FR-003, SC-002 |
| V4 | any focalization finding | `Violation.triples == ()` (no graph) | FR-010 |

## Non-goals (explicit contract boundaries)

- The recognizer is **local** to `focalization.py` — not a shared repo-wide token
  utility. `references/pending-protocol.md` remains the prose source of truth it
  mirrors.
- No other validator or constitution section gains `[PENDING]` suppression.
- The constitution template (`constitution.md.j2`) is **not** reworded.
