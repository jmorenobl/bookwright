# Quickstart: Unified Error Envelope

## The one rule

Every error that can reach a `--json` boundary subclasses `BookwrightError`
(`src/bookwright/errors.py`) and does **not** define its own `to_json()`.

## Add a new serializable error

```python
from bookwright.errors import BookwrightError  # or the package root, e.g. IOError_

class ExampleError(IOError_):           # IOError_ already inherits BookwrightError
    code = "example_problem"            # class-level identifier (snake_case)

    def __init__(self, target: str) -> None:
        self.target = target            # keep domain attributes for catch sites
        super().__init__(
            f"could not process {target}",   # message
            {"target": target},              # details (omit the arg for none)
        )
```

`ExampleError("x").to_json()` →
`{"status":"error","code":"example_problem","message":"could not process x","details":{"target":"x"}}`.

- No `details` ⇒ call `super().__init__(message)`; the `"details"` key is omitted.
- Need a per-instance code (like `_UsageError`)? Set `self.code = …` in
  `__init__` **before** `super().__init__(...)`; it overrides the class default.

## Migrating an existing error (what this iteration does to each)

1. Change the package root's base from `Exception` to `BookwrightError`
   (e.g. `class IOError_(BookwrightError): ...`). Leave it abstract — no `code`,
   no `to_json`.
2. In each concrete class, **delete** the `to_json()` method.
3. Replace the tail of `__init__` (`super().__init__(message); self.message = message`)
   with `super().__init__(message, {<details>})`.
4. Keep every public attribute (`self.path`, `self.start`, `self.names`, …) so
   catch sites and existing tests are untouched.

## Verify the change

```bash
uv run pytest tests/core/test_json_shapes.py tests/golem/test_slug.py \
  tests/indexers/test_query_errors.py tests/validation/test_base.py \
  tests/validation/test_command.py            # error-shape safety net
uv run pytest                                  # full suite, ≥80% coverage gate
uv run ruff check && uv run ruff format --check
uv run mypy --strict
```

### Manual sanity checks

- **Single source of truth (SC-001)**: `grep -rn "def to_json" src/bookwright`
  should show `to_json` defined on `BookwrightError` only among error classes
  (the surviving hits — `ManifestWarning`, `Violation`, `ValidatorError`, the
  success-report builders — are the deliberately out-of-scope payloads).
- **No flat shapes remain (SC-003)**: `grep -rn '"error":' src/bookwright`
  returns nothing in the migrated error modules.
- **No import cycle (FR-010)**: `python -c "import bookwright.errors"` imports
  cleanly with no pull-in of `core/golem/io/indexers/validation/commands`.
- **Normalized envelopes (User Story 2)**:
  ```bash
  cd /tmp/not-a-project && uv run bookwright validate --json   # canonical {status,code,...}
  ```

## Updated tests (the only assertion changes)

- `tests/core/test_json_shapes.py` — the four manifest error tests assert the
  canonical envelope (`payload["code"]`, `payload["details"][…]`) instead of the
  flat `payload["error"]` / top-level fields.
- `tests/golem/test_slug.py` — line 49 asserts
  `to_json()["code"] == "golem_empty_slug"` (was `["error"]`).

Every other error-shape test passes **unchanged**.
