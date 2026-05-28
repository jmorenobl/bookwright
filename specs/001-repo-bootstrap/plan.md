# Implementation Plan: Bootstrap inicial del repositorio Bookwright

**Branch**: `001-repo-bootstrap` | **Date**: 2026-05-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-repo-bootstrap/spec.md`

## Summary

Esta iteración deja el repositorio Bookwright listo como proyecto Python
reproducible y verificable, sin introducir lógica de dominio. El alcance es
el esqueleto técnico: `pyproject.toml` con el stack mandatado por la
Constitución, `uv.lock` commiteado, un entry point `bookwright` con dos
subcomandos (`version` y `check`) que aceptan `--json`, una suite de smoke
tests, hooks de pre-commit, y un workflow de CI en GitHub Actions que
ejercita pytest + ruff + mypy sobre Python 3.11 y 3.12. Se sigue al pie de
la letra la estructura de `bookwright-design.md § 6` (subset M0 mínimo) y
el stack tecnológico de `§ 14`. Las dependencias completas del v0 se
declaran ya en `pyproject.toml` para estabilizar el lockfile, pero solo
`typer` y `rich` se importan en código. Los directorios `core/`, `golem/`,
`integrations/`, `indexers/`, `validation/`, `io/`, `resources/` quedan
fuera del scope — se introducen en iteraciones posteriores.

## Technical Context

**Language/Version**: Python 3.11+ (mínimo Constitucional). CI ejercita
matriz `3.11` + `3.12` para tests; lint y type-check corren solo en `3.12`.

**Primary Dependencies (runtime)**:

- `typer>=0.12` — CLI framework (subcomandos, parsing, `--help`).
- `rich>=13.7` — output legible humano (consolas, tablas, colores).
- `rdflib>=7.0`, `pydantic>=2.5`, `tomlkit>=0.12`, `jinja2>=3.1`,
  `python-slugify>=8.0`, `platformdirs>=4.2`, `uuid-utils>=0.16` — el
  resto del set mínimo declarado por la Constitución se incluye en
  `pyproject.toml` desde esta iteración para estabilizar `uv.lock`, pero
  **no se importa** en código (Principio "no plumbing for future X" se
  respeta porque la declaración de deps es prerrequisito directo del
  lockfile reproducible exigido por FR-002 y FR-017).

**Primary Dependencies (dev)**: `pytest>=8.0`, `pytest-cov>=5.0`,
`ruff>=0.5`, `mypy>=1.10`, `pre-commit>=3.7`.

**Build backend**: `hatchling` (Principio II).

**Storage**: N/A (no hay estado persistente en esta iteración).

**Testing**: `pytest` + `pytest-cov`; reporte de cobertura local (terminal
+ artefacto XML/HTML adjunto al run de CI); sin servicios externos
(Codecov/Coveralls) por FR-020 + Q&A de 2026-05-28.

**Target Platform**: macOS y Linux (validación primaria); Windows
best-effort (Assumptions del spec).

**Project Type**: CLI tool empaquetada como library Python instalable
(`bookwright-cli` en PyPI; entry point `bookwright`).

**Performance Goals**:

- `uv sync` desde caché vacía con red disponible: < 60 s (SC-001, SC-006).
- `bookwright check` (todos los chequeos): < 5 s (SC-004).
- Suite de smoke tests: < 10 s (SC-005).
- Pipeline de CI completa (tests + lint + type-check) sobre la matriz: < 5 min (SC-008).
- Instalación de hooks locales tras `pre-commit install`: < 2 min (SC-007).

**Constraints**:

- **JSON-over-stdout (Principio IX)**: `version --json` y `check --json`
  emiten **un único** documento JSON a stdout y nada más; prosa va a
  stderr. Sin `--json`, salida humano-legible por defecto.
- **src-layout (Principio III)**: todo el código de producción bajo
  `src/bookwright/`, todos los tests bajo `tests/`. Sin excepciones.
- **Modular Command Surface (Principio IV)**: cada subcomando vive en su
  propio módulo bajo `src/bookwright/commands/`, ≤ 500 líneas por archivo.
- **Lookup de schema GOLEM por archivo**: `version` lee
  `src/bookwright/schemas/golem/VERSION` (texto plano, una línea); si no
  existe, reporta `"unknown"`. El comando **no** importa `rdflib` ni
  ninguna dependencia de dominio (FR-006).
- **Ruff**: rulesets `E, W, F, I, B, UP, RUF, SIM, PL`; `line-length =
  100`; `target-version = py311`.
- **Mypy strict**: `--strict` activa `disallow_untyped_defs`,
  `disallow_any_generics`, `warn_return_any`, etc. (FR-013).
- **Pre-commit hooks**: ruff format (auto-fix), ruff check, check-toml,
  check-yaml.
- **CI matrix**: tests en `{python: [3.11, 3.12]}`. Lint + type-check solo
  en `3.12` (FR-015a).

**Scale/Scope**: Bootstrap mínimo. Estimado:

- Código de producción: ~5 archivos, < 200 LOC totales.
- Tests: 4–6 archivos de smoke, ~120 LOC.
- Configuración: `pyproject.toml`, `.pre-commit-config.yaml`,
  `.github/workflows/tests.yml`, `.gitignore`, `LICENSE`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Esta iteración se evalúa contra los 10 principios de
`.specify/memory/constitution.md` v1.0.0.

| # | Principio | Aplicabilidad | Veredicto | Notas |
|---|---|---|---|---|
| I | Plain Text as Source of Truth | Aplica | ✅ Pass | Solo se introducen Markdown, TOML, YAML, Python source. Ningún binario / cache opaca. |
| II | Modern Python Stack | Aplica | ✅ Pass | `pyproject.toml` declara exactamente el stack mandatado: Python 3.11+, hatchling, uv (lockfile commiteado), ruff, mypy, typer, pydantic v2, etc. Cero dependencias fuera del set autorizado. |
| III | src-layout | Aplica | ✅ Pass | Código bajo `src/bookwright/`, tests bajo `tests/`. Sin tests al lado del código. |
| IV | Modular Command Surface | Aplica | ✅ Pass | `commands/version.py` y `commands/check.py` son archivos separados, cada uno < 500 LOC. `cli.py` solo orquesta el Typer app. |
| V | Plugin-Based Integrations | **No aplica esta iteración** | N/A | No se introducen integraciones en M0-iter1. `SkillsIntegration` y `INTEGRATION_REGISTRY` llegan en la iteración 3. Esta iteración no crea ningún archivo bajo `integrations/`. |
| VI | Agent Skills Only — No Legacy Commands | **No aplica esta iteración** | N/A | No se materializan skills todavía. La iteración 9 los emite. |
| VII | agentskills.io Standard Compliance | **No aplica esta iteración** | N/A | Sin skills generados, no hay nada que validar contra el estándar. |
| VIII | Test Discipline | Aplica | ✅ Pass | pytest + ruff + mypy corren en CI sobre cada push/PR. Harness de cobertura instalado y reportando local + artefacto CI. El umbral ≥ 80 % se activa desde día uno vía `--cov-fail-under=80` en `[tool.pytest.ini_options].addopts`: la superficie de código (~200 LOC) es trivialmente cubierta por los smoke tests de US1 y US4. No hay diferimientos. |
| IX | JSON-over-stdout CLI Contract | Aplica | ✅ Pass | FR-009a, FR-009b, FR-009c lo cubren explícitamente. Tests cubren ambos modos (humano y `--json`) por FR-009c. |
| X | Design Document Axioms | Aplica | ✅ Pass | Ninguna decisión de la Sección 16 se reabre. Se respetan: Python, plain text, sin shell scripts, sin Grafeo, sin presets, sin extension system. |

**Technical Constraints (Constitución § Technical Constraints)**:

- Python 3.11+: ✅ — `requires-python = ">=3.11"`.
- Set mínimo de dependencias runtime: ✅ — declarado completo, aunque solo
  `typer` + `rich` se importan.
- Build backend `hatchling`: ✅.
- `uv.lock` commiteado: ✅.
- PyPI package name `bookwright-cli`: ✅.
- CI con pytest + ruff check + ruff format --check + mypy --strict: ✅
  todos los gates en GitHub Actions.

**Scope & Release Discipline**:

- Sin preset system, sin GrafeoIndexer, sin integraciones extra, sin
  extension system, sin export EPUB/PDF: ✅. FR-021 y FR-022 lo blindan
  desde el spec.

**Resultado del gate**: PASS. Cero violaciones que requieran justificación.
La sección **Complexity Tracking** queda vacía.

## Project Structure

### Documentation (this feature)

```text
specs/001-repo-bootstrap/
├── plan.md              # Este archivo
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (entidades de configuración)
├── quickstart.md        # Phase 1 output (developer onboarding)
├── contracts/           # Phase 1 output (esquemas CLI --json)
│   ├── version.schema.json
│   └── check.schema.json
├── checklists/          # ya existe (de iteraciones previas si las hubiera)
└── tasks.md             # Phase 2 output (creado por /speckit-tasks, NO por este comando)
```

### Source Code (repository root)

Subset M0-iteración-1 del árbol completo descrito en
`bookwright-design.md § 6`. Solo los archivos imprescindibles:

```text
bookwright/                                # repo root
├── LICENSE                                # Apache-2.0
├── README.md                              # mínimo: install + uv sync + uv run bookwright --help
├── pyproject.toml                         # metadata + deps + tool.ruff + tool.mypy + tool.pytest
├── uv.lock                                # lockfile commiteado (FR-002)
├── .python-version                        # 3.11 (default local)
├── .gitignore                             # caches Python, .venv, htmlcov/, coverage.xml, *.pyc
├── .pre-commit-config.yaml                # ruff format + ruff check + check-toml + check-yaml
│
├── src/
│   └── bookwright/
│       ├── __init__.py                    # __version__ (leído por hatch desde aquí)
│       ├── __main__.py                    # `python -m bookwright` → cli.app()
│       ├── cli.py                         # Typer app + registro de subcomandos
│       └── commands/
│           ├── __init__.py
│           ├── version.py                 # subcomando `version` (humano + --json)
│           └── check.py                   # subcomando `check`   (humano + --json)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                        # fixtures comunes (CliRunner, paths)
│   ├── test_smoke_import.py               # importa bookwright; verifica __version__
│   ├── test_cli_version.py                # `bookwright version` humano + --json
│   └── test_cli_check.py                  # `bookwright check`   humano + --json
│
└── .github/
    └── workflows/
        └── tests.yml                      # matriz {3.11, 3.12}: tests + lint + type-check
```

**Directorios explícitamente NO creados en esta iteración** (per Pista del
plan + FR-021):

- `src/bookwright/core/`
- `src/bookwright/golem/`
- `src/bookwright/integrations/`
- `src/bookwright/indexers/`
- `src/bookwright/validation/`
- `src/bookwright/io/`
- `src/bookwright/resources/`
- `tests/integration/`, `tests/e2e/`, `tests/fixtures/`
- `docs/`, `scripts/`
- `.github/workflows/release.yml`, `docs.yml`
- `CHANGELOG.md`, `CONTRIBUTING.md`

**Structure Decision**: src-layout single-project (Constitución Principio
III). El árbol arriba refleja exactamente lo que debe existir cuando esta
iteración mergee a `main`. Cualquier archivo o directorio fuera de esa
lista es scope creep y debe rechazarse en review.

## Complexity Tracking

> No hay violaciones de la Constitution Check. Esta sección queda vacía.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| _N/A_ | _N/A_ | _N/A_ |
