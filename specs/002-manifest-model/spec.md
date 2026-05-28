# Feature Specification: Manifest Model

**Feature Branch**: `002-manifest-model`

**Created**: 2026-05-28

**Status**: Draft

**Input**: User description: "Cada proyecto Bookwright declara su configuración en un manifest.toml en la raíz. El CLI necesita un modelo robusto para leer, validar y escribir ese archivo, con compatibilidad hacia adelante (manifest_version) y validación estricta de campos obligatorios."

## Clarifications

### Session 2026-05-28

- Q: Where do non-fatal warnings (e.g., unknown future `manifest_version`) surface, given the JSON-over-stdout contract? → A: Loader returns warnings as structured data attached to the loaded manifest; the CLI layer surfaces them on stderr in human mode and as a `warnings` array inside the JSON document in `--json` mode.
- Q: What counts as a "syntactically valid URI" for `bookwright.uri_base`? → A: An absolute URI with scheme `http` or `https`, a non-empty host (authority), no query and no fragment, and a trailing `/`.
- Q: How are `cli_version_min` and `manifest_version` compared? → A: `cli_version_min` is a strict PEP 440 version string (`X.Y.Z` + optional pre-release), compared with PEP 440 ordering; `manifest_version` is a strict positive integer encoded as a decimal string (`"1"`, `"2"`, …), compared as integer. Each is rejected at load time if malformed.
- Q: What constitutes the "closed list" of ISO 639-1 codes accepted for `book.language`? → A: The full ISO 639-1 registry (the complete set of ~184 two-letter codes), sourced from a small constant bundled inside the `bookwright` package; no curation or editorial filtering, no network access at load time.
- Q: What is the shape of the manifest builder API (FR-015) — strict three-input, typed keyword overrides, or arbitrary partial dict? → A: Three required inputs (`title`, `authors`, `integration_key`) plus keyword overrides for any documented optional manifest field; unknown keyword arguments raise immediately; defaults from FR-017 fill anything still unset; the returned manifest is validated end-to-end (FR-004 through FR-010) before being handed back to the caller.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Load a valid project manifest (Priority: P1)

A user (or a downstream CLI command) needs to inspect a Bookwright project's configuration. They point the CLI at the project root, and a typed manifest object becomes available with every declared field accessible by name — title, type, language, authors, URI base, vocabularies, validators, integration metadata, and path conventions.

**Why this priority**: Loading is the foundation. Every later command (`init`, `graph`, `validate`, the skills layer) reads the manifest before doing anything else. Without a reliable load step there is no project state to operate on.

**Independent Test**: Place a hand-crafted, fully-populated `manifest.toml` matching § 8.1 in a temp directory and call the load API. Assert that all documented fields are reachable on the returned object with the right Python types and values (strings, lists, enums) and that the integration block is present as informational metadata.

**Acceptance Scenarios**:

1. **Given** a `manifest.toml` that declares all required and optional fields from § 8.1, **When** the manifest is loaded, **Then** a typed object is returned exposing every field with the value declared in the file.
2. **Given** a `manifest.toml` that declares only the required fields, **When** the manifest is loaded, **Then** optional fields take their documented defaults and the load succeeds.
3. **Given** a loaded manifest, **When** the `[integration]` block is inspected, **Then** the integration `key`, `skills_dir`, and `options` are exposed as data only — the system does not consult them to resolve any path during loading.

---

### User Story 2 - Reject invalid manifests with field-precise errors (Priority: P1)

A user has a malformed or incomplete `manifest.toml` — a required field is missing, an enum value is wrong, the URI base does not end with `/`, the language code is unknown. The CLI refuses to load it and tells the user exactly which field is wrong and why, so they can fix the file without guessing.

**Why this priority**: A loose validator that silently substitutes defaults for invalid input would produce projects that compile but misbehave downstream. Strict, surgical error messages are the only way the user can self-serve recovery. This is co-equal with P1 loading.

**Independent Test**: Construct a series of broken manifests (missing `title`, `type = "novella"`, `language = "klingon"`, `authors = []`, `uri_base` without trailing slash, `status = "wip"`, etc.). Load each and assert the load fails with an error that names the offending field path and explains the rule that was violated.

**Acceptance Scenarios**:

1. **Given** a manifest where `[book].title` is missing or empty, **When** it is loaded, **Then** the load fails citing `book.title` and stating the field is required and non-empty.
2. **Given** a manifest where `[book].type` is not in `{novel, essay, memoir, non-fiction-narrative, other}`, **When** it is loaded, **Then** the load fails citing `book.type`, the rejected value, and the allowed set.
3. **Given** a manifest where `[book].language` is not a known ISO 639-1 code, **When** it is loaded, **Then** the load fails citing `book.language` and identifying the value as not a valid two-letter language code.
4. **Given** a manifest where `[book].authors` is missing or `[]`, **When** it is loaded, **Then** the load fails citing `book.authors` and stating it must contain at least one author.
5. **Given** a manifest where `[bookwright].uri_base` is not a valid URI or does not end with `/`, **When** it is loaded, **Then** the load fails citing `bookwright.uri_base` with the specific rule violated (invalid URI vs missing trailing slash).
6. **Given** a manifest where `[book].status` is set but not in `{idea, structuring, drafting, revising, done}`, **When** it is loaded, **Then** the load fails citing `book.status`, the rejected value, and the allowed set.
7. **Given** a manifest with several independent errors, **When** it is loaded, **Then** the failure reports all detected errors together, not just the first one.
8. **Given** a manifest where `[bookwright].cli_version_min` is not a valid PEP 440 version string (e.g., `"v1"`, `"1.x"`, `"latest"`), **When** it is loaded, **Then** the load fails citing `bookwright.cli_version_min` and the malformed value.
9. **Given** a manifest where `[bookwright].manifest_version` is not a positive-integer decimal string (e.g., `"1.0"`, `"v2"`, `"01"`, `""`), **When** it is loaded, **Then** the load fails citing `bookwright.manifest_version` and the malformed value.

---

### User Story 3 - Refuse manifests demanding a newer CLI (Priority: P1)

A user opens a project authored with a newer Bookwright CLI. The manifest declares `cli_version_min` higher than the installed CLI. The CLI refuses to load the manifest and explains that the installed version is too old, naming the required minimum and the currently installed version, so the user can upgrade.

**Why this priority**: Loading a project under an underpowered CLI risks silent data corruption (writing back a manifest with fields the older code does not know about). The version gate is the cheapest safeguard and must work from day one.

**Independent Test**: Build a manifest with `cli_version_min = "9999.0.0"`. Load it under the current CLI and assert the load fails with a message naming both the required and installed versions.

**Acceptance Scenarios**:

1. **Given** a manifest with `cli_version_min` greater than the installed CLI version, **When** it is loaded, **Then** the load fails with an error that names both versions and points the user to upgrade.
2. **Given** a manifest with `cli_version_min` equal to or less than the installed CLI version, **When** it is loaded, **Then** the version check passes and the load continues with the other validations.

---

### User Story 4 - Generate a new manifest from minimal inputs (Priority: P2)

A user (or a higher-level command, eventually `bookwright init`) has only the bare essentials of a new project — a title, one author, and an integration choice. They ask the manifest layer to produce a complete, valid `manifest.toml` with sensible defaults filled in for everything else, and to write it to disk in a deterministic, human-readable form.

**Why this priority**: This is what makes the manifest model usable without forcing every caller to know all forty-odd fields. It is P2 because no end-user-facing command needs it until iteration 4; the model + parser + validator + writer must exist first.

**Independent Test**: Call the builder API with `(title="Test Book", authors=["A. Writer"], integration_key="claude")`. Write the result to a temp file. Load the file back. Assert (a) the file parses, (b) every required field is present and valid, (c) optional fields hold the documented defaults, (d) reading and re-writing the same manifest produces a byte-identical file.

**Acceptance Scenarios**:

1. **Given** the minimal inputs (title, author list, integration key), **When** a new manifest is built, **Then** the resulting object is valid against every rule from Story 2 and exposes documented defaults for `type`, `language`, `status`, `manifest_version`, `schema_version`, `cli_version_min`, `indexer`, `paths.*`, `vocabularies.active`, and `validators.*`.
1a. **Given** the minimal inputs plus documented keyword overrides (e.g., `language="es"`, `type="memoir"`, `status="structuring"`), **When** a new manifest is built, **Then** the resulting object reflects the overrides where supplied and the FR-017 defaults everywhere else, and still validates end-to-end.
1b. **Given** a call to the builder with an unknown keyword argument (e.g., `flavor="spicy"`), **When** the builder is invoked, **Then** it raises a programming-error exception naming the unexpected argument, before any object is constructed.
2. **Given** a built manifest, **When** it is written to disk, **Then** the resulting `.toml` is human-readable (one top-level section per block, comments preserved where the template defines them) and section/key order is deterministic.
3. **Given** a manifest loaded from disk and immediately written back without modification, **When** the two files are compared byte-for-byte, **Then** they are identical.
4. **Given** a request to write a manifest to a path that already has a file, **When** the writer is invoked, **Then** it refuses to overwrite unless an explicit overwrite flag is set, and the failure mode is documented (no silent truncation).

---

### User Story 5 - Tolerate unknown future manifest versions (Priority: P3)

A user opens an old project under a newer CLI, or opens a project authored by a newer CLI that bumped `manifest_version`. The CLI tries to do something useful: when the version is older but known, it loads normally; when the version is newer than what the CLI recognizes, it loads best-effort and emits a warning so the user knows the loaded view may be incomplete.

**Why this priority**: This forward-compat behavior matters once there is more than one `manifest_version` in the wild. Until then it is exercised only in tests. P3 because there is no urgent failure mode without it, but the rule must be encoded now so future CLIs do not need to relitigate it.

**Independent Test**: Set `manifest_version = "9"` (or any value greater than the highest known). Load the manifest and assert (a) the load succeeds, (b) a warning is surfaced naming the unknown version, (c) all fields the current CLI understands are still populated correctly.

**Acceptance Scenarios**:

1. **Given** a manifest whose `manifest_version` is strictly greater than every version the CLI knows, **When** it is loaded, **Then** the load succeeds, the typed object is returned with all recognized fields, and a warning is emitted naming the unknown version and recommending a CLI upgrade.
2. **Given** a manifest whose `manifest_version` matches a known version, **When** it is loaded, **Then** no warning is emitted and validation proceeds normally.
3. **Given** a manifest whose `manifest_version` is missing or malformed, **When** it is loaded, **Then** the load fails citing `bookwright.manifest_version` (this is a required field with a strict format, not a forward-compat case).

---

### Edge Cases

- Manifest file is missing at the expected path → the load fails with a clear "no manifest at <path>" error; it does not silently invent an empty one.
- Manifest file exists but is not valid TOML → the load fails with the TOML parser's location (line/column) preserved in the error message.
- `[book].authors` contains duplicate names or whitespace-only entries → empty/whitespace-only entries fail validation; legitimate duplicates are allowed (co-author with the same name as another contributor is an edge case the model does not police).
- `[vocabularies].active` is empty → allowed; means the user opted out of every vocabulary. Not an error at load time.
- `[vocabularies].active` references vocabularies that do not exist under `.bookwright/vocabularies/` → **out of scope for this iteration**: the model does not check the filesystem. The downstream command that actually loads vocabularies is responsible for that check.
- `[integration].options` contains arbitrary nested data → preserved verbatim and round-trips through write; this iteration does not validate plugin-specific option shapes.
- `[book].metadata` contains arbitrary free-form keys → preserved verbatim; not interpreted.
- Writing a manifest fails mid-write (disk full, permission denied) → the original file on disk is not left half-written; the writer either succeeds atomically or fails leaving the prior state intact.

## Requirements *(mandatory)*

### Functional Requirements

**Loading and parsing**

- **FR-001**: The system MUST load a `manifest.toml` from a given filesystem path and return a typed in-memory representation exposing every field defined in `bookwright-design.md § 8.1`.
- **FR-002**: The system MUST fail to load when the manifest file is absent or is not valid TOML, surfacing a message that names the path and (when available) the parser's location of the syntax error.
- **FR-003**: The system MUST treat unknown top-level keys, unknown subkeys in `[book.metadata]`, and unknown keys in `[integration].options` as opaque data: preserved on load, round-tripped on write, never validated.

**Required-field and value validation**

- **FR-004**: The system MUST reject manifests where `book.title` is missing, not a string, or empty/whitespace-only, citing the field path in the error.
- **FR-005**: The system MUST reject manifests where `book.type` is missing or not in `{novel, essay, memoir, non-fiction-narrative, other}`, citing the field path, the rejected value, and the allowed set.
- **FR-006**: The system MUST reject manifests where `book.language` is missing, not a string, or not in the **full ISO 639-1 registry** (the complete set of ~184 two-letter codes, sourced from a constant bundled inside the `bookwright` package), citing the field path and the rejected value. The check MUST be exact-case (lowercase) and MUST NOT call the network.
- **FR-007**: The system MUST reject manifests where `book.authors` is missing, not a list, empty, or contains any non-string or empty/whitespace-only entry, citing the field path and the offending element when applicable.
- **FR-008**: The system MUST reject manifests where `bookwright.uri_base` is missing, not a string, or does not satisfy ALL of: (a) is an absolute URI, (b) has scheme `http` or `https` (case-insensitive), (c) has a non-empty host (authority), (d) carries no query component, (e) carries no fragment component, (f) ends with `/`. The error MUST cite `bookwright.uri_base` and the specific sub-rule that was violated.
- **FR-009**: The system MUST, when `book.status` is present, reject values not in `{idea, structuring, drafting, revising, done}`, citing the field path, the rejected value, and the allowed set. When absent, the default `drafting` MUST apply.
- **FR-010**: The system MUST reject manifests where the required-fields block in `[bookwright]` — `cli_version_min`, `schema_version`, `manifest_version`, `uri_base` — is missing any element, citing each missing field.
- **FR-011**: The system MUST surface all detected validation errors for a single manifest together rather than stopping at the first one.

**Version compatibility**

- **FR-012**: The system MUST treat `bookwright.cli_version_min` as a strict PEP 440 version string (`MAJOR.MINOR.PATCH` with an optional pre-release suffix, e.g., `0.1.0`, `1.2.3rc1`). The system MUST reject the manifest with a field-precise error when the value is missing, not a string, or not a valid PEP 440 version. When valid, the system MUST compare it against the installed CLI version using PEP 440 ordering and fail to load when the installed version is strictly lower, naming both versions in the error.
- **FR-013**: The system MUST treat `bookwright.manifest_version` as a strict positive-integer decimal string (`"1"`, `"2"`, `"3"`, …; no leading zeros, no `+`/`-` sign, no dots, no `v` prefix, no whitespace). The system MUST reject the manifest with a field-precise error when the value is missing, not a string, or not a positive-integer decimal string. When valid and strictly greater (by integer comparison) than every version the current CLI knows, the system MUST complete the load best-effort and attach a structured warning to the returned manifest object that names the unknown version and recommends upgrading the CLI. The model layer MUST NOT write the warning directly to any output stream; the CLI layer surfaces accumulated warnings on stderr in human mode and as a `warnings` array inside the single JSON document in `--json` mode.
- **FR-014**: The system MUST, when `bookwright.manifest_version` declares a known value (integer-equal to a member of the known set), perform validation under the rules for that version with no warning.

**Defaults and construction**

- **FR-015**: The system MUST expose a builder that takes three required inputs — `title`, `authors` (non-empty list), and `integration_key` — and accepts keyword arguments for any documented optional manifest field (at minimum: `language`, `type`, `subtitle`, `genre`, `target_length_words`, `status`, `book_metadata`, `vocabularies_active`, `validators_enabled`, `validators_disabled`, `validators_custom`, `paths_*`, `integration_options`, `manifest_version`, `schema_version`, `cli_version_min`, `indexer`). Unknown keyword arguments MUST raise a programming-error exception immediately (not be silently absorbed into free-form metadata). The builder MUST apply the FR-017 defaults for every field the caller did not override, and MUST run the full validation suite (FR-004 through FR-010) over the resulting object before returning it, surfacing any failure to the caller via the same `ValidationError` channel used by load.
- **FR-016**: Defaults supplied during construction MUST themselves satisfy every validation rule in FR-004 through FR-010 so that "build → validate" never fails on a default-driven build when no caller overrides are supplied. (Validation of caller-supplied overrides is part of FR-015.)
- **FR-017**: The defaults policy MUST be documented inside the spec for this iteration so the implementation has a single source of truth: `type = "novel"`, `language = "en"`, `status = "drafting"`, `manifest_version = "1"`, `schema_version = "golem-1.0"`, `cli_version_min = <current CLI version>`, `indexer = "rdflib"`, `vocabularies.active = []`, `validators.enabled = []`, `validators.disabled = []`, `validators.custom = []`, and the paths block populated with `manuscript = "manuscript/"`, `bible = "bible/"`, `outline = "outline/"`, `graph = "bible/graph.ttl"`, `constitution = "bible/constitution.md"`. The integration block's `skills_dir` default depends on `integration_key` (`claude` → `.claude/skills`, `generic` → `.agents/skills`); `options = {}`. The following fields have **no** default and MUST be supplied by the caller: `book.title`, `book.authors`, and `integration.key` (as the three required positional kwargs to `Manifest.build(...)`); `bookwright.uri_base` (as an override on the builder, or — downstream — by the iteration-4 `init` command which will prompt or compute one).

**Writing**

- **FR-018**: The system MUST serialize a manifest object to a `manifest.toml` file with deterministic section order, deterministic key order within each section, and stable formatting, so identical inputs produce identical bytes.
- **FR-019**: The system MUST refuse to overwrite an existing file unless an explicit overwrite flag is set, and MUST fail without truncating or corrupting the prior file when overwrite is not granted.
- **FR-020**: A manifest loaded from disk and written back without modification MUST produce a byte-identical file on disk.
- **FR-021**: The writer MUST treat the write as atomic from the caller's perspective: on failure mid-write, the prior contents at the destination path MUST be preserved.

**Integration block treatment**

- **FR-022**: The system MUST treat `[integration]` as informational metadata only. `key`, `skills_dir`, and `options` MUST be readable on the typed object and writable back to disk, but the load path MUST NOT consult them to resolve any other path or behavior in this iteration.

**Out-of-scope filesystem checks (deferred)**

- **FR-023**: The system MUST NOT, in this iteration, verify that the vocabularies named in `vocabularies.active` exist on disk under `.bookwright/vocabularies/`. That check belongs to the downstream command that actually loads them.

**Agent-consumable surface**

- **FR-024**: When this iteration's functionality is exposed to a CLI subcommand that supports `--json`, validation failures MUST be representable as a single JSON document on stdout listing the offending field paths, rejected values, and rule messages — keeping the JSON-over-stdout contract usable by skills. Successful loads that produced warnings MUST surface those warnings inside the same JSON document under a `warnings` array (one entry per warning, each naming the rule and the offending value), never on stdout outside the JSON envelope.

### Key Entities *(include if feature involves data)*

- **Manifest**: The typed in-memory representation of a project's `manifest.toml`. Owns the top-level blocks `[bookwright]`, `[book]`, `[book.metadata]`, `[vocabularies]`, `[validators]`, `[integration]`, `[paths]`. Provides typed access to every field and round-trips through write without information loss. Carries an attached list of non-fatal warnings produced during load (empty when the load was clean).
- **ManifestVersion**: A positive-integer decimal string identifying the manifest schema generation (`"1"`, `"2"`, …). Used to gate validation rules and to drive the future-version warning. Belongs to the Manifest. Compared as integer.
- **CliVersionFloor**: A PEP 440 version string declared by the manifest as the minimum CLI version required to open the project. Compared at load time against the installed CLI version using PEP 440 ordering.
- **IntegrationRecord**: The serialized record of which integration was used and the `skills_dir` it resolved to. Read and written, never re-interpreted in this iteration.
- **ValidationError**: A structured error tied to a specific field path (e.g., `book.authors[0]`), the rejected value, and the rule that was violated. Multiple errors can be reported per load. Has a JSON form suitable for `--json` consumers.
- **ManifestWarning**: A structured, non-fatal advisory tied to a rule (e.g., `manifest_version.unknown_future`), the offending value, and a human-readable message. Attached to a successfully-loaded Manifest. Has a JSON form so it can appear in the `warnings` array of a `--json` response.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every `ManifestValidationError.to_json()` failure entry contains a non-empty `field`, a `value` (possibly `null` for missing-field cases), a stable `rule` identifier, and a human-readable `message`.
- **SC-002**: Every required field listed in § 8.1 has an explicit validation rule covered by at least one automated test, and every enum has a test for each allowed value plus one rejected value.
- **SC-003**: Loading a manifest with `cli_version_min` above the installed CLI version produces an error that names both versions in the first sentence.
- **SC-004**: Building a manifest from the minimum inputs (title, authors, integration key) succeeds in 100% of cases for valid inputs, and the result passes the full validator without exception. Building with any combination of documented keyword overrides also succeeds when the overrides are individually valid; building with an unknown keyword raises a programming-error exception that names the unexpected argument.
- **SC-005**: For any manifest file that loads successfully, a load → write round-trip yields a file byte-identical to the original.
- **SC-006**: A manifest declaring a `manifest_version` higher than the CLI knows produces exactly one warning attached to the returned manifest object per load, no writes to stdout/stderr from the model layer itself, and a still-usable typed object.
- **SC-007**: When a manifest declares multiple independent errors, the user sees all of them in a single load attempt rather than having to fix-retry-fix-retry.

## Assumptions

- The set of "known" `manifest_version` values is encoded as a closed set of positive integers inside the CLI and is updated whenever the manifest schema changes incompatibly. For this iteration the known set is `{1}` (matched against the integer parse of the manifest's string value).
- The closed list of ISO 639-1 language codes is the full registry (~184 codes), bundled with the CLI as an in-package constant. No curation, no network call at load time. Constructed and historical languages (e.g., `eo`, `la`, `cu`) are admitted because they have ISO 639-1 codes.
- "Valid URI" for `uri_base` is the restricted form defined in FR-008 (absolute `http`/`https`, host present, no query/fragment, trailing `/`). The narrower rule reflects that `uri_base` is the prefix used to mint GOLEM entity IRIs in the Turtle graph (iterations 5–6) and must be safely serializable as a Turtle `@prefix` declaration; RFC 3986 in its full generality (URNs, `file:`, `data:`, relative refs) is intentionally out of scope here.
- The defaults defined in FR-017 are themselves part of the contract: changing them is a breaking change to the manifest builder and requires bumping `manifest_version` or otherwise being treated as such.
- The `[book.metadata]` block is free-form by design (§ 8.1). Treating its contents as opaque is intentional, not a gap.
- Vocabulary-existence checks against `.bookwright/vocabularies/` are explicitly the responsibility of the downstream command (iteration 6+), per the user input. This iteration cannot perform that check because the indexer is not yet present.
- The `bookwright init` command (iteration 4) is the consumer of the build API from FR-015. This iteration MUST NOT pre-bake any prompting/user-input logic; it only exposes the building block.
