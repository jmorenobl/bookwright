# Cambios

Registro de versiones de Bookwright. Sigue el espíritu de
[Keep a Changelog](https://keepachangelog.com/es/) y el versionado semántico.

## v0.4.0 — Estructura narrativa: Propp/Greimas (v0.4)

Da vida de extremo a extremo a la **capa de estructura narrativa** (las clases
`G7`/`G9`/`G10`, modeladas pero sin alimentar hasta ahora): `outline/units/*.md`
ya se ingiere, el grafo ensambla secuencias narrativas a partir de él, los
vocabularios de Propp y Greimas tipan el resultado, y un nuevo validador de
continuidad consume la capa. Con esto se alcanza el **norte de paridad de
ingesta**: todo concepto autorable tiene ya una vía de ingesta. Aditivo y sin
coste para un proyecto que no lo use; la ontología GOLEM sigue **congelada**.
Ver [Estructura narrativa](narrative-structure.md). Consolida las iteraciones
028–032.

### Añadido

- **Ingesta de `outline/units/*.md` → unidades (`G9`) y funciones (`G10`)**
  narrativas: los beats del outline se mapean al grafo como unidades narrativas
  con su función, el tercer espejo ingerido del patrón de `bible/` tras
  localizaciones (G13) y objetos (G16).
- **Ensamblado de secuencias (`G7`)**: las claves opcionales `sequence`/`order`
  del front-matter de las unidades componen secuencias narrativas ordenadas,
  cerrando la ingesta `G7`/`G9`/`G10`.
- **Vocabularios de Propp y Greimas como `crm:E55_Type`** (31 funciones de Propp
  + 6 actantes de Greimas, etiquetas ES+EN): cuando la lista `[vocabularies]
  active` del manifiesto activa un vocabulario, las funciones narrativas (G10) y
  los roles de personaje (G11) se tipan vía `crm:P2_has_type`, sin regresión
  cuando no hay vocabulario activo.
- **Validador `narrative_structure`**: el primer *consumidor* de la capa — un
  chequeo auto-descubierto, por defecto `warning`, sin LLM, con dos reglas: beat
  huérfano (una unidad `G9` en ninguna secuencia `G7`) y rol sin resolver. Ver
  [Validación](validation.md).
- **Ejemplo `tiny-quest`, E2E y docs**: un *fixture* con oráculo co-localizado
  (Propp activo, un beat huérfano y un rol sin resolver deliberados), el test E2E
  `build → validate`, y la página [Estructura narrativa](narrative-structure.md).

### Cambiado

- **Aplazamientos G6/G3 re-apuntados a `demand-pulled`**: `RelationshipRole` (G6)
  y `PsychologicalState` (G3) pasan del destino `v0.4` al centinela de primer
  orden `demand-pulled` — se entregan cuando se cumpla una condición de
  activación concreta, no en una versión preasignada.

### Hardening posterior (v0.4.1 – v0.4.4)

Cuatro parches de pura consolidación sobre la línea v0.4, tres de ellos surgidos
de una sesión de *dogfooding* (un libro real de principio a fin):

- **v0.4.1** — elimina el concepto muerto `NarrativeRole` (sin vía de
  materialización) y blinda el contrato de paridad de ingesta para que un
  concepto muerto no vuelva a contarse como alcanzable.
- **v0.4.2** — despierta el validador `focalization`, que la propia plantilla de
  Bookwright silenciaba: ahora tolera la declaración de voz con prefijo Markdown
  (`- **Voz narrativa**: …`) que emite el scaffold.
- **v0.4.3** — hace la capa narrativa **consultable**: emite `rdfs:label` en
  unidades y funciones (búsqueda por nombre) y materializa `bw:sequenceOrdinal`
  (recorrido en orden declarado bajo RDF no ordenado).
- **v0.4.4** — hace **accionables** los errores de carga de fuentes de
  investigación (enumera el vocabulario aceptado y prefija cada fallo con el
  nombre o el índice `#n` de la fuente). Incluye además el **relicenciamiento a
  EUPL-1.2** (antes Apache-2.0) y la atribución de la ontología GOLEM como
  CC BY 4.0.

## v0.3.0 — Orquestación de contexto (M5)

Añade el **hilo conductor** (diseño § 21): un plan de trabajo en tres capas que no se
pisan —**autorada** (el bloque `[focus]`), **derivada** (`bookwright status`) y de
**juicio** (las skills)— que responde *en qué trabajo y qué hago a continuación* sin un
TODO escrito a mano que envejece. El plan es una **función** del texto plano: borra el
grafo, reconstruye y obtienes el mismo estado. Opcional y aditivo: un proyecto que no lo
usa se comporta como en v0.2. Ver [Orquestación](orchestration.md).

### Añadido

- **Foco autorado** (iteración 19): el bloque opcional `[focus]` del manifiesto
  (`target`, `notes`, `updated_at` sellado por la CLI) y los comandos
  [`bookwright focus set`](commands/focus-set.md) / [`show`](commands/focus-show.md) /
  [`clear`](commands/focus-clear.md). Estado autorado en texto plano; `focus set`
  preserva el resto del manifiesto byte a byte.
- **`bookwright status`** (iteración 20): el [comando de estado derivado](commands/status.md).
  Reconstruye el grafo en cada ejecución (la recomputación *es* la frescura), agrega los
  hechos —fase, foco, preguntas abiertas, anclas sin soporte, hallazgos de baja
  fiabilidad, resumen de validación— y los pasa por una tabla de reglas pura y ordenada
  que produce `next_actions` (skill + prompt + razón). Sin LLM ni red: bytes idénticos
  para el mismo corpus. Las reglas recomiendan **por workstream, no por elemento**, de
  modo que cerrar una pregunta no acorta la lista: solo convergen su prompt y su razón.
- **Skills que consumen `status`** (iteraciones 21–22): las skills de autoría leen
  `bookwright status` al arrancar, anclando la capa de juicio en el estado derivado.
- **Ejemplo, E2E y docs de orquestación** (iteración 23): el *fixture* `tiny-historical`
  ampliado a ejemplo de trabajo (un `[focus]` poblado, un oráculo co-localizado
  `expected-status.md` y una resolución pre-cocinada en `_resolution/`, fuera del
  corpus), el test E2E `test_orchestration_workflow.py` que recorre
  `focus → build → status → resolver → build → status` y asevera la **convergencia de
  estado** más las rutas de inercia y degradación, y la página
  [Orquestación](orchestration.md). Las expectativas de `factual_anchor` (M4) quedan
  byte-estables.

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
