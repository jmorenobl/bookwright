# Phase 0 — Research: Integration Architecture

**Branch**: `003-integration-architecture` | **Date**: 2026-05-28 |
**Plan**: [plan.md](plan.md)

The spec has no `NEEDS CLARIFICATION` markers (the `/speckit-clarify` step
recorded that explicitly in `checklists/requirements.md`), and the
constitution-check gate in [plan.md](plan.md) passes without violations.
The questions resolved here are therefore *design choices the implementer
needs answers to* before writing code, not unresolved unknowns from the
spec.

Each entry follows the format:
- **Decision** — what was chosen.
- **Rationale** — why, grounded in spec FRs, the constitution, or design
  § 11.
- **Alternatives considered** — what else was on the table and why it
  was rejected.

---

## R1. Option-parser implementation: hand-rolled state machine, not `argparse`

**Decision**: Implement `parse_options(raw, integration_cls)` as a small
hand-rolled state machine over the `shlex.split(raw, posix=True)` token
list. It consults the integration's `options()` descriptors to (a) reject
unknown flags, (b) validate that `"string"`-typed options have a value,
(c) reject values supplied to `"flag"`-typed options, (d) reject duplicate
flags, (e) honour the equals form (`--skills-dir=X`) by splitting on the
first `=`. Returns a dict whose keys are the normalized identifier form of
each declared flag (`--skills-dir` → `skills_dir`).

**Rationale**:
- FR-018 / FR-019 mandate a structured `UnknownOptionError` /
  `MalformedOptionError` whose payload names the integration, the rejected
  flag, and the valid alternatives. `argparse`'s error path writes the
  message to stderr and calls `sys.exit(2)` — that violates FR-037 (no
  stdout/stderr writes from this layer) and FR-035 (errors must be
  raised, never printed) simultaneously.
- The valid-flag set in v0 is at most one entry (`GenericIntegration`'s
  `--skills-dir`; `ClaudeIntegration` declares none). The state machine
  is < 60 lines.
- `shlex.split` already handles quoted values, the spec's edge case for
  paths with spaces (`--skills-dir "path with spaces/skills"`).

**Alternatives considered**:
- **`argparse.ArgumentParser`**: Rejected. Customizing its error
  reporting to raise instead of `sys.exit` requires subclassing and
  monkey-patching `error()`, `exit()`, and `_print_message()`. The
  resulting code is longer than the hand-rolled version and harder to
  reason about under test.
- **Third-party CLI library** (e.g., `click`'s `Context.invoke` machinery,
  `cyclopts`): Rejected. The spec's parser surface is one function with
  one input string and one output dict. Adding a dependency for one
  function violates the spirit of Constitution Principle II (minimum
  dependencies).
- **Defer to Typer (the project's CLI library)**: Rejected. Typer is the
  surface for *user-facing* CLI options. `--integration-options` is a
  string that the user passes whole; the parser that interprets it is a
  domain-layer concern that runs inside `bookwright init`. Pulling
  Typer into the integrations layer would invert the dependency
  direction (the CLI consumes integrations; integrations must not
  consume the CLI).

---

## R2. `default_skills_dir` lives on the integration class; `core/manifest.py` derives, does not duplicate

**Decision**: The canonical per-key default skills directory is the
`default_skills_dir` class attribute on each integration (FR-007, FR-008).
The dict `DEFAULT_SKILLS_DIR = {"claude": ".claude/skills", "generic":
".agents/skills"}` currently in `src/bookwright/core/manifest.py:57-60`
is replaced with a derivation from the integrations registry,
performed via a late import inside `_build_manifest` (or its helper in
`core/_build.py`).

**Rationale**:
- The user's recent R1/R2/R4 closure (commit `9753ebf`,
  "single-source enum constants + coverage") makes "one declaration per
  domain constant" the active norm. Leaving two literal copies of
  `.claude/skills` and `.agents/skills` in the codebase — one in
  `manifest.py`, one in each integration class — guarantees they will
  drift.
- The iteration-2 spec's FR-022 says the manifest reads/writes the
  `[integration]` block as opaque data — it does *not* prohibit the
  build helper from consulting another module for a default during
  *construction*. The opacity promise covers `load()`, not `build()`.
- A late import inside `_build_manifest` (rather than a module-top
  import) keeps `bookwright.core` importable in isolation. The
  integrations package itself imports nothing from `bookwright.core`
  except, at type-check time, the `Manifest` annotation on `setup()` —
  and even that is a TYPE_CHECKING-guarded import. So no real cycle
  exists; the late import is belt-and-braces for future refactors.

**Alternatives considered**:
- **Keep the literal dict in `manifest.py`**: Rejected. Two sources of
  truth for the same string in the same codebase, contradicting the
  recently-locked norm.
- **Move the dict to a third "shared constants" module** (e.g.,
  `bookwright/shared/integrations_meta.py`): Rejected. There is already
  a clear owner — the integration class declares its own default. Adding
  a third module to hold a derivation is gratuitous indirection.
- **Have `manifest.py` import `INTEGRATION_REGISTRY` at module top**:
  Rejected. Eager cross-module imports between `core/` and
  `integrations/` widen the surface for future cycles; the late-import
  pattern is conventional and cheap.

---

## R3. Marker file: write only if missing, fixed content, no timestamp

**Decision**: `setup()` writes
`<resolved_skills_dir>/.bookwright-skills-placeholder` with the single-line
text `bookwright integration: <key> — SKILL.md materialization deferred to
iteration 9\n` (FR-027). The write happens only when the file is absent.
The content is fully determined by the integration's `key` — no
timestamp, no version, no host data.

**Rationale**:
- FR-028 mandates byte-identical idempotency. A timestamp would break
  this immediately on the second `setup()` call. Pinning content to
  `key` alone makes the property trivially observable in tests
  (`hashlib.sha256(file.read_bytes())` is stable across runs).
- The placeholder's only consumers are (a) iteration 4's `init`, which
  reads it as a "setup() ran" signal, and (b) iteration 9's
  materializer, which deletes/replaces it when real `SKILL.md` files
  land. Neither consumer needs metadata that a one-line tagged string
  doesn't already convey.
- "Write only if missing" preserves any user-authored file at the same
  name (extremely unlikely, but FR-028 explicitly requires
  not-overwriting user content).

**Alternatives considered**:
- **Include a timestamp / CLI version in the marker**: Rejected. Breaks
  FR-028 idempotency; iteration 9 already knows what version it is.
- **Use an empty file or `.gitkeep`**: Rejected. The marker carries
  identifying text so iteration 9 can tell a Bookwright-installed
  v0-stub directory apart from an arbitrary empty skills directory the
  user created by hand.
- **Write the marker into a hidden subdirectory** (e.g.,
  `<skills_dir>/.bookwright/`): Rejected. Adds a directory the user
  doesn't need to see and that iteration 9 has no reason to keep.

---

## R4. Structured-error class shape: one custom base, `to_dict()` is the contract

**Decision**: All five error types
(`UnknownIntegrationError`, `UnknownOptionError`, `MalformedOptionError`,
`DuplicateRegistrationError`, `InvalidOptionDeclarationError`) inherit
from a private `_IntegrationError(Exception)` and each declares:
- a class-level `code: str` (e.g., `"unknown_integration"`),
- an `__init__` that captures the offending value(s) on `self`,
- a `to_dict()` method returning a JSON-safe dict shaped per FR-035
  (always `{"code", "message"}`; `value` / `valid` / `integration` /
  `rule` added when relevant), and
- a human-readable `message` set on the exception itself.

**Rationale**:
- FR-036 requires the dict be `json.dumps`-able with no custom encoder.
  Returning only stdlib-JSON-compatible types (`str`, `list[str]`,
  `None`) makes that mechanical.
- A shared private base lets the `to_dict()` shape, the `code`
  convention, and a future `__init_subclass__` validation (asserting
  every subclass declares a non-empty `code`) live in one place.
- Inheriting from `Exception` (not `ValueError` or `RuntimeError`)
  prevents a `except ValueError` in caller code from accidentally
  catching one of our errors and losing the structured detail.

**Alternatives considered**:
- **Pydantic `BaseModel` errors**: Rejected. Pydantic models aren't
  exceptions; you would need to wrap them or use a hybrid class.
  Iteration 2's `ManifestWarning` is a `BaseModel`, but warnings are
  data, not exceptions. The asymmetry is intentional.
- **`dataclass(frozen=True)` carrying the payload + a wrapper
  exception**: Rejected. Forces every raise site to construct two
  objects (the dataclass and the exception around it). The fields are
  immutable in practice anyway because we only ever set them once in
  `__init__` and never mutate.
- **One single `IntegrationError` class with a `code` constructor arg**:
  Rejected. Loses `except UnknownOptionError as e:` precision in
  iteration-4 wiring; the `code` field is for serialization, the class
  hierarchy is for catch-clause selection.

---

## R5. `_register_builtins()` idempotency: re-call is safe; only conflicting registration raises

**Decision**: `_register_builtins()` is implemented as a loop over
`(ClaudeIntegration, GenericIntegration)` that calls a small helper
`_register(cls)`. The helper:
- looks up `cls.key` in `INTEGRATION_REGISTRY`;
- if absent, inserts `cls`;
- if present **and the registered value is the same class object**,
  is a no-op (this is the re-import / re-call path);
- if present **and the registered value is a different class**, raises
  `DuplicateRegistrationError(key, existing_cls=..., new_cls=...)`.

`_register_builtins()` is called once at the bottom of
`integrations/__init__.py`. Re-running it (which Python only does if
the module is force-reloaded, e.g., under test) is a no-op.

**Rationale**:
- FR-002 mandates "Re-running it MUST be safe (idempotent: same classes,
  same keys, no exception)." The same-class check satisfies this exactly.
- FR-005 mandates that two *different* classes under the same key raise
  with the colliding key + both classes named. The different-class
  branch satisfies this exactly.
- The split between `_register_builtins()` (the public entry point that
  ships the two built-ins) and `_register(cls)` (the helper used by both
  the loop and the US5 plugin path) is what gives the FR-031 promise:
  a future contributor adds one `_register(NewIntegration)` call without
  touching the loop body.

**Alternatives considered**:
- **`if cls.key not in REGISTRY: REGISTRY[cls.key] = cls`** (silent
  skip): Rejected. Hides the FR-005 collision case; a duplicate
  registration would be a no-op instead of an error, and the spec is
  explicit that it MUST raise.
- **`REGISTRY[cls.key] = cls`** (silent overwrite): Rejected for the
  same reason — and worse, because the second registration would win
  silently.
- **Registration via a decorator** (`@register("claude")`): Rejected.
  Cute, but adds a registration side effect at class-definition time
  which makes test isolation harder (you cannot construct a class
  without polluting the registry).

---

## R6. `parse_options(...)` returns `{}` for empty / `None` input — but malformed → raises

**Decision**: `parse_options(raw, integration_cls)` checks at the top:
if `raw` is `None` or `raw.strip() == ""`, return `{}` immediately,
regardless of the integration's declared `options()`. Validation of
required options (FR-021) happens **after** tokenization, so an empty
input on an integration with a required option WILL raise
`MalformedOptionError(rule="missing_required")` — but in v0 no
integration declares `required = True`, so this branch is exercised only
by the `FakeIntegration` test for the rule's existence.

**Rationale**:
- FR-020 is unambiguous: empty / absent input yields `{}` and MUST NOT
  raise, *regardless of the chosen integration*. The early-return is
  the simplest way to honour that.
- FR-021 is a forward-compat hook: it must exist for the parser to be
  complete, but no v0 integration triggers it. The test for it uses a
  stub integration so the rule's behaviour is locked without v0 callers
  depending on it.
- The two FRs don't conflict because no v0 integration combines an
  empty default with `required = True`. The empty-input early return
  short-circuits before the required-option check would fire, which is
  fine since no v0 integration declares `required = True`. If a future
  integration ever does, the `required` enforcement moves before the
  early return at that time — that is a v0.x change, not a v0 change.

**Alternatives considered**:
- **Always tokenize then loop**: Rejected. Adds two passes over an
  empty input for no benefit; the spec's "MUST yield `{}` and MUST NOT
  raise" is easier to read as a single short-circuit.
- **Conflate "empty input" with "all defaults applied"**: Rejected.
  Defaults are a downstream concern. The parser's job is to translate
  the user's literal input into a dict; default-filling is the
  consumer's responsibility (`resolve_skills_dir` itself is the one
  that consults `default_skills_dir` when `parsed_options` lacks the
  key).

---

## R7. `test_no_stdio.py`: AST scan of the integrations package — not a runtime monkey-patch

**Decision**: The FR-037 / SC-009 enforcement test is implemented as an
AST scan over every `.py` file under `src/bookwright/integrations/`.
The scan rejects any:
- call to `print` (at any name binding — `print(...)`),
- attribute access of `sys.stdout` / `sys.stderr` (`sys.stdout`,
  `sys.stderr`),
- `import sys` followed by a `sys.std*` use,
- `from sys import stdout / stderr`.

The test fails with a structured message naming the file, line, and the
offending construct.

**Rationale**:
- A runtime monkey-patch (`monkeypatch.setattr(sys, "stdout", ...)` then
  call every entry point) only catches the call paths the test
  exercises. The AST scan catches dormant ones too — which is exactly
  what a "this layer MUST NOT write" guard needs.
- The scan is one short test (~30 lines), runs in < 50 ms, and is
  immediately understandable.
- AST is the right level: a source-grep would false-positive on
  docstrings and comments (e.g., a docstring saying "do not print to
  stderr").

**Alternatives considered**:
- **`capsys` over every public entry point**: Rejected for coverage
  reasons stated above.
- **`ruff` custom rule**: Rejected. The project already uses ruff
  (Principle II); adding a custom rule plugin is heavier than a single
  pytest. If the layer grows large enough that the AST scan slows down
  noticeably, this becomes attractive.
- **No mechanical enforcement, just code review**: Rejected. SC-009
  explicitly demands a mechanical check ("the exact check shape is the
  implementer's choice, but it MUST exist").

---

## R8. Plugin-extensibility smoke test: `FakeIntegration` declared inline + git-state assertion

**Decision**: `tests/integrations/test_plugin_contract.py` declares a
`FakeIntegration(SkillsIntegration)` in the test module body, mutates
`INTEGRATION_REGISTRY` to insert it inside a fixture that restores the
original registry on teardown, then exercises lookup, listing, option
parsing, `resolve_skills_dir`, and `setup()` against it. A second test
in the same file asserts (via `pathlib`) that none of the files under
`src/bookwright/integrations/claude/`,
`src/bookwright/integrations/generic/`, or
`src/bookwright/integrations/base.py` were modified relative to their
state at the start of the iteration — the assertion is a content
hash, not a git `diff`, so the test is hermetic.

**Rationale**:
- US5 / FR-031 / SC-007 demand the test exists *and* that it
  mechanically proves the no-edit promise. A content-hash snapshot
  taken once and pinned in the test file is the cheapest reliable
  signal.
- Restoring `INTEGRATION_REGISTRY` on teardown via a `pytest` fixture
  prevents bleed into other tests (registry is module-level state).
- Inline class declaration avoids creating a sibling `tests/_fixtures/`
  package with a one-class file; the class only ever exists for this
  test.

**Alternatives considered**:
- **Spawn `git diff --quiet -- src/bookwright/integrations/claude
  src/bookwright/integrations/generic src/bookwright/integrations/base.py`
  inside the test**: Rejected. Couples the test to a working git
  checkout; CI environments where the working tree is detached or where
  the integration is consumed as an installed wheel cannot run it.
- **A `pyproject.toml` entry-point-based plugin registration test**:
  Rejected. v0 does not use entry-points; `_register_builtins()` is the
  only registration path. Adding entry-point loading just to test it is
  premature scope (the deferred Extensions system, v0.5).
