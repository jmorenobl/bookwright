# Bookwright

**Toolkit de autoría spec-driven para novelas, ensayos y memorias.**

Bookwright lleva el patrón *Spec-Driven Development* a la escritura de formato
largo: destilas tus ideas en un conjunto reducido de documentos canónicos
—constitución, biblia, outline, escenas— y dejas que un agente de IA escriba a
partir de *ellos*, no de un chat libre. Tu libro vive en texto plano, versionado
en git, completamente auditable, y sobrevive al toolkit.

## Por qué Bookwright

- **El texto plano es la fuente de verdad.** Manuscrito, biblia, constitución y
  grafo narrativo son Markdown, TOML o Turtle (RDF): auditables por humanos,
  *diffables* en git, portables.
- **Agnóstico de agente.** La capa de comandos se materializa como
  [Agent Skills](https://agentskills.io) portables. v0 entrega dos
  integraciones: `claude` (escribe en `.claude/skills/`) y `generic`
  (escribe en `.agents/skills/`).
- **Grafo narrativo GOLEM.** Personajes, eventos, settings, relaciones y
  procedencia de inferencias se serializan en Turtle con la ontología
  [GOLEM](https://github.com/GOLEM-lab/golem-ontology), consultable con SPARQL.
- **Validación de continuidad.** `bookwright validate` comprueba presencia de
  personajes, focalización, continuidad de settings y coherencia temporal sobre
  el grafo derivado de tu biblia y tu manuscrito.

## El loop del escritor

1. **Idea libremente** en tu agente o tu libreta y vuelca un brief a Markdown.
2. **Scaffolding**: `bookwright init mi-novela --integration claude`.
3. **Destila, en orden**: usa los *Agent Skills* (`/bookwright-constitution`,
   `/bookwright-bible`, `/bookwright-outline`, `/bookwright-scenes`,
   `/bookwright-draft`, …) para convertir input no estructurado en artefactos
   versionables.
4. **Construye y consulta el grafo**: `bookwright graph build` y
   `bookwright graph query`.
5. **Valida la continuidad**: `bookwright validate`.

¿Listo para empezar? Ve a [Primeros pasos](getting-started.md).
