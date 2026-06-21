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

### DEBT-008 — el heurístico de proper-noun marca la primera palabra de los encabezados markdown
- **Estado:** abierta
- **Detectada en:** dogfooding v0.4.5 (2026-06-21)
- **Ubicación:** `src/bookwright/validation/validators/character_presence.py` (regla `_CANDIDATE` + exclusión por `_SENTENCE_END`/inicio de línea, ~líneas 23–29 y 160–166)
- **Clase de deuda:** falso positivo de validador (heurístico que no contempla la sintaxis markdown del manuscrito)
- **Descripción:** el chequeo `character_presence` excluye una mayúscula a inicio de línea o tras puntuación de fin de frase (es gramatical, no un nombre propio), pero no salta el prefijo de encabezado markdown (`# `, `## `, …). La primera palabra de todo `# Capítulo 1` queda precedida por `# ` y se trata como mitad de frase, disparando `proper noun 'Capítulo' appears in the manuscript but has no bible entry` en cada cabecera de capítulo. Reproducido en la corrida de dogfooding (`manuscript/cap-01.md:1`). Es `warning`, no rompe CI, pero es ruido recurrente en cualquier manuscrito con encabezados.
- **Por qué se difiere:** el track v0.4.x (post-dogfooding) está cerrado y sin deuda abierta; esta es una clase de validador distinta a las que tocó (focalización), así que limpiarla aquí rompería el scope. Es su propia iteración.
- **Resolución sugerida / versión objetivo:** normalizar la línea quitando el prefijo de encabezado markdown (y, opcionalmente, todo `#{1,6}\s+` de apertura) antes de aplicar el heurístico, de modo que la primera palabra del heading reciba el mismo trato de "inicio de oración" que ya existe; añadir un fixture de manuscrito con encabezados de capítulo al test del validador. Patch menor (siguiente hardening de validación).

---

## Deuda aceptada (no se arreglará)

_Ninguna por ahora._
