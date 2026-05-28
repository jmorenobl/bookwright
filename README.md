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

## Pre-commit hooks

Install the project's pre-commit hooks (ruff format, ruff check,
`check-toml`, `check-yaml`):

```bash
uv run pre-commit install
```

After this, every `git commit` is gated locally. Skipping this step still
leaves the CI pipeline as the safety net.

## Detailed onboarding

The canonical walkthrough — including a worked example of the pre-commit
hooks rejecting malformed commits — lives in
[specs/001-repo-bootstrap/quickstart.md](specs/001-repo-bootstrap/quickstart.md).
