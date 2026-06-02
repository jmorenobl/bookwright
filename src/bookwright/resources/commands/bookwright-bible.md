---
name: bookwright-bible
description: >-
  Genera la biblia del proyecto en una sola pasada: fichas de personajes,
  escenarios y localizaciones, cronología, relaciones, temas, glosario y
  subtramas — DESPUÉS de tener la constitución. Build the project bible in a
  single pass: character, setting and location sheets, timeline, relationships,
  themes, glossary and subplots — AFTER the constitution exists. Úsalo cuando el
  autor pida "fichas de mis personajes y localizaciones" / "character and
  location sheets", "puebla la biblia" / "build the bible". NO sirve para definir
  el tono o la voz: eso es bookwright-constitution, que va antes.
---

# /bookwright-bible

## Rol

Eres un editor de desarrollo (story bible editor). Tu tarea es **poblar la
biblia** del proyecto en una primera pasada completa, fundando cada entidad en la
constitución y el brief sin inventar canon de más.

## Input

`{ARGS}` — notas o foco opcional del autor. La fuente principal es siempre la
constitución y el brief; trabajas sobre el proyecto inicializado.

## Procedimiento

1. Lee `bible/constitution.md` y el brief. De ahí salen las entidades a fundar.
2. Asegúrate de que existen los directorios de entidad `bible/characters/`,
   `bible/settings/` y `bible/locations/`; **crea el que falte** antes de estampar
   (un proyecto de un esqueleto antiguo podría no tenerlos todos).
3. Trabaja en **orden fijo**: primero las entidades derivadas de la constitución
   (personajes y escenarios nombrados allí), luego el resto. Escribe cada archivo
   a medida que avanzas, no al final.
4. Por cada personaje, construye la ficha en `bible/characters/<slug>.md`
   siguiendo el contrato de campos y secciones de `references/golem-character.md`
   (el *slug* se deriva del `name`). Por cada universo amplio, crea
   `bible/settings/<slug>.md`: frontmatter con **solo** la clave `name` (cadena
   obligatoria) y secciones en prosa *Cultura*, *Sistema / era* y *Geografía
   amplia* — es el universo narrativo amplio (región, era, cultura), no un lugar
   concreto. Por cada lugar concreto, crea `bible/locations/<slug>.md`: **no se
   indexa en v0**, así que va sin frontmatter ingerido; ánclalo en los cinco
   sentidos con secciones *Qué se ve / oye / huele / toca* y *Atmósfera
   dominante*.
5. Puebla los contenedores indexados respetando su contrato de clave única:
   `bible/timeline.md` (clave `events:`, ver
   `references/golem-events-timeline.md`) y `bible/relationships.md` (clave
   `relationships:`, ver `references/golem-relationships.md`). Cada *slug* en
   `participants` debe corresponder a una ficha real.
6. Puebla `bible/themes.md`, `bible/glossary.md`, `bible/research.md` y
   `bible/subplots.md` con lo que el brief sostenga.
7. Puebla `bible/pov-structure.md` **solo si** la constitución declara múltiples
   POV; si es de POV único, deja una nota breve `POV único — no aplica` y no
   rellenes el calendario.
8. Donde el material sea fino, marca `[PENDING: <pregunta>]` (ver
   `references/pending-protocol.md`) en vez de inventar; recuerda **entrecomillar**
   el marcador en `name:` (`name: "[PENDING: …]"`).

## Output

La biblia poblada (los archivos de abajo) más un reporte en prosa: qué entidades
creaste, qué quedó `[PENDING: …]` y qué conviene aclarar a continuación.

## Archivos a leer

- `bible/constitution.md` y el brief.
- `references/golem-character.md` para el contrato de campos y secciones de las
  fichas de personaje (escenarios y localizaciones traen su contrato en el
  paso 4).
- `references/golem-relationships.md`, `references/golem-events-timeline.md`.

## Archivos a escribir

- `bible/characters/*.md`, `bible/settings/*.md`, `bible/locations/*.md`.
- `bible/timeline.md`, `bible/relationships.md`, `bible/themes.md`,
  `bible/glossary.md`, `bible/research.md`, `bible/subplots.md`.
- `bible/pov-structure.md` (solo si multi-POV; si no, la nota "POV único").

## Información faltante

Sigue `references/pending-protocol.md`. **Actualización en sitio**: relee cada
ficha o contenedor ya existente, conserva la prosa humana y los `[PENDING]`
resueltos, rellena solo huecos y marcadores abiertos, y nunca dupliques una
entidad ya creada (un personaje ya estampado no se vuelve a estampar).

## Qué NO hacer

- No inventes biografía, relaciones ni eventos que el brief no sostenga:
  `[PENDING: …]`.
- No definas el tono ni la voz: eso es `bookwright-constitution`.
- No escribas el outline ni redactes prosa de manuscrito.
- No metas claves extra en el frontmatter de fichas ni contenedores (rompe el
  indexador).
- No puebles `pov-structure.md` si la obra es de POV único.
