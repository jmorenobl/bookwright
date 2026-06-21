# Data Model: `focalization` `[PENDING]` placeholder suppression

This iteration introduces **no new entities** and **no new types**. It is a prose
validator behavior change. The relevant existing model and its one new "absence"
case are recorded here for completeness.

## Existing entity (unchanged shape)

### `_Declaration` (`focalization.py`, frozen dataclass)

| Field | Type | Meaning |
|---|---|---|
| `person` | `str \| None` | `"first"` \| `"third"` \| `None` (no recognizable person word in the body) |
| `limited` | `bool` | the declared voice is limited (`limitada`/`limitado`/`limited`) |
| `focal` | `str \| None` | the bible character named in the declaration body, if any |

`_parse_declaration(text, character_names) -> _Declaration | None` returns:

- `None` when **no** constitution line matches `_DECLARATION` (no `Voz narrativa` /
  `Narrative voice` line with a colon-delimited body), **and now also**
- `None` when the matched body is **solely an unanswered `[PENDING: …]` token**
  (the new behavior — FR-001). This is the *only* model-level change: a third input
  class (`unanswered placeholder body`) is folded into the existing `None`
  ("no declaration") output. No field, no class, no enum is added.

## State / value transitions (the one new mapping)

| Input: parsed declaration body | Before (DEBT-007) | After (this iteration) |
|---|---|---|
| `[PENDING: …(primera/tercera persona…limitada)?]` (live scaffold) | `_Declaration(person="third", limited=True, focal=None)` → head-hopping flood | `None` → zero findings |
| `[pending: ¿x?]` (no person word) | `_Declaration(person=None, …)` → zero findings | `None` → zero findings (same outcome, cleaner cause) |
| `Tercera persona [PENDING: ¿focal?]` (real text + leftover token) | `_Declaration(person="third", …)` | `_Declaration(person="third", …)` (unchanged — not *solely* a placeholder) |
| `Tercera persona limitada, focalizada en Halia` (real voice) | `_Declaration(person="third", limited=True, focal="Halia")` | identical (unchanged) |
| no `Voz narrativa` line | `None` | `None` (unchanged) |

## Validation rules (unchanged, for reference)

`validate()` already gates on `declaration is None or declaration.person is None →
return []`. The new guard simply routes the "solely a placeholder" body into the
`declaration is None` branch — no new gate, no new rule. The two heuristics
(first-person break, head-hopping) and the markdown normalization (iteration 034)
are untouched (FR-006).

## Ontology impact

**None.** Findings carry `triples=()` (asserted by the existing
`test_scaffold_shape_wakes_validator_through_validate` and reaffirmed by the new
FR-008 test). The frozen GOLEM closure (Constitution X) is not touched (FR-010).
