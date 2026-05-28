# Phase 1 Data Model: Manifest Model

**Feature**: 002-manifest-model
**Date**: 2026-05-28

This is the schema the implementation MUST match. It is grounded in
`bookwright-design.md § 8.1` (the canonical manifest TOML) and the
acceptance criteria from `spec.md`. Field names are exactly the TOML
keys (snake_case). Pydantic v2 idioms are noted in parentheses where
they materially affect implementation.

## Entity tree

```text
Manifest                       (Pydantic BaseModel; root)
├─ bookwright: BookwrightBlock
├─ book: BookBlock
│   └─ metadata: dict[str, Any]      # free-form, opaque (FR-003)
├─ vocabularies: VocabulariesBlock
├─ validators: ValidatorsBlock
├─ integration: IntegrationBlock    # data only, never dispatched on (FR-022)
├─ paths: PathsBlock
└─ warnings: tuple[ManifestWarning, ...]   # attached on load, NOT serialised
```

`Manifest.warnings` is a non-TOML attribute populated during `load()`; it is
not written back out by `dump()`. Round-tripping (FR-020) compares the TOML
file contents, not the warning list.

## Top-level entity: `Manifest`

### Pydantic config

- `model_config = ConfigDict(extra="allow", strict=True)` at the
  `Manifest` level so unknown top-level keys (e.g. a future
  `[experimental]` block) round-trip unmodified per FR-003.
- Per-block models use `extra="allow"` for `[book.metadata]` and
  `[integration.options]` (the two explicitly free-form maps), and
  `extra="forbid"` everywhere else so unknown keys inside a *known*
  block are caught as errors rather than silently discarded.
- Strict mode (`strict=True`) prevents type coercion (e.g. integer
  passed for a string field is a failure, not a silent str-cast). This
  matches FR-004…FR-010, which all demand "is a string" as part of the
  rule.

### Public API

| Member | Signature | Notes |
|---|---|---|
| `Manifest.load` | `classmethod (cls, path: Path \| str) -> Manifest` | Reads file via `tomlkit`, builds `Manifest`, accumulates warnings, raises on validation failure. |
| `Manifest.dump` | `(self, path: Path \| str, *, overwrite: bool = False) -> Path` | Atomic write (R7). Returns the resolved absolute path. |
| `Manifest.build` | `classmethod (cls, *, title: str, authors: list[str], integration_key: str, **overrides: Any) -> Manifest` | FR-015 builder. Unknown overrides raise `TypeError`. |
| `Manifest.warnings` | `tuple[ManifestWarning, ...]` | Frozen tuple; empty on a clean load. |
| `Manifest._document` | `tomlkit.TOMLDocument` (private) | The underlying `tomlkit` document used for round-trip and for `dump()`. Not part of the public API. |

## Block: `BookwrightBlock`

Maps to TOML `[bookwright]`. All four members are required (FR-010).

| Field | Type | Required | Validation rule | Default (FR-017) |
|---|---|---|---|---|
| `cli_version_min` | `str` | yes | Must parse as `packaging.version.Version`; compared against installed CLI (`bookwright.__version__`) using PEP 440 ordering. Load fails if installed < required (FR-012). | The installed CLI's `__version__` at build time. |
| `schema_version` | `str` | yes | Must be a non-empty string. No further structural check in v0; serves as a stamp for the GOLEM schema generation. | `"golem-1.0"` |
| `manifest_version` | `str` | yes | Regex `^[1-9][0-9]*$` (R6). Compared as `int` to `KNOWN_MANIFEST_VERSIONS` (`frozenset({1})` today). | `"1"` |
| `uri_base` | `str` | yes | `http`/`https` scheme, non-empty host, no query, no fragment, trailing `/` (R5; FR-008). | (no default — must be supplied by builder caller) |
| `indexer` | `str` | no | Free-form string in v0; design doc § 8.1 reserves `"rdflib"` as the only supported value, but the model layer does NOT enforce that — the indexer registry (iteration 6) does. | `"rdflib"` |

**Note on `uri_base` default**: The builder (FR-015) does **not** invent
a `uri_base` from `title`. If the caller does not pass `uri_base=`,
construction fails with a field-precise validation error citing the
missing required field. This keeps the model honest: the manifest
contract has no opinion on what the project's namespace should be.

## Block: `BookBlock`

Maps to TOML `[book]`.

| Field | Type | Required | Validation rule | Default (FR-017) |
|---|---|---|---|---|
| `title` | `str` | yes | Non-empty after `strip()` (FR-004). | (no default — required builder input) |
| `type` | `Literal["novel", "essay", "memoir", "non-fiction-narrative", "other"]` | yes | Pydantic `Literal` does this for free (FR-005). | `"novel"` |
| `language` | `str` | yes | Lowercase two-letter code; membership in `ISO_639_1_CODES` (R3; FR-006). | `"en"` |
| `authors` | `list[str]` | yes | Non-empty list; each element non-empty after `strip()` (FR-007). Duplicates allowed (Edge Cases). | (no default — required builder input) |
| `subtitle` | `str` | no | Free-form. Empty string allowed. | `""` |
| `genre` | `list[str]` | no | Free-form. Empty list allowed. | `[]` |
| `target_length_words` | `int \| None` | no | Positive integer when present. | `None` |
| `status` | `Literal["idea", "structuring", "drafting", "revising", "done"]` | no (defaults applied) | Pydantic `Literal` (FR-009). | `"drafting"` |
| `metadata` | `dict[str, Any]` | no | Opaque (FR-003); preserved verbatim. | `{}` |

`[book.metadata]` is the only sub-block under `[book]`. Pydantic models
it as a plain `dict[str, Any]` with `extra="allow"` so arbitrary keys
round-trip.

## Block: `VocabulariesBlock`

Maps to TOML `[vocabularies]`.

| Field | Type | Required | Validation rule | Default (FR-017) |
|---|---|---|---|---|
| `active` | `list[str]` | no | List of vocabulary names. Empty list allowed (Edge Cases). **No filesystem check** in this iteration (FR-023). | `[]` |

## Block: `ValidatorsBlock`

Maps to TOML `[validators]`.

| Field | Type | Required | Validation rule | Default (FR-017) |
|---|---|---|---|---|
| `enabled` | `list[str]` | no | List of built-in validator names. No registry check in this iteration. | `[]` |
| `disabled` | `list[str]` | no | Same. | `[]` |
| `custom` | `list[str]` | no | Names resolved against `.bookwright/validators/` by downstream code, not here. | `[]` |

## Block: `IntegrationBlock`

Maps to TOML `[integration]`. Per FR-022 this is **data only**: the
manifest loader MUST NOT consult this block to resolve any path or
behaviour.

| Field | Type | Required | Validation rule | Default (FR-017) |
|---|---|---|---|---|
| `key` | `str` | yes | Non-empty string. The model does NOT check against the integration registry (that's iteration 3's job and would create a circular dep). | (no default — required builder input) |
| `skills_dir` | `str` | yes | Non-empty string. The builder fills it from `integration_key`: `claude` → `.claude/skills`, `generic` → `.agents/skills`. Other keys: the builder raises a programming-error if the caller did not supply `skills_dir` explicitly. | (computed from `integration_key`; see FR-017) |
| `options` | `dict[str, Any]` | no | Opaque (FR-003); preserved verbatim. | `{}` |

## Block: `PathsBlock`

Maps to TOML `[paths]`.

| Field | Type | Required | Validation rule | Default (FR-017) |
|---|---|---|---|---|
| `manuscript` | `str` | no | Non-empty string. No filesystem check. | `"manuscript/"` |
| `bible` | `str` | no | Non-empty string. No filesystem check. | `"bible/"` |
| `outline` | `str` | no | Non-empty string. No filesystem check. | `"outline/"` |
| `graph` | `str` | no | Non-empty string. No filesystem check. | `"bible/graph.ttl"` |
| `constitution` | `str` | no | Non-empty string. No filesystem check. | `"bible/constitution.md"` |

## Supporting entities

### `ManifestVersion` (R6)

Not a class — encoded as the `manifest_version: str` field plus the
module-level `KNOWN_MANIFEST_VERSIONS: frozenset[int] = frozenset({1})`.
Helper functions:

- `_parse_manifest_version(raw: str) -> int` — applies the
  `^[1-9][0-9]*$` regex, raises a Pydantic-friendly error otherwise.
- `_classify_manifest_version(parsed: int) -> Literal["known", "future"]`
  — single source of truth for FR-013 vs FR-014.

### `CliVersionFloor` (R4)

Not a class — encoded as the `cli_version_min: str` field plus a single
model-level validator that:

1. Parses both `cli_version_min` and `bookwright.__version__` with
   `packaging.version.Version`. Either parse failure on the manifest's
   side is a validation error citing `bookwright.cli_version_min`.
2. Compares `installed < required` and raises a validation error citing
   both versions if so (FR-012).

The installed version is read from `bookwright.__version__`. Tests can
monkey-patch this via `bookwright.core.manifest._installed_version()`
(a thin indirection helper) to simulate older/newer CLIs.

### `IntegrationRecord` (spec § Key Entities)

Not a separate class. Aliased to `IntegrationBlock` for the spec's
benefit — the recorded integration metadata (`key`, `skills_dir`,
`options`) lives inside the block and is round-tripped verbatim
(FR-022).

### `ManifestError` hierarchy (errors.py)

```text
ManifestError                      # base; everything below is an instance
├─ ManifestNotFoundError           # FR-002 (file missing)
├─ ManifestSyntaxError             # FR-002 (invalid TOML; carries .line/.column when tomlkit provides them)
├─ ManifestValidationError         # FR-004–FR-013 (one or more field failures)
└─ ManifestOverwriteError          # FR-019 (refuse to overwrite without flag)
```

`ManifestValidationError.failures: tuple[_FieldFailure, ...]` where each
`_FieldFailure` is:

```python
@dataclass(frozen=True)
class _FieldFailure:
    field_path: str            # "book.authors[0]"
    rejected_value: Any        # what the user wrote (post-TOML-parse)
    rule_id: str               # "book.authors.entry.empty"
    message: str               # human-readable
```

`ManifestValidationError.to_json() -> dict[str, Any]` returns:

```json
{
  "error": "manifest_validation",
  "failures": [
    {
      "field": "book.authors[0]",
      "value": "",
      "rule": "book.authors.entry.empty",
      "message": "authors[0] must be a non-empty string"
    }
  ]
}
```

This shape is the FR-024 contract: a future `--json`-aware CLI command
(iteration 4 `init` is the first) emits this dict directly inside its
JSON envelope under an `error` key.

### `ManifestWarning`

```python
class ManifestWarning(BaseModel):
    rule_id: str               # e.g. "manifest_version.unknown_future"
    field_path: str            # e.g. "bookwright.manifest_version"
    offending_value: Any       # e.g. "9"
    message: str               # human-readable

    def to_json(self) -> dict[str, Any]: ...
```

`Manifest.warnings` is `tuple[ManifestWarning, ...]`. The JSON form per
FR-024 is `{"rule": ..., "field": ..., "value": ..., "message": ...}`,
collected into a `warnings: [...]` array by the consuming CLI command.

## Module-level constants

| Constant | Type | Value | Source |
|---|---|---|---|
| `ISO_639_1_CODES` | `frozenset[str]` | 184 two-letter lowercase codes | `core/iso639_1.py` |
| `KNOWN_MANIFEST_VERSIONS` | `frozenset[int]` | `frozenset({1})` | `core/manifest.py` (top-level) |
| `BOOK_TYPES` | `frozenset[str]` | `{"novel", "essay", "memoir", "non-fiction-narrative", "other"}` | `core/manifest.py` (used inside the `Literal`; also re-exported for callers that need the rejected-value error message) |
| `BOOK_STATUSES` | `frozenset[str]` | `{"idea", "structuring", "drafting", "revising", "done"}` | `core/manifest.py` |
| `DEFAULT_SKILLS_DIR` | `dict[str, str]` | `{"claude": ".claude/skills", "generic": ".agents/skills"}` | `core/manifest.py` (used only by `Manifest.build`) |

## State diagram: `Manifest.load`

```text
file_path
   │
   ▼
[exists?] ──no──► raise ManifestNotFoundError (FR-002)
   │ yes
   ▼
tomlkit.parse(text)
   │ syntax error
   ├─────────────► raise ManifestSyntaxError (FR-002)
   ▼ ok
build Pydantic Manifest
   │ collected ValidationError
   ├─────────────► raise ManifestValidationError (FR-004…FR-013, FR-011)
   ▼ ok
classify manifest_version
   │
   ├─── known  ───────────────────────► attach no warning
   └─── future ───────────────────────► attach ManifestWarning(rule_id="manifest_version.unknown_future")
   ▼
return Manifest(  ..., warnings=tuple(collected_warnings))
```

## State diagram: `Manifest.build`

```text
build(title=, authors=, integration_key=, **overrides)
   │
   ▼
validate kwargs against known optional-field allowlist
   │ unknown kwarg
   ├──────────► raise TypeError (FR-015)
   ▼ ok
load template TOMLDocument (R8)
   │
   ▼
fill required values from the three positional kwargs +
fill defaults from FR-017 +
overlay overrides
   │
   ▼
re-parse the resulting document through the Pydantic model
   │ collected ValidationError
   ├──────────► raise ManifestValidationError (FR-016 second sentence:
   │            "When caller overrides are supplied, the builder MUST
   │             validate the merged result and surface validation failures")
   ▼ ok
return Manifest(...) with the freshly-built _document attached
```

## State diagram: `Manifest.dump`

```text
dump(path, overwrite=False)
   │
   ▼
[path exists AND not overwrite] ──► raise ManifestOverwriteError (FR-019)
   │
   ▼
open tempfile in path.parent
   │
   ▼
write tomlkit.dumps(self._document) → flush → fsync
   │ I/O error
   ├──────────────────────► clean up temp file, re-raise
   ▼ ok
os.replace(temp_path, path)              (atomic; FR-021)
   │
   ▼
return path.resolve()
```

## Coverage map: requirements → entities

| FR | Touches |
|---|---|
| FR-001 | `Manifest.load`, all block models |
| FR-002 | `ManifestNotFoundError`, `ManifestSyntaxError` |
| FR-003 | `Manifest` top-level `extra="allow"`, `BookBlock.metadata`, `IntegrationBlock.options` |
| FR-004 | `BookBlock.title` validator |
| FR-005 | `BookBlock.type` `Literal` |
| FR-006 | `BookBlock.language` validator + `ISO_639_1_CODES` |
| FR-007 | `BookBlock.authors` validator |
| FR-008 | `BookwrightBlock.uri_base` validator (R5) |
| FR-009 | `BookBlock.status` `Literal` + default |
| FR-010 | Per-field `required=True` on `BookwrightBlock` |
| FR-011 | Pydantic v2 multi-error accumulation (R2) |
| FR-012 | `BookwrightBlock.cli_version_min` validator + `_installed_version()` |
| FR-013 | `BookwrightBlock.manifest_version` parser + `_classify_manifest_version` + `ManifestWarning` |
| FR-014 | Same path as FR-013, "known" branch |
| FR-015 | `Manifest.build` |
| FR-016 | `Manifest.build` post-validation re-parse |
| FR-017 | FR-017 defaults table above + `DEFAULT_SKILLS_DIR` + template TOML |
| FR-018 | `tomlkit` round-trip + template-driven construction |
| FR-019 | `Manifest.dump(..., overwrite=False)` + `ManifestOverwriteError` |
| FR-020 | `tomlkit` round-trip property |
| FR-021 | Atomic write recipe (R7) |
| FR-022 | `IntegrationBlock` is read/written as data; no callers in this iteration consult it for path resolution |
| FR-023 | `VocabulariesBlock.active` has no filesystem check |
| FR-024 | `ManifestValidationError.to_json`, `ManifestWarning.to_json` |
