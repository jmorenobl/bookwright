# Cambios

Registro de versiones de Bookwright. Sigue el espíritu de
[Keep a Changelog](https://keepachangelog.com/es/) y el versionado semántico.

## v0.2.0 — Investigación y procedencia (M4)

Añade el sistema de **investigación con procedencia**, opcional y aditivo: una obra
puede documentar qué sabe, de dónde y con qué fiabilidad, y dejar que esa investigación
restrinja la ficción de forma verificable. Un proyecto que no lo usa no paga nada por
él. Ver [Investigación](research.md).

### Añadido

- **Modelo de procedencia `Source` / `Finding` / `Anchor`** serializado a RDF, sin
  añadir clases nuevas a la ontología GOLEM (reutiliza `crm:E55_Type` y
  `crm:E13_Attribute_Assignment`). Vive en texto plano bajo `bible/research/`.
- **Bloque `[research]` en el manifiesto** (`enabled`, `source_languages`,
  `min_reliability_for_anchor`) con validación ISO 639-1 de los idiomas de fuente.
- **Lector estricto de `bible/research/`**: facetas de procedencia obligatorias,
  vocabularios controlados de `type` y `reliability`, y la regla de `translation` para
  fuentes en lengua extranjera (multilingüismo como invariante de procedencia).
- **Skill `/bookwright-research`**: investiga un tema y lo documenta como hallazgos con
  procedencia, marcando cuáles son anclas. Dispara con prompts en español e inglés.
- **Skill `/bookwright-verify`**: verifica el manuscrito ya redactado contra las anclas
  (anacronismos, errores de procedimiento, inexactitudes culturales). Solo lectura,
  post-draft; paso manual documentado.
- **Validador `factual_anchor`**: audita en CI la integridad estructural y cronológica
  de las anclas (reglas R1–R5; R5, el anacronismo de lapso temporal, es `error`). Inerte
  cuando la investigación está apagada o no hay anclas. Ver [Validación](validation.md).
- **Ejemplo trabajado `tiny-historical`**: una novela histórica mínima con un corpus de
  investigación atribuido y tres defectos plantados, más un test E2E que recorre
  `build → query → validate` y un oráculo co-localizado de hallazgos esperados.
- **Documentación**: la página [Investigación](research.md), la referencia de
  `factual_anchor` en [Validación](validation.md) y las skills de investigación en
  [El flujo de autoría](authoring.md).

## v0.1.0 — Toolkit base (M0–M3)

Primera versión del toolkit de autoría *spec-driven*.

### Añadido

- **CLI `bookwright`** (`init`, `check`, `version`, `validate`, `graph build`,
  `graph query`, `integration use`) con contrato JSON-sobre-stdout para cada comando
  consumido por agentes.
- **Manifiesto `manifest.toml`** (modelo `pydantic` round-tripped con `tomlkit`,
  preservando comentarios) y scaffolding de proyecto con `bookwright init`.
- **Modelo de dominio narrativo GOLEM** serializado a Turtle/RDF, con procedencia
  estructural (`file:line`) de cada aserción derivada.
- **Indexador `rdflib`** y los verbos `graph build` / `graph query` (SPARQL).
- **Las 10 skills de autoría** materializadas como *Agent Skills* portables, con dos
  integraciones: `claude` (`.claude/skills/`) y `generic` (`.agents/skills/`).
- **Sistema de validación de continuidad**: `character_presence`, `focalization`,
  `setting_continuity` y `temporal` sobre el grafo derivado.
- **Plantillas** de biblia, outline y constitución, y los *fixtures* de ejemplo
  (`tiny-novel`, `tiny-essay`, `tiny-memoir`).
