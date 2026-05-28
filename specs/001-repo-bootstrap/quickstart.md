# Quickstart — Bookwright iteración 1 (Bootstrap)

**Target reader**: un desarrollador que clona el repo por primera vez,
después de que esta iteración haya mergeado a `main`.

Este documento es la prueba operativa de las historias **US1** y **US3**
del spec. Si los pasos abajo no funcionan exactamente como están escritos,
la iteración no está terminada.

## Prerrequisitos

- Python ≥ 3.11 disponible en `PATH` (o que `uv` pueda instalar — `uv
  python install` lo hace por ti).
- [`uv`](https://docs.astral.sh/uv/) ≥ 0.4. Instalación:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # o en macOS via Homebrew:
  brew install uv
  ```

- Git.

## Flujo "from zero to working CLI" (US1, SC-001, SC-006)

```bash
git clone <repo-url> bookwright
cd bookwright
uv sync                       # crea .venv y resuelve deps desde uv.lock (< 60 s)
uv run bookwright --help      # muestra ayuda y subcomandos
uv run bookwright version     # muestra versión del paquete + "unknown" para GOLEM schema
uv run bookwright check       # exit 0, OK por cada chequeo
```

Si `uv sync` tarda > 60 s con red disponible, hay un regression de
SC-006: investigar.

## Comprobar el contrato JSON (US1 + Principio IX)

```bash
uv run bookwright version --json
# Esperado (compacto, una sola línea, terminado en \n):
#   {"package_version":"0.0.1","golem_schema_version":"unknown"}

uv run bookwright check --json
# Esperado:
#   {"ok":true,"checks":[{"name":"python_version","status":"ok","detail":"3.12.x"},...]}
```

`stderr` puede estar vacío o contener prosa diagnóstica; `stdout`
**debe** contener exactamente un documento JSON.

Validación contractual rápida (requiere `jq`):

```bash
uv run bookwright version --json | jq '.package_version, .golem_schema_version'
uv run bookwright check --json | jq '.ok, .checks | length'
```

## Activar pre-commit hooks localmente (US3, SC-007)

```bash
uv run pre-commit install      # < 2 min, normalmente segundos
```

Probar que los hooks pegan, usando un directorio scratch ignorado por git
(`.scratch/` está en `.gitignore`; el `-f` en `git add` lo fuerza solo
para el experimento, y al borrar el directorio el repo vuelve a estado
limpio sin riesgo de mutar `pyproject.toml`):

```bash
mkdir -p .scratch

# 1. Test de formato auto-corregible:
echo "x=1" > .scratch/scratch.py
git add -f .scratch/scratch.py
git commit -m "test hook"        # ruff-format reescribe el archivo y aborta
git restore --staged .scratch/scratch.py

# 2. Test de TOML inválido:
echo "[broken" > .scratch/scratch.toml
git add -f .scratch/scratch.toml
git commit -m "test hook"        # check-toml aborta con línea/motivo
git restore --staged .scratch/scratch.toml

# 3. Test de YAML inválido:
printf 'a:\n  b: c\n d: e\n' > .scratch/scratch.yaml
git add -f .scratch/scratch.yaml
git commit -m "test hook"        # check-yaml aborta con línea/motivo
git restore --staged .scratch/scratch.yaml

rm -rf .scratch
```

## Correr la suite de tests (US2 indirecto, SC-005)

```bash
uv run pytest                  # < 10 s, todos verdes
uv run pytest -k version       # filtra a tests del subcomando version
```

Cobertura local:

```bash
uv run pytest                  # muestra `--cov` report en terminal por defecto
open htmlcov/index.html        # si se generó (cuando se añada --cov-report=html ad-hoc)
```

## Correr los gates de calidad localmente (US2)

Replica exactamente lo que hace CI:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

Si cualquiera falla en local, fallará en CI. Si todos pasan en local pero
CI falla, hay un drift entre `pyproject.toml` y `uv.lock` (correr `uv
lock` y commitear).

## Comprobar el comportamiento en CI

Tras push o apertura de PR contra `main`:

1. GitHub Actions dispara `.github/workflows/tests.yml`.
2. El job `quality` corre en matriz `python-version: ["3.11", "3.12"]`.
3. Tanto `3.11` como `3.12` corren tests; solo `3.12` corre lint + mypy.
4. El job termina en < 5 minutos (SC-008).
5. El check agregador de la PR refleja el estado: cualquier fallo bloquea
   merge (FR-016).
6. El artefacto `coverage-3.12` aparece descargable en la pestaña Actions.

## Caminos de fallo esperados

| Escenario | Comando | Comportamiento esperado |
|---|---|---|
| Python < 3.11 | `bookwright check` | exit ≠ 0; detail `"found X.Y.Z, requires >=3.11"` |
| Dependencia ausente (improbable tras `uv sync`) | `bookwright check` | exit ≠ 0; `dependency:<x>` con status `fail` |
| Schema GOLEM ausente (caso actual) | `bookwright version` | `golem_schema_version: "unknown"`, exit 0 |
| TOML malformado en commit | `git commit` | hook `check-toml` aborta con línea/motivo |
| YAML malformado en commit | `git commit` | hook `check-yaml` aborta con línea/motivo |
| Push sin red en CI | GitHub Actions | `uv sync --frozen` falla, job rojo |

## Cómo el dev valida la iteración antes de cerrar la PR

Procedimiento de validación end-to-end. Cada paso debe terminar como se
describe; si alguno falla, la PR no está lista para merge.

1. **Cold clone + bootstrap.** Desde un directorio limpio: `git clone
   <repo-url> bookwright && cd bookwright && uv sync`. El paso `uv sync`
   debe completar en < 60 s con red disponible (SC-006).
2. **Superficie CLI.** `uv run bookwright --help` lista `version` y
   `check` como subcomandos.
3. **Subcomando `version`.** `uv run bookwright version` imprime la
   versión del paquete y `unknown` para el schema GOLEM. Con `--json`,
   `stdout` contiene exactamente un documento JSON conforme a
   [contracts/version.schema.json](contracts/version.schema.json).
4. **Subcomando `check`.** `uv run bookwright check` retorna exit 0 en el
   entorno del repo. Con `--json`, `stdout` cumple
   [contracts/check.schema.json](contracts/check.schema.json).
5. **Pre-commit local.** `uv run pre-commit install` instala los hooks.
   Reproducir los tres casos de `§ Activar pre-commit hooks localmente`
   (ruff-format, check-toml, check-yaml): cada uno aborta el commit con
   diagnóstico legible.
6. **Gates locales en bloque.** `uv run pytest && uv run ruff check . &&
   uv run ruff format --check . && uv run mypy` termina con cero issues.
   Esto es exactamente lo que CI ejecuta.
7. **CI verde sobre la PR.** Tras push, el workflow
   `.github/workflows/tests.yml` pasa en matriz `python-version: ["3.11",
   "3.12"]` en < 5 min (SC-008).
8. **Árbol del repo.** El layout coincide exactamente con `plan.md §
   Project Structure → Source Code` — ni un archivo de más, ni uno de
   menos. Verificable con `find src/bookwright -type d` y `find tests
   -type f`.

Los pasos 1, 7 y la parte "cold" de 5 dependen de red, CI o un clon
fresco y no se pueden auditar desde un working tree existente; ejecutarlos
explícitamente antes de pedir review.
