# Phase 0 — Research: Bootstrap Bookwright

**Iteración**: 001-repo-bootstrap
**Date**: 2026-05-28

El `spec.md` está totalmente clarificado (cuatro Q&A resueltas en la sesión
del 2026-05-28). No quedan items "NEEDS CLARIFICATION" abiertos. Esta fase
documenta las decisiones técnicas concretas para cada pieza del stack ya
mandatado por la Constitución, junto con las mejores prácticas adoptadas.

## Resumen de decisiones

| Tema | Decisión |
|---|---|
| Gestor de paquetes | `uv` con `uv.lock` commiteado |
| Build backend | `hatchling`, versión vía `tool.hatch.version` apuntando a `src/bookwright/__init__.py` |
| CLI framework | `typer` con sub-apps por comando |
| Output JSON | dos flujos separados; stdout solo JSON cuando `--json`, prosa a stderr siempre |
| Lookup de `golem_schema_version` | leer `src/bookwright/schemas/golem/VERSION` (text/plain, una línea) |
| Lint/format | `ruff` con rulesets `E, W, F, I, B, UP, RUF, SIM, PL`, `line-length=100` |
| Type checking | `mypy --strict` |
| Test runner | `pytest` + `pytest-cov` |
| CI | GitHub Actions, matrix `python-version: ["3.11", "3.12"]` para tests; lint+mypy solo en `3.12` |
| Reporte de cobertura | local-only: terminal + artefacto XML/HTML; sin servicios externos |
| Pre-commit hooks | `ruff format`, `ruff check`, `check-toml`, `check-yaml` |
| Licencia | Apache-2.0 |

---

## R1 — `uv` como gestor de paquetes y lockfile

**Decisión**: usar `uv` con `uv sync` para crear/poblar `.venv`, `uv lock`
para regenerar el lockfile, `uv run <cmd>` para ejecutar comandos en el
entorno.

**Rationale**:

- Mandatado por Constitución § Technical Constraints.
- `uv.lock` es determinista y reproducible cross-platform; resuelve el
  grafo completo de dependencias transitivas con hash.
- `uv sync` instala dependencias en < 60 s desde caché vacía con red
  disponible (cubre SC-001 y SC-006).
- Compatible con dependency groups (PEP 735) — separamos runtime de dev
  deps limpiamente sin `[project.optional-dependencies]` para dev.

**Alternativas consideradas**:

- `pip + pip-tools`: descartado — sin lockfile multi-plataforma robusto.
- `poetry`: descartado — Constitución mandata `hatchling`, y `poetry` se
  acopla a su propio build backend.
- `pdm`: descartado — `uv` es más rápido y la elección Constitucional.

**Configuración relevante en `pyproject.toml`**:

```toml
[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.5",
    "mypy>=1.10",
    "pre-commit>=3.7",
]
```

---

## R2 — `hatchling` como build backend

**Decisión**: `hatchling` con configuración mínima en `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build]
include = ["src/bookwright"]

[tool.hatch.version]
path = "src/bookwright/__init__.py"
```

**Rationale**:

- Mandatado por Constitución § Technical Constraints.
- `tool.hatch.version` evita duplicación: `__version__` vive solo en
  `__init__.py` y hatch lo lee al build-time.
- En esta iteración aún no hay `resources/`, así que el `include` se
  limita a `src/bookwright`. Cuando llegue iteración 4+ se ampliará.

**Alternativas consideradas**:

- `setuptools`: descartado por Constitución.
- `flit`: descartado por Constitución.

---

## R3 — `typer` como CLI framework

**Decisión**: usar `typer.Typer()` como app raíz en `src/bookwright/cli.py`.
Cada subcomando vive en un módulo bajo `src/bookwright/commands/` y se
registra como sub-app o callback.

**Patrón adoptado**:

```python
# src/bookwright/cli.py
import typer
from bookwright.commands import check, version

app = typer.Typer(
    name="bookwright",
    help="Bookwright — Spec-driven authoring toolkit.",
    no_args_is_help=True,
    add_completion=False,
)
app.command("version")(version.run)
app.command("check")(check.run)
```

**Rationale**:

- Mandatado por Constitución.
- Cumple Principio IV (Modular Command Surface): un archivo por
  subcomando.
- `no_args_is_help=True` satisface FR-004 (invocar sin argumentos muestra
  help).
- `add_completion=False` mantiene el `--help` limpio para esta iteración;
  se reevalúa si se reclama completion en futuro.

**Alternativas consideradas**:

- `click` directo: descartado — `typer` es la elección Constitucional y
  añade type-hints sin pérdida de funcionalidad.
- `argparse`: descartado por Constitución.

---

## R4 — Patrón JSON-over-stdout

**Decisión**: cada subcomando con `--json`:

1. Construye un `dict` con el payload.
2. Lo serializa con `json.dumps(payload, separators=(",", ":"))` —
   compacto, una sola línea.
3. Imprime exactamente eso a `sys.stdout` (vía `typer.echo` con
   `nl=False` o `print` directo) **sin newline trailing** opcional, pero
   con newline trailing aceptable (los parsers JSON ignoran whitespace
   externo). Adoptamos newline trailing por compatibilidad con `cat`.
4. Cualquier mensaje informativo va a `sys.stderr` (`typer.echo(..., err=True)`).
5. El proceso termina con `raise typer.Exit(code=...)` donde `code` es 0
   en éxito y `≠ 0` en fallo. El payload JSON siempre se emite,
   independientemente del exit code (FR-008 + Principio IX).

**Schema mínimo `version --json`** (FR-009b):

```json
{
  "package_version": "0.0.1",
  "golem_schema_version": "unknown"
}
```

**Schema mínimo `check --json`** (FR-009b):

```json
{
  "ok": true,
  "checks": [
    {"name": "python_version", "status": "ok", "detail": "3.12.3"},
    {"name": "dependency:typer", "status": "ok"}
  ]
}
```

En fallo, `ok=false`, y los chequeos fallidos tienen `status: "fail"` y
`detail` describiendo el problema.

**Rationale**:

- Principio IX: JSON-over-stdout es contractual.
- El JSON compacto en una sola línea facilita `jq`/parsing por agentes y
  evita ambigüedad sobre dónde termina el documento.
- Emitir el JSON incluso en fallo permite al agente parsear el detalle
  estructurado del error en lugar de scrapear stderr.

**Alternativas consideradas**:

- JSON pretty-printed: rechazado — multilínea complica el parsing y abre
  la puerta a "líneas extra" accidentales.
- Solo JSON en éxito, prosa en fallo: viola el espíritu del Principio IX
  y obliga al agente a switchear modos de parsing.

---

## R5 — Lookup del `golem_schema_version`

**Decisión**: ruta fija dentro del paquete:
`src/bookwright/schemas/golem/VERSION` (un solo archivo de texto, una
línea, sin BOM). Se lee con `importlib.resources.files("bookwright").joinpath("schemas/golem/VERSION").read_text(encoding="utf-8").strip()`.

Si el archivo **no existe**, el comando reporta literalmente `"unknown"`
sin abortar. **No** se importa `rdflib` ni se valida el contenido en esta
iteración.

**Rationale**:

- Q&A explícita del 2026-05-28: "Lookup basado en archivo — se lee desde
  una ruta fija dentro del paquete; si el archivo no existe, se reporta
  `unknown`."
- FR-006 prohíbe importar dependencias de dominio desde `version`.
- Cuando la iteración 5 introduzca el schema GOLEM, ese archivo aparecerá
  bajo `src/bookwright/resources/schemas/golem-1.0/version.json` o
  equivalente. Para esta iteración acordamos la ruta canónica más simple
  posible (`schemas/golem/VERSION` texto plano) para que el contrato no
  dependa de detalles de empaquetado futuros.

**Compromiso forward-compatible**: cuando iteración 5 cambie a
`resources/schemas/golem-1.0/version.json`, el código de `version` se
actualiza para leer el nuevo path. El test `test_cli_version` se mantiene
verde porque el `unknown` actual sigue siendo la respuesta correcta en la
ausencia del archivo. La spec de iteración 5 deberá incluir la
actualización del lookup como parte de su scope.

**Alternativas consideradas**:

- Leer desde `manifest.toml` del proyecto: rechazado — `version` es un
  comando del toolkit, no del proyecto.
- Hard-code en código: rechazado — exige bump de versión del paquete cada
  vez que cambie el schema.
- `importlib.metadata`: no aplica — el schema no es un paquete instalado.

---

## R6 — `ruff` configuración

**Decisión** en `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "RUF", "SIM", "PL"]
# PL incluye PLR, PLW, PLE, PLC; aceptamos PLR (refactor) como warnings — no excluimos por ahora.

[tool.ruff.format]
# defaults: double quotes, 4-space indent
```

**Rationale**:

- Rulesets mandatados por FR-012 y `bookwright-design.md § 14.3`.
- `target-version = "py311"` permite a `UP` aplicar pyupgrade hasta 3.11.
- `src = ["src", "tests"]` ayuda al ordering de imports (regla `I`) a
  distinguir first-party.

**Alternativas consideradas**:

- Activar `ALL` y excluir reglas problemáticas: rechazado — la
  Constitución y el spec especifican un set cerrado; activar `ALL` añade
  reglas no auditadas y crea churn.

---

## R7 — `mypy` configuración

**Decisión** en `pyproject.toml`:

```toml
[tool.mypy]
strict = true
python_version = "3.11"
files = ["src", "tests"]
# strict implica: disallow_untyped_defs, disallow_any_generics,
# warn_return_any, warn_unused_ignores, no_implicit_reexport, etc.
```

**Rationale**:

- FR-013 + Constitución II.
- `strict = true` es un único flag que activa todas las restricciones
  exigidas.
- `python_version = "3.11"` ancla la evaluación al floor; mypy igualmente
  acepta sintaxis de versiones más nuevas si se usa.

---

## R8 — `pytest` + `pytest-cov` configuración

**Decisión** en `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --cov=bookwright --cov-report=term-missing --cov-report=xml"

[tool.coverage.run]
source = ["src/bookwright"]
branch = true
```

**Rationale**:

- `--cov-report=term-missing` resumen en terminal (Q&A 2026-05-28).
- `--cov-report=xml` produce `coverage.xml` que CI sube como artefacto.
- `branch = true` da una métrica más honesta que line-only.
- **Sin** `--cov-fail-under=N` en esta iteración: la cobertura es meta no
  bloqueante (spec Assumption + Edge Case).

**Suite de smoke prevista**:

1. `test_smoke_import.py`: `import bookwright; assert bookwright.__version__`.
2. `test_cli_version.py`:
   - modo humano: invoca `bookwright version` vía `CliRunner` y verifica
     que stdout contiene la versión del paquete y `unknown` (no hay
     schema todavía).
   - modo `--json`: invoca `bookwright version --json` y verifica que
     stdout es un JSON parseable con keys `package_version` y
     `golem_schema_version: "unknown"`, sin contenido en stderr.
3. `test_cli_check.py`:
   - modo humano: exit 0, líneas con `OK` por chequeo.
   - modo `--json`: JSON con `ok: true`, `checks: [...]`.

---

## R9 — GitHub Actions workflow

**Decisión**: un solo workflow `.github/workflows/tests.yml` con un job
`quality` que corre matriz `python-version: ["3.11", "3.12"]` para tests,
y pasos adicionales (lint + mypy) que se ejecutan **solo** cuando
`matrix.python-version == '3.12'`.

**Estructura**:

```yaml
name: CI

on:
  push:
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true
      - name: Set up Python
        run: uv python install ${{ matrix.python-version }}
      - name: Sync deps
        run: uv sync --frozen
      - name: Lint (ruff check)
        if: matrix.python-version == '3.12'
        run: uv run ruff check .
      - name: Format check (ruff format --check)
        if: matrix.python-version == '3.12'
        run: uv run ruff format --check .
      - name: Type check (mypy --strict)
        if: matrix.python-version == '3.12'
        run: uv run mypy
      - name: Tests
        run: uv run pytest
      - name: Upload coverage
        if: matrix.python-version == '3.12'
        uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.python-version }}
          path: coverage.xml
```

**Rationale**:

- FR-014: dispara en push (cualquier rama) y PR contra `main`.
- FR-015a: matriz cubre 3.11 + 3.12; lint y type-check solo en 3.12 (la
  versión más alta, como permite la FR).
- FR-016: si cualquier paso falla, el job falla → el agregador de checks
  de la PR queda rojo.
- FR-017: `uv sync --frozen` usa el `uv.lock` commiteado, garantizando
  paridad con local.
- `timeout-minutes: 10` cubre el caso de "pipeline cuelga" del Edge Case
  del spec.
- `fail-fast: false`: queremos ver ambas celdas falladas si las hay, no
  solo la primera.

**Alternativas consideradas**:

- Tres jobs separados (`tests`, `lint`, `typecheck`): rechazado por
  simplicidad — un job con pasos visibles cumple FR-015 ("jobs
  **independientes o pasos visibles**") sin multiplicar la cuenta de
  jobs.
- Cachear `~/.cache/uv` manualmente: rechazado — `astral-sh/setup-uv@v3`
  con `enable-cache: true` lo hace por nosotros.

---

## R10 — Pre-commit hooks

**Decisión** en `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.7   # se ancla a versión concreta; se mantiene en sync con dev dep
    hooks:
      - id: ruff-format
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-toml
      - id: check-yaml
```

**Rationale**:

- FR-011: cubre formateo (auto-corregible), lint, TOML, YAML.
- `--exit-non-zero-on-fix` para `ruff`: cuando ruff arregla algo, el
  commit se aborta para que el dev re-stagee los cambios — comportamiento
  exigido por FR-011 / US3 Acceptance Scenario #1.
- `check-toml` y `check-yaml` son hooks oficiales del repo
  `pre-commit-hooks` (estándar de facto).
- **No** incluimos `mypy` en pre-commit local: es lento sobre archivos
  staged y la CI ya lo gatea. Mantener el ciclo local rápido.

**Activación**: el README documenta `uv run pre-commit install` como paso
post-`uv sync`. Si el dev lo omite, la CI sigue siendo la red de seguridad
(Edge Case del spec).

---

## R11 — `__version__` y discovery

**Decisión**: `src/bookwright/__init__.py` contiene:

```python
__version__ = "0.0.1"
```

`hatch.version.path` lo lee al build-time. En runtime, `version --json`
también lee este valor directamente (`from bookwright import __version__`)
porque es el camino más simple y evita la dependencia de
`importlib.metadata` (que requiere que el paquete esté instalado, no solo
importable — relevante para `python -m bookwright` en desarrollo).

**Rationale**:

- Single source of truth (DRY): `__version__` vive en un solo lugar.
- Funciona tanto en modo desarrollo (`uv run`) como en wheel instalado.

---

## R12 — `bookwright check` superficie

**Decisión** en `src/bookwright/commands/check.py`: dos chequeos en esta
iteración:

1. **`python_version`**: `sys.version_info >= (3, 11)` → OK; si menor, FAIL
   con `detail` indicando versión encontrada vs. requerida.
2. **`dependencies`**: itera sobre la lista runtime declarada
   (`typer`, `rich`, `rdflib`, `pydantic`, `tomlkit`, `jinja2`,
   `slugify` — alias de python-slugify —, `platformdirs`, `uuid_utils`)
   e intenta `importlib.import_module(name)`. Cada uno produce un chequeo
   con `name` = `dependency:<modulo>`. Si falla el import, FAIL con
   `detail` = mensaje del `ImportError`.

El exit code es `0` si todos pasan, `1` si alguno falla.

**Rationale**:

- FR-007 exige "(a) versión de Python ≥ 3.11, (b) que cada dependencia
  declarada está importable". Cubierto exactamente.
- La lista de dependencias se mantiene como una constante local en
  `check.py`; un solo lugar para actualizar cuando la Constitución amplíe
  el set.
- No se chequea conectividad de red ni nada extra: SC-004 exige < 5 s, y
  estos imports son sub-segundo.

---

## R13 — Licencia y archivos legales

**Decisión**: Apache-2.0. El archivo `LICENSE` se commitea con el texto
oficial completo. `pyproject.toml` declara
`license = { text = "Apache-2.0" }` (SPDX expression simple) y
`classifiers = ["License :: OSI Approved :: Apache Software License"]`.

**Rationale**:

- `bookwright-design.md § 6` lo lista como `LICENSE Apache-2.0`.
- Apache-2.0 es estándar para herramientas Python con potencial de
  adopción amplia.

**Sin `NOTICE`** por ahora — no hay contribuciones externas que requieran
atribución explícita; se añadirá si y cuando.

---

## Open questions consolidadas

Ninguna. Todas las preguntas del spec se resolvieron en la sesión de
clarificación del 2026-05-28 y todas las decisiones técnicas se cierran en
las R1–R13 arriba.
