# Contract: `bookwright status` derived state (tri-valued validation)

Additive change to the `status` `--json` document. One new key under
`state.validation`; one new `next_actions` rule.

## `state.validation` payload

```jsonc
"validation": {
  "counts": { "error": 0, "warning": 0, "info": 0 },   // UNCHANGED
  "ran": ["character_presence", "focalization", "setting_continuity", "..."],  // UNCHANGED
  "not_evaluated": [                                     // NEW (FR-010)
    { "validator": "focalization", "reason": "the constitution does not declare a narrative voice" }
  ]
}
```

- Sorted by validator name (FR-013); byte-identical across runs on an unchanged
  corpus (the `reason` strings are fixed English templates — no clock/URI/env).
- Degraded path (no build prerequisites): `validation` stays
  `{counts: {}, ran: [], not_evaluated: []}` — the status command constructs an empty
  `ValidationSummary` there, so the new key is always present (never missing).

## `next_actions` — activation rule (FR-010 / SC-004)

A new pure rule `activate_dormant_validators`:

- **Applies** iff `state.validation.not_evaluated` is non-empty.
- **Builds** one `Action`:
  - `skill`: `bookwright-continuity` (the validation-facing skill).
  - `reason`: e.g. `"1 validator could not evaluate"` (count-driven, `_plural`).
  - `prompt`: enumerates each dormant validator that has a concrete remedy in the
    static `_REMEDIES` map, e.g.
    `"Activate the dormant validators: focalization — declare the narrative voice in the constitution."`
- **Priority**: after `review_continuity`, before `define_focus` in `RULES`.
- Validators with no mapped remedy contribute nothing to the prompt (FR-010 "where
  an actionable remedy exists"); if none of the not-evaluated validators has a
  remedy, the action's prompt still names the dormant ones generically — but the
  migrated set all have remedies, so SC-004's focalization remedy is always present
  when `focalization` is not-evaluated.

`_REMEDIES` (static, English):

| Validator | Remedy clause |
|---|---|
| `focalization` | `declare the narrative voice in the constitution` |
| `setting_continuity` | `add manuscript prose to validate` |
| `character_presence` | `add a bible character roster and manuscript prose` |

## Skill resource (FR-011)

`resources/commands/bookwright-research.md` startup step (the `bookwright status
--json` read) lists the **raw** `state.validation.not_evaluated` facts among the raw
facts it surfaces in its "Próximos pasos / Punto de partida" block — read from
`state.validation`, **not** from `next_actions[]` (which stays a between-skills
handoff, per the existing skill contract). Minimal Spanish edit, consistent with the
existing `state.open_questions` / `state.unresolved_anchors` enumeration.
