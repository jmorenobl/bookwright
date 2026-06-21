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

### DEBT-007 — el placeholder `[PENDING]` de la constitución se parsea como una voz narrativa declarada
- **Estado:** abierta
- **Detectada en:** dogfooding "El Faro de Halia" (2026-06-21)
- **Ubicación:** `src/bookwright/validation/validators/focalization.py:154-179`
  (`_parse_declaration`); origen del texto en
  `src/bookwright/resources/project/bible/constitution.md.j2:20` (la línea
  `- **Voz narrativa**: [PENDING: …(primera/tercera persona, omnisciente/limitada)?]`).
- **Clase de deuda:** parsing de la declaración de focalización (misma clase que
  DEBT-004, cerrada en la iteración 034 / `v0.4.2`).
- **Descripción:** un proyecto recién creado por `bookwright init`, con la
  constitución **sin rellenar**, ya dispara avisos `focalization` de *head-hopping*
  contra **todos** los personajes en cuanto el manuscrito contiene un verbo de
  interioridad (`pensó/supo/sintió/…`). La causa es que el texto del placeholder
  `[PENDING: …]` contiene literalmente "tercera persona" y "limitada", de modo que
  `_parse_declaration` lo acepta como una declaración real y deduce
  `person=third, limited=True, focal=None`; con `focal=None` cada personaje cuenta
  como "non-focal". El docstring del propio validador promete lo contrario ("No
  parsable declaration → zero findings (edge case)"): la intención es que una
  constitución no rellenada produzca cero hallazgos, y el placeholder derrota esa
  intención. Verificado empíricamente: sustituir el `[PENDING]` por una voz real
  focalizada ("Tercera persona limitada, focalizada en Halia") hace desaparecer el
  aviso espurio del personaje focal.
- **Por qué se difiere:** el dogfooding es un ejercicio de detección, no una
  iteración; arreglarlo en el acto saltaría el ciclo SDD (spec → plan → tasks →
  implement) que el repo exige para todo cambio de comportamiento.
- **Resolución sugerida / versión objetivo:** iteración 037, patch `v0.4.5`.
  Guard en `_parse_declaration`: tratar como "no declaración" (devolver `None`)
  cuando el cuerpo de la declaración es todavía un token `[PENDING: …]` sin
  responder. Test en `tests/validation/` que parta de la constitución del scaffold
  + un manuscrito con un verbo de interioridad y exija cero hallazgos
  `focalization`. Mantener el comportamiento actual cuando el cuerpo es una voz
  real (no regresión sobre las fixtures existentes).

Las tres entradas del **ejercicio de dogfooding** previo sobre un libro real ("El
Cerco de Almenara", 49 ficheros / 90 entidades / 1550 triples, 2026-06-21) están
cerradas y borradas de aquí (git conserva el historial): el validador
`focalization` dormido (DEBT-004) en la iteración 034 / `v0.4.2`, el gap de recall
narrativo G9 (DEBT-005) en la iteración 035 / `v0.4.3`, y los mensajes de error de
research ciegos en la iteración 036 / `v0.4.4`.

---

## Deuda aceptada (no se arreglará)

_Ninguna por ahora._
