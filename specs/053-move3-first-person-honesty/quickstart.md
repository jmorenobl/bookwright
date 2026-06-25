# Quickstart — validating the first-person-recall honesty + the `code` discriminator

Runnable scenarios that prove the iteration end to end. All verification is **empirical**
via `uv run pytest` and the real CLI — no LLM, no skill change in this slice.

## Prerequisites

```bash
uv sync
```

## Scenario 1 — a third-person-limited project declares the recall ceiling honestly (SC-001/SC-002)

```bash
uv run pytest tests/e2e/test_tri_valued_validation.py -q
```

Expected: a third-person-limited fixture (`tiny-novel`) carries **two** `focalization`
`not_evaluated` entries — `code=head_hopping` and `code=first_person_recall`, both
`kind=pending_capability` — and still reads **GREEN**. A first-person fixture
(`tiny-memoir`) carries **no** `first_person_recall` entry. Every entry carries the `code`
key.

Manual cross-check against a fixture:

```bash
cd "$(mktemp -d)" && cp -r "$OLDPWD/tests/fixtures/tiny-novel"/. . && \
  uv run bookwright graph build --json >/dev/null && \
  uv run bookwright validate --json | python -m json.tool | grep -A1 -E '"code"|first_person_recall|head_hopping'
```

Expect `"code": "first_person_recall"` and `"code": "head_hopping"` among the
`not_evaluated` entries; `"failed": false`.

## Scenario 2 — the explicit-pronoun warnings are byte-for-byte unchanged (SC-003)

```bash
uv run pytest tests/validation/validators/test_focalization.py -q
```

Expected: the `_first_person_breaks` warnings (`yo`/`nosotros`/…) and the regex are
unchanged; the first-person voice branch and the four `missing_input` causes gain no
`code=first_person_recall` entry.

## Scenario 3 — `status` keys the head-hopping nudge by `code`, never mis-fires (SC-004)

```bash
uv run pytest tests/status/test_rules.py -q
```

Expected — at the synthetic-state level (no disk):

- `(focalization, pending_capability, head_hopping)` → head-hopping `next_action` present.
- `(focalization, pending_capability, first_person_recall)` **alone** → head-hopping
  `next_action` **absent**; **no** first-person `next_action`.
- `(focalization, missing_input)` → no head-hopping `next_action`.
- `(character_unknown_mentions, pending_capability, undeclared_characters)` → the 051 nudge
  present, unchanged.

## Scenario 4 — the orchestration oracle converges, `next_actions` stays 5 (SC-005)

```bash
uv run pytest tests/e2e/test_orchestration_workflow.py -q
```

Expected: `tiny-historical` (third-person-limited) gains the `first_person_recall`
`not_evaluated` entry (now **3** entries) with `code` keys; `next_actions` stays length
**5** (head-hop nudge still fires; no first-person nudge); the project stays GREEN where it
was GREEN.

## Scenario 5 — the four gates (SC-008)

```bash
uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest
```

Expected: all green, coverage ≥ 80 %.

## What this iteration does NOT do

- No skill change (`bookwright-continuity` / `bookwright-verify` untouched); the
  first-person **judgment** + its nudge is iteration 054, which closes DEBT-021.
- No first-person `status` nudge (no destination yet).
- No regex widening; `_first_person_breaks` is preserved verbatim.
- No green/gate change; no new dependency; frozen ontology untouched.
