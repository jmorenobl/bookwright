# Deuda técnica conocida — Bookwright

> **Propósito:** registro plano y trackeado (Principio I) de la deuda técnica
> que un paso del ciclo SDD **detecta pero no limpia en el acto** porque hacerlo
> excedería el scope de la iteración en curso (Scope discipline: no se implementa
> ni se refactoriza por delante del plan). Esta deuda **no se descarta jamás**:
> queda aquí hasta que se resuelve en su propia iteración.
>
> **Qué NO va aquí:**
> - Deuda de la **misma clase** que toca la iteración en curso — esa se barre
>   *entera* en esa misma iteración (todas las instancias, aunque vivan fuera del
>   diff). Precedente: iteración 027 unificó *todos* los envelopes JSON, no solo
>   el citado. Si la clase ya se está tocando, no se difiere: se limpia.
> - Conceptos GOLEM modelados-pero-no-ingestados — esos tienen su propio
>   contrato en `src/bookwright/golem/deferrals.py` (y su test de paridad).
> - Trabajo deliberadamente **cancelado** (presets, Grafeo, multi-integración,
>   extension system) — eso vive en `bookwright-roadmap.md`, no es deuda.
>
> **Regla del ciclo (`bookwright-quality` workflow):** todo paso que encuentre
> deuda ajena al scope la **anexa aquí** (con ubicación, clase, motivo de
> diferimiento y versión sugerida) **y** la reporta en voz alta en su salida.
> Cuando una iteración limpia la deuda, **se borra su entrada** — git conserva
> el historial, igual que `deferrals.py` borra la entrada de un concepto al
> cablearlo (no se archiva en una sección "resuelta", eso solo duplicaría git).
> La única deuda que permanece registrada estando "cerrada" es la que decides
> **no arreglar nunca** (estado `aceptada`): se queda para que el workflow no la
> vuelva a detectar y re-anotar en cada pasada.

## Formato de entrada

```
### DEBT-NNN — <título corto>
- **Estado:** abierta | aceptada (no se arreglará — motivo)
- **Detectada en:** spec-NNN (<fecha>)
- **Ubicación:** <path:línea o módulo>
- **Clase de deuda:** <p. ej. envelope JSON duplicado, validador no cubierto, …>
- **Descripción:** <qué es y por qué es deuda>
- **Por qué se difiere:** <por qué limpiarla ahora rompería el scope de la iteración>
- **Resolución sugerida / versión objetivo:** <cómo limpiarla y cuándo>
```

---

## Deuda abierta

### DEBT-003 — Segmento URI `narrative-role` obsoleto en la tabla de diseño
- **Estado:** abierta
- **Detectada en:** spec-033 (2026-06-21)
- **Ubicación:** `bookwright-design.md:203` (tabla "segmento fijo por concepto", § 6)
- **Clase de deuda:** inconsistencia de documentación en el diseño canónico (la
  tabla nombra un segmento URI que ningún código acuña).
- **Descripción:** la fila `| Rol narrativo (`G11_Narrative_Role`) |
  `narrative-role` | slug |` asigna a G11 un segmento URI de nivel superior que
  nunca se materializó: la única encarnación real de G11 es el nodo
  `CharacterRole` anidado en personaje, con URI `{personaje}/role/{slug}` (no
  `narrative-role`). El segmento `narrative-role` era el `path_segment` de la
  clase muerta `NarrativeRole`, eliminada en spec-033. La drift es **previa** a
  esta iteración (el segmento jamás se acuñó) y el propio diseño ya enuncia la
  semántica correcta en otra parte (línea 1603: "G11 = rol de un personaje";
  § 7.4: los roles resuelven contra roles de personaje, no acuñan).
- **Por qué se difiere:** clase distinta a la que toca spec-033 (honestidad del
  registro `CONCEPTS` en código + prosa de conteo). `bookwright-design.md` es el
  diseño canónico congelado autoría del owner (numeración de secciones
  load-bearing); el spec-033 lo dejó **deliberadamente** fuera de scope y lo
  cita como autoridad (línea 1603, § 7.4). Reescribir el artefacto canónico en
  una pasada de revisión automática excedería el scope y la disciplina del plan.
- **Resolución sugerida / versión objetivo:** en una iteración que toque la
  documentación de diseño, reconciliar la fila para reflejar el carácter
  anidado-en-personaje de G11 (segmento `role` bajo el personaje) o retirarla,
  alineándola con la línea 1603 / § 7.4. Edición en español, sin renumerar.

---

## Deuda aceptada (no se arreglará)

_Ninguna por ahora._
