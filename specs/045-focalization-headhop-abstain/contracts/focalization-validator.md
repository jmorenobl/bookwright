# Contract: `focalization` abstention behavior (iteration 045)

The stable contract `focalization` honors after the head-hopping rule stops faking.
It refines — does not replace — the iteration 040/044 tri-valued / kind contract.

## C1 — Precondition → verdict table

| Constitution / declaration state | Verdict | `kind` | Reason (English, stable) |
|---|---|---|---|
| (i) no constitution file | `not_evaluated` | `missing_input` | `there is no constitution to read the narrative voice from` |
| (ii) constitution, no voice line | `not_evaluated` | `missing_input` | `the constitution does not declare a narrative voice` |
| (iii) voice is solely `[PENDING]` | `not_evaluated` | `missing_input` | `the narrative-voice declaration is still unanswered ([PENDING])` |
| (iv) declaration names no person | `not_evaluated` | `missing_input` | `the narrative-voice declaration names no grammatical person (neither first nor third)` |
| **third person + limited (focal, any/none resolved)** | **`not_evaluated`** | **`pending_capability`** | **`head-hopping / interiority attribution requires semantic judgment (move 3); the deterministic heuristic was measured nearly dormant on real prose`** |
| third person + NOT limited | `evaluated` | — | runs the first-person-break check; `[]` or `warning` findings |
| first person | `evaluated` | — | no findings (nothing third-person to flag) |

Rows (i)–(iv) and the two `evaluated` rows are **byte-identical to the current
release** (FR-004/FR-005/FR-008). Only the bold row is new.

## C2 — Invariants

1. **Single validator** — `focalization` is **not** split (FR-006); its `name`,
   `severity_default`, registration, and auto-discovery are unchanged.
2. **All-or-nothing** — a run either returns `list[Violation]` **or** raises
   `NotEvaluated`, never both. Under limited-third it raises, so the first-person-break
   check does not also run (the DEBT-019 over-claim — documented, not hidden).
3. **Prose validator** — `triples == ()` on every finding; no graph access; frozen
   GOLEM ontology untouched (FR-012, Constitution X).
4. **Kind correctness** — the capability-gap entry MUST be `pending_capability` and MUST
   NOT deny green nor fire the `status` dormant-validator nudge (per the 044 refined
   predicate / rule); the four input-conditional rows MUST stay `missing_input` (FR-003).
5. **No machinery edit** — the green predicate, `NotEvaluatedKind`, the `not_evaluated[]`
   serialization, the `status` nudge rule, and the report render are unchanged; 045 only
   *consumes* them (FR-009).
6. **Determinism** — the verdict is a pure function of the constitution declaration
   (the manuscript is not even read under limited-third), so it is stable across runs.

## C3 — Serialization (unchanged, 044)

The capability-gap entry appears in every consumer that surfaces `not_evaluated[]`:

```json
{
  "validator": "focalization",
  "reason": "head-hopping / interiority attribution requires semantic judgment (move 3); the deterministic heuristic was measured nearly dormant on real prose",
  "kind": "pending_capability"
}
```

In the human report it renders as
`focalization [known limitation — no action available yet]: <reason>` (the
`_KIND_LABEL` tag is kind-generic; the move-3 specifics stay in `reason`).

## C4 — Anti-drift guarantees (tests)

- A unit test asserts the bold row: a parseable third-limited focal voice raises exactly
  one `NotEvaluated` with `kind == pending_capability` and the C1 reason; and a
  third-limited voice naming **no** focal character abstains identically.
- The four `missing_input` rows keep their existing unit tests (reason + kind unchanged).
- `tests/e2e/test_tri_valued_validation.py` asserts a clean third-limited fixture
  (`tiny-novel`) stays **green** carrying both the `focalization` and
  `character_unknown_mentions` capability-gap entries, while a first-person fixture
  (`tiny-memoir`) carries only `character_unknown_mentions`.
- The `tiny-historical` oracle pins the additive `focalization` entry with
  `counts`/`next_actions` unchanged.
