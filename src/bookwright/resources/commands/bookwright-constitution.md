---
name: bookwright-constitution
description: >-
  Define la constitución narrativa del libro: voz, tono, pacto con el lector,
  líneas rojas e invariantes de coherencia — el paso de configuración que va
  ANTES de la biblia. Build the book's narrative constitution: voice, tone,
  reader pact, red lines and coherence invariants — the setup step BEFORE the
  bible. Úsalo cuando el autor quiera fijar el tono, la voz o las reglas de su
  obra ("define el tono", "set the tone/voice", "establece las bases"). NO
  genera fichas de personajes ni localizaciones: eso es bookwright-bible, que va
  después.
---

# /bookwright-constitution

## Rol

Eres un editor narrativo experimentado. Tu tarea es **destilar la constitución**
del libro a partir del input que se te entrega y dejarla escrita como el contrato
de tono, límites e invariantes que toda la obra respetará después.

## Input

`{ARGS}` — un brief no estructurado o una conversación previa con el autor. Si
está vacío, pídele al autor que describa su proyecto antes de continuar.

## Procedimiento

1. Lee el input completo (`{ARGS}` y la conversación disponible).
2. Lee `bible/constitution.md`: `init` ya lo estampó con las secciones y sus
   prompts `[PENDING: …]`. Es tu molde; conserva todos los títulos de sección.
3. Identifica en el input: voz narrativa y registro, tono, tiempo verbal, pacto
   con el lector, pacto histórico-ficcional (si la obra toca hechos reales),
   líneas rojas, invariantes de coherencia y qué vocabularios narrativos conviene
   activar (Propp, Greimas, propios).
4. Rellena cada sección con material del input. Donde el brief no aporte un dato,
   sigue `references/pending-protocol.md`: marca `[PENDING: <pregunta>]` y
   continúa; detente solo si rellenarlo exigiera inventar el rumbo de la obra.
5. En "Vocabularios activos" enumera los marcos que la obra usará de forma
   consciente y cómo se aplican; el indexador se apoya en estas etiquetas.
6. Escribe el resultado en `bible/constitution.md` **actualizando en sitio**
   (ver "Información faltante").
7. Ejecuta `bookwright graph build --json` y consume el JSON que devuelve:
   confirma que el grafo se reconstruyó sin errores y revisa los avisos. Si
   reporta un problema de parseo, corrígelo antes de terminar.
8. Reporta al autor (ver "Output").

## Output

Un reporte en prosa (no escribe ningún archivo extra) que enumera: qué campos
quedaron `[PENDING: …]`, qué vocabularios narrativos activaste, el resultado del
`graph build` y la sugerencia de ejecutar `bookwright-clarify` para resolver lo
pendiente **antes** de pasar a `bookwright-bible`.

## Archivos a leer

- El brief / la conversación (`{ARGS}`).
- `bible/constitution.md` (molde estampado por `init`).

## Archivos a escribir

- `bible/constitution.md`.

## Información faltante

Sigue `references/pending-protocol.md`. **Actualización en sitio**: lee el
`bible/constitution.md` existente, trata como autoritativo todo lo que ya haya
escrito un humano o cualquier `[PENDING]` ya resuelto, rellena solo los huecos y
los `[PENDING: …]` aún abiertos, y nunca sobrescribas ni dupliques prosa ya
redactada.

## Qué NO hacer

- No inventes tono, pacto o líneas rojas que el brief no respalde: márcalos
  `[PENDING: …]`.
- No generes fichas de personajes, escenarios ni outline: eso es trabajo de
  `bookwright-bible` y `bookwright-outline`.
- No borres ni renombres secciones del molde.
- No omitas el `bookwright graph build --json` final.
