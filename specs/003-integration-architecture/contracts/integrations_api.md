# Contract: `bookwright.integrations` public API

**Branch**: `003-integration-architecture` | **Date**: 2026-05-28 |
**Plan**: [../plan.md](../plan.md) | **Data model**: [../data-model.md](../data-model.md)

This document fixes the importable surface of the integrations layer
shipped by iteration 3. Iteration 4 (`bookwright init`) and iteration 9
(`SKILL.md` materialization) consume exactly this surface; any rename,
signature change, or behaviour change after merge is a breaking change.

The shape of every `to_dict()` payload below is contractual (FR-036) —
the iteration-4 `init --json` consumer will assert against these fields.

---

## Package layout

```text
bookwright.integrations              # eagerly populates INTEGRATION_REGISTRY at import
├── __init__.py                      # INTEGRATION_REGISTRY, get, list_keys, _register_builtins
├── base.py                          # SkillsIntegration
├── options.py                       # IntegrationOption, parse_options
├── errors.py                        # 5 structured exception types
├── constants.py                     # SKILL_NAME_MAX_LENGTH, SKILL_DESCRIPTION_MAX_LENGTH, SKILL_PLACEHOLDER_MARKER_NAME
├── claude/__init__.py               # ClaudeIntegration
└── generic/__init__.py              # GenericIntegration
```

Importing `bookwright.integrations` is sufficient to populate the
registry — no caller needs to call `_register_builtins()` explicitly
(FR-002).

---

## Public symbols

### From `bookwright.integrations`

```python
INTEGRATION_REGISTRY: dict[str, type[SkillsIntegration]]

def get(key: str) -> type[SkillsIntegration]: ...
def list_keys() -> list[str]: ...

# Re-exports for convenience:
SkillsIntegration       # from .base
IntegrationOption       # from .options
parse_options           # from .options

# Re-exported error types (from .errors):
UnknownIntegrationError
UnknownOptionError
MalformedOptionError
DuplicateRegistrationError
InvalidOptionDeclarationError

# Re-exported constants (from .constants):
SKILL_NAME_MAX_LENGTH
SKILL_DESCRIPTION_MAX_LENGTH
SKILL_PLACEHOLDER_MARKER_NAME

# Internal — not part of the stable surface, but documented for plugin authors (US5):
_register_builtins      # populates INTEGRATION_REGISTRY at module-import time
_register               # the helper a future contributor wires into _register_builtins
```

`__all__` in `bookwright/integrations/__init__.py` MUST list exactly the
public symbols above (excluding `_register_builtins` and `_register`,
which are underscore-prefixed conventional internals).

---

### `get(key)`

```python
def get(key: str) -> type[SkillsIntegration]:
    """Look up an integration class by its short string key.

    Raises:
        UnknownIntegrationError: if `key` is not in INTEGRATION_REGISTRY.
            The payload contains the rejected key (verbatim — `str | None`,
            see data-model § 6.1) and the alphabetically-sorted list of
            currently-registered keys.

    Contract:
        - Non-string input is treated as unknown (the lookup uses dict
          containment; a non-string is just "not in the dict"). The
          UnknownIntegrationError payload's `value` field is therefore
          typed `str | None` and the test pins `value is None` for the
          `get(None)` path.
        - Empty string is treated as unknown.
        - The function MUST NOT print to stdout/stderr (FR-037).
    """
```

**Tests pin (US1, FR-001 → FR-005, SC-001, SC-002)**:
- `get("claude") is ClaudeIntegration`
- `get("generic") is GenericIntegration`
- `get("copilot")` raises `UnknownIntegrationError` with
  `to_dict() == {"code": "unknown_integration", "value": "copilot", "valid": ["claude", "generic"], "message": ...}`
- `get("")` and `get(None)` (via `cast(str, None)` or `# type: ignore`)
  both raise `UnknownIntegrationError`.

---

### `list_keys()`

```python
def list_keys() -> list[str]:
    """Return registered integration keys in alphabetic order.

    Contract:
        - Order is alphabetic, NOT insertion order (FR-004).
        - The returned list is a fresh list per call; callers may mutate
          it without affecting the registry.
    """
```

**Tests pin (US1, FR-004)**:
- `list_keys() == ["claude", "generic"]` in v0.
- After test-fixture insertion of a `FakeIntegration` with key `"fake"`,
  `list_keys() == ["claude", "fake", "generic"]`.

---

### `SkillsIntegration`

```python
class SkillsIntegration:
    """Base class for every Bookwright v0 integration."""

    # Class attributes (declared by subclasses; defaults on the base
    # exist solely so a subclass that forgets one fails loudly when
    # registered, not silently inherit Claude-Code-specific values).
    key: ClassVar[str] = ""                                # sentinel; MUST override
    config: ClassVar[dict[str, str | bool]] = {}           # MUST contain name, install_url, requires_cli
    default_skills_dir: ClassVar[str] = ""                 # MUST override

    supports_dynamic_context: ClassVar[bool] = False
    supports_subagents: ClassVar[bool] = False
    supports_tool_restrictions: ClassVar[bool] = False

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        """Default: empty list. Override to declare CLI options."""
        return []

    def resolve_skills_dir(
        self,
        parsed_options: dict[str, object] | None = None,
    ) -> Path:
        """Return the project-relative skills directory.

        Base implementation returns `Path(self.default_skills_dir)` and
        ignores `parsed_options`. Subclasses that declare options on
        `--integration-options` (e.g., GenericIntegration's
        --skills-dir) MUST override to honour them.
        """
        return Path(self.default_skills_dir)

    def setup(
        self,
        project_root: Path,
        manifest: "Manifest",
        parsed_options: dict[str, object] | None = None,
    ) -> None:
        """v0 stub: create the resolved skills dir + write the marker.

        Idempotent (FR-028). Never writes outside the resolved dir (FR-029).
        The manifest argument is part of the iteration-9 contract;
        unused in this iteration's body.

        Concretely:
            target = project_root / self.resolve_skills_dir(parsed_options)
            target.mkdir(parents=True, exist_ok=True)
            marker = target / SKILL_PLACEHOLDER_MARKER_NAME
            if not marker.exists():
                marker.write_text(
                    f"bookwright integration: {self.key} "
                    f"— SKILL.md materialization deferred to iteration 9\n",
                    encoding="utf-8",
                )
        """
```

**Tests pin (US2, FR-026 → FR-030, SC-006)**:
- After `ClaudeIntegration().setup(tmp, manifest, None)`:
  `(tmp / ".claude/skills").is_dir()` and
  `(tmp / ".claude/skills/.bookwright-skills-placeholder").read_text() == "bookwright integration: claude — SKILL.md materialization deferred to iteration 9\n"`.
- After `GenericIntegration().setup(tmp, manifest, None)`:
  `(tmp / ".agents/skills").is_dir()` and the marker is present.
- After `GenericIntegration().setup(tmp, manifest, {"skills_dir": ".cursor/skills"})`:
  `(tmp / ".cursor/skills").is_dir()`, marker present, and
  `(tmp / ".agents/skills").exists() is False`.
- Two consecutive `setup()` calls on the same `tmp`:
  `marker.read_bytes()` byte-identical pre/post second call (use a
  recorded `sha256` digest).
- After manually placing `(tmp / ".claude/skills/my-skill/SKILL.md")`,
  a second `setup()` call leaves that file untouched.
- A "no writes outside the resolved dir" test compares the set of files
  under `tmp` before and after `setup()` — only the resolved dir and
  the marker may be new.

---

### `IntegrationOption`

```python
@dataclass(frozen=True)
class IntegrationOption:
    flag: str                                # MUST start with "--"
    type: Literal["flag", "string"] = "flag"
    required: bool = False
    default: str | None = None
    help: str = ""
```

Constructed by subclasses inside `options()`. Direct construction by
consumers is allowed and used in tests.

**Tests pin (FR-012, FR-015)**:
- `IntegrationOption(flag="--skills-dir", type="string", default=".agents/skills", help="...")` round-trips its fields.
- Frozen: `dataclasses.FrozenInstanceError` on attribute assignment.
- `IntegrationOption(flag="skills-dir", ...)` is technically constructible
  (the dataclass itself does no validation), but the first time
  `parse_options` sees it, `InvalidOptionDeclarationError(rule="bad_flag_prefix")`
  is raised. Tests cover both: construction succeeds, parser rejects.

---

### `parse_options(raw, integration_cls)`

```python
def parse_options(
    raw: str | None,
    integration_cls: type[SkillsIntegration],
) -> dict[str, str | bool]:
    """Parse `--integration-options` raw input against an integration's options().

    Args:
        raw: the literal --integration-options string from the CLI.
             `None`, `""`, and whitespace-only inputs all yield `{}`.
        integration_cls: the integration class whose options() declares
                         the valid flag set.

    Returns:
        Dict keyed by each declared option's normalized identifier form
        (`--skills-dir` -> "skills_dir"). Values are `str` for type=string
        options, `True` for type=flag options. Options not present in
        the input are omitted from the returned dict (consumer applies
        defaults).

    Raises:
        InvalidOptionDeclarationError: if any descriptor in `integration_cls.options()`
            violates a structural rule (flag must start with --, type must
            be "flag" or "string"). Raised on first descriptor scan.
        UnknownOptionError: if the input contains a flag the integration
            does not declare.
        MalformedOptionError: if a string option has no value, a flag
            option has a value, the same flag appears twice, or a
            required option is missing.

    Contract:
        - Tokenizes via `shlex.split(raw, posix=True)`.
        - Accepts both whitespace (`--skills-dir X`) and equals
          (`--skills-dir=X`) forms for string options.
        - Never writes to stdout/stderr.
        - Returns a fresh dict per call.
    """
```

**Tests pin (US3, FR-016 → FR-021, SC-005)** — non-exhaustive,
parametrized table:

| Input                                       | `integration_cls`         | Expected                                                                                       |
|---------------------------------------------|---------------------------|------------------------------------------------------------------------------------------------|
| `None`                                      | any                       | `{}`                                                                                           |
| `""`                                        | any                       | `{}`                                                                                           |
| `"   "`                                     | any                       | `{}`                                                                                           |
| `"--skills-dir .cursor/skills"`             | `GenericIntegration`      | `{"skills_dir": ".cursor/skills"}`                                                             |
| `"--skills-dir=.cursor/skills"`             | `GenericIntegration`      | `{"skills_dir": ".cursor/skills"}`                                                             |
| `'--skills-dir "path with spaces/skills"'`  | `GenericIntegration`      | `{"skills_dir": "path with spaces/skills"}` (shlex passthrough)                                |
| `"--skills-dir x"`                          | `ClaudeIntegration`       | `UnknownOptionError(integration="claude", value="--skills-dir", valid=[])`                     |
| `"--bogus x"`                               | `GenericIntegration`      | `UnknownOptionError(integration="generic", value="--bogus", valid=["--skills-dir"])`           |
| `"--skills-dir"`                            | `GenericIntegration`      | `MalformedOptionError(rule="missing_value", value="--skills-dir")`                             |
| `"--skills-dir a --skills-dir b"`           | `GenericIntegration`      | `MalformedOptionError(rule="duplicate_flag", value="--skills-dir")`                            |
| `"--skills-dir --foo"`                      | `GenericIntegration`      | `{"skills_dir": "--foo"}` (string type, next token is the value)                               |
| an integration with a `flag`-typed option supplied a value | (test stub)| `MalformedOptionError(rule="unexpected_value", value=<flag>)`                                  |
| an integration with `required=True` option absent | (test stub)         | `MalformedOptionError(rule="missing_required", value=<flag>)`                                  |

---

### Exception payloads (`integrations/errors.py`)

Every exception MUST expose:
- a class-level `code: str` attribute (immutable),
- a constructor that captures the offending values on `self`,
- a `to_dict()` method returning a `json.dumps`-compatible dict,
- a `message: str` attribute (the human-readable form passed up to
  `Exception.__init__`).

The `to_dict()` shapes are pinned in [../data-model.md § 6](../data-model.md).
Tests in `tests/integrations/test_errors_json.py` parametrize over all
five types, instantiate each, call `to_dict()`, then `json.dumps(...)`
the result — round-trip success is the assertion (SC-008).

---

### Constants (`integrations/constants.py`)

```python
from typing import Final

SKILL_NAME_MAX_LENGTH: Final[int] = 64
SKILL_DESCRIPTION_MAX_LENGTH: Final[int] = 1024
SKILL_PLACEHOLDER_MARKER_NAME: Final[str] = ".bookwright-skills-placeholder"
```

**Tests pin (FR-033, FR-034, SC-010)**:
- `SKILL_NAME_MAX_LENGTH == 64`
- `SKILL_DESCRIPTION_MAX_LENGTH == 1024`
- `SKILL_PLACEHOLDER_MARKER_NAME == ".bookwright-skills-placeholder"`
- A grep / AST check verifies no other module re-declares the same
  numeric literal (the constants are the single source of truth).

---

## Behavioural invariants the layer publishes

These hold across every public entry point in this iteration. Tests
verify each one mechanically.

1. **No stdout/stderr writes.** AST scan of every `.py` under
   `src/bookwright/integrations/` rejects `print(...)`, `sys.stdout`,
   `sys.stderr` (SC-009, R7).
2. **`setup()` is idempotent.** Two consecutive calls with the same
   arguments leave on-disk state byte-identical (SC-006, FR-028).
3. **`setup()` writes only inside the resolved skills dir.** Before/after
   file-tree diff over `project_root` is empty except for the resolved
   skills directory and its marker (FR-029).
4. **Registry lookup is deterministic.** `get("claude")` always returns
   `ClaudeIntegration`; `list_keys()` always returns
   `["claude", "generic"]` (after `_register_builtins()` runs)
   (FR-001 → FR-004).
5. **Registration rejects duplicates by class identity, not key alone.**
   Re-registering the same `ClaudeIntegration` class with the same key
   is a no-op; registering a *different* class under the same key raises
   `DuplicateRegistrationError` (FR-002, FR-005, R5).
6. **Adding a new integration touches no existing source file under
   `integrations/claude/`, `integrations/generic/`, or
   `integrations/base.py`.** Verified mechanically by
   `test_plugin_contract.py` via content-hash snapshot (FR-031, SC-007,
   R8).

---

## Side effects on the iteration-2 manifest module

This iteration makes one surgical edit to
`src/bookwright/core/manifest.py`:

**Before** (iteration 2):
```python
DEFAULT_SKILLS_DIR: dict[str, str] = {
    "claude": ".claude/skills",
    "generic": ".agents/skills",
}
```

**After** (iteration 3, derived from the integrations registry):
```python
def _default_skills_dir_map() -> dict[str, str]:
    """Late-imported view of the integrations registry, used by
    _build_manifest to fill the per-key skills_dir default."""
    from bookwright.integrations import INTEGRATION_REGISTRY
    return {key: cls.default_skills_dir for key, cls in INTEGRATION_REGISTRY.items()}
```

with `_build_manifest` (in `core/_build.py`) calling
`_default_skills_dir_map()` at build time instead of indexing the module-
level dict.

**Why this is not a breaking change to iteration 2**:
- The FR-022 promise of iteration 2 ("manifest reads/writes `[integration]`
  as opaque data") covers `Manifest.load()` and `Manifest.dump()`. Both
  are unchanged.
- `Manifest.build(...)` (FR-015 → FR-017 of iteration 2) is the only
  consumer of the per-key default. Its public signature is unchanged.
- An iteration-2 test that asserted the literal dict shape (if any)
  needs to assert the derivation shape instead — this is a one-line
  test edit, not a contract change.
- The integrations registry and the manifest module both agree on the
  string `".claude/skills"` and `".agents/skills"` because those strings
  live in exactly one place (each integration class), satisfying the
  single-source-of-truth norm the user locked in `9753ebf` (R2).
