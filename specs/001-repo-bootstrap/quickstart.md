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

Probar que los hooks pegan:

```bash
# 1. Test de formato auto-corregible:
echo "x=1" > tests/_scratch.py
git add tests/_scratch.py
git commit -m "test hook"      # ruff-format debe reescribir el archivo y abortar
rm tests/_scratch.py

# 2. Test de TOML inválido:
echo "[broken" >> pyproject.toml
git add pyproject.toml
git commit -m "test hook"      # check-toml debe abortar con línea/motivo
git checkout pyproject.toml
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

## Definición de "done" para esta iteración

Cuando todas las afirmaciones siguientes son verdaderas:

- [ ] `uv sync` desde clean checkout funciona en < 60 s.
- [ ] `uv run bookwright --help` lista `version` y `check`.
- [ ] `uv run bookwright version` y `--json` ambos pasan los smoke tests.
- [ ] `uv run bookwright check` y `--json` ambos pasan los smoke tests
      con exit 0 en el entorno del repo.
- [ ] `uv run pre-commit install` instala hooks; los hooks de ruff,
      check-toml y check-yaml bloquean commits malformados.
- [ ] `uv run pytest && uv run ruff check . && uv run ruff format --check
      . && uv run mypy` pasa local con cero issues.
- [ ] La pipeline CI corre verde sobre PR contra `main` en < 5 min.
- [ ] El árbol del repo coincide exactamente con `plan.md § Project
      Structure → Source Code` (ni un archivo de más, ni uno de menos).
