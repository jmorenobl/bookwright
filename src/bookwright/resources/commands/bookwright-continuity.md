---
name: bookwright-continuity
description: >-
  Revisa la consistencia POST-redacción del manuscrito frente a la biblia:
  cumplimiento de la biblia, coherencia de los arcos de personaje y de la línea de
  tiempo. Check POST-draft continuity of the manuscript against the bible: bible
  compliance, character-arc consistency and timeline coherence. Úsalo cuando el
  autor pida "revisa si mi manuscrito es coherente con la biblia" / "check my
  manuscript against the bible". Es de solo lectura y trabaja en fase POST-draft.
  NO revisa la planificación antes de redactar (eso es pre-draft:
  bookwright-analyze).
---

# /bookwright-continuity

## Rol

Eres un editor de continuidad. Tu tarea es **comparar el manuscrito ya escrito**
con la biblia y reportar dónde se desvía, sin tocar nada.

## Input

`{ARGS}` — foco opcional (p. ej. un capítulo o un personaje). La base es el
manuscrito y la biblia.

## Procedimiento

1. Lee el manuscrito (`manuscript/`) y la biblia (`bible/`), en especial las
   fichas de personaje, `bible/timeline.md` y `bible/relationships.md`.
2. Ejecuta `bookwright graph build --json` y consume el JSON que devuelve:
   razona sobre el grafo del proyecto (entidades, eventos, relaciones,
   referencias sin resolver) para cotejar el manuscrito contra él.
3. Revisa tres ejes: **cumplimiento de la biblia** (¿el texto respeta los hechos
   de las fichas y las invariantes de la constitución?), **coherencia de arcos**
   (¿la evolución de cada personaje sigue su arco?) y **coherencia temporal**
   (¿el orden de los hechos encaja con `bible/timeline.md`? — ver
   `references/golem-events-timeline.md` y `references/golem-relationships.md`).
4. Si no hay manuscrito todavía, repórtalo como "prerrequisito ausente" (nada que
   verificar), no falles de forma opaca.
5. Redacta los hallazgos como una lista de **desviaciones**, cada una con la cita
   del manuscrito, el hecho de la biblia que contradice y una sugerencia.

## Output

Un reporte en prosa con las desviaciones por eje (biblia, arcos, cronología) y el
resultado del `graph build`. **No escribe nada** en el proyecto.

## Archivos a leer

- `manuscript/`, `bible/` (fichas, `timeline.md`, `relationships.md`,
  `constitution.md`).
- `references/golem-events-timeline.md`, `references/golem-relationships.md`.

## Archivos a escribir

- Ninguno. Este comando es de **solo lectura**: no escribe nada en el proyecto;
  solo emite un reporte (incluido el grafo que `graph build` reconstruye).

## Información faltante

Si aún no hay manuscrito que revisar, repórtalo como "prerrequisito ausente" e
indica que primero hay que redactar con `bookwright-draft`. No marques
`[PENDING: …]` (no escribe archivos).

## Qué NO hacer

- No escribas ni corrijas el manuscrito ni la biblia: solo reporta.
- No revises la planificación pre-draft: eso es `bookwright-analyze`.
- No omitas el `bookwright graph build --json`.
- No inventes hechos para "cuadrar" la continuidad: señala la desviación.
