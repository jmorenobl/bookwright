<p align="center">
  <picture>
    <source srcset="https://raw.githubusercontent.com/jmorenobl/bookwright/main/assets/banner.svg" type="image/svg+xml">
    <img src="https://raw.githubusercontent.com/jmorenobl/bookwright/main/assets/banner.png" alt="Bookwright — toolkit de autoría spec-driven para novelas, ensayos y memorias" width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/jmorenobl/bookwright/actions/workflows/tests.yml"><img src="https://github.com/jmorenobl/bookwright/actions/workflows/tests.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/jmorenobl/bookwright/blob/main/CHANGELOG.md"><img src="https://img.shields.io/badge/version-0.4.5-6f42c1" alt="Versión 0.4.5"></a>
  <a href="https://github.com/jmorenobl/bookwright/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-EUPL--1.2-blue" alt="Licencia: EUPL-1.2"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-3776ab?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/coverage-%E2%89%A580%25-2ea44f" alt="Cobertura ≥80%">
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white" alt="Lint con Ruff"></a>
  <img src="https://img.shields.io/badge/types-mypy%20strict-2a6db2" alt="Tipado con mypy --strict">
  <a href="https://github.com/github/spec-kit"><img src="https://img.shields.io/badge/built%20with-Spec%20Kit-0b7285" alt="Hecho con Spec Kit"></a>
</p>

<p align="center">
  <b>Toolkit de autoría spec-driven para novelas, ensayos y memorias.</b><br>
  <i><a href="https://github.com/jmorenobl/bookwright/blob/main/README.md">Read in English</a></i>
</p>

Bookwright aplica el patrón Spec-Driven Development a la escritura de
formato largo: destilas tus ideas en un puñado de documentos canónicos
(constitución, biblia, outline, escenas) y dejas que un agente IA escriba
a partir de *ellos*, no de un chat libre. Tu libro vive en texto plano,
versionado en git, completamente auditable, y sobrevive al toolkit.

**¿Por qué?** Porque te avisa de que tu personaje tiene los ojos azules en
el capítulo 3 y verdes en el 12 — antes que tu lector. Bookwright deriva un
grafo de conocimiento de tu obra y valida la continuidad (personajes,
settings, cronología, focalización) de forma determinista.

> Estado: **v0.4.5** — usable para investigar, estructurar, redactar y
> validar continuidad. Investiga con procedencia, ingiere la estructura
> narrativa (unidades, funciones y secuencias) y la tipa contra los
> vocabularios de Propp y Greimas. Detalle de cambios en el
> [CHANGELOG](https://github.com/jmorenobl/bookwright/blob/main/CHANGELOG.md).

---

## Cómo se usa, en una frase

Bookwright es **una CLI más un conjunto de skills para tu agente**. Esto
define *dónde* tecleas cada cosa, y es la idea que conviene tener clara
antes de empezar:

| Cuándo | Dónde | Qué |
| --- | --- | --- |
| **Una vez, al empezar** | en tu **terminal** | `bookwright init` |
| **El 95% del tiempo** | dentro de tu **agente** (Claude Code, etc.) | invocas skills: `/bookwright-constitution`, `/bookwright-bible`, … |
| **De vez en cuando** | en tu **terminal** | `bookwright graph build` · `bookwright validate` · `bookwright status` |

Las skills se invocan **dentro del agente**, escribiendo `/bookwright-<comando>`
en el prompt. Lo que escribes después del comando llega a la skill como su
input (una referencia a un archivo, texto pegado, o la conversación previa).

---

## Instalación

El paquete en PyPI es `bookwright-cli`; el comando que instala es `bookwright`.

```bash
uv tool install bookwright-cli   # con uv (recomendado)
pipx install bookwright-cli      # o con pipx
bookwright version
```

¿Probarlo una vez sin instalar nada?

```bash
uvx --from bookwright-cli bookwright version
```

Directamente desde el repositorio (última versión de `main`):

```bash
uv tool install "git+https://github.com/jmorenobl/bookwright"
# o:  pipx install "git+https://github.com/jmorenobl/bookwright"
```

Para desarrollar sobre el toolkit, clona el repo y sincroniza el entorno:

```bash
git clone https://github.com/jmorenobl/bookwright && cd bookwright
uv sync
uv run bookwright --help
```

---

## Quickstart: tu primera escena validada

### 1 · Crea el proyecto · `[en tu terminal]`

```bash
bookwright init mi-novela --integration claude
cd mi-novela
```

Esto genera la estructura (`bible/`, `outline/`, `manuscript/`), el
`manifest.toml` y materializa las skills de Bookwright en `.claude/skills/`.

Vuelca tu idea en un Markdown libre, sin formato obligatorio — la premisa,
los personajes que ya conoces, el tono:

```bash
echo "Un peregrino abandona el Camino de Santiago en la etapa 17..." > idea.md
```

### 2 · Destila tu idea con las skills · `[en tu agente]`

Abre el proyecto en Claude Code e invoca la primera skill. **Esto se teclea
en el prompt del agente, no en la terminal:**

```
/bookwright-constitution lee idea.md y destila la constitución
```

La skill lee tu brief, redacta el artefacto y marca con `[PENDING: ¿…?]` lo
que tu material todavía no decide — sin inventar canon. Una sesión típica:

```
Tú  ▸ /bookwright-constitution lee idea.md y destila la constitución

Claude ▸ He leído idea.md y redactado la constitución en
         bible/constitution.md. Resumen:
           · Voz: tercera persona cercana, foco en el peregrino
           · Pacto con el lector: realismo psicológico, sin giros sobrenaturales
           · Líneas rojas: no resolver el conflicto con coincidencias
         He dejado 2 pendientes que necesito que decidas:
           · [PENDING: ¿en qué año transcurre?]
           · [PENDING: ¿el narrador conoce el final desde el principio?]
```

Resuelves los pendientes cuando quieras (editando el `.md` o volviendo a
invocar la skill) y sigues con el resto del pipeline, **en orden**:

```
/bookwright-bible      ← personajes, settings, cronología, relaciones
/bookwright-outline    ← arcos y estructura de actos/capítulos
/bookwright-scenes     ← desglose en escenas concretas
/bookwright-draft      ← redacta la prosa de UNA escena
```

> Estas cinco son el camino principal. Hay otras skills de apoyo
> (`/bookwright-synopsis`, `/bookwright-clarify` para listar dudas abiertas,
> `/bookwright-checklist` para comprobar si un artefacto está completo,
> `/bookwright-analyze`, `/bookwright-continuity`, `/bookwright-research`,
> `/bookwright-verify`) que usarás cuando las necesites.

### 3 · Construye y valida · `[en tu terminal]`

```bash
bookwright graph build      # deriva el grafo GOLEM → bible/graph.ttl
bookwright validate         # exit 0 si no hay errores de continuidad
```

---

## El loop, no la escalera

Ese orden de cinco pasos es solo tu **primera pasada**. Escribir no es
lineal: investigando una escena descubres un dato que cambia un personaje,
replanteas la estructura a mitad del draft, una decisión tardía contradice
algo que diste por cerrado. Bookwright está hecho para ese ir y venir, no
para una única bajada en escalera.

<p align="center">
  <picture>
    <source srcset="https://raw.githubusercontent.com/jmorenobl/bookwright/main/assets/loop.svg" type="image/svg+xml">
    <img src="https://raw.githubusercontent.com/jmorenobl/bookwright/main/assets/loop.png" alt="El loop del escritor: idea → scaffolding → destila → build y valida → edita, y vuelta a empezar" width="100%">
  </picture>
</p>

A partir de la primera pasada, trabajas en bucle:

- **Descubres algo que cambia el canon** (investigando, o sin más,
  pensando) → reinvocas la skill afectada (`/bookwright-bible`,
  `/bookwright-outline`…). Las skills generativas **actualizan en sitio**:
  respetan tu prosa y los pendientes ya resueltos, y solo rellenan lo que
  sigue abierto. No reescriben lo que ya decidiste.
- **Replanteas la estructura** → vuelves a `/bookwright-outline`, y
  `/bookwright-analyze` te señala qué quedó descolgado entre constitución,
  biblia, outline y escenas (consistencia **pre-draft**).
- **Ya tienes prosa y quieres saber qué rompiste** → `bookwright validate`
  (chequeo determinista sobre el grafo) y `/bookwright-continuity` (el
  manuscrito frente a la biblia: cumplimiento, arcos, cronología,
  **post-draft**).
- **Para obra basada en hechos**, la investigación es su propio sub-loop:
  `/bookwright-research` documenta hallazgos con procedencia y marca cuáles
  son *anclas* que restringen la ficción; `/bookwright-verify` contrasta la
  prosa ya escrita contra esas anclas (anacronismos, errores de
  procedimiento).
- **¿No recuerdas por dónde ibas?** `bookwright focus set` fija tu objetivo
  actual y `bookwright status` deriva el estado y el siguiente paso.

El motor de todo esto es el protocolo `[PENDING]`: dejas un hueco marcado,
sigues avanzando, y lo resuelves cuando el material esté maduro. Un
`[PENDING]` sin responder se trata como *indeciso*, no como una respuesta:
una declaración de voz que sigue como `[PENDING: …]` permanece invisible
para las comprobaciones de continuidad hasta que la decidas de verdad,
nunca una falsa alarma. `/bookwright-clarify` te lista en cualquier momento
las dudas abiertas del proyecto. **No hay una pasada "definitiva"**: hay un manuscrito y un grafo
que convergen iteración a iteración.

El recorrido completo está en
[Primeros pasos](https://github.com/jmorenobl/bookwright/blob/main/docs/getting-started.md).

---

## Principios de diseño

- **El texto plano es la fuente de verdad.** Manuscrito, biblia,
  constitución y grafo son Markdown, TOML o Turtle (RDF). Auditables por
  humanos, diffables en git, portables.
- **Batch, no conversacional.** Tú consolidas el input; la skill lo destila
  en un artefacto versionable. Iteras los *documentos*, no el chat. El
  agente no es un co-escritor frase a frase.
- **Agnóstico de agente.** Las skills se materializan como
  [Agent Skills](https://agentskills.io) portables. Bookwright entrega dos
  integraciones (`claude`, `generic`); agentes como Codex, Cursor o Copilot
  consumen la salida `generic` directamente.
- **GOLEM por debajo.** El grafo narrativo usa la
  [ontología GOLEM](https://github.com/GOLEM-lab/golem-ontology) serializada
  en Turtle. No necesitas tocar RDF para usar Bookwright.

---

## Roadmap y fuera de scope

Bookwright ya cubre investigación con procedencia, orquestación de contexto
(foco autoral y estado derivado con siguiente paso) y la ingesta de la
estructura narrativa: unidades, funciones y secuencias, con tipado opcional
contra los vocabularios de Propp y Greimas y un validador de continuidad
narrativa. La intención durable a través de versiones vive en
[bookwright-roadmap.md](https://github.com/jmorenobl/bookwright/blob/main/bookwright-roadmap.md).

**Horizonte demand-pulled (sin versión asignada)**, se activa solo ante un
disparador concreto, nunca como plumbing especulativo: **búsqueda vectorial**
(se activa con un corpus real multi-libro / serie o ante un fallo medido de
recall estructural) y **export** a EPUB / PDF / impresión (se activa cuando el
flujo de extremo a extremo esté probado sobre un libro real).

**Cancelado (decisión del owner), no lo pidas:** presets de género /
paquetes de plantilla; el motor `Grafeo` / `GrafeoIndexer`; integraciones
más allá de `claude` y `generic`; el sistema de extensiones.

---

## Documentos del proyecto

- **[Sitio de documentación](https://github.com/jmorenobl/bookwright/blob/main/docs/index.md)** — guía de usuario completa
  (primeros pasos, comandos, validación, extender, FAQ).
- **[bookwright-design.md](https://github.com/jmorenobl/bookwright/blob/main/bookwright-design.md)** — la especificación
  de diseño completa.
- **[bookwright-roadmap.md](https://github.com/jmorenobl/bookwright/blob/main/bookwright-roadmap.md)** — la intención
  durable a través de versiones.
- **[CONTRIBUTING.md](https://github.com/jmorenobl/bookwright/blob/main/CONTRIBUTING.md)** — instalación, quality gates y
  cómo extender el toolkit (nueva integración, validador, vocabulario).
- **[CHANGELOG.md](https://github.com/jmorenobl/bookwright/blob/main/CHANGELOG.md)** — historial de cambios.

## Licencia

[EUPL-1.2](https://github.com/jmorenobl/bookwright/blob/main/LICENSE) (Licencia Pública de la Unión Europea v. 1.2; el `LICENSE` incluye el texto oficial en español e inglés). Consulta [NOTICE](https://github.com/jmorenobl/bookwright/blob/main/NOTICE) para la atribución.

Esta licencia cubre **solo el software bookwright**. El contenido que crees
con la herramienta —*bibles*, escaletas, manuscritos y los grafos de
conocimiento derivados— sigue siendo enteramente tuyo.
