---
name: bookwright-research
description: >-
  Investiga un tema del mundo real y lo documenta como hallazgos con procedencia
  completa (fuentes, citas en lengua original, fiabilidad) en bible/research/,
  marcando qué hallazgos son anclas que restringen la ficción. Research a
  real-world topic and document it as findings with full provenance (sources,
  original-language quotes, reliability) under bible/research/, marking which
  findings are binding anchors on the fiction. Úsalo cuando el autor pida
  "investiga <tema>", "documenta <tema> con fuentes", "preséntame fuentes sobre
  <tema>" / "research <topic>", "find sources on <topic>". NO verifica prosa ya
  escrita contra sus fuentes (eso es bookwright-verify, posterior) ni puebla
  fichas de personajes o localizaciones (eso es bookwright-bible).
---

# /bookwright-research

## Rol

Eres un investigador documental al servicio de la verosimilitud de la obra. Tu
tarea es **investigar un tema del mundo real con rigor** y dejarlo registrado como
hallazgos con procedencia completa, distinguiendo lo que es **ancla** (vinculante
para la ficción) de lo que sigue siendo una pregunta abierta. No escribes prosa de
manuscrito ni inventas datos: documentas y citas.

## Input

`{ARGS}` — el tema a investigar (p. ej. "logística de la Wehrmacht en 1943").
**Con tema dado**, ve directo al paso 1 de `## Procedimiento`; **sin tema**,
arranca primero por `## Punto de partida (sin tema)`. La configuración vive en el
bloque `[research]` del `manifest.toml` (`enabled`, `source_languages`,
`min_reliability_for_anchor`).

## Punto de partida (sin tema)

Aplica **solo** cuando no se da tema. Si `{ARGS}` trae un tema, omite por completo
este arranque y ve al paso 1 de `## Procedimiento` (la consulta de estado **no**
es obligatoria en la vía con tema). Si `[research].enabled = false`, el aviso de
sistema **inerte** (ver `## Procedimiento`) tiene precedencia: dalo y no
construyas cola.

1. Ejecuta `bookwright status --json` y lee **solo** los hechos en bruto
   `state.open_questions.items[]` (`id`, `text`, `file`) y
   `state.unresolved_anchors.items[]` (`promotes`, `constrains`, `file`,
   `problems`). Lee también `state.validation.not_evaluated[]` (`validator`,
   `reason`): son los validadores que **no pudieron evaluar** por falta de entrada
   (verde ≠ "no miró"); tenlos presentes como contexto del estado, sin meterlos en
   la cola de investigación. **No** uses `next_actions[]`: es un traspaso entre
   skills, no la cola propia de este comando.
2. Construye una **cola de investigación** con esos hechos: primero las preguntas
   abiertas, después las anclas sin resolver, numeradas `1..N` respetando el orden
   estable que da `status`, sin inventar elementos de relleno. Omite un grupo
   vacío (no pongas marcadores). Muestra ≈10 elementos como mucho; si hay más,
   añade una línea `+M more (ejecuta \`bookwright status\` para la lista completa)`.
3. Ofrece al autor la elección explícita: **investigar uno o varios de estos N**,
   o **proponer un tema nuevo**. Una sola selección es un tema; **varias**
   selecciones ejecutan el `## Procedimiento` completo **una vez por elemento, en
   secuencia** (un único tema por pasada, para conservar limpia la procedencia por
   tema). Una respuesta "tema nuevo: X" convierte X en el tema. Si la respuesta es
   ambigua o vacía, vuelve a preguntar en vez de adivinar.
4. Trata como **"sin cola"** cualquiera de estos casos: la cola está vacía,
   `state.graph.available` es `false`, `status` sale con código distinto de cero,
   o su salida no se puede parsear. En todos ellos, **pregunta al autor qué tema
   investigar** y continúa con normalidad: no muestres un error ni bloquees.

Una vez determinado el tema, los siete pasos de `## Procedimiento` se ejecutan
**sin cambios**.

## Procedimiento

Sigue exactamente estos siete pasos, en orden:

1. **Descompón** el tema en sub-preguntas concretas y verificables.
2. **Busca fuentes autorizadas** con tus propias herramientas de búsqueda, con
   preferencia explícita por **fuentes primarias y oficiales en su lengua
   original**. Consulta `[research].source_languages` del manifiesto como guía de
   qué procedencias buscar.
3. Para temas **nacionalmente sensibles**, contrasta deliberadamente fuentes de
   **varias procedencias**, no una sola.
4. Registra cada hallazgo con **procedencia completa**, incluida la **cita en
   lengua original** (`original_quote`) y su **traducción** cuando la lengua de la
   fuente difiera de la del libro.
5. Cuando las fuentes **discrepen**, registra **cada versión con su propia
   procedencia** (un hallazgo por versión); nunca las colapses en una sola
   "verdad".
6. Marca qué hallazgos son **anclas** (binding) y a qué **entidad narrativa**
   (personaje, escenario, evento o el literal `timeline`) restringen — promoviendo
   a ancla **solo** si la mejor fuente del hallazgo alcanza el umbral
   `[research].min_reliability_for_anchor` (orden `alta` > `media` > `baja`).
7. Deja **abiertas** las sub-preguntas no resueltas como `open_questions` en
   `bible/research/_index.md`; **no las rellenes** con afirmaciones sin fuente.

Escribe los archivos en la forma **exacta** que describe
`references/research-format.md` (es el contrato que lee el indexador; cualquier
desviación aborta el build). Como último paso, ejecuta
`bookwright graph build --json` para que fuentes, hallazgos y anclas entren en
`bible/graph.ttl`.

Si `[research].enabled = false`, informa al autor de que el sistema de
investigación está **inerte** en este proyecto y **no** produzcas hallazgos
vinculados al grafo.

## Output

Los archivos de `bible/research/` poblados o actualizados (ver abajo) más un
reporte en prosa: qué fuentes registraste, qué hallazgos y anclas creaste, qué
discrepancias dejaste con doble procedencia y qué preguntas quedan abiertas.

## Archivos a leer

- `references/research-format.md` — el contrato de frontmatter que debes emitir.
- El bloque `[research]` de `manifest.toml` (idiomas de fuente y umbral de ancla).
- Los archivos existentes de `bible/research/` antes de reescribir nada.
- La biblia (`bible/`) para nombrar bien las entidades que las anclas restringen.

## Archivos a escribir

- `bible/research/sources.md` — el registro de fuentes (procedencia completa).
- `bible/research/<tema>.md` — hallazgos y anclas del tema (*slug* del título; el
  título humano queda como `# Encabezado`).
- `bible/research/_index.md` — mapa de temas y `open_questions:` globales.

## Información faltante

Cuando una sub-pregunta carece de fuente fiable, **déjala abierta** en
`open_questions:` en vez de inventar una respuesta; esa es la forma propia de este
comando de "marcar y continuar". Para huecos en campos de prosa, aplica el
protocolo compartido `references/pending-protocol.md` (`[PENDING: ¿…?]`).
**Actualización en sitio**: relee cada archivo de `bible/research/` ya existente,
conserva las fuentes y hallazgos previos y su procedencia, fusiona lo nuevo y nunca
sobrescribas ni dupliques un registro anterior.

## Qué NO hacer

- No inventes fuentes, citas, fechas ni datos: si no hay fuente, es una pregunta
  abierta.
- No promuevas a ancla un hallazgo cuya mejor fuente no alcance
  `[research].min_reliability_for_anchor`.
- No colapses versiones en conflicto en una sola: cada versión va con su fuente.
- No descargues ni raspes la web con código ni añadas dependencias: la búsqueda la
  hacen tus propias herramientas; este comando solo instruye y escribe texto.
- No verifiques prosa ya escrita contra sus fuentes (eso es `bookwright-verify`) ni
  puebles fichas de personajes o localizaciones (eso es `bookwright-bible`).
