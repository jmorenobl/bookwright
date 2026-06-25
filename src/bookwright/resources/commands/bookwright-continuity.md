---
name: bookwright-continuity
description: >-
  Revisa la consistencia POST-redacción del manuscrito frente a la biblia:
  cumplimiento de la biblia, coherencia de los arcos de personaje y de la línea de
  tiempo, personajes mencionados en la prosa pero sin ficha en bible/characters/,
  y head-hopping / saltos de punto de vista. Check POST-draft continuity of the
  manuscript against the bible: bible compliance, character-arc consistency,
  timeline coherence, characters used in the prose but undeclared (no sheet in
  bible/characters/), and head-hopping / POV breaks. Úsalo cuando el autor pida
  "revisa si mi manuscrito es coherente con la biblia" / "check my manuscript
  against the bible", "revisa si hay personajes sin declarar / mencionados pero
  sin ficha" / "check for undeclared / unbacked characters", o "revisa
  head-hopping / saltos de punto de vista / focalización rota" / "check for
  head-hopping / POV breaks". Es de solo lectura y trabaja en fase POST-draft. NO
  revisa la planificación antes de redactar (eso es pre-draft: bookwright-analyze).
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
3. Revisa cinco ejes: **cumplimiento de la biblia** (¿el texto respeta los
   hechos de las fichas y las invariantes de la constitución?), **coherencia de
   arcos** (¿la evolución de cada personaje sigue su arco?), **coherencia
   temporal** (¿el orden de los hechos encaja con `bible/timeline.md`? — ver
   `references/golem-events-timeline.md` y `references/golem-relationships.md`),
   **menciones de conjunto abierto / personajes sin declarar** (ver el eje 4
   abajo) y **head-hopping / saltos de punto de vista / focalización rota** (ver
   el eje 5 abajo).
4. **Cuarto eje — personajes mencionados pero sin ficha.** Construye el *roster*
   de personas declaradas leyendo el campo `name:` de cada
   `bible/characters/*.md` — el nombre vive en la **ficha**, no en una etiqueta
   del grafo: `G1_Character` no tiene `rdfs:label`, el nombre está en `name:` y
   en el slug de la URI (ver `references/golem-character.md`). Lee también los
   nombres de `bible/settings/`, `bible/locations/` y `bible/objects/` para saber
   qué nombres propios ya están declarados (y no son personas). Recorre el
   manuscrito buscando nombres propios y **juzga** cuáles nombran a una *persona
   usada en la prosa pero sin ficha en la biblia* (p. ej. una `Amelia` que
   aparece en el texto pero no tiene `bible/characters/amelia.md`),
   distinguiéndolos del ruido que **no** necesita ficha: organizaciones, nombres
   de lugar, vocativos y palabras de título. El *roster* es la base de juicio que
   separa la señal (un personaje real sin ficha) del ruido (una organización o un
   topónimo).
5. **Quinto eje — head-hopping / saltos de punto de vista / focalización rota.**
   Este eje es **semántico**: lo juzgas tú, anclado en la biblia, no un heurístico.
   El procedimiento, en orden:
   - **(a) Lee la voz narrativa declarada** en `bible/constitution.md`
     ("Voz narrativa: …") y procede **solo** bajo **tercera persona limitada /
     focalizada**. Bajo **omnisciente** o **primera persona** el head-hopping
     **no aplica**: no reportes nada por este eje.
   - **(b) Lee el POV focal por capítulo** en `bible/pov-structure.md` (la sección
     "Calendario de POV") — es prosa autoral, no está en el grafo. Dice qué
     personaje *puede* sostener la interioridad en cada capítulo.
   - **(c) Lee el *roster*** de personas declaradas (el campo `name:` de cada
     `bible/characters/*.md`, igual que el cuarto eje) para resolver a quién
     atribuye la interioridad un pasaje.
   - **(d) Juzga, capítulo a capítulo**, si la prosa atribuye **interioridad**
     (verbos de pensar / sentir / percibir, monólogo interior) a un personaje que
     **no** es el POV focal de ese capítulo: eso es un head-hop.
   - **(e) Hueco de anclaje**: cuando el calendario de POV está **ausente**, no
     tiene sección "Calendario de POV", o es un marcador **`[PENDING: …]`**
     (trátalo como *POV focal no declarado*, igual que `focalization` trata una
     voz `[PENDING]`), **reporta el hueco de anclaje y NO adivines** el POV focal:
     un ancla ausente es un hueco de entrada del juicio, nunca un head-hop
     inventado.

   Cita siempre el anclaje de este eje: la **voz declarada** + el **calendario de
   POV** (`bible/pov-structure.md`) + el ***roster*** — exactamente lo que el
   heurístico determinista no podía resolver.
6. Si no hay manuscrito todavía, repórtalo como "prerrequisito ausente" (nada que
   verificar), no falles de forma opaca.
7. Redacta los hallazgos como una lista de **desviaciones**, cada una con la cita
   del manuscrito, el hecho de la biblia que contradice y una sugerencia.

## Output

Un reporte en prosa con las desviaciones por eje (biblia, arcos, cronología,
personajes sin declarar, head-hopping) y el resultado del `graph build`. Cada
mención de una persona usada en la prosa pero **sin ficha** se reporta como **una
desviación más**: la cita del manuscrito, la frase "no entry in `bible/characters/`"
(sin ficha en `bible/characters/`) y una sugerencia (crear la ficha, o confirmar
que no es un personaje). Cada **head-hop** se reporta también como **una desviación
más**: la cita del manuscrito, la frase que nombra *la interioridad de un personaje
no focal bajo el POV focal del capítulo* (p. ej. "interiority of *Irene* under the
POV of *Teo* in *<capítulo>*") y una sugerencia (reescribir el pasaje desde el POV
focal, o confirmar el calendario de POV). Es un **juicio, no una `error`** de
validación: no nace ningún `error` de estos ejes. **No escribe nada** en el
proyecto.

## Archivos a leer

- `manuscript/`, `bible/` (fichas, `timeline.md`, `relationships.md`,
  `constitution.md`).
- `bible/characters/*.md` (el campo `name:` — el *roster* de personas),
  `bible/settings/`, `bible/locations/`, `bible/objects/` (nombres ya declarados
  que no son personas), para el cuarto eje.
- `bible/constitution.md` (la "Voz narrativa: …" — acota el quinto eje a tercera
  persona limitada) y `bible/pov-structure.md` (la sección "Calendario de POV" —
  el POV focal por capítulo), para el quinto eje (head-hopping).
- `references/golem-events-timeline.md`, `references/golem-relationships.md`,
  `references/golem-character.md` (el *roster* se lee de las fichas, no de una
  etiqueta del grafo).

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
