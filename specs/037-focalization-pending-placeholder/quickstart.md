# Quickstart: verifying the `[PENDING]` voice-placeholder suppression

Runnable validation scenarios that prove the feature. See
[contracts/parse-declaration.md](./contracts/parse-declaration.md) for the full
recognition table and [data-model.md](./data-model.md) for the value transitions.

## Prerequisites

```bash
uv sync
```

## Scenario 1 — fresh scaffold produces zero focalization findings (FR-007 / SC-001)

The defect: a brand-new project (constitution placeholder untouched) floods the
author with head-hopping warnings as soon as an interiority verb appears.

After the fix, the parser treats the unanswered `[PENDING: …]` voice body as no
declaration:

```bash
# Unit-level: the live scaffold voice line parses to None.
uv run python -c "
import importlib.resources
from bookwright.validation.validators.focalization import _parse_declaration
tpl = importlib.resources.files('bookwright.resources.project.bible').joinpath('constitution.md.j2').read_text(encoding='utf-8')
line = [l for l in tpl.splitlines() if 'Voz narrativa' in l][0]
assert _parse_declaration(line, ['Halia']) is None, 'placeholder must parse to None'
print('OK: scaffold placeholder parses to None')
"
```

End-to-end through `validate()` (the new test, FR-007): the exact scaffold
constitution + a manuscript scene `Halia pensó que el faro callaba.` → **0**
findings.

## Scenario 2 — answering the prompt wakes the validator (FR-008 / SC-002)

Replace only the placeholder body with a real voice; the previously-suppressed
finding fires:

```bash
uv run python -c "
from bookwright.validation.validators.focalization import _parse_declaration
d = _parse_declaration('- **Voz narrativa**: Tercera persona limitada, focalizada en Halia', ['Halia'])
assert d is not None and d.person == 'third' and d.limited and d.focal == 'Halia'
print('OK: real voice wakes the parser', d)
"
```

## Scenario 3 — no regression on existing fixtures (FR-003 / SC-002)

```bash
uv run pytest tests/validation/test_focalization.py -q
```

Expected: all pass, including the updated `test_template_binding` (now asserts the
live placeholder line parses to `None`) and the two new tests.

## Scenario 4 — DEBT-007 removed (FR-009 / SC-004)

```bash
grep -c "DEBT-007" DEBT.md   # expected: 0
```

## Full gate run (SC-003)

```bash
uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest
```

Expected: all four green, coverage ≥ 80 %.
