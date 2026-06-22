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

### DEBT-010 — `character_presence` marca tokens de settings multi-palabra como nombres propios sin entrada
- **Estado:** abierta
- **Detectada en:** dogfood v0.5.0 (2026-06-22) — fixture `tiny-historical`
- **Ubicación:** `src/bookwright/validation/validators/character_presence.py:107` (`roster = project.character_names()` — solo personajes, no settings/locations/objects).
- **Clase de deuda:** roster de cruce incompleto (el heurístico solo conoce el roster de personajes).
- **Descripción:** `la Real Fábrica de Paños` es un setting declarado (`bible/settings/la-real-fabrica-de-panos.md`), pero `character_presence` solo cruza contra `character_names()`, así que sus tokens `Real`, `Fábrica`, `Paños` se marcan como nombres propios «sin entrada en la bible» — cuando la entrada existe, solo que en `settings/` en vez de `characters/`. El texto del warning es honesto («heuristic — may be a place or organization»), pero sobre una novela terminada el ruido es alto y el diagnóstico engañoso.
- **Por qué se difiere:** es una cuestión de diseño (¿debe `character_presence` consultar también settings/locations/objects, o crearse un validador de presencia de entornos?), mayor que un fix puntual; fuera del scope de v0.5.0.
- **Resolución sugerida / versión objetivo:** **iteración 042 → `v0.5.2`** (ver `bookwright-implementation-plan.md` § 1+). La regla de menciones-desconocidas suprime candidatos cuyo slug (o tokens) casen la UNIÓN de los rosters de personajes + settings + locations + objects (nuevos accesores `location_names()`/`object_names()` en `ValidationContext`, espejo de `setting_names()`); la regla de huérfanos (`error`, protege el gate) y el guard `NotEvaluated` de 040 no cambian.

### DEBT-011 — `character_presence` marca el primer término tras una comilla-líder de apertura (`«` U+00AB, `"` U+201C, `'` U+2018, `"` ASCII)
- **Estado:** abierta
- **Detectada en:** auditoría de `spec-041` (2026-06-22) — al cerrar DEBT-009 (la raya de diálogo `—`/`–`/`―`) se verificó **empíricamente** que la *misma clase* de fallo persiste para los marcadores de comilla líder.
- **Ubicación:** `src/bookwright/io/prose.py` (`_normalize` retira encabezados ATX, viñetas/citas ASCII y —tras 041— las tres rayas de diálogo `—`/`–`/`―`; NO retira la comilla angular `«`/`»` U+00AB/BB, las comillas tipográficas `"`/`"` U+201C/D, ni las comillas rectas ASCII `"`/`'`); consumido por `character_presence._is_sentence_initial` (`_SENTENCE_END` ya cubre `¿¡` pero no estas comillas).
- **Clase de deuda:** emparentada con DEBT-008/DEBT-009 / issue #1 (acoplamiento a un marcador de superficie líder no normalizado), pero un *diseño distinto*: la comilla es un marcador **par** (apertura…cierre), no una raya líder simple.
- **Descripción:** `«Esto es el porvenir»` y `"Hola"` dejan el primer término citado (`Esto`, `Hola`) en offset ≠ 0 con un prefijo de comilla (`«`/`"`) que no está en `_SENTENCE_END`, así que `_is_sentence_initial` devuelve `False` y el demostrativo/saludo se marca como nombre propio sin entrada en la bible. Verificado en la auditoría de spec-041: ambas formas producen el flag espurio hoy. (La barra horizontal `―` U+2015 era de esta familia pero es *misma clase y mismo diseño* que la raya de diálogo, así que **se barrió en 041** junto a `—`/`–`, no se difiere aquí.)
- **Por qué se difiere:** 041 cierra todas las *rayas* de diálogo (`—`/`–`/`―`), la convención española dominante y el caso observado en el dogfood de `tiny-historical`. Las comillas son un marcador DISTINTO con semántica de par (apertura `«`…cierre `»`), pueden aparecer a mitad de línea como contenido citado, y su normalización (¿retirar solo la comilla de apertura líder?, ¿la de cierre?, interacción con el `¿¡` que `_SENTENCE_END` ya trata) es una decisión de diseño propia, mayor que añadir un code-point a la clase de caracteres de la raya.
- **Resolución sugerida / versión objetivo:** una iteración futura (horizonte demand-pulled, tras 042). En el seam (`io/prose.py`), extender `_normalize` para retirar el marcador de comilla de apertura líder (`«`, `"`, `"`, `'`) — restaurando el primer término a inicio-de-frase y heredando la exención existente, mismo mecanismo que 041. Ningún validador se toca.

---

## Deuda aceptada (no se arreglará)

_Ninguna por ahora._
