# Phase 1 Data Model — Move 3 first slice (undeclared characters)

No new persisted types and no ontology change (Principle X). This slice composes
**existing** records across the deterministic layer (`validate`) and the skill layer
(`bookwright-continuity`), bound by the `not_evaluated` channel. The "entities" below
are the conceptual contract; the only code-level additions are one status `Action`
builder + `Rule`, and prose in the skill body / reference doc.

## E1 — Authored person roster (read at skill runtime, not persisted)

The set of declared names the agent uses as grounding to separate signal from noise.

| Field | Source | Notes |
|---|---|---|
| person names | `bible/characters/*.md` → `name:` field | **Not** a graph label — `G1_Character` has no `rdfs:label`; the name is in `name:` and the URI slug. |
| non-person declared names | `bible/settings/*.md`, `bible/locations/*.md`, `bible/objects/*.md` | Lets the agent recognize proper nouns that are *already declared but are not persons* (so they are not reported). |

- **Validation rule**: a manuscript proper noun naming a **person** that is **not** in
  the person roster, **and** is not an organization / place name / vocative / title word,
  is an *undeclared-character* deviation.
- **Empty-roster edge**: if the person roster is empty, every proper noun is a candidate;
  the agent still judges person vs. org/place-name and reports the persons (thin grounding
  is a judgment input, not an error).

## E2 — `not_evaluated` entry / `Abstention` — the inter-layer contract

The existing `NotEvaluatedResult(validator, reason, kind)` (frozen; see
`validation/base.py`), surfaced by the runner into both the `validate` envelope and
`ValidationSummary.not_evaluated`.

| Field | Value for this slice |
|---|---|
| `validator` | `"character_unknown_mentions"` |
| `reason` | "open-set proper-noun discovery requires semantic judgment (move 3); …" (unchanged) |
| `kind` | `NotEvaluatedKind.pending_capability` (unchanged) |

- **Role**: § 20.6.2 decision 2 — this datum *is* the contract. The validator **names**
  the gap; the skill **closes** it with the roster as grounding. It is emitted
  **unconditionally** (the validator is a pure abstainer), so it is present on every
  validated project. **Unchanged by this iteration.**

## E3 — Continuity deviation (undeclared-character) — skill report output

One more deviation in the continuity prose report (not a persisted record; not a CLI
finding). Shape:

| Part | Content |
|---|---|
| quote | the manuscript prose naming the undeclared person |
| gap | the phrase "no entry in `bible/characters/`" (ES/EN equivalent) |
| suggestion | create the sheet, or confirm it is not a character |

- **Severity**: this lives in the **skill** report (judgment), never a `bookwright validate`
  `error` — no `error` is born from an LLM (FR-012, § 20.6.2 decision 4).

## E4 — Status `next_action` (informative) — the discoverability surface

A new `Action` produced by a new `Rule` in `status/rules.py` (pure `state → list[Action]`,
no I/O).

| Field | Value |
|---|---|
| `skill` | `"bookwright-continuity"` |
| `prompt` | fixed English template directing the agent to scan proper nouns, read the authored roster, and report each person used in the prose with no sheet in `bible/characters/`. |
| `reason` | fixed English template naming the abstaining source (`character_unknown_mentions` could not judge open-set mentions — the skill provides the semantic judgment). |

- **Predicate**: fires iff any `state.validation.not_evaluated` entry has
  `validator` in the **judge source-set** (a module-level frozenset, today
  `{"character_unknown_mentions"}`). Keys on the **source validator**, never on the
  `pending_capability` *kind* (FR-009, Clarifications).
- **Determinism**: the same state yields a byte-identical action (the rule-table
  determinism contract, SC-002); the prompt/reason are fixed templates with no minted
  data.
- **Green invariant**: producing this action **never** changes the green predicate
  (`validation/report.py`, `missing_input`-only). A `pending_capability` entry does not
  degrade green (FR-010). The action is purely additive to `next_actions[]`.

## Rule-table placement

`RULES` tuple order (priority) after this slice:

```
bootstrap_graph            (short-circuits everything on a degraded graph)
research_queue
verify_findings
review_continuity
activate_dormant_validators        (missing_input-only — UNCHANGED, 044)
judge_undeclared_characters        (NEW — keyed on the abstaining source)
define_focus
```

- On `tiny-historical`: `research_queue`, `verify_findings`, `review_continuity` fire as
  today, then `judge_undeclared_characters` fires (the `character_unknown_mentions`
  abstention is present) → a second `bookwright-continuity` action. `next_actions.skills`
  grows from `[research, verify, continuity]` to `[research, verify, continuity, continuity]`.
  Status stays GREEN; `validation.counts` and the `not_evaluated` entries are byte-identical.
- On the green controls `tiny-novel`/`tiny-memoir`: the abstention is present (unconditional),
  so the judge action fires; they have no errors/`missing_input`, so they stay GREEN —
  proving the nudge is informative.

## State transitions

None. All records are frozen/immutable; the status rule is a pure function of an
already-aggregated `StatusState`.
