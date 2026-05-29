# Bookwright

**Toolkit de autoría spec-driven para novelas, ensayos y memorias.**

*[Read in English](README.md)*

Bookwright aplica el patrón Spec-Driven Development a la escritura de
formato largo: destilas tus ideas en un conjunto reducido de documentos
canónicos (constitución, biblia, outline, escenas) y dejas que un agente
IA escriba a partir de *ellos*, no de un chat libre. Tu libro vive en
texto plano, versionado en git, completamente auditable, y sobrevive al
toolkit.

> ### Estado: pre-alpha
>
> Bookwright está **en construcción activa**. Las iteraciones 1 y 2 de 11
> ya están en `main`; la iteración 3 (arquitectura de integraciones)
> está en curso. Los comandos de autoría que un escritor realmente usa
> (`/bookwright-constitution`, `/bookwright-bible`,
> `/bookwright-outline`, `/bookwright-draft`, …) llegan en las
> iteraciones 7–9.
>
> Si eres escritor y estás evaluando Bookwright hoy, **marca el
> repositorio y vuelve en v0.1**. Si eres colaborador o desarrollas
> agentes IA, sigue leyendo.

## Cómo funcionará (el loop del escritor)

1. **Idea libremente** — conversa con claude.ai, Gemini, ChatGPT o tu
   libreta. Vuelca la conversación o un brief a un Markdown.
2. **Scaffolding del proyecto** —
   `bookwright init mi-novela --integration claude` genera la estructura
   de directorios, los templates de los documentos canónicos e instala
   los *Agent Skills* de Bookwright en `.claude/skills/` para que tu
   agente pueda invocarlos.
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

4. **Valida la continuidad** — `bookwright validate` corre chequeos de
   consistencia (continuidad temporal, presencia de personajes,
   focalización, anclas históricas) contra el grafo narrativo derivado
   de la biblia y el manuscrito.

5. **Edita en tu editor favorito** — Bookwright no es un editor de
   texto. Abre los `.md` en Obsidian, Scrivener, VS Code, vim. El
   toolkit te devuelve el manuscrito en texto plano.

## Principios de diseño

- **El texto plano es la fuente de verdad.** Manuscrito, biblia,
  constitución y grafo narrativo son Markdown, TOML o Turtle (RDF).
  Auditables por humanos, diffables en git, portables.
- **Agnóstico de agente.** Bookwright apunta a Claude Code primero, pero
  la capa de comandos se materializa como
  [Agent Skills](https://agentskills.io) portables. v0 entrega dos
  integraciones (`claude`, `generic`); variantes nativas de Copilot,
  Gemini y Cursor están en el roadmap.
- **Batch, no conversacional.** Tú consolidas el input; el comando lo
  destila. El agente no es un co-escritor frase a frase.
- **GOLEM por debajo.** El grafo narrativo usa la
  [ontología GOLEM](https://github.com/GOLEM-lab/golem-ontology)
  publicada (personajes, eventos, settings, relaciones, estructura
  narrativa, procedencia de inferencias) serializada en Turtle.

## Qué funciona hoy

Solo está conectado el esqueleto del toolchain. Todavía no existe
`bookwright init`.

```bash
uv sync                          # instala el entorno del proyecto
uv run bookwright --help         # lista los comandos disponibles
uv run bookwright version        # versión del CLI y del schema
uv run bookwright check          # verifica el toolchain
```

Tanto `version` como `check` aceptan `--json` para consumo por agentes.

## Roadmap hacia v0

El plan de 11 iteraciones vive en
[bookwright-implementation-plan.md](bookwright-implementation-plan.md).
Hitos:

| Hito | Iteraciones | Qué desbloquea |
|---|---|---|
| **M0** — toolchain | 1–4 | `bookwright init`, scaffolding del proyecto |
| **M1** — grafo | 5–6 | Modelo de dominio GOLEM, comandos `bookwright graph` |
| **M2** — autoría | 7–9 | Templates + los 10 comandos fuente + materialización como Agent Skills |
| **M3** — validación | 10–11 | Chequeos de continuidad, fixtures end-to-end, documentación |

Fuera del scope de v0 (no pedirlas para v0): presets de género (v0.2),
búsqueda vectorial (v0.3), integraciones adicionales (v0.4), sistema de
extensiones (v0.5), export a EPUB/PDF (v1.0).

## Documentos del proyecto

- **[bookwright-design.md](bookwright-design.md)** — la especificación
  de diseño completa (~1.4k líneas). La numeración de secciones es
  load-bearing.
- **[bookwright-implementation-plan.md](bookwright-implementation-plan.md)**
  — el plan de iteraciones ordenado.
- **[.specify/memory/constitution.md](.specify/memory/constitution.md)** —
  los principios ratificados y vinculantes para cada PR.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — instalación, quality gates,
  pre-commit hooks para colaboradores y agentes IA que trabajan sobre
  el toolkit en sí.

## Licencia

A decidir antes de v0.1. Tracked en el documento de diseño.
