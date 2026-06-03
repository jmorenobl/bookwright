# Bookwright

Spec-driven authoring toolkit for novels, essays, and memoirs.

## Install

Bookwright is developed with [`uv`](https://docs.astral.sh/uv/). Install `uv`
first, then sync the project environment from the committed lockfile:

```bash
uv sync
```

This resolves dependencies from `uv.lock`, creates `.venv/`, and installs
the package in editable mode in under 60 seconds on a warm cache. If the
host has no network and the wheels are not cached, `uv sync` will fail
loudly — that's the expected offline failure mode.

## Run the CLI

```bash
uv run bookwright --help
uv run bookwright version
uv run bookwright version --json
uv run bookwright check
uv run bookwright check --json
```

Both `version` and `check` accept `--json` to emit a single JSON document
on stdout (Principio IX).

## Quality gates (local)

Replica of the CI pipeline. Run before pushing:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

If any of the four fails locally, it will fail in CI.

## Traceability tags in code

Comments and docstrings may reference the planning artifacts that justify a
piece of code. Keep these — in a spec-driven repo they are how a reader (and
`/speckit-analyze`) navigates from code back to the *why*.

**Allowed in source/tests:**

- `FR-0xx` / `SC-0xx` — a requirement / success criterion in the **owning
  iteration's** `specs/NNN-*/spec.md`.
- `D-x` — a recorded decision in that iteration's `research.md`.
- `bookwright-design.md § N.M` — a section of the global design doc.

**Forbidden in source/tests** (planning bookkeeping with no durable artifact):

- `US-x` / `+USx` — user-story / backlog tags.
- `T0xx` — task IDs from `tasks.md`.

**Two rules that keep the allowed tags trustworthy:**

1. **Refs resolve relative to the file's iteration.** Each `src/` subtree maps
   to one iteration; a bare `FR-021` means *that* iteration's spec. (Specs
   restart numbering at `FR-001`, so the number alone is ambiguous.)
2. **Numbers freeze on merge.** Once an iteration lands on `main`, its
   `FR`/`SC`/`D` numbers are never renumbered — so inline refs never go stale.

Prefer pairing the ref with the reason, not a bare pointer:

    # dedup identical feature values (FR-021)   ✅
    # (FR-021)                                  ⚠️ adds nothing on its own

## Pre-commit hooks

Install the project's pre-commit hooks (ruff format, ruff check,
`check-toml`, `check-yaml`):

```bash
uv run pre-commit install
```

After this, every `git commit` is gated locally. Skipping this step still
leaves the CI pipeline as the safety net.

## Extending Bookwright

All three extension points follow the plugin architecture (Constitution
Principle V): you add a small, self-contained module and register it — no
edits to a central dispatcher.

### Create a new integration

An integration materializes the source commands as Agent Skills in the
directory a given agent expects.

1. Create `src/bookwright/integrations/<key>/__init__.py` with a subclass of
   `SkillsIntegration` that overrides `key`, `config`, and
   `default_skills_dir`. Override `resolve_skills_dir()` only when the resolved
   directory depends on `--integration-options`, and set the `supports_*` flags
   for capabilities the agent has.
2. Register it by adding a single `_register(<Your>Integration)` line in
   `integrations/__init__.py` (`_register_builtins`). Do **not** edit `base.py`,
   `claude/`, or `generic/` — `tests/integrations/test_plugin_contract.py`
   enforces this mechanically.

`setup()` is implemented once in the base class: it materializes one `SKILL.md`
per source command and runs the agentskills.io linter (Principle VII). Switching
a live project to your integration is then `bookwright integration use <key>`.

### Create a custom validator

A validator inspects the project and the built graph and returns findings.

1. Add a module under the project's `.bookwright/validators/` directory exposing
   a class with `name: str`, `severity_default: Severity`, and
   `validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]`.
2. The `validate` method MUST be deterministic and MUST NOT write to disk or
   mutate the graph. It reads `project` (constitution text, character/setting
   rosters, manuscript files) and `indexer` (the already-built graph).
3. Declare its `name` under `[validators] custom` in `manifest.toml`.

Only `error`-severity findings gate CI; emit `warning` for heuristic checks so a
false positive can never fail a build.

### Create a vocabulary

Narrative vocabularies (e.g. Propp functions, Greimas actants) ship as Turtle
graphs whose classes and predicates extend the GOLEM model.

1. Place the `.ttl` file under the project's `.bookwright/vocabularies/`.
2. Activate it by name in `manifest.toml`:

   ```toml
   [vocabularies]
   active = ["propp", "greimas"]
   ```

The vocabulary is loaded alongside the project graph, so its terms become
available to `bookwright graph query`.

## Detailed onboarding

The canonical walkthrough — including a worked example of the pre-commit
hooks rejecting malformed commits — lives in
[specs/001-repo-bootstrap/quickstart.md](specs/001-repo-bootstrap/quickstart.md).
