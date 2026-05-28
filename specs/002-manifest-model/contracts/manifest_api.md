# Contract: `bookwright.core` public API

**Feature**: 002-manifest-model
**Date**: 2026-05-28

This document is the **public-API contract** for the manifest model. The
"interface" of this iteration is a Python module surface, not a CLI
command or HTTP endpoint: iteration 2 ships a library that iterations
3+ import. The contract below is what downstream code (and the eventual
iteration-4 `init` CLI command) is allowed to rely on.

Any breaking change to a signature, exception type, return shape, or
JSON envelope listed here is a contract change and requires a
`manifest_version` bump or a constitutional MINOR amendment, whichever
applies.

## Package surface

```python
# src/bookwright/core/__init__.py — public re-exports
from bookwright.core.manifest import (
    Manifest,
    KNOWN_MANIFEST_VERSIONS,
    BOOK_TYPES,
    BOOK_STATUSES,
)
from bookwright.core.errors import (
    ManifestError,
    ManifestNotFoundError,
    ManifestSyntaxError,
    ManifestValidationError,
    ManifestOverwriteError,
    ManifestWarning,
)

__all__ = [
    "Manifest",
    "KNOWN_MANIFEST_VERSIONS",
    "BOOK_TYPES",
    "BOOK_STATUSES",
    "ManifestError",
    "ManifestNotFoundError",
    "ManifestSyntaxError",
    "ManifestValidationError",
    "ManifestOverwriteError",
    "ManifestWarning",
]
```

Anything *not* in `__all__` is implementation detail and may change
without notice.

## `Manifest`

```python
class Manifest(BaseModel):
    bookwright: BookwrightBlock
    book: BookBlock
    vocabularies: VocabulariesBlock
    validators: ValidatorsBlock
    integration: IntegrationBlock
    paths: PathsBlock
    warnings: tuple[ManifestWarning, ...]

    @classmethod
    def load(cls, path: Path | str) -> "Manifest": ...

    def dump(self, path: Path | str, *, overwrite: bool = False) -> Path: ...

    @classmethod
    def build(
        cls,
        *,
        title: str,
        authors: list[str],
        integration_key: str,
        **overrides: Any,
    ) -> "Manifest": ...
```

### `Manifest.load`

**Signature**: `classmethod load(cls, path: Path | str) -> Manifest`

**Behaviour**:
- Reads the file at `path` via `tomlkit.parse(text)`.
- Builds a `Manifest` from the parsed document.
- Compares `cli_version_min` against `bookwright.__version__` using
  PEP 440 ordering (`packaging.version.Version`).
- Classifies `manifest_version`:
  - In `KNOWN_MANIFEST_VERSIONS` → no warning.
  - Strictly greater than `max(KNOWN_MANIFEST_VERSIONS)` → attaches one
    `ManifestWarning(rule_id="manifest_version.unknown_future", ...)`.
- Returns the built `Manifest` with `.warnings` populated (possibly
  empty).

**Forward-compat boundary (v0 — explicit limit)**: "Best-effort load"
for a future `manifest_version` applies to changes in the **value** of
`manifest_version` alone. Adding new keys inside the known blocks
(`[bookwright]`, `[book]`, `[vocabularies]`, `[validators]`,
`[integration]`, `[paths]`) is still a hard validation error under
`extra="forbid"`: each of those block models rejects unknown keys with
rule id `<block>.<key>.unknown_key`, raised *before*
`manifest_version` classification runs. Only **new top-level blocks**
(e.g. an `[experimental]` table) round-trip opaquely, because the root
`Manifest` model is `extra="allow"`. Key-level forward-compat inside
known blocks is not in v0 scope; introducing a new key to a known
block in a future `manifest_version` requires a CLI version that knows
about it. The negative regression test
[tests/core/test_future_version.py::test_unknown_key_in_bookwright_still_raises](../../../tests/core/test_future_version.py)
pins this limit.

**Exceptions**:
- `ManifestNotFoundError` — file at `path` does not exist.
- `ManifestSyntaxError` — file exists but is not valid TOML. Carries
  the tomlkit parser's location (line/column) when available.
- `ManifestValidationError` — any combination of FR-004…FR-013
  failures. Carries the full set of `_FieldFailure` entries (FR-011).
- Other `OSError` subclasses if reading the file fails for I/O reasons
  unrelated to its absence (permission denied, etc.).

**Side effects**: Reads the given file. Does **not** read any other
filesystem path. Does **not** call the network.

**Idempotence**: Calling `load(path)` twice on the same unchanged file
returns equivalent `Manifest` instances; the underlying `tomlkit`
document objects are distinct.

### `Manifest.dump`

**Signature**: `dump(self, path: Path | str, *, overwrite: bool = False) -> Path`

**Behaviour**:
- Atomic write per research §R7 (write to a temp file in
  `path.parent`, `fsync`, `os.replace`).
- Refuses to overwrite an existing file unless `overwrite=True`.
- Returns the resolved absolute path that was written.

**Exceptions**:
- `ManifestOverwriteError` — `path` exists and `overwrite=False`.
- `OSError` subclasses for I/O failures. On any such failure the
  destination at `path` is **guaranteed** to retain its prior contents
  (FR-021).
- `RuntimeError` if called on a `Manifest` instance not produced by
  `Manifest.load(...)` or `Manifest.build(...)` — bare construction
  (e.g. via `Manifest(...)` or `Manifest.model_construct(...)`) leaves
  the underlying `tomlkit` document unset and is not part of the v0
  contract. Supported entry points always attach the document, so this
  exception is unreachable from contract-compliant code.

**Side effects**: Writes one file. Cleans up its own temp file on both
success and failure paths.

**Round-trip guarantee (FR-020, SC-005)**: For any `Manifest` instance
produced by `Manifest.load(p)`,
`Manifest.load(p).dump(q, overwrite=True)` produces a file at `q` whose
contents are byte-identical to the file at `p`.

**Mutation semantics (v0 — explicit limit)**: `dump()` serialises the
underlying `tomlkit` document captured at `load()` or `build()` time,
NOT the current state of the Pydantic model tree. Mutations applied to
the model after construction (e.g. `m.book.title = "new"`,
`m.validators.enabled.append("foo")`) are **not** reflected in the
dumped output. The Pydantic models are not configured `frozen=True`,
so such assignments are syntactically legal but silently dropped on
dump. To change a field and persist it, construct a fresh manifest via
`Manifest.build(...)` with the desired values (or with overrides) and
dump that. Editing the on-disk TOML directly and reloading is also
valid. Direct model mutation followed by `dump()` is not part of the
v0 contract; the regression test
[tests/core/test_write.py::test_dump_ignores_post_load_mutation](../../../tests/core/test_write.py)
pins this behaviour as deliberate.

### `Manifest.build`

**Signature**:
```python
@classmethod
def build(
    cls,
    *,
    title: str,
    authors: list[str],
    integration_key: str,
    **overrides: Any,
) -> "Manifest": ...
```

**Behaviour**:
- Three keyword-only required inputs.
- Accepts keyword overrides for any documented optional field. The
  documented set is (with TOML-side path in parentheses):

  | Override kwarg | Maps to |
  |---|---|
  | `language` | `book.language` |
  | `type` | `book.type` |
  | `subtitle` | `book.subtitle` |
  | `genre` | `book.genre` |
  | `target_length_words` | `book.target_length_words` |
  | `status` | `book.status` |
  | `book_metadata` | `book.metadata` |
  | `vocabularies_active` | `vocabularies.active` |
  | `validators_enabled` | `validators.enabled` |
  | `validators_disabled` | `validators.disabled` |
  | `validators_custom` | `validators.custom` |
  | `paths_manuscript` | `paths.manuscript` |
  | `paths_bible` | `paths.bible` |
  | `paths_outline` | `paths.outline` |
  | `paths_graph` | `paths.graph` |
  | `paths_constitution` | `paths.constitution` |
  | `integration_options` | `integration.options` |
  | `integration_skills_dir` | `integration.skills_dir` (overrides the default mapping from `integration_key`) |
  | `manifest_version` | `bookwright.manifest_version` |
  | `schema_version` | `bookwright.schema_version` |
  | `cli_version_min` | `bookwright.cli_version_min` |
  | `uri_base` | `bookwright.uri_base` |
  | `indexer` | `bookwright.indexer` |

- Unknown `**overrides` keys raise `TypeError` immediately, BEFORE any
  Pydantic object is built (FR-015, spec User Story 4 Scenario 1b).
- Applies the FR-017 defaults for every field not supplied by the
  caller.
- Runs the full validation suite over the resulting object. Validation
  failures (e.g. `language="zz"`, `status="wip"`) raise
  `ManifestValidationError`, NOT `TypeError`.

**Exceptions**:
- `TypeError` — unknown override kwarg, missing required kwarg, or
  wrong-type required kwarg before validation runs.
- `ManifestValidationError` — the merged result fails validation. This
  is the *expected* exception when a caller supplies a syntactically
  legal-but-rule-violating override.

**Note on `uri_base`**: The builder has no default for `uri_base`
(see data-model.md). A `build(...)` call that omits `uri_base=` and
where the integration's defaulting cannot supply one MUST raise
`ManifestValidationError` citing `bookwright.uri_base`. iteration 4's
`init` command will be responsible for prompting / computing a default
before calling `build`.

## Exception JSON shapes (FR-024)

These are the stable shapes a `--json` CLI command will embed in its
JSON envelope. Any future change to a key name is a breaking change.

### `ManifestValidationError.to_json()`

```json
{
  "error": "manifest_validation",
  "failures": [
    {
      "field": "book.authors[0]",
      "value": "",
      "rule": "book.authors.entry.empty",
      "message": "authors[0] must be a non-empty string"
    },
    {
      "field": "bookwright.uri_base",
      "value": "https://example.org",
      "rule": "bookwright.uri_base.no_trailing_slash",
      "message": "uri_base must end with '/'"
    }
  ]
}
```

- `failures` is always a non-empty list (a `ManifestValidationError`
  with zero failures is never raised).
- `field` is a dotted path. List indices use `[N]` notation, e.g.
  `book.authors[2]`.
- `rule` identifiers follow the convention `<field_path>.<short_kind>`
  where `<short_kind>` is one of (non-exhaustive, expanded as needed):
  `missing`, `empty`, `not_a_string`, `not_a_list`, `not_in_enum`,
  `not_iso_639_1`, `entry.empty`, `entry.not_a_string`,
  `not_pep440`, `not_positive_integer_string`, `invalid_uri`,
  `wrong_scheme`, `empty_host`, `has_query`, `has_fragment`,
  `no_trailing_slash`, `installed_too_old`, `parse_failure`,
  `unknown_key` (raised by `extra="forbid"` blocks for keys not in the
  known schema; see the "Forward-compat boundary" paragraph above).

### `ManifestWarning.to_json()`

```json
{
  "rule": "manifest_version.unknown_future",
  "field": "bookwright.manifest_version",
  "value": "9",
  "message": "manifest_version 9 is newer than this CLI knows about (max known: 1); load was best-effort"
}
```

The consuming CLI command collects warnings into a top-level
`warnings: [...]` array inside its JSON envelope (FR-024).

### `ManifestSyntaxError.to_json()`

```json
{
  "error": "manifest_syntax",
  "field": "bookwright.<file>",
  "line": 14,
  "column": 3,
  "message": "expected '=' after key, got newline"
}
```

`line` and `column` may be `null` when tomlkit does not surface them.

### `ManifestNotFoundError.to_json()`

```json
{
  "error": "manifest_not_found",
  "path": "/abs/path/to/manifest.toml",
  "message": "no manifest at /abs/path/to/manifest.toml"
}
```

### `ManifestOverwriteError.to_json()`

```json
{
  "error": "manifest_overwrite_refused",
  "path": "/abs/path/to/manifest.toml",
  "message": "refuse to overwrite existing manifest at /abs/path/to/manifest.toml (pass overwrite=True to force)"
}
```

## Stability

- The signatures, exception types, and JSON keys above are the stable
  contract for v0.
- Adding new keys to a JSON shape is **non-breaking** if existing keys
  retain their meaning. New `rule` identifiers may be added at any
  time; consumers MUST treat unknown `rule` values as opaque strings.
- Renaming or removing a key, narrowing a value's domain, or changing
  the parent class of an exception is **breaking** and requires the
  process noted at the top of this file.
