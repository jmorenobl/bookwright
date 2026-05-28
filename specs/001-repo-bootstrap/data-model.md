# Phase 1 — Data Model: Bootstrap Bookwright

**Iteración**: 001-repo-bootstrap
**Date**: 2026-05-28

Esta iteración no introduce lógica de dominio (FR-021). No hay entidades
GOLEM, ni manifest, ni grafo, ni validators. Las "entidades" en juego son
exclusivamente artefactos de **configuración del proyecto** y **payloads
de salida del CLI**.

## Entidades de configuración (filesystem)

### E1 — Paquete `bookwright`

- **Ubicación**: `src/bookwright/`
- **Tipo**: paquete Python instalable.
- **Atributos**:
  - `__version__: str` — semver del toolkit. Fuente única en
    `src/bookwright/__init__.py`. v0.0.1 inicial.
  - `__name__: str` — `"bookwright"` (módulo); el paquete distribuible en
    PyPI se llama `bookwright-cli`.
- **Reglas**:
  - Cumple Principio III (src-layout).
  - Subpaquete `commands/` con un módulo por subcomando (Principio IV).
  - Ningún módulo supera 500 LOC (Principio IV).
- **Transiciones**: build-time `hatchling` lee `__version__` desde
  `__init__.py`. Runtime, `version --json` lo lee importando el módulo.

### E2 — Lockfile reproducible

- **Ubicación**: `uv.lock` en la raíz del repo.
- **Tipo**: archivo gestionado por `uv`, commiteado.
- **Atributos**: grafo completo de dependencias resueltas con hashes.
- **Reglas**:
  - **MUST** commitearse (Constitución § Technical Constraints, FR-002).
  - `uv sync --frozen` debe pasar en CI sin re-resolver.
  - Cualquier cambio en `pyproject.toml` regenera `uv.lock`; los dos van
    juntos en la misma PR.
- **Transiciones**: `uv lock` regenera tras editar deps; `uv sync` lo
  consume.

### E3 — Manifest del proyecto Python (`pyproject.toml`)

- **Ubicación**: raíz del repo.
- **Tipo**: TOML PEP 621-compliant.
- **Atributos clave**:
  - `[project].name` = `"bookwright-cli"`.
  - `[project].version` — vía `dynamic = ["version"]` + `tool.hatch.version.path`.
  - `[project].requires-python` = `">=3.11"`.
  - `[project].dependencies` — set completo Constitucional.
  - `[project.scripts].bookwright` = `"bookwright.cli:app"`.
  - `[build-system].requires = ["hatchling"]`, `build-backend = "hatchling.build"`.
  - `[dependency-groups].dev` — pytest, pytest-cov, ruff, mypy, pre-commit.
  - `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.mypy]`, `[tool.pytest.ini_options]`, `[tool.coverage.run]` — ver `research.md` R6-R8.
- **Reglas**:
  - **MUST** validar como TOML (gateado por pre-commit `check-toml`).
  - **MUST NOT** declarar dependencias fuera del set Constitucional (FR-022).

### E4 — Configuración de pre-commit (`.pre-commit-config.yaml`)

- **Ubicación**: raíz del repo.
- **Atributos**: lista de `repos`, cada uno con `rev` (ancla de versión) y
  `hooks` con `id` y `args`.
- **Hooks requeridos** (FR-011):
  - `ruff-format` (auto-fix).
  - `ruff` con `--fix --exit-non-zero-on-fix`.
  - `check-toml`.
  - `check-yaml`.
- **Reglas**:
  - **MUST** validar como YAML (gateado por `check-yaml`, irónicamente).
  - El dev activa los hooks con `uv run pre-commit install`; sin ese paso
    los commits no se gatean localmente (sigue siendo válido pero la red
    de seguridad cae sobre CI).

### E5 — Workflow de CI (`.github/workflows/tests.yml`)

- **Ubicación**: `.github/workflows/tests.yml`.
- **Triggers**: `push: {}` (cualquier rama) y `pull_request: { branches: [main] }`.
- **Jobs**: `quality` (matriz Python 3.11 + 3.12).
- **Pasos del job** (en orden):
  1. Checkout.
  2. Setup uv.
  3. Install Python `${{ matrix.python-version }}`.
  4. `uv sync --frozen`.
  5. (`if: matrix.python-version == '3.12'`) `uv run ruff check .`.
  6. (`if: matrix.python-version == '3.12'`) `uv run ruff format --check .`.
  7. (`if: matrix.python-version == '3.12'`) `uv run mypy`.
  8. `uv run pytest`.
  9. (`if: matrix.python-version == '3.12'`) Upload `coverage.xml` como artefacto.
- **Reglas**:
  - `timeout-minutes: 10` por job (cubre Edge Case "pipeline cuelga").
  - `fail-fast: false` para ver todas las celdas falladas.
  - Si cualquier paso falla, el agregador de checks bloquea merge (FR-016).

### E6 — Reporte de schema GOLEM (ausente)

- **Ubicación esperada**: `src/bookwright/schemas/golem/VERSION`.
- **Estado en esta iteración**: **no existe**.
- **Comportamiento esperado del CLI**: `version --json` reporta
  `"golem_schema_version": "unknown"`.
- **Iteración que lo crea**: 5 (GOLEM domain model).

---

## Payloads de salida del CLI (modelo lógico)

Los dos payloads JSON están definidos formalmente en
`contracts/version.schema.json` y `contracts/check.schema.json`. Aquí
documentamos el modelo lógico.

### P1 — `bookwright version --json`

```text
VersionPayload
├── package_version : str         # semver del toolkit, p.ej. "0.0.1"
└── golem_schema_version : str    # "unknown" si el archivo VERSION no existe
```

Invariantes:

- `package_version` siempre presente, siempre semver válido.
- `golem_schema_version` siempre presente; valor `"unknown"` en esta
  iteración.
- Exactamente esas dos claves de primer nivel en v0.0.1; extensiones
  futuras añaden claves opcionales, nunca renombran ni quitan.

### P2 — `bookwright check --json`

```text
CheckPayload
├── ok : bool                     # AND-agregado de todos los checks
└── checks : list[CheckResult]
        ├── name : str            # identificador estable del check
        ├── status : "ok" | "fail"
        └── detail : str?         # opcional; presente en fail, opcional en ok
```

Checks en v0.0.1 (en orden de ejecución):

1. `name: "python_version"`, OK si `sys.version_info >= (3, 11)`. `detail`
   = string con la versión encontrada (p.ej. `"3.12.3"`) en ambos
   estados.
2. Por cada módulo runtime declarado (lista cerrada en `check.py`):
   `name: "dependency:<modulo>"`, OK si `importlib.import_module` no
   levanta. `detail` ausente en OK; en fail contiene `str(exc)` del
   `ImportError`.

Invariantes:

- `ok == all(c.status == "ok" for c in checks)`.
- Exit code del proceso: `0` ⇔ `ok == True`. `1` ⇔ `ok == False`.
- `checks` no vacío (al menos el chequeo `python_version`).

### Reglas de salida (ambos comandos)

- En modo `--json`: stdout contiene **exclusivamente** un único documento
  JSON serializado con `json.dumps(payload, separators=(",", ":"))` +
  newline trailing (única). Stderr puede contener prosa diagnóstica o
  estar vacío.
- En modo humano (sin `--json`): stdout es prosa legible (puede usar
  colores via `rich`). Stderr opcionalmente recibe warnings.
- Schema versioning: cualquier evolución de los payloads requiere bump
  semver del paquete y nota en CHANGELOG (cuando exista). En esta
  iteración la versión es `0.0.1` y los payloads se consideran
  experimentales pero estables suficientes para que la suite de tests
  pinche cualquier regresión.

---

## Estados y transiciones globales

No aplica. El bootstrap no tiene state machines. Los comandos `version` y
`check` son funciones puras de "lee el entorno → reporta".
