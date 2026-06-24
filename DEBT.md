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
> - **Track A — honestidad** (`not_evaluated`): DEBT-019
>   (abierta por spec-045 como efecto colateral de que `focalization`
>   deje de fingir el head-hopping y se abstenga bajo tercera-limitada;
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
>   se ingiere igual sin `crm:P2_has_type`. Eliminada de este registro), DEBT-017.
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

### DEBT-017 — `narrative_structure` identifica la unidad de forma inconsistente entre sus dos reglas (nombre vs. slug)
- **Estado:** abierta
- **Detectada en:** dogfood `sombra-en-el-puerto` (2026-06-23), ronda de estructura narrativa.
- **Ubicación:** `src/bookwright/validation/validators/narrative_structure.py` (la regla de rol-sin-resolver imprime el `name` humano de la unidad; la regla de beat-huérfano imprime el `slug`).
- **Clase de deuda:** inconsistencia de presentación dentro de un mismo validador (pulido / UX), sin impacto funcional.
- **Descripción:** sobre la misma clase de entidad (unidad narrativa G9), los dos mensajes usan identificadores distintos: `narrative unit 'La fechoría en el muelle' references role 'informante' …` (nombre humano) vs. `narrative unit 'el-recuerdo-de-la-primera-marea' belongs to no narrative sequence …` (slug). El locator `relpath:línea` es correcto en ambos; lo inconsistente es qué identificador se imprime.
- **Por qué se difiere:** banco fuera del repo; trivial pero ajeno al scope de cualquier iteración en curso, y conviene fijar primero la convención (¿siempre el `name` humano? ¿siempre el slug? ¿ambos?) para aplicarla a todos los validadores a la vez.
- **Resolución sugerida / versión objetivo:** **track B (pulido determinista)** (puede ir junto a DEBT-015, ambos son consistencia de mensajes). Unificar el identificador de unidad (preferiblemente el `name` humano, con el slug entre paréntesis si hace falta) en las dos reglas.

### DEBT-019 — el contrato `NotEvaluated` todo-o-nada obliga a `focalization` a abstenerse del validador entero bajo tercera-limitada, dejando de ejecutar la comprobación determinista de ruptura de primera persona
- **Estado:** abierta
- **Detectada en:** spec-045 (2026-06-23), paso de endurecimiento de la spec.
- **Ubicación:** `src/bookwright/validation/validators/focalization.py` (`validate()` se abstiene del run entero bajo tercera-limitada tras 045) + el contrato de `src/bookwright/validation/base.py` (`NotEvaluated` es todo-o-nada: un validador o devuelve `list[Violation]` o lanza `NotEvaluated`, nunca ambos en un mismo run).
- **Clase de deuda:** ausencia de **evaluación parcial** — un validador que SÍ puede comprobar deterministamente una dimensión (ruptura de 1ª persona) pero necesita juicio semántico para otra (head-hopping) debe abstenerse del validador ENTERO, perdiendo la dimensión determinista. Es familia 040 (honestidad), pero a nivel de *sub-comprobación* dentro de un validador, no de fichero de entrada (DEBT-018) ni de regla de conjunto abierto (043).
- **Descripción:** tras 045, una declaración de voz «Tercera persona limitada, focalizada en X» hace que `focalization` declare `not_evaluated` (`kind=pending_capability`) para TODO el run, así que `_first_person_breaks` (marcadores de 1ª persona fuera de diálogo bajo 3ª declarada) ya **no** se ejecuta para proyectos focalizados — aunque sí siga ejecutándose bajo 3ª **no-limitada** (omnisciente). Verificado: las tres fixtures focalizadas (`tiny-historical`, `tiny-novel`, `tiny-quest`) emiten hoy cero hallazgos de `focalization`, así que la regresión es **real pero invisible** en la suite (ninguna fixture ejercita un break de 1ª persona bajo 3ª-limitada). La razón fija del `not_evaluated` (FR-002 de 045) habla solo de head-hopping, de modo que la pérdida de la comprobación de persona no queda ni siquiera nombrada en la entrada.
- **Por qué se difiere:** arreglarlo de verdad exige un **contrato de evaluación parcial** (un validador emitiendo hallazgos **y** una entrada `not_evaluated` en el mismo run), un cambio de la escala de 040/044 y ajeno al scope de 045 (que solo CONSUME `pending_capability`, sin tocar el contrato). Contenerlo con un hack condicional-a-hallazgos (devolver `[]` o abstenerse según si `_first_person_breaks` encontró algo) sería justo el smell que la doctrina prohíbe.
- **Resolución sugerida / versión objetivo:** **track A (honestidad, familia 040)** o subsumida por **track C (move 3)**. (a) Introducir un contrato de evaluación parcial para que `focalization` corra `_first_person_breaks` Y declare la abstención de head-hopping a la vez. (b) El move 3 cubre consistencia de persona + focalización de forma semántica y la mitad determinista deja de hacer falta. Validador de prosa, `triples=()`, ontología congelada intacta.

### DEBT-020 — `bookwright init` falla el primer commit si git no tiene identidad configurada
- **Estado:** abierta
- **Detectada en:** caso de onboarding real (amigo psicólogo, Windows, 2026-06-23).
- **Ubicación:** `src/bookwright/commands/init/git.py` (`git init` + `git add` + `git commit`) y `src/bookwright/commands/init/resolve.py` (hoy solo resuelve el autor del manifest desde git config con fallback a `$USER`/"Unknown Author"; no fija la identidad de git para el commit).
- **Clase de deuda:** brecha de onboarding — el commit inicial de `init` aborta con el error de git "Please tell me who you are" (`user.name`/`user.email` sin configurar), un muro para un autor no-técnico que acaba de instalar git.
- **Descripción:** en una máquina con git recién instalado y sin `user.name`/`user.email` globales, `git commit` falla. `init` ya lee git config para el autor del manifest, pero no garantiza que el commit tenga identidad: si falta, el primer commit del proyecto explota con un mensaje pensado para programadores. Es justo el punto donde el onboarding del horizonte demand-pulled (roadmap § 5, «Onboarding de un comando») delega la identidad git en `init`/`doctor` en vez de en el bootstrap.
- **Por qué se difiere:** ajeno al scope de la iteración en curso (validación, issue #1). Toca el flujo de `init` y conlleva una pequeña decisión de UX (¿preguntar nombre/email interactivamente?, ¿fijar identidad **local del repo** —nunca global a ciegas—?, ¿qué hacer en modo `--json`/no-interactivo?), propia de su iteración.
- **Resolución sugerida / versión objetivo:** parte del onboarding demand-pulled. Cuando falte identidad git, `init` la pide (interactivo) o la deriva del autor ya resuelto y la fija **local al repo** (`git -c user.name=… -c user.email=…` para el commit, o `git config --local`), de modo que el primer commit nunca aborte; en modo no-interactivo, usar el fallback del manifest y avisar por stderr. Idealmente compartido con un futuro `bookwright doctor`.

---

## Deuda aceptada (no se arreglará)

_Ninguna por ahora._
