# Feature Specification: Unified Error Envelope (shared `BookwrightError` base)

**Feature Branch**: `018-unified-error-envelope`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Bookwright has several independent exception hierarchies (core, golem, io, indexers, validation, and a local error class in commands/validate.py) that each reimplement the same `to_json()` producing the JSON-over-stdout error envelope (Principle IX). The duplication forces replicating any change to the error contract in N places. We need a shared error base that centralizes the envelope shape. Reference: finding R3 of specs/006-graph-indexer/review.md and data-model § 6."

## Clarifications

### Session 2026-06-05

- Q: `core/errors.py` (Manifest\* errors → `{"error":"manifest_not_found",...}`) and `golem/errors.py` (`EmptySlugError` → `{"error":"golem_empty_slug",...}`) emit a **flat** `{"error": …}` shape, not the `{status, code, message, details}` envelope, and existing tests assert that flat shape. Migrating them to a shared canonical base is incompatible with the originally stated "byte-identical JSON / tests unchanged" constraint. How should the shared base treat these two divergent-shape hierarchies? → A: **Normalize everything to the single canonical envelope.** Maximize quality and minimize technical debt — no stopgaps. The two legacy flat-shape hierarchies are the oldest modules (002, 005), predating the envelope convention; they are the outliers and will be converted to the canonical `{status, code, message, details}` envelope. Every flat field maps losslessly (the former `"error"` value becomes `code`; remaining flat fields become `details`). Error **codes**, **messages**, and **exit codes** are preserved; the JSON **bodies** of the ~5 manifest/golem errors are reorganized into the envelope, and their asserting tests and contract docs are updated accordingly.
- Q: `_UsageError` (`commands/validate.py`) is a single class that sets a different `code` per instance (`no_project`, `invalid_manifest`, `unknown_validator`, `empty_scope`), which conflicts with declaring `code` at the class level. How should the base reconcile a per-instance code? → A: **Instance `code` overrides the class default.** The base's serialization reads the effective `self.code`; the class-level `code` is a default that most subclasses set as a class attribute, but a subclass MAY set `self.code` in its constructor. `_UsageError` stays one class, migrated onto the base, setting `code` per instance — no splitting into per-code subclasses, no separate serialization.
- Q: `ManifestError`, `IOError_`, `IndexerError`, and `GolemError` are per-package base exceptions, and `except ManifestError` is a catch target in four command modules. How should they relate to `BookwrightError`? → A: **Preserve them as intermediate classes.** Each package root keeps existing but now inherits `BookwrightError`, yielding a two-level hierarchy (`BookwrightError` → `<PackageError>` → concrete error). The roots stay abstract (no `code`, never serialized), so every existing `except <PackageError>` catch site keeps working unchanged — zero catch-site edits.
- Q: Beyond the six cited hierarchies, `integrations/errors.py` (`_IntegrationError` + 8 subclasses) has its **own** envelope serializer (`to_dict()`) and is emitted under `--json` by `integration use` (attributes spread flat at the top level) and by `init` (attributes nested under `details`) — i.e. the **same** error rendered in two different shapes. `InvalidProjectNameError` (`commands/init/validate.py`) is also serialized under `init --json` while being a bare `Exception`. Are these in scope? → A: **Yes — both are in scope.** Leaving them out preserves exactly the R3 debt this feature exists to remove (a second envelope serializer + one error in two shapes). The correct scope is "**every** exception that reaches a `--json` boundary", not a fixed list of six. They migrate to `BookwrightError`, `to_dict()` is deleted, and their attributes move under `details`. Command **boundary writers** that legitimately extend the body (`init` adds `rolled_back` + `bookwright_version`) are kept, but they MUST source the body from `exc.to_json()`/`exc.details`, never reconstruct it. Exceptions that never reach a `--json` boundary (`io/fs.BackupCreationError`, `io/fs.TargetOutsideProjectRootError`, `commands/init/git.GitInitError`) stay plain `Exception`s — an explicit carve-out, not an oversight.

## Why this scope (decision record)

The defect (review finding R3) is that the JSON-over-stdout error envelope is hand-rolled in many places — the six R3 originally named, plus the integrations `to_dict()` and the bare `init` error the command serializes by hand (eight origins in all) — so any change to the contract must be replicated N times. The goal is a **single source of truth** for the envelope: the contract should be defined in exactly one place and changeable in exactly one place, ever.

Two partial resolutions were rejected because they leave residual technical debt:

- **"Leave the flat-shape hierarchies out of scope"** would consolidate only the four hierarchies that already emit the canonical envelope, leaving two competing error contracts in the codebase permanently — the real debt R3 names would persist.
- **"Inherit the base but override `to_json` in the flat-shape classes"** re-introduces per-class `to_json` methods (the very thing being removed) and means the base is *not* the single source of truth — an envelope change would still have to touch the overrides.

Only full normalization to one envelope achieves zero residual debt and a genuine single point of change. The flat shapes map losslessly to the envelope, so normalization is lossless in meaning (codes, messages, and exit codes are all preserved). This follows the project precedent of fixing a defective requirement with the best real design rather than faking preservation: the original "migrate these *and* keep byte-identical JSON" requirement is internally impossible, so the requirement is corrected here to "migrate these to the one envelope, preserving codes/messages/exit codes and updating the now-obsolete shape assertions."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One place to change the error envelope (Priority: P1)

A maintainer needs to change the error envelope (for example, add or rename a top-level key, or alter how `details` is attached). Today that means editing `to_json()`/`to_dict()` across eight origins and hoping none was missed. After this change, the envelope shape is defined once on a shared base class, every serializable error inherits it, and no concrete error class reimplements the serialization.

**Why this priority**: This is the entire purpose of the feature (R3). Without the single definition, every other benefit (uniformity, lower change cost) does not exist. It is the MVP: even if nothing else were done, a single envelope definition that all errors inherit delivers the value.

**Independent Test**: Pick one representative error from every former hierarchy (core/manifest, golem, io, indexers, validation, commands/validate), construct each, and confirm its serialized JSON is produced by the shared base's single serialization method — verifiable by the absence of any per-class serialization override and by each error producing a well-formed canonical envelope.

**Acceptance Scenarios**:

1. **Given** the shared error base, **When** a maintainer changes the envelope's serialization in the one base method, **Then** every serializable error across all former hierarchies reflects the change with no other edits.
2. **Given** any concrete serializable error class, **When** its source is inspected, **Then** it declares its `code` (and populates `message`/`details`) but does **not** reimplement the envelope serialization.

---

### User Story 2 - Uniform error envelope for agent consumers (Priority: P2)

An agent (or any `--json` consumer) parsing Bookwright command output gets the **same** error envelope shape regardless of which subsystem failed. Errors that previously emitted the flat `{"error": …, <flat fields>}` shape (manifest and golem errors) now emit the canonical `{status, code, message, details}` envelope, matching every other command.

**Why this priority**: Uniformity is the observable payoff of the consolidation for downstream consumers and removes a long-standing inconsistency between the oldest modules and the rest of the CLI. It depends on P1 (the shared base) being in place.

**Independent Test**: Trigger an error from a command that previously emitted the flat shape (e.g., a missing/invalid manifest, or an empty-slug condition) under `--json`, and assert the output is a single canonical `{status:"error", code, message, details?}` document whose `code` equals the former flat `"error"` value.

**Acceptance Scenarios**:

1. **Given** a project condition that raises a manifest error, **When** the relevant command runs with `--json`, **Then** stdout is exactly one canonical envelope with `status:"error"`, `code` equal to the former flat error name (e.g. `manifest_not_found`), and the former flat fields carried under `details`.
2. **Given** a name that slugifies to empty, **When** the failure is serialized, **Then** it emits the canonical envelope with `code:"golem_empty_slug"` and `details:{"name": …}`.
3. **Given** any serializable error with no extra detail fields, **When** it is serialized, **Then** the `details` key is omitted entirely (not present as `null` or `{}`).

---

### User Story 3 - No regression for already-canonical errors, codes, or exit codes (Priority: P3)

A consumer already relying on the canonical-envelope hierarchies (io, indexers, validation, commands/validate) sees **no change at all**: their JSON is byte-identical. Across every hierarchy, error `code` values, error messages, and command exit codes are unchanged.

**Why this priority**: This is the guardrail that keeps the refactor safe. It bounds the blast radius: the only observable changes in the whole feature are the reorganization of the ~5 manifest/golem JSON bodies and the `integration use --json` attributes moving under `details` (FR-005a); everything else (codes, messages, exit codes, the `init` envelope, the four canonical hierarchies) is preserved.

**Independent Test**: Run the existing error-shape tests for the four already-canonical hierarchies unchanged and confirm they pass; confirm every error's `code` string and every command's exit code are identical to `main` before the change.

**Acceptance Scenarios**:

1. **Given** an error from io/indexers/validation/commands.validate, **When** it is serialized, **Then** the JSON is byte-identical to the pre-change output (same keys, same `details` shape).
2. **Given** any command that fails, **When** it exits, **Then** its exit code is identical to the pre-change behavior.
3. **Given** the existing test suite, **When** it runs, **Then** the only assertions that needed editing are those asserting the former **flat** manifest/golem shapes and the integration `to_dict()` / `integration use` top-level-attribute shape (FR-005a); all other error-shape assertions — including the `init` envelope tests — pass unchanged.

---

### Edge Cases

- **Empty vs. populated `details`**: the canonical envelope omits `details` when there are no detail fields and includes it only when populated — this behavior must be identical for every error, including the newly normalized ones.
- **`ManifestValidationError`**: its current flat output is `{"error":"manifest_validation","failures":[…]}` with **no** top-level `message`. Normalization places `failures` under `details` and includes the canonical top-level `message` (the existing summary string). This is the one case where a top-level `message` newly appears; it is an intended part of the canonical envelope and the corresponding test is updated.
- **Layering / import cycles**: the base module must be importable by every layer (core, golem, io, indexers, validation, commands) without importing any of them back — no new import cycle may be introduced.
- **Non-serialized exceptions**: internal/base exception classes that never reach a `--json` boundary (e.g. abstract bases like the per-package root exceptions) need a `code` only if they are themselves serialized; the base must not force a meaningless `code` onto purely-structural parents.
- **Out-of-scope payloads stay put**: success envelopes (`status:"ok"`) and finding payloads (`Violation`, `ValidatorError`, `ManifestWarning`) keep their own serialization and are not routed through the error base.
- **Integration errors across two boundaries**: the same integration error is emitted by `integration use` and by `init`. After normalization both carry the attributes under `details`; `integration use`'s top-level-attribute shape is the one that changes, and its tests are updated accordingly. The `init` boundary is byte-identical (already nested).
- **Command envelope supersets**: `init`'s error envelope legitimately extends the canonical body with `rolled_back`/`bookwright_version`; this is sanctioned and is NOT a second envelope definition (the body still comes from the base). Non-serialized exceptions (`io/fs.*`, `commands/init/git.GitInitError`) stay plain `Exception`s.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a single shared base exception (`BookwrightError`) that defines the canonical error envelope and is the one place the envelope serialization lives.
- **FR-002**: The base MUST define the canonical error envelope: a `code` (a class-level attribute that a subclass MAY override per instance via `self.code`), an instance `message`, and optional `details`, exposed through a single serialization method that reads the effective `self.code`, builds `{"status":"error","code":…,"message":…}`, and adds `"details"` only when details are present.
- **FR-003**: Every exception in the codebase that is serialized to JSON for a `--json` boundary MUST inherit from `BookwrightError` and MUST NOT define its own envelope-building serializer (`to_json` **or** `to_dict`); each concrete class declares its `code` and populates `message`/`details`. Exceptions that never reach a `--json` boundary (`io/fs.BackupCreationError`, `io/fs.TargetOutsideProjectRootError`, `commands/init/git.GitInitError`) MAY remain plain `Exception`s.
- **FR-004**: The following hierarchies MUST be migrated onto the base, preserving their current canonical output **byte-for-byte**: `io/errors.py` (`ProjectNotFoundError`, `MissingDirectoryError`, `InvalidFrontmatterError`, `ResearchError`, `SlugCollisionError`), `indexers/errors.py` (`UnknownIndexerError`, `GraphNotBuiltError`, `GraphLoadError`, `InvalidQueryError`), `validation/base.py` (`UnknownValidatorError`), and the local `_UsageError` in `commands/validate.py`.
- **FR-005**: The two legacy flat-shape hierarchies MUST be migrated onto the base and **normalized** to the canonical envelope: `core/errors.py` (`ManifestNotFoundError`, `ManifestSyntaxError`, `ManifestValidationError`, `ManifestOverwriteError`) and `golem/errors.py` (`EmptySlugError`).
- **FR-005a**: The integrations hierarchy MUST be migrated onto the base: `_IntegrationError` becomes abstract `_IntegrationError(BookwrightError)` (no `code`, no serializer), its `to_dict()` is **deleted**, and each of `UnknownIntegrationError`, `UnknownOptionError`, `MalformedOptionError`, `DuplicateRegistrationError`, `InvalidOptionDeclarationError`, `InvalidIntegrationError`, `SkillLintError`, `SkillMaterializationError` keeps its `code` verbatim and moves its public attributes under `details`. The `integration use --json` body changes shape (attributes move from top level into `details` — a normalization, like the flat hierarchies); the `init --json` body is byte-identical (it already nests them under `details`).
- **FR-005b**: `InvalidProjectNameError` (`commands/init/validate.py`) MUST inherit `BookwrightError`, keep `code = "invalid_project_name"`, and pass `details={"value": …, "rule": …}` — so the error owns the body the `init` command currently hand-assembles. Its serialized output is byte-identical.
- **FR-005c**: Command boundary writers that extend the error body (`commands/init/envelope.error_envelope` adds `rolled_back` + `bookwright_version`) MAY keep those command-specific fields, but MUST source `code`/`message`/`details` from `BookwrightError` (`exc.to_json()` / `exc.code`/`exc.message`/`exc.details`) — never from `to_dict()` nor by reading raw attributes. `init`'s richer envelope is a sanctioned superset, not a competing definition.
- **FR-006**: Normalization MUST be lossless in meaning: each former flat `"error"` value becomes the error's `code` (same string), the human `message` is preserved, and every remaining flat field is carried under `details` (e.g. `path`, `field`/`line`/`column`, `failures`, `name`).
- **FR-007**: Error `code` values MUST NOT change for any error in any hierarchy (the former flat `"error"` strings are reused verbatim as `code`).
- **FR-008**: Error human-readable `message` strings MUST NOT change for any error.
- **FR-009**: Per-command exit codes MUST NOT change for any command or failure mode.
- **FR-010**: The base module MUST NOT import from `core`, `golem`, `io`, `indexers`, `validation`, `integrations`, or `commands` (dependencies flow only toward the base); no new import cycle may be introduced.
- **FR-011**: The system MUST NOT introduce any new error type, and MUST NOT alter the JSON-over-stdout contract beyond reorganizing the two legacy flat shapes into the canonical envelope (Principle IX preserved).
- **FR-012**: Success envelopes (`status:"ok"`, e.g. `io/report.py`, `validation/report.py`) and finding payloads (`Violation`, `ValidatorError`, `ManifestWarning`) MUST remain out of scope and keep their existing serialization unchanged.
- **FR-013**: Tests that assert the former **flat** manifest/golem shapes MUST be updated to assert the canonical envelope; all other existing error-shape assertions MUST pass without modification.
- **FR-014**: Contract documentation that describes the former flat shapes (e.g. `data-model § 6`, `specs/002-manifest-model/contracts/`) MUST be updated to reflect the unified envelope; documentation of the already-canonical shapes is unchanged.
- **FR-015**: The four per-package base exceptions (`ManifestError`, `IOError_`, `IndexerError`, `GolemError`) MUST be preserved as intermediate abstract classes that inherit from `BookwrightError`, producing a two-level hierarchy (`BookwrightError` → `<PackageError>` → concrete error). They remain abstract (no `code`, never serialized), so every existing `except <PackageError>` catch site keeps working unchanged. No catch site may be modified.
- **FR-016**: `_UsageError` (`commands/validate.py`) MUST remain a single class migrated onto `BookwrightError`, setting its `code` per instance via `self.code` in its constructor (no splitting into per-code subclasses, no separate serialization).

### Key Entities

- **`BookwrightError`**: the shared base exception. Attributes: class-level `code` (the stable machine-readable error identifier), instance `message` (human-readable), optional `details` (a mapping of error-specific fields). Behavior: a single serialization producing the canonical envelope. Every serializable error is a subclass.
- **Canonical error envelope**: the JSON document `{"status":"error","code":<str>,"message":<str>[,"details":<object>]}`, where `details` is present only when non-empty. The single shape emitted by all errors after this change.
- **Concrete error class**: a subclass of `BookwrightError` declaring its own `code` and populating `message`/`details` in its constructor; carries no serialization logic of its own.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The error body is defined in **exactly one** location; a search for envelope-building serializers on error classes (**both `def to_json` and `def to_dict`**) returns **zero** results outside `BookwrightError` (down from the six `to_json` + one `to_dict` hand-rolled implementations).
- **SC-002**: **100%** of JSON-serialized exceptions across **all eight** former origins (core, golem, io, indexers, validation, commands.validate, integrations, commands.init) inherit from `BookwrightError`.
- **SC-003**: Every error emits the **same** canonical **body** `{status, code, message[, details]}`; there are **zero** errors emitting the legacy flat `{"error": …}` shape and **zero** spreading error-specific fields at the envelope top level. Command writers MAY add documented envelope-level fields (`init`: `rolled_back`, `bookwright_version`) on top of that body.
- **SC-004**: **Zero** error `code` values, **zero** error `message` strings, and **zero** command exit codes change relative to `main`.
- **SC-005**: The four already-canonical hierarchies produce **byte-identical** JSON to `main`; the **only** edited test assertions are those covering the former flat manifest/golem shapes.
- **SC-006**: A single edit to the base's serialization method changes the envelope for **all** errors simultaneously (demonstrable by a test exercising one representative error per hierarchy through the base).
- **SC-007**: All four CI gates (`ruff check`, `ruff format --check`, `mypy --strict`, `pytest` at ≥ 80% coverage) pass, and no import cycle is introduced.
- **SC-008**: **Zero** exception catch sites (`except <PackageError>` / `except <ConcreteError>`) require modification; the per-package base exceptions remain valid catch targets.

## Assumptions

- The "byte-identical / tests-unchanged" phrasing in the original input applies to the **four already-canonical hierarchies**; for the two legacy flat-shape hierarchies the clarified intent (max quality, zero debt) is to normalize them to the one envelope, accepting the reorganization of those specific JSON bodies and the corresponding test/doc updates. (Per Clarifications, Session 2026-06-05.)
- The former flat `"error"` field value is semantically the same concept as the canonical `code`, so reusing it as `code` preserves the machine-readable identifier consumers key on.
- No external/published consumer depends on the legacy flat manifest/golem JSON bodies, nor on the flat top-level attributes that `integration use --json` currently spreads, beyond the in-repo tests and contract docs; this is a pre-1.0 toolkit (v0.2 in progress) where unifying the error contract is appropriate.
- The base belongs at a layer low enough that all of `core`, `golem`, `io`, `indexers`, `validation`, `integrations`, and `commands` can import it without a cycle; the exact module location is an implementation/plan decision and is not fixed by this spec.
- Purely-structural parent exceptions (the per-package root classes that are never serialized) may remain abstract under the new base without declaring a `code`, as long as no `--json` path serializes them directly.
