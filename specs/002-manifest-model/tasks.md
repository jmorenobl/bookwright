---
description: "Task list for iteration 002: Manifest Model"
---

# Tasks: Manifest Model

**Input**: Design documents from `/specs/002-manifest-model/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/manifest_api.md, quickstart.md

**Tests**: Test tasks are included. The spec mandates them (Constitution Principle VIII — ≥80 % coverage CI gate; this iteration's local acceptance bar is ≥90 % for `bookwright.core`). Each FR maps to at least one test.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1–US5). Setup/Foundational/Polish tasks have no story label.
- All file paths are relative to the repo root.

## Path Conventions

Single-project layout (Constitution Principle III): `src/bookwright/` for production code, `tests/` at the root. New code in this iteration lands under `src/bookwright/core/`, `src/bookwright/resources/`, and `tests/core/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Constitutional amendment + dependency bump + directory skeleton.

- [X] T001 Amend [.specify/memory/constitution.md](.specify/memory/constitution.md) as a MINOR amendment (1.0.0 → 1.1.0) per Governance: (a) add `packaging>=23.0` to the runtime dependency list in the Technical Constraints section (alphabetical order); (b) bump the `**Version**:` footer line to `1.1.0` and update `**Last Amended**:` to today's date; (c) update the Sync Impact Report header at the top — record the version change, state the bump rationale ("MINOR: addition to runtime dependency list per Principle II / Technical Constraints, required by FR-012 PEP 440 ordering"), and confirm under "Templates requiring updates" that no `.specify/templates/*.md` change is required; (d) scan `.specify/templates/*.md` to verify point (c). See plan.md Complexity Tracking row 1.
- [X] T002 Add `packaging>=23.0` to `[project].dependencies` in [pyproject.toml](pyproject.toml) (alphabetical order) and run `uv sync` to refresh `uv.lock`
- [X] T003 Update [pyproject.toml](pyproject.toml) `[tool.hatch.build]` and `[tool.hatch.build.targets.wheel]` so the new `src/bookwright/resources/` subtree is included as package data (no exclusion of the template `.toml`)
- [X] T004 [P] Create directory skeleton: `src/bookwright/core/` with empty [src/bookwright/core/__init__.py](src/bookwright/core/__init__.py); `src/bookwright/resources/templates/` with empty [src/bookwright/resources/__init__.py](src/bookwright/resources/__init__.py) and [src/bookwright/resources/templates/__init__.py](src/bookwright/resources/templates/__init__.py)
- [X] T005 [P] Create test directory skeleton: [tests/core/__init__.py](tests/core/__init__.py) (empty) and `tests/core/fixtures/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Modules every user story phase imports. No user-story work can begin until this phase is complete.

**Critical**: errors.py, iso639_1.py, the Pydantic block-model scaffold in manifest.py, and the test conftest must exist before any US-phase task can start.

- [X] T006 [P] Implement [src/bookwright/core/iso639_1.py](src/bookwright/core/iso639_1.py): `ISO_639_1_CODES: frozenset[str]` literal with all 184 ISO 639-1 alpha-2 codes (lowercase) per research §R3. No I/O, no network. Add a module docstring naming the source.
- [X] T007 [P] Implement [src/bookwright/core/errors.py](src/bookwright/core/errors.py): the exception hierarchy `ManifestError` → {`ManifestNotFoundError`, `ManifestSyntaxError`, `ManifestValidationError`, `ManifestOverwriteError`}, the `_FieldFailure` frozen dataclass (`field_path`, `rejected_value`, `rule_id`, `message`), the `ManifestWarning` Pydantic model (`rule_id`, `field_path`, `offending_value`, `message`), and `.to_json()` methods on each exception/warning matching the JSON shapes in [contracts/manifest_api.md](specs/002-manifest-model/contracts/manifest_api.md) §"Exception JSON shapes"
- [X] T008 Implement Pydantic block models in [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py): `BookwrightBlock`, `BookBlock`, `VocabulariesBlock`, `ValidatorsBlock`, `IntegrationBlock`, `PathsBlock`, and the root `Manifest` model per data-model.md. Field types only (use `Literal` for `book.type` and `book.status`; `list[str]`, `dict[str, Any]`, `int | None` as documented). Set `model_config = ConfigDict(extra="allow", strict=True)` on `Manifest` (round-trips future top-level blocks). Set `extra="forbid"` on every known block (`BookwrightBlock`, `BookBlock`, `VocabulariesBlock`, `ValidatorsBlock`, `IntegrationBlock`, `PathsBlock`). `BookBlock.metadata` and `IntegrationBlock.options` are typed as `dict[str, Any]` and therefore accept arbitrary keys by construction — no per-block `extra="allow"` override is needed. Define module constants: `KNOWN_MANIFEST_VERSIONS = frozenset({1})`, `BOOK_TYPES`, `BOOK_STATUSES`, `DEFAULT_SKILLS_DIR = {"claude": ".claude/skills", "generic": ".agents/skills"}`. Add a private `_installed_version()` thin indirection that returns `bookwright.__version__` (so tests can monkey-patch). Add `Manifest.warnings: tuple[ManifestWarning, ...]` field with default `()` and exclude it from TOML serialisation. No custom validators yet — those land per-story.
- [X] T009 Implement [src/bookwright/core/__init__.py](src/bookwright/core/__init__.py) re-exports per [contracts/manifest_api.md](specs/002-manifest-model/contracts/manifest_api.md) §"Package surface" with the exact `__all__` list (`Manifest`, `KNOWN_MANIFEST_VERSIONS`, `BOOK_TYPES`, `BOOK_STATUSES`, `ManifestError`, `ManifestNotFoundError`, `ManifestSyntaxError`, `ManifestValidationError`, `ManifestOverwriteError`, `ManifestWarning`)
- [X] T010 Author [src/bookwright/resources/templates/manifest.template.toml](src/bookwright/resources/templates/manifest.template.toml): a comment-preserving template covering every top-level block from `bookwright-design.md` § 8.1 with placeholder values that the builder will overwrite. Section order and key order match the desired deterministic output (FR-018). Comments explain each block in human-readable prose (preserved through `tomlkit` round-trip).
- [X] T011 [P] Implement [tests/core/conftest.py](tests/core/conftest.py): `tmp_manifest` fixture (writes a string to a tmp_path manifest and returns the path); `installed_version` fixture that monkey-patches `bookwright.core.manifest._installed_version` to a caller-supplied PEP 440 string; helper `load_fixture(name)` resolving relative to `tests/core/fixtures/`

**Checkpoint**: Foundation ready — every US phase can start in parallel.

---

## Phase 3: User Story 1 — Load a valid project manifest (Priority: P1) 🎯 MVP

**Goal**: `Manifest.load(path)` returns a typed object exposing every field from § 8.1 with the values declared in the file.

**Independent Test**: Place a fully-populated `manifest.toml` in a temp dir and call `Manifest.load`. Assert every documented attribute is reachable with the right type and value; `manifest.integration` is exposed as data only.

### Fixtures for User Story 1

- [X] T012 [P] [US1] Create [tests/core/fixtures/valid_full.toml](tests/core/fixtures/valid_full.toml): every required and optional field from § 8.1 populated (all blocks, opaque keys in `[book.metadata]` and `[integration.options]`); `book.authors` includes a duplicate entry to exercise the Edge Case "legitimate duplicates allowed"
- [X] T013 [P] [US1] Create [tests/core/fixtures/valid_minimal.toml](tests/core/fixtures/valid_minimal.toml): only the required fields (`bookwright.cli_version_min`, `schema_version`, `manifest_version`, `uri_base`; `book.title`, `type`, `language`, `authors`; `integration.key`, `skills_dir`)

### Implementation & Tests for User Story 1

> Ordering: fixtures (above) → implementation → test. The test (T015) is
> last because it imports the module the implementation builds. Run it
> with `pytest -x` to confirm the failures land where you expect.

- [X] T014 [US1] Implement `Manifest.load(cls, path)` in [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py): resolve path, read text, parse via `tomlkit.parse`, build `Manifest` through Pydantic, attach the underlying `_document`, return with `warnings=()` (no version-classification logic yet — that's US5). Use `pathlib.Path` for `path: Path | str`. No file existence or syntax-error handling yet (US2 covers that).
- [X] T015 [US1] Write [tests/core/test_load_valid.py](tests/core/test_load_valid.py) — Acceptance Scenarios 1–3 (FR-001, FR-003, FR-022): full-field load returns every value as declared; minimal load returns defaults for optionals; `[integration]` is exposed as data and never re-interpreted; the loaded `book.authors` preserves the duplicate entry verbatim (Edge Case); a parametrized sub-test iterates over every member of `BOOK_TYPES` and `BOOK_STATUSES` and asserts each value loads cleanly (SC-002); a regression-guard sub-test loads a manifest with `vocabularies.active = ["does-not-exist"]` and asserts the load succeeds (FR-023)

**Checkpoint**: User Story 1 — loading a valid manifest works end-to-end and is testable independently.

---

## Phase 4: User Story 2 — Reject invalid manifests with field-precise errors (Priority: P1)

**Goal**: Malformed/incomplete manifests fail with errors that name the field path and explain the rule violated. All independent errors surface together.

**Independent Test**: Load each of nine broken fixtures. Each load raises `ManifestValidationError` whose `failures` list cites the offending field path, the rejected value, and a stable `rule_id`. A multi-error fixture surfaces every failure in one raise.

### Fixtures for User Story 2

- [X] T016 [P] [US2] Create the invalid-fixture set under [tests/core/fixtures/](tests/core/fixtures/) — one file per rule (suggested names): `invalid_book_title_missing.toml`, `invalid_book_type_bad.toml`, `invalid_book_language_klingon.toml`, `invalid_book_authors_empty.toml`, `invalid_book_authors_blank_entry.toml`, `invalid_book_status_wip.toml`, `invalid_uri_base_no_scheme.toml`, `invalid_uri_base_no_trailing_slash.toml`, `invalid_uri_base_has_query.toml`, `invalid_uri_base_has_fragment.toml`, `invalid_cli_version_min_v1.toml`, `invalid_manifest_version_dotted.toml`, `invalid_manifest_version_zero.toml`, `invalid_bookwright_missing_uri_base.toml`, `invalid_bookwright_missing_schema_version.toml`, `invalid_bookwright_missing_manifest_version.toml`, `invalid_bookwright_missing_cli_version_min.toml`, `invalid_multi_error.toml` (combines ≥3 independent failures for FR-011)

### Implementation & Tests for User Story 2

> Ordering: fixture (above) → implementation → test. The test (T020) is
> last because it imports the module the implementation builds. Run it
> with `pytest -x` to confirm the failures land where you expect.

- [X] T017 [US2] Add field/model validators in [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py): `BookBlock.title` non-empty after `strip()` (FR-004, rule `book.title.empty`/`.missing`); `BookBlock.language` membership in `ISO_639_1_CODES`, exact lowercase (FR-006, rule `book.language.not_iso_639_1`); `BookBlock.authors` list non-empty and every entry non-empty after `strip()` (FR-007, rules `book.authors.empty`/`book.authors[N].entry.empty`); `BookwrightBlock.uri_base` validator using `urllib.parse.urlsplit` per research §R5 with sub-rule ids (`bookwright.uri_base.invalid_uri`/`wrong_scheme`/`empty_host`/`has_query`/`has_fragment`/`no_trailing_slash`); `BookwrightBlock.manifest_version` regex `^[1-9][0-9]*$` (FR-013, rule `bookwright.manifest_version.not_positive_integer_string`); `BookwrightBlock.cli_version_min` PEP 440 parse via `packaging.version.Version` (FR-012, rule `bookwright.cli_version_min.not_pep440`). Expose two private helpers used downstream: `_parse_manifest_version(raw: str) -> int` (applies the same `^[1-9][0-9]*$` regex and returns the parsed integer) and `_classify_manifest_version(parsed: int) -> Literal["known", "future"]` comparing against `KNOWN_MANIFEST_VERSIONS`. Each validator uses Pydantic v2 `field_validator` / `model_validator(mode="after")` so failures accumulate (R2).
- [X] T018 [US2] Implement the `pydantic.ValidationError` → `ManifestValidationError` translator in [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py): convert every Pydantic error into one `_FieldFailure(field_path, rejected_value, rule_id, message)`. Render field paths in dotted/`[N]` form (`book.authors[0]`). Map Pydantic error types/contexts to the stable `rule_id` taxonomy in [contracts/manifest_api.md](specs/002-manifest-model/contracts/manifest_api.md). Wire the translator into `Manifest.load` so all collected failures surface in one raise (FR-011, SC-007).
- [X] T019 [US2] Add file-existence and TOML-syntax handling to `Manifest.load` in [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py): raise `ManifestNotFoundError(path=...)` when the file is missing; catch `tomlkit.exceptions.ParseError` and re-raise as `ManifestSyntaxError(path=..., line=..., column=..., message=...)` extracting line/column when available (FR-002).
- [X] T020 [US2] Write [tests/core/test_load_invalid.py](tests/core/test_load_invalid.py) — Acceptance Scenarios 1–9 (FR-002, FR-004…FR-011, FR-013 parse failure): each invalid fixture loads and raises `ManifestValidationError` containing the expected `field_path` and `rule_id`; `invalid_multi_error.toml` surfaces ≥3 failures in one raise (SC-007); the four `invalid_bookwright_missing_*.toml` fixtures each cite their respective missing field with `rule_id` ending in `.missing` (FR-010); a missing file raises `ManifestNotFoundError`; an unparseable file raises `ManifestSyntaxError`

**Checkpoint**: User Story 2 — invalid manifests are rejected with field-precise, multi-error reports.

---

## Phase 5: User Story 3 — Refuse manifests demanding a newer CLI (Priority: P1)

**Goal**: A manifest with `cli_version_min` higher than the installed CLI is refused with both versions named in the error.

**Independent Test**: With `cli_version_min = "9999.0.0"` (or by monkey-patching `_installed_version()` lower than the manifest's value), `Manifest.load` raises `ManifestValidationError` citing `bookwright.cli_version_min` and naming both versions in the message.

### Fixtures for User Story 3

- [X] T021 [P] [US3] Create [tests/core/fixtures/future_cli_version.toml](tests/core/fixtures/future_cli_version.toml) with `cli_version_min = "9999.0.0"` (otherwise valid minimal manifest)

### Implementation & Tests for User Story 3

> Ordering: fixture (above) → implementation → test. The test (T023) is
> last because it imports the module the implementation builds. Run it
> with `pytest -x` to confirm the failures land where you expect.

- [X] T022 [US3] Add the installed-vs-required comparison as a `Manifest.model_validator(mode="after")` in [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py), reading the installed CLI's version via `_installed_version()`: compare `Version(self.bookwright.cli_version_min)` to `Version(_installed_version())` with PEP 440 ordering; raise a Pydantic error mapped to `_FieldFailure(field_path="bookwright.cli_version_min", rule_id="bookwright.cli_version_min.installed_too_old", message="installed CLI {installed} is older than required {required}")` (FR-012, SC-003). Rationale: same scope as the US5 `manifest_version` classifier, so both checks share the failure-translation path.
- [X] T023 [US3] Write [tests/core/test_version_gate.py](tests/core/test_version_gate.py) — Acceptance Scenarios 1–2 (FR-012, SC-003): monkey-patch `_installed_version` to `"0.0.1"` and load `future_cli_version.toml` → expect `ManifestValidationError` whose first-failure message names both `0.0.1` and `9999.0.0`; with `_installed_version` set to `"9999.0.0"` or higher the load succeeds and the rest of validation continues normally

**Checkpoint**: User Story 3 — the CLI version gate is enforced.

---

## Phase 6: User Story 4 — Generate a new manifest from minimal inputs (Priority: P2)

**Goal**: `Manifest.build(title, authors, integration_key, **overrides)` produces a fully valid manifest with FR-017 defaults filled in; `Manifest.dump(path, *, overwrite=False)` writes it atomically and deterministically.

**Independent Test**: Build with minimal inputs → assert defaults match FR-017. Dump to a temp file → load it back → byte-identical round-trip on second dump. Refuse-overwrite is enforced. Unknown override kwarg raises `TypeError`; rule-violating override raises `ManifestValidationError`.

### Preparation for User Story 4

- [X] T024 [P] [US4] Verify the template authored in T010 ([src/bookwright/resources/templates/manifest.template.toml](src/bookwright/resources/templates/manifest.template.toml)) covers every key listed in the override allowlist of [contracts/manifest_api.md](specs/002-manifest-model/contracts/manifest_api.md) §`Manifest.build`. Add any missing key with its FR-017 default. No-op if T010 is already complete.

### Implementation & Tests for User Story 4

> Ordering: template check (above) → implementation → tests. T027 and T028
> are last because they exercise the builder/dump path built in T025–T026.
> Run them with `pytest -x` to confirm the failures land where you expect.

- [X] T025 [US4] Implement `Manifest.build(...)` in [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py): (a) enumerate the documented override allowlist from [contracts/manifest_api.md](specs/002-manifest-model/contracts/manifest_api.md) §"Manifest.build"; (b) raise `TypeError("build() got unexpected keyword argument '<name>'")` on any unknown kwarg, before constructing anything (FR-015, SC-004); (c) load the template via `importlib.resources.files("bookwright.resources.templates").joinpath("manifest.template.toml")` as a `tomlkit.TOMLDocument`; (d) overwrite `book.title`, `book.authors`, `integration.key`, `integration.skills_dir` (from `DEFAULT_SKILLS_DIR[integration_key]` unless `integration_skills_dir` override supplied; raise `KeyError`/`TypeError` for unknown integration without explicit override), and `bookwright.cli_version_min` (= installed version); apply FR-017 defaults for every other field; overlay caller overrides; (e) re-parse the resulting document through Pydantic for end-to-end validation (FR-016); on failure raise `ManifestValidationError`; (f) attach `_document` and return.
- [X] T026 [US4] Implement `Manifest.dump(self, path, *, overwrite=False)` in [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py): resolve path; if exists and `not overwrite` → raise `ManifestOverwriteError(path=...)` (FR-019); otherwise open `tempfile.NamedTemporaryFile(dir=path.parent, delete=False)`, write `tomlkit.dumps(self._document)`, `flush()`, `os.fsync(fd)`; `os.replace(temp_path, path)` (FR-021, research §R7); on any exception delete the temp file and re-raise without touching `path`; return `path.resolve()`
- [X] T027 [P] [US4] Write [tests/core/test_build.py](tests/core/test_build.py) — Acceptance Scenarios 1, 1a, 1b (FR-015, FR-016, FR-017, SC-004): minimal-input build defaults match FR-017; overrides take effect and still validate; unknown kwarg raises `TypeError` naming the argument; rule-violating override (e.g. `language="zz"`) raises `ManifestValidationError`; omitting `uri_base` raises `ManifestValidationError` citing `bookwright.uri_base`
- [X] T028 [P] [US4] Write [tests/core/test_write.py](tests/core/test_write.py) — Acceptance Scenarios 2–4 + round-trip (FR-018, FR-019, FR-020, FR-021, SC-005): dump produces a human-readable file with preserved comments and deterministic section/key order; second dump to the same path raises `ManifestOverwriteError`; `overwrite=True` succeeds; `Manifest.load(p).dump(q, overwrite=True)` yields a file byte-identical to `p` for both `valid_full.toml` and `valid_minimal.toml`; simulate a write failure (e.g. patch `os.replace` to raise) and assert the prior file contents at the destination are untouched and the temp file is cleaned up

**Checkpoint**: User Story 4 — building and writing manifests works end-to-end with the round-trip and atomicity guarantees.

---

## Phase 7: User Story 5 — Tolerate unknown future manifest versions (Priority: P3)

**Goal**: A manifest declaring a future `manifest_version` loads best-effort and surfaces exactly one warning naming the unknown version; known versions load with no warning; malformed/missing values still fail (US2 territory).

**Independent Test**: Load a fixture with `manifest_version = "9"` → load succeeds, `manifest.warnings` has exactly one entry with `rule_id="manifest_version.unknown_future"`, and every recognised field is still populated.

### Fixtures for User Story 5

- [X] T029 [P] [US5] Create [tests/core/fixtures/future_manifest_version.toml](tests/core/fixtures/future_manifest_version.toml) with `manifest_version = "9"` (otherwise valid minimal manifest)

### Implementation & Tests for User Story 5

> Ordering: fixture (above) → implementation → test. The test (T031) is
> last because it imports the module the implementation builds. Run it
> with `pytest -x` to confirm the failures land where you expect.

- [X] T030 [US5] Add `manifest_version` classification in [src/bookwright/core/manifest.py](src/bookwright/core/manifest.py): use the `_parse_manifest_version` and `_classify_manifest_version` helpers introduced in T017; in `Manifest.load`, after the typed `Manifest` is built, classify and attach `ManifestWarning(rule_id="manifest_version.unknown_future", field_path="bookwright.manifest_version", offending_value=raw, message=f"manifest_version {parsed} is newer than this CLI knows about (max known: {max(KNOWN_MANIFEST_VERSIONS)}); load was best-effort")` to `Manifest.warnings` as a tuple; emit nothing for known versions (FR-013, FR-014, SC-006). The model layer MUST NOT write to stdout/stderr.
- [X] T031 [US5] Write [tests/core/test_future_version.py](tests/core/test_future_version.py) — Acceptance Scenarios 1–3 (FR-013, FR-014, SC-006): future `manifest_version` produces exactly one warning whose `rule_id` and `offending_value` match, every recognised field is still populated, and capsys/capfd capture no writes from the model layer; known `manifest_version` produces an empty `warnings` tuple; missing/malformed `manifest_version` raises `ManifestValidationError` (delegated to US2's path, asserted here too as a regression guard)

**Checkpoint**: User Story 5 — forward-compat warning behaviour is encoded.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: FR-024 JSON shapes, coverage gate, lint/type gates, quickstart smoke.

- [X] T032 [P] Write [tests/core/test_json_shapes.py](tests/core/test_json_shapes.py) — FR-024: `ManifestValidationError.to_json()`, `ManifestWarning.to_json()`, `ManifestSyntaxError.to_json()`, `ManifestNotFoundError.to_json()`, `ManifestOverwriteError.to_json()` produce dicts whose keys, value types, and shapes match [contracts/manifest_api.md](specs/002-manifest-model/contracts/manifest_api.md) §"Exception JSON shapes" exactly (assert via `json.dumps` round-trip)
- [X] T033 Run `uv run pytest tests/core/ --cov=bookwright.core --cov-report=term-missing` and ensure `bookwright.core` package coverage ≥ 90 % (spec acceptance bar). Add small targeted tests if any branch is uncovered.
- [X] T034 Run `uv run ruff check`, `uv run ruff format --check`, and `uv run mypy --strict src tests` from the repo root; fix every issue. CI gates from iteration 1 already enforce these on push.
- [X] T035 Verify the [quickstart.md](specs/002-manifest-model/quickstart.md) examples end-to-end: `uv sync`; `uv run python -c "from bookwright.core import Manifest, KNOWN_MANIFEST_VERSIONS; print(KNOWN_MANIFEST_VERSIONS)"`; build a manifest, dump it, load it back, confirm byte-identical round-trip on a second dump

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)**: T001 blocks T002 (constitution amendment must land or be coordinated with the dep addition). T003 depends on the directory skeleton from T004. T004/T005 are independent of T001–T003 and can run in parallel.
- **Phase 2 (Foundational)**: requires Phase 1 complete. T008 depends on T007 (`ManifestWarning` is referenced as a `Manifest` field type). T009 depends on T007 and T008. T010 can be drafted in parallel with T006–T009. T011 depends on T009 (imports from `bookwright.core`).
- **Phases 3–7 (User Stories)**: every story phase depends on **all** of Phase 2. After Phase 2, US1, US2, US3, US4, US5 can in principle be tackled in parallel; in practice US1 → US2 → US3 in sequence is friendliest because they all extend `Manifest.load` in the same file. US4 (build/dump) and US5 (future-version warning) edit different code paths in the same file and can be interleaved with US2/US3 once Phase 2 is done.
- **Phase 8 (Polish)**: depends on all user stories complete.

### User-story dependencies

- **US1 (Load valid)**: depends on Foundational only.
- **US2 (Reject invalid)**: depends on Foundational and on US1's `Manifest.load` scaffold (T014) — validators and the error translator are wired into that path.
- **US3 (Version gate)**: depends on Foundational and on US2's validation accumulator (T018) — its error surfaces through the same channel.
- **US4 (Build/Dump)**: depends on Foundational plus the validators added in US2 (T017) so the post-construction re-parse can fail meaningfully.
- **US5 (Future-version warning)**: depends on Foundational, US1's load path (T014), and US2's `manifest_version` regex validator (T017).

### Within each user story

- Fixtures first (in parallel where possible), tests second (must fail), implementation third.
- Within `manifest.py`, validators → translator → load-path glue → file-existence/syntax handling. These all touch one file, so they are sequential.

### Parallel opportunities

- Phase 1: T004 ∥ T005 ∥ (T001, T002, T003 sequential among themselves).
- Phase 2: T006 ∥ T007 ∥ T010 ∥ T011 (T008/T009 sequential after T007).
- Phase 3 (US1): T012 ∥ T013, then T014 → T015.
- Phase 4 (US2): T016 in parallel with starting US3/US4/US5 fixtures; T017 → T018 → T019 → T020.
- Phase 5 (US3): T021 in parallel with other-story fixtures; T022 → T023.
- Phase 6 (US4): T024 in parallel with T021/T029; T025 → T026; T027 ∥ T028.
- Phase 7 (US5): T029 in parallel with other-story fixtures; T030 → T031.
- Phase 8: T032 in parallel with T033/T034 prep; T035 last.

---

## Parallel example: Foundational phase

```bash
# After Phase 1 directory skeleton is in place, four foundational files
# can be written in parallel because they touch different files:
Task T006: "Implement src/bookwright/core/iso639_1.py with ISO_639_1_CODES frozenset"
Task T007: "Implement src/bookwright/core/errors.py with the ManifestError hierarchy and to_json shapes"
Task T010: "Author src/bookwright/resources/templates/manifest.template.toml comment-preserving template"
Task T011: "Implement tests/core/conftest.py with tmp_manifest and installed_version fixtures"

# T008 (block-model scaffold in manifest.py) and T009 (__init__.py re-exports)
# run after T007 because they import ManifestWarning / ManifestError.
```

## Parallel example: User Story 4 tests

```bash
# After T025 + T026 land, the build- and write-side tests can run in parallel:
Task T027: "Write tests/core/test_build.py covering Scenarios 1, 1a, 1b"
Task T028: "Write tests/core/test_write.py covering Scenarios 2-4 + round-trip"
```

---

## Implementation Strategy

### MVP first (User Story 1 only)

1. Complete Phase 1 (Setup).
2. Complete Phase 2 (Foundational) — Manifest scaffold + errors + ISO 639-1 + template + conftest.
3. Complete Phase 3 (US1): `Manifest.load` for valid manifests + `test_load_valid.py` green.
4. **STOP and VALIDATE**: load `valid_full.toml` and `valid_minimal.toml`. This is the MVP slice — every other capability builds on it.

### Incremental delivery

After the MVP:

1. Add US2 → invalid fixtures + validators + error translator + `test_load_invalid.py` green.
2. Add US3 → version-gate validator + `test_version_gate.py` green.
3. Add US4 → builder + atomic dump + `test_build.py` + `test_write.py` green.
4. Add US5 → future-version warning + `test_future_version.py` green.
5. Polish (Phase 8) → JSON shape tests + coverage gate + lint/type/format + quickstart smoke.

Each step adds value without breaking the previous: the load path keeps loading valid manifests after every step.

### Parallel team strategy

With multiple contributors:

1. One contributor completes Phase 1 + Phase 2 (they're small and tightly sequential).
2. Once Phase 2 is in:
   - Dev A: US2 (validators + translator) — owns most of `manifest.py`.
   - Dev B: US4 (builder + dump) — also touches `manifest.py` but a different region; coordinate via small PRs to avoid conflicts.
   - Dev C: US5 (warning classifier) — small, touches `Manifest.load`'s tail.
3. US3 (version gate) is small enough to bundle with whichever PR lands first after US1.
4. Polish (Phase 8) is a single sweep at the end.

---

## Notes

- `[P]` tasks = different files, no dependencies on incomplete tasks.
- `[Story]` label maps each task to a user story for traceability; setup/foundational/polish tasks have no story label by design.
- Each user story is independently testable per its acceptance scenarios.
- Spec mandates tests (Constitution Principle VIII): tests MUST be written before the implementation that satisfies them within each story phase.
- Commit after each task or logical group (the project's auto-git hook will prompt).
- Do not pull future-iteration scope forward: no CLI subcommand wiring, no vocabulary filesystem checks, no `GrafeoIndexer`. FR-024 only requires that the JSON shapes are *ready* for `--json` consumption (T032), not that any `--json` CLI flag exists yet.
- Same-file conflicts to watch: `src/bookwright/core/manifest.py` is touched by T008, T014, T017, T018, T019, T022, T025, T026, T030. Sequence these carefully and prefer small commits.

---

## Task summary

| Phase | Tasks | Count |
|---|---|---|
| 1 — Setup | T001–T005 | 5 |
| 2 — Foundational | T006–T011 | 6 |
| 3 — US1 (Load valid, P1, MVP) | T012–T015 | 4 |
| 4 — US2 (Reject invalid, P1) | T016–T020 | 5 |
| 5 — US3 (Version gate, P1) | T021–T023 | 3 |
| 6 — US4 (Build/Dump, P2) | T024–T028 | 5 |
| 7 — US5 (Future-version warning, P3) | T029–T031 | 3 |
| 8 — Polish | T032–T035 | 4 |
| **Total** | | **35** |

Suggested MVP scope: Phase 1 + Phase 2 + Phase 3 (US1). Everything else is incremental.
