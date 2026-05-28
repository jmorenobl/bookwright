# Quickstart: Manifest Model

**Feature**: 002-manifest-model
**Date**: 2026-05-28

This is the developer-facing usage guide for the `bookwright.core`
manifest model. It assumes iteration 2 has been merged (`uv sync` has
pulled in the new `packaging` dependency; `Manifest`,
`ManifestValidationError`, etc. are importable from `bookwright.core`).

The audience is (a) future iterations of Bookwright that need to read
or write a `manifest.toml`, and (b) downstream tests. There is no
end-user CLI surface in this iteration.

## Install + sanity check

```bash
uv sync
uv run python -c "from bookwright.core import Manifest, KNOWN_MANIFEST_VERSIONS; print(KNOWN_MANIFEST_VERSIONS)"
# frozenset({1})
```

## Load an existing manifest

```python
from pathlib import Path
from bookwright.core import Manifest, ManifestValidationError

try:
    manifest = Manifest.load(Path("./my-book/manifest.toml"))
except ManifestValidationError as exc:
    for failure in exc.failures:
        print(f"{failure.field_path}: {failure.message}")
    raise

print(manifest.book.title)
print(manifest.book.authors)
print(manifest.bookwright.uri_base)
print(manifest.integration.key)         # 'claude' or 'generic' (informational)
for w in manifest.warnings:
    print(f"warning: {w.message}")
```

**What you get back**: a `Manifest` instance whose attribute names are
exactly the TOML key paths in snake_case. `manifest.book.metadata` and
`manifest.integration.options` are plain dicts (opaque, free-form).

## Build a new manifest from minimal inputs (FR-015)

```python
from bookwright.core import Manifest

m = Manifest.build(
    title="The Quiet Empire",
    authors=["Jorge Moreno"],
    integration_key="claude",
    uri_base="https://books.example.org/quiet-empire/",
)

# Defaults applied per FR-017:
assert m.book.type == "novel"
assert m.book.language == "en"
assert m.book.status == "drafting"
assert m.bookwright.manifest_version == "1"
assert m.integration.skills_dir == ".claude/skills"
assert m.paths.manuscript == "manuscript/"
```

### With overrides

```python
m = Manifest.build(
    title="Una memoria entre dos puertos",
    authors=["Ana Ruiz"],
    integration_key="generic",
    uri_base="https://books.example.org/dos-puertos/",
    language="es",
    type="memoir",
    status="structuring",
    integration_options={"flavor": "cursor"},
)

assert m.book.language == "es"
assert m.book.type == "memoir"
assert m.book.status == "structuring"
assert m.integration.skills_dir == ".agents/skills"        # default for 'generic'
assert m.integration.options == {"flavor": "cursor"}
```

### Unknown override → `TypeError`

```python
from bookwright.core import Manifest

try:
    Manifest.build(
        title="x",
        authors=["a"],
        integration_key="claude",
        uri_base="https://books.example.org/x/",
        flavor="spicy",     # not a documented override
    )
except TypeError as exc:
    print(exc)
    # build() got unexpected keyword argument 'flavor'
```

### Override that violates a rule → `ManifestValidationError`

```python
from bookwright.core import Manifest, ManifestValidationError

try:
    Manifest.build(
        title="x",
        authors=["a"],
        integration_key="claude",
        uri_base="https://books.example.org/x/",
        language="klingon",   # not in ISO 639-1
    )
except ManifestValidationError as exc:
    for f in exc.failures:
        print(f"{f.field_path} ({f.rule_id}): {f.message}")
    # book.language (book.language.not_iso_639_1): language 'klingon' is not a valid ISO 639-1 code
```

## Write a manifest

```python
from pathlib import Path
from bookwright.core import Manifest, ManifestOverwriteError

m = Manifest.build(
    title="...",
    authors=["..."],
    integration_key="claude",
    uri_base="https://books.example.org/x/",
)

target = Path("./my-book/manifest.toml")

# First write: ok
m.dump(target)

# Second write to the same path: refused (FR-019)
try:
    m.dump(target)
except ManifestOverwriteError as exc:
    print(exc)

# Explicit overwrite: ok
m.dump(target, overwrite=True)
```

**Atomicity (FR-021)**: if the write fails midway (disk full,
permission denied) the file at `target` retains its prior contents.
The dump is implemented as write-to-temp + `os.replace`, both inside
`target.parent`.

## Round-trip property (FR-020, SC-005)

```python
from pathlib import Path
from bookwright.core import Manifest

src = Path("./my-book/manifest.toml")
dst = Path("./my-book/manifest.roundtrip.toml")

Manifest.load(src).dump(dst, overwrite=True)

assert src.read_bytes() == dst.read_bytes()
```

This holds for any manifest that loads successfully.

## Future-version warning (FR-013)

```python
from pathlib import Path
from bookwright.core import Manifest

# manifest.toml declares manifest_version = "9"
m = Manifest.load(Path("./future-project/manifest.toml"))

assert len(m.warnings) == 1
w = m.warnings[0]
assert w.rule_id == "manifest_version.unknown_future"
assert w.offending_value == "9"
print(w.message)
# manifest_version 9 is newer than this CLI knows about (max known: 1); load was best-effort
```

The model layer attaches the warning to the returned object. It does
**not** print to stdout/stderr from the model layer itself
(SC-006). The future iteration-4 CLI command will surface
`manifest.warnings` onto stderr (human mode) or into the `warnings`
array of its JSON envelope (`--json` mode).

## Running the tests for this iteration

```bash
# all manifest tests
uv run pytest tests/core/

# one user story at a time (during development)
uv run pytest tests/core/test_load_valid.py        # US1
uv run pytest tests/core/test_load_invalid.py      # US2
uv run pytest tests/core/test_version_gate.py      # US3
uv run pytest tests/core/test_build.py             # US4 (build)
uv run pytest tests/core/test_write.py             # US4 (write + round-trip)
uv run pytest tests/core/test_future_version.py    # US5
uv run pytest tests/core/test_json_shapes.py       # FR-024

# coverage gate for this module (spec's acceptance criterion is ≥90 %)
uv run pytest tests/core/ --cov=bookwright.core --cov-report=term-missing
```

The global CI gate is `--cov-fail-under=80` (set in `pyproject.toml`);
the iteration's own acceptance criterion is stricter for the
`bookwright.core` package, so review locally before pushing.

## Acceptance criteria check (FR → quickstart section)

| FR | Demonstrated above in | Notes |
|---|---|---|
| FR-001 | "Load an existing manifest" | |
| FR-002 | (tested only) | Caught by `tests/core/test_load_invalid.py`; no quickstart example because file-missing/syntax-error are exception paths the consumer rarely demos. |
| FR-003 | "Build a new manifest with overrides" — `integration_options={"flavor": "cursor"}` round-trips verbatim. | |
| FR-004–FR-010 | "Override that violates a rule" | One representative example (`language`); other rules behave identically. |
| FR-011 | (tested only) — multi-error accumulation is a `ManifestValidationError.failures` property exercised in tests. | |
| FR-012 | (tested only) — version gate is a property of `load()`. | |
| FR-013–FR-014 | "Future-version warning" | |
| FR-015–FR-017 | "Build a new manifest" sections | |
| FR-018–FR-021 | "Write a manifest" + "Round-trip property" | |
| FR-022 | "Load an existing manifest" — `manifest.integration.key` is just read. | |
| FR-023 | (tested only) — absence of a check is what the test asserts. | |
| FR-024 | (tested only) — `.to_json()` shapes are asserted in `tests/core/test_json_shapes.py`. | |
