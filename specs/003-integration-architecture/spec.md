# Feature Specification: Integration Architecture

**Feature Branch**: `003-integration-architecture`

**Created**: 2026-05-28

**Status**: Draft

**Input**: User description: "Bookwright debe poder materializar artefactos (Agent Skills) para distintos agentes IA sin que el código del CLI se acople a un agente específico. El usuario elige el agente al inicializar el proyecto y la integración correspondiente decide dónde y cómo escribir los archivos."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Look up an integration by key from the central registry (Priority: P1)

A downstream caller (the iteration-4 `bookwright init` command, the iteration-9 skills materializer, any future agent-facing subcommand) has a string like `"claude"` or `"generic"` and needs the corresponding integration class. They ask the central registry and receive the class, ready to be instantiated and used.

**Why this priority**: The registry is the entry point of the entire integration system. Without it there is no way for any other code to discover which integrations exist or to obtain one to work with. Every later story depends on this story being live.

**Independent Test**: Import the registry. Look up `"claude"` and `"generic"`. Assert each returns a class whose `key` attribute matches the lookup. Look up an unregistered key and assert a structured error is raised that names the rejected key and lists the registered keys.

**Acceptance Scenarios**:

1. **Given** the registry is loaded, **When** the caller asks for `"claude"`, **Then** the returned class is `ClaudeIntegration` and its `key` attribute is `"claude"`.
2. **Given** the registry is loaded, **When** the caller asks for `"generic"`, **Then** the returned class is `GenericIntegration` and its `key` attribute is `"generic"`.
3. **Given** the registry is loaded, **When** the caller asks for any string not in the registry (e.g., `"copilot"`), **Then** a structured error is raised whose payload contains the rejected key and the full list of currently-registered keys in alphabetic order.
4. **Given** the registry is loaded, **When** the caller asks for the list of available integration keys, **Then** the response is a stable, alphabetically-ordered list containing at least `"claude"` and `"generic"`.

---

### User Story 2 - Materialize an integration into a project via setup() (Priority: P1)

A higher-level command (eventually `bookwright init`) has resolved an integration class, parsed the user's `--integration-options` into a dict, and loaded the project manifest. It now calls `integration.setup(project_root, manifest, parsed_options)` and the integration takes responsibility for creating the right directory in the right place. In this iteration `setup()` is intentionally a stub: it creates the resolved skills directory and writes a marker file documenting that real SKILL.md materialization is deferred to iteration 9. The contract is exercised end-to-end so iteration 4 (`init`) can rely on it.

**Why this priority**: This is the actual "do work" entry point of the integration system. Without a working `setup()` the iteration-4 init command cannot finish — even at stub level, the directory must exist on disk and the integration must be the one that decides where. Co-equal with P1 registry lookup.

**Independent Test**: Construct a temp `project_root`, build a minimal valid manifest, instantiate `ClaudeIntegration`, call `setup(project_root, manifest, parsed_options=None)`. Assert the directory `<project_root>/.claude/skills/` exists and contains a placeholder marker file. Repeat with `GenericIntegration` and `parsed_options={"skills_dir": ".cursor/skills"}`. Assert `<project_root>/.cursor/skills/` exists with a placeholder marker. Call `setup()` a second time on the same project_root and assert no exception is raised and the on-disk state is unchanged.

**Acceptance Scenarios**:

1. **Given** a clean project_root and `ClaudeIntegration`, **When** `setup(project_root, manifest, None)` runs, **Then** `<project_root>/.claude/skills/` exists with all parents created and a placeholder marker file is present inside it.
2. **Given** a clean project_root and `GenericIntegration`, **When** `setup(project_root, manifest, None)` runs, **Then** `<project_root>/.agents/skills/` exists with a placeholder marker file present inside it.
3. **Given** a clean project_root and `GenericIntegration`, **When** `setup(project_root, manifest, {"skills_dir": ".cursor/skills"})` runs, **Then** `<project_root>/.cursor/skills/` exists with a placeholder marker, and `<project_root>/.agents/skills/` is NOT created.
4. **Given** a project_root where `setup()` has already run successfully, **When** `setup()` runs a second time with the same arguments, **Then** the call succeeds without raising and the on-disk state is identical (idempotent).
5. **Given** a `setup()` call in this iteration, **When** it completes, **Then** no file outside the resolved skills directory has been mutated (no source-commands read, no SKILL.md emitted, no `CLAUDE.md` touched) — those concerns belong to iteration 9.

---

### User Story 3 - Parse and validate `--integration-options` against an integration's declared options (Priority: P1)

A user invokes `bookwright init my-novel --integration generic --integration-options="--skills-dir .cursor/skills"`. The CLI hands the raw `--integration-options` string and the chosen integration class to a parsing layer. That layer compares the supplied flags against the options the integration declares via its `options()` classmethod, produces a typed dict on success, and raises a precise structured error on any mismatch — naming the integration, the rejected flag, and the list of valid flags.

**Why this priority**: Without this layer the user can pass anything in `--integration-options` and the system will either silently ignore it or break in a confusing way downstream. Strict, surgical option validation is the only way the user can self-correct mistakes without reading source code. P1 because iteration 4 cannot ship a usable `init` command without it.

**Independent Test**: Take `GenericIntegration` and call the parser with the string `"--skills-dir .cursor/skills"`. Assert the result is `{"skills_dir": ".cursor/skills"}`. Repeat with `"--skills-dir=.cursor/skills"` (equals form) and assert the same result. Pass an unknown flag (`"--bogus xyz"`) and assert a structured error is raised whose payload names the integration key (`"generic"`), the rejected flag (`"--bogus"`), and the valid flag list (`["--skills-dir"]`). Pass a malformed input (e.g., `"--skills-dir"` with no value) and assert a structured error naming the violation.

**Acceptance Scenarios**:

1. **Given** `GenericIntegration` and the input `"--skills-dir .cursor/skills"`, **When** the parser runs, **Then** the returned dict is `{"skills_dir": ".cursor/skills"}` and no error is raised.
2. **Given** `GenericIntegration` and the input `"--skills-dir=.cursor/skills"`, **When** the parser runs, **Then** the returned dict is `{"skills_dir": ".cursor/skills"}`.
3. **Given** `GenericIntegration` and an empty/absent input, **When** the parser runs, **Then** the returned dict is `{}` and no error is raised.
4. **Given** `ClaudeIntegration` (which declares no options) and an empty/absent input, **When** the parser runs, **Then** the returned dict is `{}`.
5. **Given** `ClaudeIntegration` and any non-empty input (e.g., `"--skills-dir x"`), **When** the parser runs, **Then** a structured error is raised whose payload names `"claude"`, the rejected flag `"--skills-dir"`, and the empty list of valid flags.
6. **Given** `GenericIntegration` and an unknown flag input (e.g., `"--bogus x"`), **When** the parser runs, **Then** a structured error is raised whose payload names `"generic"`, the rejected flag `"--bogus"`, and the valid flag list `["--skills-dir"]`.
7. **Given** `GenericIntegration` and a malformed input (`--skills-dir` declared as type `"string"` with no following value), **When** the parser runs, **Then** a structured error is raised whose payload names the offending flag and the rule that was violated (`missing_value`).
8. **Given** any integration and a duplicate flag input (same flag supplied twice), **When** the parser runs, **Then** a structured error is raised whose payload names the duplicated flag.

---

### User Story 4 - Inspect integration metadata and capabilities (Priority: P2)

A consumer (the iteration-4 `init` command surfacing the `[integration]` block in `manifest.toml`, a future `bookwright integrations list --json` subcommand, the iteration-9 skills materializer choosing whether to emit a `tools:` line in SKILL.md) needs to read an integration's declared metadata — its display name, install URL, whether it requires a CLI installed locally, its default skills directory — and the three Agent Skills capability flags (dynamic context injection, subagents, tool restrictions).

**Why this priority**: Nothing in this iteration consumes the capability flags at runtime; they exist so iteration 9 can branch on them when rendering SKILL.md and so `init` can present a coherent view of the chosen integration. They MUST be declared and stable from day one. P2 because no end-user-facing failure depends on them landing in this iteration.

**Independent Test**: Instantiate `ClaudeIntegration` and `GenericIntegration`. Read `key`, `config["name"]`, `config["install_url"]`, `config["requires_cli"]`, `default_skills_dir`, `supports_dynamic_context`, `supports_subagents`, `supports_tool_restrictions` on each. Assert each value matches the locked table in Requirements (FR-007, FR-008).

**Acceptance Scenarios**:

1. **Given** `ClaudeIntegration`, **When** its metadata is inspected, **Then** `key == "claude"`, `default_skills_dir == ".claude/skills"`, `config["name"] == "Claude Code"`, `config["install_url"] == "https://docs.claude.com/claude-code"`, `config["requires_cli"] is True`, and `config["context_file"] == "CLAUDE.md"`.
2. **Given** `ClaudeIntegration`, **When** its capability flags are inspected, **Then** `supports_dynamic_context`, `supports_subagents`, and `supports_tool_restrictions` are all `True`.
3. **Given** `GenericIntegration`, **When** its metadata is inspected, **Then** `key == "generic"`, `default_skills_dir == ".agents/skills"`, `config["name"] == "Generic (Agent Skills standard)"`, `config["install_url"] == "https://agentskills.io"`, and `config["requires_cli"] is False`.
4. **Given** `GenericIntegration`, **When** its capability flags are inspected, **Then** `supports_dynamic_context`, `supports_subagents`, and `supports_tool_restrictions` are all `False`.
5. **Given** the `SkillsIntegration` base class, **When** the three capability flags are inspected on the unsubclassed base, **Then** they all default to `False`, so a new integration that forgets to declare them does not silently inherit Claude-Code-specific assumptions.

---

### User Story 5 - Add a new integration as a self-contained subpackage (Priority: P3)

A future contributor (post-v0: Copilot, Cursor-specific extensions, etc.) wants to add a new integration. The contract is: drop a new subpackage under the integrations directory that defines a `SkillsIntegration` subclass, and append one line to `_register_builtins()` so the registry picks it up at import time. No existing code anywhere else in the codebase needs to be edited. The new integration is immediately discoverable via the registry, accepts the same `setup()` shape, and may declare its own options.

**Why this priority**: This is the architectural promise of the registry — true plugin-ability — but no v0 user-visible feature breaks if it is verified only by a smoke test. P3 because there is no real-world third integration in v0; the test exists to lock the contract so iteration 4+ refactors don't silently break it.

**Independent Test**: In a test, declare a stub `FakeIntegration(SkillsIntegration)` with key `"fake"`, default skills dir `".fake/skills"`, all capabilities `False`, and no options. Insert it into `INTEGRATION_REGISTRY` (simulating what `_register_builtins()` would do). Assert: looking it up by `"fake"` returns the class; `resolve_skills_dir(None)` returns `Path(".fake/skills")`; `setup()` (inherited from base) creates the directory and writes the placeholder; the test required zero edits to `claude/`, `generic/`, or the base class itself.

**Acceptance Scenarios**:

1. **Given** a new `FakeIntegration(SkillsIntegration)` subclass declared in a test, **When** it is registered via `INTEGRATION_REGISTRY[FakeIntegration.key] = FakeIntegration`, **Then** registry lookup by `"fake"` returns it and the listing function includes `"fake"`.
2. **Given** the same `FakeIntegration` and a temp project_root, **When** `setup()` runs against it, **Then** `<project_root>/.fake/skills/` exists with the placeholder marker (the base-class `setup()` does the work; the subclass needed no override).
3. **Given** a `FakeIntegration` that declares its own `options()` list (e.g., one `--scope` string flag), **When** the parser is called against it, **Then** the `--scope` flag is accepted and unknown flags are rejected — without any code change to the parser itself.

---

### Edge Cases

- A caller asks the registry for the empty string or `None` → treated as an unknown key; the same structured error is raised as for any other unknown key.
- The `--integration-options` string contains shell-quoted values (e.g., `--skills-dir "path with spaces/skills"`) → parsed via shlex semantics; the quoted value reaches the integration intact.
- The `--integration-options` string contains a value that itself starts with `--` (e.g., `--skills-dir --foo`) → the parser treats the second token as the value of `--skills-dir` only when the option's type is `"string"`; if the option's type is `"flag"`, the second `--foo` is rejected as an unknown flag. The parser does not invent positional arguments.
- `setup()` is called against a `project_root` that does not exist on disk → the parent path is created along with the skills directory; this iteration does not refuse to materialize into a fresh tree (the iteration-4 `init` command owns project-root pre-existence policy).
- `setup()` is called against a `project_root` where the resolved skills directory already exists with arbitrary contents the user authored → the directory is not deleted, no user files are overwritten, the placeholder marker is written only if it is missing.
- An integration declares an `IntegrationOption` whose `flag` does not start with `--` → this is a programming error caught at class-definition / first-call time, not a user-facing validation; the error MUST surface clearly enough that a contributor adding a new integration sees the violation immediately.
- A future integration's `key` collides with an already-registered key → `_register_builtins()` MUST refuse the duplicate registration with an error that names both the colliding key and the already-registered class, rather than silently overwriting.

## Requirements *(mandatory)*

### Functional Requirements

**Central registry**

- **FR-001**: The system MUST expose a central integration registry keyed by short string identifier (e.g., `"claude"`, `"generic"`). The registry MUST be a single in-process source of truth populated at module-import time.
- **FR-002**: The system MUST provide a `_register_builtins()` routine that registers, at minimum, `ClaudeIntegration` under key `"claude"` and `GenericIntegration` under key `"generic"`. The routine MUST run once at module-import time. Re-running it MUST be safe (idempotent): re-registering the *same* class under its existing key is a no-op (no mutation, no exception), and registering a *different* class under an already-occupied key MUST raise `DuplicateRegistrationError` per FR-005. This guarantees `importlib.reload(bookwright.integrations)` is a safe operation in tests and tooling.
- **FR-003**: The system MUST provide a lookup function that, given a string key, returns the integration class. For any key not in the registry — including the empty string and any non-string-convertible input — the lookup MUST raise a structured `UnknownIntegrationError` whose payload contains the rejected key and the full list of currently-registered keys in alphabetic order.
- **FR-004**: The system MUST provide a listing function that returns the keys currently in the registry in stable alphabetic order. Order MUST NOT depend on registration order.
- **FR-005**: `_register_builtins()` MUST refuse to register two classes under the same key. The second registration MUST raise an error that names the colliding key and identifies both the already-registered class and the would-be replacement.

**Integration metadata**

- **FR-006**: Every integration class MUST declare, as class attributes: `key` (str), `config` (dict containing at minimum `name: str`, `install_url: str`, `requires_cli: bool`, and optionally `context_file: str`), and `default_skills_dir` (str interpretable as a relative POSIX path).
- **FR-007**: `ClaudeIntegration` MUST declare: `key = "claude"`, `default_skills_dir = ".claude/skills"`, `config = {"name": "Claude Code", "install_url": "https://docs.claude.com/claude-code", "requires_cli": True, "context_file": "CLAUDE.md"}`.
- **FR-008**: `GenericIntegration` MUST declare: `key = "generic"`, `default_skills_dir = ".agents/skills"`, `config = {"name": "Generic (Agent Skills standard)", "install_url": "https://agentskills.io", "requires_cli": False}`. The `context_file` key MUST NOT be present in `GenericIntegration.config` (no managed context file for a neutral agent).

**Capability declarations**

- **FR-009**: Every integration MUST declare three boolean capability flags as class attributes: `supports_dynamic_context`, `supports_subagents`, `supports_tool_restrictions`. The base class `SkillsIntegration` MUST default all three to `False` so a subclass that forgets to declare them does not silently inherit Claude-Code-specific assumptions.
- **FR-010**: `ClaudeIntegration` MUST set all three capability flags to `True`. `GenericIntegration` MUST set all three to `False`.
- **FR-011**: The system MUST NOT, in this iteration, branch any behavior on the capability flags. The flags exist as declared metadata so iteration 9 (SKILL.md materialization) can read them when deciding whether to emit `!`shell`` blocks, subagent invocations, or `tools:` frontmatter restrictions.

**Integration options declaration**

- **FR-012**: Every integration class MUST expose an `options()` classmethod returning a list of `IntegrationOption` descriptors. Each descriptor MUST carry at minimum: `flag` (str, MUST start with `--`), `type` (one of `"flag"` or `"string"`), `required` (bool), `default` (`str | None`), `help` (str).
- **FR-013**: `ClaudeIntegration.options()` MUST return an empty list in v0.
- **FR-014**: `GenericIntegration.options()` MUST return exactly one option with `flag = "--skills-dir"`, `type = "string"`, `required = False`, `default = ".agents/skills"`, and a non-empty `help` string mentioning the default and that this is the override for the skills destination.
- **FR-015**: An `IntegrationOption` whose `flag` does not start with `--` MUST surface as a programming-error exception clearly enough that a contributor adding a new integration sees the violation immediately (not a user-facing validation; this is a class-definition guard).

**Integration options parsing**

- **FR-016**: The system MUST expose a parser that takes (a) the raw `--integration-options` string the user passed on the CLI (possibly empty or `None`), and (b) the chosen integration class. The parser MUST return a dict keyed by each option's flag normalized to identifier form: leading dashes stripped, internal hyphens converted to underscores (e.g., `--skills-dir` → key `skills_dir`).
- **FR-017**: The parser MUST accept both whitespace-separated and equals-separated forms for `"string"`-typed options (`--skills-dir X` and `--skills-dir=X`). The tokenization of the raw string MUST follow shlex semantics so shell-quoted values pass through intact.
- **FR-018**: The parser MUST raise a structured `UnknownOptionError` for any flag in the input that the integration does not declare. The error payload MUST contain the integration `key`, the rejected `flag` (as provided, with its leading dashes), and the alphabetically-sorted list of valid flags (which MAY be the empty list).
- **FR-019**: The parser MUST raise a structured `MalformedOptionError` when: (a) a `"string"`-typed option has no following value, (b) a `"flag"`-typed option is supplied a value, or (c) the same flag appears twice in the same input. The error payload MUST contain the offending flag and a stable rule identifier (e.g., `missing_value`, `unexpected_value`, `duplicate_flag`).
- **FR-020**: An empty or absent `--integration-options` input MUST yield `{}` and MUST NOT raise, regardless of the chosen integration. This short-circuit takes precedence over FR-021 — required-flag validation runs only against non-empty input.
- **FR-021**: For a non-empty `--integration-options` input (subject to FR-020), an option declared with `required = True` whose flag is absent from the tokenized input MUST raise a structured `MalformedOptionError` with rule `missing_required`. In v0 no integration declares `required = True`; this rule exists so future integrations get the validation for free.

**Skills directory resolution**

- **FR-022**: Every integration MUST expose `resolve_skills_dir(parsed_options: dict | None) -> Path` returning a `Path` derived from `parsed_options` when applicable, otherwise from `default_skills_dir`.
- **FR-023**: `ClaudeIntegration.resolve_skills_dir(...)` MUST always return `Path(".claude/skills")` regardless of `parsed_options` (no options declared; nothing to override).
- **FR-024**: `GenericIntegration.resolve_skills_dir(parsed_options)` MUST return `Path(parsed_options["skills_dir"])` when `parsed_options` is a non-empty dict containing `skills_dir`, and `Path(".agents/skills")` otherwise (input is `None`, `{}`, or contains no `skills_dir` key).
- **FR-025**: The returned `Path` MUST be a relative path (project-root relative). The `setup()` method, not `resolve_skills_dir()`, is responsible for combining it with the absolute `project_root`.

**setup() contract (stub level for this iteration)**

- **FR-026**: Every integration MUST expose `setup(project_root: Path, manifest, parsed_options: dict | None = None) -> None`. In this iteration, the base-class `setup()` MUST: (a) call `self.resolve_skills_dir(parsed_options)` to obtain the relative skills path, (b) compute the absolute target `project_root / relative_path`, (c) create that directory and any missing parents using `mkdir(parents=True, exist_ok=True)`, (d) write a placeholder marker file inside it (filename and contents defined in FR-027) iff the marker is not already present.
- **FR-027**: The placeholder marker file MUST be named `.bookwright-skills-placeholder` and its single-line text contents MUST identify the integration `key` and state that real SKILL.md materialization is deferred to iteration 9. The exact format is: `bookwright integration: <key> — SKILL.md materialization deferred to iteration 9\n`. The file exists so iteration 4 (`init`) has a positive signal that `setup()` ran and so iteration 9 can detect a v0-stub install and replace it.
- **FR-028**: `setup()` MUST be idempotent. Running it twice on the same `project_root` with the same arguments MUST NOT raise and MUST leave on-disk state byte-identical (no marker rewritten, no directory recreated). Running it after the user has manually placed real files inside the skills directory MUST NOT delete or overwrite any user-authored file; the marker is written only if it is missing.
- **FR-029**: `setup()` MUST NOT, in this iteration, read source command files from `resources/commands/`, render any `SKILL.md`, mutate `CLAUDE.md` (even when `ClaudeIntegration.config["context_file"]` declares it), or touch any file outside the resolved skills directory. Those concerns belong to iteration 9.
- **FR-030**: `setup()` MUST trust the `manifest` argument as already-validated (the iteration-2 manifest model owns validation) and MUST NOT re-validate it. The `manifest` parameter MAY be unused in this iteration's stub body and is part of the contract solely so iteration 9 can read fields from it (e.g., `manifest.book.title` for SKILL.md description enrichment) without a signature change.

**Plugin-extensibility contract**

- **FR-031**: The system MUST be structured so that adding a new integration requires only: (a) creating a new subpackage under `src/bookwright/integrations/<key>/` containing a class inheriting `SkillsIntegration`, and (b) registering that class in `_register_builtins()`. No edit to `ClaudeIntegration`, `GenericIntegration`, the base class, the registry lookup, the listing function, the options parser, the skills-dir resolver, or `setup()` MUST be required.
- **FR-032**: `SkillsIntegration` MUST be the only operative base class for v0 integrations. The system MUST NOT ship a `MarkdownIntegration` (or any other base class) that emits artifacts in legacy `.claude/commands/` or analogous non-Agent-Skills locations. This is a Constitution Principle VI hard line (see `bookwright-design.md` § 16, axiom 7).

**Agent Skills compliance constants**

- **FR-033**: The base class (or a sibling constants module imported by it) MUST expose three named constants that encode agentskills.io structural rules: a `SKILL_NAME_MAX_LENGTH` of 64, a `SKILL_DESCRIPTION_MAX_LENGTH` of 1024, and a documented invariant that the directory name housing a `SKILL.md` equals the `name:` value in its frontmatter. These constants MUST be referenced by FR-033 consumers (iteration 9's SKILL.md materializer and its tests) so the limits live in one place and tests can pin them.
- **FR-034**: This iteration MUST NOT generate any `SKILL.md` content; the constants from FR-033 exist as the contract for iteration 9. The presence of the constants in this iteration is what lets iteration 9 land without rediscovering them.

**Structured errors**

- **FR-035**: All errors raised by this layer — `UnknownIntegrationError`, `UnknownOptionError`, `MalformedOptionError`, the registration-collision error, and the bad-flag programming-error guard — MUST be structured exception types carrying at minimum: a stable string `code` (e.g., `unknown_integration`, `unknown_option`, `malformed_option`, `duplicate_registration`, `invalid_option_declaration`), a human-readable `message`, the offending `value` where applicable, and the list of valid alternatives (`valid`) where applicable.
- **FR-036**: Each structured error type MUST expose a serialization method (e.g., `to_dict()`) that returns a JSON-safe dict containing those fields. The method MUST NOT include traceback data, Python types, or any non-JSON-safe value. This is the surface iteration 4's `bookwright init --json` will use to honor the JSON-over-stdout contract (Constitution Principle IX).
- **FR-037**: This layer MUST NOT write to stdout or stderr. Errors are raised, never printed. Surfacing belongs to the CLI command layer that consumes this layer (iteration 4 onward).

### Key Entities *(include if feature involves data)*

- **IntegrationRegistry**: The in-process dictionary mapping integration keys (`str`) to integration classes. Populated once at module import via `_register_builtins()`. Single source of truth for "what integrations exist." Exposes lookup (FR-003), listing (FR-004), and rejects duplicate registrations (FR-005).
- **SkillsIntegration**: The only v0 operative base class for integrations. Defines the contract every integration MUST satisfy: declared class attributes (`key`, `config`, `default_skills_dir`), three capability flags (defaulting to `False`), the `options()` classmethod (defaulting to an empty list), `resolve_skills_dir(parsed_options)`, and the stub `setup(project_root, manifest, parsed_options)` that creates the resolved directory and writes the placeholder marker.
- **ClaudeIntegration**: Concrete subclass for Claude Code. Key `"claude"`, default skills dir `.claude/skills`, declares all three capability flags `True`, declares zero options.
- **GenericIntegration**: Concrete subclass for the neutral Agent Skills standard (Codex CLI, Cursor, VS Code Copilot, any agent that reads agentskills.io-compliant SKILL.md). Key `"generic"`, default skills dir `.agents/skills`, declares all three capability flags `False`, declares one option `--skills-dir`.
- **IntegrationOption**: Declarative descriptor for a single CLI option an integration accepts via `--integration-options`. Carries `flag`, `type` (`"flag"` or `"string"`), `required`, `default`, `help`. Immutable.
- **ParsedIntegrationOptions**: Dict-shaped result of parsing the raw `--integration-options` string against an integration's `options()` declaration. Keys are option flags normalized to identifier form (`--skills-dir` → `skills_dir`).
- **UnknownIntegrationError**: Structured error raised when the registry receives a lookup for a key it does not know. Payload: `code = "unknown_integration"`, `value = <rejected key>`, `valid = <alphabetic list of registered keys>`, `message`.
- **UnknownOptionError**: Structured error raised by the option parser when the input contains a flag the chosen integration does not declare. Payload: `code = "unknown_option"`, `integration = <key>`, `value = <rejected flag>`, `valid = <alphabetic list of valid flags>`, `message`.
- **MalformedOptionError**: Structured error raised by the option parser for syntactic violations (missing value, unexpected value, duplicate flag, missing required option). Payload: `code = "malformed_option"`, `rule = <stable rule id>`, `value = <offending flag>`, `message`.
- **PlaceholderMarker**: The single file `.bookwright-skills-placeholder` written inside the resolved skills directory by `setup()` in this iteration. Carries one line identifying the integration `key` and stating materialization is deferred to iteration 9. Iteration-9 contract: the marker is the v0-stub install signal and MAY be deleted when real `SKILL.md` files are written.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For both `"claude"` and `"generic"`, registry lookup returns a class whose `key` attribute equals the lookup key, in 100% of test invocations.
- **SC-002**: Registry lookup for any string not in the registry produces an `UnknownIntegrationError` whose `to_dict()` output contains the rejected key under `value` and an alphabetically-sorted list of registered keys under `valid` — the test asserts both fields on the same instance.
- **SC-003**: `ClaudeIntegration.resolve_skills_dir(parsed_options)` returns `Path(".claude/skills")` for every input drawn from `{None, {}, {"skills_dir": "anything"}}`. Three test cases, one assertion each.
- **SC-004**: `GenericIntegration.resolve_skills_dir(parsed_options)` returns `Path(".agents/skills")` when `parsed_options` is `None` or `{}`, and returns `Path(X)` whenever `parsed_options == {"skills_dir": X}` for representative non-empty values of `X` (including a path containing spaces wrapped through shlex earlier in the pipeline).
- **SC-005**: Parsing `--integration-options="--skills-dir .cursor/skills"` against `GenericIntegration.options()` produces the dict `{"skills_dir": ".cursor/skills"}`. Parsing `--integration-options="--bogus x"` produces an `UnknownOptionError` whose `to_dict()` output contains `integration == "generic"`, `value == "--bogus"`, and `valid == ["--skills-dir"]`. Both assertions in the same test slice.
- **SC-006**: After `setup(project_root, manifest, parsed_options)` runs on a clean temp project_root, the resolved skills directory exists on disk and `<resolved_dir>/.bookwright-skills-placeholder` exists with the single-line text identifying the integration key. Running `setup()` a second time leaves the marker file's bytes (asserted via `sha256(marker.read_bytes())`) identical to the first call (idempotent) and does not raise.
- **SC-007**: Adding a stub `FakeIntegration` in a test by directly inserting it into `INTEGRATION_REGISTRY` and running the registry lookup, the listing function, the option parser (against `FakeIntegration.options()`), `resolve_skills_dir`, and `setup` against it all succeed — the test asserts each one without modifying `claude/`, `generic/`, or the base class.
- **SC-008**: Every error type defined by this layer (`UnknownIntegrationError`, `UnknownOptionError`, `MalformedOptionError`, registration-collision, invalid-option-declaration) has a `to_dict()` method returning a dict that is `json.dumps`-able without a custom encoder. A single parametrized test covers all of them.
- **SC-009**: A grep / static-analysis check that this layer does not write to `sys.stdout` or `sys.stderr` from any `setup()`, parser, or registry function passes. (The intent is to enforce FR-037 mechanically; the exact check shape is the implementer's choice, but it MUST exist.)
- **SC-010**: The two agentskills.io constants `SKILL_NAME_MAX_LENGTH == 64` and `SKILL_DESCRIPTION_MAX_LENGTH == 1024` are exposed at importable module locations and are referenced (not duplicated) by every test or downstream module that needs them, verified by direct attribute assertion in this iteration's tests.

## Assumptions

- The `manifest` argument that `setup()` accepts comes from the iteration-2 manifest model and has already passed every validation rule of FR-004 through FR-024 of `specs/002-manifest-model/spec.md` by the time it reaches this layer. This iteration trusts it without re-validating.
- The `--integration-options` raw string is tokenized using `shlex.split` (POSIX mode). Shell-quoted values (`"path with spaces"`) pass through intact; the parser does not need to re-implement quoting.
- The placeholder marker file (`.bookwright-skills-placeholder`) is purely a "this iteration was here" artifact. It is not part of the user-visible project surface; it is gitignored by the iteration-4 `init` command's `.gitignore` template (this iteration does not own that template). Iteration 9 (SKILL.md materialization) MAY delete it when it writes real SKILL.md files; iteration 4 (`init`) treats its presence as the success signal of `setup()`.
- v0 integrations are exactly `claude` and `generic`. Copilot, Codex-specific, Cursor-specific, and any other integration is deferred to v0.4 per the Constitution's Scope & Release Discipline section. A PR adding a third integration in this iteration MUST be rejected.
- The CLI command layer (iteration 4 onward) owns surfacing of errors to the user and to the JSON envelope. This layer raises structured exceptions and never writes to a stream itself (FR-037).
- `_register_builtins()` runs at module-import time. Importing `bookwright.integrations` is therefore the act of populating the registry; consumers that need the registry populated MUST import the package (no explicit `_register_builtins()` call in user code).
- Forward-compat: when iteration 9 needs to read `supports_dynamic_context`, `supports_subagents`, or `supports_tool_restrictions` to decide what to render in `SKILL.md`, those flags are read from the class (not the instance) and the values are exactly the ones declared in FR-010. Changing those declared values in any subsequent iteration is a behavior change to materialization, not to this iteration's contract.
- The `[integration]` block written to `manifest.toml` by iteration 2 (per `specs/002-manifest-model/spec.md` FR-022) is independent of this iteration's runtime registry. The manifest stores `{key, skills_dir, options}` as informational metadata; this layer is the authority that interprets the same `key` at runtime to choose a class. The two views are deliberately kept loose so a project authored with one integration can be re-keyed without rewriting the manifest's other blocks.
