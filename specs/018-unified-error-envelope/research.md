# Phase 0 Research: Unified Error Envelope

All NEEDS CLARIFICATION items were resolved by the spec's 2026-06-05
clarification session; this document records the resulting engineering decisions.

## Decision 1 — Module location: root `src/bookwright/errors.py`

**Decision**: Place `BookwrightError` in a new top-level module
`src/bookwright/errors.py` (no subpackage).

**Rationale**: It must be importable by `core`, `golem`, `io`, `indexers`,
`validation`, and `commands` while importing **none** of them (FR-010). The
package root is the unique layer below all six. The base needs only stdlib
(`typing`, `json` is not even required — `to_json()` returns a `dict`), so it has
zero intra-package dependencies and a cycle is structurally impossible.

**Alternatives considered**:
- `core/errors.py` (reuse an existing module): rejected — `core` is a sibling
  layer, and `golem`/`io`/`indexers` importing from `core` to reach the base
  would couple them to the manifest package and risk a cycle (`validation`
  already imports `core.manifest`).
- A `_internal/` or `common/` package: rejected as ceremony; a single root
  module is the smallest thing that works and matches the repo's flat layering.

## Decision 2 — `code` is a plain class attribute, NOT `ClassVar` (mypy-driven)

**Decision**: Declare the error identifier on the base as a plain class
attribute annotation `code: str` (no value). Concrete subclasses assign it at
class scope (`code = "unknown_indexer"`); `_UsageError` assigns it per instance
(`self.code = code`). The base's `to_json()` reads the **effective** `self.code`.

**Rationale**: The technical hint literally proposed `code: ClassVar[str]`, but
clarification Q2 requires that `_UsageError` remain **one** class that sets a
different `code` per instance (`no_project` / `invalid_manifest` /
`unknown_validator` / `empty_scope`). Under `mypy --strict`, assigning to a
`ClassVar` through an instance (`self.code = …`) is a hard error
("Cannot assign to class variable via instance"). `ClassVar` and the
clarified per-instance override are therefore mutually exclusive. FR-002's own
normative wording resolves the tension — it calls `code` "a class-level
attribute that a subclass MAY override per instance via `self.code`", which is
exactly a plain (non-`ClassVar`) class attribute. So the base uses `code: str`.
This is a deliberate, clarification-driven correction of the literal hint, not a
divergence from intent: subclasses still declare `code` at class level (the
"default"), and instances may still override it.

**Consequence for abstract roots**: `ManifestError`, `IOError_`, `IndexerError`,
`GolemError` declare **no** `code`. The annotation-only `code: str` on the base
means accessing `self.code` on a never-assigned instance raises `AttributeError`
at runtime — acceptable because those roots are abstract and never serialized
(FR-015, edge case "Non-serialized exceptions"). mypy does not require the
annotation to have a value, so no dummy code is forced onto structural parents.

**Alternatives considered**:
- Keep `ClassVar[str]` and split `_UsageError` into four subclasses: rejected by
  clarification Q2 (explicitly "no splitting into per-code subclasses").
- Keep `ClassVar[str]` and give `_UsageError` a separate `to_json()`: rejected —
  re-introduces the duplicate serialization this feature removes (FR-003).
- A `# type: ignore` on `self.code`: rejected — silences a real type signal and
  violates the project's clean-`mypy --strict` discipline.

## Decision 3 — Base `__init__(message, details=None)`; subclasses delegate

**Decision**: The base provides
`__init__(self, message: str, details: dict[str, Any] | None = None)` that sets
`self.message`, `self.details`, and calls `super().__init__(message)` (so
`str(exc)` is unchanged). Each concrete subclass keeps its own `__init__` for
domain-specific attributes (`self.path`, `self.start`, `self.names`, …) and ends
by calling `super().__init__(<message>, <details-dict>)`, dropping the now
redundant `self.message = message` line.

**Rationale**: Centralizing `message`/`details` storage in the base is what lets
`to_json()` be the single source of truth. Subclasses still own their
construction logic and public attributes (preserved verbatim — e.g.
`commands/validate.py` reads `exc.start`, `exc.names`), so no call site changes.

## Decision 4 — `details` omitted when empty/falsy (uniform)

**Decision**: `to_json()` adds the `"details"` key **only** when `self.details`
is truthy (non-empty dict). It builds `{"status":"error","code":…,"message":…}`
first, then conditionally appends `"details"`.

**Rationale**: This exactly reproduces the existing behavior of all four
canonical hierarchies (every one writes `details` from a populated dict) and of
`_UsageError` (`if self.details:` with `details or {}`), so their JSON is
byte-identical (FR-004, SC-005). Key insertion order
(`status, code, message, details`) matches the current dict literals, so even
ordered/serialized comparisons are unchanged. Edge case "Empty vs. populated
`details`" (spec) is satisfied uniformly for every error including the newly
normalized ones.

## Decision 5 — Flat → canonical normalization map (lossless)

**Decision**: For the two legacy flat hierarchies, the former `"error"` value
becomes `code` (verbatim), the human `message` is preserved, and every remaining
flat field moves under `details`:

| Class | Former flat body | Canonical `code` | Canonical `details` | Note |
|---|---|---|---|---|
| `ManifestNotFoundError` | `{error, path, message}` | `manifest_not_found` | `{"path": …}` | |
| `ManifestSyntaxError` | `{error, field, line, column, message}` | `manifest_syntax` | `{"field":…,"line":…,"column":…}` | `line`/`column` may be `null` |
| `ManifestValidationError` | `{error, failures}` (no `message`) | `manifest_validation` | `{"failures":[…]}` | **top-level `message` newly appears** (the existing summary string) — intended (spec edge case) |
| `ManifestOverwriteError` | `{error, path, message}` | `manifest_overwrite_refused` | `{"path": …}` | |
| `EmptySlugError` | `{error, name, message}` | `golem_empty_slug` | `{"name": …}` | |

**Rationale**: Lossless in meaning (FR-006): codes, messages, and the per-field
data all survive; only the JSON layout changes. `ManifestValidationError` is the
single case gaining a top-level `message` (it had none in the flat shape); this
is the canonical envelope's required field and the spec calls it out explicitly.

## Decision 6 — Preserve per-package roots as abstract intermediates

**Decision**: `ManifestError`, `IOError_`, `IndexerError`, `GolemError` keep
their names and bodies but change their base from `Exception` to
`BookwrightError`. They declare no `code` and define no `to_json()`.

**Rationale**: Clarification Q3 + FR-015. The five `except <PackageError>` catch
sites (`commands/integration/use.py`, `commands/graph/build.py`,
`commands/graph/query.py`, `commands/validate.py`) keep matching unchanged
(SC-008: zero catch-site edits). The two-level hierarchy
(`BookwrightError → <PackageError> → concrete`) is preserved.

## Decision 7 — Out-of-scope payloads stay put

**Decision**: Do not route `ManifestWarning` (a `pydantic.BaseModel` with its own
`to_json()`), `Violation`, `ValidatorError`, or the success-envelope builders
(`io/report.py`, `validation/report.py`) through the base. They are not error
exceptions and keep their existing serialization.

**Rationale**: FR-012. They are `status:"ok"` envelopes or finding payloads, not
the error envelope; conflating them would expand scope and break their shapes.

## Safety net (existing tests, mostly unchanged)

- **Updated** (flat → canonical assertions): `tests/core/test_json_shapes.py`
  (4 manifest error tests), `tests/golem/test_slug.py` (the `EmptySlugError`
  assertion at line 49).
- **Unchanged, must still pass** (byte-identical canonical output):
  `tests/indexers/test_query_errors.py`, `tests/validation/test_base.py`,
  `tests/validation/test_command.py`, and the `io` error tests. These are the
  regression guardrail for FR-004 / SC-005.
- A new focused test asserts SC-006 (one representative error per former
  hierarchy serializes through the base's single `to_json()` — verifiable by the
  absence of a per-class override and a well-formed envelope from each).
