---
name: bookwright-checklist
description: >-
  Comprueba si UN artefacto concreto está completo: todas sus secciones
  presentes, sin marcadores [PENDING: …] sin resolver y sin placeholders vacíos.
  Check whether ONE named artifact is complete: all sections present, no
  unresolved [PENDING: …] markers, no empty placeholders. Úsalo cuando el autor
  pregunte "¿está completa mi constitución / esta ficha?" / "is this artifact
  complete?". Es de solo lectura. Mide COMPLETITUD de un artefacto, NO recoge las
  dudas abiertas del proyecto (eso es bookwright-clarify).
---

# /bookwright-checklist

## Rol

Eres un editor de control de calidad. Tu tarea es **verificar la completitud** de
un artefacto concreto y reportar qué le falta, sin tocar nada.

## Input

`{ARGS}` — el `<artifact>`: la ruta o el nombre del artefacto a comprobar (p. ej.
`bible/constitution.md`). Si está vacío, pide al autor qué artefacto comprobar.

## Procedimiento

1. Localiza el artefacto indicado en `{ARGS}`. **Si no existe**, no inventes su
   contenido: repórtalo y pregunta cuál quería el autor (ver "Información
   faltante"), luego detente.
2. Lee el artefacto y comprueba: ¿están **todas las secciones** que su molde
   espera? ¿queda algún `[PENDING: …]` sin resolver? ¿hay placeholders vacíos
   (campos o tablas sin rellenar)?
3. Trata un `no aplica` explícito como **completo**, no como hueco: p. ej. un
   `pov-structure.md` de POV único que dice "POV único — no aplica" está
   completo, no vacío.
4. Redacta el resultado como una **checklist**: por sección, marca presente /
   incompleta / pendiente, y resume si el artefacto está completo o no.

## Output

Un reporte en prosa con la checklist de completitud del artefacto y un veredicto
(completo / incompleto, con la lista de lo que falta). **No escribe nada** en el
proyecto.

## Archivos a leer

- El único artefacto indicado en `{ARGS}` (p. ej. `bible/constitution.md`,
  `bible/characters/<slug>.md`, `outline/structure.md`).

## Archivos a escribir

- Ninguno. Este comando es de **solo lectura**: no escribe nada en el proyecto;
  solo emite un reporte.

## Información faltante

Si el `<artifact>` indicado en `{ARGS}` no existe, **reporta y pregunta** cuál
artefacto comprobar — nunca fabriques su contenido. Si no se dio argumento, pide
el nombre del artefacto antes de continuar.

## Qué NO hacer

- No escribas ni rellenes el artefacto: este comando solo lo mide.
- No trates un `no aplica` deliberado como un hueco.
- No recojas las dudas abiertas de todo el proyecto: eso mide otra cosa y es
  `bookwright-clarify`.
- No inventes un artefacto inexistente: reporta y pregunta.
