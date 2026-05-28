# Phase 0 Research: Manifest Model

**Feature**: 002-manifest-model
**Date**: 2026-05-28
**Status**: Complete — all `NEEDS CLARIFICATION` items in the spec were
resolved during `/speckit-clarify`; the open technical questions below
remained for `/speckit-plan` and are now decided.

This document records the design decisions that the implementation MUST
follow. Each entry lists the **Decision**, **Rationale**, and
**Alternatives considered**. Tasks (Phase 2) will reference these by
heading.

---

## R1. TOML reader/writer library

**Decision**: Use `tomlkit` for both read and write. Do **not** introduce
`tomli` or `tomli_w`.

**Rationale**:
- `tomlkit` is already pinned in `pyproject.toml` from iteration 1
  (`tomlkit>=0.12`) and is the only TOML library the constitution lists.
- It preserves comments, blank lines, and original key order on
  round-trip, which is exactly what FR-018, FR-020, and SC-005 require
  ("a manifest loaded from disk and written back without modification
  MUST produce a byte-identical file").
- The iteration 2 hint in `bookwright-implementation-plan.md`
  explicitly says: *"NO usar tomli/tomli_w; usar tomlkit consistentemente."*

**Alternatives considered**:
- Stdlib `tomllib` (read-only, Python 3.11+) + `tomli_w` (write): faster,
  but discards comments and key order. Would violate FR-020.
- A hand-rolled writer: rejected on maintenance grounds.

---

## R2. Pydantic v2 multi-error accumulation

**Decision**: Express every field rule as either a Pydantic v2 field
validator, a `model_validator(mode="after")`, or a typed annotation
(`Literal`, `conlist`, etc.). Let Pydantic accumulate offences into a
single `pydantic.ValidationError`, then translate it into our public
`ManifestValidationError` (one `_FieldFailure` entry per Pydantic error).

**Rationale**:
- Pydantic v2 collects all field-level failures in one pass — exactly
  what FR-011 and SC-007 require ("a manifest with several independent
  errors fails reporting all of them").
- Translating once at the boundary keeps the public exception shape
  stable even if Pydantic's internal representation changes.
- The `_FieldFailure` carries `field_path` (dotted: `book.authors[0]`),
  `rejected_value`, `rule_id` (machine-readable, e.g.
  `book.type.not_in_enum`), and `message` (human-readable). These are
  exactly the four pieces FR-024 needs for the `--json` envelope.

**Alternatives considered**:
- Raising on the first failure: violates FR-011.
- Re-implementing error accumulation manually around `model_validate`:
  more code, less robust, and would duplicate Pydantic's location
  tracking.

---

## R3. ISO 639-1 source of truth

**Decision**: Embed the 184 ISO 639-1 alpha-2 codes as a Python
`frozenset[str]` literal in `src/bookwright/core/iso639_1.py`. Codes are
lowercase. No network access, no filesystem load.

**Rationale**:
- The `/speckit-clarify` session settled this: the closed list is the
  full ISO 639-1 registry, bundled in-package, no curation, no network
  (spec § Clarifications, Q4; FR-006).
- A frozenset literal is constant-time membership-check, zero startup
  cost, and trivially auditable in code review.
- The list is stable in practice (constructed languages like `eo`, `la`,
  `cu` are included because they have codes; no editorial filtering).

**Alternatives considered**:
- `pycountry`: pulls in IANA registry data plus other registries we
  don't need. Heavier dependency for one frozenset's worth of value.
- Reading a bundled `.txt` at import time: same outcome, more I/O,
  harder to audit at a glance.

---

## R4. PEP 440 parsing and comparison

**Decision**: Add `packaging>=23.0` to the runtime dependency list and
use `packaging.version.Version` for both `cli_version_min` and the
installed CLI's `bookwright.__version__`. Comparison: standard `<`/`==`
on `Version` instances.

**Rationale**:
- FR-012 explicitly mandates PEP 440 semantics (`MAJOR.MINOR.PATCH` +
  optional pre-release suffix; example `1.2.3rc1`).
- `packaging` is the canonical implementation; it is already a
  transitive dependency of `pip` itself on every developer machine.
- The library handles the easy-to-mess-up corner of PEP 440 — *pre-release
  ordering*: `1.0.0rc1 < 1.0.0` (rc precedes the final release). Getting
  that wrong by hand could silently let an underpowered CLI open a
  future-version manifest.

**Constitutional impact**:
- The Technical Constraints section of `.specify/memory/constitution.md`
  enumerates the runtime dependency list. Adding to it is a **MINOR**
  amendment. This iteration's plan flags the amendment in its Complexity
  Tracking table; the amendment PR MUST land before this iteration's
  `/speckit-implement` step (or as part of it).

**Alternatives considered**:
- Hand-rolled regex (`r"^\d+\.\d+\.\d+((a|b|rc)\d+)?$"`) plus tuple
  comparison with pre-release demotion. Possible but brittle; one of
  the better-known PEP 440 traps. Maintenance burden outweighs the
  saving of one dependency.
- Restricting `cli_version_min` to `X.Y.Z` only (no pre-release). Would
  contradict the spec's worked example (`1.2.3rc1`).

---

## R5. `uri_base` validation

**Decision**: Use stdlib `urllib.parse.urlsplit`. Reject the value
unless ALL of the following hold (FR-008):
1. Non-empty `scheme` whose lowercase form is `http` or `https`.
2. Non-empty `netloc` (the host, possibly with port).
3. Empty `query` (`""`).
4. Empty `fragment` (`""`).
5. The original (untouched) string ends with `/`.

The rule check is exact-case for the trailing slash but case-insensitive
for the scheme.

**Rationale**:
- The spec's clarification (Q2) restricts the URI to absolute `http`/`https`
  with no query/fragment and a trailing slash, because it will be used as
  a Turtle `@prefix` declaration in iterations 5–6. RFC 3986 in full
  generality (URN, `file:`, `data:`, relative refs) is intentionally out
  of scope.
- `urllib.parse.urlsplit` is a standard library function with no
  surprising edge cases for the subset we care about.

**Alternatives considered**:
- `pydantic.HttpUrl`: closer in spirit, but normalises the URL (may
  strip or add components), which would break the byte-identical
  round-trip guarantee (FR-020, SC-005). We want to reject malformed
  values, not silently rewrite them.
- A regex: fragile against IDN hosts and IPv6 brackets.

---

## R6. `manifest_version` parsing

**Decision**: `manifest_version` is read as a string from TOML, then
validated against the regex `^[1-9][0-9]*$` (strict positive-integer
decimal: no leading zeros, no sign, no `v` prefix, no dots, no
whitespace). When the regex matches, the value is parsed as `int` and
compared by integer ordering against the known set
`KNOWN_MANIFEST_VERSIONS: frozenset[int] = frozenset({1})`.

- If the integer ∈ `KNOWN_MANIFEST_VERSIONS` → validate normally, no
  warning (FR-014).
- If the integer > max known → load best-effort, attach one
  `ManifestWarning(rule_id="manifest_version.unknown_future", ...)` to
  the returned object (FR-013).
- Otherwise (regex fails OR the field is absent) → reject with a
  field-precise `ManifestValidationError` (FR-013, spec User Story 5
  Acceptance Scenario 3).

**Rationale**:
- Matches the clarified contract exactly (spec § Clarifications, Q3).
- Keeps `manifest_version` and `cli_version_min` formally distinct: one
  is an integer-as-string, the other is a PEP 440 version. They will
  never be confused at the comparison call site.

**Alternatives considered**:
- Accept any string and let downstream code interpret: rejected because
  silent acceptance of e.g. `"1.0"` would push the failure into a later
  command and confuse the user.

---

## R7. Atomic write

**Decision**: `Manifest.dump(path, *, overwrite=False)` writes via the
classic *write-temp-and-rename* pattern:
1. Open a unique temp file in the **same directory** as `path` (so
   the rename is on the same filesystem and is atomic on POSIX).
2. Write the TOML body, `flush()`, and `os.fsync()` the file descriptor.
3. `os.replace(temp_path, path)` — atomic on POSIX, atomic-enough on
   modern Windows.
4. On any exception during steps 1–3, attempt to delete the temp file
   and re-raise. The destination file is untouched.
5. If `overwrite=False` and the destination already exists, raise
   `ManifestError("refuse to overwrite", ...)` BEFORE opening the temp
   file (FR-019).

**Rationale**:
- FR-021 requires that the caller never observes a half-written
  manifest. Write-temp-and-rename is the standard POSIX recipe for that.
- The temp file lives in the destination directory because cross-device
  renames are not atomic. `tempfile.NamedTemporaryFile(dir=path.parent)`
  satisfies this naturally.

**Alternatives considered**:
- Truncate-and-write-in-place: violates FR-021.
- Lockfile + in-place write: solves concurrent writers, but Bookwright
  is single-user CLI; we don't need that complexity.

---

## R8. Comment-preserving construction

**Decision**: `Manifest.build(...)` produces its TOML output by loading
the bundled template `src/bookwright/resources/templates/manifest.template.toml`
(via `importlib.resources.files("bookwright.resources.templates").joinpath("manifest.template.toml")`),
mutating values in the resulting `tomlkit.TOMLDocument` to reflect the
caller's inputs and the FR-017 defaults, and returning the document
attached to the `Manifest` instance. `dump(...)` then serialises that
same document.

**Rationale**:
- The spec's User Story 4 Acceptance Scenario 2 requires that newly
  built manifests are "human-readable, comments preserved where the
  template defines them, deterministic section/key order."
- Driving construction from a real TOML template (instead of building
  one programmatically) lets us preserve those comments verbatim, and
  any future change to commentary is a one-file diff for code review.
- The `tomlkit.TOMLDocument` is the same object that backs a loaded
  manifest, so `build → dump → load → dump` lands on a stable byte
  representation by construction.

**Alternatives considered**:
- Render via Jinja2 + a `.jinja` template: works, but the output is a
  string, not a `TOMLDocument`, so the resulting manifest object would
  need a re-parse step before `dump` could reuse it for round-tripping.
  Extra moving parts for the same outcome.
- Programmatic `tomlkit` construction in code: comments must be added
  by hand; a future change to commentary touches Python, not data.

---

## R9. Public API shape

**Decision**: The library entry points exposed by `bookwright.core` are:

| Symbol | Kind | Purpose |
|---|---|---|
| `Manifest` | Pydantic v2 model class | Typed access to every block and field. Stable attribute names match the TOML key names (snake_case). |
| `Manifest.load(path: Path \| str) -> Manifest` | classmethod | Read + parse + validate + attach any warnings. |
| `Manifest.dump(self, path: Path \| str, *, overwrite: bool = False) -> Path` | method | Atomic write. Returns the absolute path written. |
| `Manifest.build(*, title: str, authors: list[str], integration_key: str, **kwargs: Any) -> Manifest` | classmethod | The FR-015 builder: three required inputs + keyword overrides for any documented optional field; unknown kwargs raise `TypeError`. |
| `Manifest.warnings: tuple[ManifestWarning, ...]` | attribute | Frozen tuple of warnings attached during load. Empty on a clean load. |
| `ManifestError` | exception (parent) | Base for every failure mode this module owns. |
| `ManifestValidationError(ManifestError)` | exception | Carries the list of `_FieldFailure` entries. `.to_json()` returns the JSON form for FR-024. |
| `ManifestWarning` | dataclass / Pydantic model | Carries `rule_id`, `field_path`, `offending_value`, `message`. `.to_json()` returns the JSON form. |
| `KNOWN_MANIFEST_VERSIONS` | `frozenset[int]` | Currently `frozenset({1})`. Updated when the manifest schema changes incompatibly. |

**Rationale**:
- Matches the spec's Key Entities list one-for-one (Manifest,
  ManifestVersion, CliVersionFloor, IntegrationRecord, ValidationError,
  ManifestWarning).
- `dump` returns the path so callers (iteration 4 `init`) can print or
  log it without recomputing.
- `build` is a `classmethod` so the constructor (`Manifest(...)`)
  remains the low-level "I already have validated data" path; callers
  going through the builder always get the defaults + validation pass.

**Alternatives considered**:
- A free function `load_manifest(path)` instead of `Manifest.load`:
  symmetrical but inconsistent with `Manifest.dump`. Stick with one
  style.
- Exposing `_FieldFailure` as public: rejected; the JSON form is the
  public surface, the dataclass is implementation detail.
