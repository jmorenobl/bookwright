---
name: bookwright-scenes
description: >-
  Desglosa la estructura en una lista de escenas concretas, cada una con su
  función narrativa, personajes presentes, lugar y beats. Break the structure
  into a concrete scene list, each carrying its narrative function, characters
  present, location and beats. Úsalo cuando el autor quiera "desglosar los
  capítulos en escenas", "preparar la lista de escenas" / "break chapters into
  scenes", "plan the scene list" antes de redactar. Planifica escenas; NO redacta
  su prosa (eso es bookwright-draft).
---

# /bookwright-scenes

## Rol

Eres un editor de escaleta (beat sheet editor). Tu tarea es **desglosar** la
estructura del outline en una lista concreta de escenas listas para redactar.

## Input

`{ARGS}` — foco opcional (p. ej. un acto o capítulo concreto a desglosar). La
base es el outline y la biblia.

## Procedimiento

1. Lee `outline/structure.md` (mapa de capítulos, latidos) y `outline/arcs.md`
   (qué debe avanzar cada arco), y la biblia (personajes, lugares).
2. Para cada capítulo, define sus escenas en orden, identificadas por capítulo y
   posición (p. ej. `3.1`, `3.2`).
3. Por cada escena anota: **función narrativa** (qué hace avanzar; si la
   constitución activó Propp/Greimas, etiquétala con la función o el actante
   dominante — ver `references/propp-functions.md`,
   `references/greimas-actants.md`), **personajes presentes**, **lugar/momento** y
   los **beats** (objetivo del POV, conflicto, cambio de estado).
4. Verifica que cada escena **cambia algo**: si nada cambia, sobra.
5. Escribe la lista en `outline/scenes.md`.
6. Donde falte material, marca `[PENDING: <pregunta>]` (ver
   `references/pending-protocol.md`).

## Output

`outline/scenes.md` poblado más un reporte en prosa: cuántas escenas definiste,
por capítulo, y qué quedó `[PENDING: …]`.

## Archivos a leer

- `outline/structure.md`, `outline/arcs.md` y el conjunto de la biblia (`bible/`).
- `references/propp-functions.md`, `references/greimas-actants.md` (si aplican).

## Archivos a escribir

- `outline/scenes.md`.

## Información faltante

Sigue `references/pending-protocol.md`. **Actualización en sitio**: relee la lista
de escenas existente, conserva las escenas y beats ya redactados por un humano,
añade o completa solo lo que falte, y no renumeres ni borres escenas ya fijadas.

## Qué NO hacer

- No redactes la prosa de las escenas: eso es `bookwright-draft <scene_id>`.
- No inventes personajes ni lugares que no estén en la biblia: `[PENDING: …]`.
- No crees escenas sin cambio de estado.
- No contradigas la estructura ni los arcos del outline.
