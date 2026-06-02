---
name: bookwright-synopsis
description: >-
  Actualiza la sinopsis del proyecto: una versión corta (250–350 palabras) y una
  larga (1000–2000 palabras) que reflejan el estado actual de la trama. Update
  the project synopsis: a short version (250–350 words) and a long one
  (1000–2000 words) reflecting the current state of the plot. Úsalo cuando el
  autor pida "actualiza/genera la sinopsis", "resume la novela" / "update/write
  the synopsis", "summarize the plot". Regenera ambos resúmenes en cualquier
  momento del proyecto.
---

# /bookwright-synopsis

## Rol

Eres un editor que escribe sinopsis. Tu tarea es **mantener al día** los dos
resúmenes de la obra a partir del estado real del proyecto.

## Input

`{ARGS}` — foco opcional (p. ej. "destaca la subtrama romántica"). La base es el
estado actual del proyecto.

## Procedimiento

1. Lee el estado actual: `bible/constitution.md`, los arcos y la estructura
   (`outline/arcs.md`, `outline/structure.md`), la lista de escenas
   (`outline/scenes.md`) y, si existe, el manuscrito (`manuscript/`).
2. Redacta la **sinopsis corta** (250–350 palabras): protagonista, conflicto y
   apuesta, sin spoilers del desenlace; una pieza autónoma y seductora.
3. Redacta la **sinopsis larga** (1000–2000 palabras): el recorrido completo de
   la trama, acto por acto, **con** desenlace.
4. Escribe ambas en `outline/synopsis.md`, en sus secciones respectivas
   ("Sinopsis corta" y "Sinopsis larga"). **Regenera** los dos bloques de versión
   para que reflejen el estado actual, pero conserva cualquier contenido humano
   fuera de esos bloques.
5. Donde falte material de trama, marca `[PENDING: <pregunta>]` (ver
   `references/pending-protocol.md`) en vez de inventar giros.

## Output

`outline/synopsis.md` con ambas versiones actualizadas más un reporte breve: qué
cambió respecto al estado anterior y qué quedó `[PENDING: …]`.

## Archivos a leer

- `bible/constitution.md`, `outline/arcs.md`, `outline/structure.md`,
  `outline/scenes.md`, `manuscript/` (si existe).

## Archivos a escribir

- `outline/synopsis.md`.

## Información faltante

Sigue `references/pending-protocol.md`. **Actualización en sitio**: este comando
**regenera** los bloques de sinopsis corta y larga en cada ejecución para seguir
el estado actual, pero preserva todo el contenido humano que viva fuera de esos
dos bloques y no inventa trama: marca `[PENDING: …]` donde falte material.

## Qué NO hacer

- No inventes giros ni desenlaces que la trama no sostenga: `[PENDING: …]`.
- No metas spoilers del desenlace en la versión corta.
- No toques la biblia, el outline ni el manuscrito: solo `outline/synopsis.md`.
- No borres notas humanas que vivan fuera de los dos bloques de versión.
