# Data Model: `focalization` after the head-hopping abstention (iteration 045)

`focalization` persists nothing and emits no graph triples (`triples=()`). The "data
model" here is the in-memory parsed declaration and the `validate()` decision tree —
both shrink. No new type is introduced; the iteration *consumes* `NotEvaluatedKind`
(044, `validation/base.py`) unchanged.

## Surviving in-memory shape

```python
@dataclass(frozen=True)
class _Declaration:
    person: str | None   # "first" | "third" | None
    limited: bool
    # focal: str | None   ← DELETED (FR-007): fed head-hopping alone
```

`_parse_declaration` keeps recognizing the bilingual, markdown-tolerant
narrative-voice line and computing `person` / `limited`; it **drops** its
`character_names` argument and the focal-name computation block.

```python
def _parse_declaration(view: ProseView) -> _Declaration:   # signature loses character_names
    # (ii) no line declares a voice            → raise NotEvaluated(...)             [missing_input]
    # (iii) body is solely [PENDING] (037)     → raise NotEvaluated(...)             [missing_input]
    # else: person from _THIRD/_FIRST, limited from _LIMITED. No focal resolution.
    return _Declaration(person=..., limited=bool(_LIMITED.search(body)))
```

## `validate()` decision tree (after 045)

```
constitution_text() is None
    └─► raise NotEvaluated("there is no constitution …")                 [missing_input]  (i)

declaration = _parse_declaration(constitution_view())     # may raise (ii)/(iii)  [missing_input]

declaration.person is None
    └─► raise NotEvaluated("… names no grammatical person …")            [missing_input]  (iv)

person == "third":
    limited:
        └─► raise NotEvaluated(
              "head-hopping / interiority attribution requires semantic judgment "
              "(move 3); the deterministic heuristic was measured nearly dormant on "
              "real prose",
              kind=NotEvaluatedKind.pending_capability)                  [pending_capability]  NEW
    not limited:
        └─► return self._first_person_breaks(view)     # evaluated; may be []  (non-limited third)

person == "first":
    └─► return []                                       # evaluated, no findings
```

Key invariants:

- The `limited` branch raises **before** `_first_person_breaks` runs — the whole
  validator abstains for limited-third (the source of DEBT-019).
- `character_names` is no longer computed in `validate` (orphaned once focal resolution
  is gone) — deleted.
- `_first_person_breaks` is unchanged and reachable **only** under non-limited third
  (FR-008).

## Deleted symbols (zero remaining consumers — grep-confirmed, FR-007)

| Symbol | Role | Why deletable |
|---|---|---|
| `Focalization._head_hopping` | the dormant heuristic | replaced by the abstention raise |
| `_INTERIORITY` (module regex) | interiority-verb matcher | fed `_head_hopping` only |
| `_Declaration.focal` | focal character name | consumed by `_head_hopping` only |
| focal-name computation in `_parse_declaration` | resolves `focal` | produces the deleted field |
| `character_names` param of `_parse_declaration` | feeds focal resolution | orphaned |
| `character_names = [...]` in `validate` | feeds the above | orphaned |

`_DECLARATION`, `_THIRD`, `_FIRST`, `_LIMITED`, `_FIRST_PERSON`, `_DIALOGUE_PREFIX`,
`_is_dialogue`, `_first_person_breaks`, `_PENDING_ONLY` (via `is_placeholder`) are all
**retained** — they serve the parser and the first-person-break check.

## Result types (unchanged — 044)

- `NotEvaluated(reason, kind)` — `validation/base.py`; `kind` defaults to
  `missing_input`. 045 adds one raise with `kind=pending_capability`.
- `NotEvaluatedResult(validator, reason, kind)` — stamped by the runner from
  `skip.kind`; serialized additively via `to_json()` (`kind` key). No edit.
