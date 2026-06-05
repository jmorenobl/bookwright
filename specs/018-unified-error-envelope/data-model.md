# Phase 1 Data Model: Unified Error Envelope

## `BookwrightError` (the shared base)

A plain `Exception` subclass in `src/bookwright/errors.py`. The single owner of
the canonical error-envelope serialization.

| Member | Kind | Type | Notes |
|---|---|---|---|
| `code` | class attribute (annotation-only on base) | `str` | The stable machine-readable identifier. Concrete subclasses assign it at class scope; `_UsageError` assigns `self.code` per instance. Abstract roots leave it unset. **Not** `ClassVar` (would forbid the per-instance override — see research Decision 2). |
| `message` | instance attribute | `str` | Human-readable; set by `__init__`. Also passed to `Exception.__init__` so `str(exc)` is unchanged. |
| `details` | instance attribute | `dict[str, Any] \| None` | Error-specific fields; `None`/empty ⇒ omitted from JSON. |
| `__init__(message, details=None)` | method | — | Sets `message`/`details`, calls `super().__init__(message)`. |
| `to_json()` | method | `dict[str, Any]` | The **one** envelope builder (see contract). |

### Reference implementation (target)

```python
"""The shared error base — the single source of truth for the JSON-over-stdout
error envelope (Principle IX, review finding R3)."""

from __future__ import annotations

from typing import Any


class BookwrightError(Exception):
    """Base for every Bookwright error that reaches a ``--json`` boundary.

    Subclasses declare a class-level ``code`` (the machine-readable identifier),
    pass a human ``message`` and optional ``details`` to ``__init__``, and inherit
    the one canonical ``to_json()``. A subclass MAY set ``self.code`` per instance
    (``_UsageError``). Abstract package roots leave ``code`` unset and are never
    serialized.
    """

    code: str  # class-level default; subclasses assign it (or set self.code).

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)

    def to_json(self) -> dict[str, Any]:
        """The canonical error envelope; ``details`` only when non-empty."""
        payload: dict[str, Any] = {
            "status": "error",
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload
```

## Hierarchy after migration (two levels under the base)

```text
BookwrightError                       (src/bookwright/errors.py — the only to_json)
├── ManifestError                     (core/errors.py — abstract, no code, no to_json)
│   ├── ManifestNotFoundError         code="manifest_not_found"        details={path}
│   ├── ManifestSyntaxError           code="manifest_syntax"           details={field,line,column}
│   ├── ManifestValidationError       code="manifest_validation"       details={failures}
│   └── ManifestOverwriteError        code="manifest_overwrite_refused" details={path}
├── GolemError                        (golem/errors.py — abstract, no code, no to_json)
│   └── EmptySlugError                code="golem_empty_slug"          details={name}
├── IOError_                          (io/errors.py — abstract, no code, no to_json)
│   ├── ProjectNotFoundError          code="not_a_project"             details={start}
│   ├── MissingDirectoryError         code="missing_directory"         details={name,path}
│   ├── InvalidFrontmatterError       code="invalid_frontmatter"       details={path,reason}
│   ├── ResearchError                 code="invalid_research"          details={relpath,value}
│   └── SlugCollisionError            code="slug_collision"            details={identifier,sources}
├── IndexerError                      (indexers/errors.py — abstract, no code, no to_json)
│   ├── UnknownIndexerError           code="unknown_indexer"           details={name,available}
│   ├── GraphNotBuiltError            code="graph_not_built"           details={path}
│   ├── GraphLoadError                code="graph_load_failed"         details={path,reason}
│   └── InvalidQueryError             code="invalid_query"             details={reason}
├── UnknownValidatorError             (validation/base.py — code="unknown_validator" details={names})
├── _UsageError                       (commands/validate.py — per-instance self.code, see below)
├── _IntegrationError                 (integrations/errors.py — abstract, no code, no to_json/to_dict)
│   ├── UnknownIntegrationError       code="unknown_integration"          details={value,valid}
│   ├── UnknownOptionError            code="unknown_option"               details={integration,value,valid}
│   ├── MalformedOptionError          code="malformed_option"             details={rule,value}
│   ├── DuplicateRegistrationError    code="duplicate_registration"       details={value,existing,new}
│   ├── InvalidOptionDeclarationError code="invalid_option_declaration"   details={rule,value}
│   ├── InvalidIntegrationError       code="invalid_integration"          details={rule,value}
│   ├── SkillLintError                code="skill_lint_failed"            details={skill,rule,detail}
│   └── SkillMaterializationError     code="skill_materialization_failed" details={skill,rule,detail}
└── InvalidProjectNameError           (commands/init/validate.py — code="invalid_project_name" details={value,rule})
```

`_UsageError` is a single class whose `code` is set per instance to one of
`no_project` (`details={start}`), `invalid_manifest` (no details),
`unknown_validator` (`details={names}`), or `empty_scope` (no details).

## State / behavior

Errors are immutable value-carrying exceptions: constructed, optionally caught at
a `except <PackageError>` site, then serialized once via `to_json()` at the
`--json` boundary. No state transitions.

## Out of scope (unchanged, NOT under the base)

| Type | Location | Why excluded |
|---|---|---|
| `ManifestWarning` | `core/errors.py` | A `pydantic.BaseModel` warning payload, not an error exception (FR-012). |
| `Violation` | `validation/base.py` | Finding payload, own contract shape. |
| `ValidatorError` | `validation/base.py` | Finding payload (report `errors[]`), own shape. |
| Success envelopes | `io/report.py`, `validation/report.py` | `status:"ok"` envelopes, not errors. |

## Invariants

- **INV-1**: No concrete error class defines `to_json()` **or `to_dict()`** —
  exactly one envelope serializer exists (on `BookwrightError`). (SC-001)
- **INV-2**: Every JSON-serialized exception is a `BookwrightError` subclass.
  (SC-002)
- **INV-3**: `code` strings, `message` strings, and command exit codes are
  identical to `main`. (SC-004)
- **INV-4**: `src/bookwright/errors.py` imports nothing from
  `core/golem/io/indexers/validation/integrations/commands`. (FR-010)
- **INV-5**: No `except <PackageError>` / `except <ConcreteError>` site is
  edited. (SC-008)
- **INV-6**: Command boundary writers source the error body (`status/code/
  message/details`) from `BookwrightError`; the only envelope that extends the
  body with top-level fields is `init`'s (`rolled_back`, `bookwright_version`),
  explicitly sanctioned (Decision 9). No writer hand-reads error attributes or
  calls a deleted `to_dict()`. (FR-005c, SC-003)
