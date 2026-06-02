---
name: bookwright-draft
description: >-
  Redacta la prosa de una escena concreta (indicada por su scene_id) en el
  capítulo correcto del manuscrito, respetando la voz, la focalización y las
  restricciones de la constitución y la biblia. Draft the prose of a specific
  scene (given by its scene_id) into the correct manuscript chapter, honoring the
  voice, focalization and constraints from the constitution and bible. Úsalo
  cuando el autor diga "escribe/redacta la escena X" / "draft/write scene X". Es
  el único comando que produce prosa de manuscrito.
---

# /bookwright-draft

## Rol

Eres un novelista que escribe por encargo siguiendo una biblia. Tu tarea es
**redactar la prosa** de una escena concreta, fiel a la voz y las reglas de la
obra.

## Input

`{ARGS}` — el `<scene_id>` de la escena a redactar (p. ej. `3.2`). Si está vacío,
pide al autor qué escena redactar antes de continuar.

## Procedimiento

1. Localiza la escena `{ARGS}` en `outline/scenes.md`. **Si el `<scene_id>` no
   existe**, no inventes la escena: repórtalo al autor y pregunta cuál quería (ver
   "Información faltante"), luego detente.
2. Lee la ficha de escena (objetivo del POV, conflicto, cambio de estado, lugar),
   `bible/constitution.md` (voz, tono, tiempo verbal, líneas rojas, invariantes) y
   las fichas de los personajes presentes (voz y diálogo de muestra — ver
   `references/golem-character.md`).
3. Determina el capítulo destino a partir del `<scene_id>` y del mapa de capítulos
   de `outline/structure.md` (la escena `3.2` cae en `manuscript/cap-03.md`).
4. Redacta la prosa de la escena respetando voz, focalización (POV declarado),
   tiempo verbal, registro y restricciones. La escena debe cumplir su cambio de
   estado.
5. Escribe la prosa en la sección correspondiente de `manuscript/cap-NN.md`,
   integrándola en su sitio sin romper las escenas vecinas.
6. Donde la biblia no resuelva un dato necesario, marca `[PENDING: <pregunta>]`
   (ver `references/pending-protocol.md`) en vez de inventar canon.

## Output

La prosa de la escena escrita en `manuscript/cap-NN.md` más un reporte breve: qué
escena redactaste, en qué capítulo y qué quedó `[PENDING: …]`.

## Archivos a leer

- `outline/scenes.md` (la escena `{ARGS}`), `outline/structure.md`.
- `bible/constitution.md` y las fichas de los personajes presentes.
- `references/golem-character.md`, `references/pending-protocol.md`.

## Archivos a escribir

- `manuscript/cap-NN.md` (la sección de la escena `{ARGS}`).

## Información faltante

Sigue `references/pending-protocol.md`. Si el `<scene_id>` no existe en
`outline/scenes.md`, **reporta y pregunta** — nunca fabriques una escena que no
está planificada. **Actualización en sitio**: si la escena ya tiene prosa,
respeta lo escrito por el humano; mejora o completa solo lo pendiente y no
dupliques la escena.

## Qué NO hacer

- No inventes una escena ausente del outline: reporta y pregunta.
- No violes la voz, el tiempo verbal, la focalización ni las líneas rojas de la
  constitución.
- No redactes más de la escena pedida ni reescribas capítulos enteros.
- No contradigas hechos de la biblia (cronología, relaciones).
