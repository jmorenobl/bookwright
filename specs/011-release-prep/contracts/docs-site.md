# Contract: Documentation Site & Release Metadata

**Branch**: `011-release-prep` | **Phase**: 1 | Maps to FR-010…FR-022, SC-003…SC-008

Spanish-language docs site built with MkDocs (`material` theme), plus the
finalized release metadata files. Existing draft files are **finalized, not
regressed** (edge case).

---

## MkDocs site (`mkdocs.yml` at repo root, `docs/`)

### `mkdocs.yml` required settings (D5)

```yaml
site_name: Bookwright
theme:
  name: material
strict: true            # warnings → build error (FR-014, SC-004)
nav:
  - Inicio: index.md
  - Primeros pasos: getting-started.md
  - Arquitectura: architecture.md
  - Comandos: commands/...        # one page or section per shipped command
  - Validación: validation.md
  - Extender: extending.md
  - FAQ: faq.md
```

### Required pages (FR-011, FR-012, SC-004)

| Page | Contract |
|------|----------|
| `index.md` | Explains what Bookwright is. |
| `getting-started.md` | Install + 5-minute quickstart; steps match shipped CLI (FR-015). |
| `architecture.md` | Curated summary that **links** `bookwright-design.md § N.M`; does **not** duplicate it wholesale (FR-013). |
| `commands/` | One page **or clearly delineated section per shipped command**: `init`, `check`, `version`, `validate`, `graph build`, `graph query`, `integration use` (FR-012). |
| `validation.md` | The 4 built-in validators + how to add a custom validator. |
| `extending.md` | New integration / custom validator / vocabulary. |
| `faq.md` | Common questions. |

### Build contract

- **DOC-1**: `mkdocs build --strict` → exit 0, **zero warnings** (FR-014, SC-004).
- **DOC-2**: Documented command set **==** registered Typer command set,
  enforced by the D4 drift test (FR-015, VR-11).
- **DOC-3**: Docs deps (`mkdocs`, `mkdocs-material`) live in a `docs`
  dependency group, not `[project.dependencies]` (D6 — no constitutional
  amendment).

---

## Release metadata files

| File | Contract | Maps to |
|------|----------|---------|
| `README.es.md` | Canonical: qué es / install / 5-min quickstart / docs links; **status updated** from "pre-alpha, iter 1–2" to v0.1.0 (FR-010, FR-015). | FR-010 |
| `README.md` | MAY remain a short English pointer to `README.es.md` + docs (not required to carry full quickstart). | FR-010 |
| `CHANGELOG.md` | A `## [0.1.0]` entry enumerating **every** shipped feature (consolidate current `[Unreleased]` + iterations 1–11); Keep-a-Changelog format. | FR-016, SC-008 |
| `CONTRIBUTING.md` | Finalize to also cover: **create a new integration**, **create a custom validator**, **create a vocabulary** (current draft lacks these). | FR-017, SC-008 |
| `LICENSE` | Apache-2.0 present (already), referenced from `pyproject.toml` (`license = "Apache-2.0"`, already set). | FR-018, SC-008 |

---

## CI & artifact gates (`.github/workflows/tests.yml`)

| ID | Gate | Maps to |
|----|------|---------|
| CI-1 | `pytest` with coverage **≥ 80%**, fail-closed with **no round-up**. Threshold single-sourced in `[tool.coverage.report]` (`fail_under = 80`, `precision = 2`); CI runs plain `pytest` and does **not** pass `--cov-fail-under` (avoids a second, drift-prone threshold). | FR-019, SC-005, edge case |
| CI-2 | `ruff check` + `ruff format --check`. | FR-020, SC-006 |
| CI-3 | `mypy --strict`. | FR-020, SC-006 |
| CI-4 | `pre-commit` passes locally/CI. | FR-020, SC-006 |
| CI-5 | `mkdocs build --strict` (new docs job/step, `--group docs`). | FR-021, FR-014 |
| CI-6 | `uv build` produces wheel + sdist (new step). | FR-022 |

---

## Manual / packaged-install validation (D7)

- **MAN-1**: `uv build` → install local wheel into an isolated env
  (`pipx install ./dist/bookwright_cli-*.whl` or `uv tool install`).
- **MAN-2**: A new user runs the README quickstart against the installed
  `bookwright` **without touching the source tree** and completes
  init → edit → build → query → validate in ≤ 5 minutes (SC-003, SC-007).
- **MAN-3**: Documented as a repeatable procedure in `quickstart.md`;
  optionally wrapped as a `@pytest.mark.manual` test deselected by default.
