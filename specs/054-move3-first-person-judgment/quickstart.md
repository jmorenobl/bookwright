# Quickstart: validating the first-person judgment slice (iteration 054)

Runnable checks that prove the slice works end to end. This is a **validation /
run guide** — implementation detail lives in `tasks.md` and the source. The
skill is LLM-judged prose, so its judgment quality is exercised at runtime, not
unit-asserted; what these steps verify is materialization, lint, the folded
trigger, the keyed nudge, and preserved green.

## Prerequisites

```bash
uv sync          # install deps + dev group
```

## 1. Measure the description headroom (before & after)

```bash
uv run python -c "from bookwright.integrations.descriptions import SKILL_DESCRIPTIONS as D; print(len(D['bookwright-continuity']))"
```

Expected: **before** the change `1000`; **after** the folded edit, **≤ 1024**
(the 1st-person trigger is folded into the 5th-axis voice/focalization phrase,
not appended). The front-matter `description` in
`resources/commands/bookwright-continuity.md` and the
`SKILL_DESCRIPTIONS["bookwright-continuity"]` mirror MUST be **byte-identical**.

## 2. The skill carries the sixth axis (contract `skill-sixth-axis.md`)

```bash
uv run pytest tests/resources/test_command_body.py -q
uv run pytest tests/resources/test_command_activation.py -q
uv run pytest tests/integrations/test_descriptions.py tests/integrations/test_skill_capabilities.py tests/integrations/test_materialize.py -q
```

Expected: green. The new `test_continuity_carries_the_sixth_first_person_axis`
asserts the 6th axis is present in `## Procedimiento` / `## Output`, names the
first-person / voice-slip judgment, cites the **declared voice**
(`bible/constitution.md`) as grounding, and carries the exact deviation phrasing
("first-person voice under a narration declared in third person"). The activation
oracle confirms the folded ES + EN trigger fires and the 4th/5th triggers still
fire. The equality gate confirms the verbatim mirror; lint confirms `name` ≤ 64
(= directory), `description` ≤ 1024, valid YAML.

## 3. The status nudge keys precisely on `first_person_recall` (contract `status-nudge.md`)

```bash
uv run pytest tests/status/test_rules.py tests/commands/test_status.py -q
```

Expected: green, covering —

- **Positive**: a `(focalization, pending_capability, first_person_recall)` state
  → exactly one `bookwright-continuity` first-person action, GREEN.
- **Negative / keying**: a `head_hopping`-only state → no first-person action;
  the first-person nudge never fires on `head_hopping` and vice versa.
- **All three co-fire** in table order (undeclared → head-hopping → first-person),
  distinct prompts.
- **Negative (first-person voice)**: no `first_person_recall` abstention → no nudge.

## 4. End-to-end: `tiny-historical` gains the nudge, stays GREEN

```bash
uv run pytest tests/e2e/test_orchestration_workflow.py -q
```

Expected: green. `tiny-historical` (third-person limited) now lists **6**
`next_actions` skills (a fourth `bookwright-continuity` — the first-person
judgment nudge) and stays GREEN; the co-located prose and inline `# nudge:` /
iteration comments in `tests/fixtures/tiny-historical/expected-status.md` are
internally consistent with the new state (5 → 6, «seis workstreams», «las
cuatro», the 054 rule comment). `tiny-novel` / `tiny-memoir` stay GREEN.

## 5. `focalization` and everything under `validation/` are untouched

```bash
git diff --stat -- src/bookwright/validation/   # expect: no output (zero diff)
uv run pytest tests/validation -q                # expect: green, unchanged
```

Expected: **no** diff under `validation/`; the abstention `code` contract and the
`_judges` helper are unchanged (FR-013).

## 6. Full gates

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest                                    # ≥ 80% coverage
```

Expected: all four gates green (SC-008). The CI gate stays error-only; no `error`
is born from an LLM (judgment, not gate).

## 7. Records reconciled

- `DEBT-021` is **removed** from `DEBT.md` (the dimension is complete: honesty 053
  + judgment 054) — `grep -n DEBT-021 DEBT.md` returns nothing.
- `bookwright-design.md` § 20.6.2 / § 13.5 mark the third move-3 dimension landed
  and the first move-3 wave complete (grounding for the 1st-person axis recorded
  as the **declared voice only** — see `research.md` Decision 1).
- The milestone prose / iteration index (row 054) reflects shipped work
  (release-time, alongside `CHANGELOG.md` / `CLAUDE.md`).
