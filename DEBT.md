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

### DEBT-011 — `character_presence` marca el primer término tras una comilla-líder de apertura (`«` U+00AB, `"` U+201C, `'` U+2018, `"` ASCII)
- **Estado:** abierta
- **Detectada en:** auditoría de `spec-041` (2026-06-22) — al cerrar DEBT-009 (la raya de diálogo `—`/`–`/`―`) se verificó **empíricamente** que la *misma clase* de fallo persiste para los marcadores de comilla líder.
- **Ubicación:** `src/bookwright/io/prose.py` (`_normalize` retira encabezados ATX, viñetas/citas ASCII y —tras 041— las tres rayas de diálogo `—`/`–`/`―`; NO retira la comilla angular `«`/`»` U+00AB/BB, las comillas tipográficas `"`/`"` U+201C/D, ni las comillas rectas ASCII `"`/`'`); consumido por `character_presence._is_sentence_initial` (`_SENTENCE_END` ya cubre `¿¡` pero no estas comillas).
- **Clase de deuda:** emparentada con DEBT-008/DEBT-009 / issue #1 (acoplamiento a un marcador de superficie líder no normalizado), pero un *diseño distinto*: la comilla es un marcador **par** (apertura…cierre), no una raya líder simple.
- **Descripción:** `«Esto es el porvenir»` y `"Hola"` dejan el primer término citado (`Esto`, `Hola`) en offset ≠ 0 con un prefijo de comilla (`«`/`"`) que no está en `_SENTENCE_END`, así que `_is_sentence_initial` devuelve `False` y el demostrativo/saludo se marca como nombre propio sin entrada en la bible. Verificado en la auditoría de spec-041: ambas formas producen el flag espurio hoy. **Confirmado empíricamente** por el dogfood `sombra-en-el-puerto` (novela negra, 2026-06-23, banco desechable fuera del repo): `«Inspectora` y `«Las` —primer término de cada línea de diálogo abierta con `«`— se reportan como nombre propio sin entrada; `Las` es además un **artículo**, no un nombre propio, y solo se marca por el desplazamiento de offset que introduce la `«` (evidencia de que el fallo es de superficie, no de léxico). (La barra horizontal `―` U+2015 era de esta familia pero es *misma clase y mismo diseño* que la raya de diálogo, así que **se barrió en 041** junto a `—`/`–`, no se difiere aquí.)
- **Por qué se difiere:** 041 cierra todas las *rayas* de diálogo (`—`/`–`/`―`), la convención española dominante y el caso observado en el dogfood de `tiny-historical`. Las comillas son un marcador DISTINTO con semántica de par (apertura `«`…cierre `»`), pueden aparecer a mitad de línea como contenido citado, y su normalización (¿retirar solo la comilla de apertura líder?, ¿la de cierre?, interacción con el `¿¡` que `_SENTENCE_END` ya trata) es una decisión de diseño propia, mayor que añadir un code-point a la clase de caracteres de la raya.
- **Resolución sugerida / versión objetivo:** iteración 043 (track `v0.5.x`, `v0.5.3`; gemela de 041). En el seam (`io/prose.py`), extender `_normalize` para retirar el marcador de comilla de apertura líder (`«`, `"`, `"`, `'`) — restaurando el primer término a inicio-de-frase y heredando la exención existente, mismo mecanismo que 041. Ningún validador se toca.

### DEBT-012 — `character_presence` escanea el cuerpo de un encabezado (título) como prosa más allá de la primera palabra
- **Estado:** abierta
- **Detectada en:** dogfood `sombra-en-el-puerto` (novela negra, 2026-06-23) — banco desechable fuera del repo, sobre `v0.5.2`.
- **Ubicación:** `src/bookwright/validation/validators/character_presence.py` (`_unknown_mentions`: `_HEADING_MARKER.sub("", line, count=1)` retira el marcador ATX, pero el RESTO del título se escanea como prosa); emparentada con la costura `io/prose.py`.
- **Clase de deuda:** issue #1 / DEBT-008 (el validador trata markup estructural —aquí el cuerpo de un título— como prosa narrativa), pero un *mecanismo distinto* de DEBT-011: no es un marcador líder que desplaza el primer token, es que un TÍTULO entero no es prosa.
- **Descripción:** DEBT-008 exime solo la PRIMERA palabra del encabezado (`Capítulo` en `# Capítulo 1 — Marea baja`, que cae a offset 0 y hereda la exención de inicio-de-frase). El resto del título se sigue escaneando como prosa, así que una palabra capitalizada tras la raya interna del título (`Marea` de "— Marea baja") se reporta como nombre propio sin entrada en la bible. Verificado en el dogfood: `# Capítulo 1 — Marea baja` dispara sobre `Marea` (`manuscript/01-marea-baja.md:1`). Un título de capítulo es texto editorial, no prosa narrativa: sus nombres propios son estilísticos y los personajes reales del capítulo se mencionan igual en el cuerpo.
- **Por qué se difiere:** el dogfood que lo destapó es un banco fuera del repo; arreglarlo a mano en `main`, sin iteración numerada, viola la disciplina de scope. Además el mecanismo correcto (¿eximir TODA la línea de encabezado del heurístico de nombres propios?, ¿en la costura o como política anclada del validador?) es una decisión de `/speckit-plan`, no un ad hoc.
- **Resolución sugerida / versión objetivo:** iteración 044 (track `v0.5.x`, `v0.5.4`). Tratar la línea de encabezado como no-prosa para la regla de menciones-desconocidas: detectado el marcador ATX, eximir TODO el cuerpo del título (no solo la primera palabra). Decidir en `/speckit-plan` si la exención vive en la costura (`io/prose.py` señala la línea como encabezado) o como política en `character_presence`. La regla de huérfanos (`error`) y el gate no se tocan.

### DEBT-013 — `character_presence` marca nombres de organización (no hay roster de organizaciones)
- **Estado:** abierta
- **Detectada en:** dogfood `sombra-en-el-puerto` (2026-06-23).
- **Ubicación:** `src/bookwright/validation/validators/character_presence.py` (`_unknown_mentions`) + el conjunto de clases GOLEM con roster (no existe una clase «Organization» ni `bible/organizations/`).
- **Clase de deuda:** NO es acoplamiento de superficie (issue #1) — es el límite **semántico** del heurístico: un nombre de organización capitalizado y off-roster es indistinguible, para un heurístico de mayúsculas sin NER, de un nombre propio sin declarar.
- **Descripción:** en "la Naviera Salas", `Naviera` (cabeza del nombre de la organización) se reporta como nombre propio sin entrada en la bible (`manuscript/01-marea-baja.md:13`), aunque `Salas` sí esté en el roster de personajes (`Víctor Salas`). La unión de rosters de DEBT-010 (character/setting/location/object) NO cubre organizaciones. Ninguna normalización de superficie lo cura.
- **Por qué se difiere:** a diferencia de DEBT-011/012, esto NO se arregla en el seam. Requiere una **decisión de diseño** previa, no un patch: **(a)** introducir una 5ª clase de roster (organizaciones) y su directorio en la bible —lo que amplía la ingestión y roza el cierre congelado del Principio X, con su propio análisis—, o **(b)** diferirlo al juicio semántico (movimiento 3 de issue #1, demand-pulled), que distinguiría «Naviera = organización» de «Elena = personaje sin declarar» sin un roster nuevo. Elegir entre (a) y (b) es materia de la **issue #1** (`design`/`discussion`), no de una iteración lista.
- **Resolución sugerida / versión objetivo:** **PENDIENTE DE DECISIÓN DE DISEÑO** (issue #1). No se promueve a iteración hasta resolver (a) vs. (b). Trigger: que el ruido de organizaciones se mida alto y frecuente en libros reales (→ justifica el roster nuevo o activa el movimiento 3).

---

## Deuda aceptada (no se arreglará)

_Ninguna por ahora._
