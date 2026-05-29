# Phase 1 — Data Model: Integration Architecture

**Branch**: `003-integration-architecture` | **Date**: 2026-05-28 |
**Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

Every entity below is in-process state (Python objects). Nothing in this
iteration persists data beyond the one marker file written by `setup()`.
"Storage" rows are therefore "in-memory only" except where noted.

The contract surface — class names, attribute names, exception names,
method signatures — is what iteration 4 (`init`) and iteration 9 (skills
materialization) will import. Renaming any of these after this iteration
merges is a breaking change. The shapes of the JSON `to_dict()` outputs
are also part of the contract (FR-036; iteration-4 `--json` consumer).

---

## 1. `IntegrationOption`

**Purpose**: Immutable declarative descriptor for one CLI option an
integration accepts inside `--integration-options`. Each integration's
`options()` classmethod returns a list of these.

**Shape**: `@dataclass(frozen=True)` in `integrations/options.py`.

| Field      | Type            | Required | Default | Notes                                                                                       |
|------------|-----------------|----------|---------|---------------------------------------------------------------------------------------------|
| `flag`     | `str`           | yes      | —       | MUST start with `--` (FR-012, FR-015). Validated at descriptor-construction time.            |
| `type`     | `Literal["flag", "string"]` | yes | —    | Drives parser behaviour. `"flag"` = boolean presence; `"string"` = takes a following value. |
| `required` | `bool`          | no       | `False` | When `True`, absence of the flag in parsed input raises `MalformedOptionError(rule="missing_required")` (FR-021). |
| `default`  | `str \| None`   | no       | `None`  | The default *value* if the flag is absent; *not* applied by the parser — consumer (e.g., `resolve_skills_dir`) decides whether to consult it. |
| `help`     | `str`           | no       | `""`    | Human-readable help text. Surfaced by iteration-4 `init --help-integration <key>` (not in this iteration's scope; the field is stored so iteration 4 can render it). |

**Validation rules**:
- `flag.startswith("--")` MUST be true; violation raises
  `InvalidOptionDeclarationError(value=flag, rule="bad_flag_prefix")` at
  the moment `parse_options` (or any direct introspection) first reads
  the descriptor. This is the "programming error" guard of FR-015.
- `type` MUST be exactly `"flag"` or `"string"`; any other string is an
  `InvalidOptionDeclarationError(value=type, rule="bad_type")`.

**Relationships**: An `IntegrationOption` is owned by exactly one
`SkillsIntegration` subclass, returned via `cls.options()`. The same
option object MUST NOT appear in more than one integration's list (the
parser keys on `flag`, so a shared object would be aliased state across
integrations).

**Storage**: In-memory only; constructed at class-import time by
`options()`.

---

## 2. `SkillsIntegration` (base class)

**Purpose**: The only operative v0 base class for integrations. Defines
the contract every integration MUST satisfy: declared class attributes,
the three capability flags (defaulting to `False`), the `options()`
classmethod (defaulting to an empty list), `resolve_skills_dir(...)`, and
the stub `setup(...)` that owns directory creation and marker writing.

**Shape**: regular class in `integrations/base.py`. Not a
`Protocol` — design § 11 shows `IntegrationBase` as a Protocol and
`SkillsIntegration` as the concrete base; this iteration ships only
`SkillsIntegration` (the Protocol is a documentation shape, not a
runtime artefact in v0).

**Class attributes (declared by subclasses)**:

| Attribute              | Type                                    | Default on base | Notes                                                                                                                       |
|------------------------|-----------------------------------------|-----------------|-----------------------------------------------------------------------------------------------------------------------------|
| `key`                  | `ClassVar[str]`                         | `""` (sentinel) | MUST be overridden by every concrete subclass. `""` on the base class is sentinel; any attempt to register the base raises. |
| `config`               | `ClassVar[dict[str, str \| bool]]`       | `{}`            | MUST contain at minimum `{"name", "install_url", "requires_cli"}`. MAY contain `"context_file"`. Other keys allowed for forward-compat. |
| `default_skills_dir`   | `ClassVar[str]`                         | `""`            | Project-relative POSIX path. The single source of truth (FR-007, FR-008) — manifest defaults derive from this (R2).        |
| `supports_dynamic_context`    | `ClassVar[bool]`                 | `False`         | Capability flag (FR-009, FR-010). Pure metadata in this iteration.                                                          |
| `supports_subagents`          | `ClassVar[bool]`                 | `False`         | Capability flag.                                                                                                            |
| `supports_tool_restrictions`  | `ClassVar[bool]`                 | `False`         | Capability flag.                                                                                                            |

**Classmethods / methods**:

```python
@classmethod
def options(cls) -> list[IntegrationOption]:
    """Return the integration's declared options. Default: []. (FR-012)"""
    return []

def resolve_skills_dir(
    self, parsed_options: dict[str, object] | None = None,
) -> Path:
    """Return the project-relative skills dir for this integration.
    Default: Path(self.default_skills_dir). Subclasses MAY override
    to honour parsed_options (FR-022 → FR-024).
    """

def setup(
    self,
    project_root: Path,
    manifest: "Manifest",  # TYPE_CHECKING-guarded import
    parsed_options: dict[str, object] | None = None,
) -> None:
    """v0 stub: create resolved skills dir + write placeholder marker.
    Idempotent; never writes outside the resolved dir (FR-026 → FR-030).
    """
```

**Invariants**:
- `setup()` MUST NOT read source-command files, MUST NOT render any
  `SKILL.md`, MUST NOT touch `CLAUDE.md`, MUST NOT write outside the
  resolved skills directory (FR-029). The base implementation is the
  only `setup()` body in v0; no subclass overrides it.
- `key` is the registry primary key. The base sentinel `""` lets
  `_register_builtins()` raise an `InvalidOptionDeclarationError`-shaped
  error (renamed for this site: `_RegistrationError` reusing the same
  base) if a subclass forgets to declare it. This is a defence-in-depth
  layer over FR-002 / FR-005.

**Relationships**: Subclassed by every integration in
`INTEGRATION_REGISTRY`. Consumed by `parse_options` (reads `cls.options()`),
by `setup()` (calls `self.resolve_skills_dir`), and by iteration 9's
materializer (reads `supports_*` flags).

**Storage**: In-memory only; classes loaded once per process.

---

## 3. `ClaudeIntegration`

**Purpose**: Concrete integration for Claude Code. Declares the locked
metadata of FR-007 and the all-`True` capability matrix of FR-010.

**Shape**: `class ClaudeIntegration(SkillsIntegration)` in
`integrations/claude/__init__.py`.

**Declared attributes** (all `ClassVar`, all locked by FR-007 + FR-010):

| Attribute                    | Value                                                                                                             |
|------------------------------|-------------------------------------------------------------------------------------------------------------------|
| `key`                        | `"claude"`                                                                                                        |
| `default_skills_dir`         | `".claude/skills"`                                                                                                |
| `config`                     | `{"name": "Claude Code", "install_url": "https://docs.claude.com/claude-code", "requires_cli": True, "context_file": "CLAUDE.md"}` |
| `supports_dynamic_context`   | `True`                                                                                                            |
| `supports_subagents`         | `True`                                                                                                            |
| `supports_tool_restrictions` | `True`                                                                                                            |

**Overrides**:
- `options(cls) -> list[IntegrationOption]`: returns `[]` (FR-013).
- `resolve_skills_dir(parsed_options) -> Path`: returns
  `Path(".claude/skills")` for every input (FR-023, SC-003). The base
  implementation would already do this since `default_skills_dir` is
  `".claude/skills"` and the base ignores `parsed_options`; the override
  is therefore optional. **Decision**: do not override — inherit the
  base behaviour to keep the no-options invariant visible.
- `setup`: inherited from base unchanged.

**Storage**: In-memory.

---

## 4. `GenericIntegration`

**Purpose**: Concrete integration for the neutral Agent Skills standard
(Codex CLI, Cursor, VS Code Copilot, any agent that reads
agentskills.io-compliant `SKILL.md`). Declares one option (`--skills-dir`)
and the all-`False` capability matrix.

**Shape**: `class GenericIntegration(SkillsIntegration)` in
`integrations/generic/__init__.py`.

**Declared attributes** (all `ClassVar`, all locked by FR-008 + FR-010):

| Attribute                    | Value                                                                                              |
|------------------------------|----------------------------------------------------------------------------------------------------|
| `key`                        | `"generic"`                                                                                        |
| `default_skills_dir`         | `".agents/skills"`                                                                                 |
| `config`                     | `{"name": "Generic (Agent Skills standard)", "install_url": "https://agentskills.io", "requires_cli": False}` (note: `context_file` MUST NOT be present — FR-008 explicit). |
| `supports_dynamic_context`   | `False`                                                                                            |
| `supports_subagents`         | `False`                                                                                            |
| `supports_tool_restrictions` | `False`                                                                                            |

**Overrides**:
- `options(cls) -> list[IntegrationOption]`: returns exactly one
  descriptor (FR-014):
  ```python
  IntegrationOption(
      flag="--skills-dir",
      type="string",
      required=False,
      default=".agents/skills",
      help=(
          "Directory where SKILL.md files are materialized. "
          "Default: .agents/skills (Codex/Cursor convention). "
          "Common alternatives: .cursor/skills, .github/skills."
      ),
  )
  ```
- `resolve_skills_dir(parsed_options) -> Path`: returns
  `Path(parsed_options["skills_dir"])` when `parsed_options` is a
  non-empty dict containing `"skills_dir"`, otherwise
  `Path(".agents/skills")` (FR-024, SC-004).
- `setup`: inherited from base unchanged.

**Storage**: In-memory.

---

## 5. `INTEGRATION_REGISTRY` (module-level state)

**Purpose**: The single in-process source of truth for "what integrations
exist." Maps a `str` key to a `SkillsIntegration` subclass.

**Shape**: `dict[str, type[SkillsIntegration]]` declared at the top of
`integrations/__init__.py`. Populated once at module-import time by
`_register_builtins()`.

**Invariants**:
- Single instance per process (module-level dict).
- Keys are exactly the strings declared by each registered class's `key`
  attribute. Reading `INTEGRATION_REGISTRY["claude"]` and reading
  `ClaudeIntegration.key` MUST yield the same string.
- Mutating the dict directly is supported as a *plugin* path (US5,
  FR-031); tests do this via a fixture that snapshots and restores the
  dict on teardown.
- Iteration order is insertion order (Python ≥ 3.7 dict). Public listing
  (`list_keys()`) re-sorts alphabetically per FR-004.

**Lifecycle**: populated at import time by `_register_builtins()`. Not
torn down — process-lifetime singleton.

**Relationships**: Consumed by:
- `get(key) -> type[SkillsIntegration]` (FR-003), the lookup function.
- `list_keys() -> list[str]` (FR-004), the listing function.
- Iteration 4's `bookwright init` to dispatch on `--integration <key>`.
- Iteration 9's materializer to enumerate "what skills layouts exist."
- `_build_manifest` in `core/_build.py` (via late import) to derive the
  per-key default `skills_dir` (R2).

---

## 6. Exception family (`integrations/errors.py`)

All five exception types share a private base `_IntegrationError(Exception)`
and follow the contract of FR-035 / FR-036. Each carries a class-level
`code` and a `to_dict()` returning a `json.dumps`-compatible dict.

### 6.1 `UnknownIntegrationError`

| Field         | Type       | Source            | Notes                                       |
|---------------|------------|-------------------|---------------------------------------------|
| `code`        | `str`      | class attribute   | Always `"unknown_integration"`.             |
| `value`       | `str`      | constructor arg   | The rejected key (may be `""`).             |
| `valid`       | `list[str]`| `list_keys()` at raise time | Alphabetically sorted, includes every currently-registered key. |
| `message`     | `str`      | derived           | `"unknown integration: {value!r}; valid: [a, b, ...]"` |

**Raised by**: `get(key)` when `key not in INTEGRATION_REGISTRY` (FR-003).

**`to_dict()` shape**:
```json
{"code": "unknown_integration", "value": "copilot", "valid": ["claude", "generic"], "message": "..."}
```

### 6.2 `UnknownOptionError`

| Field         | Type       | Source            | Notes                                       |
|---------------|------------|-------------------|---------------------------------------------|
| `code`        | `str`      | class attribute   | Always `"unknown_option"`.                  |
| `integration` | `str`      | constructor arg   | The `key` of the integration whose `options()` was consulted. |
| `value`       | `str`      | constructor arg   | The rejected flag with its leading dashes (e.g., `"--bogus"`). |
| `valid`       | `list[str]`| constructor arg   | Alphabetically sorted list of valid flags (may be `[]`).        |
| `message`     | `str`      | derived           | `"unknown option {value} for integration {integration!r}; valid: [...]"` |

**Raised by**: `parse_options(...)` when the input contains a flag the
integration does not declare (FR-018).

**`to_dict()` shape**:
```json
{"code": "unknown_option", "integration": "generic", "value": "--bogus", "valid": ["--skills-dir"], "message": "..."}
```

### 6.3 `MalformedOptionError`

| Field         | Type       | Source            | Notes                                       |
|---------------|------------|-------------------|---------------------------------------------|
| `code`        | `str`      | class attribute   | Always `"malformed_option"`.                |
| `rule`        | `str`      | constructor arg   | One of `"missing_value"`, `"unexpected_value"`, `"duplicate_flag"`, `"missing_required"`. |
| `value`       | `str`      | constructor arg   | The offending flag.                         |
| `message`     | `str`      | derived           | Human-readable, names the rule and the flag. |

**Raised by**: `parse_options(...)` per FR-019, FR-021.

**`to_dict()` shape**:
```json
{"code": "malformed_option", "rule": "missing_value", "value": "--skills-dir", "message": "..."}
```

### 6.4 `DuplicateRegistrationError`

| Field           | Type   | Source            | Notes                                                                   |
|-----------------|--------|-------------------|-------------------------------------------------------------------------|
| `code`          | `str`  | class attribute   | Always `"duplicate_registration"`.                                      |
| `value`         | `str`  | constructor arg   | The colliding key.                                                      |
| `existing`      | `str`  | constructor arg   | Fully-qualified class name of the already-registered integration (e.g., `"bookwright.integrations.claude.ClaudeIntegration"`). |
| `new`           | `str`  | constructor arg   | Fully-qualified class name of the would-be replacement.                 |
| `message`       | `str`  | derived           | Names key, existing class, and new class.                               |

**Raised by**: `_register(cls)` when the registry already holds a
*different* class under `cls.key` (FR-005, R5).

**`to_dict()` shape**:
```json
{"code": "duplicate_registration", "value": "claude", "existing": "...", "new": "...", "message": "..."}
```

### 6.5 `InvalidOptionDeclarationError`

| Field         | Type       | Source            | Notes                                       |
|---------------|------------|-------------------|---------------------------------------------|
| `code`        | `str`      | class attribute   | Always `"invalid_option_declaration"`.      |
| `rule`        | `str`      | constructor arg   | One of `"bad_flag_prefix"`, `"bad_type"`.   |
| `value`       | `str`      | constructor arg   | The offending attribute (the flag string or the type string). |
| `message`     | `str`      | derived           | Names rule and offending value; mentions that this is a programming error in the integration's declaration. |

**Raised by**: any consumer of `IntegrationOption` that detects a
malformed descriptor (the parser does this on first introspection of the
integration's `options()`). Per FR-015 this is a class-definition guard,
not a user-facing validation.

**`to_dict()` shape**:
```json
{"code": "invalid_option_declaration", "rule": "bad_flag_prefix", "value": "skills-dir", "message": "..."}
```

---

## 7. Agent Skills compliance constants

**Purpose**: One importable home for the two numeric agentskills.io
constants so iteration 9 and its tests reference (not duplicate) them.

**Shape**: module-level `Final[int]` declarations in
`integrations/constants.py`.

| Name                            | Type        | Value | Notes                                                                                                            |
|---------------------------------|-------------|-------|------------------------------------------------------------------------------------------------------------------|
| `SKILL_NAME_MAX_LENGTH`         | `Final[int]`| `64`  | FR-033, agentskills.io `name` field cap. Tests pin this directly (`assert SKILL_NAME_MAX_LENGTH == 64`).         |
| `SKILL_DESCRIPTION_MAX_LENGTH`  | `Final[int]`| `1024`| FR-033, agentskills.io `description` field cap.                                                                  |
| `SKILL_PLACEHOLDER_MARKER_NAME` | `Final[str]`| `".bookwright-skills-placeholder"` | The marker file `setup()` writes (FR-027). Centralised here so iteration 9 imports the same string when deciding what to replace. |

**Invariants**:
- FR-034 forbids this iteration from generating any `SKILL.md` content.
  The constants exist purely as the contract.
- The directory-name-equals-`name` invariant from FR-033 is documented
  in this module's docstring (it is structural, not numeric, so it
  cannot be a constant).

**Storage**: module-level; immutable.

---

## 8. `ParsedIntegrationOptions` (typed dict, not a class)

**Purpose**: The result type of `parse_options(raw, integration_cls)`.

**Shape**: structurally `dict[str, str | bool]` — keys are the normalized
identifier form of each declared flag (`--skills-dir` → `"skills_dir"`),
values are:
- the captured value for `type == "string"` options (always `str`);
- `True` for `type == "flag"` options when the flag was present.

There is no `TypedDict` declared in v0 because the keys are per-integration
and the static type does not gain expressive power from a single shared
type alias. The contract is documented here and in the parser's
docstring.

**Storage**: in-memory, short-lived (passed to `setup()` and discarded).

---

## State transitions & lifecycles

### Registry population (process startup)
1. First import of `bookwright.integrations` triggers
   `integrations/__init__.py`.
2. `from .claude import ClaudeIntegration` and
   `from .generic import GenericIntegration` execute — each subpackage
   declares its class as a side effect of module load.
3. `_register_builtins()` runs: `_register(ClaudeIntegration)`,
   `_register(GenericIntegration)`. After this, `INTEGRATION_REGISTRY ==
   {"claude": ClaudeIntegration, "generic": GenericIntegration}`.
4. Re-importing the module is a no-op (Python module cache). Force-reload
   (`importlib.reload`) re-runs `_register_builtins()`; the same-class
   branch in `_register` makes this idempotent (R5).

### Lookup path (`bookwright init` flow, iteration 4 will exercise)
1. `init` reads `--integration <key>`, calls
   `bookwright.integrations.get(key)`.
2. `get` raises `UnknownIntegrationError` if `key` is not registered;
   `init` translates that error into its `--json` envelope.
3. `init` calls `parse_options(raw, integration_cls)` to convert the
   `--integration-options` string into a typed dict; `init` translates
   `UnknownOptionError` / `MalformedOptionError` similarly.
4. `init` instantiates the class, calls
   `instance.setup(project_root, manifest, parsed_options)`. The base
   `setup()` creates `<project_root>/<resolved_skills_dir>/` and writes
   the marker (idempotently).

### `setup()` idempotency invariant
- First call: directory created, marker written.
- Second call (same args): directory `exist_ok=True` no-op; marker
  already present, no write. On-disk bytes identical.
- After a user authors files in the directory: those files preserved;
  marker still present (or written if missing).
