# Quickstart / Validation Guide: `character_presence` heading-marker normalization

How to prove the fix end to end. The validator is a prose-level check; these
scenarios run it directly via the unit-test harness and via the real CLI.

## Prerequisites

```bash
uv sync   # deps + dev group into .venv
```

## Scenario 1 — Heading-opening word produces zero findings (User Story 1, FR-006)

A manuscript organized under chapter headings with no out-of-roster prose names
must yield **zero** `character_presence` findings.

- **Setup (in-test, synthetic)**: a project whose roster contains the one character
  it mentions, and a manuscript such as:

  ```markdown
  # Capítulo 1

  Aparici llegó al muelle.

  ## Escena en el faro

  Allí esperó.
  ```

  Headings at multiple depths (`#` … `######`), each followed by a space and a
  capitalized word, exercise the depth range (Acceptance Scenario 2).
- **Run**: `CharacterPresence().validate(load_context(root), RdflibIndexer())`.
- **Expected**: `[]` — no `proper noun 'Capítulo' …` / `'Escena' …` warning; the
  heading-opening words are exempted as line-initial (SC-001).

## Scenario 2 — Out-of-roster name inside a heading body is still flagged (User Story 2, FR-007)

Stripping the marker must restore the title to ordinary prose, **not** exempt the
whole line.

- **Setup**: roster `["Aparici"]`; manuscript heading `# La caída de Elena` with
  `Elena` absent from the roster (and not in the manuscript body either).
- **Run**: same as above.
- **Expected**: exactly one `warning` whose message contains `Elena`, citing the
  heading's `relpath:line` (SC-002). `La` opens the title and is exempt; `Elena`
  is mid-line and fires.

## Scenario 3 — Existing-behavior parity (FR-003 / FR-004 / SC-003)

The pre-existing suite must stay green unchanged — no finding added or removed in
non-heading prose, stop-set and orphan(`error`) direction byte-identical.

```bash
uv run pytest tests/validation/test_character_presence.py -q
```

- **Expected**: all prior tests (`test_orphan_bible_character_is_error`,
  `test_unknown_mention_is_warning_deduped_per_name`,
  `test_clean_project_has_no_findings`,
  `test_sentence_initial_capital_is_not_flagged`) pass without edits, plus the two
  new tests.

## Scenario 4 — Full gates (SC-004)

```bash
uv run ruff check
uv run ruff format --check
uv run mypy --strict
uv run pytest        # full suite, ≥ 80 % coverage enforced
```

- **Expected**: all four green.

## Scenario 5 — DEBT ledger cleared (FR-008 / SC-005)

```bash
grep -c "DEBT-008" DEBT.md   # → 0
```

- **Expected**: no `DEBT-008` entry; the "Deuda abierta" section reads
  `_Ninguna por ahora._`.

## References

- Requirements & acceptance: [spec.md](./spec.md)
- Design decisions (marker shape, locator stability, scope-local recognizer):
  [research.md](./research.md)
- Analysis constructs: [data-model.md](./data-model.md)
