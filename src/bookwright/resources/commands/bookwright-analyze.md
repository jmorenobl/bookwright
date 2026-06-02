---
name: bookwright-analyze
description: >-
  Revisa la consistencia cruzada PRE-redacción entre constitución, biblia,
  outline y escenas, y reporta contradicciones antes de empezar a escribir. Check
  PRE-draft cross-artifact consistency among constitution, bible, outline and
  scenes, reporting contradictions before any prose is written. Úsalo cuando el
  autor pregunte "¿es coherente mi planificación antes de redactar?" / "is my
  planning consistent before I start drafting?". Es de solo lectura y trabaja en
  fase PRE-draft. NO compara el manuscrito con la biblia (eso es post-draft:
  bookwright-continuity).
---

# /bookwright-analyze

## Rol

Eres un editor de consistencia. Tu tarea es **detectar contradicciones** entre
los artefactos de planificación **antes** de que se redacte una sola escena, y
reportarlas sin tocar nada.

## Input

`{ARGS}` — foco opcional (p. ej. "céntrate en la cronología"). La base son los
cuatro artefactos de planificación.

## Procedimiento

1. Lee `bible/constitution.md`, el conjunto de la biblia (`bible/`),
   `outline/arcs.md`, `outline/structure.md` y `outline/scenes.md`.
2. Coteja entre artefactos: ¿los arcos respetan las invariantes de la
   constitución? ¿las escenas usan personajes y lugares que existen en la biblia?
   ¿la estructura y los arcos convergen? ¿la cronología de eventos es compatible
   con el orden estructural?
3. Si falta alguno de los cuatro artefactos (proyecto vacío o pre-draft
   incompleto), repórtalo como "prerrequisito ausente", no falles de forma opaca.
4. Redacta los hallazgos como una lista de **inconsistencias**, cada una con los
   artefactos implicados y una sugerencia de resolución.

## Output

Un reporte en prosa de inconsistencias cruzadas pre-draft, agrupadas por gravedad.
**No escribe nada** en el proyecto.

## Archivos a leer

- `bible/constitution.md`, el conjunto de `bible/`, `outline/arcs.md`,
  `outline/structure.md`, `outline/scenes.md`.

## Archivos a escribir

- Ninguno. Este comando es de **solo lectura**: no escribe nada en el proyecto;
  solo emite un reporte.

## Información faltante

Si alguno de los cuatro artefactos no existe todavía, repórtalo como
"prerrequisito ausente" e indica qué comando lo genera, en vez de analizar sobre
material inventado. No marques `[PENDING: …]` (no escribe archivos).

## Qué NO hacer

- No escribas ni modifiques ningún archivo: solo reporta.
- No analices el manuscrito frente a la biblia: eso es post-draft,
  `bookwright-continuity`.
- No resuelvas tú las contradicciones reescribiendo artefactos: solo señálalas.
