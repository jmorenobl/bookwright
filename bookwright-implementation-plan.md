# Bookwright — Plan de implementación con Spec Kit

> **Documento complementario a:** `bookwright-design.md`.
> **Propósito:** secuencia de iteraciones para implementar Bookwright usando Spec Kit como herramienta de desarrollo. Cada iteración tiene un prompt listo para invocar `/speckit-specify`.
> **Audiencia:** Jorge (o cualquier desarrollador con Spec Kit instalado y `bookwright-design.md` en el root del repo).

---

## 0. Cómo usar este documento

Este plan asume:

- Spec Kit ≥ 0.8 instalado (`uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`).
- El repo destino inicializado con `specify init bookwright --integration claude` (o tu integración preferida).
- El archivo `bookwright-design.md` en el root del repo, accesible para que el agente lo lea cuando los prompts lo referencien.
- Familiaridad con el flujo Spec-Driven Development de Spec Kit (`constitution → specify → clarify → plan → tasks → analyze → implement`).

Cada iteración produce un **branch nuevo con su spec** (`specs/NNN-<short-name>/spec.md`). El orden importa: cada iteración construye sobre artefactos producidos por las anteriores.

---

## 1. Setup inicial

### 1.1 Preparar el repo

```bash
# Estando dentro del directorio donde ya viven bookwright-design.md y este plan:
specify init --here --integration claude
# spec-kit inicializa .specify/, .claude/skills/speckit-*/ y un repo git (si no existía).
# Los dos .md que ya están en el directorio no se tocan.
```

### 1.2 Establecer la constitution del proyecto

Antes de cualquier iteración, ejecuta `/speckit-constitution` con este prompt:

```
/speckit-constitution

Bookwright es un toolkit Python para producción de libros (novelas, ensayos, memorias) que aplica Spec-Driven Development al dominio narrativo. El diseño completo está en bookwright-design.md.

Principios no-negociables:

1. Texto plano como fuente de verdad. Todos los artefactos relevantes (manuscrito, bible, constitution, grafo) deben ser Markdown, TOML o Turtle. Nada de SQLite, JSON binario ni formatos opacos.

2. Python 3.11+, ecosistema moderno. Usar Typer para CLI, Pydantic v2 para modelos, rdflib para grafos, hatchling como build backend, uv como package manager, ruff y mypy strict para calidad.

3. src-layout. Todo el código de producción en src/bookwright/. Tests en tests/. Sin excepciones.

4. Comandos del CLI en archivos separados, no monolitos. Cada subcomando es un módulo bajo src/bookwright/commands/. Sin archivos de más de 500 líneas.

5. Plugin-based desde el inicio. La arquitectura de integraciones es SkillsIntegration + INTEGRATION_REGISTRY (espejado del refactor de Spec Kit). NO replicar AGENT_CONFIG monolítico.

6. Solo Agent Skills, nunca commands legacy. Bookwright se alinea con Agent Skills (agentskills.io) por portabilidad, progressive disclosure y validación estructural. Nunca escribe en .claude/commands/ ni equivalentes.

7. Skills generados deben cumplir el estándar agentskills.io: name < 64 chars y debe matchear el directorio padre, description < 1024 chars, frontmatter YAML válido.

8. Tests obligatorios. Mínimo 80% de cobertura en v0. Unit tests para core, integration tests para flows, E2E para el workflow completo del usuario.

9. JSON sobre stdout. Cualquier comando que devuelva datos al agente IA acepta --json. Mensajes informativos a stderr.

10. Decisiones del documento de diseño son axiomas. La sección 16 de bookwright-design.md lista decisiones ya tomadas que NO se re-cuestionan. El agente las trata como restricciones fijas.

Restricciones técnicas:

- Python 3.11+.
- Dependencias mínimas: typer, rich, rdflib, pydantic, tomlkit, jinja2, python-slugify, platformdirs, uuid-utils.
- Build: hatchling. Lock: uv.lock.
- Distribución: PyPI como bookwright-cli. Tags semver v0.X.Y.
- CI: GitHub Actions con tests + ruff + mypy.

Fuera de scope hasta post-v0:

- Sistema de investigación y verificación (M4 / v0.2, iteraciones 13–17).
- Búsqueda vectorial (v0.3, ChromaDB sobre rdflib — sin GrafeoIndexer).
- Export EPUB/PDF (v1.0).

Consulta bookwright-design.md para el detalle exhaustivo de cualquier punto.
```

Tras `/speckit-constitution`, Spec Kit crea `.specify/memory/constitution.md`. Revísalo y ajústalo si hace falta antes de continuar.

### 1.3 Convenciones de iteración

Cada iteración sigue este flujo:

```
/speckit-specify <prompt de la iteración>    # crea branch NNN-name + spec.md
/speckit-clarify                              # responde preguntas, refina spec
/speckit-plan <pista técnica>                 # genera plan.md con el cómo
/speckit-tasks                                # desglose en tareas
/speckit-analyze                              # cross-artifact check
/speckit-implement                            # ejecuta tareas
```

**No saltes `/speckit-clarify`**. Es donde se cierran ambigüedades antes de codificar. Si el prompt es muy completo y no genera dudas, di explícitamente "no hay clarificaciones" para desbloquear el siguiente paso.

**En `/speckit-plan` aprovecha el doc de diseño**. El prompt típico es: *"Sigue el stack y la arquitectura definidos en bookwright-design.md, secciones X.Y. Restricciones específicas: [lo que aplique]."*

**Merge a `main` tras cada iteración completada** (asumiendo tests verdes y `/speckit-analyze` sin issues). Las iteraciones siguientes asumen el código de las previas en `main`.

---

## 2. Mapa de iteraciones

| # | Título | Depende de | Hito |
|---|---|---|---|
| 1 | Bootstrap del repo y CLI vacío | — | M0 |
| 2 | Modelo de Manifest | 1 | M0 |
| 3 | Arquitectura de Integration | 1, 2 | M0 |
| 4 | Comando `bookwright init` | 1, 2, 3 | M0 |
| 5 | Modelo de dominio GOLEM | 1 | M1 |
| 6 | Indexer y comandos de grafo | 5 | M1 |
| 7 | Templates de bible, outline y constitution | 4 | M2 |
| 8 | Redacción de los 10 commands source | 7 | M2 |
| 9 | Materialización de commands a Agent Skills | 3, 8 | M2 |
| 10 | Consolidación de envelopes de error | 2, 5, 6 | M3 |
| 11 | Sistema de validación | 6, 9, 10 | M3 |
| 12 | Fixtures, tests E2E y documentación | 1-11 | M3 |
| 13 | Modelo de procedencia: Fuente / Hallazgo / Ancla | 5, 6 | M4 |
| 14 | Skill `bookwright-research` + `bible/research/` | 7, 8, 9, 13 | M4 |
| 15 | Validator `factual_anchor` | 11, 13 | M4 |
| 16 | Skill `bookwright-verify` | 13, 14 | M4 |
| 17 | Fixture histórica, E2E de investigación y docs | 13-16 | M4 |
| 18 | Saneamiento de tags de trazabilidad prohibidos | — | Mantenimiento |

Las iteraciones 1–12 conforman v0.1.0 (hitos M0–M3) y ya están completadas. Las
iteraciones **13–17 son el hito M4 — Investigación y verificación**, que se
libera como **v0.2.0** (ver `bookwright-design.md` § 20 y § 15.5). Roadmap post-M4:
v0.3 búsqueda vectorial (ChromaDB sobre rdflib, sin Grafeo), v0.4 commands de
autoría, v1.0 export. Descartados: presets, GrafeoIndexer, multi-integración y
extension system (ver § 15.5 del diseño).

La **iteración 18 es mantenimiento transversal** (no pertenece a ningún hito de
producto): cancela la deuda de tags de trazabilidad prohibidos por
`CONTRIBUTING.md` acumulada en `src/` y `tests/`, y añade un gate que impide su
reaparición. No depende de ninguna otra iteración y conviene ejecutarla cuando no
haya ramas de feature en vuelo, para minimizar conflictos de merge.

Estimación total (1–12): 6-8 semanas a tiempo parcial, 3-4 semanas a tiempo
completo. M4 (13–17): 1-2 semanas adicionales. Cada iteración entre medio día y
dos días de trabajo del agente más revisión humana.

---

## 3. Iteraciones detalladas

### Iteración 1 — Bootstrap del repo y CLI vacío

**Objetivo:** dejar el repo listo para que cualquier iteración futura pueda añadir código en condiciones (tooling, CI, estructura). Sin lógica de dominio todavía.

**Prompt:**

```
/speckit-specify

Necesidad: Bookwright es un proyecto Python que aún no existe como código. Necesitamos el bootstrap inicial del repositorio para que cualquier desarrollo posterior tenga un entorno consistente, automatizado y verificable.

Comportamiento esperado:

- Un desarrollador clona el repo y con `uv sync` tiene un entorno funcional en segundos.
- El comando `bookwright` está disponible como entry point del paquete, aunque por ahora solo imprima la versión y muestre help.
- Ejecutar `bookwright version` devuelve la versión del paquete y la versión congelada del schema GOLEM (que aún no existe en el repo; mostrar "unknown" si no hay schema).
- Ejecutar `bookwright check` valida que el entorno cumple los requisitos (Python ≥ 3.11, dependencias instaladas) y devuelve resultado.
- Al hacer commit, pre-commit hooks corren automáticamente (ruff format + check, validación de TOML, validación de YAML).
- En cada push o PR, CI corre tests, lint y type-check; falla si algo no pasa.
- Los tests existen aunque sean mínimos (smoke test: importar el paquete, ejecutar `bookwright version`).

Calidad y restricciones:

- Cobertura inicial no necesita ser alta, pero el harness debe estar listo.
- mypy strict desde el día uno (disallow_untyped_defs, disallow_any_generics, warn_return_any).
- ruff con rulesets E, W, F, I, B, UP, RUF, SIM, PL; line-length 100.
- Sin lógica de dominio: ni manifest, ni golem, ni indexer, ni integrations todavía. Solo el esqueleto.

Referencia: ver bookwright-design.md secciones 6 (estructura del repo), 14 (stack tecnológico) y 15.1 (hito M0).
```

**Pista para `/speckit-plan`:** *"Sigue § 6 (árbol del repo) y § 14 (stack) de bookwright-design.md. Crea solo los archivos imprescindibles para el bootstrap: pyproject.toml, src/bookwright/__init__.py con `__version__`, src/bookwright/cli.py con un Typer app que registra `version` y `check`, tests/conftest.py + un test smoke, .github/workflows/tests.yml, .pre-commit-config.yaml, .gitignore, LICENSE Apache-2.0. NO crear todavía los directorios core/, golem/, integrations/, indexers/, validation/."*

**Criterio de aceptación:** `uv sync && uv run bookwright version` muestra la versión. `uv run pytest` pasa. `uv run pre-commit run --all-files` pasa. CI verde.

---

### Iteración 2 — Modelo de Manifest

**Objetivo:** poder leer, validar y escribir el `manifest.toml` que es el contrato entre el CLI y los proyectos Bookwright.

**Prompt:**

```
/speckit-specify

Necesidad: cada proyecto Bookwright declara su configuración en un manifest.toml en la raíz. El CLI necesita un modelo robusto para leer, validar y escribir ese archivo, con compatibilidad hacia adelante (manifest_version) y validación estricta de campos obligatorios.

Comportamiento esperado:

- El CLI puede cargar un manifest.toml de un proyecto y obtener un objeto Python tipado con todos los campos accesibles.
- Si el manifest tiene campos obligatorios faltantes o valores inválidos, la carga falla con mensajes claros que indican exactamente qué campo está mal y por qué.
- El CLI puede generar un manifest.toml nuevo a partir de inputs mínimos (título, autor, integración) rellenando defaults sensatos.
- Si el manifest declara cli_version_min mayor que la versión instalada del CLI, la carga falla con mensaje explicativo.
- El bloque [integration] del manifest registra qué integración se usó y qué skills_dir resultó (informativo, no se interpreta para resolver paths).
- Si manifest_version es de una versión futura desconocida, el CLI emite warning pero intenta cargar best-effort.

Validaciones específicas:

- title no vacío.
- type en el enum {novel, essay, memoir, non-fiction-narrative, other}.
- language en ISO 639-1 (validación contra lista cerrada).
- authors es lista no vacía.
- uri_base es una URI válida y termina en "/".
- vocabularies.active solo referencia vocabularios existentes en .bookwright/vocabularies/ (validación diferida al runtime, no en el modelo Pydantic).
- status en el enum {idea, structuring, drafting, revising, done}.

Fuera de scope:

- Lógica de generación del manifest a partir de input. Ese código vive en el comando init (iteración 4). Aquí solo modelo + parser + validador + writer.
- Validación de vocabularios contra archivos en disco; eso se hace en el comando que lo necesite.

Referencia: ver bookwright-design.md § 8 para la spec completa del manifest.toml.
```

**Pista para `/speckit-plan`:** *"Implementa `src/bookwright/core/manifest.py` con Pydantic v2 BaseModel. Usa tomlkit para preservar formato y comentarios al escribir. Tests unitarios exhaustivos para validación de cada campo, incluyendo casos negativos. NO usar tomli/tomli_w; usar tomlkit consistentemente."*

**Criterio de aceptación:** `Manifest.load(path)` y `Manifest.dump(path)` funcionan en ambos sentidos sin pérdida de información. Tests cubren al menos 90% del módulo.

---

### Iteración 3 — Arquitectura de Integration

**Objetivo:** crear la base plugin-based para integraciones IA, con las dos implementaciones concretas de v0 (claude y generic).

**Prompt:**

```
/speckit-specify

Necesidad: Bookwright debe poder materializar artefactos (Agent Skills) para distintos agentes IA sin que el código del CLI se acople a un agente específico. El usuario elige el agente al inicializar el proyecto y la integración correspondiente decide dónde y cómo escribir los archivos.

Comportamiento esperado:

- Existe un registro central de integraciones disponibles que el CLI puede consultar por clave (ej. "claude", "generic").
- Cada integración declara sus metadatos (nombre, install_url, si requiere CLI instalado), su directorio de skills por defecto (.claude/skills/ para claude, .agents/skills/ para generic) y qué capacidades del estándar Agent Skills aprovecha (dynamic context injection, subagents, tool restrictions).
- Cada integración puede declarar opciones que se pasan vía `--integration-options`. Por ejemplo, generic acepta `--skills-dir <ruta>` para customizar el directorio destino.
- El método setup() de una integración recibe el project_root, el manifest cargado y las opciones parseadas, y materializa los artefactos necesarios. En esta iteración el setup puede estar parcialmente stub: solo crea el directorio destino y deja un placeholder, la materialización real de SKILL.md llega en iteración 9.
- Añadir una integración nueva (post-v0: copilot, codex, cursor) consiste en crear un nuevo subpaquete y registrarlo en _register_builtins(). No requiere modificar código existente.

Restricciones:

- Solo SkillsIntegration como clase base operativa en v0. NO implementar MarkdownIntegration (decisión axiomática, ver bookwright-design.md § 16.7).
- Skills generados deben cumplir agentskills.io: nombre del directorio = name del frontmatter, name < 64 chars, description < 1024 chars.
- ClaudeIntegration declara supports_dynamic_context=True, supports_subagents=True, supports_tool_restrictions=True.
- GenericIntegration declara las tres como False (estándar puro sin extensiones).

Casos límite:

- Si el usuario pasa `--integration <clave-inexistente>`, el CLI falla con error claro listando integraciones disponibles.
- Si el usuario pasa `--integration-options` con flags que no declara el plugin, el CLI falla con error listando opciones válidas para esa integración.

Referencia: ver bookwright-design.md § 11 (Sistema de Integration) para la spec completa, incluido el código Python concreto de las dos integraciones.
```

**Pista para `/speckit-plan`:** *"Implementa exactamente la estructura de § 11 de bookwright-design.md. La materialización de SKILL.md en setup() puede ser stub en esta iteración (solo crear el directorio); la lógica real llegará en iteración 9. Tests unitarios para el registry y para resolve_skills_dir() de cada integración con varios parsed_options."*

**Criterio de aceptación:** `INTEGRATION_REGISTRY["claude"]` y `["generic"]` devuelven las clases correctas. `ClaudeIntegration().resolve_skills_dir() == Path(".claude/skills")`. `GenericIntegration().resolve_skills_dir({"skills_dir": ".cursor/skills"}) == Path(".cursor/skills")`. Parser de `--integration-options` testeado.

---

### Iteración 4 — Comando `bookwright init`

**Objetivo:** primera funcionalidad visible al usuario. `bookwright init` crea un proyecto Bookwright completo y consistente.

**Prompt:**

```
/speckit-specify

Necesidad: el usuario quiere empezar un nuevo libro. Necesita un comando que en un solo paso cree el directorio del proyecto, escriba el manifest, copie todos los templates de la bible y outline, instale la integración del agente IA elegido, e inicialice git con un commit limpio.

Comportamiento esperado:

- `bookwright init mi-libro` crea el directorio mi-libro/ con la estructura completa descrita en § 7 de bookwright-design.md, configura la integración Claude por defecto, e inicializa git.
- `bookwright init --here` hace lo mismo en el directorio actual, sin crear uno nuevo. Si el directorio ya tiene archivos, pide confirmación a menos que se pase --force.
- `bookwright init mi-libro --integration generic` configura la integración Generic con skills_dir .agents/skills/ por defecto.
- `bookwright init mi-libro --integration generic --integration-options="--skills-dir .cursor/skills"` respeta el override del directorio.
- `bookwright init mi-libro --no-git` salta la inicialización de git.
- El manifest generado tiene todos los campos obligatorios rellenos con defaults sensatos (autor desde $USER o git config, type=novel, language detectado o "es" por defecto, status=idea, integración configurada).
- Tras init, `git log` muestra un único commit "Initial commit from bookwright init" con todos los archivos en stage.
- Si se pasa `--ai claude` (flag deprecado), el comando funciona pero emite warning sugiriendo --integration.
- Si se pasa `--ai-skills` o `--ai-commands-dir` (flags ya no aceptados), el comando falla con error explicativo apuntando al equivalente actual.

Estructura escrita:

- manifest.toml, README.md, .gitignore en raíz.
- manuscript/ vacío (placeholder con .gitkeep).
- bible/ con constitution.md (template completo, no rellenado), characters/ vacío, settings/ vacío, timeline.md, etc.
- outline/ con estructura vacía.
- .bookwright/ con init-options.json, schema/, vocabularies/ (propp.ttl, greimas.ttl como mínimo), templates/, scripts/, cache/ (gitignored).
- La integración configurada escribe en .claude/skills/ o .agents/skills/ (placeholder en esta iteración, materialización real en iter 9).

Casos límite:

- Si el directorio destino ya existe y no es vacío, sin --force ni --here: error.
- Si el directorio existe pero está vacío: proceder.
- Si --here y ya hay un .bookwright/: error (proyecto ya inicializado).
- Si no se detecta git instalado y no se pasó --no-git: warning y continúa sin git.

Referencia: ver bookwright-design.md § 5.2 (flags) y § 7 (estructura del proyecto generado).
```

**Pista para `/speckit-plan`:** *"Implementa `src/bookwright/commands/init.py`. Usa `importlib.resources.files()` para leer templates de src/bookwright/resources/. Para esta iteración los templates de bible pueden ser placeholders mínimos (versión completa en iter 7). El commit inicial de git se hace con subprocess; no usar GitPython como dependencia. Tests E2E con tmp_path fixtures que verifiquen la estructura completa generada en varios escenarios."*

**Criterio de aceptación:** ejecutar `bookwright init demo --integration claude` produce un proyecto que pasa todos los checks de § 15.1 del documento de diseño.

---

### Iteración 5 — Modelo de dominio GOLEM

**Objetivo:** representar las clases y relaciones de la ontología GOLEM en código Python, con generación correcta de URIs y namespaces.

**Prompt:**

```
/speckit-specify

Necesidad: Bookwright necesita representar el modelo de dominio narrativo (personajes, eventos, settings, relaciones, etc.) como objetos Python tipados que sepan cómo serializarse a RDF/Turtle según la ontología GOLEM.

Comportamiento esperado:

- Existen clases Python para cada concepto principal de los seis módulos de GOLEM (Character, Object, Event, PsychologicalState, Setting, NarrativeLocation, SocialRelationship, RelationshipRole, NarrativeUnit, NarrativeFunction, NarrativeRole, NarrativeSequence, AttributeAssignment para inference).
- Cada instancia tiene una URI estable generada a partir del namespace base del proyecto (declarado en manifest.toml > uri_base) y un slug derivado del nombre canónico.
- Las URIs siguen los patrones del § 4.5 del doc de diseño: character/{slug}, event/{slug}, location/{slug}, assertion/{uuid7}.
- Los slugs se generan con python-slugify; se preserva mayúsculas/diacríticos solo donde aporta (acentos en nombres propios sí, espacios siempre a guión).
- Cada clase puede serializarse a triples RDF compatibles con el TTL de GOLEM congelado en .bookwright/schema/golem-1.0/golem.ttl.
- El namespace base GOLEM (golem:) y los prefijos comunes (rdf:, rdfs:, crm:, dolce:, dul:) están registrados en un módulo de namespaces.
- Cada AttributeAssignment (inference module) registra: la afirmación (qué atributo a qué entidad), la fuente (P16_used_specific_object con un path tipo "bible/characters/aparici.md" o "manuscript/cap-04.md:42"), y opcionalmente la aserción premisa.

Fuera de scope:

- Lectura del manuscrito o de la bible para construir instancias. Eso es trabajo del indexer (iteración 6).
- Validación de coherencia semántica entre instancias. Eso es trabajo de los validators (iteración 10).
- Solo definir el modelo de dominio y la capacidad de serializarse a triples.

Restricciones:

- El TTL de GOLEM debe descargarse del repo upstream (github.com/GOLEM-lab/golem-ontology) y congelarse en src/bookwright/resources/schemas/golem-1.0/. Incluir version.json con el commit SHA del upstream.
- URIs son inmutables una vez generadas; cambiar el nombre canónico de un personaje genera una nueva URI (problema de migración futuro, no resolver en v0).
- UUIDs para aserciones son UUIDv7 (orden temporal sin colisiones).

Referencia: ver bookwright-design.md § 4 (Modelo de dominio: GOLEM) completo.
```

**Pista para `/speckit-plan`:** *"Crea src/bookwright/golem/ con submódulos modules/character.py, modules/relationship.py, modules/event.py, modules/setting.py, modules/narrative.py, modules/inference.py. Cada uno con dataclasses o Pydantic models. namespaces.py centraliza prefijos. base.py contiene la clase base con .uri y .to_triples(). Tests unitarios para URI generation, generación de triples, y serialización round-trip a Turtle."*

**Criterio de aceptación:** un Character con nombre "Manuel de Aparici" y uri_base "https://kola-coca.bookwright.dev/" produce URI "https://kola-coca.bookwright.dev/character/manuel-de-aparici". Tests pasan con coverage > 85%.

---

### Iteración 6 — Indexer y comandos de grafo

**Objetivo:** poder construir el grafo desde la bible y manuscrito, y consultarlo con SPARQL.

**Prompt:**

````
/speckit-specify

Necesidad: el grafo de un proyecto Bookwright es la representación consultable de su contenido narrativo. Necesitamos poder construirlo desde los archivos markdown de la bible y manuscrito, y consultarlo desde el CLI o desde los commands.

Comportamiento esperado:

- `bookwright graph build` lee los archivos de bible/ y manuscript/ del proyecto actual, extrae instancias del modelo GOLEM y genera bible/graph.ttl con todos los triples.
- `bookwright graph build --force` reconstruye desde cero ignorando caché.
- `bookwright graph query "<SPARQL>"` ejecuta una query SPARQL sobre el grafo construido y devuelve resultados. Soporta --json para output parseable.
- El indexer está detrás de un Protocol (interfaz abstracta); la implementación usa rdflib, el motor permanente. El Protocol mantiene la puerta abierta a añadir capacidades (p. ej. la capa de búsqueda vectorial de v0.3) sin tocar este código. GrafeoIndexer queda descartado.
- El motor a usar se lee de manifest.toml > [bookwright] indexer (default: "rdflib").
- El parser de bible markdown identifica personajes por archivos .md en bible/characters/, settings por bible/settings/*.md, etc. La estructura mínima del frontmatter de cada archivo determina qué triples se generan.
- Cada triple generado lleva su correspondiente AttributeAssignment apuntando al archivo de origen y a la línea cuando aplique.

Formato de frontmatter de un personaje (ejemplo):

```yaml
---
name: "Manuel de Aparici"
born: 1828
died: 1900
features:
  - "ingeniero químico"
  - "miembro fundador de Destilerías Ayelo"
narrative_roles:
  - protagonist
---
```

El parser convierte ese frontmatter en los triples correspondientes según el módulo Character de GOLEM.

Casos límite:

- Si bible/ o manuscript/ no existen, fallar con error claro.
- Si un archivo tiene frontmatter inválido, listar el archivo y la razón pero seguir con los demás. Reportar al final.
- Si dos personajes generan la misma URI por slug colisión, fallar con error explícito.

Fuera de scope:

- Validators y consistency checks (iteración 10).
- Mutación del grafo desde la línea de comandos (write-back). Solo lectura/build.

Referencia: ver bookwright-design.md § 12 (Sistema de Indexers) y § 5.1 (comandos del CLI).
````

**Pista para `/speckit-plan`:** *"Crea src/bookwright/indexers/base.py con el Protocol Indexer, y rdflib_indexer.py con la implementación. src/bookwright/io/turtle.py para serialización. src/bookwright/io/bible.py y io/manuscript.py para parsing de markdown con frontmatter (usar python-frontmatter o parsear YAML manual). src/bookwright/commands/graph.py con subcomandos build y query. Tests con fixture tiny-novel/ minimal."*

**Criterio de aceptación:** sobre una fixture con 3 personajes, 2 settings y 5 eventos en markdown, `bookwright graph build` produce un graph.ttl con todos los triples esperados. `bookwright graph query "SELECT ?c WHERE { ?c a golem:G1_Character }" --json` devuelve los 3 personajes.

---

### Iteración 7 — Templates de bible, outline y constitution

**Objetivo:** redactar todos los templates markdown que `bookwright init` copiará al proyecto. El trabajo es de redacción de plantillas, no de código.

**Prompt:**

```
/speckit-specify

Necesidad: cada proyecto Bookwright nace con un conjunto de templates en bible/, outline/ y como constitution.md que guían al autor y al agente IA sobre qué información rellenar y en qué formato. Estos templates son la pieza intelectual más visible para el usuario final.

Comportamiento esperado:

- bible/constitution.md.tmpl es un template Markdown con secciones para voz narrativa, registro, pacto con el lector, pacto histórico-ficcional, líneas rojas, invariantes de coherencia y vocabularios activos. Cada sección tiene placeholders [PENDIENTE: <pregunta>] que el agente IA debe rellenar usando un input narrativo.
- bible/character.md.tmpl es un template para una ficha de personaje: nombre, age, biographical features, psychological features, physical features, narrative role, sample dialogue, body language patterns.
- bible/setting.md.tmpl para el universo narrativo en general (cultura, sistema, época, geografía amplia).
- bible/location.md.tmpl para una localización concreta con anclas sensoriales (qué se ve, qué se oye, qué se huele, qué se toca, qué atmósfera predomina).
- bible/timeline.md.tmpl con una estructura cronológica de eventos del relato.
- bible/relationship.md.tmpl para una relación entre dos o más personajes (tipo, evolución, eventos clave).
- bible/pov-structure.md.tmpl para novelas multi-POV (modo, schedule, voice differentiation, information asymmetry map).
- bible/themes.md.tmpl con motif registry, symbol tracker, chapter thematic map.
- bible/glossary.md.tmpl con invented terms, capitalization rules, consistency log.
- bible/research.md.tmpl con open questions, source notes, resolved findings.
- bible/subplots.md.tmpl con beat sheets de subtramas y puntos de intersección con la trama principal.
- outline/arcs.md.tmpl, outline/structure.md.tmpl, outline/synopsis.md.tmpl, outline/scenes.md.tmpl.
- manuscript/chapter.md.tmpl con la estructura de un capítulo.
- manifest.toml.tmpl con todos los campos comentados.
- readme.md.tmpl con una breve guía para humanos (cómo trabajar con bookwright y este proyecto).
- gitignore.tmpl apropiado.

Cada template:

- Tiene frontmatter YAML mínimo cuando aplica (para que el parser del indexer pueda leerlo).
- Tiene comentarios HTML <!-- --> con instrucciones para el agente IA o el autor humano.
- Es legible directamente por un humano sin renderizar (Markdown plano).

Fuente de inspiración:

- El preset fiction-book-writing (adaumann/speckit-preset-fiction-book-writing v1.7) tiene un inventario excelente de tipos de documento. Sus templates están bajo MIT y se pueden estudiar para estructura, pero la redacción debe ser propia para Bookwright (Apache-2.0) y adaptada a nuestro modelo GOLEM. Acreditar la inspiración en CHANGELOG.

Fuera de scope:

- La lógica del comando init que los copia (ya implementada en iter 4).
- El parser que los lee (ya implementado en iter 6).
- Solo trabajo de redacción de los .tmpl en src/bookwright/resources/templates/.

Referencia: ver bookwright-design.md § 9 (constitution), § 6 (estructura de templates en el repo), § 17.2 (análisis del preset y qué se aprende de él).
```

**Pista para `/speckit-plan`:** *"Esta iteración es 90% redacción. Trata cada .tmpl como un artefacto literario-técnico. Para cada uno, primero revisar el equivalente del preset fiction-book-writing (carpeta fiction-book-writing/templates/ del repo de adaumann) para entender qué cubre, y luego adaptar/reescribir para Bookwright con frontmatter que case con el modelo GOLEM de iter 5. Validación: cada template debe poder ser leído por el parser de iter 6 sin errores (test de smoke). Coverage no aplica aquí; los tests son de validación de formato y completitud."*

**Criterio de aceptación:** todos los templates existen en src/bookwright/resources/templates/. Tests automatizados validan que cada .tmpl con frontmatter es parseable y que el contenido es no-vacío y no contiene placeholders fundamentales sin reemplazar (ej. `{{TODO}}`).

---

### Iteración 8 — Redacción de los 10 commands source

**Objetivo:** redactar los 10 archivos .md de `src/bookwright/resources/commands/` que serán materializados como Agent Skills.

**Prompt:**

```
/speckit-specify

Necesidad: cada uno de los 10 commands de Bookwright (constitution, bible, outline, scenes, draft, synopsis, clarify, analyze, continuity, checklist) es un prompt estructurado que el agente IA ejecuta cuando el usuario lo invoca. Son la interfaz creativa principal y deben estar redactados con cuidado.

Comportamiento esperado de cada command:

Para cada uno, existe un archivo .md en src/bookwright/resources/commands/ con:

- YAML frontmatter con: description (claro y con triggers explícitos para activación implícita; < 1024 chars). Sin bloque scripts: las invocaciones al CLI bookwright se escriben inline en el cuerpo (ej. `bookwright graph build --json`).
- Cuerpo Markdown con: contexto/rol del agente, input esperado, procedimiento paso a paso, output esperado, qué archivos del proyecto leer, qué archivos escribir, qué hacer si hay información faltante (marcar [PENDIENTE] vs preguntar), qué cosa NO hacer.

Los 10 commands:

1. bookwright-constitution: destila la constitution narrativa desde un brief o conversación previa. Input: dump de texto del usuario. Output: bible/constitution.md rellenado a partir del template.

2. bookwright-bible: dada la constitution y el brief, genera la bible completa (personajes, settings, locations, timeline, relationships, themes, glossary, research, subplots, pov-structure si aplica). Output: bible/* archivos completos.

3. bookwright-outline: dado constitution + bible, genera arcs, structure y un synopsis inicial. Output: outline/*.md.

4. bookwright-scenes: dado outline + bible, desglosa en una lista de escenas concretas con función narrativa, personajes presentes, localización, beats. Output: outline/scenes.md.

5. bookwright-draft <scene_id>: dado outline + bible + scene, escribe el borrador de una escena/capítulo concreto respetando voz, focalización y constraints. Output: manuscript/cap-NN.md (o sección de él).

6. bookwright-synopsis: actualiza outline/synopsis.md con versión corta (250-350 palabras) y larga (1000-2000 palabras) basadas en el estado actual del proyecto.

7. bookwright-clarify: detecta ambigüedades en cualquier artefacto del proyecto y devuelve una lista de preguntas que el autor debe responder antes de seguir.

8. bookwright-analyze: análisis cross-artifact pre-draft. Detecta inconsistencias entre constitution, bible, outline, scenes. Output: reporte en stdout.

9. bookwright-continuity: análisis post-draft. Verifica bible compliance, character arc consistency, timeline coherence en el manuscrito. Usa el grafo construido vía bookwright graph build. Output: reporte en stdout.

10. bookwright-checklist <artifact>: dado un artefacto concreto, valida que esté completo (todas las secciones, sin placeholders sin rellenar, etc.). Output: reporte en stdout.

Calidad esperada de los prompts:

- Cada description debe activarse correctamente en contexto narrativo apropiado. Hacer A/B mental: si un agente lee un prompt de usuario que dice "ayúdame a definir el tono de mi libro", ¿se activa bookwright-constitution? Sí. ¿Se activa bookwright-bible? Probablemente no (es prematuro). Las descriptions deben capturar estas distinciones.
- Los prompts son didácticos pero concisos. No exceder 5000 tokens en el cuerpo (constraint del estándar agentskills.io tier 2).
- Cuando un command necesita contexto extenso (ej. explicación del modelo GOLEM o del vocabulario de Propp), referencia archivos en references/ del skill (tier 3 progressive disclosure) en lugar de inflar el cuerpo.

Fuera de scope:

- La materialización de estos .md a SKILL.md (iteración 9).
- Los scripts auxiliares Python que invocan (también iteración 9).
- Solo redacción de los 10 commands source.

Referencia: ver bookwright-design.md § 10 (Sistema de Commands) completo, incluido el ejemplo anotado de bookwright-constitution.md en § 10.1.
```

**Pista para `/speckit-plan`:** *"Esta iteración es redacción de prompts. Para cada command, partir del ejemplo de § 10.1 del doc de diseño y adaptar. Crear también src/bookwright/resources/commands/references/ con los archivos auxiliares (golem-character.md, propp-functions.md, etc.) que los commands referencien. Tests: validar que cada .md tiene frontmatter válido, description < 1024 chars, cuerpo no-vacío y < 5000 tokens (medir aproximadamente con tiktoken si está disponible, o por carácter)."*

**Criterio de aceptación:** los 10 archivos existen, todos pasan validación de formato. Una lectura manual del prompt de bookwright-constitution muestra que sería ejecutable por Claude Code sin ambigüedades.

---

### Iteración 9 — Materialización de commands a Agent Skills

**Objetivo:** completar el setup() de las integraciones para que generen SKILL.md válidos a partir de los commands source, e implementar los scripts auxiliares Python que los commands invocan.

**Prompt:**

```
/speckit-specify

Necesidad: cuando el usuario ejecuta `bookwright init`, las integraciones deben transformar los commands source en Agent Skills válidos en el directorio destino. Cada SKILL.md generado debe cumplir el estándar agentskills.io y, si la integración soporta capacidades extendidas (como Claude Code), aprovecharlas.

Comportamiento esperado:

- ClaudeIntegration.setup() y GenericIntegration.setup() ahora hacen la materialización real (en iter 3 era stub).
- Para cada .md en resources/commands/, se genera un directorio <skills_dir>/<command-name>/ con SKILL.md dentro. Ej: .claude/skills/bookwright-constitution/SKILL.md.
- El frontmatter del SKILL.md incluye: name (idéntico al directorio padre), description (la del command enriquecida con triggers desde SKILL_DESCRIPTIONS dict), license (heredado de bookwright-design o Apache-2.0), metadata.author = "bookwright", metadata.version = versión del CLI.
- El cuerpo del SKILL.md sustituye {ARGS} → "$ARGUMENTS" para todas las integraciones de v0 (convención mayoritaria). Las llamadas al CLI bookwright se escriben inline (ej. `bookwright graph build --json`); no hay token {SCRIPT}.
- Si el command source referencia archivos en references/ (ej. references/golem-character.md), esos archivos se copian al subdirectorio references/ del skill: .claude/skills/bookwright-constitution/references/golem-character.md.
- ClaudeIntegration, si supports_dynamic_context=True, puede usar la sintaxis !`shell` en el SKILL.md para inyección de contexto dinámico. Ej: un command puede incluir `!`cat bible/constitution.md`` para que Claude Code lea el contenido al ejecutar el skill. GenericIntegration NO usa esta sintaxis (no es del estándar).
- La operación es idempotente: si <skills_dir>/<command>/SKILL.md ya existe, NO se sobrescribe. Esto preserva customizaciones del usuario.
- No hay scripts auxiliares en .bookwright/scripts/. Los SKILL.md llaman al CLI `bookwright` directamente (subcomandos como `graph build`, `graph query`, `validate`, todos con --json para output parseable).

Validaciones automatizadas:

- Cada SKILL.md generado debe pasar un linter que valide la spec agentskills.io (nombre matchea directorio, description < 1024 chars, cuerpo < 5000 tokens aproximados, frontmatter YAML válido).
- Para ClaudeIntegration con extensiones, validar que dynamic context (sintaxis !`shell`) solo se usa para inyectar contenido de archivos del proyecto (ej. `!`cat bible/constitution.md``) o invocar el CLI bookwright; nunca apunta a wrappers Python inexistentes.

Fuera de scope:

- Implementar nuevos validators (eso es iter 10).
- Solo la materialización de los SKILL.md.

Referencia: ver bookwright-design.md § 11.4 (Generación de SKILL.md desde commands) y § 11.5 (progressive disclosure).
```

**Pista para `/speckit-plan`:** *"Reescribe los setup() de ClaudeIntegration y GenericIntegration. Crea src/bookwright/integrations/base.py::generate_skill_md(command_path, target_dir, integration) como helper compartido. SKILL_DESCRIPTIONS dict vive en base.py. Para tokens (solo {ARGS}), usa string.Template o re. Los SKILL.md generados llaman al CLI bookwright directamente (ej. `bookwright graph build --json`); no hay wrappers Python en .bookwright/scripts/. Tests E2E: ejecutar init en tmp_path, validar que los SKILL.md generados pasan un linter ad-hoc."*

**Criterio de aceptación:** tras `bookwright init demo --integration claude`, el directorio demo/.claude/skills/ contiene los 10 subdirectorios con SKILL.md válidos. Validar uno cargándolo en Claude Code real (manual smoke test). `bookwright init demo --integration generic --integration-options="--skills-dir .cursor/skills"` produce skills equivalentes en demo/.cursor/skills/ sin sintaxis Claude-específica.

---

### Iteración 10 — Consolidación de envelopes de error

**Objetivo:** unificar las cuatro jerarquías de excepción que hoy duplican `to_json()` (core, golem, io, indexers) en una base compartida, **antes** de que el sistema de validación añada una quinta forma de salida estructurada (`Violation`). Refactor de comportamiento preservado; no añade funcionalidad de usuario.

**Motivación:** auditoría de calidad de la iteración 6 (finding **R4**, `specs/006-graph-indexer/review.md`). Cada módulo de errores reimplementa a mano el sobre `{"status":"error","code":...,"message":...,"details":{...}}`. Con cuatro copias, cualquier cambio en el contrato de error es shotgun surgery; la iteración 11 (validación) introduciría una quinta (`Violation`). Consolidar aquí evita esa deuda y deja una base de la que `Violation` puede heredar.

**Prompt:**

```
/speckit-specify

Necesidad: Bookwright tiene cuatro jerarquías de excepción independientes (core, golem, io, indexers) que reimplementan el mismo método to_json() produciendo el sobre de error JSON-sobre-stdout (Principio IX). La duplicación obliga a replicar cualquier cambio del contrato de error en N sitios, y el sistema de validación de la siguiente iteración añadiría una jerarquía más. Necesitamos una base de error compartida que centralice la forma del sobre, preservando el comportamiento observable byte-a-byte.

Comportamiento esperado:

- Existe una clase base (BookwrightError) de la que heredan todas las excepciones que se serializan a JSON. Declara code (a nivel de clase), message (de instancia) y details opcional, y un único to_json() que construye {"status":"error","code":...,"message":...} y añade "details" solo cuando hay detalles.
- Cada subclase concreta (ProjectNotFoundError, MissingDirectoryError, SlugCollisionError, InvalidFrontmatterError, UnknownIndexerError, GraphNotBuiltError, GraphLoadError, InvalidQueryError, ManifestError, EmptySlugError, etc.) declara su code y rellena message/details; ya no reimplementa to_json().
- El JSON emitido por cada error es idéntico al actual (mismas claves, misma forma de details). Los tests existentes de forma de error siguen pasando sin cambios de aserción.
- Los códigos de error (code) y los exit codes de cada comando no cambian.

Restricciones:

- Refactor de comportamiento preservado: ningún cambio en mensajes, codes, exit codes ni en la forma del JSON. Es reorganización interna, no rediseño del contrato.
- Mantener la independencia de capas: el módulo base no debe importar de core/golem/io/indexers (solo al revés). Sin ciclos de import.
- No tocar el contrato JSON-sobre-stdout (Principio IX).

Fuera de scope:

- Cambiar códigos o mensajes de error existentes.
- Añadir nuevos tipos de error (el Violation de validación llega en la iteración siguiente y heredará de esta base).
- Cualquier cambio funcional en los comandos.

Referencia: ver el finding R4 de specs/006-graph-indexer/review.md y data-model § 6 (forma del sobre de error).
```

**Pista para `/speckit-plan`:** *"Crea una base `BookwrightError(Exception)` con `code: ClassVar[str]`, `message: str`, `details: dict | None` y un único `to_json()`. Colócala donde no genere ciclos (un módulo raíz `src/bookwright/errors.py` es lo más seguro; core/golem/io/indexers importan de él, no al revés). Migra las jerarquías de core/errors.py, golem/errors.py, io/errors.py e indexers/errors.py a heredar de ella, borrando los `to_json()` duplicados. Apóyate en los tests de forma de error existentes como red de seguridad — no deben requerir cambios de aserción."*

**Criterio de aceptación:** ningún módulo de errores reimplementa `to_json()`; todos heredan de `BookwrightError`. La suite completa pasa sin modificar las aserciones de los tests de forma de error. `mypy --strict` y `ruff` verdes. La cobertura no baja respecto a la iteración previa.

---

### Iteración 11 — Sistema de validación

**Objetivo:** detectar inconsistencias automáticamente con validators ejecutables, complementando a los chequeos LLM.

**Prompt:**

```
/speckit-specify

Necesidad: la calidad de un libro depende de la coherencia interna. Bookwright debe poder detectar automáticamente inconsistencias temporales, presencia de personajes, continuidad de settings y respeto a la focalización declarada. Los validators son código Python que opera sobre el grafo y son deterministas (a diferencia de los chequeos LLM).

Comportamiento esperado:

- Existe un Validator Protocol con un método validate(project, indexer) -> list[Violation]. Cada Violation tiene severity, message, source (archivo y línea cuando aplique) y triples implicados.
- Existe un registry que autodescubre validators. Los built-in viven en src/bookwright/validation/. Validators custom del usuario en <proyecto>/.bookwright/validators/*.py se cargan dinámicamente.
- `bookwright validate` ejecuta todos los validators habilitados (según manifest.toml > [validators]) y reporta resultados. Soporta --json, --scope <archivo|directorio> para limitar el alcance, y --severity error|warning|info para filtrar.
- Los 4 validators built-in de v0:
  - temporal: detecta inconsistencias en la línea temporal de eventos (ej. evento A en 1885 antes que evento B en 1884 pero el manuscrito implica B antes que A).
  - character_presence: personajes mencionados en manuscrito que no existen en bible, y viceversa.
  - setting_continuity: settings con descripciones contradictorias entre archivos (ej. capítulo 3 dice "ciudad costera", capítulo 7 dice "ciudad de interior").
  - focalization: violaciones de la persona narrativa declarada en constitution.md (ej. constitution dice "tercera limitada en Aparici", pero un párrafo accede a pensamientos de otro personaje).

- El validator temporal usa el módulo Event de GOLEM y las propiedades temporales (P4_has_time-span, follows, temporally-overlaps).
- character_presence cruza G1_Character instancias del grafo con menciones en el manuscrito (extracción simple por nombre, sin NER complejo en v0).
- setting_continuity y focalization son más heurísticos; pueden devolver warnings en lugar de errores.

Errores claros:

- Cada Violation reporta exactamente qué archivo y línea, qué regla se violó y por qué.
- En modo --json, el output es parseable para integrarse con CI o IDE.

Fuera de scope:

- Validators basados en LLM (los hay vía el command bookwright-continuity, pero los validators de código son distintos).
- Auto-fix. Los validators reportan, no arreglan.

Referencia: ver bookwright-design.md § 13 (Sistema de Validación) completo.
```

**Pista para `/speckit-plan`:** *"Crea src/bookwright/validation/base.py con el Protocol, registry.py con autodescubrimiento (entry_points o iterando módulos), y los 4 validators en archivos separados. src/bookwright/commands/validate.py con el comando. Para character_presence, usa expresiones regulares simples sobre menciones por nombre; NER queda fuera de scope. Tests: para cada validator, una fixture con violación inyectada y una sin violación; verificar detección correcta."*

**Criterio de aceptación:** sobre fixtures con violaciones conocidas, `bookwright validate --json` detecta exactamente las violaciones esperadas. Sobre la fixture limpia, devuelve 0 violations. Cobertura > 85% en src/bookwright/validation/.

---

### Iteración 12 — Fixtures, tests E2E y documentación

**Objetivo:** asegurar que todo el sistema funciona de extremo a extremo y queda documentado para usuarios y contribuidores.

**Prompt:**

```
/speckit-specify

Necesidad: Bookwright v0.1 está cerca de listo. Antes del primer release necesitamos fixtures realistas para tests E2E, un sitio de documentación navegable, y un changelog que registre qué hay en esta versión.

Comportamiento esperado:

Fixtures completas:

- tests/fixtures/tiny-novel/: una novela mínima pero coherente con 3 personajes, 2 settings, 5 eventos, 1 capítulo borrador. Toda la bible y outline rellenos. Usable para tests E2E.
- tests/fixtures/tiny-essay/: un ensayo mínimo (3 capítulos, sin personajes ficticios, con bibliografía).
- tests/fixtures/tiny-memoir/: una memoria mínima (1 protagonista = autor, escenas autobiográficas).
- Cada fixture es un proyecto Bookwright válido que se puede inicializar, validar y consultar.

Tests E2E:

- test_full_workflow.py recorre el flujo: bookwright init → editar manifest y constitution → bookwright graph build → bookwright graph query → bookwright validate. Verifica que cada paso produce el resultado esperado.
- test_skills_materialization.py verifica que los SKILL.md generados son válidos según el estándar agentskills.io.
- test_integration_swap.py verifica que tras `bookwright init --integration claude` y luego cambiar el manifest a generic + re-init (con --here --force), los skills se materializan correctamente en .agents/skills/.

Documentación:

- README.md del repo con: qué es Bookwright, instalación rápida, quickstart de 5 minutos, links a docs.
- docs/ con MkDocs (mkdocs-material). Páginas: index, getting-started, architecture (resumen del doc de diseño), commands (uno por command), validation, extending, FAQ.
- CHANGELOG.md con la versión v0.1.0 y todas las funcionalidades incluidas.
- CONTRIBUTING.md con cómo contribuir, cómo crear una integración nueva, cómo crear un validator custom, cómo crear un vocabulario.
- LICENSE Apache-2.0.

Calidad final:

- pytest pasa con cobertura > 80%.
- ruff check y format pasan.
- mypy --strict pasa.
- pre-commit pasa.
- CI verde.
- mkdocs build genera el sitio sin warnings.
- Validación manual: tras `pipx install bookwright-cli` (desde wheel local), un usuario nuevo puede ejecutar el quickstart sin tocar el código fuente y completar el flujo entero.

Fuera de scope:

- Optimizaciones de performance del indexer (eso es post-v0 si rdflib resulta lento).
- Sistema de investigación y verificación (M4 / v0.2, iteraciones 13–17).
- Vector search (v0.3).

Referencia: ver bookwright-design.md § 15.4 (M3) y § 15.5 (post-v0).
```

**Pista para `/speckit-plan`:** *"Esta iteración es polish y consolidación. Fixtures son trabajo creativo (escribir un esqueleto de novela, ensayo, memoria) — pueden ser muy cortos pero deben ser coherentes. Tests E2E usan las fixtures como input. MkDocs con tema material; la sección de architecture puede ser un resumen automático con links al doc de diseño completo (que va junto al repo). Validación manual al final con un usuario externo si es posible."*

**Criterio de aceptación:** todos los criterios listados en el prompt se cumplen. Release v0.1.0 publicado en GitHub con wheel y sdist adjuntos.

---

## 3.bis Hito M4 — Investigación y verificación (v0.2.0)

> Estas iteraciones implementan el sistema de § 20 del documento de diseño.
> Asumen v0.1.0 (iteraciones 1–12) ya en `main`. Mismo flujo Spec Kit que el
> resto. Principio rector: **Bookwright no busca; estructura, ancla y verifica.**
> La búsqueda real de fuentes la hace el agente que ejecuta el skill; el toolkit
> aporta modelo de procedencia, persistencia en texto plano, integración en el
> grafo y validación. No se añaden dependencias de runtime para acceso a red.

### Iteración 13 — Modelo de procedencia: Fuente / Hallazgo / Ancla

**Objetivo:** modelar la investigación como datos de primera clase en el grafo,
reutilizando el módulo Inference de GOLEM (`E13_Attribute_Assignment`) y el patrón
`E55_Type`, sin extender el esquema. Es el cimiento del que dependen las demás.

**Prompt:**

```
/speckit-specify

Necesidad: la investigación que sostiene un libro (fuentes oficiales, en idioma original, con su fiabilidad) debe poder representarse en el grafo del proyecto, no solo como prosa suelta. Necesitamos un modelo de procedencia con tres entidades —Fuente, Hallazgo y Ancla— que se serialicen en Turtle y se enlacen a las entidades narrativas GOLEM que constriñen.

Comportamiento esperado:

- Una Fuente registra: referencia/URL, autor, idioma original, tipo (primaria, secundaria, oficial, académica, periodística, testimonial), fiabilidad (alta/media/baja con justificación), fecha de acceso y cita textual (original + traducción si difiere del idioma del libro).
- Un Hallazgo es una afirmación sobre el mundo real sostenida por una o más Fuentes; se reifica como E13_Attribute_Assignment (qué se afirma, quién lo afirma, sobre qué entidad recae, con qué fuentes). Un Hallazgo puede quedar en estado "abierto" (pregunta sin resolver).
- Un Ancla es un Hallazgo promovido a restricción vinculante, enlazado a la entidad narrativa que constriñe (G1_Character, G12_Setting, G5_Narrative_Event o la timeline) y, opcionalmente, con un time-span para detección de anacronismos.
- Existe un vocabulario controlado sources.ttl que define los tipos de Fuente y niveles de fiabilidad vía E55_Type, más las propiedades bw: que reifican Fuente/Hallazgo/Ancla sobre E13.
- Los ficheros de investigación viven en bible/research/ (un .md por tema con front-matter estructurado, más _index.md y sources.md). io/research.py los parsea y emite las tríadas; bookwright graph build las incorpora a graph.ttl.
- Se generan URIs por composición para los segmentos source (slug), finding (UUIDv7) y anchor (UUIDv7), siguiendo la convención de § 4.5.

Fuera de scope:

- El skill que dirige la investigación (iteración 14).
- El validator factual_anchor (iteración 15) y la verificación LLM (iteración 16).
- Búsqueda vectorial sobre el corpus de fuentes (v0.3). El agente lee los Markdown directamente.
- No se crean clases GOLEM nuevas: solo E13/E55 y propiedades bw:.

Referencia: ver bookwright-design.md § 20.2, § 20.3, § 20.5, § 20.7, § 20.8 y § 4 (modelo GOLEM, módulo Inference).
```

**Pista para `/speckit-plan`:** *"Modela Fuente/Hallazgo/Ancla en `src/bookwright/golem/` reutilizando el patrón E13_Attribute_Assignment ya usado para aserciones; NO añadas clases GOLEM nuevas. Crea `resources/vocabularies/sources.ttl`. Crea `src/bookwright/io/research.py` análogo a `io/bible.py` y engánchalo en el RdflibIndexer (iteración 6). Front-matter YAML para los hallazgos/anclas, prosa Markdown debajo. Tests: fixture de `bible/research/<tema>.md` → verificar tríadas E13 emitidas, enlace a entidad, y URIs correctas."*

**Criterio de aceptación:** sobre una fixture con `bible/research/`, `bookwright graph build` emite las tríadas de Fuente/Hallazgo/Ancla y una query SPARQL recupera las anclas que constriñen a un personaje dado. Cobertura > 85% en el código nuevo.

---

### Iteración 14 — Skill `bookwright-research` + `bible/research/`

**Objetivo:** dar al autor un comando que dirija al agente por un protocolo de
investigación riguroso (fuentes oficiales/primarias, idioma original, contraste
de procedencias) y persista los resultados en `bible/research/` y el grafo.

**Prompt:**

```
/speckit-specify

Necesidad: investigar es parte del proceso de escritura. El autor necesita un command que, dado un tema (p. ej. "detectives privados en España" o "logística de la Wehrmacht en 1943"), guíe al agente para investigar con rigor y deje los hallazgos estructurados, con procedencia, anclados al grafo.

Comportamiento esperado:

- Existe un command source bookwright-research que se materializa como Agent Skill (igual que los 10 de v0.1, ver iteración 8 y 9), disponible en las integraciones claude y generic.
- El SKILL.md codifica un protocolo: (1) descomponer el tema en sub-preguntas verificables; (2) buscar fuentes autorizadas, con preferencia explícita por fuentes primarias y oficiales EN IDIOMA ORIGINAL; (3) para temas con cargas nacionales, consultar deliberadamente fuentes de varias procedencias en vez de una sola; (4) registrar cada hallazgo con procedencia completa, incluyendo cita en idioma original; (5) cuando las fuentes discrepan, registrar cada versión con su procedencia en lugar de colapsarlas; (6) marcar qué hallazgos son anclas y a qué entidad narrativa enlazan; (7) dejar abiertas las preguntas sin resolver.
- El resultado se escribe en bible/research/<tema>.md (con _index.md y sources.md actualizados), en el formato que io/research.py (iteración 13) sabe parsear.
- Se añaden templates de bible/research/ a los resources (resolubles por capas, como el resto de templates de iteración 7).
- /bookwright-bible se actualiza para crear bible/research/_index.md en vez del antiguo research.md, y /bookwright-clarify sigue pudiendo recoger las preguntas abiertas.
- Se añade el bloque [research] al manifest (enabled, source_languages, min_reliability_for_anchor) con defaults; el modelo de manifest (iteración 2) se extiende.

Fuera de scope:

- El motor de búsqueda: lo aporta el agente, no Bookwright. El skill instruye; no implementa fetch ni añade dependencias de red.
- La verificación del manuscrito contra anclas (iteración 16).
- El validator de integridad estructural (iteración 15).

Referencia: ver bookwright-design.md § 20.4, § 20.7, § 20.9, y § 10/§ 11 (formato de commands y materialización a skills).
```

**Pista para `/speckit-plan`:** *"Redacta `resources/commands/bookwright-research.md` siguiendo el formato de command source de § 10.1 y los 10 ya existentes; el procedimiento es el protocolo de 7 pasos. Reutiliza la materialización a SKILL.md de la iteración 9 (no dupliques el pipeline). Añade `resources/templates/bible/research/` (_index, sources, tema). Extiende el modelo de manifest (iteración 2) con el bloque `[research]` y sus validaciones. El skill debe triggerear en español e inglés (preferencia del usuario). Tests: el SKILL.md generado valida contra agentskills.io; el bloque [research] se carga y valida."*

**Criterio de aceptación:** `bookwright init` genera el skill bookwright-research válido en ambas integraciones; un proyecto con `[research]` carga sin error; el flujo manual (correr el skill en un agente) produce un `bible/research/<tema>.md` parseable por `graph build`. Cobertura > 85% en el código nuevo.

---

### Iteración 15 — Validator `factual_anchor`

**Objetivo:** verificación determinista de la integridad estructural de las
anclas y detección de anacronismos, integrada en `bookwright validate`.

**Prompt:**

```
/speckit-specify

Necesidad: las anclas de investigación solo sirven si están bien formadas y no chocan con la cronología. Necesitamos un validator de código (determinista, complementario a los chequeos LLM) que audite la integridad de las anclas sobre el grafo.

Comportamiento esperado:

- Un validator factual_anchor implementa el Validator Protocol de la iteración 11 (validate(project, indexer) -> list[Violation]).
- Comprueba la integridad ESTRUCTURAL, no la veracidad: que cada ancla tenga al menos una Fuente con todos los campos de procedencia obligatorios; que las entidades narrativas a las que enlaza existan en el grafo; y emite warning sobre anclas sin fuente o de fiabilidad por debajo de manifest.research.min_reliability_for_anchor.
- Cuando un ancla lleva time-span, detecta anacronismos contra la timeline reutilizando la lógica del validator temporal (iteración 11). Anacronismo duro = error; problema estructural = warning.
- Se autodescubre por el registry existente y se activa vía manifest.toml > [validators].enabled. bookwright validate lo incluye con soporte --json, --scope y --severity ya existentes.

Fuera de scope:

- Juicio semántico sobre si el manuscrito contradice un hecho (eso es bookwright-verify, iteración 16, vía LLM).
- Auto-fix. El validator reporta, no arregla.

Referencia: ver bookwright-design.md § 20.6 y § 13 (Sistema de Validación).
```

**Pista para `/speckit-plan`:** *"Crea `src/bookwright/validation/factual_anchor.py` siguiendo el patrón de los 4 validators de la iteración 11. Para anacronismos, reutiliza/extrae la comparación de time-spans del validator temporal en vez de duplicarla. Tests: fixtures con (a) ancla sin fuente → warning, (b) ancla con fiabilidad baja → warning, (c) ancla con entidad inexistente → error/warning, (d) ancla con time-span anacrónico → error, (e) fixture limpia → 0 violations."*

**Criterio de aceptación:** sobre fixtures con violaciones conocidas, `bookwright validate --json` detecta exactamente las esperadas; sobre la fixture limpia, 0 violations. Cobertura > 85% en `src/bookwright/validation/`.

---

### Iteración 16 — Skill `bookwright-verify`

**Objetivo:** verificación semántica (LLM) del manuscrito contra las anclas:
detectar pasajes que contradicen lo investigado. Es a la investigación lo que
`bookwright-continuity` es a la bible.

**Prompt:**

```
/speckit-specify

Necesidad: tras escribir el borrador, el autor necesita saber si el texto contradice lo que investigó: anacronismos, errores de procedimiento (el detective hace algo ilegal o imposible en España), inexactitudes culturales o lingüísticas. Eso exige juicio, no solo código: lo resuelve un agente leyendo el manuscrito contra las anclas.

Comportamiento esperado:

- Existe un command source bookwright-verify materializado como Agent Skill en claude y generic.
- El SKILL.md instruye al agente a cargar las anclas del grafo (vía bookwright graph query) y leer el manuscrito buscando pasajes que las contradigan; produce un reporte estructurado por capítulo/escena con cita del pasaje, ancla violada, fuente de la ancla y severidad.
- Se ejecuta en la fase post-draft (tras la fase 5, Draft), igual que bookwright-continuity.
- El reporte es legible por humanos y, donde aplique, referencia archivo y línea.

Fuera de scope:

- La integridad estructural de las anclas (iteración 15, determinista).
- Auto-corrección del manuscrito. El skill reporta; el autor decide.

Referencia: ver bookwright-design.md § 20.6 y el command bookwright-continuity como patrón análogo.
```

**Pista para `/speckit-plan`:** *"Redacta `resources/commands/bookwright-verify.md` tomando `bookwright-continuity` como plantilla estructural (mismo patrón de reporte post-draft). Reutiliza la materialización a SKILL.md de la iteración 9. El skill consume el grafo vía `bookwright graph query` (anclas) y los .md del manuscrito. Trigger bilingüe ES/EN. Tests: SKILL.md válido contra agentskills.io en ambas integraciones."*

**Criterio de aceptación:** `bookwright init` genera el skill bookwright-verify válido en ambas integraciones; el flujo manual sobre la fixture histórica (iteración 17) produce un reporte que señala los anacronismos inyectados.

---

### Iteración 17 — Fixture histórica, E2E de investigación y docs

**Objetivo:** validar el sistema de investigación de extremo a extremo y
documentarlo, cerrando v0.2.0.

**Prompt:**

```
/speckit-specify

Necesidad: antes de release v0.2.0 necesitamos una fixture realista con investigación, tests E2E del flujo investigar→anclar→validar→verificar, y documentación del nuevo sistema.

Comportamiento esperado:

Fixture:

- tests/fixtures/tiny-historical/: una mini-novela documentada (ambientación histórica con anclas reales: fechas, hechos, procedimientos), con bible/research/ relleno (al menos 1 tema, varias Fuentes con procedencia, varias anclas), y un capítulo de manuscrito que contiene un anacronismo deliberado para que la verificación lo detecte.

Tests E2E:

- test_research_workflow.py recorre: graph build (con bible/research/) → graph query (recupera anclas) → validate (factual_anchor detecta el ancla mal formada inyectada y el anacronismo de time-span) → verificación manual del reporte de bookwright-verify sobre el anacronismo del manuscrito.
- Verificar que un proyecto sin [research]/sin bible/research/ sigue funcionando igual (el sistema es inerte si no se usa).

Documentación:

- Página docs/research.md (MkDocs): qué es la investigación en Bookwright, el modelo Fuente/Hallazgo/Ancla, el protocolo del skill, cómo se verifica, multilingüismo y procedencia.
- Actualizar docs/commands con bookwright-research y bookwright-verify, y docs/validation con factual_anchor.
- CHANGELOG.md: entrada v0.2.0 con el sistema de investigación y verificación.

Calidad final:

- pytest > 80% global (manteniendo el umbral de v0.1), > 85% en el código nuevo de M4.
- ruff, mypy --strict, pre-commit, CI verdes. mkdocs build sin warnings.

Fuera de scope:

- Búsqueda vectorial sobre fuentes (v0.3). El agente lee los Markdown directamente.

Referencia: ver bookwright-design.md § 20 completo y § 15.5 (M4).
```

**Pista para `/speckit-plan`:** *"La fixture tiny-historical es trabajo creativo pero corto y coherente; el anacronismo debe ser inequívoco para tests deterministas. Los tests E2E usan las fixtures como input, igual que la iteración 12. Docs en MkDocs material, integradas con el sitio existente. Verifica explícitamente que el sistema es inerte cuando [research].enabled=false o no hay bible/research/."*

**Criterio de aceptación:** todos los criterios del prompt se cumplen; el flujo E2E de investigación pasa; `mkdocs build` limpio; CHANGELOG con v0.2.0. Release v0.2.0 listo para publicar.

---

## 3.ter Mantenimiento — deuda técnica

Iteraciones que no entregan funcionalidad de producto sino que cancelan deuda
acumulada. No pertenecen a ningún hito y pueden intercalarse cuando convenga.

### Iteración 18 — Saneamiento de tags de trazabilidad prohibidos

**Objetivo:** dejar `src/` y `tests/` con **cero** tags de trazabilidad prohibidos
por `CONTRIBUTING.md` ("Traceability tags in code"), y añadir un gate que impida
su reaparición. Auditoría inicial: ~57 ocurrencias en 40 ficheros (20 `T0xx` +
37 `US`/`+US`), repartidas entre código ya mergeado (iteraciones 1–11) y algunos
tests recientes. Es deuda contra una convención propia del proyecto, no un bug:
los `T0xx` (IDs de `tasks.md`) y `US`/`+US` (user-stories) son bookkeeping de
planificación sin artefacto durable —los números de tareas no se congelan al
merge y quedan obsoletos—, a diferencia de `FR`/`SC`/`D` y `bookwright-design.md
§ N.M`, que sí son referencias durables.

**Prompt:**

```
/speckit-specify

Necesidad: CONTRIBUTING.md prohíbe explícitamente los tags de trazabilidad T0xx (IDs de tasks.md) y US-x/+USx (user-stories) en código fuente y tests, porque son bookkeeping de planificación sin artefacto durable que queda obsoleto tras el merge. Sin embargo, el código ya mergeado (iteraciones 1–11) y algunos tests recientes los contienen (~57 ocurrencias en ~40 ficheros). Queremos cancelar esa deuda por completo y dejarla en cero permanente.

Comportamiento esperado:

- Tras la iteración, una búsqueda de T0xx (T seguido de tres dígitos) y de US-x/USx/+USx sobre src/ y tests/ no devuelve ninguna ocurrencia (excluyendo binarios y __pycache__).
- Cada tag se trata según aporte:
  - Si el tag aportaba trazabilidad real (un T0xx que justificaba un fragmento), se sustituye por la referencia durable equivalente: el FR/SC/D del spec de la iteración propietaria de ese fichero, o bookwright-design.md § N.M. Si no existe un equivalente durable claro, se reescribe a prosa neutra que explique el porqué sin citar el ID de tarea.
  - Si el tag era un marcador de sección decorativo (p. ej. "# --- sources.md (US1) ---" o un docstring "US1 - Acceptance Scenarios..."), se reescribe a una etiqueta descriptiva del comportamiento, sin el ID.
- Es un cambio exclusivamente de comentarios y docstrings: cero cambios en lógica de código, firmas, nombres de tests o aserciones. El comportamiento observable y la cobertura no cambian.
- Se añade un gate de no-regresión que falla si reaparece un T0xx o US-x en src/ o tests/, integrado en la suite/CI (Principio VIII) de modo que la deuda quede en cero de forma permanente.

Restricciones (de CONTRIBUTING.md, sección "Traceability tags in code"):

- Las referencias resuelven relativas a la iteración del fichero: al sustituir un T0xx por un FR/SC/D, usa el número del spec de la iteración propietaria de ese subárbol, no de otra.
- Los números FR/SC/D ya mergeados están congelados: no renumerar ni reescribir referencias durables existentes; solo eliminar/convertir las prohibidas.
- Permitido y NO objetivo de limpieza: "iteración N" en prosa, y los IDs en specs/ (la prohibición es solo para src/ y tests/).

Fuera de scope:

- Tocar artefactos bajo specs/ (spec.md, plan.md, tasks.md, etc.): ahí los IDs de tarea son legítimos.
- Renumerar o "mejorar" referencias FR/SC/D existentes.
- Cualquier refactor de código que vaya más allá de comentarios/docstrings.

Referencia: ver CONTRIBUTING.md (sección "Traceability tags in code") y la constitución § VIII (disciplina de tests / gates de CI).
```

**Pista para `/speckit-plan`:** *"Barrido determinista: `grep -rnIE '\bT0[0-9]{2}\b|\bUS-?[0-9]+\b|\+US[0-9]+' src/ tests/` (excluye binarios). Clasifica cada hit en {convertible a FR/SC/D durable, convertible a § N.M, reescribir a prosa neutra} y edita en consecuencia, fichero por fichero, resolviendo cada FR/SC/D contra el spec de la iteración dueña del subárbol. El gate de no-regresión es preferible como test en `tests/` (corre en CI sin depender de pre-commit): un test que ejecuta el mismo grep sobre src/ y tests/ y asevera cero coincidencias, excluyéndose a sí mismo y a los ficheros que legítimamente mencionen el patrón en una cadena de regex. No modifiques lógica: usa `git diff` para confirmar que solo cambian comentarios/docstrings."*

**Criterio de aceptación:** el grep de tags prohibidos sobre `src/` y `tests/` devuelve vacío; el nuevo gate falla si se reintroduce un `T0xx`/`US-x`; `ruff`, `mypy --strict`, `pytest` y la cobertura se mantienen sin cambios (mismo número de tests, mismo comportamiento); `git diff` muestra exclusivamente cambios en comentarios y docstrings.

---

## 4. Notas operativas

### 4.1 Manejo de spec rechazadas

Si tras `/speckit-analyze` aparecen issues de consistencia entre spec/plan/tasks, vuelve a `/speckit-clarify` o edita el spec.md directamente, regenera plan y tasks, y vuelve a analizar. No fuerces `/speckit-implement` con análisis con errores.

### 4.2 Iteraciones que se complican

Si una iteración crece más de lo previsto durante `/speckit-tasks` (más de ~10 tareas), considera dividirla en dos specs. La iteración 4 (bookwright init) y la 7 (templates) son las candidatas más probables para split.

### 4.3 Cambios en el documento de diseño

Si durante la implementación descubres que algo del diseño no encaja con la realidad técnica, actualiza `bookwright-design.md` **antes** de divergir el código. El doc de diseño debe seguir siendo la fuente de verdad. Documenta el cambio en CHANGELOG bajo "Design decisions revised during implementation".

### 4.4 Cuándo pedir ayuda al humano

Spec Kit es bueno generando spec/plan/tasks pero puede divagar en decisiones de diseño no triviales. Cuando dudes, ejecuta `/speckit-clarify` o intervén manualmente. Las decisiones registradas en § 16 del doc de diseño son inmutables — si el agente las cuestiona, redirígelo al doc.

### 4.5 Después de v0.1.0

El hito **M4 — Investigación y verificación (v0.2.0)** ya tiene su plan detallado
arriba (§ 3.bis, iteraciones 13–17) y su diseño en `bookwright-design.md` § 20.

Las iteraciones post-M4 que sí se mantienen (búsqueda vectorial en v0.3, commands
de autoría en v0.4, export en v1.0) seguirán el mismo patrón. Cuando llegue el
momento, redactar un plan equivalente a éste, también versionado. Quedan
descartados (no se implementarán): presets, GrafeoIndexer/Grafeo, multi-integración
y extension system; ver `bookwright-design.md` § 15.5.

---

**Fin del plan.**
