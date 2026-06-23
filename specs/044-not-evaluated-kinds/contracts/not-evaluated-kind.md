# Contract: the `kind` field on `not_evaluated[]`

This contract is **additive** to the iteration-040 `not_evaluated` channel. Every
pre-existing key and type is preserved (SC-007); one key, `kind`, is added to each
`not_evaluated[]` element on every serialized surface.

## 1. `bookwright validate --json` envelope

`not_evaluated[]` element — **before** (040):

```json
{ "validator": "character_unknown_mentions", "reason": "open-set proper-noun discovery requires semantic judgment (move 3); the deterministic heuristic was measured insufficient on real prose" }
```

**after** (044) — one additive key:

```json
{ "validator": "character_unknown_mentions", "reason": "open-set proper-noun discovery requires semantic judgment (move 3); the deterministic heuristic was measured insufficient on real prose", "kind": "pending_capability" }
```

An input-gap entry carries `"kind": "missing_input"`:

```json
{ "validator": "focalization", "reason": "the constitution does not declare a narrative voice", "kind": "missing_input" }
```

- `kind` ∈ `{"missing_input", "pending_capability"}` (closed set, FR-001).
- `violations[]`, `errors[]`, `summary`, `status`, `failed` are **unchanged**.
- The `status` field is still `"ok"` when there are no reported violations — it
  does **not** encode greenness (greenness is the derived predicate below).

## 2. `bookwright status` payload

`state.validation.not_evaluated[]` mirrors the same shape (it serializes each
entry via the same `NotEvaluatedResult.to_json`):

```json
{
  "validation": {
    "counts": { "error": 0, "warning": 0, "info": 0 },
    "ran": ["character_presence", "character_unknown_mentions", "focalization", "setting_continuity", "temporal", "..."],
    "not_evaluated": [
      { "validator": "character_unknown_mentions", "reason": "…", "kind": "pending_capability" }
    ]
  }
}
```

## 3. Human report (stderr / console)

The `not evaluated:` section labels each entry by its **kind-generic** tag; the
validator-specific detail stays in the reason:

```
not evaluated:
  character_unknown_mentions [known limitation — no action available yet]: open-set proper-noun discovery requires semantic judgment (move 3); the deterministic heuristic was measured insufficient on real prose
  focalization [input gap]: the constitution does not declare a narrative voice
```

- The exact label wording is a UX detail; the constraint (FR-007) is that the
  capability-gap label reads as a **non-actionable known limitation**, the
  input-gap label reads as something the author can fix, and **neither** is a
  silent pass.
- A run whose only content is a `not_evaluated` entry of **either** kind still
  shows this section — it does **not** print "no violations found" (FR-010).

## 4. Derived: the green/clean predicate (refined)

> A run is **green/clean** ⟺ `status == "ok"` **and** no `not_evaluated` entry has
> `kind == "missing_input"`.

| Run | `status` | `not_evaluated` kinds | green? |
|---|---|---|---|
| clean project | `ok` | `[pending_capability]` | **yes** (FR-004) |
| clean project | `ok` | `[]` | yes |
| missing voice declaration | `ok` | `[missing_input]` | **no** |
| both at once | `ok` | `[missing_input, pending_capability]` | no |
| has an `error` violation | `violations` | any | no |

## 5. Derived: the dormant-validator nudge (refined)

`bookwright status` recommends the `bookwright-continuity` "activate the dormant
validators" action **iff** at least one `not_evaluated` entry has
`kind == "missing_input"`. A `pending_capability`-only project produces **zero**
such actions (FR-005, SC-002). The action's prompt names only the `missing_input`
validators (edge case "both at once").

## 6. Invariants (unchanged)

- The CI **gate** fails iff there is an `error` `Violation`; no `not_evaluated`
  entry of either kind gates (FR-009, SC-005).
- `not_evaluated` is a channel distinct from `errors[]` (validators that crashed).
- Entries are sorted by validator name; serialization is byte-stable across runs.
