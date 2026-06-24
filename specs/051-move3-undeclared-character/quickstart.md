# Quickstart — Move 3 first slice (undeclared characters)

Runnable validation that the slice works end to end. Prerequisites: `uv sync`.

## 1. All gates green

```bash
uv run pytest          # full suite, ≥80% coverage
uv run ruff check && uv run ruff format --check
uv run mypy --strict
```

Expected: all four green (SC-007).

## 2. The skill materializes, lints, and carries the 4th axis (SC-001, FR-001/003/005/008)

```bash
uv run pytest tests/resources/test_command_body.py \
              tests/resources/test_command_activation.py \
              tests/integrations/test_descriptions.py \
              tests/integrations/test_materialize.py \
              tests/integrations/test_skill_capabilities.py
```

Expected: green. Manually confirm in
`src/bookwright/resources/commands/bookwright-continuity.md`:
- `## Procedimiento` has a **fourth axis** ("open-set mentions / undeclared characters")
  that reads the authored roster, scans proper nouns, and judges person-without-a-sheet
  vs. org/place-name.
- `## Output` states each undeclared-person mention is reported as a deviation with a
  manuscript quote + "no entry in `bible/characters/`" + a suggestion.
- the procedure cites `references/golem-character.md` for "person roster from the sheets,
  not from a graph label".
- the widened `description` triggers in ES+EN and stays < 1024 chars, mirrored verbatim in
  `integrations/descriptions.py`.

## 3. The status nudge surfaces and never degrades green (SC-003/SC-004/FR-009/FR-010)

```bash
uv run pytest tests/status/test_rules.py tests/commands/test_status.py
uv run pytest tests/e2e/test_orchestration_workflow.py   # tiny-historical oracle
```

Expected: green. The behavior proven:
- a project whose validation report carries the `character_unknown_mentions`
  `pending_capability` abstention gains **exactly one** `bookwright-continuity`
  `next_action` (the semantic-judgment nudge);
- `tiny-historical` carries that nudge **and** stays GREEN;
- the flawless controls `tiny-novel`/`tiny-memoir` stay GREEN and carry the same nudge
  (it is informative — it never flips green).

Manual cross-check on a fixture:

```bash
uv run bookwright validate --json --project tests/fixtures/tiny-historical \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print([n for n in d['not_evaluated']])"
uv run bookwright status --json --project tests/fixtures/tiny-historical \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print([a['skill'] for a in d['next_actions']['items']])"
```

Expected: the `not_evaluated` list contains a `character_unknown_mentions`
`pending_capability` entry; the `next_actions` skills include `bookwright-continuity` for
the judge nudge (in addition to any error-driven continuity action), and the report's
status stays green for clean projects.

## 4. The validator and the gate are unchanged (SC-005, FR-011/FR-012)

```bash
uv run pytest tests/status/test_queries.py   # "always dormant" abstainer
```

Expected: `character_unknown_mentions` still raises
`NotEvaluated(kind=pending_capability)` unconditionally; only `error` findings gate CI;
no `error` is born from an LLM.

## 5. Records reconciled (SC-006)

- `DEBT.md`: `DEBT-013` is gone (`grep -n "DEBT-013" DEBT.md` → no match).
- `bookwright-design.md` § 20.6.2 marks the first vertical slice as landed; § 13.5 reframed.
- `CLAUDE.md`: milestone prose + iteration index gain row 051; the SPECKIT block points at
  this plan.
