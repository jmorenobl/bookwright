# Bookwright — Documento de diseño

> **Estado:** v0.1 (diseño inicial)
> **Audiencia:** agente de desarrollo encargado de la implementación.
> **Lenguaje del proyecto:** Python 3.11+.
> **Repositorio destino:** `bookwright/` (a crear).
> **Inspiración técnica directa:** [github/spec-kit](https://github.com/github/spec-kit).

---

## 0. TL;DR para el agente de desarrollo

Bookwright es un toolkit para la producción de libros (novelas, ensayos, memorias) que aplica el patrón **Spec-Driven Development** al dominio narrativo. Consta de:

1. Un **CLI Python** (`bookwright`) que hace scaffolding determinista de proyectos.
2. Un conjunto de **commands** (templates Markdown con YAML frontmatter, en el código fuente de Bookwright) que se materializan en cada proyecto destino como **Agent Skills** siguiendo el estándar abierto [agentskills.io](https://agentskills.io), invocables como slash commands (`/bookwright-constitution`, etc.) por cualquier agente IA compatible.
3. Una **arquitectura plugin-based de integraciones** (`INTEGRATION_REGISTRY` con clase base `SkillsIntegration`), heredada conceptualmente del refactor reciente de Spec Kit (issue github/spec-kit#1924). En v0 se entregan dos integraciones: `claude` (escribe en `.claude/skills/`) y `generic` (escribe en `.agents/skills/`, convención usada por Codex y Cursor).
4. Un **modelo de dominio narrativo** basado en la ontología GOLEM, serializado en Turtle (RDF).
5. Un **motor de validación de consistencia** sobre el grafo, construido con `rdflib` en v0.

El usuario instala `bookwright-cli`, ejecuta `bookwright init --integration claude`, abre el directorio con su agente (Claude Code recomendado), y lanza los commands en orden: `/bookwright-constitution`, `/bookwright-bible`, `/bookwright-outline`, `/bookwright-scenes`, `/bookwright-draft`. Cada command toma input no estructurado (una conversación previa, un brief, un dump) y produce artefactos versionables en git.

El patrón operacional es **idéntico al de Spec Kit**; lo que cambia es el dominio. Donde Spec Kit produce `spec.md / plan.md / tasks.md`, Bookwright produce `constitution.md / bible/* / outline.md / scenes.md / manuscript/*`.

**Decisiones operativas clave que el agente debe internalizar antes de empezar:**

- **Skills, no commands**: Bookwright se alinea con Agent Skills como formato canónico (progressive disclosure de tres tiers, portabilidad entre Claude Code / Codex / Cursor / Copilot, validación estructural por estándar abierto). Nunca genera archivos en `.claude/commands/` ni equivalentes; siempre `.claude/skills/<command>/SKILL.md`. Mismo principio para todas las integraciones.
- **Estándar Agent Skills como contrato externo**: Bookwright cumple [agentskills.io](https://agentskills.io). Esto garantiza portabilidad entre Claude Code, Codex CLI, Cursor, GitHub Copilot (vía VS Code) y otros 25+ agentes compatibles.
- **Bookwright no es un preset ni una extensión de Spec Kit**. Es una herramienta independiente que comparte patrones de diseño documentados públicamente. Existe un preset `fiction-book-writing` (adaumann) que aborda parcialmente el mismo problema; ver § 17 para el análisis y por qué Bookwright es un proyecto separado.

---

## 1. Objetivos y no-objetivos

### 1.1 Objetivos

- **Producir libros, no editarlos en vivo**: Bookwright asiste el proceso de pre-producción y borrador, no es un editor de texto.
- **Texto plano como fuente de verdad**: todo lo importante (manuscrito, bible, constitution, grafo) es Markdown, TOML o Turtle. Auditables por humanos, versionables en git, supervivientes a la desaparición del toolkit.
- **Funcionar con cualquier agente IA mainstream**: Claude Code es el target principal, pero el diseño no se acopla a él. Soporte explícito en v0: Claude (Code + claude.ai). Soporte futuro trivial: Copilot, Gemini, Cursor.
- **Workflow batch, no conversacional**: el usuario consolida información en un input estructurado y un command la destila en artefactos. El agente no es un compañero de escritura frase-a-frase.
- **Consistencia narrativa verificable**: el grafo derivado del manuscrito y la bible permite chequeos automáticos (continuidad temporal, presencia de personajes, focalización, anclas históricas si las hay).

### 1.2 No-objetivos (explícitos)

- **No es un editor de texto**. No reemplaza a Obsidian, Scrivener, VS Code. El usuario edita los `.md` en su editor favorito.
- **No genera la novela**. Asiste destilación, validación y refinamiento. El borrador final lo escribe el autor.
- **No publica**. La exportación a EPUB/PDF/print queda fuera de scope de v0. Hay hooks para ello en el diseño pero no se implementa en v0.
- **No es un preset de Spec Kit**. Comparte patrón y código heredado/inspirado, pero es una herramienta separada con identidad propia. La razón: el dominio diverge demasiado y la audiencia (escritores) no debe conocer Spec Kit.
- **No requiere Grafeo en v0**. La opción de indexer con Grafeo queda como extensión futura. v0 usa `rdflib`.
- **No genera assets multimedia**. Sin generación de imágenes, audio, ni interactivos.

---

## 2. Filosofía: Document-Driven Authoring (DDA)

Bookwright es la aplicación del patrón **Spec-Driven Development** (SDD) al dominio narrativo. Renombramos a **Document-Driven Authoring (DDA)** para que la metáfora encaje sin contorsiones.

| Spec-Driven Development | Document-Driven Authoring |
|---|---|
| Specs son el centro del proceso. | Documentos canónicos (constitution, bible, outline) son el centro. |
| El AI escribe código a partir de la spec. | El AI destila documentos a partir de inputs no estructurados. |
| Spec → Plan → Tasks → Implement. | Constitution → Bible → Outline → Scenes → Draft. |
| Iterar la spec, no el código. | Iterar los documentos canónicos, no los borradores. |
| El producto es software. | El producto es un libro. |

**Implicación operativa para el agente de desarrollo:** los commands de Bookwright replican estructuralmente los de Spec Kit. Cualquier patrón resuelto en Spec Kit (manejo de frontmatter, generación de skills desde commands, resolución de templates por capas) se reutiliza con cambios mínimos.

---

## 3. Arquitectura general

### 3.1 Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                         Bookwright                              │
│                                                              │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │     CLI     │    │   Commands    │    │    Skills    │    │
│  │  (Python)   │    │  (.md + YAML) │    │  (SKILL.md)  │    │
│  │             │    │               │    │              │    │
│  │ Determinista│    │   Prompts     │    │  Skills      │    │
│  │  scaffolds  │    │   estructur.  │    │  derivadas   │    │
│  │  parses,    │    │   ejecutados  │    │  de commands │    │
│  │  validates  │    │   por agente  │    │  con          │    │
│  │             │    │               │    │  --skills    │    │
│  └──────┬──────┘    └───────┬───────┘    └──────┬───────┘    │
│         │                   │                    │            │
│         └───────────────────┼────────────────────┘            │
│                             │                                 │
│                  ┌──────────▼───────────┐                     │
│                  │   Modelo de dominio  │                     │
│                  │      (GOLEM)          │                     │
│                  │   en Turtle (RDF)     │                     │
│                  └──────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

**Tres reglas estrictas:**

1. **Commands llaman al CLI**, nunca al revés.
2. **El CLI nunca llama a un LLM**. Si necesita extracción semántica, falla y devuelve "trabajo de command".
3. **La interfaz entre CLI y commands es JSON sobre stdout** (mismo patrón que Spec Kit).

### 3.2 Flujo de uso (cara al autor)

```
[Fase 1: Ideación]
└─ Conversación libre con claude.ai / Gemini / etc.
   └─ Output: dump de conversación o brief en .md

[Fase 2: Inicialización]
└─ bookwright init mi-libro
   └─ Genera estructura de directorios, manifest, templates,
      commands, skills locales al proyecto.

[Fase 3: Destilación estructurada]
└─ Abrir mi-libro/ con Claude Code (u otro agente)
   └─ /bookwright-constitution con el dump de Fase 1
      └─ /bookwright-bible
         └─ /bookwright-outline
            └─ /bookwright-scenes
               └─ /bookwright-draft (por escena/capítulo)

[Fase 4: Refinamiento]
└─ Iteración sobre cualquier artefacto:
   /bookwright-clarify, /bookwright-analyze, /bookwright-checklist
```

---

## 4. Modelo de dominio: GOLEM

### 4.1 Por qué GOLEM y no otra ontología

La ontología elegida es **GOLEM** (Pianzola, Cheng, Pannach et al., 2025), publicada en *Humanities* 14(10):193, DOI 10.3390/h14100193. Repositorio: `github.com/GOLEM-lab/golem-ontology`. Documentación: `ontology.golemlab.eu`.

Razones:

- Es la única ontología actualmente disponible que integra coherentemente personajes, relaciones, eventos, settings, narrativa e inferencia en un solo modelo.
- Extiende **CIDOC CRM** (ISO 21127) y **LRMoo** (modelo bibliográfico de IFLA), alineada con **DOLCE**.
- Modular: cada uno de los seis módulos puede usarse independientemente.
- Soporta el patrón `E55_Type` para vocabularios controlados, lo que permite enchufar Propp, Greimas, los Seven Plots de Booker, estructuras de ensayo, etc., sin tocar el core.
- Tiene un módulo de **Inference** explícito (`E13_Attribute_Assignment`) que permite trazar la procedencia de cada afirmación: lo que dice el manuscrito vs. lo que infirió el agente.
- Licencia compatible con uso comercial.

### 4.2 Los seis módulos

| Módulo | Clases principales | Función |
|---|---|---|
| **Character** | `G1_Character`, `G0_Character-Stoff`, `G16_Object`, `G17_Character_Feature`, `G18_Textual_Feature` | Personajes y sus atributos, distinción entre personaje narrativo y personaje "platónico" (Character-Stoff). |
| **Relationship** | `G4_Social_Relationship`, `G6_Relationship_Role` | Relaciones sociales reificadas con roles. |
| **Event** | `G5_Narrative_Event`, `G3_Psychological_State` | Eventos narrativos vs. estados psicológicos. Distinción perdurante/estativo. |
| **Setting** | `G12_Setting`, `G13_Narrative_Location` | Universo narrativo y localizaciones. |
| **Narrative** | `G14_Narrative-Stoff`, `G9_Narrative_Unit`, `G10_Narrative_Function`, `G11_Narrative_Role`, `G7_Narrative_Sequence` | Material narrativo, unidades, funciones (Proppianas y otras), secuencias (fabula, syuzhet). |
| **Inference** | `E13_Attribute_Assignment` (de CIDOC CRM) | Trazabilidad de afirmaciones: fuente, método, premisa. |

### 4.3 Versionado de la ontología

- La versión de GOLEM se **congela** en cada release de Bookwright. Vive en `src/bookwright/resources/schemas/golem-{version}/`.
- El proyecto generado registra qué versión usa en `manifest.toml > [bookwright] schema_version`.
- Cuando GOLEM publique una versión nueva, se añade una carpeta `golem-{nueva}/` sin tocar la anterior. El usuario migra explícitamente con `bookwright migrate-schema`.
- v0 inicia con GOLEM 1.0 (la versión publicada en 2025).

### 4.4 Vocabularios controlados

GOLEM proporciona el patrón `E55_Type` para enchufar vocabularios sin extender el esquema. Bookwright incluye en v0:

- `propp.ttl` — funciones Proppianas y dramatis personae.
- `greimas.ttl` — modelo actancial de Greimas.
- `booker-seven-plots.ttl` — los siete plots básicos.
- `essay-structures.ttl` — estructuras retóricas para no-ficción (tesis, argumento, contraargumento, etc.).

Los usuarios pueden añadir vocabularios propios en `<proyecto>/.bookwright/vocabularies/`.

### 4.5 Generación de URIs

Cada proyecto declara un namespace base en `manifest.toml`. Por ejemplo:

```toml
[bookwright]
uri_base = "https://example.org/my-book/"
```

Las URIs se generan por composición, `{uri_base}{segmento}/{token}`, con un
segmento fijo por concepto y un token de identidad (slug para entidades con
nombre, UUIDv7 para aserciones):

| Concepto | Segmento | Token |
|---|---|---|
| Personaje (`G1_Character`) | `character` | slug |
| Objeto (`G16_Object`) | `object` | slug |
| Evento (`G5_Narrative_Event`) | `event` | slug |
| Estado psicológico (`G3_Psychological_State`) | `psychological-state` | slug |
| Setting (`G12_Setting`) | `setting` | slug |
| Localización (`G13_Narrative_Location`) | `location` | slug |
| Relación social (`G4_Social_Relationship`) | `relationship` | slug |
| Rol de relación (`G6_Relationship_Role`) | `relationship-role` | slug |
| Unidad narrativa (`G9_Narrative_Unit`) | `narrative-unit` | slug |
| Función narrativa (`G10_Narrative_Function`) | `narrative-function` | slug |
| Rol narrativo (`G11_Narrative_Role`) | `narrative-role` | slug |
| Secuencia narrativa (`G7_Narrative_Sequence`) | `narrative-sequence` | slug |
| Aserción de atributo (`E13_Attribute_Assignment`) | `assertion` | UUIDv7 |

El segmento por concepto evita que dos entidades de tipos distintos que
comparten slug colapsen en la misma URI.

El slug se genera del nombre canónico con `python-slugify` en su modo por
defecto: **minúsculas y solo ASCII**. Los caracteres acentuados o no-ASCII se
transliteran a su forma ASCII más próxima (`José Peña` → `jose-pena`,
`La caída` → `la-caida`), los espacios y separadores colapsan a un único guión,
y se recortan los guiones de los extremos. Un nombre canónico cuyo slug
resultante quede vacío se rechaza con un error explícito. Se eligió ASCII puro
—en lugar de preservar diacríticos— por portabilidad: las IRIs con caracteres
no-ASCII obligan a percent-encoding y se comportan de forma inconsistente entre
endpoints SPARQL, herramientas RDF y espejos en el sistema de ficheros. La
desambiguación de slugs colisionantes es responsabilidad del indexer (iteración
6), no del modelo de dominio.

Las aserciones usan UUIDv7 (vía `uuid_utils.uuid7()` del paquete `uuid-utils`)
para mantener orden temporal sin colisiones. Toda entidad salvo la aserción de
atributo se construye a partir de un nombre canónico provisto por quien la crea;
el modelo nunca sintetiza nombres a partir de los participantes.

---

## 5. Diseño del CLI

### 5.1 Comandos

Todos los comandos son sub-apps de Typer.

| Comando | Propósito | Ejemplo |
|---|---|---|
| `bookwright init [NAME]` | Inicializa un nuevo proyecto. | `bookwright init my-novel` |
| `bookwright init --here` | Inicializa en el directorio actual. | `bookwright init --here` |
| `bookwright graph build` | (Re)construye el grafo desde Turtle y la bible. | `bookwright graph build --force` |
| `bookwright graph query SPARQL` | Ejecuta una query SPARQL sobre el grafo. | `bookwright graph query "SELECT ?c WHERE { ?c a golem:G1_Character }"` |
| `bookwright validate` | Corre todos los validators. | `bookwright validate --scope manuscript/cap-01.md` |
| `bookwright check` | Verifica el toolchain (Python, dependencias). | `bookwright check` |
| `bookwright version` | Imprime versión del CLI y del schema GOLEM. | `bookwright version` |

### 5.2 Flags de `bookwright init`

Bookwright usa el sistema **Integration** plugin-based de Spec Kit (introducido en su issue #1924). En v0, todas las integraciones generan **Agent Skills** según el estándar [agentskills.io](https://agentskills.io); no se generan archivos en `.claude/commands/` ni equivalentes (formato deprecado por Claude Code y por la mayoría de agentes modernos).

| Flag | Tipo | Default | Descripción |
|---|---|---|---|
| `PROJECT_NAME` | posicional | — | Nombre del directorio. Mutex con `--here`. |
| `--here` | flag | False | Inicializa en directorio actual. |
| `--force` | flag | False | Sobreescribe directorio existente. |
| `--no-git` | flag | False | Salta inicialización de git. |
| `--integration` | string | `claude` | Integración target. v0: `claude`, `generic`. |
| `--integration-options` | string | — | Opciones específicas del plugin de integración. Solo aplica si el plugin declara opciones. v0: `generic` acepta `--skills-dir` para override del default `.agents/skills/`. |
| `--script` | choice | auto | `sh` o `ps`. Detecta por SO si no se indica. Reservado para v0.2+ (en v0 no hay scripts auxiliares: los SKILL.md invocan el CLI `bookwright` directamente). |
| `--preset` | string | — | Preset de género (v0.2+, no en v0). |

**Defaults por integración:**

| Integración | Directorio de skills generado | Estándar |
|---|---|---|
| `claude` | `.claude/skills/<command>/SKILL.md` | Agent Skills (Claude Code extensions) |
| `generic` | `.agents/skills/<command>/SKILL.md` | Agent Skills puro (compatible Codex, Cursor, VS Code Copilot) |

**Alias de compatibilidad y deprecación.** El CLI acepta `--ai` como alias oculto de `--integration` durante un ciclo de release, emitiendo un warning y reenviando el valor internamente. Los flags `--ai-skills` y `--ai-commands-dir` (de la API vieja de Spec Kit) ya no se aceptan: el primero porque skills es ahora el único modo, el segundo porque `generic` usa `.agents/skills/` por defecto. Si alguien los pasa, el CLI emite un error explicativo apuntando al equivalente actual.

**Ejemplos:**

```bash
# Inicialización para Claude Code (caso típico)
bookwright init my-novel --integration claude

# Inicialización para Codex CLI / Cursor / VS Code (Agent Skills puro)
bookwright init my-novel --integration generic

# Override del directorio de skills para generic
bookwright init my-novel --integration generic --integration-options="--skills-dir .cursor/skills"
```

### 5.3 Output JSON (patrón Spec Kit)

Los comandos que devuelven datos al agente IA aceptan `--json`. El output va a stdout en una sola línea para parseo trivial. Mensajes informativos y warnings van a stderr.

Ejemplo: `bookwright graph query "..." --json`:

```json
{"status": "ok", "results": [{"c": "https://...character/aparici", "name": "Aparici"}], "count": 1}
```

`bookwright validate --json`:

```json
{"status": "ok", "violations": [{"validator": "temporal", "severity": "error", "message": "...", "source": "manuscript/cap-04.md:42"}], "violation_count": 1}
```

### 5.4 Resolución de templates (4 capas, como Spec Kit)

Cuando un command necesita un template, lo resuelve en orden:

1. **Overrides**: `.bookwright/templates/overrides/{name}`
2. **Presets**: `.bookwright/presets/{preset-id}/templates/{name}` (priority-based, lowest number wins)
3. **Extensions**: `.bookwright/extensions/{ext-id}/templates/{name}` (futuro)
4. **Core**: `.bookwright/templates/{name}` (default)

Función `resolve_template()` en `src/bookwright/core/templates.py`, idiomática Python (no bash como Spec Kit).

---

## 6. Estructura del repo de Bookwright (el toolkit)

```
bookwright/
├── README.md
├── LICENSE                              # Apache-2.0
├── CHANGELOG.md
├── CONTRIBUTING.md
├── pyproject.toml
├── uv.lock
├── .python-version                      # 3.11
├── .gitignore
├── .pre-commit-config.yaml
│
├── docs/
│   ├── index.md
│   ├── getting-started.md
│   ├── architecture.md
│   ├── ontology.md                      # GOLEM aplicado
│   ├── manifest-spec.md                 # spec del manifest.toml
│   ├── command-format.md                # formato de los commands
│   └── extending/
│       ├── adding-vocabularies.md
│       ├── custom-presets.md            # post-v0
│       └── writing-skills.md
│
├── src/
│   └── bookwright/
│       ├── __init__.py                  # __version__
│       ├── __main__.py                  # python -m bookwright
│       ├── cli.py                       # entry point Typer
│       │
│       ├── commands/                    # un módulo por comando del CLI
│       │   ├── __init__.py
│       │   ├── init.py
│       │   ├── graph.py
│       │   ├── validate.py
│       │   ├── check.py
│       │   └── version.py
│       │
│       ├── core/                        # lógica del CLI reutilizable
│       │   ├── __init__.py
│       │   ├── project.py               # ProjectContext
│       │   ├── manifest.py              # parser y modelo del manifest.toml
│       │   ├── constitution.py          # parser del constitution.md
│       │   ├── paths.py                 # convenciones de rutas
│       │   ├── templates.py             # resolve_template() 4-layer
│       │   ├── errors.py
│       │   └── io_json.py               # JSON output helpers
│       │
│       ├── golem/                       # modelo de dominio GOLEM
│       │   ├── __init__.py
│       │   ├── namespaces.py            # URI generation, prefixes
│       │   ├── base.py                  # clases base, mixins
│       │   └── modules/                 # uno por módulo GOLEM
│       │       ├── __init__.py
│       │       ├── character.py
│       │       ├── relationship.py
│       │       ├── event.py
│       │       ├── setting.py
│       │       ├── narrative.py
│       │       └── inference.py
│       │
│       ├── indexers/                    # motor de grafo intercambiable
│       │   ├── __init__.py
│       │   ├── base.py                  # Indexer Protocol
│       │   ├── rdflib_indexer.py        # default v0
│       │   └── grafeo_indexer.py        # stub, post-v0
│       │
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── base.py                  # Validator Protocol
│       │   ├── registry.py              # autodescubrimiento de validators
│       │   ├── temporal.py
│       │   ├── character_presence.py
│       │   ├── setting_continuity.py
│       │   └── focalization.py
│       │
│       ├── io/                          # serialización
│       │   ├── __init__.py
│       │   ├── turtle.py                # leer/escribir .ttl
│       │   ├── manuscript.py            # markdown del manuscrito
│       │   └── bible.py                 # estructura de bible/
│       │
│       ├── integrations/                # arquitectura plugin-based (espeja Spec Kit)
│       │   ├── __init__.py              # INTEGRATION_REGISTRY + _register_builtins()
│       │   ├── base.py                  # SkillsIntegration, IntegrationOption, SKILL_DESCRIPTIONS
│       │   ├── claude/
│       │   │   ├── __init__.py          # ClaudeIntegration(SkillsIntegration)
│       │   │   └── references/          # docs auxiliares específicos para .claude/skills/.../references/
│       │   └── generic/
│       │       ├── __init__.py          # GenericIntegration(SkillsIntegration)
│       │       └── references/
│       │
│       └── resources/                   # artefactos empaquetados
│           ├── schemas/
│           │   └── golem-1.0/
│           │       ├── golem.ttl
│           │       └── version.json
│           ├── vocabularies/
│           │   ├── propp.ttl
│           │   ├── greimas.ttl
│           │   ├── booker-seven-plots.ttl
│           │   └── essay-structures.ttl
│           ├── templates/
│           │   ├── manifest.toml.tmpl
│           │   ├── constitution.md.tmpl
│           │   ├── readme.md.tmpl
│           │   ├── gitignore.tmpl
│           │   ├── bible/
│           │   │   ├── character.md.tmpl
│           │   │   ├── setting.md.tmpl
│           │   │   ├── timeline.md.tmpl
│           │   │   ├── relationship.md.tmpl
│           │   │   ├── pov-structure.md.tmpl     # ← inspirado en fiction-book preset
│           │   │   ├── themes.md.tmpl            # ← motif registry + symbol tracker
│           │   │   ├── world-building.md.tmpl    # ← reglas del mundo (post-v0 para no-ficción)
│           │   │   ├── locations.md.tmpl         # ← anclas sensoriales por localización
│           │   │   ├── research.md.tmpl          # ← open questions + source notes
│           │   │   ├── glossary.md.tmpl          # ← invented terms + consistency log
│           │   │   └── subplots.md.tmpl          # ← beat sheets de subtramas
│           │   ├── outline/
│           │   │   ├── arcs.md.tmpl
│           │   │   ├── structure.md.tmpl
│           │   │   └── synopsis.md.tmpl          # ← corta (250-350) + larga (1000-2000)
│           │   ├── scenes/
│           │   │   └── scene.md.tmpl
│           │   └── manuscript/
│           │       └── chapter.md.tmpl
│           ├── commands/                # source-of-truth de cada Agent Skill
│           │   │                        # cada .md aquí se materializa como
│           │   │                        # <skills_dir>/<command>/SKILL.md en el proyecto
│           │   ├── bookwright-constitution.md
│           │   ├── bookwright-bible.md
│           │   ├── bookwright-outline.md
│           │   ├── bookwright-scenes.md
│           │   ├── bookwright-draft.md
│           │   ├── bookwright-synopsis.md           # ← actualiza sinopsis corta+larga
│           │   ├── bookwright-clarify.md
│           │   ├── bookwright-analyze.md            # ← pre-draft: spec↔plan↔scenes
│           │   ├── bookwright-continuity.md         # ← post-draft: manuscrito↔bible
│           │   └── bookwright-checklist.md
│           └── presets/                 # post-v0, estructura ya prevista
│               ├── novel/
│               ├── historical-fiction/
│               ├── essay/
│               └── memoir/
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_manifest.py
│   │   ├── test_golem_classes.py
│   │   ├── test_namespaces.py
│   │   ├── test_rdflib_indexer.py
│   │   └── test_validators.py
│   ├── integration/
│   │   ├── test_init.py
│   │   ├── test_graph_build.py
│   │   └── test_validate.py
│   ├── e2e/
│   │   └── test_full_workflow.py
│   └── fixtures/
│       ├── tiny-novel/
│       ├── tiny-essay/
│       └── tiny-memoir/
│
├── scripts/                             # dev-only scripts del repo
│   ├── update-golem-schema.py
│   ├── verify-skills.py
│   └── generate-fixtures.py
│
└── .github/
    └── workflows/
        ├── tests.yml
        ├── release.yml
        └── docs.yml
```

### 6.1 Decisiones explicadas

- **src-layout**: evita imports erróneos en pytest. Estándar moderno.
- **Comandos por archivo**: Spec Kit los concentra en un módulo de 2000+ líneas; eso envejece mal. Aquí cada comando es un archivo bajo `commands/`, registrado en `cli.py` via Typer sub-apps.
- **`golem/modules/` espeja la modularización de GOLEM**: lectura cruzada paper ↔ código.
- **`integrations/` plugin-based desde el día uno**: Spec Kit ha hecho ya el refactor de `AGENT_CONFIG` (diccionario monolítico) a `INTEGRATION_REGISTRY` con una jerarquía de clases base (`IntegrationBase`, `SkillsIntegration`, `MarkdownIntegration`) y un dataclass `IntegrationOption` para declarar opciones por plugin. Bookwright nace con la arquitectura nueva pero solo usa `SkillsIntegration` (el modelo Markdown-puro queda fuera del scope por la deprecación de commands en Claude Code; ver § 11). Cada integración es un subpaquete autocontenido en `src/bookwright/integrations/<key>/` con `__init__.py` exponiendo la clase de la integración y, opcionalmente, `references/` para archivos auxiliares que se materializan en los skills.
- **Indexer Protocol**: permite migrar de `rdflib` a `grafeo` (futuro) sin tocar commands ni validators.
- **Validator Protocol con registry**: cada chequeo es independiente, autodescubierto. El usuario puede añadir validators custom en `<proyecto>/.bookwright/validators/`.
- **`resources/` es la clave**: contiene todo lo que el CLI distribuye. Accedido via `importlib.resources.files("bookwright.resources")`. Cero rutas hardcoded. Cero llamadas a la red en `init`.
- **Templates dentro del wheel** (no GitHub Releases como Spec Kit). v0 tiene una sola integración principal, no se justifica la complejidad de release-based templates. Se migra a release-based si y cuando se justifique.
- **Templates de bible expandidos respecto al diseño inicial**: la lectura del preset `fiction-book-writing` ha revelado un inventario más completo de documentos canónicos útiles para producción narrativa (synopsis, themes, locations, research, glossary, subplots, pov-structure). Adoptamos estos templates como inspiración con licencia MIT, adaptando su estructura al modelado GOLEM. Ver § 17 para el detalle del trabajo relacionado.

---

## 7. Estructura del proyecto generado

Tras `bookwright init my-book`:

```
my-book/
├── manifest.toml                        # Contrato del proyecto
├── README.md                            # Guía mínima para humanos
├── .gitignore
├── .python-version                      # opcional
│
├── manuscript/                          # Borrador del libro
│   ├── cap-01.md
│   ├── cap-02.md
│   └── ...
│
├── bible/                               # Documentos canónicos
│   ├── constitution.md                  # Pacto narrativo
│   ├── characters/
│   │   └── *.md
│   ├── settings/
│   │   └── *.md
│   ├── locations/                       # Anclas sensoriales por localización (opcional)
│   │   └── *.md
│   ├── timeline.md
│   ├── relationships.md
│   ├── pov-structure.md                 # Sólo si multi-POV
│   ├── themes.md                        # Motif registry + symbol tracker
│   ├── glossary.md                      # Invented terms + consistency log
│   ├── research.md                      # Open questions + source notes (clave en histórica)
│   ├── subplots.md                      # Beat sheets de subtramas
│   └── graph.ttl                        # Turtle: fuente de verdad del grafo
│
├── outline/                             # Estructura narrativa
│   ├── arcs.md
│   ├── structure.md
│   ├── synopsis.md                      # Corta (250-350) y larga (1000-2000)
│   └── scenes.md
│
├── .bookwright/                            # Configuración del toolkit
│   ├── init-options.json                # Opciones con que se inició
│   ├── schema/
│   │   └── golem.ttl                    # Ontología congelada para este proyecto
│   ├── vocabularies/
│   │   ├── propp.ttl
│   │   ├── greimas.ttl
│   │   └── ...                          # los que el usuario active
│   ├── templates/                       # Templates resolubles (capa "core")
│   │   ├── overrides/                   # Capa 1 de resolución
│   │   ├── manifest.toml.tmpl
│   │   ├── constitution.md.tmpl
│   │   └── ...
│   ├── presets/                         # Capa 2 (post-v0)
│   ├── extensions/                      # Capa 3 (post-v0)
│   └── cache/                           # Reconstruible, en .gitignore
│
└── .claude/                             # Sólo si --integration claude
    └── skills/
        ├── bookwright-constitution/
        │   └── SKILL.md
        ├── bookwright-bible/
        │   └── SKILL.md
        └── ...

# Alternativa (sólo si --integration generic):
# .agents/
# └── skills/
#     ├── bookwright-constitution/SKILL.md
#     └── ...
```

### 7.1 Qué se versiona en git y qué no

**En git:**
- Todo `manuscript/`, `bible/`, `outline/`
- `manifest.toml`, `README.md`
- `.bookwright/init-options.json`, `.bookwright/schema/`, `.bookwright/vocabularies/`, `.bookwright/templates/` (incluyendo `overrides/`)
- `.claude/skills/` (si `--integration claude`) o `.agents/skills/` (si `--integration generic`)

**En `.gitignore`:**
- `.bookwright/cache/` (caché reconstruible)
- `*.pyc`, `__pycache__/`
- `.venv/`, `.env`

El principio: lo que un humano puede leer o reconstruir desde texto, se versiona. Lo que es caché o ruido del sistema, no.

---

## 8. Manifest del proyecto: `manifest.toml`

### 8.1 Spec completa

```toml
# manifest.toml — Contrato entre Bookwright CLI y el proyecto.

[bookwright]
# OBLIGATORIO. Versiones para compatibilidad.
cli_version_min = "0.1.0"
schema_version = "golem-1.0"
manifest_version = "1"

# OBLIGATORIO. URI base del proyecto.
uri_base = "https://books.example.org/my-book/"

# Motor de grafo. v0: solo "rdflib".
indexer = "rdflib"

[book]
# OBLIGATORIO.
title = "My Book"
type = "novel"        # novel | essay | memoir | non-fiction-narrative | other
language = "es"       # ISO 639-1
authors = ["Jorge Moreno"]

# OPCIONAL pero recomendado.
subtitle = ""
genre = ["historical-fiction"]
target_length_words = 80000
status = "drafting"   # idea | structuring | drafting | revising | done

[book.metadata]
# Libre, para uso del autor. No interpretado por el CLI.
isbn = ""
publisher = ""
publication_date = ""

[vocabularies]
# Vocabularios activos. Cada uno debe existir en .bookwright/vocabularies/<name>.ttl
# Si el archivo no existe en el proyecto, se copia desde el paquete bookwright.
active = ["propp", "greimas"]

[validators]
# Lista de validators activos. Si está vacío, todos los validators built-in se activan.
enabled = ["temporal", "character_presence", "setting_continuity"]
disabled = []

# Validators custom del usuario (busca en .bookwright/validators/)
custom = []

[integration]
# Integración configurada.
key = "claude"
# Directorio donde se materializaron las skills (relativo a la raíz del proyecto).
# claude → .claude/skills/
# generic → .agents/skills/ (default) o el directorio especificado vía --skills-dir
skills_dir = ".claude/skills"
# Opciones serializadas que se pasaron vía --integration-options.
# Cada plugin define qué claves acepta.
options = {}

[paths]
# Convenciones de paths relativos al manifest. Editar con cuidado.
manuscript = "manuscript/"
bible = "bible/"
outline = "outline/"
graph = "bible/graph.ttl"
constitution = "bible/constitution.md"
```

### 8.2 Versionado y compatibilidad

- `cli_version_min`: si el CLI instalado es anterior, el comando falla con un mensaje claro.
- `schema_version`: vincula al schema GOLEM congelado. Si el usuario actualiza el CLI y el CLI trae una versión más nueva de GOLEM, no migra automáticamente: `bookwright migrate-schema` lo hace explícitamente.
- `manifest_version`: string que sigue semver-major (`"1"`, `"2"`, …). Se incrementa cuando el formato del manifest sufre cambios incompatibles. El CLI tiene un parser tolerante para versiones antiguas y emite warning ante versiones futuras desconocidas.

### 8.3 Validación del manifest

`src/bookwright/core/manifest.py` define un modelo Pydantic con todos los campos. Validación al cargar:

- Campos obligatorios presentes.
- URIs válidas.
- Lengua en ISO 639-1.
- `type` en el enum permitido.
- Vocabularios referenciados existen como archivos `.ttl`.
- `cli_version_min` ≤ `__version__`.

---

## 9. Constitution: el pacto narrativo

### 9.1 Función

Equivalente a la `constitution.md` de Spec Kit (gobernanza del proyecto), pero para libros. Es **input para todos los demás commands** y debe rellenarse con criterio antes de avanzar.

### 9.2 Estructura del template

```markdown
# Constitution — {{ book.title }}

## Voz y registro
- **Persona narrativa**: (primera persona / tercera limitada / tercera omnisciente / múltiples POV / experimental)
- **Tono**: (neutral / coloquial / lírico / técnico / etc.)
- **Registro**: (formal / informal / mixto)
- **Tiempos verbales**: (pasado / presente / mezclado)

## Pacto con el lector
- **Género contractual**: (qué espera el lector — ej. "novela negra con resolución racional", "ensayo argumentativo con evidencia citada")
- **Promesas estructurales**: (cliffhangers, capítulos cortos, etc.)
- **Promesas estéticas**:

## Pacto histórico-ficcional (si aplica)
- **Fechas intocables**: (eventos históricos cuya fecha NO se puede modificar)
- **Personajes históricos reales presentes**: (con criterio de fidelidad)
- **Anacronismos permitidos**: (cuáles, con qué función)
- **Licencias deliberadas**:

## Líneas rojas
- (Cosas que el libro NO va a hacer. Ej. "no glorificar la violencia gratuita", "no usar metáforas marítimas para la protagonista".)

## Invariantes de coherencia
- (Reglas duras que cualquier validador debe respetar. Ej. "El personaje X no puede aparecer en cap. anteriores al 5".)

## Vocabularios activos
- (Lista de vocabularios narrativos que el agente debe usar al modelar.)

## Notas para el agente
- (Cualquier guía adicional para cómo el agente debe interpretar inputs y producir artefactos.)
```

### 9.3 Diferencia con Spec Kit

En Spec Kit, la constitution es la fuente del orden técnico del proyecto. En Bookwright, la constitution es la **fuente de coherencia estética y contractual**. No es opcional: sin constitution rellenada, los demás commands tienen poco contra qué validar.

---

## 10. Sistema de Commands

### 10.1 Formato del command template

Hereda directamente del formato de Spec Kit (ver `templates/commands/specify.md` en su repo). Cada command es un archivo Markdown con frontmatter YAML:

```markdown
---
description: Destilar la constitution narrativa desde un brief o conversación previa.
handoffs:
  - label: "Bible"
    agent: bookwright-bible
    prompt: "Genera la bible desde la constitution y el brief."
    send: true
---

# /bookwright-constitution

Eres un editor narrativo experimentado. Tu tarea es destilar la **constitution** del libro a partir del input que se te entrega: una conversación previa o un brief no estructurado.

## Input
{ARGS}

## Procedimiento

1. Lee el input completo.
2. Identifica:
   - Voz y registro narrativos.
   - Pacto con el lector.
   - Pacto histórico-ficcional si aplica.
   - Líneas rojas.
   - Invariantes de coherencia.
   - Vocabularios narrativos que conviene activar.
3. Lee `.bookwright/templates/constitution.md.tmpl` (o el override si existe).
4. Rellena todos los campos del template con material del input.
5. Si hay campos sin información en el input, marca explícitamente como `[PENDIENTE]` con una pregunta de clarificación.
6. Escribe el resultado en `bible/constitution.md`.
7. Ejecuta `bookwright graph build --json` para reconstruir el grafo y validar consistencia.
8. Reporta:
   - Qué campos quedaron `[PENDIENTE]`.
   - Qué vocabularios activaste.
   - Sugerencia: ejecutar `/bookwright-clarify` antes de pasar a `/bookwright-bible`.
```

### 10.2 Tokens substituibles

Bookwright simplifica el set de tokens de Spec Kit: como todos los SKILL.md invocan el CLI `bookwright` directamente (no hay wrappers shell/Python intermedios), el token `{SCRIPT}` desaparece y el SO deja de ser variable de sustitución.

| Token | Reemplazado por | Scope |
|---|---|---|
| `{ARGS}` | `$ARGUMENTS` (agentes estilo-Claude) o `{{args}}` (Gemini, Qwen). | Cuerpo |
| `__AGENT__` | El identificador del agente. | Cuerpo |

Cualquier invocación de comando se escribe inline en el SKILL.md como `bookwright <sub> --json [args]`. Esto es posible porque el CLI es Python puro, está en el `PATH` tras `pipx install bookwright-cli`, y todos los subcomandos relevantes soportan `--json` para output parseable por el agente.

### 10.3 Pipeline command source → Agent Skill por integración

Conviene precisar la terminología antes de seguir:

- **"Command" en el código de Bookwright** = el archivo `.md` en `src/bookwright/resources/commands/`. Es el source-of-truth de la lógica. Su nombre es `bookwright-constitution.md`, `bookwright-bible.md`, etc.
- **"Slash command" para el usuario final** = lo que escribe en su agente, ej. `/bookwright-constitution`. Lo que materializa esa invocación es siempre un Agent Skill (formato SKILL.md). Claude Code, Codex, Cursor, Copilot y otros agentes compatibles convierten `/<skill-name>` en una invocación explícita del skill.

Durante `bookwright init`, la integración resuelta toma cada `.md` de `resources/commands/` y lo materializa como un Agent Skill en `<skills_dir>/<command>/SKILL.md`:

| Integration key | `skills_dir` por defecto | Estándar de skills | Estado v0 |
|---|---|---|---|
| `claude` | `.claude/skills/` | Agent Skills + extensiones de Claude Code | ✓ |
| `generic` | `.agents/skills/` | Agent Skills puro (agentskills.io) | ✓ |
| `copilot` | `.github/skills/` | Agent Skills (VS Code) | post-v0 |
| `cursor` | `.cursor/skills/` | Agent Skills + extensiones Cursor | post-v0 |
| `codex` | `.agents/skills/` | Agent Skills puro | post-v0 (cubierto por `generic`) |

Para añadir una integración futura basta con crear `src/bookwright/integrations/<key>/__init__.py` con una clase que herede de `SkillsIntegration` y declare su `skills_dir` y `extensions` (capacidades opcionales del agente que se quieren aprovechar: dynamic context injection, subagents, etc.). El registro central en `integrations/__init__.py::_register_builtins()` la añade a `INTEGRATION_REGISTRY`. Mismo patrón que el documentado en `AGENTS.md` de Spec Kit.

### 10.4 Lista completa de commands en v0

| Command | Input | Output | Fase |
|---|---|---|---|
| `/bookwright-constitution` | Brief / conversación | `bible/constitution.md` | 1. Setup |
| `/bookwright-bible` | Constitution + brief | `bible/characters/*.md`, `bible/settings/*.md`, `bible/locations/*.md`, `bible/timeline.md`, `bible/relationships.md`, `bible/themes.md`, `bible/glossary.md`, `bible/research.md`, `bible/subplots.md`, `bible/pov-structure.md` (si multi-POV), `bible/graph.ttl` | 2. Setup |
| `/bookwright-outline` | Constitution + bible | `outline/arcs.md`, `outline/structure.md`, `outline/synopsis.md` | 3. Structure |
| `/bookwright-scenes` | Outline + bible | `outline/scenes.md` | 4. Pre-draft |
| `/bookwright-draft <scene_id>` | Outline + scene | `manuscript/cap-NN.md` (sección de la escena) | 5. Draft |
| `/bookwright-synopsis` | Estado actual | Actualiza `outline/synopsis.md` (corta + larga) | cualquier momento |
| `/bookwright-clarify <artifact?>` | Cualquier artefacto | Lista de preguntas pendientes | cualquier momento |
| `/bookwright-analyze` | Constitution + bible + outline + scenes | Reporte pre-draft de inconsistencias cruzadas | tras 2-4 |
| `/bookwright-continuity` | Manuscrito + bible + grafo | Reporte post-draft: bible compliance, character arcs, timeline coherence | tras 5 |
| `/bookwright-checklist <artifact>` | Un artefacto concreto | Reporte de completitud | cualquier momento |

---

## 11. Sistema de Integration

### 11.1 Arquitectura

Cada integración es un subpaquete autocontenido bajo `src/bookwright/integrations/<key>/` que expone una sola clase, heredera de `SkillsIntegration`. En v0 Bookwright no soporta agentes que solo entiendan slash commands en formato Markdown sin frontmatter (modelo legacy de Claude Code pre-2026), porque el estándar Agent Skills es el horizonte común de todos los agentes mainstream.

```python
# src/bookwright/integrations/base.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

@dataclass(frozen=True)
class IntegrationOption:
    """Opción declarativa de una integración (pasada vía --integration-options)."""
    flag: str                    # ej. "--skills-dir"
    required: bool = False
    help: str = ""
    type: str = "flag"           # "flag" | "string"
    default: str | None = None

class IntegrationBase(Protocol):
    """Interfaz mínima que toda integración debe satisfacer."""
    key: str                     # ej. "claude", "generic"
    config: dict                 # metadata: name, requires_cli, install_url
    default_skills_dir: str      # ej. ".claude/skills", ".agents/skills"

    @classmethod
    def options(cls) -> list[IntegrationOption]: ...

    def resolve_skills_dir(self, parsed_options: dict | None) -> Path: ...

    def setup(
        self,
        project_root: Path,
        manifest: "Manifest",
        parsed_options: dict | None = None,
    ) -> None:
        """Ejecuta el scaffolding específico de esta integración."""

    def teardown(self, project_root: Path) -> None:
        """Limpieza en uninstall (post-v0)."""

class SkillsIntegration(IntegrationBase):
    """Base para agentes que consumen Agent Skills (agentskills.io).
    Por defecto, todas las integraciones de Bookwright v0 heredan de esta clase.
    Implementación común de setup() que materializa los commands a SKILL.md.
    """

    # Capacidades opcionales del estándar que la integración aprovecha
    supports_dynamic_context: bool = False   # !`shell` en SKILL.md (Claude Code)
    supports_subagents: bool = False         # subagent execution (Claude Code)
    supports_tool_restrictions: bool = False # tools: list en frontmatter
```

### 11.2 Las dos integraciones de v0

**`ClaudeIntegration(SkillsIntegration)`** en `src/bookwright/integrations/claude/__init__.py`:

```python
from pathlib import Path
from ..base import SkillsIntegration

class ClaudeIntegration(SkillsIntegration):
    key = "claude"
    config = {
        "name": "Claude Code",
        "install_url": "https://docs.claude.com/claude-code",
        "requires_cli": True,            # Skills locales (.claude/skills/) requieren Claude Code
        "context_file": "CLAUDE.md",     # gestionado por Bookwright
    }
    # Nota: claude.ai web también soporta Agent Skills, pero por upload manual del
    # SKILL.md en la conversación. No lee automáticamente .claude/skills/ del filesystem.
    # Un usuario de claude.ai web puede subir los SKILL.md generados, pero queda fuera
    # del flujo automatizado de bookwright init.
    default_skills_dir = ".claude/skills"

    # Claude Code soporta extensiones sobre el estándar Agent Skills
    supports_dynamic_context = True
    supports_subagents = True
    supports_tool_restrictions = True

    @classmethod
    def options(cls):
        return []   # No requiere opciones específicas en v0

    def resolve_skills_dir(self, parsed_options=None) -> Path:
        return Path(self.default_skills_dir)

    def setup(self, project_root, manifest, parsed_options=None):
        # 1. Generar SKILL.md desde resources/commands/ en .claude/skills/<cmd>/
        # 2. Escribir/actualizar sección gestionada en CLAUDE.md (context_file)
        ...
```

**`GenericIntegration(SkillsIntegration)`** en `src/bookwright/integrations/generic/__init__.py`:

```python
from pathlib import Path
from ..base import SkillsIntegration, IntegrationOption

class GenericIntegration(SkillsIntegration):
    key = "generic"
    config = {
        "name": "Generic (Agent Skills standard)",
        "install_url": "https://agentskills.io",
        "requires_cli": False,
    }
    # Convención estándar usada por Codex CLI, Cursor, y otros agentes neutros
    default_skills_dir = ".agents/skills"

    # No asume capacidades extendidas — solo el estándar puro
    supports_dynamic_context = False
    supports_subagents = False
    supports_tool_restrictions = False

    @classmethod
    def options(cls):
        return [
            IntegrationOption(
                flag="--skills-dir",
                type="string",
                required=False,
                default=".agents/skills",
                help="Directorio donde escribir las SKILL.md. "
                     "Default: .agents/skills (estándar Codex/Cursor). "
                     "Alternativas comunes: .cursor/skills, .github/skills.",
            ),
        ]

    def resolve_skills_dir(self, parsed_options=None) -> Path:
        if parsed_options and "skills_dir" in parsed_options:
            return Path(parsed_options["skills_dir"])
        return Path(self.default_skills_dir)

    def setup(self, project_root, manifest, parsed_options=None):
        skills_dir = project_root / self.resolve_skills_dir(parsed_options)
        # Generar SKILL.md desde resources/commands/ en skills_dir/<cmd>/
        # No usar features extendidas (dynamic context, subagents) ya que generic
        # no garantiza que el agente las soporte
        ...
```

> **Nota sobre `--skills-dir` vs Spec Kit `--commands-dir`.** Bookwright renombra deliberadamente la opción de `GenericIntegration` a `--skills-dir` porque es skills-only. No confundir con el `--commands-dir` que Spec Kit usa en su propio `generic` integration: ese flag existe porque Spec Kit aún soporta el camino legacy de commands. Para alguien familiarizado con Spec Kit, conviene recordar que en Bookwright todo va a `skills_dir/<command>/SKILL.md` — no hay analogía con `commands/<command>.md`.

### 11.3 Registro central

```python
# src/bookwright/integrations/__init__.py
from .claude import ClaudeIntegration
from .generic import GenericIntegration
from .base import SkillsIntegration

INTEGRATION_REGISTRY: dict[str, type[SkillsIntegration]] = {}

def _register_builtins() -> None:
    for cls in (ClaudeIntegration, GenericIntegration):
        INTEGRATION_REGISTRY[cls.key] = cls

_register_builtins()

def get(key: str) -> type[SkillsIntegration]:
    if key not in INTEGRATION_REGISTRY:
        raise UnknownIntegrationError(key)
    return INTEGRATION_REGISTRY[key]
```

### 11.4 Generación de SKILL.md desde commands

Bookwright toma cada `.md` de `resources/commands/` y produce un `SKILL.md` válido según [agentskills.io/specification](https://agentskills.io/specification):

```markdown
---
name: bookwright-constitution
description: |
  Destila la constitution narrativa de un libro desde un brief o conversación previa.
  Activar cuando el usuario indique que quiere iniciar un libro, defina el pacto
  narrativo, o pase un dump de conversación con su idea inicial. NO activar para
  edición de manuscrito ni para generación de capítulos.
license: Apache-2.0
metadata:
  author: bookwright
  version: "0.1.0"
---

# bookwright-constitution

[cuerpo del command original, con substituciones aplicadas]
```

**Requisitos del estándar Agent Skills que Bookwright respeta:**

- `name`: < 64 chars, lowercase alphanumeric/hyphens. Debe coincidir con el nombre del directorio padre (`bookwright-constitution/SKILL.md`).
- `description`: < 1024 chars. Debe ser precisa con boundaries claros, porque es lo único que el agente ve antes de decidir invocar el skill. Bookwright enriquece la `description` del frontmatter del command source con triggers explícitos antes de escribirla.
- `license`: heredado de Bookwright (Apache-2.0). Permite a usuarios redistribuir sus proyectos sin fricción.
- `metadata.version`: vinculada a la versión del CLI que generó el skill.

**Reglas operativas:**

- La lógica enriquecedora de `description` vive en `src/bookwright/integrations/base.py` como diccionario `SKILL_DESCRIPTIONS` (patrón idéntico a Spec Kit, ver `src/specify_cli/__init__.py:1059-1069`).
- En el cuerpo se mantiene el token `{ARGS}` → `$ARGUMENTS` por convención de la mayoría de agentes. Las invocaciones del CLI Bookwright se escriben inline (ej. `bookwright graph build --json`); no hay sustitución de paths a wrappers.
- La operación es **idempotente**: si ya existe un `SKILL.md` en `<skills_dir>/<command>/SKILL.md`, no se sobrescribe (preserva customizaciones del usuario). Esto sigue el comportamiento de Spec Kit en `install_ai_skills()`.

### 11.5 Progressive disclosure (capacidad del estándar que Bookwright aprovecha)

El estándar Agent Skills define tres tiers de carga:

- **Tier 1 (~100 tokens)**: solo `name` + `description`, cargados al inicio para todos los skills.
- **Tier 2 (<5000 tokens)**: cuerpo completo del SKILL.md, cargado cuando el agente decide invocar el skill.
- **Tier 3 (as needed)**: archivos auxiliares en `scripts/`, `references/`, `assets/`, cargados solo al referenciarse.

Bookwright estructura cada skill para aprovechar esto:

```
.claude/skills/bookwright-constitution/
├── SKILL.md               # Tier 1 + Tier 2 (instrucciones core)
└── references/
    ├── golem-character.md # Tier 3: explicación del módulo Character cuando aplica
    └── propp-functions.md # Tier 3: vocabulario Propp cuando aplica
```

Esto significa que el `SKILL.md` principal puede ser corto (<2000 tokens) y solo expandirse cuando se necesita explicar GOLEM o vocabularios específicos. Bookwright v0 no usa el subdirectorio `scripts/` del estándar: el CLI `bookwright` ya es ejecutable y los SKILL.md lo invocan directamente.

### 11.6 Añadir una integración post-v0

Proceso para añadir, por ejemplo, soporte de Cursor con sus extensiones específicas:

1. Crear `src/bookwright/integrations/cursor/__init__.py` con `CursorIntegration(SkillsIntegration)`.
2. Declarar `key`, `config`, `default_skills_dir` (probablemente `.cursor/skills`).
3. Declarar qué capacidades soporta (`supports_dynamic_context = True` si lo soporta Cursor).
4. Override `setup()` solo si necesita lógica extra (escribir un `.cursorrules` por ejemplo).
5. Añadir al `_register_builtins()`.
6. Test en `tests/integrations/test_cursor.py` siguiendo el patrón de los tests existentes.

Si la integración usa una convención de directorio idéntica a una que ya existe (ej. Codex usa `.agents/skills/`), basta con que el usuario use `--integration generic` con su default. No es necesario crear una integración específica salvo que añada extensiones.

---

## 12. Sistema de Indexers

### 12.1 Protocol

```python
# src/bookwright/indexers/base.py
from typing import Protocol, Iterable, Any
from pathlib import Path

class Indexer(Protocol):
    """Interfaz que cualquier motor de grafo debe implementar."""

    def load(self, ttl_path: Path) -> None:
        """Carga el grafo desde un archivo Turtle."""

    def save(self, ttl_path: Path) -> None:
        """Serializa el grafo a Turtle."""

    def add_triple(self, s: str, p: str, o: str | int | float) -> None:
        """Añade un triple."""

    def query(self, sparql: str) -> Iterable[dict[str, Any]]:
        """Ejecuta una query SPARQL."""

    def construct(self, sparql: str) -> "Indexer":
        """Ejecuta un CONSTRUCT, devuelve sub-grafo."""

    def count(self) -> int:
        """Número de triples."""
```

### 12.2 `RdflibIndexer` (v0 default)

Implementación con `rdflib`:

- `load`: `rdflib.Graph().parse(path, format="turtle")`.
- `save`: `graph.serialize(destination=path, format="turtle")`.
- `query`: usa SPARQLWrapper interno de rdflib.
- Performance esperado: aceptable para grafos <10k triples (la mayoría de libros).

### 12.3 `GrafeoIndexer` (stub v0, implementación post-v0)

Misma interfaz. Implementación posterior cuando:
- Algún proyecto Bookwright real demuestre que rdflib es bottleneck.
- O un usuario quiera explícitamente vector search HNSW.

El cambio será transparente para commands, validators y el resto del CLI.

### 12.4 Selección del indexer

El indexer se elige en `manifest.toml > [bookwright] indexer`. El factory en `indexers/__init__.py` resuelve el nombre a la clase concreta.

---

## 13. Sistema de Validación

### 13.1 Protocol

```python
# src/bookwright/validation/base.py
from typing import Protocol
from dataclasses import dataclass
from enum import Enum

class Severity(str, Enum):
    error = "error"
    warning = "warning"
    info = "info"

@dataclass
class Violation:
    validator: str
    severity: Severity
    message: str
    source: str | None  # ej. "manuscript/cap-04.md:42"
    triples: list[tuple[str, str, str]] | None  # triples implicados

class Validator(Protocol):
    name: str
    severity_default: Severity

    def validate(self, project, indexer) -> list[Violation]:
        """Devuelve lista de violaciones. Vacía si OK."""
```

### 13.2 Validators built-in en v0

| Validator | Severity default | Qué valida |
|---|---|---|
| `temporal` | error | Que los eventos en la timeline sean consistentes (no contradicciones). |
| `character_presence` | error | Que los personajes mencionados en manuscrito existan en la bible y viceversa. |
| `setting_continuity` | warning | Que los settings se mantengan coherentes (ej. clima, descripciones). |
| `focalization` | warning | Que la persona narrativa declarada en constitution se respete. |

### 13.3 Registry

Validators se autodescubren en `bookwright.validation` y se filtran por `manifest.toml > [validators].enabled`. Validators custom del usuario en `<proyecto>/.bookwright/validators/*.py` se cargan dinámicamente.

---

## 14. Stack tecnológico

### 14.1 Dependencias principales

```toml
# pyproject.toml (extracto)
[project]
name = "bookwright-cli"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "rich>=13.7",
    "rdflib>=7.0",
    "pydantic>=2.5",
    "tomlkit>=0.12",
    "jinja2>=3.1",
    "python-slugify>=8.0",
    "platformdirs>=4.2",
    "uuid-utils>=0.16",
]

[project.optional-dependencies]
grafeo = ["grafeo>=0.5"]   # opcional, futuro

[project.scripts]
bookwright = "bookwright.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build]
include = ["src/bookwright", "src/bookwright/resources"]

[tool.hatch.version]
path = "src/bookwright/__init__.py"
```

### 14.2 Dev dependencies

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

### 14.3 Configuración de tooling

- **Ruff**: line-length 100, target-version py311, todos los rulesets razonables activos (E, W, F, I, B, UP, RUF, SIM, PL).
- **Mypy**: strict mode. `disallow_untyped_defs`, `disallow_any_generics`, `warn_return_any`.
- **Pytest**: coverage mínimo 80% en v0, escalando a 90% en v0.3.
- **Pre-commit**: hooks para ruff (lint+format), mypy, validar TOML, check-yaml.

### 14.4 Instalación y distribución

- Distribución vía PyPI: `pipx install bookwright-cli` o `uv tool install bookwright-cli`.
- Modo desarrollo: `uv tool run --from git+https://github.com/<owner>/bookwright.git bookwright init my-book`.
- Versionado semver. Tags `v0.1.0`, `v0.2.0`, etc.

---

## 15. Plan de implementación

### 15.1 M0 — Esqueleto, integrations base, y `init` (semana 1)

**Objetivo:** `bookwright init` funcional, con las dos integraciones de v0 (`claude`, `generic`) generando Agent Skills, proyecto generado correcto, sin commands ni validación todavía.

- Scaffolding del repo (todo lo de § 6).
- `pyproject.toml`, `uv.lock`, pre-commit, CI básico (tests + lint).
- `cli.py` con Typer registrando los comandos.
- `commands/init.py`: lee `resources/templates/`, resuelve integración, delega scaffolding al plugin. Maneja `--here`, `--force`, `--no-git`, `--integration`, `--integration-options`.
- `core/manifest.py`: modelo Pydantic completo, parser, validador, con bloque `[integration]` (`key`, `skills_dir`, `options`).
- `core/paths.py`: convenciones.
- `integrations/base.py`: `SkillsIntegration` (única clase base en v0), `IntegrationOption`, diccionario `SKILL_DESCRIPTIONS`.
- `integrations/__init__.py`: `INTEGRATION_REGISTRY` + `_register_builtins()`.
- `integrations/claude/__init__.py`: `ClaudeIntegration` con `default_skills_dir = ".claude/skills"`.
- `integrations/generic/__init__.py`: `GenericIntegration` con `default_skills_dir = ".agents/skills"` y opción `--skills-dir`.
- Templates mínimos en `resources/templates/`: manifest.toml.tmpl, constitution.md.tmpl, readme.md.tmpl, gitignore.tmpl.
- Alias de deprecación: `--ai` → `--integration` con warning (un ciclo de release). Error claro si se pasan `--ai-skills` o `--ai-commands-dir`.
- Tests unit + integration de `init` con las dos integraciones.

**Criterio de aceptación:**
- `bookwright init my-book` (default `--integration claude`) produce `.claude/skills/` y NO produce `.claude/commands/`.
- `bookwright init my-book --integration generic` produce `.agents/skills/` por defecto.
- `bookwright init my-book --integration generic --integration-options="--skills-dir .cursor/skills"` produce `.cursor/skills/`.
- `cat manifest.toml` muestra el bloque `[integration]` correcto con el `skills_dir` reflejando lo anterior.
- `bookwright init my-book --ai claude` funciona pero emite un warning de deprecación.
- `bookwright init my-book --ai-skills` falla con error explicativo.
- `git status` muestra commit inicial limpio en todos los casos.

### 15.2 M1 — Modelo GOLEM + indexer rdflib (semana 2)

**Objetivo:** capacidad de construir y consultar el grafo de un proyecto.

- `golem/namespaces.py`, `golem/base.py`, `golem/modules/*`.
- `resources/schemas/golem-1.0/`: copiar el TTL de GOLEM upstream, validar.
- `indexers/base.py`, `indexers/rdflib_indexer.py`.
- `commands/graph.py`: `build`, `query`.
- `io/turtle.py`, `io/bible.py`, `io/manuscript.py`.
- Tests unit del indexer, tests integration de `graph build`.

**Criterio de aceptación:** sobre la fixture `tiny-novel/`, `bookwright graph build` produce un `graph.ttl` consistente, y `bookwright graph query "SELECT ?c WHERE { ?c a golem:G1_Character }"` devuelve los personajes esperados.

### 15.3 M2 — Commands materializados como Agent Skills (semana 3)

**Objetivo:** los 10 commands de v0 disponibles como Agent Skills (formato agentskills.io) en ambas integraciones.

- Redactar los 10 commands en `resources/commands/` (constitution, bible, outline, scenes, draft, synopsis, clarify, analyze, continuity, checklist).
- Redactar los templates de bible expandidos en `resources/templates/bible/` (los inspirados en el preset: pov-structure, themes, locations, research, glossary, subplots).
- `integrations/base.py::SKILL_DESCRIPTIONS`: descripciones enriquecidas con triggers para cada command, optimizadas para activación implícita.
- `SkillsIntegration.setup()`: lógica completa de materialización de commands a SKILL.md según el estándar agentskills.io (frontmatter válido, name = directory name, description < 1024 chars, license, metadata.version).
- Lógica de progressive disclosure: cuando un command necesita explicar GOLEM o vocabularios, en lugar de inflar el SKILL.md se referencian archivos en `references/`.
- Los SKILL.md invocan el CLI `bookwright` directamente (`bookwright graph build --json`, `bookwright validate --json`, etc.). No hay wrappers Python intermedios.
- Tests E2E de cada command sobre fixtures.

**Criterio de aceptación:**
- Desde Claude Code abierto en un proyecto inicializado, `/bookwright-constitution` invocado con un brief produce un `bible/constitution.md` válido.
- `/bookwright-bible` produce los archivos de bible incluyendo los nuevos (themes, glossary, etc.).
- Encadenamiento completo hasta `/bookwright-draft` funciona en la fixture `tiny-novel/`.
- Validar cada SKILL.md contra la spec de agentskills.io: `name` matchea directorio, `description` < 1024 chars, body < 5000 tokens.
- El mismo encadenamiento funciona desde Codex CLI (probando que `--integration generic` produce skills realmente portables).

### 15.4 M3 — Validación (semana 4)

**Objetivo:** los 4 validators built-in + `bookwright validate` + el command `/bookwright-continuity` apoyado en ellos.

- `validation/base.py`, `validation/registry.py`.
- Los 4 validators built-in (temporal, character_presence, setting_continuity, focalization).
- `commands/validate.py`: ejecuta el registry, formatea output (texto + JSON).
- `/bookwright-continuity` invoca `bookwright validate` y formatea el resultado para el usuario.
- Tests unit de cada validator.
- Documentación de cómo añadir validators custom.

**Criterio de aceptación:** sobre fixtures con violaciones inyectadas, `bookwright validate --json` detecta exactamente las violaciones esperadas. `/bookwright-continuity` sobre `tiny-novel/` con un capítulo inconsistente reporta las violaciones en lenguaje narrativo.

### 15.5 Post-v0 (no incluido en este documento)

- v0.2: sistema de presets (genre packages); commands `bookwright-export`, `bookwright-feedback`, `bookwright-polish`, `bookwright-revise`, `bookwright-query`, `bookwright-status`.
- v0.3: `GrafeoIndexer`, vector search (ChromaDB o equivalente).
- v0.4: soporte multi-integración (Copilot, Gemini, Codex); comandos `bookwright integrate list/install/switch`.
- v0.5: extension system para hooks pre-commit y validators distribuidos.
- v1.0: export a EPUB/PDF (`bookwright-export` con pandoc).

---

## 16. Decisiones explícitas que el agente NO debe re-cuestionar

Estas decisiones se discutieron extensamente en la fase de diseño. Cambiarlas requeriría rehacer secciones enteras. El agente las trata como axiomas:

1. **Python, no Rust ni TypeScript.** Ecosistema de scientific computing y semántica está en Python.
2. **rdflib en v0, no Grafeo.** Grafeo es v0.5 de un único mantenedor; rdflib es maduro y estándar.
3. **GOLEM como ontología.** No diseñar una ontología propia.
4. **Texto plano (Markdown, TOML, Turtle) como fuente de verdad.** No SQLite, no JSON binario, no LevelDB.
5. **Patrón Spec Kit como referencia operacional, sin acoplamiento.** Adoptamos su arquitectura (`INTEGRATION_REGISTRY`, `SkillsIntegration`, formato de command templates, resolución de templates por capas), pero Bookwright es proyecto autónomo. No depende del wheel de `specify-cli`.
6. **Sin scripts shell.** Todo Python, vía Typer.
7. **Solo Agent Skills, no commands legacy.** Bookwright se alinea con Agent Skills (agentskills.io) como formato canónico: progressive disclosure de tres tiers, portabilidad entre Claude Code, Codex, Cursor y Copilot, y validación estructural por estándar abierto. No usamos `.claude/commands/` ni equivalentes; toda la lógica de cada command vive en su SKILL.md.
8. **`.agents/skills/` como default para `--integration generic`.** Es la convención que usan Codex CLI y Cursor, y la más portable entre agentes. No usar `.agents/commands/` (no existe como convención).
9. **Bookwright como toolkit separado de Spec Kit y de su preset `fiction-book-writing`.** No es un preset, no es una extensión. Comparte patrón y se inspira en sus templates, pero es proyecto independiente con licencia propia.
10. **Arquitectura `INTEGRATION_REGISTRY` plugin-based desde el día uno.** No replicar el `AGENT_CONFIG` monolítico que Spec Kit ya está abandonando.

---

## 17. Trabajo relacionado

Bookwright no nace en el vacío. Existen dos referencias técnicas directas cuyas decisiones, código y patrones se aprovechan deliberadamente:

### 17.1 Spec Kit (github/spec-kit)

**Relación:** inspiración arquitectónica directa. Bookwright aplica el patrón **Spec-Driven Development** al dominio narrativo, renombrado como Document-Driven Authoring para que las metáforas encajen.

**Lo que Bookwright adopta de Spec Kit:**

- La estructura `.specify/` → `.bookwright/` (memory, templates, init-options.json). Sin `scripts/`: el CLI Bookwright es Python puro y los SKILL.md lo invocan directo.
- El formato de command templates con YAML frontmatter + tokens substituibles (en Bookwright solo `{ARGS}`; `{SCRIPT}` desaparece porque no hay wrappers).
- La resolución de templates por capas (overrides → presets → extensions → core).
- La arquitectura plugin-based de integrations (`INTEGRATION_REGISTRY`, `SkillsIntegration`, `IntegrationOption`). Nota: Bookwright solo necesita `SkillsIntegration` porque todas las integraciones de v0 producen Agent Skills (commands legacy ya no es opción).
- El patrón de generación de SKILL.md desde command templates con `SKILL_DESCRIPTIONS` enriquecidas.
- El contrato CLI ↔ agente vía JSON sobre stdout.
- El patrón mental de constitution como gobernanza.

**Lo que Bookwright NO adopta:**

- El acoplamiento al ciclo de release de Spec Kit (Bookwright es proyecto independiente).
- El soporte de bash + powershell (Bookwright es Python puro).
- El sistema completo de extensions (lo dejamos para post-v0).
- El download de templates desde GitHub releases (Bookwright empaqueta dentro del wheel).
- La nomenclatura software-céntrica (`specify`, `plan`, `tasks`, `implement`).

**Licencia de Spec Kit:** MIT. Compatible con Bookwright (Apache-2.0). No hay reutilización de código fuente sin atribución; lo que se reutiliza son patrones de diseño documentados públicamente.

### 17.2 Preset `fiction-book-writing` para Spec Kit (adaumann/speckit-preset-fiction-book-writing)

**Relación:** intento previo de aplicar Spec Kit a producción narrativa, restringido a ficción y operando como overlay sobre Spec Kit. Tracción baja (4 stars, 1 autor) pero inventario de templates valioso.

**Por qué Bookwright no es una iteración de este preset:**

- Solo cubre ficción. Bookwright cubre también ensayo, memoria y no-ficción narrativa.
- No tiene modelo de dominio formal. Todo es prosa interpretada por el LLM. Bookwright añade grafo (GOLEM) + validators ejecutables.
- Sin trazabilidad de inferencias. Bookwright modela `E13_Attribute_Assignment` para distinguir manuscrito de inferencia.
- Atado a Spec Kit y su refactor. Bookwright es independiente.

**Lo que Bookwright toma del preset (con crédito en CHANGELOG):**

- El inventario de documentos canónicos: synopsis (corta+larga), themes con motif registry, locations con sensory anchors, glossary, research, subplots, pov-structure.
- El comando `continuity` (post-draft) como complemento a `analyze` (pre-draft).
- La idea de incluir RAG vector search en el indexer (futuro v0.3).
- El patrón de export con pandoc (futuro v1.0).

**Licencia del preset:** MIT. Permite reutilización de estructura de templates con atribución.

**Posible interoperabilidad futura (v0.4+):** que `bookwright` pueda importar un proyecto inicializado con el preset y construir el grafo GOLEM a partir de sus archivos. Esto sería un gancho de adopción para usuarios que ya estén en ese ecosistema.

### 17.3 Agent Skills open standard (agentskills.io)

**Relación:** estándar de facto que Bookwright cumple para garantizar portabilidad de los skills generados entre agentes IA mainstream.

**Origen:** desarrollado por Anthropic, introducido públicamente el 16 de octubre de 2025, publicado como estándar abierto el 18 de diciembre de 2025. Mantenido en `github.com/agentskills/agentskills` (Apache-2.0 + CC-BY-4.0). El ecosistema más amplio está coordinado por la Agentic AI Foundation bajo Linux Foundation.

**Lo que Bookwright adopta del estándar:**

- Formato `SKILL.md` con frontmatter YAML (`name`, `description`, opcional `license`, `metadata`).
- Directorio por skill con subdirectorios opcionales (`scripts/`, `references/`, `assets/`).
- Progressive disclosure de tres tiers (metadata → instructions → resources).
- Constraints de validación: `name` < 64 chars y debe matchear el directorio padre; `description` < 1024 chars.

**Adopción del estándar en la industria** (relevante porque garantiza la portabilidad de los proyectos Bookwright):

| Agente | Directorio de skills | Estado |
|---|---|---|
| Claude Code | `.claude/skills/` | Native (Anthropic original) |
| Codex CLI (OpenAI) | `.agents/skills/` | Native |
| Cursor | `.agents/skills/` o `.cursor/skills/` | Native |
| GitHub Copilot (VS Code) | `.github/skills/` | Native |
| Gemini CLI | varía | Compatible |
| Spring AI | (Java/Spring) | Compatible |

**Implicación para Bookwright:** un proyecto inicializado con `--integration generic` (que usa `.agents/skills/`) es portable entre Codex, Cursor y otros sin reconfiguración. Un proyecto inicializado con `--integration claude` aprovecha las extensiones específicas de Claude Code (dynamic context injection, subagents) que no están en el estándar puro.

### 17.4 Otras referencias menores

- **GOLEM upstream** (GOLEM-lab/golem-ontology): la ontología en sí. Apache-2.0. Bookwright congela una versión y la distribuye en `resources/schemas/`.
- **Grafeo** (grafeo.dev): considerado para v0 como motor de grafo, descartado por madurez. Vuelve como opción en v0.3 vía `GrafeoIndexer`.

---

## 18. Apéndice A — Glosario de términos GOLEM

| Término | Definición |
|---|---|
| **Character-Stoff** (G0) | La versión "platónica" de un personaje, agregando todas sus variantes posibles a través de obras. |
| **Character** (G1) | Personaje narrativo concreto en una obra. Subclase de social object agentivo. |
| **Object** (G16) | Objeto narrativo no-agentivo (con excepciones: objetos mágicos pueden ser agentivos). |
| **Character Feature** (G17) | Atributo de un personaje (físico, psicológico, biográfico). |
| **Textual Feature** (G18) | Atributo del texto (focalización, POV, registro). |
| **Social Relationship** (G4) | Relación social entre personajes, reificada como entidad. |
| **Relationship Role** (G6) | Rol funcional dentro de una relación (amigo, amante, rival). |
| **Narrative Event** (G5) | Evento narrativo, perdurante. Cambio de estado o proceso. |
| **Psychological State** (G3) | Estado mental de un personaje, estativo. |
| **Setting** (G12) | Universo narrativo en el que ocurre la obra. |
| **Narrative Location** (G13) | Localización concreta dentro del setting. |
| **Narrative-Stoff** (G14) | Material narrativo abstracto, base para múltiples narraciones. |
| **Narrative Unit** (G9) | Unidad mínima de estructura narrativa (un hilema). |
| **Narrative Function** (G10) | Función de una unidad (función Proppiana, motivo, etc.). |
| **Narrative Role** (G11) | Rol de un personaje en la narrativa (héroe, villano, mentor). |
| **Narrative Sequence** (G7) | Secuencia de unidades (fabula, syuzhet, hilema-sequence). |
| **Fandom** (G15) | Comunidad alrededor de una obra (no central para Bookwright v0). |
| **E13_Attribute_Assignment** | Patrón CIDOC CRM para reificar la afirmación de un atributo. Base del módulo Inference. |
| **E55_Type** | Patrón CIDOC CRM para enchufar vocabularios controlados sin extender el esquema. |

---

## 19. Apéndice B — Referencias

- **GOLEM**: Pianzola, F., Cheng, L., Pannach, F., Yang, X., & Scotti, L. (2025). *The GOLEM Ontology for Narrative and Fiction*. Humanities 14(10):193. DOI: 10.3390/h14100193. Repo: github.com/GOLEM-lab/golem-ontology
- **Agent Skills standard**: agentskills.io. Spec: agentskills.io/specification. Repo: github.com/agentskills/agentskills (Apache-2.0).
- **Claude Code Skills docs**: code.claude.com/docs/en/skills. Importante: documenta que slash commands han sido fusionados con skills desde enero de 2026.
- **Spec Kit**: github.com/github/spec-kit. DeepWiki: deepwiki.com/github/spec-kit. Issue #1924 (refactor Agents→Integrations).
- **Spec Kit `AGENTS.md`** (guía de cómo añadir una integración): github.com/github/spec-kit/blob/main/AGENTS.md
- **Fiction-book preset**: github.com/adaumann/speckit-preset-fiction-book-writing (MIT, v1.8.1).
- **Codex CLI Skills docs**: developers.openai.com/codex/skills (referencia para `.agents/skills/`).
- **VS Code Agent Skills docs**: code.visualstudio.com/docs/copilot/customization/agent-skills
- **CIDOC CRM**: ISO 21127:2023. cidoc-crm.org
- **LRMoo**: IFLA Library Reference Model object-oriented. iflastandards.info
- **DOLCE**: Descriptive Ontology for Linguistic and Cognitive Engineering. www.loa.istc.cnr.it/dolce/overview.html
- **rdflib**: rdflib.readthedocs.io
- **Typer**: typer.tiangolo.com
- **Grafeo**: grafeo.dev (motor de grafo opcional, futuro v0.3).

---

**Fin del documento.**
