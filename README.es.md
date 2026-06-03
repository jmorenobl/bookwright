# Bookwright

**Toolkit de autoría spec-driven para novelas, ensayos y memorias.**

*[Read in English](README.md)*

Bookwright aplica el patrón Spec-Driven Development a la escritura de
formato largo: destilas tus ideas en un conjunto reducido de documentos
canónicos (constitución, biblia, outline, escenas) y dejas que un agente
IA escriba a partir de *ellos*, no de un chat libre. Tu libro vive en
texto plano, versionado en git, completamente auditable, y sobrevive al
toolkit.

> ### Estado: v0.1.0
>
> Las once iteraciones del plan v0 están en `main`: scaffolding del
> proyecto (`bookwright init`), el modelo de dominio GOLEM, el indexer y
> los comandos `bookwright graph`, los 10 comandos de autoría
> materializados como Agent Skills, el sistema de validación de
> continuidad, y la capa de fixtures + tests E2E + documentación de esta
> release. La documentación de usuario completa vive en el
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
# edita bible/constitution.md, bible/characters/<slug>.md, bible/timeline.md
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
  [Agent Skills](https://agentskills.io) portables. v0 entrega dos
  integraciones (`claude`, `generic`); variantes nativas de Copilot,
  Gemini y Cursor están en el roadmap.
- **Batch, no conversacional.** Tú consolidas el input; el comando lo
  destila. El agente no es un co-escritor frase a frase.
- **GOLEM por debajo.** El grafo narrativo usa la
  [ontología GOLEM](https://github.com/GOLEM-lab/golem-ontology)
  publicada (personajes, eventos, settings, relaciones, estructura
  narrativa, procedencia de inferencias) serializada en Turtle.

## Fuera del scope de v0

No las pidas para v0: presets de género (v0.2), búsqueda vectorial
(v0.3), integraciones adicionales (v0.4), sistema de extensiones (v0.5),
export a EPUB/PDF (v1.0).

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

[Apache-2.0](LICENSE).
