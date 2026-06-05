# Bookwright

**Toolkit de autoría spec-driven para novelas, ensayos y memorias.**

*[Read in English](README.md)*

Bookwright aplica el patrón Spec-Driven Development a la escritura de
formato largo: destilas tus ideas en un conjunto reducido de documentos
canónicos (constitución, biblia, outline, escenas) y dejas que un agente
IA escriba a partir de *ellos*, no de un chat libre. Tu libro vive en
texto plano, versionado en git, completamente auditable, y sobrevive al
toolkit.

> ### Estado: v0.2.0
>
> Dos hitos están en `main`. **v0.1.0** (el toolkit base, iteraciones
> 1–11): scaffolding del proyecto (`bookwright init`), el modelo de
> dominio GOLEM, el indexer y los comandos `bookwright graph`, las skills
> de autoría materializadas como Agent Skills, y el sistema de validación
> de continuidad. **v0.2.0 / M4** (investigación y verificación,
> iteraciones 12–18): el modelo de procedencia `Source` / `Finding` /
> `Anchor`, las skills `/bookwright-research` y `/bookwright-verify`, el
> validador `factual_anchor` y la envoltura `--json` unificada. La
> documentación de usuario completa vive en el
> [sitio de documentación](docs/index.md).

## El loop del escritor

1. **Idea libremente** — conversa con tu agente o tu libreta y vuelca un
   brief a Markdown.
2. **Scaffolding del proyecto** —
   `bookwright init mi-novela --integration claude` genera la estructura
   de directorios, los templates de los documentos canónicos e instala
   los *Agent Skills* de Bookwright en `.claude/skills/`.
3. **Destila, en orden** — abre el proyecto con Claude Code (o cualquier
   agente compatible con [agentskills.io](https://agentskills.io)) y
   ejecuta:

   ```
   /bookwright-constitution   ← reglas no negociables de la obra
   /bookwright-bible          ← personajes, settings, lore
   /bookwright-outline        ← estructura de actos/capítulos
   /bookwright-scenes         ← desglose beat por beat
   /bookwright-draft          ← generación de prosa por escena
   ```

   Cada comando toma input no estructurado y produce un artefacto
   Markdown / Turtle versionable. Iteras los *documentos*, no el
   borrador.

4. **Construye y valida** — `bookwright graph build` deriva el grafo
   narrativo GOLEM y `bookwright validate` corre los chequeos de
   continuidad (continuidad temporal, presencia de personajes,
   focalización, continuidad de settings).

5. **Edita en tu editor favorito** — Bookwright no es un editor de
   texto. Abre los `.md` en Obsidian, Scrivener, VS Code o vim.

## Instalación

```bash
uv build
pipx install ./dist/bookwright_cli-*.whl   # o: uv tool install ./dist/*.whl
bookwright version
```

Para desarrollar sobre el toolkit, sincroniza el entorno del proyecto:

```bash
uv sync
uv run bookwright --help
```

## Quickstart en 5 minutos

```bash
bookwright init mi-novela --integration claude   # scaffolding + Agent Skills
cd mi-novela
```

Abre el proyecto en tu agente y destila tu idea con las skills (no editas los
documentos a mano; las skills leen tu brief y te preguntan lo que falte):

```
/bookwright-constitution lee idea.md y destila la constitución
/bookwright-bible        ← personajes, settings, cronología
/bookwright-outline      ← arcos y estructura
/bookwright-scenes       ← desglose en escenas
/bookwright-draft        ← redacta la prosa de una escena
```

Para obra basada en hechos (p. ej. novela histórica), el loop opcional de
investigación documenta fuentes, hallazgos y anclas, y contrasta la prosa
contra ellas:

```
/bookwright-research <tema>   ← documenta hallazgos con procedencia completa
/bookwright-verify            ← contrasta la prosa redactada con las anclas
```

Y construye/valida desde el CLI:

```bash
bookwright graph build                            # → bible/graph.ttl
bookwright graph query "SELECT ?c WHERE { ?c a golem:G1_Character }" --json
bookwright validate                               # exit 0 si no hay errores
```

¿Quieres cambiar de integración (p. ej. de `claude` a `generic`)?

```bash
bookwright integration use generic                # re-materializa en .agents/skills/
```

El recorrido completo está en
[docs/getting-started.md](docs/getting-started.md).

## Principios de diseño

- **El texto plano es la fuente de verdad.** Manuscrito, biblia,
  constitución y grafo narrativo son Markdown, TOML o Turtle (RDF).
  Auditables por humanos, diffables en git, portables.
- **Agnóstico de agente.** La capa de comandos se materializa como
  [Agent Skills](https://agentskills.io) portables. Bookwright entrega dos
  integraciones (`claude`, `generic`); agentes como Codex, Cursor o Copilot
  consumen la salida `generic` directamente, sin integración nativa dedicada.
- **Batch, no conversacional.** Tú consolidas el input; el comando lo
  destila. El agente no es un co-escritor frase a frase.
- **GOLEM por debajo.** El grafo narrativo usa la
  [ontología GOLEM](https://github.com/GOLEM-lab/golem-ontology)
  publicada (personajes, eventos, settings, relaciones, estructura
  narrativa, procedencia de inferencias) serializada en Turtle.

## Roadmap y fuera de scope

Hecho: **v0.2 / M4** — investigación y verificación (modelo de procedencia,
skills `research`/`verify`, validador `factual_anchor`). Planificado:
**v0.3** — búsqueda vectorial (ChromaDB sobre rdflib, desacoplada); **v1.0** —
export a EPUB / PDF / impresión vía pandoc.

**Cancelado (decisión del owner), no lo pidas:** presets de género / paquetes
de plantilla (la resolución es de 2 capas, overrides → core); el motor
`Grafeo` / `GrafeoIndexer`; integraciones más allá de `claude` y `generic`;
el sistema de extensiones. Agentes como Codex, Cursor o Copilot ya se soportan
hoy vía la integración `generic` con `--integration-options="--skills-dir …"`,
sin integración nativa dedicada.

## Documentos del proyecto

- **[Sitio de documentación](docs/index.md)** — guía de usuario completa
  (primeros pasos, comandos, validación, extender, FAQ).
- **[bookwright-design.md](bookwright-design.md)** — la especificación
  de diseño completa. La numeración de secciones es load-bearing.
- **[bookwright-implementation-plan.md](bookwright-implementation-plan.md)**
  — el plan de iteraciones ordenado.
- **[.specify/memory/constitution.md](.specify/memory/constitution.md)** —
  los principios ratificados y vinculantes para cada PR.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — instalación, quality gates y
  cómo extender el toolkit (nueva integración, validador, vocabulario).
- **[CHANGELOG.md](CHANGELOG.md)** — historial de cambios.

## Licencia

[Apache-2.0](LICENSE). Consulta [NOTICE](NOTICE) para la atribución.

Esta licencia cubre **solo el software bookwright**. El contenido que crees
con la herramienta —*bibles*, escaletas, manuscritos y los grafos de
conocimiento derivados— sigue siendo enteramente tuyo.
