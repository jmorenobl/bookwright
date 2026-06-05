# Quickstart: Traceability Tag Cleanup

Reproduce the sweep, the cleanup verification, and the gate locally.

## 1. Run the sweep (the same regex the gate uses)

```bash
grep -rnIE '\bT0[0-9]{2}\b|\bUS-?[0-9]+\b|\+US[0-9]+' src/ tests/
```

- **Before this iteration**: ~67 lines / 48 files.
- **After**: zero output (SC-001). `grep` exits non-zero on no match.

## 2. Confirm the edits are comment-only (FR-008)

After editing, before committing:

```bash
git diff src/ tests/ | grep -E '^[-+]' | grep -vE '^[-+]{3}'
```

Every changed line must be inside a `#` comment or a `"""docstring"""`. No
`def`/`class`/assert/test-name line may appear in the diff. The two `src/`
touches are exactly `core/_research_block.py:1` and `integrations/base.py:11`.

## 3. Run the no-regression gate alone

```bash
uv run pytest tests/meta/test_no_traceability_tags.py -q
```

Green on the cleaned tree (C1).

## 4. Prove the gate bites (C2)

```bash
# inject a tag into any in-scope file, e.g.:
echo '# T013 regression probe' >> tests/conftest.py
uv run pytest tests/meta/test_no_traceability_tags.py -q   # → FAIL, names the file:line
git checkout tests/conftest.py                              # revert the probe
```

## 5. Full suite + coverage unchanged (SC-003)

```bash
uv run pytest                 # ≥80% coverage, same tests pass
uv run ruff check && uv run ruff format --check
uv run mypy --strict
```

All four gates green = ready to merge. The cleanup changes no executed line,
so coverage and behaviour are unchanged (FR-009).

## What this iteration does NOT touch

- Anything under `specs/` (FR-012) — task/story IDs are legitimate there.
- Any existing `FR`/`SC`/`D` number (FR-007) — frozen on merge.
- `docs/`, `bookwright-design.md`, repo root — outside the gate's scan.
