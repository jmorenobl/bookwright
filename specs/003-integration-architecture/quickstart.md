# Quickstart: Integration Architecture

**Branch**: `003-integration-architecture` | **Date**: 2026-05-28 |
**Plan**: [plan.md](plan.md) | **Contract**: [contracts/integrations_api.md](contracts/integrations_api.md)

This iteration ships no new user-facing CLI command. The integration
layer is a *library* consumed by iteration 4's `bookwright init` and
iteration 9's skills materializer. This quickstart is therefore for
**implementers and downstream-consumer authors** — the people who will
write code against `bookwright.integrations` once iteration 3 merges.

If you are an end user looking for "how do I run bookwright?", you are
in the wrong iteration. Skip to iteration 4 (`bookwright init`).

---

## Setup

```bash
git checkout 003-integration-architecture
uv sync
uv run pytest tests/integrations/ -v
```

All tests in `tests/integrations/` MUST pass before any consumer of the
layer (iteration 4 onward) is written.

---

## Five things you'll do with this layer

### 1. Look up an integration by key

```python
from bookwright.integrations import get, list_keys, UnknownIntegrationError

assert list_keys() == ["claude", "generic"]

ClaudeCls = get("claude")     # -> ClaudeIntegration
GenericCls = get("generic")   # -> GenericIntegration

try:
    get("copilot")
except UnknownIntegrationError as exc:
    payload = exc.to_dict()
    assert payload["code"] == "unknown_integration"
    assert payload["value"] == "copilot"
    assert payload["valid"] == ["claude", "generic"]
```

### 2. Inspect an integration's metadata before instantiating

```python
from bookwright.integrations import get

cls = get("claude")
assert cls.key == "claude"
assert cls.default_skills_dir == ".claude/skills"
assert cls.config["name"] == "Claude Code"
assert cls.config["install_url"] == "https://docs.claude.com/claude-code"
assert cls.config["requires_cli"] is True
assert cls.config["context_file"] == "CLAUDE.md"
assert cls.supports_dynamic_context is True
assert cls.supports_subagents is True
assert cls.supports_tool_restrictions is True
```

`GenericIntegration` mirrors the structure but without
`config["context_file"]` and with all three capability flags `False`.

### 3. Parse the user's `--integration-options` string

```python
from bookwright.integrations import (
    get, parse_options,
    UnknownOptionError, MalformedOptionError,
)

GenericCls = get("generic")

# Happy paths
assert parse_options(None, GenericCls) == {}
assert parse_options("", GenericCls) == {}
assert parse_options("--skills-dir .cursor/skills", GenericCls) == {"skills_dir": ".cursor/skills"}
assert parse_options("--skills-dir=.cursor/skills", GenericCls) == {"skills_dir": ".cursor/skills"}

# Error paths
try:
    parse_options("--bogus xyz", GenericCls)
except UnknownOptionError as exc:
    payload = exc.to_dict()
    assert payload["code"] == "unknown_option"
    assert payload["integration"] == "generic"
    assert payload["value"] == "--bogus"
    assert payload["valid"] == ["--skills-dir"]

try:
    parse_options("--skills-dir", GenericCls)  # no value
except MalformedOptionError as exc:
    payload = exc.to_dict()
    assert payload["code"] == "malformed_option"
    assert payload["rule"] == "missing_value"
    assert payload["value"] == "--skills-dir"
```

### 4. Materialize the integration into a project

```python
from pathlib import Path
from bookwright.core import Manifest
from bookwright.integrations import get, parse_options

project_root = Path("/tmp/my-novel")
project_root.mkdir(parents=True, exist_ok=True)

cls = get("generic")
parsed = parse_options("--skills-dir .cursor/skills", cls)
manifest = Manifest.build(
    title="My Novel", author="Alice", language="en",
    type_="novel", status="idea", integration_key="generic",
    # ... other build kwargs filled per iteration-2 contract
)

instance = cls()
instance.setup(project_root, manifest, parsed)

skills_dir = project_root / ".cursor/skills"
assert skills_dir.is_dir()
marker = skills_dir / ".bookwright-skills-placeholder"
assert marker.read_text() == (
    "bookwright integration: generic "
    "— SKILL.md materialization deferred to iteration 9\n"
)

# Idempotent: second call is a no-op.
instance.setup(project_root, manifest, parsed)
# marker bytes are byte-identical to before.
```

### 5. Resolve the skills directory without running setup

```python
from bookwright.integrations import get

# Claude ignores parsed_options entirely.
claude = get("claude")()
assert claude.resolve_skills_dir() == Path(".claude/skills")
assert claude.resolve_skills_dir({}) == Path(".claude/skills")
assert claude.resolve_skills_dir({"skills_dir": "ignored"}) == Path(".claude/skills")

# Generic honours parsed_options when present.
generic = get("generic")()
assert generic.resolve_skills_dir() == Path(".agents/skills")
assert generic.resolve_skills_dir({}) == Path(".agents/skills")
assert generic.resolve_skills_dir({"skills_dir": ".cursor/skills"}) == Path(".cursor/skills")
```

`resolve_skills_dir` returns a **project-relative** `Path`. Combine it
with `project_root` yourself — `setup()` does this internally.

---

## Adding a new integration (post-v0 contract)

This is the path a future contributor (Cursor-specific extensions,
Copilot, etc.) follows. It is proven mechanically in
`tests/integrations/test_plugin_contract.py` (US5, FR-031).

1. Create `src/bookwright/integrations/<your_key>/__init__.py`:
   ```python
   from ..base import SkillsIntegration
   # IntegrationOption import only if you declare options.

   class YourIntegration(SkillsIntegration):
       key = "<your_key>"
       default_skills_dir = ".your/skills"
       config = {
           "name": "Your Agent",
           "install_url": "https://...",
           "requires_cli": False,
       }
       supports_dynamic_context = False
       supports_subagents = False
       supports_tool_restrictions = False
   ```

2. Add one line to `_register_builtins()` in
   `src/bookwright/integrations/__init__.py`:
   ```python
   from .your_key import YourIntegration   # at the top of the module

   def _register_builtins() -> None:
       _register(ClaudeIntegration)
       _register(GenericIntegration)
       _register(YourIntegration)          # NEW
   ```

3. Add `tests/integrations/test_your_key.py` mirroring `test_metadata.py`
   and `test_resolve_skills_dir.py`.

That is the complete change set. No edit to `base.py`, `options.py`,
`errors.py`, `constants.py`, `claude/`, or `generic/` is permitted. The
plugin-contract test will fail if any of those files is touched.

Per the v0 Scope & Release Discipline section of the constitution, do
not attempt to land a third integration in v0 — that is v0.4 work.

---

## What this iteration deliberately does **not** do

- No real `SKILL.md` rendering. The marker file is the entire v0 output
  (FR-026 → FR-030, FR-034). Iteration 9 owns the real materializer.
- No `bookwright` CLI subcommand. Iteration 4 wires `bookwright init`
  on top of this layer.
- No new third-party runtime dependency.
- No mutation of `CLAUDE.md`, `resources/commands/`, or any file
  outside the resolved skills directory (FR-029).
- No third integration registered (FR-031, Scope & Release Discipline).

---

## Validating your install

Run the integration-layer slice of the test suite and assert coverage
clears the iteration target:

```bash
uv run pytest tests/integrations/ -v --cov=bookwright.integrations --cov-report=term-missing
```

The expected slice-level coverage is ≥ 95 % (the layer is small and the
test plan in [plan.md](plan.md) covers every branch). The global
`--cov-fail-under=80` gate in `pyproject.toml` continues to apply across
the whole project.

Additional sanity checks:

```bash
uv run ruff check src/bookwright/integrations tests/integrations
uv run ruff format --check src/bookwright/integrations tests/integrations
uv run mypy --strict src/bookwright/integrations tests/integrations
```

All four MUST pass before this branch is mergeable (Constitution
Principle II / Technical Constraints).
