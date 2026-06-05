# Contract: No-regression gate

The gate is the only new executable surface in this iteration. It is a pytest
test, not a CLI command, so its "contract" is its observable test behaviour
rather than a JSON schema.

## Location & shape

- File: `tests/meta/test_no_traceability_tags.py` (new `tests/meta/` package).
- One public test function (e.g. `test_no_forbidden_traceability_tags`).
- Stdlib only: `re`, `pathlib`. No new dependency (Constitution II).

## The pattern (single source of truth)

```python
FORBIDDEN = re.compile(r"\bT0[0-9]{2}\b|\bUS-?[0-9]+\b|\+US[0-9]+")
```

Identical to the sweep in spec/research/plan. The three alternatives:
`T` + exactly 3 digits; `US` + optional `-` + digits; `+US` + digits.

## Scan surface (FR-001, FR-002, FR-012, D4)

- **In scope**: every text file under `src/` and `tests/`, both relative to the
  repo root resolved from the gate's `__file__`.
- **Skipped**: `__pycache__` directories; binaries (open as UTF-8, skip on
  `UnicodeDecodeError`); the gate's own file (`Path(__file__)`).
- **Out of scope**: everything outside `src/`+`tests/` — notably `specs/`,
  `docs/`, `bookwright-design.md`, repo root. The gate never reads them.

## Behavioural contract

| # | Given | When | Then | Maps to |
|---|---|---|---|---|
| C1 | the cleaned tree | gate runs under `uv run pytest` | passes (0 matches) | SC-004, US3-AS1 |
| C2 | a `T0xx`/`US-x` is introduced into any in-scope file | gate runs | **fails**, and the assertion message lists offending `file:line: matched-token` | FR-010, US3-AS2 |
| C3 | the gate runs in CI on push/PR | a PR reintroduces a tag | CI is red → merge blocked | FR-010, US3-AS3 |
| C4 | permitted content (`FR-021`, `SC-009`, `D-2`, `§ 20.5`, "iteration 9") present | gate runs | passes — no false positive | FR-011, US3 |
| C5 | the gate's own pattern literal + `T0xx`/`US-x`/`+USx` placeholders in docs | gate runs | passes — the regex provably does not match its own source or placeholders (research D3) | FR-011, edge case "gate's own source" |

## Failure-message format

On failure, the assertion message MUST identify each offender precisely enough
to fix without re-running the sweep manually — minimum `relative/path.py:LINE:
TOKEN`, one per line, e.g.:

```
Forbidden traceability tags found (see CONTRIBUTING.md § "Traceability tags in code"):
  src/bookwright/foo.py:42: T013
  tests/bar/test_x.py:1: US2
Convert to a durable FR/SC/D ref or rewrite to neutral prose.
```

## Non-goals (locked by spec Clarifications)

- No pre-commit hook wired (trivial future add, out of scope).
- No ruff custom rule.
- The gate does not auto-fix; it only reports.
