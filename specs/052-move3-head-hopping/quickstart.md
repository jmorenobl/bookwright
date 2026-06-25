# Quickstart — Move 3 second slice: judge head-hopping in `bookwright-continuity`

A runnable validation guide proving the second move-3 slice end to end: the extended skill
materializes/lints/triggers on head-hopping prompts, and `bookwright status` surfaces an
informative head-hopping nudge on a limited-third project while green stays. The LLM judgment
quality is exercised by the agent at runtime — **not** asserted here (Principle VIII split).

## Prerequisites

```bash
uv sync
```

## 1. The extended skill materializes and lints (User Story 1)

```bash
uv run pytest tests/resources/test_command_body.py \
              tests/resources/test_command_activation.py \
              tests/integrations/test_descriptions.py \
              tests/integrations/test_materialize.py \
              tests/integrations/test_skill_capabilities.py
```

**Expected**: green. The body carries the **fifth axis** ("head-hopping / broken
focalization") in `## Procedimiento` and `## Output`, cites voice + POV calendar
(`bible/pov-structure.md`) + roster as grounding, documents the absent/`[PENDING]`-calendar
grounding-gap handling, lists `bible/pov-structure.md` under "Archivos a leer", and the
widened `description` (< 1024) triggers on ES + EN head-hopping prompts. The description
equality gate confirms `descriptions.py` mirrors the frontmatter verbatim.

## 2. The head-hopping status nudge fires on limited-third, green-preserving (User Story 2)

```bash
uv run pytest tests/status/test_rules.py \
              tests/commands/test_status.py \
              tests/e2e/test_orchestration_workflow.py
```

**Expected**: green. A state carrying `(focalization, pending_capability)` produces exactly
one new `bookwright-continuity` head-hopping `next_action` (distinct from the 051
undeclared-character action). The `tiny-historical` oracle's `next_actions` is **5** (was 4),
its GREEN status, `validation.counts`, and `not_evaluated` entries byte-identical.

## 3. The negative case — `missing_input` does NOT fire the head-hopping nudge (SC-004)

```bash
uv run pytest tests/status/test_rules.py -k "missing_input or focalization or judge or dormant"
```

**Expected**: green. A `(focalization, missing_input)` abstention fires
`activate_dormant_validators` and **not** `judge_head_hopping`; a `(focalization,
pending_capability)` abstention fires `judge_head_hopping` and **not**
`activate_dormant_validators`. The 051 `(character_unknown_mentions, pending_capability)`
nudge is unchanged.

## 4. End-to-end CLI surface unchanged on a real fixture

```bash
uv run bookwright status --json --project tests/fixtures/tiny-historical | python3 -m json.tool
```

**Expected**: a well-formed envelope; `next_actions[]` includes the three
`bookwright-continuity` entries (continuity-errors, undeclared-characters judge, head-hopping
judge); the project stays GREEN (no `missing_input` abstention). No LLM is invoked by the CLI.

## 5. Full suite + four gates (SC-008)

```bash
uv run pytest
uv run ruff check && uv run ruff format --check
uv run mypy --strict
```

**Expected**: all green, coverage ≥ 80 %.

## Definition of done

- [ ] `bookwright-continuity` has the fifth axis (procedure + output + grounding + grounding-gap
      clause + `bible/pov-structure.md` in "Archivos a leer"); widened bilingual `description`
      < 1024; lint passes (FR-001..FR-008).
- [ ] `descriptions.py` mirrors the widened description verbatim (FR-015; gate green).
- [ ] `status/rules.py`: `_JUDGE_SOURCES` deleted; shared `_judges(...)` helper added;
      `judge_undeclared_characters` byte-identical; new `judge_head_hopping` peer rule after it,
      before `define_focus` (FR-009/FR-010/FR-011).
- [ ] `focalization` and everything under `validation/` unchanged (FR-013); green predicate
      byte-identical; `activate_dormant_validators` stays `missing_input`-only (FR-012).
- [ ] `tiny-historical` oracle `next_actions` 4 → 5, GREEN preserved; negative case pure-unit
      (FR-017); LLM output not unit-asserted.
- [ ] `bookwright-design.md` § 20.6.2 (2nd slice landed) + § 13.5 reframed; CLAUDE.md milestone
      prose + iteration index row 052 updated; **no `DEBT.md` entry removed** (DEBT-021 stays
      open) (FR-018).
- [ ] `uv run pytest` + four gates green.
