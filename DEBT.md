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
> - **Track C — move 3** (juicio semántico, norte): ~~DEBT-013~~ (cerrada en la
>   **iteración 051**, que aterriza la **primera rebanada vertical de move 3**: el
>   eje «menciones de conjunto abierto / personajes sin declarar» de
>   `bookwright-continuity` lee el *roster* de personas de las fichas y juzga
>   «`Naviera` = organización» vs. «`Amelia` = personaje sin ficha» sin roster
>   nuevo, y `status` emite un *nudge* informativo `judge_undeclared_characters`
>   anclado en la fuente abstinente `character_unknown_mentions`. Eliminada de este
>   registro). Queda DEBT-021 (recall morfológico de 1ª persona) plegado con el
>   head-hopping para rebanadas posteriores de move 3.
> - **Descartado:** parches de costura por instancia; 5º roster «organización».

## Deuda abierta

### DEBT-021 — el recall completo de la ruptura de 1ª persona en `focalization` es juicio semántico (techo de conjunto abierto), no determinista
- **Estado:** abierta — **mitad de honestidad LANDED en la iteración 053**; la mitad de
  **juicio** (que la CIERRA) es la iteración 054.
- **Detectada en:** 3er dogfood `el-año-de-las-casas-vacías` (2026-06-24).
- **Avance (iteración 053, mitad de honestidad):** `focalization` ya **declara el techo
  honestamente**. Bajo **cualquier** voz de 3ª persona emite una abstención
  `pending_capability` `code="first_person_recall"`
  (`Abstention(_FIRST_PERSON_RECALL_PENDING, …)`) en ambas ramas (limitada y no-limitada,
  esta última envuelta ahora en `EvalResult`), exactamente como el head-hopping se partió en
  honestidad (045/050) y juicio (052). El silencio `[]`-significa-limpio a nivel de
  sub-chequeo queda cerrado: el techo de recall es **visible** en `not_evaluated[]`. El
  contrato gana un `code` aditivo (discriminador, como la 044 añadió `kind`) para que las dos
  abstenciones `pending_capability` de `focalization` sigan distinguibles; los nudges move-3
  pasan a clavar `(validator, code)`. El núcleo determinista del pronombre explícito
  (`_first_person_breaks`, el regex `_FIRST_PERSON`) queda **byte-idéntico**. **No** se añade
  nudge de 1ª persona todavía (su destino es la 054).
- **Lo que queda para la 054 (mitad de juicio, cierre):** el **sexto** eje de
  `bookwright-continuity` que juzga el recall morfológico anclado en la voz declarada + el
  roster + el calendario de POV, y su nudge `judge_first_person_recall` keyed en
  `(focalization, first_person_recall)`. Ahí se **elimina** esta entrada.
- **Ubicación:** `src/bookwright/validation/validators/focalization.py` (`_FIRST_PERSON`
  regex, línea ~69: `(yo|nosotros|nosotras|i|we)`; consumida por `_first_person_breaks`).
- **Clase de deuda:** **MISMA clase que el head-hopping y las menciones-desconocidas** —el
  techo **semántico** de un heurístico determinista sobre prosa de **conjunto abierto**, NO
  un hueco de recall parcheable. El chequeo que la iteración 050 (re)activó bajo
  tercera-limitada casa el **pronombre sujeto explícito** (`yo`/`nosotros`): conjunto
  **cerrado** y **sólido** (FP ~nulo). Pero "¿esta prosa **está** en 1ª persona?" es
  conjunto abierto: el español es **pro-drop** y la forma natural de deslizarse a 1ª persona
  es la **morfología verbal** sin pronombre (`Caminé`, `Me senté`, `Escribí`, `cerré`), que
  ni el regex ve ni **ningún** regex captura sin reabrir el whack-a-mole (la morfología 1sg
  colisiona: `-o` presente ≈ sustantivos; `-aba`/`-ía` 1sg ≈ 3sg).
- **Descripción:** en el banco, `manuscript/02-teo.md:7` (`yo lo entendí`) **sí** se marca
  (`warning`, el núcleo determinista sólido de 050 funcionando), pero
  `manuscript/03-dolors.md:3-13` —un pasaje **sostenido** y flagrante en 1ª persona (`cerré
  la escuela`, `Caminé hasta`, `Me senté`, `abrí`, `Escribí`, `guardé`, `apagué`), una
  ruptura real de la voz declarada de 3ª limitada— produce **cero** hallazgos porque ningún
  `yo`/`nosotros` aparece. No es que el chequeo esté "incompleto" y haya que enumerar más
  formas: es que el recall completo es **irreductiblemente semántico**, exactamente el techo
  que la issue #1 demostró que ninguna lista cerrada sube.
- **Por qué NO se parchea en determinista:** ampliar el regex a la morfología verbal (p. ej.
  `Me`/`Nos` inicial + pretérito `-é`/`-í`) **es el whack-a-mole** que la issue #1 cerró —
  perseguir un conjunto abierto con una lista cerrada más, con FP garantizados por la
  colisión morfológica. Por `bookwright-design.md` § 20.6.1 principio 1 (la frontera es el
  **sustrato**: la prosa de conjunto abierto es territorio LLM) esto es **move 3**. El
  núcleo determinista (`yo`/`nosotros`) se **conserva** como "el determinismo añade
  confianza, nunca suprime" (principio 3): cortocircuita el caso inequívoco; el LLM cubre el
  recall morfológico anclado en la voz declarada del grafo (principio 2).
- **Resolución sugerida / versión objetivo:** **track C — move 3**, plegada con el
  head-hopping (`focalization` ya abstiene de él) y las menciones-desconocidas (la
  primera rebanada de move 3, ~~DEBT-013~~, cerrada en la iteración 051) — son **la
  misma cara** del techo semántico. Se parte en dos rebanadas verticales, igual que el
  head-hopping: **honestidad** (iteración 053, LANDED — la abstención `first_person_recall`
  + el contrato `code`) y **juicio** (iteración 054, que CIERRA esta entrada — el sexto eje
  + su nudge). No bloquea el gate (`focalization` es `warning`). El núcleo determinista del
  pronombre explícito se mantiene intacto entretanto.

---

## Deuda aceptada (no se arreglará)

_Ninguna por ahora._
