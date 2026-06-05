# Quickstart: Unified Error Envelope

## The one rule

Every error that can reach a `--json` boundary subclasses `BookwrightError`
(`src/bookwright/errors.py`) and does **not** define its own envelope serializer
(neither `to_json()` nor `to_dict()`). A command may *wrap* that body with its own
envelope fields (e.g. `init`'s `rolled_back`/`bookwright_version`), but it sources
`code`/`message`/`details` from the error, never reconstructs them.

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
  tests/validation/test_command.py tests/integrations/test_errors_json.py \
  tests/commands/integration/test_use.py      # error-shape safety net (all eight origins)
uv run pytest                                  # full suite, ≥80% coverage gate
uv run ruff check && uv run ruff format --check
uv run mypy --strict
```

### Manual sanity checks

- **Single source of truth (SC-001)**: `grep -rnE "def to_(json|dict)" src/bookwright`
  should show the envelope serializer on `BookwrightError` only among error classes
  (the surviving hits — `ManifestWarning`, `Violation`, `ValidatorError`, the
  success-report builders — are the deliberately out-of-scope payloads; `to_dict`
  on an error class returns **zero** hits), and `grep -rn 'to_dict()' src/bookwright/commands`
  shows no command splicing `{"status":"error", **exc.to_dict()}`.
- **No flat shapes remain (SC-003)**: `grep -rn '"error":' src/bookwright`
  returns nothing in the migrated error modules, and no error spreads its fields
  at the envelope top level.
- **No import cycle (FR-010)**: `python -c "import bookwright.errors"` imports
  cleanly with no pull-in of `core/golem/io/indexers/validation/integrations/commands`.
- **Normalized envelopes (User Story 2 / 2b)**:
  ```bash
  cd /tmp/not-a-project && uv run bookwright validate --json     # canonical {status,code,...}
  uv run bookwright integration use bogus --json                 # canonical body; attrs under details
  ```

## Updated tests (the only assertion changes)

- `tests/core/test_json_shapes.py` — the four manifest error tests assert the
  canonical envelope (`payload["code"]`, `payload["details"][…]`) instead of the
  flat `payload["error"]` / top-level fields.
- `tests/golem/test_slug.py` — line 49 asserts
  `to_json()["code"] == "golem_empty_slug"` (was `["error"]`).
- `tests/integrations/test_errors_json.py` — assertions move from `to_dict()`
  (`{code,message,**attrs}`) to `to_json()` (`{status,code,message,details:{attrs}}`);
  the `to_dict` references in `tests/integrations/test_{registry,quickstart,plugin_contract,setup_materialize,option_parser}.py`
  retarget to `to_json`. Any top-level-attribute assertion in
  `tests/commands/integration/test_use.py` moves under `details`.

Every other error-shape test (including `init`'s envelope tests, byte-identical)
passes **unchanged**.
