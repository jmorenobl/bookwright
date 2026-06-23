# Quickstart — validating the split

Runnable checks that prove the feature end to end. See [contracts/validator-split.md](./contracts/validator-split.md)
and [data-model.md](./data-model.md) for the shapes referenced here.

## Prerequisites

```bash
uv sync
```

## 1. The abstainer always declares `not_evaluated` (Story 1, SC-001/SC-002)

```bash
uv run pytest tests/validation/test_character_unknown_mentions.py -q
```

Expected: every case raises `NotEvaluated` with the open-set reason — on an empty project, a
clean project, and a project full of off-roster proper nouns. **Zero** unknown-mention
`warning` is ever produced.

## 2. The orphan `error` is byte-for-byte unchanged (Story 2, SC-003/SC-004)

```bash
uv run pytest tests/validation/test_character_presence.py -q
```

Expected: the migrated orphan/guard tests pass — an unmentioned bible character is exactly one
`error` with `validator="character_presence"`, citing its bible file; the
`not roster and not files` guard raises with the identical reason string.

## 3. Both verdicts coexist in one run (Story 3)

```bash
uv run pytest tests/validation/test_runner.py tests/validation/test_command.py -q
```

Expected: a project with a never-mentioned character **and** off-roster proper nouns reports the
orphan `error` **and** the `character_unknown_mentions` `not_evaluated` entry together; the exact
`ran` set is the 7 built-ins.

## 4. The green predicate is honestly `False` everywhere (Story 4, SC-006)

```bash
# inside any bookwright project (e.g. a copy of tests/fixtures/tiny-novel):
uv run bookwright graph build --json >/dev/null
uv run bookwright validate --json | python -c "import sys,json; p=json.load(sys.stdin); \
print('green =', p['status']=='ok' and p['not_evaluated']==[]); \
print('not_evaluated =', [r['validator'] for r in p['not_evaluated']])"
```

Expected: `green = False` and `character_unknown_mentions` present in `not_evaluated`. The
validate exit code is unchanged (not-evaluated never gates).

## 5. `tiny-historical` oracle: counts unchanged, `not_evaluated` + 4th action added (SC-005)

```bash
uv run pytest tests/e2e/test_orchestration_workflow.py tests/commands/test_status.py -q
```

Expected: `validation.counts` is byte-identical `{error: 1, warning: 1, info: 0}`; the oracle's
`next_actions.skills` is the 4-entry list (the extra `bookwright-continuity` is the always-on
dormant nudge); the new `not_evaluated` entry is documented.

## 6. No dead code, no ontology/seam/dep change (SC-008/SC-009)

```bash
# SC-009: every deleted symbol is gone from src/ and tests/
grep -rn "_unknown_mentions\|_roster_slugs\|_CANDIDATE\|_STOP_WORDS\|_is_sentence_initial\|location_names\|object_names" src tests
grep -rn "locations=\|objects=" tests/validation/conftest.py
# setting_names keeps exactly its setting_continuity consumer:
grep -rn "setting_names" src tests

# SC-008: seam + ontology untouched, file sizes ≤ 500
git diff --stat -- src/bookwright/io/prose.py src/bookwright/resources/schemas/golem-1.1/ '*golem.ttl'
wc -l src/bookwright/validation/validators/character_presence.py \
      src/bookwright/validation/validators/character_unknown_mentions.py \
      src/bookwright/validation/base.py
```

Expected: the first grep prints **nothing**; the `locations=/objects=` grep prints nothing; the
`setting_names` grep shows only `base.py` + `setting_continuity.py` (+ their tests); the
`git diff --stat` on the seam/ontology is empty; every `wc -l` is ≤ 500.

## 7. All four gates green (SC-007)

```bash
uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest
```

Expected: all pass; `ruff` reports **no** unused import left by the deletions; `DEBT.md` no
longer contains a DEBT-011 or DEBT-012 entry.
