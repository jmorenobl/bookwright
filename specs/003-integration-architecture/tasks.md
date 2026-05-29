---

description: "Iteration 3 tasks — integration architecture (registry, base class, options parser, stub setup)"
---

# Tasks: Integration Architecture

**Input**: Design documents from `/specs/003-integration-architecture/`

**Prerequisites**:
- [plan.md](plan.md) (required) — class shape, file layout, constitution-check
- [spec.md](spec.md) (required) — 5 user stories with priorities, 37 FRs, 10 SCs
- [research.md](research.md) — R1–R8 design decisions
- [data-model.md](data-model.md) — entity shapes + `to_dict()` payloads
- [contracts/integrations_api.md](contracts/integrations_api.md) — public API surface

**Tests**: Required. Constitution Principle VIII (test discipline, ≥ 80 %
global coverage, ratcheting upward) and the spec's per-iteration target
of ≥ 95 % slice coverage on `bookwright.integrations` both mandate tests
for every FR. Test tasks are written **first**, expected to fail until
the matching implementation task lands.

**Organization**: One phase per user story. Cross-cutting guards
(`test_no_stdio.py`, `test_errors_json.py`, `test_constants.py`) land in
the final Polish phase so they survive churn from any story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: User story this task serves (US1–US5)
- Every task names exact file paths

## Path Conventions

Single-project `src/` layout per Constitution Principle III. All new
production code under `src/bookwright/integrations/`; all new tests
under `tests/integrations/`. Iteration-2 files (`core/manifest.py`,
`core/_build.py`) get one surgical edit each in the Polish phase.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the empty package skeleton iterations 1 and 2 did not lay down.

- [X] T001 [P] Create production package skeleton: empty `src/bookwright/integrations/__init__.py`, `src/bookwright/integrations/base.py`, `src/bookwright/integrations/constants.py`, `src/bookwright/integrations/errors.py`, `src/bookwright/integrations/options.py`, `src/bookwright/integrations/claude/__init__.py`, `src/bookwright/integrations/generic/__init__.py`
- [X] T002 [P] Create test scaffolding: empty `tests/integrations/__init__.py` and a placeholder `tests/integrations/conftest.py` (refined in T007)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Land the contract surface every user story imports. Until this phase completes, no story phase can compile or run.

**⚠️ CRITICAL**: No US1–US5 task may start until T003–T007 are green.

- [X] T003 [P] Implement agentskills.io compliance constants in `src/bookwright/integrations/constants.py`: `SKILL_NAME_MAX_LENGTH: Final[int] = 64`, `SKILL_DESCRIPTION_MAX_LENGTH: Final[int] = 1024`, `SKILL_PLACEHOLDER_MARKER_NAME: Final[str] = ".bookwright-skills-placeholder"`; module docstring documents the FR-033 directory-name-equals-`name` structural invariant (FR-033, FR-034)
- [X] T004 [P] Implement structured exception family in `src/bookwright/integrations/errors.py` per [data-model.md § 6](data-model.md): private `_IntegrationError(Exception)` base with class-level `code`, `message` attribute, and `to_dict()` returning a `json.dumps`-safe dict; five concrete subclasses `UnknownIntegrationError`, `UnknownOptionError`, `MalformedOptionError`, `DuplicateRegistrationError`, `InvalidOptionDeclarationError` each carrying the exact payload fields listed in data-model § 6.1–6.5 (FR-035, FR-036)
- [X] T005 [P] Implement `IntegrationOption` frozen dataclass in `src/bookwright/integrations/options.py`: `@dataclass(frozen=True)` with fields `flag: str`, `type: Literal["flag", "string"] = "flag"`, `required: bool = False`, `default: str | None = None`, `help: str = ""` — no validation in `__post_init__` (validation deferred to the parser per R1) (FR-012); leave a `parse_options` placeholder raising `NotImplementedError` for T015 to fill
- [X] T006 Implement `SkillsIntegration` base class in `src/bookwright/integrations/base.py`: `ClassVar` attributes with sentinel defaults (`key = ""`, `config = {}`, `default_skills_dir = ""`, three capability flags `False`), default `options()` classmethod returning `[]`, default `resolve_skills_dir(parsed_options=None) -> Path` returning `Path(self.default_skills_dir)`, and `setup(project_root, manifest, parsed_options=None) -> None` method signature with a `pass` body (real body lands in T013); `manifest: "Manifest"` annotation under `TYPE_CHECKING` guard importing from `bookwright.core.manifest` (FR-009, FR-012 default, FR-022 default, FR-026 signature)
- [X] T007 Implement test fixtures in `tests/integrations/conftest.py`: `tmp_project` fixture returning a fresh `tmp_path`-based directory, `minimal_manifest` factory building the iteration-2 `Manifest` model with the lockable defaults (positional kwargs `title`, `authors` as `list[str]`, `integration_key`; plus overrides `language`, `type`, `status` mapped through `_BUILD_OVERRIDE_ALLOWLIST_TABLE`), and a `registry_snapshot` fixture that snapshots `INTEGRATION_REGISTRY` and restores it on teardown (consumed by US5)

**Checkpoint**: Foundation ready — US1, US2, US3, US4 can begin in any order.

---

## Phase 3: User Story 1 — Registry lookup (Priority: P1) 🎯 MVP

**Goal**: Downstream callers ask the registry for `"claude"` or `"generic"` and receive the integration class; an unknown key raises a structured `UnknownIntegrationError` whose payload names the rejected key and the registered keys in alphabetic order.

**Independent Test**: `from bookwright.integrations import get, list_keys`; `get("claude") is ClaudeIntegration`; `get("generic") is GenericIntegration`; `list_keys() == ["claude", "generic"]`; `get("copilot")` raises `UnknownIntegrationError(value="copilot", valid=["claude", "generic"])`.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation lands.**

- [X] T008 [P] [US1] Write `tests/integrations/test_registry.py` covering FR-001–FR-005, SC-001, SC-002: lookup for `"claude"` returns `ClaudeIntegration`; lookup for `"generic"` returns `GenericIntegration`; `list_keys()` returns alphabetically-sorted list `["claude", "generic"]` (assert order, not just set equality); lookup for `""`, `"copilot"`, and a non-string `None` (via `cast(str, None)` or `# type: ignore`) all raise `UnknownIntegrationError` with `to_dict()["value"]` equal to the rejected key and `to_dict()["valid"] == ["claude", "generic"]`; re-running `_register_builtins()` is a no-op (same classes, no exception); registering a *different* class under an existing key raises `DuplicateRegistrationError` whose payload names both classes

### Implementation for User Story 1

- [X] T009 [P] [US1] Implement `ClaudeIntegration` in `src/bookwright/integrations/claude/__init__.py`: subclass of `SkillsIntegration` declaring `key = "claude"`, `default_skills_dir = ".claude/skills"`, `config = {"name": "Claude Code", "install_url": "https://docs.claude.com/claude-code", "requires_cli": True, "context_file": "CLAUDE.md"}`, three capability flags all `True`, no `options()` override (inherits empty list per FR-013), no `resolve_skills_dir` override (inherits base per data-model § 3 decision) (FR-007, FR-010, FR-013)
- [X] T010 [P] [US1] Implement `GenericIntegration` in `src/bookwright/integrations/generic/__init__.py`: subclass of `SkillsIntegration` declaring `key = "generic"`, `default_skills_dir = ".agents/skills"`, `config = {"name": "Generic (Agent Skills standard)", "install_url": "https://agentskills.io", "requires_cli": False}` (note: `context_file` MUST NOT be present per FR-008), three capability flags all `False`, `options()` classmethod returning one `IntegrationOption(flag="--skills-dir", type="string", required=False, default=".agents/skills", help="...")` (FR-014, exact `help` text per [data-model.md § 4](data-model.md)), and `resolve_skills_dir(parsed_options)` override returning `Path(parsed_options["skills_dir"])` when `parsed_options` is a non-empty dict containing `"skills_dir"` else `Path(".agents/skills")` (FR-024) (FR-008, FR-010, FR-014, FR-024)
- [X] T011 [US1] Implement the central registry in `src/bookwright/integrations/__init__.py`: module-level `INTEGRATION_REGISTRY: dict[str, type[SkillsIntegration]] = {}`; helper `_register(cls)` per [research.md § R5](research.md) (no-op when same class re-registers; raises `DuplicateRegistrationError(value=cls.key, existing=<dotted name>, new=<dotted name>)` when a different class collides); `_register_builtins()` calling `_register(ClaudeIntegration)` then `_register(GenericIntegration)`; `get(key) -> type[SkillsIntegration]` raising `UnknownIntegrationError(value=key, valid=list_keys())` when `key not in INTEGRATION_REGISTRY`; `list_keys() -> list[str]` returning `sorted(INTEGRATION_REGISTRY.keys())`; module bottom invokes `_register_builtins()`; `__all__` lists the public re-exports per [contracts/integrations_api.md § "From `bookwright.integrations`"](contracts/integrations_api.md) (FR-001–FR-005) — depends on T009, T010

**Checkpoint**: US1 fully functional — registry MVP shippable. Iteration 4 can already dispatch on `--integration <key>`.

---

## Phase 4: User Story 2 — `setup()` stub (Priority: P1)

**Goal**: A caller with a resolved integration class, a parsed-options dict, and a manifest calls `integration.setup(project_root, manifest, parsed_options)`; the integration creates the resolved skills directory and writes the placeholder marker idempotently, touching nothing outside that directory.

**Independent Test**: `ClaudeIntegration().setup(tmp, manifest, None)` creates `tmp/.claude/skills/` with `.bookwright-skills-placeholder` whose contents identify the integration key; second call leaves on-disk bytes identical; `GenericIntegration().setup(tmp, manifest, {"skills_dir": ".cursor/skills"})` materializes into `.cursor/skills/` and does NOT create `.agents/skills/`.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before T012 lands.**

- [X] T012 [P] [US2] Write `tests/integrations/test_setup_stub.py` covering FR-026–FR-030, SC-006: after `ClaudeIntegration().setup(tmp_project, minimal_manifest, None)`, `(tmp / ".claude/skills")` is a directory and `(tmp / ".claude/skills/.bookwright-skills-placeholder").read_text() == "bookwright integration: claude — SKILL.md materialization deferred to iteration 9\n"`; same shape for `GenericIntegration` with `None` (writes `.agents/skills`) and with `{"skills_dir": ".cursor/skills"}` (writes `.cursor/skills`, not `.agents/skills`); idempotency: two consecutive calls with identical args leave `sha256(marker.read_bytes())` byte-identical; user-content preservation: pre-place `(tmp / ".claude/skills/my-skill/SKILL.md")` then call `setup()` and assert the user file is untouched and the marker is still present; "no writes outside the resolved dir": snapshot `set(tmp.rglob("*"))` before/after `setup()` and assert every new path lies on the chain `project_root → resolved_skills_dir`, with at most one new *file* — the marker `<resolved_dir>/.bookwright-skills-placeholder` (FR-029, edge-case #4). Concretely: for each new path P, either `P` is a directory and `P.is_relative_to(project_root)` AND (`resolved_dir.is_relative_to(P)` or `P == resolved_dir`), OR `P` is the marker file inside `resolved_dir`; "missing project_root" case: pass `project_root = tmp_path / "fresh-root"` (does NOT exist on disk) and assert `setup()` creates it via the implicit `parents=True` in `mkdir(parents=True, exist_ok=True)`, with the resolved skills dir + marker present underneath (covers [spec.md](spec.md) edge-case bullet #4); `manifest` argument is unused in v0 body (assert by passing a manifest with sentinel fields and re-reading them post-call)

### Implementation for User Story 2

- [X] T013 [US2] Implement the `setup()` body on `SkillsIntegration` in `src/bookwright/integrations/base.py` (replaces the T006 `pass` body): compute `target = (project_root / self.resolve_skills_dir(parsed_options))`; `target.mkdir(parents=True, exist_ok=True)`; `marker = target / SKILL_PLACEHOLDER_MARKER_NAME`; if `not marker.exists()`, write `f"bookwright integration: {self.key} — SKILL.md materialization deferred to iteration 9\n"` with `encoding="utf-8"`; never re-write an existing marker; never touch any path outside `target` (FR-026–FR-030, R3) — depends on T003 (constants), T006 (signature)

**Checkpoint**: US2 fully functional — iteration 4's `init` has a working `setup()` to call.

---

## Phase 5: User Story 3 — Option parser (Priority: P1)

**Goal**: A caller hands the raw `--integration-options` string and the chosen integration class to `parse_options(...)`; the parser returns a typed dict on success or raises a structured `UnknownOptionError` / `MalformedOptionError` whose payload names the integration, the rejected/offending flag, and the rule violated.

**Independent Test**: `parse_options("--skills-dir .cursor/skills", GenericIntegration) == {"skills_dir": ".cursor/skills"}`; `parse_options("--skills-dir=.cursor/skills", GenericIntegration) == {"skills_dir": ".cursor/skills"}`; `parse_options("--bogus xyz", GenericIntegration)` raises `UnknownOptionError(integration="generic", value="--bogus", valid=["--skills-dir"])`; `parse_options("--skills-dir", GenericIntegration)` raises `MalformedOptionError(rule="missing_value", value="--skills-dir")`.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before T015 lands.**

- [X] T014 [P] [US3] Write `tests/integrations/test_option_parser.py` covering FR-016–FR-021, SC-005 — parametrized table per [contracts/integrations_api.md § parse_options](contracts/integrations_api.md): empty/`None`/whitespace-only → `{}`; whitespace and equals forms both produce `{"skills_dir": ".cursor/skills"}`; shlex-quoted spaces `'--skills-dir "path with spaces/skills"'` round-trip intact; `ClaudeIntegration` + any non-empty input raises `UnknownOptionError(valid=[])`; `GenericIntegration` + `"--bogus x"` raises `UnknownOptionError(valid=["--skills-dir"])`; `--skills-dir` with no value raises `MalformedOptionError(rule="missing_value")`; duplicate flag `--skills-dir a --skills-dir b` raises `MalformedOptionError(rule="duplicate_flag")`; string-typed option `--skills-dir --foo` accepts `--foo` as the value (FR-017 lookahead); using an inline-declared `FakeIntegration` with one `type="flag"` option `--my-flag` and input `"--my-flag --foo"`, `parse_options` raises `UnknownOptionError(value="--foo", valid=["--my-flag"])` — proves the parser does NOT consume a following token as a value for `type="flag"` (spec edge-case "value starts with `--`", FR-019); using an inline-declared `FakeIntegration` with a `type="flag"` option supplied a value raises `MalformedOptionError(rule="unexpected_value")`; using an inline `FakeIntegration` with a `required=True` option absent raises `MalformedOptionError(rule="missing_required")`; FR-020 precedence over FR-021: `parse_options(None, FakeWithRequired)` and `parse_options("", FakeWithRequired)` both return `{}` (no error), even when `FakeWithRequired` declares a `required=True` option — the empty-input short-circuit fires before the required-flag check (R6); declaring an option with `flag="skills-dir"` (missing `--` prefix) and calling the parser raises `InvalidOptionDeclarationError(rule="bad_flag_prefix", value="skills-dir")` (FR-015); declaring an option with `type="weird"` raises `InvalidOptionDeclarationError(rule="bad_type")`

### Implementation for User Story 3

- [X] T015 [US3] Implement `parse_options(raw, integration_cls)` in `src/bookwright/integrations/options.py` per [research.md § R1, § R6](research.md): early-return `{}` when `raw is None` or `raw.strip() == ""`; tokenize via `shlex.split(raw, posix=True)`; build the `{flag: IntegrationOption}` lookup from `integration_cls.options()`, validating each descriptor (`flag.startswith("--")` else `InvalidOptionDeclarationError(rule="bad_flag_prefix")`; `type in ("flag", "string")` else `InvalidOptionDeclarationError(rule="bad_type")`); iterate tokens with a small state machine — split on first `=` for equals form, consume next token as value for `type=="string"`, error on `type=="flag"` value, track seen flags for duplicate detection; raise `UnknownOptionError(integration=integration_cls.key, value=flag, valid=sorted(declared_flags))` on unknown flag; raise `MalformedOptionError(rule=..., value=flag)` on `missing_value` / `duplicate_flag` / `unexpected_value`; after token loop, scan declared options for any `required=True` flag absent from results and raise `MalformedOptionError(rule="missing_required", value=flag)`; return a fresh dict keyed on normalized identifier form (leading `--` stripped, internal `-` → `_`) (FR-016–FR-021) — depends on T004 (errors), T005 (`IntegrationOption`)

**Checkpoint**: US3 fully functional — iteration 4 can validate user input before calling `setup()`.

---

## Phase 6: User Story 4 — Metadata inspection (Priority: P2)

**Goal**: Consumers (iteration-4 `init` surfacing the `[integration]` block, iteration-9 SKILL.md materializer branching on capabilities, a future `bookwright integrations list --json`) read declared `key`, `config`, `default_skills_dir`, and the three capability flags from the integration classes; values match the locked tables in FR-007, FR-008, FR-010.

**Independent Test**: Read `ClaudeIntegration.key`, `.config`, `.default_skills_dir`, and the three `supports_*` flags; assert each against the FR-007/FR-010 locked table. Same for `GenericIntegration` against FR-008/FR-010. Assert `SkillsIntegration` base defaults the three capability flags to `False`.

### Tests for User Story 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before US1 implementation completes.** (The classes T009/T010 produced are the implementation; these tests pin their declared metadata.)

- [X] T016 [P] [US4] Write `tests/integrations/test_metadata.py` covering FR-006–FR-011: `ClaudeIntegration.key == "claude"`, `.default_skills_dir == ".claude/skills"`, `.config == {"name": "Claude Code", "install_url": "https://docs.claude.com/claude-code", "requires_cli": True, "context_file": "CLAUDE.md"}`, all three `supports_*` flags `True`; `GenericIntegration.key == "generic"`, `.default_skills_dir == ".agents/skills"`, `.config == {"name": "Generic (Agent Skills standard)", "install_url": "https://agentskills.io", "requires_cli": False}` AND `"context_file" not in .config` (explicit absence per FR-008), all three `supports_*` flags `False`; on the unsubclassed `SkillsIntegration`, all three `supports_*` flags default to `False` (defence-in-depth per FR-009); FR-011 negative assertion — search the integrations package for any `if .supports_dynamic_context` / `if .supports_subagents` / `if .supports_tool_restrictions` branch and assert none exists (the flags are pure metadata in v0)
- [X] T017 [P] [US4] Write `tests/integrations/test_resolve_skills_dir.py` parametrized over `(integration_cls, parsed_options, expected_path)` covering FR-022–FR-025, SC-003, SC-004: for `ClaudeIntegration`, every input in `{None, {}, {"skills_dir": "anything"}, {"skills_dir": ".cursor/skills"}}` returns `Path(".claude/skills")` (FR-023); for `GenericIntegration`, `None` and `{}` return `Path(".agents/skills")`, `{"skills_dir": ".cursor/skills"}` returns `Path(".cursor/skills")`, `{"skills_dir": "path with spaces/skills"}` returns `Path("path with spaces/skills")` (FR-024); all returned paths are relative (`.is_absolute() is False`, FR-025)

**Checkpoint**: US4 metadata locked. Iteration 4 can render `bookwright integrations list --json` against this surface without rediscovering values.

---

## Phase 7: User Story 5 — Plugin extensibility (Priority: P3)

**Goal**: A future contributor adds a new integration as a self-contained subpackage plus one `_register_builtins()` line. No existing file under `claude/`, `generic/`, or `base.py` is touched. The test mechanically pins this.

**Independent Test**: Inline-declare `FakeIntegration(SkillsIntegration)` with `key = "fake"`, `default_skills_dir = ".fake/skills"`, all capabilities `False`, no options. Insert into `INTEGRATION_REGISTRY` via fixture (restored on teardown). Assert lookup, listing, option parsing, `resolve_skills_dir`, and `setup()` all succeed against it. Assert content-hash of `claude/`, `generic/`, `base.py` unchanged.

### Tests for User Story 5 ⚠️

> **NOTE: Write this test once T011 + T013 + T015 are green; it exercises all of them.**

- [X] T018 [P] [US5] Write `tests/integrations/test_plugin_contract.py` covering FR-031, SC-007, R8: inline-declare `FakeIntegration(SkillsIntegration)` with the attributes above; use the `registry_snapshot` fixture from T007 to safely mutate `INTEGRATION_REGISTRY["fake"] = FakeIntegration`; assert `get("fake") is FakeIntegration`, `"fake" in list_keys()` and list is alphabetic, `FakeIntegration().resolve_skills_dir(None) == Path(".fake/skills")`, `FakeIntegration().setup(tmp_project, minimal_manifest, None)` creates `tmp/.fake/skills/` with the marker; declare a second `FakeWithOptionsIntegration(SkillsIntegration)` returning one `IntegrationOption(flag="--scope", type="string", default="all", help="...")` and assert `parse_options("--scope wide", FakeWithOptionsIntegration) == {"scope": "wide"}` and `parse_options("--bogus x", FakeWithOptionsIntegration)` raises `UnknownOptionError(valid=["--scope"])` — proves the parser is generic over `options()`; finally, capture `hashlib.sha256` of `src/bookwright/integrations/claude/__init__.py`, `src/bookwright/integrations/generic/__init__.py`, `src/bookwright/integrations/base.py` at module-import time and assert against a pinned expected map at test end — the test fails loudly if anyone edits any of those three files

**Checkpoint**: All five user stories independently functional. Plugin contract locked mechanically.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Cross-cutting guards, the one surgical edit to iteration-2 code, and the verification pass against quickstart + linters + coverage.

- [X] T019 Re-root `DEFAULT_SKILLS_DIR` in `src/bookwright/core/manifest.py` per [contracts/integrations_api.md § "Side effects on the iteration-2 manifest module"](contracts/integrations_api.md): replace the literal dict `DEFAULT_SKILLS_DIR = {"claude": ".claude/skills", "generic": ".agents/skills"}` with a helper `def _default_skills_dir_map() -> dict[str, str]` performing a late import `from bookwright.integrations import INTEGRATION_REGISTRY` inside the function body and returning `{key: cls.default_skills_dir for key, cls in INTEGRATION_REGISTRY.items()}`; update `_build_manifest` in `src/bookwright/core/_build.py` to call `_default_skills_dir_map()` at build time instead of indexing the module-level dict (R2) — depends on T011 (registry must populate at import)
- [X] T020 [P] Update any iteration-2 test in `tests/core/` that asserts the literal `DEFAULT_SKILLS_DIR` dict shape to assert the derivation shape (call `_default_skills_dir_map()` and compare); preserve the FR-022 promise that `Manifest.load()`/`Manifest.dump()` treat `[integration]` as opaque data
- [X] T021 [P] Write `tests/integrations/test_constants.py` covering FR-033, FR-034, SC-010: direct attribute assertions `SKILL_NAME_MAX_LENGTH == 64`, `SKILL_DESCRIPTION_MAX_LENGTH == 1024`, `SKILL_PLACEHOLDER_MARKER_NAME == ".bookwright-skills-placeholder"`; grep-style guard via AST scan over `src/bookwright/` for any *other* module re-declaring `64` or `1024` as `SKILL_*_MAX_LENGTH` (single-source-of-truth pin)
- [X] T022 [P] Write `tests/integrations/test_errors_json.py` covering FR-036, SC-008: parametrize over all five error types instantiating each with representative payloads (e.g., `UnknownIntegrationError(value="copilot", valid=["claude", "generic"])`); assert `to_dict()` returns the exact field set named in [data-model.md § 6.1–6.5](data-model.md); assert `json.dumps(err.to_dict())` round-trips without a custom encoder; assert `code` is the class-level attribute (immutable); assert `message` is non-empty and human-readable
- [X] T023 [P] Write `tests/integrations/test_no_stdio.py` covering FR-037, SC-009, R7: AST-scan every `.py` file under `src/bookwright/integrations/` (recursive); reject any `ast.Call` whose `func` is a bare `print` Name, any `ast.Attribute` of the form `sys.stdout` / `sys.stderr`, any `from sys import stdout` / `from sys import stderr`; fail with a structured message naming file, line, and the offending construct
- [X] T023a [P] Write `tests/integrations/test_no_legacy_commands.py` covering FR-032 (Constitution Principle VI, NON-NEGOTIABLE): AST-scan every `.py` file under `src/bookwright/integrations/` (recursive); reject (a) any `ast.ClassDef` whose name ends in `MarkdownIntegration` or whose bases include a name other than `SkillsIntegration` / `object`, (b) any `ast.Constant` string literal matching the pattern `*commands/*` (catches `.claude/commands/`, `.agents/commands/`, etc.) outside of comments / docstrings, (c) any path-building call (`Path(...)`, `os.path.join(...)`) whose joined segments include `"commands"`; fail with a structured message naming file, line, and the offending construct. Mirror the test shape of T023 so future contributors recognise the pattern.
- [X] T024 Run quickstart validation: execute every code block in [quickstart.md](quickstart.md) §§ 1–5 inside a single `tests/integrations/test_quickstart.py` test using `tmp_project`; assert each expected value/exception per the quickstart prose
- [X] T025 Run the full quality gate from quickstart §§ "Validating your install": `uv run pytest tests/integrations/ -v --cov=bookwright.integrations --cov-report=term-missing` (slice ≥ 95 %), `uv run pytest --cov=src --cov-fail-under=80` (global gate), `uv run ruff check src/bookwright/integrations tests/integrations`, `uv run ruff format --check src/bookwright/integrations tests/integrations`, `uv run mypy --strict src/bookwright/integrations tests/integrations`; fix any findings

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)**: no dependencies — start immediately
- **Phase 2 (Foundational)**: depends on Phase 1; BLOCKS every user story
- **Phase 3 (US1)**: depends on Phase 2 — registry MVP
- **Phase 4 (US2)**: depends on Phase 2 (specifically T003 + T006); independent of US1 — `setup()` body needs the base class and the marker constant, not the registry
- **Phase 5 (US3)**: depends on Phase 2 (T004 errors + T005 `IntegrationOption`); independent of US1
- **Phase 6 (US4)**: depends on US1 tasks T009, T010 (the classes whose metadata is asserted)
- **Phase 7 (US5)**: depends on US1 (T011 registry) + US2 (T013 `setup()`) + US3 (T015 parser)
- **Phase 8 (Polish)**:
  - T019, T020 depend on US1 (T011 — registry must populate at import for the late-import helper to work)
  - T021–T023a, T024 can run any time after Phase 2 lands; recommend post-US1 to avoid churn
  - T025 is the final gate — runs once everything else is green

### Within each user story

- Tests come first (`Tests for User Story N`). Tests expected to FAIL until implementation lands.
- Implementation tasks follow. Single-file tasks marked `[P]` are parallelizable across stories that depend only on Phase 2.

### Parallel opportunities

- **Phase 1**: T001 + T002 in parallel (different paths).
- **Phase 2**: T003 + T004 + T005 in parallel (independent files). T006 + T007 sequential after.
- **Phases 3 + 4 + 5** can run **in parallel** once Phase 2 is green — they touch disjoint files and disjoint user stories:
  - US1 tests + impl: `claude/__init__.py`, `generic/__init__.py`, `integrations/__init__.py`, `tests/integrations/test_registry.py`
  - US2 tests + impl: edit to `base.py` (`setup` body), `tests/integrations/test_setup_stub.py`
  - US3 tests + impl: edit to `options.py` (parser fill), `tests/integrations/test_option_parser.py`
- **Phase 6 (US4)** can start as soon as T009 + T010 land — runs in parallel with US2 and US3 finishing.
- **Phase 8 polish tests (T021–T023)** can all run in parallel with each other.

---

## Parallel example: Phase 2 foundational sprint

```bash
# Three implementers, three independent files:
Implementer A: T003 Implement constants module
Implementer B: T004 Implement structured error family
Implementer C: T005 Implement IntegrationOption dataclass
# Then sequentially:
T006 Implement SkillsIntegration base (sentinel attrs + signatures)
T007 Implement test fixtures (tmp_project, minimal_manifest, registry_snapshot)
```

## Parallel example: Phases 3 + 4 + 5 once Phase 2 is green

```bash
# Three streams, disjoint files:
Stream US1: T008 -> (T009 || T010) -> T011
Stream US2: T012 -> T013
Stream US3: T014 -> T015
# Then merge into US4 (T016, T017) and US5 (T018).
```

---

## Implementation Strategy

### MVP first (User Story 1 only)

1. Complete Phase 1: Setup (T001 + T002).
2. Complete Phase 2: Foundational (T003 → T007). CRITICAL — blocks all stories.
3. Complete Phase 3: US1 (T008 → T011).
4. **STOP and VALIDATE**: `uv run pytest tests/integrations/test_registry.py -v`. The registry is shippable as MVP — iteration 4 can dispatch on `--integration <key>` even without `setup()` body or option parsing.

### Incremental delivery

1. Setup + Foundational → contract surface ready.
2. US1 (T008–T011) → registry MVP.
3. US2 (T012–T013) → `setup()` works end-to-end. Iteration 4's `init` can now finish.
4. US3 (T014–T015) → `--integration-options` validated.
5. US4 (T016–T017) → metadata pinned. Iteration-9 dependencies locked.
6. US5 (T018) → plugin contract proven. Post-v0 contributors unblocked.
7. Polish (T019–T023a, T024–T025) → manifest re-rooting, cross-cutting guards (incl. FR-032 legacy-commands guard), quickstart validation, final quality gate.

### Parallel team strategy

With three developers, after Phase 2 lands:

- Dev A: US1 (T008 → T009 + T010 in parallel → T011).
- Dev B: US2 (T012 → T013).
- Dev C: US3 (T014 → T015).

Then any developer picks up US4 (T016, T017 in parallel), then US5 (T018), then Polish (T019–T025).

---

## Notes

- [P] tasks = different files, no incomplete dependencies.
- [Story] label maps each task to its user story for traceability.
- Tests come before implementation per Constitution Principle VIII; expect them to fail until the matching impl task lands.
- Per-file ≤ 500 LOC (Principle IV). Every integrations module in this iteration is well under that limit.
- No CLI subcommand added in this iteration. Iteration 4 (`bookwright init`) is the first consumer of this layer.
- No new runtime dependency. Stdlib only (`pathlib`, `shlex`, `dataclasses`, `typing`).
- Commit after each task or after a logical group (e.g., all of Phase 2). The auto-commit hook will offer.
- Stop at any phase checkpoint to validate the slice independently.
