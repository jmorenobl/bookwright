# Contract: Canonical Error Envelope

The single JSON-over-stdout error shape (Principle IX) emitted by **every**
Bookwright error after this iteration. Produced by exactly one method:
`BookwrightError.to_json()` in `src/bookwright/errors.py`.

## Envelope schema

```json
{
  "status": "error",
  "code": "<machine_readable_identifier>",
  "message": "<human readable string>",
  "details": { "<field>": "<value>" }
}
```

- `status` — always the literal string `"error"`.
- `code` — stable snake_case identifier (the effective `self.code`).
- `message` — human-readable summary (`str(exc)`).
- `details` — object of error-specific fields. **Present only when non-empty**;
  omitted entirely (not `null`, not `{}`) when the error carries no extra fields.
- Key order is `status, code, message[, details]`.

This document is the authoritative registry; per-module contracts
(`specs/002-manifest-model/contracts/manifest_api.md`,
`specs/003-integration-architecture/contracts/integrations_api.md`,
`specs/005-golem-domain-model/contracts/golem_api.md`,
`specs/010-validation-system/contracts/cli-validate.md`, and the
data-model § 6 error sections) defer to it for the envelope shape.

## Error registry (code → details)

### Already-canonical — byte-identical to `main` (FR-004)

| `code` | Class | `details` keys |
|---|---|---|
| `not_a_project` | `io.ProjectNotFoundError` | `start` |
| `missing_directory` | `io.MissingDirectoryError` | `name`, `path` |
| `invalid_frontmatter` | `io.InvalidFrontmatterError` | `path`, `reason` |
| `invalid_research` | `io.ResearchError` | `relpath`, `value` |
| `slug_collision` | `io.SlugCollisionError` | `identifier`, `sources` |
| `unknown_indexer` | `indexers.UnknownIndexerError` | `name`, `available` |
| `graph_not_built` | `indexers.GraphNotBuiltError` | `path` |
| `graph_load_failed` | `indexers.GraphLoadError` | `path`, `reason` |
| `invalid_query` | `indexers.InvalidQueryError` | `reason` |
| `unknown_validator` | `validation.UnknownValidatorError` | `names` |
| `no_project` | `commands.validate._UsageError` | `start` |
| `invalid_manifest` | `commands.validate._UsageError` | *(none — `details` omitted)* |
| `unknown_validator` | `commands.validate._UsageError` | `names` |
| `empty_scope` | `commands.validate._UsageError` | *(none — `details` omitted)* |

### Normalized this iteration — flat shape → canonical envelope (FR-005/006)

| `code` | Class | Former flat body | New `details` keys |
|---|---|---|---|
| `manifest_not_found` | `core.ManifestNotFoundError` | `{error, path, message}` | `path` |
| `manifest_syntax` | `core.ManifestSyntaxError` | `{error, field, line, column, message}` | `field`, `line`, `column` |
| `manifest_validation` | `core.ManifestValidationError` | `{error, failures}` (no `message`) | `failures` (+ top-level `message` newly present) |
| `manifest_overwrite_refused` | `core.ManifestOverwriteError` | `{error, path, message}` | `path` |
| `golem_empty_slug` | `golem.EmptySlugError` | `{error, name, message}` | `name` |

> Migration rule: the former `"error"` value becomes `code` verbatim; the human
> `message` is preserved; all other former top-level fields move under `details`.
> `manifest_validation` is the only error that gains a top-level `message` (its
> existing summary string) — required by the canonical envelope.

### Integrations hierarchy — `to_dict()` deleted, attributes → `details` (FR-005a)

`_IntegrationError` previously owned a separate serializer (`to_dict()` →
`{code, message, **attrs}`). It is migrated onto `BookwrightError`; the public
attributes move under `details`. Codes are preserved verbatim.

| `code` | Class | `details` keys | `integration use --json` | `init --json` |
|---|---|---|---|---|
| `unknown_integration` | `UnknownIntegrationError` | `value`, `valid` | **shape change** (attrs → `details`) | byte-identical |
| `unknown_option` | `UnknownOptionError` | `integration`, `value`, `valid` | — | byte-identical |
| `malformed_option` | `MalformedOptionError` | `rule`, `value` | — | byte-identical |
| `duplicate_registration` | `DuplicateRegistrationError` | `value`, `existing`, `new` | — | — (registry-time) |
| `invalid_option_declaration` | `InvalidOptionDeclarationError` | `rule`, `value` | — | byte-identical |
| `invalid_integration` | `InvalidIntegrationError` | `rule`, `value` | — | — (registry-time) |
| `skill_lint_failed` | `SkillLintError` | `skill`, `rule`, `detail` | **shape change** (attrs → `details`) | — |
| `skill_materialization_failed` | `SkillMaterializationError` | `skill`, `rule`, `detail` | **shape change** (attrs → `details`) | — |

### `init` bare error — now owns its body (FR-005b)

| `code` | Class | `details` keys | Note |
|---|---|---|---|
| `invalid_project_name` | `commands.init.validate.InvalidProjectNameError` | `value`, `rule` | byte-identical; was a bare `Exception` whose body `init` hand-built |

### Sanctioned command superset — `init` (FR-005c)

`init`'s error envelope is the canonical body **plus** two command-level fields:

```json
{"status":"error","code":"…","message":"…","details":{…},"rolled_back":false,"bookwright_version":"0.2.0"}
```

This is the one writer that extends the body. It is sanctioned because `code`,
`message`, and `details` still come from `BookwrightError` (the body is not
redefined); `rolled_back`/`bookwright_version` are init's rollback-ledger
reporting, not part of the shared envelope.

## Examples (normalized cases)

`ManifestNotFoundError`:

```json
{"status":"error","code":"manifest_not_found","message":"no manifest at /p/manifest.toml","details":{"path":"/p/manifest.toml"}}
```

`ManifestValidationError` (note the newly-present top-level `message`):

```json
{"status":"error","code":"manifest_validation","message":"2 validation failure(s); first: book.language: ...","details":{"failures":[{"field":"book.language","value":"zz","rule":"...","message":"..."}]}}
```

`EmptySlugError`:

```json
{"status":"error","code":"golem_empty_slug","message":"name '!!!' slugifies to an empty string","details":{"name":"!!!"}}
```

## Invariants the contract enforces

- Exactly one envelope serializer exists across the codebase — `to_json()` on
  `BookwrightError`; no error class defines `to_json()` **or `to_dict()`** (SC-001).
- Every serialized exception subclasses `BookwrightError` (all eight origins) (SC-002).
- No legacy flat `{"error": …}` body remains, and no error spreads its fields at
  the envelope top level (SC-003).
- `code`/`message`/exit codes unchanged vs `main` (SC-004).
- A single edit to `BookwrightError.to_json()` changes the envelope for all
  errors at once (SC-006).
