# Quality Audit Checklist

Source: review.md (b286bc6)

- [X] No CRITICAL or HIGH findings — branch is clear to merge from a governance / scope / security perspective.

MEDIUM and LOW items (do not block merge, but worth addressing in a small follow-up):

- [ ] R1 — Pre-commit ruff rev (`v0.5.7`) drifts from pyproject `ruff>=0.5` ([.pre-commit-config.yaml:3](../../../.pre-commit-config.yaml#L3))
- [ ] R2 — Empty `@app.callback()` `_root` in cli.py is dead code ([src/bookwright/cli.py:15-17](../../../src/bookwright/cli.py#L15-L17))
- [ ] R3 — `main()` wrapper in `__main__.py` is a redundant hop ([src/bookwright/__main__.py:6-11](../../../src/bookwright/__main__.py#L6-L11))
- [ ] R4 — Weak `assert "OK" in result.stdout` in `test_check_human` ([tests/test_cli_check.py:17](../../../tests/test_cli_check.py#L17))
- [ ] R5 — No subprocess byte-exact stdout test for `bookwright check --json` (gap in [tests/test_cli_subprocess.py](../../../tests/test_cli_subprocess.py))
