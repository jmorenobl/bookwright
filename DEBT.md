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

> **Re-disposición tras la decisión de la issue #1 (2º dogfood, 2026-06-23).** El
> 2º dogfood midió la regla de menciones-desconocidas de `character_presence`
> (`warning`) como **100% ruido** (4 FP, 0 señal) sobre prosa real, y la issue #1
> decidió: el heurístico de **conjunto abierto** deja de fingir y declara
> `not_evaluated` (familia 040), y el **move 3** (juicio semántico) se **activa**
> como su cura de raíz. Eso reparte estas 8 deudas en tres destinos (ver
> `bookwright-roadmap.md` § 3, `bookwright-design.md` § 13.5):
> - **Track A — honestidad** (`not_evaluated`): la regresión de cobertura de
>   `focalization` bajo tercera-limitada —la abstención todo-o-nada de spec-045
>   dejaba de correr la ruptura determinista de 1ª persona— la **cerró la
>   iteración 050**, que introduce el contrato de **evaluación parcial** (forma
>   (c) `EvalResult`, § 13.1) para que `focalization` corra esa ruptura Y declare
>   la abstención de head-hopping en el mismo run. Eliminada de este registro
>   (git conserva el historial).
>   DEBT-018 —`validate` validaba un corpus parcial en silencio— la **cerró la
>   iteración 046**, que surfacéa cada fichero de la bible omitido como entrada
>   `not_evaluated` `validator="ingestion"`, así que sale de este registro). El
>   head-hopping de `focalization` —su mitad-honestidad— se cerró en la **iteración
>   045** (declara `not_evaluated`, `kind=pending_capability`), así que su entrada
>   sale de este registro; su techo de precisión lo cura el move 3 (track C). (DEBT-011 y
>   DEBT-012 estaban aquí como **subsumidas** —des-ruido de la regla de
>   menciones-desconocidas— y la **iteración 043** las cerró: partió esa regla al
>   abstainer `character_unknown_mentions`, que declara `not_evaluated`, así que los
>   parches de costura por instancia ya no aplican. Eliminadas de este registro.)
> - **Track B — pulido determinista:** ~~DEBT-015~~ (cerrada en la **iteración
>   048**, que hace que los dos validators graph-consumer —`factual_anchor`,
>   `temporal`— emitan un locator resoluble y un identificador legible:
>   `factual_anchor` resuelve `source` a `bible/research/<tema>.md` vía
>   `AnchorIdentity.relpath` sobre un corpus de investigación construido en proceso
>   y nombra el ancla con el handle compartido `anchor_handle` que ya usa `status`;
>   `temporal` aplica `resolve_source` también en las reglas a/b/c sobre un evento
>   implicado determinista. Eliminada de este registro), ~~DEBT-016~~ (cerrada en la
>   **iteración 047**, que hace que `graph build` emita un `warning` no fatal
>   —canal `untyped_vocab_terms`— enumerando los términos válidos cuando un
>   `functions:`/`narrative_roles:` con vocab activo no case ningún término; el nodo
>   se ingiere igual sin `crm:P2_has_type`. Eliminada de este registro), ~~DEBT-017~~
>   (cerrada en la **iteración 049**, que unifica el identificador de unidad de las
>   dos reglas de `narrative_structure` sobre el `name` humano autorado, a solas, vía
>   un único punto compartido `_unit_identifier`: la regla de beat-huérfano deja de
>   imprimir el slug y la de rol-sin-resolver queda byte-idéntica. Eliminada de este
>   registro).
> - **Track C — move 3** (juicio semántico, norte): DEBT-013 (decidido (b)), y el
>   techo de precisión del head-hopping cerrado en honestidad por la iter 045.
> - **Descartado:** parches de costura por instancia; 5º roster «organización».

## Deuda abierta

### DEBT-013 — `character_presence` marca nombres de organización (no hay roster de organizaciones)
- **Estado:** abierta
- **Detectada en:** dogfood `sombra-en-el-puerto` (2026-06-23).
- **Ubicación:** `src/bookwright/validation/validators/character_presence.py` (`_unknown_mentions`) + el conjunto de clases GOLEM con roster (no existe una clase «Organization» ni `bible/organizations/`).
- **Clase de deuda:** NO es acoplamiento de superficie (issue #1) — es el límite **semántico** del heurístico: un nombre de organización capitalizado y off-roster es indistinguible, para un heurístico de mayúsculas sin NER, de un nombre propio sin declarar.
- **Descripción:** en "la Naviera Salas", `Naviera` (cabeza del nombre de la organización) se reporta como nombre propio sin entrada en la bible (`manuscript/01-marea-baja.md:13`), aunque `Salas` sí esté en el roster de personajes (`Víctor Salas`). La unión de rosters de DEBT-010 (character/setting/location/object) NO cubre organizaciones. Ninguna normalización de superficie lo cura.
- **Por qué se difiere:** a diferencia de DEBT-011/012, esto NO se arregla en el seam. Requería una **decisión de diseño** previa: **(a)** una 5ª clase de roster (organizaciones), o **(b)** diferirlo al juicio semántico (move 3). **Resuelta en la issue #1 (2026-06-23): (b).** Un 5º roster es perseguir un conjunto abierto (tras orgs vienen topónimos, barcos, vocativos…) con una lista cerrada más; no converge y roza el Principio X. El move 3 cura el conjunto abierto entero distinguiendo «Naviera = organización» de «Elena = personaje sin declarar» sin roster nuevo.
- **Resolución sugerida / versión objetivo:** **track C — move 3** (juicio semántico, norte activado; `bookwright-roadmap.md` § 5, `bookwright-design.md` § 13.5/§ 20.6). Interim honesto ya cubierto por el track A: la regla de menciones-desconocidas declara `not_evaluated` (no emite el FP de `Naviera`). Esta deuda se cierra cuando el move 3 aterrice; no es una iteración de costura.

---

## Deuda aceptada (no se arreglará)

_Ninguna por ahora._
