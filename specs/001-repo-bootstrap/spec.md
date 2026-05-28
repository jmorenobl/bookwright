# Feature Specification: Bootstrap inicial del repositorio Bookwright

**Feature Branch**: `001-repo-bootstrap`

**Created**: 2026-05-28

**Status**: Draft

**Input**: User description: "Bootstrap inicial del repositorio Bookwright: entorno reproducible con `uv sync`, entry point `bookwright` con `version` y `check`, pre-commit hooks (ruff + validación TOML/YAML), CI con tests + lint + type-check, mypy strict y ruff (rulesets E, W, F, I, B, UP, RUF, SIM, PL; line-length 100). Sin lógica de dominio."

## Clarifications

### Session 2026-05-28

- Q: ¿`bookwright version` y `bookwright check` deben soportar `--json` ya en este bootstrap? → A: Sí, ambos soportan `--json` desde esta iteración; el modo humano-legible sigue siendo el default y los tests cubren las dos formas.
- Q: ¿Qué versiones de Python debe ejercitar CI en cada push/PR? → A: Matriz Python 3.11 + 3.12 (floor constitucional + estable actual); 3.13 queda fuera hasta que haya razón concreta para añadirla.
- Q: ¿Cómo descubre `bookwright version` la versión del schema GOLEM? → A: Lookup basado en archivo — se lee desde una ruta fija dentro del paquete; si el archivo no existe, se reporta `"unknown"`. Iteración 5 cumple el contrato dejando el archivo en su sitio sin tocar `version`.
- Q: ¿Dónde se reporta la cobertura de tests en este bootstrap? → A: Local-only: summary en terminal + artefacto (XML/HTML) adjunto al run de CI; sin servicio externo (Codecov/Coveralls) en esta iteración.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Onboarding sin fricción para un nuevo desarrollador (Priority: P1)

Un desarrollador (interno o colaborador externo) clona el repositorio en su máquina por primera vez. Quiere comprobar que puede empezar a trabajar sin investigar comandos ni preparar el entorno manualmente. Ejecuta una única instrucción de instalación y, segundos después, puede invocar la herramienta `bookwright`, ver la ayuda y consultar la versión.

**Why this priority**: Es la condición habilitante de todo lo demás. Si un dev no puede llegar a un entorno funcional en su primer intento, ninguna iteración posterior es viable. Marca el hito M0 del proyecto.

**Independent Test**: Tomar un equipo limpio con Python 3.11+ disponible, clonar el repo, correr el comando estándar de sincronización del entorno y luego invocar `bookwright --help` y `bookwright version`. Ambos deben responder sin errores.

**Acceptance Scenarios**:

1. **Given** un equipo con Python 3.11 o superior y el gestor de paquetes del proyecto instalados, **When** el dev clona el repo y ejecuta el comando de sincronización del entorno, **Then** se crea un entorno virtual con todas las dependencias declaradas en menos de 60 segundos y sin intervención manual adicional.
2. **Given** el entorno sincronizado, **When** el dev ejecuta `bookwright --help`, **Then** se muestra el listado de subcomandos disponibles (incluyendo al menos `version` y `check`) con descripciones legibles.
3. **Given** el entorno sincronizado, **When** el dev ejecuta `bookwright version`, **Then** se imprime la versión del paquete y la versión del schema GOLEM; si el schema todavía no existe en el repo, la versión del schema se reporta como `unknown` sin error.

---

### User Story 2 - Quality gates automáticos en cada push / pull request (Priority: P2)

El mantenedor del proyecto necesita garantizar que ninguna iteración futura introduzca regresiones silenciosas de estilo, tipos o comportamiento. Cuando alguien envía un push o abre una pull request, un sistema de integración continua ejecuta automáticamente la suite de tests, las verificaciones de lint y los chequeos de tipos. Cualquier fallo bloquea el merge.

**Why this priority**: Sin gates automáticos, las exigencias de la Constitución (Principio VIII, cobertura ≥ 80 %, mypy strict) dependen de disciplina manual y se erosionan rápido. Esta historia convierte las reglas en barreras de entrada.

**Independent Test**: Abrir una PR con un cambio que falle deliberadamente uno de los chequeos (por ejemplo, código sin anotación de tipos o un import sin usar). El sistema de CI debe reportar el fallo, marcar la PR como no apta para merge y mostrar logs accionables.

**Acceptance Scenarios**:

1. **Given** una PR contra `main` con código que pasa todos los chequeos, **When** el sistema de CI corre la pipeline completa, **Then** los jobs de tests, lint y type-check terminan con estado verde y la PR queda lista para merge.
2. **Given** una PR con código que falla cualquiera de las tres comprobaciones (un test rojo, una regla de lint violada, un error de tipo), **When** se ejecuta la pipeline, **Then** el job correspondiente termina con estado rojo, el agregador de checks de la PR marca falla, y el merge queda bloqueado por la configuración del repo.
3. **Given** un push directo sobre cualquier rama de feature, **When** la pipeline corre, **Then** los mismos chequeos se aplican y se reportan al autor del push.
4. **Given** una PR con código limpio pero cuya suite de tests no termina dentro del tiempo máximo permitido, **When** la pipeline corre, **Then** el job falla por timeout con un mensaje claro y la PR queda bloqueada.

---

### User Story 3 - Higiene local antes de cada commit (Priority: P3)

Un dev hace cambios en su rama local y ejecuta `git commit`. Antes de que el commit se materialice, una serie de hooks automáticos formatean el código y validan archivos de configuración. Si algo necesita corrección, el commit se aborta con un mensaje claro y, donde sea posible, los archivos se reformatean automáticamente para que el dev pueda reintentar.

**Why this priority**: Empuja la disciplina a la izquierda del workflow — los errores se detectan antes de que viajen al CI, ahorrando ciclos y reduciendo PRs ruidosas. No es bloqueante (P1 y P2 ya cubren el camino crítico) pero mejora notablemente la experiencia de desarrollo y reduce churn de commits "fix lint".

**Independent Test**: En un clon local, modificar un archivo de código con formato inválido y un TOML con sintaxis rota. Intentar `git commit`. El hook debe (a) reformatear el código automáticamente, (b) rechazar el commit del TOML inválido con un mensaje accionable, y (c) permitir reintentar el commit una vez corregidos los archivos.

**Acceptance Scenarios**:

1. **Given** un repo recién clonado y el dev ha ejecutado la instalación de hooks, **When** intenta hacer commit de un archivo Python con formato no canónico, **Then** el hook lo reformatea automáticamente, aborta el commit actual y le indica que vuelva a añadir los cambios al stage.
2. **Given** un dev hace commit con un archivo TOML malformado, **When** se ejecutan los hooks, **Then** el hook de validación de TOML aborta el commit reportando línea y motivo del error.
3. **Given** un dev hace commit con un archivo YAML malformado, **When** se ejecutan los hooks, **Then** el hook de validación de YAML aborta el commit reportando línea y motivo del error.
4. **Given** un commit con código Python que pasa formato pero viola reglas de lint, **When** se ejecutan los hooks, **Then** el hook de lint aborta el commit listando las reglas violadas.

---

### User Story 4 - Verificación del entorno bajo demanda (Priority: P4)

Después de instalar dependencias o cambiar de máquina, un dev (o un script de CI) necesita confirmar que su entorno cumple los requisitos mínimos del proyecto: versión de Python, dependencias instaladas y disponibilidad de las herramientas declaradas. Ejecuta `bookwright check` y obtiene un veredicto inequívoco.

**Why this priority**: Acelera el diagnóstico cuando algo va mal ("¿es mi Python?", "¿faltó instalar X?") pero no es estrictamente necesario para entregar el resto del bootstrap. Es una capa de comodidad encima del flujo principal.

**Independent Test**: En un entorno válido, ejecutar `bookwright check` y verificar exit code 0 y output que confirma cada requisito. Repetir en un entorno con Python 3.10 y verificar que el comando reporta el fallo específico y devuelve exit code distinto de 0.

**Acceptance Scenarios**:

1. **Given** un entorno que cumple todos los requisitos, **When** el dev ejecuta `bookwright check`, **Then** se imprime un resumen con cada chequeo en estado OK y el proceso termina con exit code 0 en menos de 5 segundos.
2. **Given** un entorno con Python < 3.11, **When** se ejecuta `bookwright check`, **Then** el chequeo de versión falla con un mensaje que indica versión requerida vs. encontrada y el proceso termina con exit code distinto de 0.
3. **Given** un entorno donde alguna dependencia declarada no está instalada, **When** se ejecuta `bookwright check`, **Then** se reporta la dependencia faltante y el proceso termina con exit code distinto de 0.

---

### Edge Cases

- **Schema GOLEM ausente**: el repo aún no contiene un archivo de schema; `bookwright version` debe imprimir literalmente `unknown` para la versión del schema, no romper ni inventar un valor.
- **Sin red durante sincronización del entorno**: si el dev está offline y no tiene caché local, el comando falla con el error nativo del gestor de paquetes; no es responsabilidad del bootstrap mitigarlo, pero el README debe mencionar la condición.
- **Pre-commit no instalado**: si el dev olvida ejecutar el comando que activa los hooks localmente, los commits se materializan sin protección local; la CI sigue siendo la red de seguridad final.
- **CI sin permisos de red para descargar dependencias**: la pipeline debe fallar fuerte y rápido con un job dedicado, no quedarse colgada.
- **Conflicto de versión de Python entre el gestor de paquetes y la del sistema**: el entorno virtual debe usar la versión declarada en el proyecto, no la del intérprete por defecto del sistema.

## Requirements *(mandatory)*

### Functional Requirements

**Entorno y entry point**

- **FR-001**: El repositorio MUST declarar un proyecto Python con metadatos completos (nombre, versión, descripción) y un manifest de dependencias resoluble por el gestor de paquetes mandatado por la Constitución (`uv`).
- **FR-002**: El repositorio MUST commitear un lockfile reproducible de dependencias, de modo que dos sincronizaciones del entorno en momentos distintos resuelvan exactamente las mismas versiones.
- **FR-003**: El proyecto MUST exponer un ejecutable de consola llamado `bookwright`, registrado como entry point del paquete.
- **FR-004**: Invocar `bookwright` sin argumentos o con `--help` MUST mostrar un resumen del CLI con la lista de subcomandos disponibles y su propósito.

**Subcomandos mínimos**

- **FR-005**: El subcomando `bookwright version` MUST imprimir la versión del paquete (leída desde su metadata) y la versión del schema GOLEM congelada en el repo.
- **FR-006**: `bookwright version` MUST descubrir la versión del schema GOLEM leyendo desde una ruta de archivo fija dentro del paquete (el plan concretará la ruta, p. ej. `src/bookwright/schemas/golem/VERSION`). Cuando ese archivo no exista todavía en el repo, MUST reportar `unknown` como versión del schema sin abortar. El lookup MUST NOT importar `rdflib` ni dependencias de dominio.
- **FR-007**: El subcomando `bookwright check` MUST verificar al menos: (a) versión de Python en uso ≥ 3.11, (b) que cada dependencia declarada está importable.
- **FR-008**: `bookwright check` MUST terminar con exit code 0 si todos los chequeos pasan y con exit code distinto de 0 si alguno falla.
- **FR-009**: `bookwright check` MUST imprimir un reporte legible con un estado por chequeo (OK / FAIL) y, en caso de fallo, una descripción del problema.
- **FR-009a**: Tanto `bookwright version` como `bookwright check` MUST aceptar la bandera `--json`. Cuando se pasa, MUST emitir un único documento JSON en stdout (y solo eso); cualquier mensaje de progreso o ruido va a stderr. Sin la bandera, mantienen su salida humano-legible por defecto. Concretamente, en modo `--json` stdout MUST ser exactamente `json.dumps(payload, separators=(",", ":")) + "\n"` (igualdad byte-a-byte). Cualquier byte adicional en stdout — espacios, escapes ANSI, prosa, JSON parcial concatenado — es una violación contractual del Principio IX y MUST hacer fallar los tests.
- **FR-009b**: El esquema JSON de `version --json` MUST incluir, como mínimo, las claves `package_version` y `golem_schema_version` (esta última con valor `"unknown"` cuando el schema no exista). El de `check --json` MUST incluir un campo `checks` (lista de objetos con `name`, `status` ∈ `{ "ok", "fail" }`, y `detail` opcional) y un campo `ok` booleano agregado.
- **FR-009c**: La suite de tests MUST cubrir tanto la salida humano-legible como la salida `--json` de `version` y `check`, validando exit codes y forma del documento JSON.

**Calidad estática local**

- **FR-010**: El repo MUST incluir configuración de pre-commit hooks que se ejecuten automáticamente sobre los archivos staged en cada `git commit`.
- **FR-011**: Los hooks locales MUST cubrir, como mínimo: formateo de código (auto-corregible), lint de código, validación sintáctica de archivos TOML y validación sintáctica de archivos YAML.
- **FR-012**: El lint MUST aplicar los siguientes conjuntos de reglas: errores (E), warnings (W), pyflakes (F), ordering de imports (I), bugbear (B), pyupgrade (UP), reglas específicas del linter elegido (RUF), simplificación (SIM) y pylint (PL); con un máximo de 100 caracteres por línea.
- **FR-013**: La configuración de tipado estático MUST estar habilitada en modo strict: prohibir definiciones sin anotación de tipos, prohibir genéricos sin parámetros, y advertir cuando una función retorna un valor de tipo `Any`.

**Quality gates remotos (CI)**

- **FR-014**: El repo MUST incluir una configuración de integración continua que se dispare en cada push a cualquier rama y en cada pull request contra `main`.
- **FR-015**: La pipeline de CI MUST ejecutar, como jobs independientes o pasos visibles: (a) la suite de tests, (b) lint y verificación de formato, (c) chequeo de tipos en modo strict.
- **FR-015a**: La pipeline de CI MUST ejercitar la suite de tests sobre una matriz de intérpretes Python que incluya como mínimo `3.11` y `3.12`. Lint y type-check pueden correr sobre un único intérprete (típicamente el más alto de la matriz) si así se acuerda en el plan; los tests, no.
- **FR-016**: Si cualquiera de los chequeos de CI falla en cualquier celda de la matriz, la pipeline MUST terminar con estado rojo y el agregador de checks de la PR MUST marcarse como no apto para merge.
- **FR-017**: La CI MUST instalar dependencias usando el mismo lockfile reproducible que el desarrollador local, de modo que el entorno de CI sea idéntico al local en versiones (modulo la versión de Python que dicta cada celda de la matriz).

**Harness de tests**

- **FR-018**: El repo MUST incluir un directorio `tests/` a la raíz con al menos dos tests de smoke: uno que importe el paquete principal y otro que invoque `bookwright version` como un subproceso o equivalente y verifique su salida.
- **FR-019**: El runner de tests MUST poder ejecutarse localmente con un único comando y reportar resultados en menos de 10 segundos para la suite de smoke.
- **FR-020**: El runner de tests MUST estar configurado para producir un reporte de cobertura y MUST activar el gate constitucional `--cov-fail-under=80` (Principio VIII, NON-NEGOTIABLE) desde esta iteración sin excepciones — la superficie de código del bootstrap (~200 LOC) es trivialmente cubierta por los smoke tests de US1 y US4. La cobertura se reporta solo localmente: resumen en terminal y artefacto (XML o HTML) adjunto al run de CI; en esta iteración NO se publica a servicios externos (Codecov, Coveralls u otros) ni se introduce ningún token/secreto asociado.

**Disciplina de scope**

- **FR-021**: La iteración MUST NOT introducir lógica de dominio: nada de manifest, ontología GOLEM, indexer, integrations, comandos de validación, ni plantillas de Bible / outline / constitution.
- **FR-022**: La iteración MUST NOT modificar `.specify/memory/constitution.md` ni añadir dependencias fuera de las explícitamente listadas en la Constitución para esta etapa.

### Key Entities

- **Paquete `bookwright`**: artefacto Python instalable que expone el ejecutable de consola y la versión del proyecto; vive bajo `src/bookwright/` por mandato del Principio III.
- **Lockfile reproducible**: archivo versionado que congela el grafo de dependencias completo; condición para que la sincronización del entorno sea determinista.
- **Configuración de pre-commit**: archivo declarativo que enumera los hooks locales, sus versiones y los patrones de archivos a los que se aplican.
- **Pipeline de CI**: configuración versionada que describe los jobs ejecutados automáticamente en push / PR.
- **Reporte de schema GOLEM**: información sobre la versión del schema ontológico; en esta iteración se reporta como `unknown` porque el schema todavía no existe en el repo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un desarrollador con Python 3.11+ y el gestor de paquetes instalados puede ir de `git clone` a `bookwright --help` exitoso en menos de 60 segundos sin leer documentación adicional.
- **SC-002**: El 100 % de los pull requests que rompen lint, type-check o tests son bloqueados automáticamente por CI antes de poder mergear a `main`.
- **SC-003**: El 100 % de los commits aceptados localmente con hooks instalados pasaron las cuatro validaciones (formato, lint, TOML, YAML) antes de materializarse.
- **SC-004**: `bookwright check` retorna un veredicto pass/fail definitivo en menos de 5 segundos en un equipo de desarrollo estándar.
- **SC-005**: La suite de tests de smoke se ejecuta completa (importar el paquete + invocar `bookwright version`) en menos de 10 segundos.
- **SC-006**: Una sincronización completa del entorno en un equipo con caché vacía pero red disponible se completa en menos de 60 segundos para la lista mínima de dependencias declarada en la Constitución.
- **SC-007**: Cualquier dev clona el repo, ejecuta los pasos del README para instalar los hooks locales, y los obtiene activos en menos de 2 minutos sin intervención manual adicional.
- **SC-008**: La pipeline de CI completa (tests + lint + type-check sobre el bootstrap mínimo) termina en menos de 5 minutos por ejecución.

## Assumptions

- **Constitución vigente como base**: las decisiones de stack (Python 3.11+, `uv` como gestor, `hatchling` como build backend, `ruff` como linter/formateador, `mypy` strict como type-checker, `pytest` como runner) ya están ratificadas por la Constitución v1.0.0 y no se reabren en este spec. Los nombres concretos de herramientas que aparecen en los FR son derivados de esa Constitución, no decisiones nuevas.
- **Plataforma de CI**: se asume GitHub Actions como sustrato de CI, dado que el repo opera sobre GitHub y la documentación de Spec Kit lo asume por defecto. Si en el futuro se quiere portar a otra plataforma será una decisión separada.
- **Activación local de pre-commit**: los hooks locales requieren un paso manual de instalación por dev (`pre-commit install` o equivalente). El bootstrap proporciona la configuración y la documenta; activarla es responsabilidad del dev.
- **Schema GOLEM diferido**: el archivo de schema ontológico aún no existe en el repo y se introducirá en una iteración posterior (5 — GOLEM domain model). Esta iteración solo debe tolerar su ausencia.
- **Sin dependencias de dominio importadas todavía**: las dependencias de dominio del v0 (`rdflib`, `pydantic`, `tomlkit`, `jinja2`, `python-slugify`, `platformdirs`, `uuid-utils`) pueden declararse en `pyproject.toml` ya en esta iteración para estabilizar el lockfile, pero no se importan desde código. Solo `typer` y `rich` se importan, para soportar el CLI mínimo.
- **Framework de pre-commit**: se asume el framework estándar `pre-commit` (pre-commit.com) como mecanismo, por ser el más extendido en el ecosistema Python y compatible con todos los hooks listados.
- **Sistema operativo del dev**: el flujo se valida principalmente en macOS y Linux; Windows queda como best-effort hasta que un colaborador lo pruebe explícitamente.
- **Cobertura activa desde día uno**: la superficie de código de esta iteración (entry point + `version` + `check`, ~200 LOC) es trivialmente testeable. El gate `--cov-fail-under=80` exigido por la Constitución (Principio VIII, NON-NEGOTIABLE) se activa en esta iteración sin excepciones; los smoke tests de US1 y US4 cubren toda la superficie.
