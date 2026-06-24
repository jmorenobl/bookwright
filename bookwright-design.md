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
- **Consistencia narrativa verificable**: el grafo derivado del manuscrito y la bible permite chequeos automáticos (continuidad temporal, presencia de personajes, focalización, anclas históricas si las hay). Las "anclas históricas" dejan de ser una aspiración y se materializan en el sistema de investigación y verificación de § 20.
- **Investigación como parte del proceso**: escribir no-ficción o ficción documentada exige investigar (fuentes oficiales, en idioma original, contrastando procedencias nacionales). Bookwright no busca por el autor —eso lo hace el agente— pero estructura la investigación, la ancla al grafo y la hace verificable contra el manuscrito. Ver § 20.

### 1.2 No-objetivos (explícitos)

- **No es un editor de texto**. No reemplaza a Obsidian, Scrivener, VS Code. El usuario edita los `.md` en su editor favorito.
- **No genera la novela**. Asiste destilación, validación y refinamiento. El borrador final lo escribe el autor.
- **No publica**. La exportación a EPUB/PDF/print queda fuera de scope de v0. Hay hooks para ello en el diseño pero no se implementa en v0.
- **No es un preset de Spec Kit**. Comparte patrón y código heredado/inspirado, pero es una herramienta separada con identidad propia. La razón: el dominio diverge demasiado y la audiencia (escritores) no debe conocer Spec Kit.
- **No usa Grafeo**. El motor de grafo es `rdflib`, de forma permanente. `GrafeoIndexer` queda descartado (ver § 15.5); la búsqueda vectorial de v0.4 se implementará desacoplada, sobre `rdflib` + un vector store (ChromaDB o equivalente).
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
- Cuando GOLEM publique una versión nueva, se añade una carpeta `golem-{nueva}/` sin tocar la anterior. El usuario migra explícitamente con `bookwright migrate-schema`. El `{version}` del directorio (y por tanto el valor de `schema_version`) sigue la versión de GOLEM upstream, no un versionado propio de Bookwright.
- v0 congela GOLEM **1.1**, bajo el selector `golem-1.1`. Nota de procedencia: la única serialización Turtle legible por máquina de GOLEM vive en la rama `main` del repositorio upstream (`golem/golem_v1-1.ttl`, `owl:versionInfo "1.1"`); el *release tag* `v1.0` contiene únicamente documentación HTML, sin TTL. La procedencia exacta (repo + commit + `versionIRI`) se registra en `version.json` junto al TTL congelado.

### 4.4 Vocabularios controlados

GOLEM proporciona el patrón `E55_Type` para enchufar vocabularios sin extender el esquema. Bookwright incluye en v0:

- `propp.ttl` — funciones Proppianas y dramatis personae.
- `greimas.ttl` — modelo actancial de Greimas.
- `booker-seven-plots.ttl` — los siete plots básicos.
- `essay-structures.ttl` — estructuras retóricas para no-ficción (tesis, argumento, contraargumento, etc.).
- `sources.ttl` — tipos de Fuente (primaria, secundaria, oficial, académica, periodística, testimonial) y niveles de fiabilidad para el sistema de investigación, más las propiedades `bw:` que reifican Fuente/Hallazgo/Ancla sobre `E13_Attribute_Assignment`. Ver § 20.8. (Añadido en v0.2.)

Los usuarios pueden añadir vocabularios propios en `<proyecto>/.bookwright/vocabularies/`.

**Tipado fatal vs. blando — el principio (iteración 047, issue #1 track B).** Un
valor de vocabulario no reconocido se trata según rompa o no la lógica posterior,
no por uniformidad superficial:

- En **investigación** (§ 20), un `type`/`reliability` inválido es **fatal**: lo
  rechaza con un mensaje que enumera los valores válidos, porque alimenta la
  compuerta `factual_anchor` (§ 20.5) — un valor inválido envenena un juicio que
  sí gobierna el verde de CI.
- En el **tipado Propp/Greimas** de `graph build`, un término no reconocido es
  **metadato descriptivo**: la única consecuencia es que el nodo se acuña **sin**
  `crm:P2_has_type`. Eso no rompe ninguna lógica posterior (ningún validador
  depende de la presencia de ese enlace), así que el término no reconocido emite
  solo un **aviso no fatal** de `graph build` que enumera los términos válidos del
  vocabulario activo, el nodo se ingiere igual (untyped) y ni el build aborta ni
  cambia su código de salida. Cerrado para el *tipado*, abierto para la *autoría*.

El principio rector: **fatal ⇔ un valor inválido rompe lógica posterior**. La
ausencia de un `P2_has_type` no rompe nada; la enumeración de términos válidos se
deriva del propio vocabulario en el render, nunca se desnormaliza en el registro.

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
| Secuencia narrativa (`G7_Narrative_Sequence`) | `narrative-sequence` | slug |
| Aserción de atributo (`E13_Attribute_Assignment`) | `assertion` | UUIDv7 |
| Fuente de investigación (`source`, v0.2) | `source` | slug |
| Hallazgo (`finding`, v0.2 — aserción) | `finding` | UUIDv7 |
| Ancla (`anchor`, v0.2 — aserción) | `anchor` | UUIDv7 |

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
| `bookwright status` | Computa el estado derivado del proyecto y las acciones recomendadas (§ 21.4). | `bookwright status --json` |
| `bookwright focus` | Lee/escribe el foco autoral del proyecto (§ 21.3). | `bookwright focus set --target "arco de Berlín"` |
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
| `--script` | choice | auto | `sh` o `ps`. Detecta por SO si no se indica. Reservado para futuro (en v0 no hay scripts auxiliares: los SKILL.md invocan el CLI `bookwright` directamente). |

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

### 5.4 Resolución de templates (2 capas)

Cuando un command necesita un template, lo resuelve en orden:

1. **Overrides**: `.bookwright/templates/overrides/{name}` (personalización del autor)
2. **Core**: `.bookwright/templates/{name}` (default)

Las capas de presets y extensions que figuraban en versiones anteriores quedan
descartadas junto con esos sistemas (ver § 15.5).

Función `resolve_template()` en `src/bookwright/core/templates.py`, idiomática Python (no bash como Spec Kit).

---

## 6. Estructura del repo de Bookwright (el toolkit)

```
bookwright/
├── README.md
├── LICENSE                              # EUPL-1.2
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
│       ├── indexers/                    # motor de grafo (rdflib, permanente)
│       │   ├── __init__.py
│       │   ├── base.py                  # Indexer Protocol (mantiene la puerta abierta a otros motores)
│       │   └── rdflib_indexer.py        # único motor; GrafeoIndexer descartado (§ 15.5)
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
│           │   └── golem-1.1/
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
│           │   │   ├── research/                 # ← investigación (v0.2, § 20.7)
│           │   │   │   ├── _index.md.tmpl         #     mapa de temas + preguntas abiertas
│           │   │   │   ├── sources.md.tmpl        #     registro de Fuentes con procedencia
│           │   │   │   └── topic.md.tmpl          #     hallazgos + anclas por tema
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
│           │   ├── bookwright-checklist.md
│           │   ├── bookwright-research.md           # ← investigación (v0.2, § 20.4)
│           │   └── bookwright-verify.md             # ← verificación vs anclas (v0.2, § 20.6)
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
- **Indexer Protocol**: aísla el motor de grafo detrás de una interfaz, de modo que añadir capacidades (p. ej. la búsqueda vectorial de v0.4) o cambiar de motor no obliga a tocar commands ni validators. En la práctica `rdflib` es el único motor; `GrafeoIndexer` queda descartado (§ 15.5).
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
│   ├── locations/                       # Localizaciones G13 (name:/setting:) + anclas sensoriales (opcional)
│   │   └── *.md
│   ├── objects/                         # Objetos narrativos G16 (name:)
│   │   └── *.md
│   ├── timeline.md
│   ├── relationships.md
│   ├── pov-structure.md                 # Sólo si multi-POV
│   ├── themes.md                        # Motif registry + symbol tracker
│   ├── glossary.md                      # Invented terms + consistency log
│   ├── research/                        # Investigación: hallazgos, fuentes y anclas (§ 20, v0.2)
│   │   ├── _index.md                    #   mapa de temas + preguntas abiertas globales
│   │   ├── sources.md                   #   registro de Fuentes (procedencia)
│   │   └── <tema>.md                    #   hallazgos + anclas por tema
│   ├── subplots.md                      # Beat sheets de subtramas
│   └── graph.ttl                        # Turtle: fuente de verdad del grafo
│
├── outline/                             # Estructura narrativa
│   ├── arcs.md
│   ├── structure.md
│   ├── synopsis.md                      # Corta (250-350) y larga (1000-2000)
│   ├── scenes.md
│   └── units/                           # Unidades G9 (name:/functions:/roles:/sequence:/order:)
│       └── <slug>.md                    #   se indexan (G9/G10; ensamblan G7) — ver § 7.4
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
│   │   ├── overrides/                   # Capa "overrides" de resolución
│   │   ├── manifest.toml.tmpl
│   │   ├── constitution.md.tmpl
│   │   └── ...
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

### 7.2 Ingesta de localizaciones (G13) — wired en iteración 025 (v0.3.2)

`bible/locations/*.md` **se indexa**: cada archivo produce un nodo
`G13_Narrative_Location` de primera clase, espejo de `bible/settings/*.md`. La
identidad sale del frontmatter `name:` (obligatorio; el *slug* deriva de él) y un
`setting:` opcional resuelve contra el índice de settings y emite el cross-ref ya
modelado `dlp:generic-location` (localización → setting). La clase ya era de
primera clase en este documento (tabla de clases § 4.2, generación de URIs § 4.5
con `path_segment` `location`) y existía en el código —modelo `NarrativeLocation`
en `golem/modules/setting.py`, en el cierre congelado `CLASS_IRI`, registrada en
`CONCEPTS`; la iteración 025 añadió **solo la ruta de ingesta**: el *builder* de
`locations/` en `io/bible.py` (extraído junto con los demás a
`io/_bible_builders.py`), la alimentación del `entity_index` de research y la baja
de `NarrativeLocation` del registro de aplazamientos (iteración 024).

**Resolución del `setting:`** (espejo de los participantes de eventos):
ausente / vacío → sin arista, sin aviso; presente y resoluble → arista
`dlp:generic-location`; presente pero sin setting hermano → *soft-miss*
(`UnresolvedParticipant`) con el nodo igualmente construido; no-cadena → el
archivo se omite como frontmatter inservible (FR-013).

**Consecuencia:** una investigación con `bears_on:`/`constrains:` apuntando a
una localización **ahora resuelve** contra su nodo G13 (entró al `entity_index`),
en lugar de quedar como *soft-miss* (`ResearchWarning`, § 20). Las secciones en
prosa sensorial (*Qué se ve / oye / huele / toca*, *Atmósfera dominante*) siguen
siendo prosa humana, no ingerida.

No tocó la ontología congelada (Principio X a salvo: clase y cross-ref ya
reservados) ni requirió enmienda constitucional. El command `/bookwright-bible`
pasó a dar a cada localización frontmatter `name:` (+ `setting:` opcional),
retirando el atajo de v0 ("no se indexa en v0 / sin frontmatter").

### 7.3 Ingesta de objetos (G16) — wired en iteración 026 (v0.3.3)

`bible/objects/*.md` **se indexa**: cada archivo produce un nodo `G16_Object` de
primera clase, espejo directo de `bible/settings/*.md`. La identidad sale del
frontmatter `name:` (obligatorio; el *slug* deriva de él) y la clase es
*identity-only* en v0, igual que `Setting`. La clase ya era de primera clase en
este documento (tabla de clases § 4.2, generación de URIs § 4.2 con
`path_segment` `object`) y existía en el código —modelo `Object` en
`golem/modules/character.py`, en el cierre congelado `CLASS_IRI`, registrada en
`CONCEPTS`; la iteración 026 añadió **solo la ruta de ingesta**: un sexto
`_DirSpec` en el *builder* uno-entidad-por-fichero de `io/_bible_builders.py`, la
alimentación del `entity_index` de research y la baja de `Object` del registro de
aplazamientos (iteración 024).

**Compatibilidad:** ausencia de `bible/objects/` no afecta a nada; un archivo sin
frontmatter se omite como inservible; una colisión de *slug* se rechaza como en
characters/settings. Los objetos entran al `entity_index`, así que una
investigación con `bears_on:`/`constrains:` apuntando a un objeto **ahora
resuelve** contra su nodo G16.

No tocó la ontología congelada (Principio X a salvo: la clase ya estaba
reservada) ni requirió enmienda constitucional. Quedan fuera de este patch los
atributos de objeto más allá de la identidad y los cross-refs de objeto (p. ej.
objeto → personaje portador). El command `/bookwright-bible` pasó a instruir la
creación de fichas de objeto con frontmatter `name:`.

### 7.4 Ingesta de unidades narrativas (G9/G10) y secuencias (G7) — wired en iteraciones 028/029 (v0.4)

`outline/units/*.md` **se indexa**: cada ficha produce una `G9_Narrative_Unit` de
primera clase, el primer árbol fuera de `bible/` que alimenta el grafo. La
identidad sale del frontmatter `name:` (obligatorio; el *slug* deriva de él). Las
`functions:` (lista de nombres) se acuñan como nodos `G10_Narrative_Function`
*identity-only*, deduplicados por *slug* **entre todas las fichas** (la primera
que introduce un *slug* emite su `rdf:type`; las demás lo reutilizan), enlazados
por `crm:P67_refers_to`. Las `roles:` (lista de nombres) **no acuñan nada**:
resuelven por *slug* contra los nodos de rol con alcance de personaje que los
personajes ya materializan (`narrative_roles`), una arista `crm:P67_refers_to` por
cada personaje que juega ese rol. Las clases G9/G10/G11 y ambos cross-refs ya eran
de primera clase en este documento y existían en el código (`golem/modules/
narrative.py`, en el cierre congelado `CLASS_IRI`, registradas en `CONCEPTS`); la
iteración 028 añadió **solo la ruta de ingesta**: un módulo hermano `io/outline.py`
(`map_outline`) que reutiliza el motor genérico de `io/bible.py`, una pasada
`_index_character_roles` que publica el índice de roles en `MapResult`, y la baja
de `NarrativeUnit`/`NarrativeFunction` del registro de aplazamientos (iteración
024).

**Resolución y robustez** (espejo de localizaciones/objetos): ausencia de
`outline/units/` no afecta a nada (grafo idéntico); una ficha sin frontmatter,
con `name:` ausente/vacío/no-cadena, o con `functions:`/`roles:` que no sean
listas de cadenas se omite como inservible (FR-006/007) sin filtrar ninguna
función parcial; una `role:` sin personaje que la juegue es *soft-miss*
(`UnresolvedReference`) con la unidad igualmente construida (sin arista); una
colisión de *slug* de unidad se rechaza como en characters/settings. La prosa del
cuerpo no se indexa.

**Secuencias narrativas G7 (iteración 029).** Las mismas fichas de
`outline/units/` ingieren ahora `G7_Narrative_Sequence` — **sin** directorio
propio (no hay `outline/sequences/`): las secuencias se *ensamblan*, no se
redactan. Una ficha puede declarar dos claves opcionales más, `sequence:` (la
línea argumental a la que pertenece la unidad, por nombre) y `order:` (su posición
entera dentro de esa línea). Tras construir **todas** las fichas, una segunda
pasada agrupa por *slug* de `sequence` y acuña una `NarrativeSequence` por grupo,
cuyos miembros `dlp:proper-part` son las unidades, ordenadas ascendentemente por
`order`. Un `order` ausente coloca el miembro al final, ordenado por su *slug*; un
`order` duplicado se desempata por *slug* (orden total → tupla idéntica entre
*builds*); un `order` sin `sequence` es un aviso *soft* (`UnknownKey "order"`). La
provenance es a nivel de fichero (sin `:line`), espejo de las funciones acuñadas.
La clase G7 y su cross-ref `units`→`dlp:proper-part` ya eran de primera clase
(`golem/modules/narrative.py`, `CLASS_IRI`, `CONCEPTS`); la iteración 029 añadió
**solo el ensamblaje** y dio de baja `NarrativeSequence` del registro de
aplazamientos.

No tocó la ontología congelada (Principio X a salvo: clases y cross-refs ya
reservados) ni requirió enmienda constitucional. Quedan author-only `arcs.md`,
`structure.md`, `synopsis.md` y `scenes.md`. El command `/bookwright-outline` pasó
a instruir la creación de fichas bajo `outline/units/` con frontmatter
`name:`/`functions:`/`roles:` y las claves opcionales `sequence:`/`order:`.

---

## 8. Manifest del proyecto: `manifest.toml`

### 8.1 Spec completa

```toml
# manifest.toml — Contrato entre Bookwright CLI y el proyecto.

[bookwright]
# OBLIGATORIO. Versiones para compatibilidad.
cli_version_min = "0.1.0"
schema_version = "golem-1.1"
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

[focus]
# OPCIONAL. Hilo conductor autorado (§ 21.3). El bloque entero puede no existir;
# cuando existe, `target` y `updated_at` son obligatorios. Lo escribe el CLI
# (`bookwright focus set` / `clear`), que sella `updated_at` en cada escritura;
# editable a mano como cualquier otro bloque.
target = "arco de Berlín"           # qué se está trabajando ahora (texto corto, no vacío)
notes = "cerrar la timeline del cap-04"  # hilos abiertos / decisiones pendientes ("" si ninguno)
updated_at = "2026-06-11"           # fecha ISO 8601 YYYY-MM-DD (sin hora ni zona)
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
| `copilot` | `.github/skills/` | Agent Skills (VS Code) | no planificado |
| `cursor` | `.cursor/skills/` | Agent Skills + extensiones Cursor | no planificado |
| `codex` | `.agents/skills/` | Agent Skills puro | cubierto por `generic` |

Para añadir una integración futura basta con crear `src/bookwright/integrations/<key>/__init__.py` con una clase que herede de `SkillsIntegration` y declare su `skills_dir` y `extensions` (capacidades opcionales del agente que se quieren aprovechar: dynamic context injection, subagents, etc.). El registro central en `integrations/__init__.py::_register_builtins()` la añade a `INTEGRATION_REGISTRY`. Mismo patrón que el documentado en `AGENTS.md` de Spec Kit.

### 10.4 Lista completa de commands en v0

| Command | Input | Output | Fase |
|---|---|---|---|
| `/bookwright-constitution` | Brief / conversación | `bible/constitution.md` | 1. Setup |
| `/bookwright-bible` | Constitution + brief | `bible/characters/*.md`, `bible/settings/*.md`, `bible/locations/*.md`, `bible/objects/*.md`, `bible/timeline.md`, `bible/relationships.md`, `bible/themes.md`, `bible/glossary.md`, `bible/research/_index.md`, `bible/subplots.md`, `bible/pov-structure.md` (si multi-POV), `bible/graph.ttl` | 2. Setup |
| `/bookwright-outline` | Constitution + bible | `outline/arcs.md`, `outline/structure.md`, `outline/synopsis.md`, `outline/units/*.md` | 3. Structure |
| `/bookwright-scenes` | Outline + bible | `outline/scenes.md` | 4. Pre-draft |
| `/bookwright-draft <scene_id>` | Outline + scene | `manuscript/cap-NN.md` (sección de la escena) | 5. Draft |
| `/bookwright-synopsis` | Estado actual | Actualiza `outline/synopsis.md` (corta + larga) | cualquier momento |
| `/bookwright-clarify <artifact?>` | Cualquier artefacto | Lista de preguntas pendientes | cualquier momento |
| `/bookwright-analyze` | Constitution + bible + outline + scenes | Reporte pre-draft de inconsistencias cruzadas | tras 2-4 |
| `/bookwright-continuity` | Manuscrito + bible + grafo | Reporte post-draft: bible compliance, character arcs, timeline coherence | tras 5 |
| `/bookwright-checklist <artifact>` | Un artefacto concreto | Reporte de completitud | cualquier momento |
| `/bookwright-research <tema>` (v0.2) | Tema + constitution + bible | `bible/research/<tema>.md`, fuentes con procedencia, anclas, preguntas abiertas; tríadas al grafo. Ver § 20.4 | 2. Setup / cualquier momento |
| `/bookwright-verify` (v0.2) | Manuscrito + anclas + grafo | Reporte semántico: pasajes que contradicen lo investigado (anacronismos, errores de procedimiento/culturales). Ver § 20.6 | tras 5 |

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
license: EUPL-1.2
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
- `license`: heredado de Bookwright (EUPL-1.2). Permite a usuarios redistribuir sus proyectos sin fricción.
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

### 11.6 Añadir una integración (capacidad latente, no planificada)

> El soporte multi-integración (Copilot, Gemini, Cursor/Codex específicos) queda
> **descartado del roadmap**: el target es Claude Code, y `claude` + `generic`
> cubren el uso (§ 15.5). Esta sección documenta que la arquitectura
> `INTEGRATION_REGISTRY` lo permitiría si alguna vez hiciera falta —no es un
> compromiso de implementación.

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

### 12.3 Búsqueda vectorial (horizonte demand-pulled, sobre rdflib — sin Grafeo)

`GrafeoIndexer` queda **descartado** (no se implementará; ver § 15.5): `rdflib`
es el motor de grafo permanente y cubre los grafos de tamaño libro (<10k triples)
sin problema.

La **búsqueda vectorial sí se mantiene** como capacidad del **horizonte
demand-pulled** (sin versión asignada: se activa solo ante un disparador concreto
—un corpus real multi-libro/serie o un fallo medido de structural-recall en una
skill—, nunca como plomería especulativa), pero
**desacoplada de Grafeo**: se implementa como una capa de recuperación semántica
sobre el corpus (sobre todo `bible/research/` y el manuscrito), usando un vector
store ligero (ChromaDB o equivalente, embebido y en fichero) en paralelo al grafo
rdflib, no como un indexer alternativo. El grafo sigue siendo la fuente de verdad
estructurada; los vectores son un índice secundario reconstruible que vive en
`.bookwright/cache/` (en `.gitignore`). Su coste y viabilidad se analizan en
§ 20.12.

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

class NotEvaluatedKind(str, Enum):
    """Por qué un validador NO evaluó (iteración 044). Vocabulario cerrado de dos
    valores que refleja a `Severity`; el `.value` es la cadena de wire."""
    missing_input = "missing_input"          # input-condicional: faltó una entrada
                                              # de ESTE proyecto (accionable, transitorio)
    pending_capability = "pending_capability"  # hueco de capacidad permanente: ningún
                                              # run determinista lo evalúa (espera move 3)

class NotEvaluated(Exception):
    """Señal (no error) de que un validador NO evaluó por falta de entrada.

    Es un `Exception` plano —NO un `BookwrightError`—; no es un fallo. El runner
    la captura en una cláusula **antes** de su `except Exception` genérico y la
    anota en el canal `not_evaluated`, nunca en `errors[]`. El validador declara
    `kind` al lanzar: es el único que sabe si el hueco es de *esta entrada*
    (`missing_input`, por defecto) o del *enfoque* (`pending_capability`).
    """
    def __init__(
        self, reason: str, kind: NotEvaluatedKind = NotEvaluatedKind.missing_input
    ) -> None: ...

class Validator(Protocol):
    name: str
    severity_default: Severity

    def validate(self, project, indexer) -> list[Violation]:
        """Devuelve lista de violaciones. Vacía = evaluado y limpio.

        El tipo de retorno NO cambia (`list[Violation]`). Un validador que no
        tiene entrada para NINGUNA de sus comprobaciones PUEDE
        `raise NotEvaluated(motivo)` para declararlo; la lista vacía sigue
        significando "evaluado, sin hallazgos" (un verde legítimo). Un validador
        custom que devuelve una lista pelada y nunca lanza sigue funcionando y
        cuenta siempre como **evaluado** (compatibilidad hacia atrás).
        """
```

**Resultado tri-valor (issue #1 cara B, § 13.4).** El veredicto por validador y
por ejecución tiene tres estados, **a nivel de validador entero** (no por
sub-comprobación):

| Veredicto | Cómo lo expresa el validador | Dónde aflora | ¿Gatea CI? |
|---|---|---|---|
| **evaluado, sin hallazgos** | `return []` | en ningún sitio (cuenta como limpio) | no |
| **evaluado, con hallazgos** | `return [Violation, …]` | `violations[]` | sí, si hay algún `error` |
| **no-evaluado(motivo, kind)** | `raise NotEvaluated(motivo[, kind])` | `not_evaluated[]` | no |
| **petó (load/run)** | lanza cualquier otra excepción | `errors[]` (`ValidatorError`) | no |

El estado **no-evaluado** lleva además un `kind` del vocabulario cerrado
`{missing_input, pending_capability}` (iteración 044), por defecto `missing_input`
—así toda `raise NotEvaluated(motivo)` existente queda byte-idéntica—. `missing_input`
es input-condicional (faltó una entrada de *este* proyecto: accionable, transitorio);
`pending_capability` es un hueco de capacidad permanente (ningún run determinista lo
evalúa; espera move 3 — § 13.5). El `kind` se serializa como clave **aditiva** en cada
elemento de `not_evaluated[]` (sobre `--json` y payload de `status`); ninguna clave
previa se renombra. Refina el predicado de verde y la regla del nudge (§ 13.4): solo
`missing_input` deniega verde y dispara `activate_dormant_validators`.

El motivo es texto fijo en **inglés** (sin datos minteados), determinista. El
nuevo estado fluye de forma **aditiva**: `runner.RunResult` gana un 4.º elemento
`not_evaluated` (ordenado por nombre) → `ValidationReport` gana una clave
hermana `not_evaluated[]` en el sobre `--json` y una sección "not evaluated:" en
el informe humano → `status` lo expone en `state.validation.not_evaluated` y una
regla `activate_dormant_validators` lo nombra en `next_actions`. El gate sigue
clavado **solo** en hallazgos `Violation` de severidad `error`; `no-evaluado`
nunca gatea y es un canal **distinto** de `errors[]` (que es para validadores que
petan). El predicado de verde queda fijado en un único sitio (`report.py`),
**refinado por `kind` en la iteración 044** (§ 13.5):

> Una ejecución es **verde/limpia** ⟺ `status == "ok"` **y** ninguna entrada de
> `not_evaluated` tiene `kind == "missing_input"`.

Una entrada `pending_capability` (p.ej. el abstinente `character_unknown_mentions`,
presente en *todo* proyecto) queda **visible** pero **no** deniega verde, y la regla
`activate_dormant_validators` se filtra igual: dispara **solo** cuando hay alguna
entrada `missing_input` accionable. Así un proyecto impecable vuelve a leerse verde y
el nudge deja de dispararse en todos lados (regresión que la 043 introdujo al hacer
`character_unknown_mentions` un abstinente incondicional).

**Pseudo-fuente `ingestion` (iteración 046).** `not_evaluated[]` admite además un
origen **no-validador**: cada fichero de la bible que `map_bible` **omite** por
front-matter inservible (`MapResult.skipped`) lo surfacéa `validate` como una entrada
`not_evaluated` con `validator="ingestion"` (centinela compartido para el origen
no-validador), `kind=missing_input` (un input de *este* proyecto quedó fuera del
corpus: accionable y, por el predicado de 044, **deniega verde**) y `reason` citando el
path omitido y la causa del skip. No es un canal nuevo ni una clave nueva: reusa el
canal de 040/044 a nivel de **fichero de entrada omitido**, de modo que
`not_evaluated: []` deje de leerse como «todo evaluado» cuando un fichero entero quedó
fuera del grafo (la grieta `[]`-significa-limpio de la cara B, ahora cerrada también a
ese nivel). El gate (`error`) no cambia: un skip no es `Violation`, así que el código
de salida es idéntico al de un run sin skips con los mismos hallazgos.

### 13.2 Validators built-in en v0

| Validator | Severity default | Qué valida |
|---|---|---|
| `temporal` | error | Que los eventos en la timeline sean consistentes (no contradicciones). **Las cuatro reglas** (ciclo, orden-vs-solape, contención-vs-orden, numérica) resuelven `source` a `bible/timeline.md:<línea>` vía `resolve_source` sobre un evento implicado elegido de forma determinista —subject del triple implicado en b/c/d, URI lexicográficamente menor del SCC en (a)— (iter 048; antes solo la regla d lo hacía). |
| `character_presence` | error | Que los personajes mencionados en manuscrito existan en la bible y viceversa. |
| `setting_continuity` | warning | Que los settings se mantengan coherentes (ej. clima, descripciones). |
| `focalization` | warning | Que la persona narrativa declarada en constitution se respete. **Bajo tercera persona *limitada*/focalizada se abstiene del run entero** (`NotEvaluated`, `kind=pending_capability`): el head-hopping (atribución de interioridad a un personaje no-focal) es juicio semántico —move 3 (§ 13.5)— y el heurístico determinista se midió casi dormido sobre prosa real (iter 045). La comprobación de ruptura de 1ª persona fuera de diálogo solo corre bajo tercera **no-limitada** (omnisciente); 1ª persona evalúa sin hallazgos. Las cuatro abstenciones por entrada (sin constitución / sin voz / `[PENDING]` / sin persona gramatical) siguen `missing_input`. |
| `factual_anchor` (v0.2) | warning (estructura) / error (anacronismo) | Integridad estructural de las anclas de investigación: que cada ancla tenga Fuente con procedencia completa, que las entidades enlazadas existan, y detección de anacronismos contra la timeline. Cada hallazgo resuelve `source` al fichero autor `bible/research/<tema>.md` (vía `AnchorIdentity.relpath`, no `resolve_source(anchor.uri)` —un ancla *es* la reificación `E13`, nada apunta a ella) e identifica el ancla por su handle autor (`promotes -> constrains`), a través del **mismo punto compartido** (`anchor_handle`) que usa `bookwright status` (iter 048). Ver § 20.6. |
| `narrative_structure` (v0.4) | warning | Continuidad estructural sobre la capa Propp/Greimas (§ 7.4): la regla de **beat-huérfano** marca cada `G9_Narrative_Unit` que no pertenece a ninguna `G7_Narrative_Sequence`; la regla de **rol-sin-resolver** re-surfacea cada `roles:` de una ficha que no resuelve a rol de personaje. **Ambas reglas nombran la unidad por su `name` humano autorado, a solas** (no el slug de URI, no entre paréntesis), a través de un **único punto compartido** (`_unit_identifier`, el `rdfs:label` que el `G9` ya emite desde iter 035), de modo que las dos superficies no pueden divergir (iter 049, DEBT-017); el slug solo aparece como suelo defensivo cuando el grafo no lleva `rdfs:label`. Ambas resuelven `source` a `outline/units/<ficha>.md[:línea]`. |

### 13.3 Registry

Validators se autodescubren en `bookwright.validation` y se filtran por `manifest.toml > [validators].enabled`. Validators custom del usuario en `<proyecto>/.bookwright/validators/*.py` se cargan dinámicamente.

### 13.4 Robustez de la validación — `v0.5.0` (issue #1)

> **Dirección decidida en la issue #1, transcrita aquí (Principio I).** El detalle
> concreto del contrato (la firma exacta del Protocol § 13.1) se actualiza **antes**
> de divergir el código, en la iteración 040 (plan § 7.3). Esto es el *qué/por qué*;
> el *cómo* durable está en `bookwright-roadmap.md` § 3.

El dogfooding de v0.4.x destapó **una clase de defecto** —no tres bugs— en los
validadores de prosa, con dos caras:

- **A — acoplamiento a la prosa de superficie.** Cada validador reimplementa por su
  cuenta cómo "ver más allá" del markdown que el propio andamiaje emite (encabezados
  ATX, viñetas, énfasis, placeholders `[PENDING: …]`). Cada formato nuevo reabre la
  grieta en el siguiente validador. **Cierre (iter 039):** una **costura única** en
  `io/` que clasifica cada línea/bloque y expone su vista normalizada **una vez**; los
  validadores la consumen en vez de re-escanear texto crudo, y sus strippers locales
  se borran. Es Principio I aplicado a la validación: acoplar a la **estructura ya
  clasificada**, no a la superficie. Sin dependencia de markdown nueva (Constitución
  II): clasificador determinista, no AST.
- **B — falsa confianza.** `validate()` devuelve `list[Violation]`, y `[]` no
  distingue "evaluado y limpio" de "no pude mirar" (un validador dormido se pinta
  verde). **Cierre (iter 040):** el resultado pasa a **tri-valor** —`evaluado` /
  `no-evaluado(motivo)`— y el runner, el report, el sobre `--json`, `status` y las
  skills exponen el tercer estado. Aditivo: el gate sigue clavado solo en hallazgos
  `error`; `no-evaluado` es un canal distinto de `errors[]` (que es para validadores
  que petan).

Lo que **no** entró en `v0.5.0`: convertir el heurístico en **juicio semántico** vía
el path LLM de `bookwright-verify` (§ 20.6). Era el movimiento 3 de la issue,
dirección del horizonte demand-pulled, activable solo cuando un heurístico concreto
se midiera como insuficiente. **Ese disparador se cumplió** (§ 13.5).

### 13.5 El reencuadre del 2º dogfood — honestidad de conjunto abierto + move 3 activado (issue #1)

> **Dirección decidida en la issue #1 tras el 2º dogfood (`sombra-en-el-puerto`,
> 2026-06-23), transcrita aquí (Principio I).** Es el *qué/por qué*; el detalle
> durable está en `bookwright-roadmap.md` § 3/§ 5. El contrato concreto de cada
> validador se actualiza en la spec de su iteración, antes de divergir código.

`v0.5.0` cerró las caras A/B, pero un 2º dogfood midió la regla de
menciones-desconocidas de `character_presence` (`warning`) como **100% ruido** (4
falsos positivos, 0 señal real) sobre prosa real. Eso obligó a separar **dos reglas
de naturaleza opuesta** que conviven en ese validador:

- **Huérfanos** (`error`, el gate): ¿toda CHARACTER del bible se menciona en la
  prosa? **Conjunto cerrado** — buscas nombres *conocidos*. Determinista, sin NER,
  sin costura. Sólido; intacto. (Verificado: `_orphans` usa `_is_mentioned` sobre los
  ficheros, no toca `_is_sentence_initial` ni los rosters de candidatos.)
- **Menciones-desconocidas** (`warning`): ¿todo token capitalizado tiene entrada en
  el bible? **Conjunto abierto** — *descubrir desconocidos*. Es el problema de
  NER/juicio semántico, con un techo de precisión que **ninguna costura ni roster
  nuevo sube**. Aquí vive todo lo frágil y los 4 FP.

**La decisión (tres movimientos):**

1. **El heurístico de conjunto abierto deja de fingir.** La regla de
   menciones-desconocidas y el head-hopping de `focalization` —dos heurísticos
   deterministas haciendo un trabajo semántico— dejan de emitir por defecto
   (inundar ruido / dormir en verde) y **declaran `NotEvaluated`** (el canal de la
   iteración 040) con motivo «conjunto abierto: requiere juicio semántico (move 3)».
   No es un parche: es el comportamiento terminal **permanente** (con el move 3
   offline, `not_evaluated` es el fallback correcto). El gate (`error`) no cambia.
   *Matiz del head-hopping (iter 045):* como `NotEvaluated` es **todo-o-nada**, una
   voz «tercera limitada» abstiene el validador **entero**, así que la comprobación
   determinista de ruptura de 1ª persona —que sí funciona— deja de correr para el
   caso focalizado (sigue corriendo bajo tercera no-limitada). Es una regresión de
   cobertura real registrada como **DEBT-019** (la cierra un contrato de evaluación
   parcial o el propio move 3); el contrato escrito no la oculta.
   *Matiz a nivel de fichero de entrada (iter 046):* la misma honestidad se extiende a
   la **ingestión**. Un fichero de la bible omitido por front-matter inservible
   (`map_bible.skipped`) lo **surfacéa ahora `validate`** como entrada `not_evaluated`
   (`validator="ingestion"`, `kind=missing_input`, § 13.4), **degradando verde** —no
   solo lo rechaza `status` (`code=skipped_sources`)—. Cierra la asimetría
   `status`↔`validate` (**DEBT-018**): antes `validate` —el gate de CI— validaba el
   corpus parcial en silencio (`not_evaluated: []`). El gate (`error`) y el código de
   salida no cambian: un skip se surfacéa, no gatea.
2. **El move 3 se activa** (§ 20.6, `bookwright-roadmap.md` § 5): la condición
   («heurístico concreto medido insuficiente sobre prosa real») está cumplida. Es la
   única cura de raíz del conjunto abierto; restaura la señal real (personaje usado
   sin declarar) que el `not_evaluated` deja pendiente. **Necesita diseño propio
   antes de spec** por la tensión de determinismo del gate (§ 20.6).
3. **Vocabularios cerrados, trato consistente** (DEBT-016, capa narrativa, no
   `character_presence`) — **entregado en la iteración 047**: un término Propp/Greimas
   no reconocido —antes ingerido **en silencio** como nodo sin `crm:P2_has_type`—
   emite ahora un `warning` **no fatal** en `graph build` (canal aditivo
   `untyped_vocab_terms` del sobre, hermano de `unknown_keys`/`unresolved_references`)
   que enumera los términos válidos del vocabulario activo (simetría con el rechazo de
   research § 20, DEBT-006), pero el nodo se ingiere igual (cerrado para *tipar*,
   abierto para *autorar*); el build ni aborta ni cambia su código de salida. Principio:
   **fatal ⇔ un valor inválido rompe lógica downstream** (`reliability` inválido rompe
   el gate de `factual_anchor` → fatal; `P2_has_type` ausente es metadato → no fatal,
   § 4.4).

**Descartado:** parchear la regla de conjunto abierto por instancia (la
comilla-líder `«`, el cuerpo del título) o con un 5º roster «organización» —es
perseguir un conjunto abierto con listas cerradas; no converge. La costura
`io/prose.py` se conserva para los validadores deterministas; solo se deja de
alimentar con ella el heurístico abierto.

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
    "packaging>=23.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
# Búsqueda vectorial (horizonte demand-pulled), opcional y desacoplada del grafo. Ver § 12.3 y § 20.12.
vectors = ["chromadb>=0.5"]

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
- `resources/schemas/golem-1.1/`: copiar el TTL de GOLEM upstream, validar.
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

- **M4 — Investigación y verificación** (§ 20, propuesto como **v0.2.0**): sistema
  de investigación con procedencia (Fuente/Hallazgo/Ancla sobre el módulo
  Inference), skills `bookwright-research` y `bookwright-verify`, validator
  `factual_anchor`, vocabulario `sources.ttl`, `bible/research/`. El plan
  detallado de iteraciones (13–17) vive en `bookwright-implementation-plan.md`.
- **M5 — Orquestación de contexto** (§ 21, propuesto como **v0.3.0**): el "hilo
  conductor". Estado autoral (`[focus]` + `bookwright focus`), estado derivado
  determinista (`bookwright status` + `next_actions`) y consumo por las skills
  ("Próximos pasos"). El plan detallado de iteraciones (019–023) vive en
  `bookwright-implementation-plan.md`.
- **v0.4 — capa estructural narrativa** (Propp/Greimas G7/G9/G10 + ingesta de `outline/`, § 7.4): **entregada como `v0.4.0`** (2026-06-21), cierra la paridad de ingesta.
- **Horizonte demand-pulled (sin versión asignada).** Capacidades que se activan solo cuando se cumple su disparador concreto, nunca como plomería especulativa:
  - **búsqueda vectorial** (ChromaDB o equivalente) sobre el grafo `rdflib`, para recuperación semántica del corpus de fuentes (`bible/research/`) y el manuscrito; desacoplada de Grafeo (ver § 12.3 y el análisis de coste en § 20.12). Activar ante un corpus real multi-libro/serie o un fallo medido de structural-recall en una skill.
  - **export a EPUB/PDF/print** (`bookwright-export` con pandoc): activar una vez probado el flujo end-to-end en un libro real. La etiqueta `1.0` se gana con ese flujo probado, no se pre-asigna a export.
  - commands de autoría adicionales (`bookwright-feedback`, `bookwright-polish`, `bookwright-revise`, `bookwright-query`): a demanda, sin versión asignada. (El antiguo `bookwright-status` queda absorbido por el verbo de CLI determinista `bookwright status` de M5, § 21.5.)

> **Funcionalidades descartadas (no se implementarán).** Decisiones del
> propietario, posteriores al cuerpo original del documento:
> - **Sistema de presets / genre-packages**: un resolver de templates por género.
>   La resolución de templates es de **2 capas** (overrides → core, § 5.4).
> - **`GrafeoIndexer` / motor Grafeo**: `rdflib` es el motor permanente y basta
>   para grafos de tamaño libro. La búsqueda vectorial (horizonte demand-pulled)
>   **se conserva**, pero implementada aparte (ChromaDB sobre rdflib), no vía Grafeo.
> - **Multi-integración** (Copilot, Gemini, Cursor/Codex específicos) y el
>   comando `bookwright integrate`: el target es Claude Code; `claude` y
>   `generic` ya cubren el uso. La arquitectura `INTEGRATION_REGISTRY` deja la
>   puerta abierta (§ 11.6) por si alguna vez hiciera falta, sin compromiso de
>   roadmap.
> - **Extension system** (validators distribuibles, hooks pre-commit): si hace
>   falta algo, se implementa directamente en la aplicación.
>
> El preset externo `fiction-book-writing` (§ 17.2) sigue siendo solo inspiración
> de templates, no un sistema a construir.

---

## 16. Decisiones explícitas que el agente NO debe re-cuestionar

Estas decisiones se discutieron extensamente en la fase de diseño. Cambiarlas requeriría rehacer secciones enteras. El agente las trata como axiomas:

1. **Python, no Rust ni TypeScript.** Ecosistema de scientific computing y semántica está en Python.
2. **rdflib en v0, no Grafeo.** Grafeo es v0.5 de un único mantenedor; rdflib es maduro y estándar.
3. **GOLEM como ontología.** No diseñar una ontología propia.
4. **Texto plano (Markdown, TOML, Turtle) como fuente de verdad.** No SQLite, no JSON binario, no LevelDB.
5. **Patrón Spec Kit como referencia operacional, sin acoplamiento.** Adoptamos su arquitectura (`INTEGRATION_REGISTRY`, `SkillsIntegration`, formato de command templates, resolución de templates por capas), pero Bookwright es proyecto autónomo. No depende del wheel de `specify-cli`.
6. **Sin scripts shell.** Todo Python, vía Typer. El axioma gobierna la superficie del toolkit que se distribuye: el CLI `bookwright`, sus subcomandos y las skills generadas; ninguna funcionalidad de Bookwright puede depender de un script shell. El utillaje interno del repositorio (release, regeneración de assets bajo `scripts/`) queda fuera de su alcance.
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
- La resolución de templates por capas (overrides → core).
- La arquitectura plugin-based de integrations (`INTEGRATION_REGISTRY`, `SkillsIntegration`, `IntegrationOption`). Nota: Bookwright solo necesita `SkillsIntegration` porque todas las integraciones de v0 producen Agent Skills (commands legacy ya no es opción).
- El patrón de generación de SKILL.md desde command templates con `SKILL_DESCRIPTIONS` enriquecidas.
- El contrato CLI ↔ agente vía JSON sobre stdout.
- El patrón mental de constitution como gobernanza.

**Lo que Bookwright NO adopta:**

- El acoplamiento al ciclo de release de Spec Kit (Bookwright es proyecto independiente).
- El soporte de bash + powershell (Bookwright es Python puro).
- El sistema completo de extensions (descartado, no se implementará; ver § 15.5).
- El download de templates desde GitHub releases (Bookwright empaqueta dentro del wheel).
- La nomenclatura software-céntrica (`specify`, `plan`, `tasks`, `implement`).

**Licencia de Spec Kit:** MIT. Compatible con Bookwright (EUPL-1.2). No hay reutilización de código fuente sin atribución; lo que se reutiliza son patrones de diseño documentados públicamente.

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
- La idea de incluir RAG / búsqueda vectorial para recuperación semántica (horizonte demand-pulled, desacoplada del motor de grafo; ver § 12.3 y § 20.12).
- El patrón de export con pandoc (horizonte demand-pulled).

**Licencia del preset:** MIT. Permite reutilización de estructura de templates con atribución.

**Posible interoperabilidad futura (sin versión asignada):** que `bookwright` pueda importar un proyecto inicializado con el preset y construir el grafo GOLEM a partir de sus archivos. Esto sería un gancho de adopción para usuarios que ya estén en ese ecosistema.

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

- **GOLEM upstream** (GOLEM-lab/golem-ontology): la ontología en sí. **CC BY 4.0** (declarada en los propios metadatos de la ontología vía `dcterms:license`; el repo upstream no incluye fichero `LICENSE`). CC BY 4.0 es permisiva (solo atribución, sin copyleft), por lo que es plenamente compatible con redistribuirla dentro de un proyecto EUPL-1.2. Bookwright congela una versión y la distribuye en `resources/schemas/` sin modificar, conservando intacta su atribución embebida (autoría "GOLEM Lab", cita bibliográfica, DOI y enlace de licencia).
- **Grafeo** (grafeo.dev): considerado para v0 como motor de grafo, descartado por madurez. Descartado también de forma permanente: `rdflib` es el motor único (ver § 15.5). La búsqueda vectorial de v0.4 no depende de él.

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
| **Fuente** (Source, v0.2) | Documento o testimonio consultado en la investigación, con procedencia (autor, idioma original, tipo, fiabilidad, fecha, cita). Ver § 20.3. |
| **Hallazgo** (Finding, v0.2) | Afirmación sobre el mundo real sostenida por una o más Fuentes, reificada como `E13_Attribute_Assignment`. Ver § 20.3. |
| **Ancla** (Anchor, v0.2) | Hallazgo promovido a restricción vinculante que el manuscrito no puede contradecir; enlaza a la entidad narrativa que constriñe. Materializa las "anclas históricas" de § 1.1. Ver § 20.3. |

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
- **ChromaDB**: trychroma.com (vector store embebido para la búsqueda vectorial, v0.4).

---

## 20. Extensión de diseño: Investigación y verificación (v0.2)

> **Nota de procedencia.** Esta sección se añade *después* del cuerpo original
> del documento (§§ 1–19), por eso ocupa el número 20 pese a ser materia de
> primera clase y no apéndice. Se ratifica como extensión del diseño, no como
> revisión: no toca ninguna decisión de § 16. Las únicas ediciones aguas arriba
> son aditivas (filas nuevas en tablas de §§ 1.1, 4.4, 4.5, 7, 10.4, 13.2 y un
> hito nuevo en § 15.5) y se referencian desde aquí.

### 20.1 Por qué la investigación es de primera clase

Escribir un libro es, en una fracción enorme de los casos, **investigar** antes
y durante la escritura. Una novela negra ambientada en España exige conocer
cómo opera de verdad el gremio de detectives privados (licencia TIP, límites
legales, jerga del oficio); una novela sobre la Segunda Guerra Mundial exige
manejar fuentes oficiales —alemanas, polacas, británicas, estadounidenses,
francesas— **en su idioma original**, porque la versión nacional de un hecho
cambia con la fuente. El diseño original de Bookwright (§§ 1–19) trataba la
investigación como un único documento pasivo, `bible/research.md` ("open
questions + source notes"). Eso es un esbozo, no un sistema: captura el
*producto* mínimo pero ignora el *proceso* (investigar de verdad, con
procedencia y multilingüismo) y la *restricción* (que lo investigado **obligue**
a la ficción y sea verificable). La propia § 1.1 prometía "anclas históricas si
las hay" como chequeo, pero ningún validator de § 13.2 las implementaba: una
promesa sin cableado. Esta sección cierra ese hueco.

El principio rector, coherente con la filosofía DDA (§ 2) y los axiomas de § 16:

- **Bookwright no busca; estructura, ancla y verifica.** La búsqueda real de
  fuentes (web, archivos oficiales, lectura en idioma original, juicio de
  fiabilidad) la ejecuta el agente que corre el `SKILL.md`, que ya tiene esa
  capacidad. Bookwright aporta lo que el agente no tiene: un modelo de
  procedencia, un sitio canónico en texto plano, integración en el grafo y
  validación determinista. No se añade ninguna dependencia de runtime para
  acceso a la red (respeta § 14 y el axioma "texto plano fuente de verdad").
- **La investigación es extra-diegética; la ficción es diegética.** GOLEM modela
  el mundo *de la historia*. La investigación modela el mundo *real* que lo
  constriñe. El puente entre ambos ya existe dentro de GOLEM y no exige
  inventar ontología (axioma 3): el módulo **Inference**.

### 20.2 El puente diégesis ↔ mundo real: el módulo Inference

GOLEM incluye el módulo **Inference**, construido sobre `E13_Attribute_Assignment`
de CIDOC CRM, cuyo propósito declarado (§ 4.2) es la *"trazabilidad de
afirmaciones: fuente, método, premisa"*. Es exactamente el aparato que la
investigación necesita: toda afirmación sobre el mundo —"un detective privado en
España necesita una licencia TIP", "en 1943 la Wehrmacht denominaba X a Y"— se
reifica como una aserción con su fuente, su método y la entidad narrativa a la
que aplica.

Esto significa que un hallazgo de investigación **no es metadato suelto**: es un
nodo del mismo grafo `graph.ttl` que ya contiene personajes, settings y eventos.
Una afirmación investigada puede así enlazarse a la entidad GOLEM que restringe
(un `G1_Character`, un `G12_Setting`, un `G5_Narrative_Event`, la timeline) y
participar en las mismas queries SPARQL y validaciones que el resto del dominio.
Esa es la pieza que convierte "investigación" en "investigación **validable**".

### 20.3 Las tres entidades: Fuente, Hallazgo, Ancla

El sistema introduce tres conceptos, todos serializables en Turtle vía los
puntos de extensión existentes (`E13_Attribute_Assignment` para reificar,
`E55_Type` para tipar), sin extender el esquema GOLEM:

1. **Fuente** (`source`). Un documento o testimonio consultado. Registra:
   referencia bibliográfica o URL (más copia/archivo cuando proceda), **autor**,
   **idioma original**, **tipo** (vocabulario controlado: primaria, secundaria,
   oficial, académica, periodística, testimonial), **fiabilidad** (alta / media
   / baja, con justificación), **fecha de acceso** y **cita textual** relevante
   (en idioma original + traducción cuando difiera del idioma del libro). Se tipa
   con `E55_Type` desde el vocabulario `sources.ttl` (§ 20.8).

2. **Hallazgo** (`finding`). Una afirmación concreta sobre el mundo, sostenida
   por una o más Fuentes. Se reifica como `E13_Attribute_Assignment`: *qué* se
   afirma, *quién* lo afirmó (el agente investigador o el autor), *sobre qué*
   entidad recae y *con qué fuente(s)*. Un hallazgo puede quedar en estado
   abierto (pregunta sin resolver), preservando el rol original de
   `research.md`.

3. **Ancla** (`anchor`). Un Hallazgo **promovido a restricción**: un hecho que el
   manuscrito no puede contradecir. No toda investigación es ancla —mucha es
   color o contexto—; el autor (o el skill) marca explícitamente cuáles lo son.
   Un ancla enlaza al elemento narrativo que constriñe y, cuando lleva una
   referencia temporal (`P4_has_time-span`), habilita detección de anacronismos
   reutilizando la infraestructura del validator `temporal` (§ 13.2). El ancla es
   la materialización de las "anclas históricas" prometidas en § 1.1.

Resumen de la cadena de procedencia:

```
Fuente (oficial, idioma original, fiabilidad)
   └─documenta→ Hallazgo (E13_Attribute_Assignment)
                   └─[si se promueve]→ Ancla ──restringe──▶ G1_Character / G12_Setting / G5_Event / timeline
                                                                      ▲
                                                          verificación del manuscrito
```

### 20.4 El proceso: el skill `bookwright-research`

Se añade un command/skill nuevo (§ 10.4), `/bookwright-research <tema>`, que
conduce al agente por un **protocolo de investigación riguroso** en vez de
dejarlo improvisar. El protocolo, codificado en su `SKILL.md`:

1. **Descomponer** el tema en sub-preguntas concretas y verificables.
2. **Buscar fuentes autorizadas**, con preferencia explícita por **fuentes
   primarias y oficiales en el idioma original**. Para temas con cargas
   nacionales (guerras, fronteras, gremios regulados), consultar
   **deliberadamente fuentes de varias procedencias** (p. ej. alemana, polaca,
   británica, estadounidense, francesa) en lugar de una sola.
3. **Registrar cada hallazgo con procedencia completa** (los campos de Fuente de
   § 20.3), incluyendo cita en idioma original.
4. **Contrastar versiones en conflicto**: cuando las fuentes nacionales o
   primarias discrepan, registrar cada versión con su procedencia en vez de
   colapsarlas en una sola "verdad". La discrepancia es un dato, no un error.
5. **Marcar anclas**: señalar qué hallazgos son restricciones vinculantes y a qué
   entidad narrativa enlazan.
6. **Dejar abiertas** las preguntas sin resolver (continuidad con el rol clásico
   de `research.md` y con `/bookwright-clarify`).
7. **Persistir**: escribir los hallazgos en `bible/research/<tema>.md` (§ 20.7) y
   dejar el grafo listo para reindexar.

El multilingüismo es requisito de primer orden del protocolo, no un extra: la
Fuente guarda idioma y cita original, y la regla 4 obliga a preservar la
pluralidad de procedencias.

### 20.5 La restricción: anclas en el grafo

`bookwright graph build` (indexer de § 12, iteración 6) aprende a parsear
`bible/research/` y a emitir las tríadas de Fuente, Hallazgo y Ancla al
`graph.ttl`. Se añade un lector `io/research.py` análogo a `io/bible.py`. A
partir de ahí, las anclas son consultables como cualquier otra entidad, por
ejemplo:

```sparql
# Anclas que restringen a un personaje concreto y carecen de fuente fiable
SELECT ?anchor ?claim WHERE {
  ?anchor a golem:E13_Attribute_Assignment ;
          bw:constrains <…/character/ana-sanchez/> ;
          bw:claim ?claim .
  FILTER NOT EXISTS { ?anchor bw:source ?s . ?s bw:reliability "alta" }
}
```

(El prefijo `bw:` designa las propiedades de Bookwright sobre el patrón
`E13`/`E55`; se define en `sources.ttl`. No se introducen clases GOLEM nuevas.)

### 20.6 La verificación: dos capas, código y LLM

Igual que el diseño ya separa validators de código (§ 13, deterministas) de
chequeos LLM (commands como `bookwright-continuity`), la verificación de la
investigación tiene **dos capas complementarias**:

- **Validator de código `factual_anchor`** (nuevo en § 13.2, determinista).
  Comprueba la *integridad estructural* de las anclas, no su veracidad: que cada
  ancla tenga al menos una Fuente con los campos de procedencia obligatorios;
  que las entidades a las que enlazan existan; emite *warning* sobre anclas sin
  fuente o de fiabilidad baja; y, cuando un ancla lleva `time-span`, detecta
  **anacronismos** contra la timeline reutilizando la lógica de `temporal`.
  Severidad por defecto: `warning` (estructura), `error` (anacronismo duro).
  Desde la iteración 048 (track B, DEBT-015) ambos validators graph-consumer
  emiten un locator resoluble y un identificador legible, igual que los de prosa.
  `factual_anchor` resuelve el ancla sobre un **corpus de investigación construido
  en proceso** —un accesor memoizado y **no persistente** de
  `ValidationContext` que reconstruye `map_research` y casa cada ancla con su
  `AnchorIdentity` por URI dentro de una sola build, exactamente como hace
  `status` (la URI uuid7 del ancla se re-acuña en cada build, así que un join por
  URI contra el grafo persistido de una build previa fallaría siempre)—, fija
  `source = AnchorIdentity.relpath` y nombra el ancla con el handle compartido
  `anchor_handle(promotes, constrains)`. La granularidad difiere **por diseño**,
  no por defecto: un evento `temporal` lleva `:línea` (su `E13` la registra),
  mientras que un ancla es solo fichero (`AnchorIdentity` no lleva línea, y el
  handle/fichero se ata byte a byte al que `status` ya renderiza). El corpus en
  proceso **nunca** se guarda en disco (`validate` es lectura pura; el grafo
  derivado lo produce solo `graph build`).

- **Command/skill `bookwright-verify`** (nuevo en § 10.4, semántico). El agente
  lee el manuscrito **contra las anclas** y reporta pasajes que contradicen lo
  investigado: anacronismos, errores de procedimiento (el detective hace algo
  ilegal o imposible en España), inexactitudes culturales o lingüísticas. Es a
  la investigación lo que `bookwright-continuity` es a la bible: un reporte
  post-borrador, no un auto-fix. Se ejecuta tras la fase 5 (Draft).

La división respeta la filosofía existente: lo que se puede comprobar con
código determinista (¿el ancla está bien formada? ¿hay choque temporal duro?) lo
hace un validator; lo que exige juicio (¿este párrafo contradice el hecho
investigado?) lo hace el LLM vía skill.

> **El move 3 de la issue #1 reusa esta capa LLM (activado, 2026-06-23).** El
> reencuadre del 2º dogfood (§ 13.5) activó el escalado a juicio semántico de los
> heurísticos de **conjunto abierto** —menciones-desconocidas (¿«Naviera» es
> organización o personaje sin declarar?), voz/focalización— sobre este mismo path
> `bookwright-verify`. Mientras tanto, el heurístico declara `NotEvaluated` (§ 13.5),
> no finge.

#### 20.6.1 Determinismo vs. LLM — dónde va la frontera (dirección de diseño del move 3)

> **Decidido en el hilo de la issue #1 (2026-06-24), transcrito aquí (Principio I).**
> Es la *dirección* del move 3; el contrato concreto y la spec llegan cuando se
> implemente. Reemplaza el viejo encuadre "regex pre-filtro → LLM juez", que tenía un
> fallo fatal (ver principio 3).

Cuatro principios fijan dónde acaba el determinismo y empieza el LLM:

1. **La frontera es el *sustrato*, no la dificultad.** El determinismo no es "para lo
   mecánico"; es para el **grafo derivado**, donde la verdad es relacional y exacta
   (presencia de un personaje, ciclo temporal, ancla sin fuente fiable, ojos azules en
   cap 3 / verdes en cap 12). Ahí es **superior**, no un fallback: exacto, reproducible,
   gratis, explicable (señala los triples). El LLM es para juzgar **prosa / lenguaje de
   conjunto abierto** (¿esto es head-hopping?, ¿este término es una organización?, ¿este
   párrafo contradice lo investigado?), donde la enumeración por reglas no escala (el
   whack-a-mole que la issue #1 demostró). Intentar capturar palabras/símbolos concretos
   con reglas deterministas **no escala**; eso es territorio del LLM.
2. **LLM-primero, pero *anclado en el grafo* (grounding).** El LLM no juzga la prosa en
   el vacío: la juzga **contra el canon que el grafo determinista contiene**, que se le
   inyecta como contexto (el roster para decidir «¿personaje sin declarar?», la voz
   declarada para «¿rompe la focalización?»). Determinismo y LLM no son dos validadores
   paralelos sino **una tubería**: el grafo *alimenta* el juicio. Aquí enchufa la
   búsqueda vectorial del horizonte demand-pulled (recuperar el trozo de canon relevante
   por juicio).
3. **El determinismo puede AÑADIR confianza o ahorrar coste, nunca SUPRIMIR.** El viejo
   "regex pre-filtro" fallaba porque un punto ciego del regex *descartaba* el candidato y
   el LLM no lo veía nunca (el falso negativo del head-hop dormido). En la capa de prosa
   el determinismo es **optimización de coste** (cortocircuita lo inequívoco, hace
   viable correr el LLM sobre un libro entero), nunca una frontera de correctitud que
   pueda esconder algo.
4. **Separar *juicio* de *gate*.** Es la restricción dura que mantiene la disciplina de
   test del proyecto. El **juicio** (¿qué le pasa a esta prosa?) es LLM-primero y
   **informativo** — un reporte post-borrador que NO rompe CI, como
   `bookwright-verify`/`bookwright-continuity` hoy. El **gate** (¿esto bloquea el merge?)
   se queda **determinista y reproducible**: solo hechos del grafo, o veredictos del LLM
   **cacheados/fijados** (golden runs, por hash de la entrada) para que el re-run sea
   estable. Un LLM en vivo **no** decide pasa/falla de CI. LLM-primero para opinar;
   determinista para bloquear.

Coste, operación offline y reproducibilidad de tests se resuelven dentro de estos cuatro
principios (sobre todo el 3 y el 4). La spec del move 3 los aterriza; hasta entonces, el
heurístico de conjunto abierto declara `NotEvaluated` (§ 13.5).

### 20.7 Almacenamiento: `bible/research/`

`bible/research.md` (un único fichero) se sustituye por un **directorio**
`bible/research/` (ver edición en § 7), con un fichero por tema de
investigación más un registro de fuentes:

```
bible/
└── research/
    ├── _index.md            # mapa de temas + preguntas abiertas globales
    ├── sources.md           # registro de Fuentes (procedencia consolidada)
    ├── <tema>.md            # hallazgos + anclas de un tema (front-matter estructurado)
    └── ...
```

Cada `<tema>.md` lleva front-matter YAML con la lista estructurada de hallazgos y
anclas (parseable por `io/research.py`) y prosa legible debajo. Sigue siendo
texto plano, versionable y superviviente a la desaparición del toolkit
(axioma 4). El `graph.ttl` se deriva de estos ficheros, nunca al revés.

### 20.8 Vocabulario controlado y segmentos URI

- **Vocabulario** (edición en § 4.4): se añade `sources.ttl`, que define los
  tipos de Fuente (`primaria`, `secundaria`, `oficial`, `académica`,
  `periodística`, `testimonial`) y los niveles de fiabilidad vía `E55_Type`,
  más las propiedades `bw:` que reifican Fuente/Hallazgo/Ancla sobre `E13`.
- **Segmentos URI** (edición en § 4.5): tres conceptos nuevos —`source`
  (token: slug), `finding` (token: UUIDv7, por ser aserción) y `anchor` (token:
  UUIDv7)— siguiendo la regla de composición `{uri_base}{segmento}/{token}` ya
  establecida.

### 20.9 Configuración: bloque `[research]` del manifest

Se añade un bloque opcional al `manifest.toml` (§ 8), con defaults sensatos para
que un proyecto que no investigue no pague coste alguno:

```toml
[research]
enabled = true                      # si false, el sistema queda inerte
# Procedencias de interés para el protocolo multilingüe (informativo para el skill).
source_languages = ["de", "pl", "en", "fr"]
# Fiabilidad mínima para que un hallazgo pueda promoverse a ancla.
min_reliability_for_anchor = "media"
```

Además, `factual_anchor` se suma a la lista de validators activables en
`[validators].enabled` (§ 8.1), y `sources` a `[vocabularies].active`.

### 20.10 Encaje con los axiomas (§ 16) y disciplina de scope

- **No reabre ningún axioma.** Texto plano (4) intacto; rdflib, no Grafeo (2) —el
  sistema funciona leyendo Markdown sin búsqueda vectorial; GOLEM sin ontología
  propia (3) —se usa Inference/`E13` y `E55`; solo Agent Skills (7) —research y
  verify son skills, no commands legacy; sin scripts shell (6).
- **Sinergia con vector search (horizonte demand-pulled), sin dependerla.** La búsqueda vectorial
  (ChromaDB sobre rdflib — **no** Grafeo) mejoraría la recuperación
  semántica sobre un corpus grande de fuentes, pero **no es prerrequisito**: la
  primera versión opera con el agente leyendo los Markdown de `bible/research/`
  directamente. No se adelanta plomería de los vectores (respeta la disciplina de
  scope). El análisis de coste y viabilidad de los vectores está en § 20.12.
- **Versión: v0.2.0, milestone propio.** Por su peso, este sistema es el hito
  **M4** (§ 15.5) y se libera como **v0.2.0**. La búsqueda vectorial es una
  capacidad del **horizonte demand-pulled** (sin versión asignada; se activa ante
  su disparador, ver § 12.3 / § 20.12), no un hito programado. El
  preset externo `fiction-book-writing`
  (§ 17.2) sigue siendo solo inspiración de templates.

### 20.11 Resumen de artefactos nuevos

| Artefacto | Dónde | Tipo |
|---|---|---|
| `/bookwright-research <tema>` | command source + skill | Proceso (LLM) |
| `/bookwright-verify` | command source + skill | Verificación (LLM) |
| `factual_anchor` | `src/bookwright/validation/` | Verificación (código) |
| `io/research.py` | indexer | Persistencia grafo |
| `sources.ttl` | `resources/vocabularies/` | Vocabulario `E55`/`E13` |
| `bible/research/` | proyecto generado | Almacenamiento texto plano |
| `[research]` | `manifest.toml` | Configuración |
| segmentos `source`/`finding`/`anchor` | § 4.5 | URIs |

### 20.12 Búsqueda vectorial: viabilidad y coste (horizonte demand-pulled)

> Análisis pedido por el propietario al decidir mantener los vectores tras
> descartar Grafeo. Conclusión adelantada: **es viable, barato y de bajo riesgo**
> implementarlo desacoplado, sin Grafeo. No es trabajo de un hito programado: es
> una capacidad del **horizonte demand-pulled** (sin versión asignada), que se
> activa solo ante un corpus real multi-libro/serie o un fallo medido de
> structural-recall en una skill.

**Qué problema resuelve.** El grafo `rdflib` responde preguntas *estructuradas*
(¿qué anclas restringen a este personaje? ¿qué eventos hay antes de 1944?). No
responde preguntas *semánticas* sobre el texto libre ("¿dónde menciono algo
parecido a la burocracia de fronteras?", "tráeme las notas de investigación
relacionadas con esta escena"). Cuando `bible/research/` crece a decenas de temas
y cientos de citas, el agente no puede cargarlo entero en contexto; necesita
recuperar los fragmentos relevantes. Eso es *retrieval* semántico: vectores.

**Por qué no necesita Grafeo.** Grafeo agrupaba grafo + vectores en una sola
librería. Pero las dos capacidades son ortogonales: el grafo es la fuente de
verdad estructurada (rdflib) y los vectores son un **índice secundario
reconstruible**. Separarlos es la arquitectura estándar (p. ej. RAG sobre
cualquier corpus) y evita atarse a una librería de un solo mantenedor (la misma
razón del axioma 2). El `Indexer Protocol` (§ 12.1) ya aísla esto: la capa
vectorial se añade *al lado*, no *dentro* del motor de grafo.

**Forma de la implementación.**

1. **Chunking + embeddings**: trocear `bible/research/` y el manuscrito en
   fragmentos (por hallazgo, por escena), generar embeddings y guardarlos en un
   vector store embebido (ChromaDB, en `.bookwright/cache/`, en `.gitignore`).
2. **Comando** `bookwright graph reindex --vectors` (o flag de `graph build`) que
   construye/actualiza el índice; reconstruible en cualquier momento desde el
   texto plano (no rompe el axioma 4).
3. **Consumo**: los skills `bookwright-research` y `bookwright-verify` recuperan
   los k fragmentos más cercanos antes de razonar, en vez de leer todo el corpus.
4. **Dependencia opcional**: el extra `vectors` del `pyproject` (§ 14.1). Si no se
   instala, todo lo demás funciona; los vectores son una mejora, no un requisito
   (degradación elegante a "el agente lee los Markdown directamente").

**Coste y riesgo.**

| Dimensión | Valoración |
|---|---|
| **Dependencias** | 1 extra opcional (`chromadb`). No toca el core ni el grafo. |
| **Embeddings** | Decisión abierta: locales (`sentence-transformers`, sin coste por uso, ~80–400 MB de modelo) o API (coste mínimo por token, sin modelo local). Se elige en v0.4. |
| **Almacenamiento** | Índice en `cache/`, reconstruible, fuera de git. Irrelevante para el tamaño del repo. |
| **Esfuerzo** | ~1 iteración (chunking + store + comando reindex + integración en 2 skills). Contenido, sin tocar M0–M4. |
| **Riesgo de scope** | Bajo: aislado tras el Protocol y el extra opcional; si se abandona, se borra sin tocar el grafo ni los commands. |
| **Determinismo** | Los vectores son *retrieval*, no validación. No afectan a `factual_anchor` ni a los validators deterministas; solo mejoran qué lee el LLM. |

**Recomendación.** Mantener los vectores como **v0.4**, después de M4 y M5. M4 los
**aprovecha si están** pero no los necesita: la primera versión de investigación
opera con el agente leyendo `bible/research/` directamente, y los vectores se
enchufan después como mejora de recuperación cuando el corpus lo justifique. Así
no se adelanta plomería (disciplina de scope) y el valor llega incremental.

## 21. Extensión de diseño: Orquestación de contexto (v0.3)

> **Nota de procedencia.** Como § 20, esta sección se añade *después* del cuerpo
> original (§§ 1–19) y de la extensión de investigación (§ 20). Se ratifica como
> **extensión, no revisión**: no reabre ninguna decisión de § 16. Las ediciones
> aguas arriba son aditivas: dos comandos nuevos en § 5.1, un bloque `[focus]` en
> § 8, y un hito **M5** en § 15.5 que **toma el hueco v0.3.0** y desplaza la
> búsqueda vectorial a v0.4 (export sigue en v1.0). Decisión de roadmap visible y
> reversible: si se prefiere conservar vectores en v0.3, solo se renumera el
> release; el diseño no cambia.

### 21.1 El problema: falta el hilo conductor

Spec Kit "sabe qué planificar" cuando ejecutas `/speckit-plan` porque tiene una
**máquina de estados con un puntero al estado actual**: el branch `NNN-name` más
el directorio `specs/NNN/` responden a *"¿dónde estoy y qué he decidido?"*, y
cada comando lee los artefactos previos y escribe el siguiente. La intención se
declara **una vez** (`/speckit-specify`) y queda persistida.

Bookwright no tenía ese hilo. Sus skills (los 10 de § 10.4, más `bookwright-research`
y `bookwright-verify` de § 20) son herramientas *à la carte*: leen el corpus en
texto plano, pero **no hay puntero de foco** ("qué trabajo ahora") ni un artefacto
que cada skill consulte para orientarse al arrancar una sesión nueva. Síntoma
observado en uso real: `bookwright-research`, sin contexto de sesión, no podía
inferir qué investigar y **preguntaba el tema en blanco** —algo que en Spec Kit
no pasa porque el `spec.md` ya está ahí.

Y escribir un libro **no es lineal**: el autor salta entre biblia, redacción,
investigación, validación y verificación (el flujo de § 3.2 es un ciclo, no una
tubería). Eso hace el hilo conductor *más* necesario, no menos: como no hay una
secuencia fija "después de X viene Y", el "qué hacer ahora" hay que **computarlo
desde el estado**, no cablearlo. Y lo notable es que **ese estado ya existe
estructuralmente** en el grafo: los Hallazgos abiertos (`bw:open`) y las Anclas
sin fuente fiable (§ 20.3) **son** la cola de investigación pendiente; nadie la
consumía.

### 21.2 Tres capas: autoral, derivado, juicio

El sistema separa a propósito tres clases de estado que antes se confundían:

```
CLI  bookwright status   →  hechos derivados + acción sugerida   [DETERMINISTA, testeable]
Skill (el LLM lo lee)    →  prioriza, redacta, investiga         [NO determinista, fuera del CLI]
```

1. **Autoral — el foco/intención.** Pequeño, lo escribe el autor, vive en texto
   plano canónico (bloque `[focus]` del `manifest.toml`, § 21.3). No se computa.
2. **Derivado — el "qué falta / qué sigue".** **Computado**, no escrito a mano:
   una función pura SPARQL sobre `graph.ttl` (§ 21.4), tan determinista como
   `bookwright validate` —que ya es estado derivado. Encima, una tabla de reglas
   estática produce las acciones recomendadas (§ 21.5).
3. **Juicio — la skill (LLM).** Priorizar, redactar con matiz, hacer la
   investigación. Lo único no determinista, y por eso vive *por encima* de la
   frontera del CLI.

**Principio rector:** *El estado se computa, nunca se inventa; el juicio vive en
las skills, no en el CLI. La verdad sigue en texto plano; `status.json` es una
proyección efímera.*

**Alternativa descartada (decisión clave del hito).** La tentación natural es una
**lista de tareas escrita a mano** (un JSON de TODOs en `.bookwright/`) que las
skills cargan y actualizan. Se rechaza por dos razones: (a) sería intención
autoral en formato opaco fuera del corpus canónico —viola el axioma 4 (texto
plano fuente de verdad)—; y (b) una lista mantenida a mano **se desincroniza** del
texto. Además, escribir un libro no se descompone en un DAG de tareas hechas/
no-hechas como el software: lo durable no son "tareas" sino *estado sin resolver*.
Por eso la cola de trabajo es **derivada** (una vista del grafo, siempre correcta
porque se recalcula), y lo único autoral es el puntero de foco: pequeño y en TOML.

### 21.3 Estado autoral: el bloque `[focus]`

Se añade un bloque opcional al `manifest.toml` (§ 8), modelado como los demás
(un `FocusBlock` Pydantic con `default_factory`, análogo a `ResearchBlock`):

```toml
[focus]
target = "arco de Berlín"            # qué se trabaja ahora (texto libre)
notes = "reconciliar la timeline tras el cap. 5"  # hilos/decisiones pendientes
updated_at = "2026-06-05"            # ISO 8601, lo fija el CLI al escribir
```

Tres comandos nuevos (§ 5.1) lo gobiernan: `bookwright focus show` (legible o
`--json`), `bookwright focus set --target … [--notes …]` (crea/actualiza
preservando comentarios vía tomlkit, fija `updated_at`) y `bookwright focus clear`.
El bloque es enteramente opcional: su ausencia no afecta a ningún otro comando.
Es texto plano, versionable y superviviente a la desaparición del toolkit
(axioma 4).

Es la **bitácora mínima**: foco actual + notas. Se descarta para v0.3 un
historial *append-only* / journal versionado: reconstruir el hilo conductor no
exige historia, solo el estado presente; lo demás sería over-engineering.

### 21.4 Estado derivado: `bookwright status`

`bookwright status` computa el estado del proyecto como una **función pura SPARQL**
sobre `graph.ttl`. No añade ninguna clase ni propiedad: solo **consulta** el
esquema congelado (axioma 3, Principio X). Reconstruye el grafo si está obsoleto,
igual que `bookwright validate` (resolviendo la obsolescencia de la caché como ya
se hace con `graph.ttl`). Computa estos **hechos**:

- **Foco y fase**: eco del bloque `[focus]` y de `book.status`.
- **Preguntas de investigación abiertas**: los Hallazgos con `bw:open true`
  (§ 20.3) —la cola "bottom-up" de investigación.
- **Anclas sin fuente suficiente** o con target irresoluble: reutiliza la lógica
  del validator `factual_anchor` (§ 20.6), sin duplicarla.
- **Hallazgos/anclas por debajo de `research.min_reliability_for_anchor`** (§ 20.9).
- **Resumen de validación**: conteos por severidad, **reutilizando** el runner
  `run_validators` (`src/bookwright/validation/runner.py`), que ya devuelve un
  orden total byte-idéntico (SC-003).

Las consultas usan los predicados reales de `sources.ttl` (§ 20.8). Por ejemplo:

```sparql
# Cola "bottom-up": preguntas de investigación abiertas
SELECT ?finding WHERE { ?finding bw:open true }

# Anclas que constriñen una entidad pero carecen de fuente de fiabilidad alta
SELECT ?anchor ?entity WHERE {
  ?anchor bw:promotes ?finding ; bw:constrains ?entity .
  FILTER NOT EXISTS { ?finding bw:supportedBy ?s . ?s bw:reliability rel:alta }
}
```

El reporte se cachea en `.bookwright/cache/status.json` (gitignored), regenerado
en cada ejecución. La caché es un **artefacto derivado, reconstruible, nunca
fuente de verdad** —igual que `graph.ttl` y que el índice vectorial de v0.4
(§ 12.3); coherente con el axioma 4.

**Determinismo y testabilidad.** Mismo corpus → mismos hechos byte a byte, sin
juicio ni red. Es la razón por la que esto vive en el CLI y no en la skill: la
parte computada es unit-testeable (Principio VIII); el juicio queda fuera del gate.

### 21.5 `next_actions`: la tabla de reglas hecho→acción

Sobre los hechos, una **tabla de reglas estática** mapea cada predicado de estado
a una acción recomendada: skill a invocar + plantilla de prompt + razón/prioridad.

| Predicado de estado | Acción recomendada | Prompt (plantilla) |
|---|---|---|
| Hay N preguntas abiertas / anclas sin resolver | `bookwright-research` | "Investiga estas N preguntas abiertas: …" |
| Hay anclas/hallazgos de fiabilidad insuficiente | `bookwright-research` | "Refuerza la procedencia de: …" |
| Hay borrador y anclas sin verificar | `bookwright-verify` | "Verifica el manuscrito contra estas anclas: …" |
| Hay violaciones de continuidad | revisar la biblia / `bookwright-continuity` | "Resuelve estas inconsistencias: …" |
| No hay foco definido | `bookwright focus set` | "Define el foco actual del proyecto." |

Se implementa como una **función pura** `state → list[Action]` en su propio
módulo, con la tabla estática: **unit-testeable sin grafo**. El orden de salida es
estable (prioridad, luego clave) para que el JSON sea byte-idéntico. El juicio
—priorizar entre acciones, redactar con matiz, ejecutar la investigación— sigue
en la skill, no en la tabla.

Esto **absorbe y eleva** la idea vaga de un skill de autoría `bookwright-status`
que figuraba en el roadmap v0.4 (§ 15.5): aquí no es un skill LLM, sino un **verbo
de CLI determinista**, que es lo que un "hilo conductor" necesita ser.

### 21.6 El contrato JSON

`bookwright status` respeta el patrón de § 5.3 (Principio IX): un único documento
JSON de éxito en una línea compacta a stdout, prosa a stderr, errores vía
`BookwrightError` (§ errores, iteración 018). Forma del sobre:

```json
{"status":"ok",
 "focus":{"target":"arco de Berlín","updated_at":"2026-06-05"},
 "state":{"phase":"drafting","open_findings":3,"anchors_unsourced":1,"violations":{"error":0,"warning":2}},
 "next_actions":[{"skill":"bookwright-research","prompt":"Investiga estas 3 preguntas abiertas: …","reason":"3 hallazgos abiertos"}]}
```

### 21.7 El bucle cerrado: las skills consumen el estado

El hilo solo funciona si las skills lo usan. Cada `SKILL.md` de la suite gana dos
ganchos:

- **Al iniciar**: consulta `bookwright status` para orientarse (foco actual + qué
  falta). En `claude`, vía inyección de contexto dinámico `!`bookwright status --json``
  (§ 11.5); en `generic`, como paso explícito a ejecutar (estándar puro).
- **Al terminar**: una sección **"Próximos pasos"** que muestra las `next_actions`
  relevantes con sus prompts listos para pegar.

El caso que motivó el hito: **`bookwright-research` en modo bottom-up**. Sin tema
explícito, consulta `status`, recupera los Hallazgos abiertos y las anclas sin
resolver, y los ofrece como cola de investigación —en vez de preguntar en blanco.
Con tema explícito, opera top-down como hasta ahora (§ 20.4). Donde tenga sentido
tras una transición de fase (p. ej. cerrar la biblia), una skill puede actualizar
el foco con `bookwright focus set`. Todo es **inerte** si `status` no aporta nada:
un proyecto sin `[focus]` ni `bible/research/` funciona exactamente igual que hoy.

### 21.8 Encaje con los axiomas (§ 16) y disciplina de scope

- **No reabre ningún axioma.** Texto plano (4): `focus` en TOML, `status.json` es
  caché; GOLEM sin ontología propia (3) y Principio X: `status` **solo consulta**
  SPARQL, cero clases nuevas; rdflib (2); solo Agent Skills (7): el bucle se cablea
  en los `SKILL.md`, no en commands legacy; **sin scripts shell** (6): `status` y
  `focus` son subcomandos Typer. *Contraste con Spec Kit:* sus scripts bash emiten
  JSON de punteros/paths; aquí el equivalente es un **verbo de CLI de primera
  clase**, idiomático Python, que las skills invocan.
- **No requiere enmienda constitucional**: ni cambio de stack ni principio nuevo;
  todo encaja en los principios I, VI, VIII, IX y X vigentes.
- **Fuera de scope (no adelantar plomería).** Historial/journal append-only;
  cualquier juicio LLM dentro del CLI; clases de ontología; mutar el grafo; y la
  **búsqueda vectorial (v0.4)**: `status` no la requiere ni la adelanta.
- **Versión: v0.3.0, hito M5.** Por su peso es milestone propio. La búsqueda
  vectorial pasa a **v0.4** y el export sigue en **v1.0** (§ 15.5).

### 21.9 Resumen de artefactos nuevos

| Artefacto | Dónde | Tipo |
|---|---|---|
| `bookwright status` | `src/bookwright/commands/status.py` | Estado derivado (CLI, determinista) |
| `bookwright focus` (`show`/`set`/`clear`) | `src/bookwright/commands/focus.py` | Estado autoral (CLI) |
| `[focus]` + `FocusBlock` | `manifest.toml` + `core/_focus_block.py` | Configuración autoral |
| Tabla de reglas `next_actions` | `commands/status*` (función pura) | Recomendación (determinista) |
| Consultas SPARQL de agregación | `validation/` o `status/queries.py` | Derivación de estado |
| `.bookwright/cache/status.json` | proyecto (gitignored) | Caché derivada |
| Sección "Próximos pasos" | cada `SKILL.md` | Consumo del estado (LLM) |

---

**Fin del documento.**
