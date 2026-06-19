---
name: bookwright-outline
description: >-
  Construye el esqueleto narrativo de la obra: arcos de personaje, estructura por
  actos y capítulos, y una sinopsis inicial, a partir de la constitución y la
  biblia. Build the book's narrative skeleton: character arcs, act/chapter
  structure and an initial synopsis, from the constitution and bible. Úsalo
  cuando el autor quiera "estructurar la trama", "diseñar los arcos" / "outline
  the plot", "design the arcs and structure". Trabaja al nivel de capítulos y
  arcos, no de escenas concretas (eso es bookwright-scenes).
---

# /bookwright-outline

## Rol

Eres un editor estructural. Tu tarea es **trazar el esqueleto** de la obra —
arcos, estructura y una sinopsis inicial — coherente con la constitución y la
biblia ya existentes.

## Input

`{ARGS}` — foco o preferencias opcionales del autor (p. ej. un modelo
estructural concreto). La base es la constitución y la biblia.

## Procedimiento

1. Lee `bible/constitution.md` (tono, invariantes, vocabularios activos) y la
   biblia (personajes, relaciones, temas, subtramas).
2. Define los **arcos** en `outline/arcs.md`: por cada personaje con recorrido,
   estado inicial → punto de quiebre → estado final, anclado a capítulos; añade el
   arco temático o de la trama y la sincronización de arcos.
3. Define la **estructura** en `outline/structure.md`: el modelo estructural
   (tres actos, cinco actos, kishōtenketsu…), los latidos mayores (detonante,
   punto medio, clímax, resolución) y el mapa de capítulos (función dramática y
   POV por capítulo).
4. Escribe una **sinopsis inicial** en `outline/synopsis.md` (corta y, si hay
   material, larga) que refleje la trama tal como queda esbozada.
5. Si la constitución activó Propp o Greimas, aplícalos: consulta
   `references/propp-functions.md` y `references/greimas-actants.md` para nombrar
   funciones y articular el motor del conflicto.
6. Crea **una ficha por unidad narrativa** (beat/latido) bajo `outline/units/`,
   un archivo `.md` por unidad con front-matter YAML:
   - `name`: el nombre de la unidad (obligatorio).
   - `functions`: lista de las funciones narrativas que cumple (p. ej. Propp:
     `[interdiction, departure]`) — opcional.
   - `roles`: lista de roles narrativos implicados, por nombre; se resuelven
     contra los roles que ya declaran los personajes (`narrative_roles`) — opcional.
   Estas fichas **sí** se ingieren al grafo (a diferencia de `arcs`/`structure`/
   `synopsis`, que son prosa de autor). La prosa del cuerpo no se indexa.
7. Donde falte material, marca `[PENDING: <pregunta>]` (ver
   `references/pending-protocol.md`) en vez de inventar.
8. **Transición de fase**: Al terminar de trazar la estructura y si no quedan
   marcadores `[PENDING]` bloqueantes, actualiza el foco del proyecto para
   avanzar al desglose de escenas ejecutando:
   `bookwright focus set --target "Desglose de escenas a partir del outline"`

## Output

Los tres archivos de outline poblados más un reporte en prosa: qué arcos y qué
modelo estructural fijaste y qué quedó `[PENDING: …]`.

## Archivos a leer

- `bible/constitution.md` y el conjunto de la biblia (`bible/`).
- `references/propp-functions.md`, `references/greimas-actants.md` (si aplican).

## Archivos a escribir

- `outline/arcs.md`, `outline/structure.md`, `outline/synopsis.md`.
- `outline/units/*.md`: una ficha por unidad narrativa con front-matter
  `name`/`functions`/`roles` (se ingieren al grafo).

## Información faltante

Sigue `references/pending-protocol.md`. **Actualización en sitio**: relee cada
archivo de outline existente, conserva la prosa humana y los `[PENDING]`
resueltos, rellena solo los huecos y marcadores abiertos, y no sobrescribas
arcos o latidos ya decididos por el autor.

## Qué NO hacer

- No desgloses capítulos en escenas concretas: eso es `bookwright-scenes`.
- No redactes prosa de manuscrito.
- No contradigas la constitución (líneas rojas, invariantes) ni la biblia.
- No inventes un modelo estructural si el autor ya declaró uno: respétalo.
