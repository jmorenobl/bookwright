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
> - **Track A — honestidad** (`not_evaluated`): DEBT-011, DEBT-012 (**subsumidas**:
>   no se parchean por instancia, las absorbe la regla→`not_evaluated`), DEBT-014,
>   DEBT-018.
> - **Track B — pulido determinista:** DEBT-015, DEBT-016, DEBT-017.
> - **Track C — move 3** (juicio semántico, norte): DEBT-013 (decidido (b)), techo
>   de DEBT-014.
> - **Descartado:** 043/044 como parches de costura; 5º roster «organización».

## Deuda abierta

### DEBT-011 — `character_presence` marca el primer término tras una comilla-líder de apertura (`«` U+00AB, `"` U+201C, `'` U+2018, `"` ASCII)
- **Estado:** abierta
- **Detectada en:** auditoría de `spec-041` (2026-06-22) — al cerrar DEBT-009 (la raya de diálogo `—`/`–`/`―`) se verificó **empíricamente** que la *misma clase* de fallo persiste para los marcadores de comilla líder.
- **Ubicación:** `src/bookwright/io/prose.py` (`_normalize` retira encabezados ATX, viñetas/citas ASCII y —tras 041— las tres rayas de diálogo `—`/`–`/`―`; NO retira la comilla angular `«`/`»` U+00AB/BB, las comillas tipográficas `"`/`"` U+201C/D, ni las comillas rectas ASCII `"`/`'`); consumido por `character_presence._is_sentence_initial` (`_SENTENCE_END` ya cubre `¿¡` pero no estas comillas).
- **Clase de deuda:** emparentada con DEBT-008/DEBT-009 / issue #1 (acoplamiento a un marcador de superficie líder no normalizado), pero un *diseño distinto*: la comilla es un marcador **par** (apertura…cierre), no una raya líder simple.
- **Descripción:** `«Esto es el porvenir»` y `"Hola"` dejan el primer término citado (`Esto`, `Hola`) en offset ≠ 0 con un prefijo de comilla (`«`/`"`) que no está en `_SENTENCE_END`, así que `_is_sentence_initial` devuelve `False` y el demostrativo/saludo se marca como nombre propio sin entrada en la bible. Verificado en la auditoría de spec-041: ambas formas producen el flag espurio hoy. **Confirmado empíricamente** por el dogfood `sombra-en-el-puerto` (novela negra, 2026-06-23, banco desechable fuera del repo): `«Inspectora` y `«Las` —primer término de cada línea de diálogo abierta con `«`— se reportan como nombre propio sin entrada; `Las` es además un **artículo**, no un nombre propio, y solo se marca por el desplazamiento de offset que introduce la `«` (evidencia de que el fallo es de superficie, no de léxico). (La barra horizontal `―` U+2015 era de esta familia pero es *misma clase y mismo diseño* que la raya de diálogo, así que **se barrió en 041** junto a `—`/`–`, no se difiere aquí.)
- **Por qué se difiere:** 041 cierra todas las *rayas* de diálogo (`—`/`–`/`―`), la convención española dominante y el caso observado en el dogfood de `tiny-historical`. Las comillas son un marcador DISTINTO con semántica de par (apertura `«`…cierre `»`), pueden aparecer a mitad de línea como contenido citado, y su normalización (¿retirar solo la comilla de apertura líder?, ¿la de cierre?, interacción con el `¿¡` que `_SENTENCE_END` ya trata) es una decisión de diseño propia, mayor que añadir un code-point a la clase de caracteres de la raya.
- **Resolución sugerida / versión objetivo:** **SUBSUMIDA por el track A (honestidad)** tras la decisión de issue #1. El parche de costura por instancia (extender `_normalize` con la comilla líder) **se descarta**: es des-ruido de una regla —menciones-desconocidas— que pasa a declarar `not_evaluated` por defecto (conjunto abierto, requiere move 3). `«Las` (un artículo marcado solo por el offset de la `«`) es la prueba de que el problema es semántico, no de superficie. Se cierra cuando la iteración del track A (regla→`not_evaluated`) aterrice; el move 3 (track C) restaura la señal real. La costura `io/prose.py` se conserva intacta.

### DEBT-012 — `character_presence` escanea el cuerpo de un encabezado (título) como prosa más allá de la primera palabra
- **Estado:** abierta
- **Detectada en:** dogfood `sombra-en-el-puerto` (novela negra, 2026-06-23) — banco desechable fuera del repo, sobre `v0.5.2`.
- **Ubicación:** `src/bookwright/validation/validators/character_presence.py` (`_unknown_mentions`: `_HEADING_MARKER.sub("", line, count=1)` retira el marcador ATX, pero el RESTO del título se escanea como prosa); emparentada con la costura `io/prose.py`.
- **Clase de deuda:** issue #1 / DEBT-008 (el validador trata markup estructural —aquí el cuerpo de un título— como prosa narrativa), pero un *mecanismo distinto* de DEBT-011: no es un marcador líder que desplaza el primer token, es que un TÍTULO entero no es prosa.
- **Descripción:** DEBT-008 exime solo la PRIMERA palabra del encabezado (`Capítulo` en `# Capítulo 1 — Marea baja`, que cae a offset 0 y hereda la exención de inicio-de-frase). El resto del título se sigue escaneando como prosa, así que una palabra capitalizada tras la raya interna del título (`Marea` de "— Marea baja") se reporta como nombre propio sin entrada en la bible. Verificado en el dogfood: `# Capítulo 1 — Marea baja` dispara sobre `Marea` (`manuscript/01-marea-baja.md:1`). Un título de capítulo es texto editorial, no prosa narrativa: sus nombres propios son estilísticos y los personajes reales del capítulo se mencionan igual en el cuerpo.
- **Por qué se difiere:** el dogfood que lo destapó es un banco fuera del repo; arreglarlo a mano en `main`, sin iteración numerada, viola la disciplina de scope. Además el mecanismo correcto (¿eximir TODA la línea de encabezado del heurístico de nombres propios?, ¿en la costura o como política anclada del validador?) es una decisión de `/speckit-plan`, no un ad hoc.
- **Resolución sugerida / versión objetivo:** **SUBSUMIDA por el track A (honestidad)** tras la decisión de issue #1. Igual que DEBT-011: el parche por instancia (eximir el cuerpo del título) **se descarta**, porque des-ruida la misma regla de menciones-desconocidas que pasa a `not_evaluated` por defecto. Un nombre propio en un título es exactamente el tipo de juicio de conjunto abierto (¿estilístico? ¿personaje real?) que el move 3 (track C) resuelve. Se cierra con la iteración del track A.

### DEBT-013 — `character_presence` marca nombres de organización (no hay roster de organizaciones)
- **Estado:** abierta
- **Detectada en:** dogfood `sombra-en-el-puerto` (2026-06-23).
- **Ubicación:** `src/bookwright/validation/validators/character_presence.py` (`_unknown_mentions`) + el conjunto de clases GOLEM con roster (no existe una clase «Organization» ni `bible/organizations/`).
- **Clase de deuda:** NO es acoplamiento de superficie (issue #1) — es el límite **semántico** del heurístico: un nombre de organización capitalizado y off-roster es indistinguible, para un heurístico de mayúsculas sin NER, de un nombre propio sin declarar.
- **Descripción:** en "la Naviera Salas", `Naviera` (cabeza del nombre de la organización) se reporta como nombre propio sin entrada en la bible (`manuscript/01-marea-baja.md:13`), aunque `Salas` sí esté en el roster de personajes (`Víctor Salas`). La unión de rosters de DEBT-010 (character/setting/location/object) NO cubre organizaciones. Ninguna normalización de superficie lo cura.
- **Por qué se difiere:** a diferencia de DEBT-011/012, esto NO se arregla en el seam. Requería una **decisión de diseño** previa: **(a)** una 5ª clase de roster (organizaciones), o **(b)** diferirlo al juicio semántico (move 3). **Resuelta en la issue #1 (2026-06-23): (b).** Un 5º roster es perseguir un conjunto abierto (tras orgs vienen topónimos, barcos, vocativos…) con una lista cerrada más; no converge y roza el Principio X. El move 3 cura el conjunto abierto entero distinguiendo «Naviera = organización» de «Elena = personaje sin declarar» sin roster nuevo.
- **Resolución sugerida / versión objetivo:** **track C — move 3** (juicio semántico, norte activado; `bookwright-roadmap.md` § 5, `bookwright-design.md` § 13.5/§ 20.6). Interim honesto ya cubierto por el track A: la regla de menciones-desconocidas declara `not_evaluated` (no emite el FP de `Naviera`). Esta deuda se cierra cuando el move 3 aterrice; no es una iteración de costura.

### DEBT-014 — `focalization` no detecta head-hopping por nombre de pila (exige nombre completo + misma línea física)
- **Estado:** abierta
- **Detectada en:** dogfood `sombra-en-el-puerto` (novela negra, 2026-06-23), ronda de estrés de `focalization`.
- **Ubicación:** `src/bookwright/validation/validators/focalization.py` (`_head_hopping`: `if re.search(rf"\b{re.escape(name)}\b", line.raw)` donde `name` es el nombre COMPLETO del bible, y el verbo de interioridad debe estar en esa MISMA línea física vía `_INTERIORITY.search(line.raw)`).
- **Clase de deuda:** falso negativo de un validador que parece activo (familia DEBT-004: «validador silenciosamente dormido»), agravado por una **inconsistencia de matching** con `character_presence` (que cruza por tokens, no por nombre completo).
- **Descripción:** la constitución declara "Tercera persona limitada, focalizada en Nadia Brun" y un párrafo en clara interioridad de Víctor (`Víctor … Sintió … pensó … Recordó … tuvo miedo`) NO dispara. La regla exige (1) el nombre COMPLETO del bible (`Víctor Salas`) y (2) que aparezca en la MISMA línea física que el verbo de interioridad. La prosa narrativa real nombra a los personajes por el **nombre de pila** (`Víctor`) o por epíteto, y un párrafo largo se reparte en varias líneas físicas, así que la regla está **prácticamente dormida**. Verificado empíricamente: sustituir `Víctor` → `Víctor Salas` en la línea del verbo hace que el head-hop dispare de inmediato (`manuscript/01-marea-baja.md:38`). `character_presence` SÍ reconoce `Víctor` (cruza por tokens vía `_roster_slugs`): dos validadores con dos políticas de matching de nombres sobre la misma prosa.
- **Por qué se difiere:** el banco que lo destapó está fuera del repo; arreglarlo a mano en `main` sin iteración numerada viola la disciplina de scope. Además el arreglo correcto (¿cruzar por tokens/nombre de pila como `character_presence`?, ¿escanear por frase/párrafo en vez de por línea física?, ¿cómo evitar falsos positivos con el personaje focal nombrado por pila?) es una decisión de `/speckit-plan`, mayor que un parche.
- **Resolución sugerida / versión objetivo:** **track A (honestidad) + track C (move 3)** tras la decisión de issue #1. La issue confirmó lo que esta deuda ya intuía: «un head-hop heurístico sin juicio semántico tiene techo de precisión». Por eso NO se intenta subir el heurístico (mejorar el matching) como cura: en el **track A**, cuando `focalization` tiene una declaración focal pero su heurístico no puede atribuir interioridad de forma fiable (nombre de pila, multi-línea), **declara `not_evaluated`** en vez de dormir en verde (familia 040). La detección real de head-hopping —irreductiblemente semántica— es **track C (move 3)**. Validador de prosa, `triples=()`, ontología congelada intacta.

### DEBT-015 — los validadores que consumen el grafo (`factual_anchor`, `temporal`) emiten locators ausentes/inconsistentes e identificadores opacos
- **Estado:** abierta
- **Detectada en:** dogfood `sombra-en-el-puerto` (2026-06-23), rondas de `factual_anchor` y `temporal`.
- **Ubicación:** `src/bookwright/validation/validators/factual_anchor.py` (mensaje de anchor infrasostenido: identifica el anchor por su URI uuid7 y emite `source=None`) y `src/bookwright/validation/validators/temporal.py` (reglas a/b emiten `source=None`; solo la regla numérica d resuelve `bible/timeline.md` vía `resolve_source`).
- **Clase de deuda:** brecha de **accionabilidad** común a los validadores graph-consumer: leen por SPARQL y no resuelven uniformemente el locator `relpath:línea` ni un identificador legible, a diferencia de los validadores de prosa (`character_presence`, `narrative_structure`, `focalization`), que siempre dan `relpath:línea`.
- **Descripción:** (1) `factual_anchor` reporta `anchor '019ef2c4-bc50-7b81-…' is backed only by sources below the minimum reliability 'media'` con `source: null` — el anchor sale identificado por un UUID opaco y sin fichero, **inaccionable**; mientras tanto `bookwright status` reporta EL MISMO anchor de forma legible (`promotes: paginas-arrancadas, constrains: El cuaderno de bitácora, file: bible/research/puerto.md, problems: [under_reliable]`), prueba de que el dato existe. (2) `temporal` es inconsistente consigo mismo: la regla d adjunta `source: "bible/timeline.md"` pero las reglas a (ciclo) y b (solape+orden) emiten `source: None`, aunque todos los eventos viven en `timeline.md`; la capacidad de resolver el fichero existe (`resolve_source`, que la regla d usa) y solo falta aplicarla uniforme. El grafo lleva la procedencia `file:line` reificada en los `E13`, así que el locator es resoluble.
- **Por qué se difiere:** banco fuera del repo; toca dos validadores y la capa de `queries.py` (`resolve_source`), más una decisión de presentación (¿identificar el anchor por su `constrains`-target y/o el `promotes`-finding, como hace `status`?), mayor que un parche puntual y propia de su iteración.
- **Resolución sugerida / versión objetivo:** **track B (pulido determinista)** — locator/identificador resoluble, nada semántico. (a) `factual_anchor`: identificar el anchor en el mensaje por su target/finding (el handle determinista que el fixture ya documenta) y resolver `bible/research/<tema>.md` como `source`. (b) `temporal`: aplicar `resolve_source` también en las reglas a y b. Idealmente, un helper compartido de "resuelve el locator E13 de este sujeto/triple" para todos los graph-consumers. Severidades y gate sin cambios.

### DEBT-016 — un término de vocabulario Propp/Greimas inválido se ingiere en silencio como nodo sin tipo
- **Estado:** abierta
- **Detectada en:** dogfood `sombra-en-el-puerto` (2026-06-23), ronda de estructura narrativa.
- **Ubicación:** `src/bookwright/io/vocabularies.py` (tipado por etiqueta) + la ingestión de `outline/units/*.md` (`functions:`/`roles:`); ningún canal (`graph build` warnings, validación) reporta un término no reconocido.
- **Clase de deuda:** trato **inconsistente** de vocabularios cerrados: el vocab de research (`type`/`reliability`) RECHAZA lo desconocido con un mensaje enumerado (DEBT-006/036), pero los nombres de función Propp (conjunto cerrado de 31) y de actante Greimas se aceptan en silencio si no casan ningún término.
- **Descripción:** una unidad con `functions: [intimidacion]` (que NO es una de las 31 funciones de Propp) se ingiere como `G10_Narrative_Function` con `rdfs:label "intimidacion"` y **sin** `crm:P2_has_type` (mientras `struggle`, válida, sí recibe `P2_has_type propp#function/struggle`). No hay warning al construir ni hallazgo de validación: un typo o un término inventado entra al grafo como nodo sin tipo, sin feedback. Verificado en `bible/graph.ttl` (nodo `narrative-function/intimidacion` sin `P2_has_type`).
- **Por qué se difiere:** banco fuera del repo; había una **decisión de diseño** detrás (vocabulario cerrado que rechaza vs. abierto que permite funciones propias del autor). **Resuelta en la issue #1 (2026-06-23): híbrido —cerrado para *tipar*, abierto para *autorar*.** El silencio total de hoy es lo único claramente malo; cerrarlo a la fuerza (rechazo fatal) rompería proyectos con etiquetas propias.
- **Resolución sugerida / versión objetivo:** **track B (pulido determinista)**, lista para iteración. `graph build` emite un `warning` **no fatal** cuando un `functions:`/`roles:` con vocab activo no case ningún término, **enumerando los válidos** como el loader de research (DEBT-006/036); el nodo se ingiere igual, sin `crm:P2_has_type`. Principio que lo hace consistente con el rechazo *fatal* de research: **fatal ⇔ el valor inválido rompe lógica downstream** (un `reliability` inválido rompe el gate de `factual_anchor`; un `P2_has_type` ausente es metadato descriptivo y no rompe nada). NO se introduce severidad `info` nueva (superficie injustificada).

### DEBT-017 — `narrative_structure` identifica la unidad de forma inconsistente entre sus dos reglas (nombre vs. slug)
- **Estado:** abierta
- **Detectada en:** dogfood `sombra-en-el-puerto` (2026-06-23), ronda de estructura narrativa.
- **Ubicación:** `src/bookwright/validation/validators/narrative_structure.py` (la regla de rol-sin-resolver imprime el `name` humano de la unidad; la regla de beat-huérfano imprime el `slug`).
- **Clase de deuda:** inconsistencia de presentación dentro de un mismo validador (pulido / UX), sin impacto funcional.
- **Descripción:** sobre la misma clase de entidad (unidad narrativa G9), los dos mensajes usan identificadores distintos: `narrative unit 'La fechoría en el muelle' references role 'informante' …` (nombre humano) vs. `narrative unit 'el-recuerdo-de-la-primera-marea' belongs to no narrative sequence …` (slug). El locator `relpath:línea` es correcto en ambos; lo inconsistente es qué identificador se imprime.
- **Por qué se difiere:** banco fuera del repo; trivial pero ajeno al scope de cualquier iteración en curso, y conviene fijar primero la convención (¿siempre el `name` humano? ¿siempre el slug? ¿ambos?) para aplicarla a todos los validadores a la vez.
- **Resolución sugerida / versión objetivo:** **track B (pulido determinista)** (puede ir junto a DEBT-015, ambos son consistencia de mensajes). Unificar el identificador de unidad (preferiblemente el `name` humano, con el slug entre paréntesis si hace falta) en las dos reglas.

### DEBT-018 — `validate` valida un corpus parcial en silencio cuando un fichero de la bible se omite (asimétrico con `status`)
- **Estado:** abierta
- **Detectada en:** dogfood `sombra-en-el-puerto` (2026-06-23), ronda de edge cases de ingestión.
- **Ubicación:** `src/bookwright/commands/validate/` (no propaga los `skipped` de `map_bible` al envelope ni al canal `not_evaluated[]`), frente a `src/bookwright/commands/status` (que SÍ rechaza con `code=skipped_sources`).
- **Clase de deuda:** **falsa confianza** — la misma clase que el resultado tri-valor de la iteración 040 cerró a nivel de validador, pero aquí a nivel de **fichero de entrada omitido**: `validate` afirma corrección sobre un corpus incompleto sin decirlo.
- **Descripción:** un fichero de personaje con front-matter inservible (YAML roto) se OMITE en `map_bible` (canal `skipped` de `graph build`), de modo que ese personaje desaparece del grafo y de toda validación. `bookwright status` lo trata como bloqueante: devuelve `status=error, code=skipped_sources` («status will not report facts computed from a partial corpus»). Pero `bookwright validate` —el gate de CI— **procede en silencio** sobre el corpus parcial: `status=violations`, `not_evaluated: []`, y NO menciona el skip por ningún lado (ni `rota`, ni `malformed`, ni `partial`). Así, `not_evaluated: []` se lee como «todo evaluado» cuando en realidad un personaje entero quedó fuera del corpus — justo el `[]`-significa-limpio que 040 quería erradicar. Las dos órdenes discrepan sobre si un fichero omitido es reportable. Verificado: `bible/characters/rota.md` (YAML roto) → `status` error, `validate` corre limpio sin mención.
- **Por qué se difiere:** banco fuera del repo; toca cómo `validate` ensambla su `ValidationContext`/envelope para propagar los `skipped` de la ingestión, decisión propia de su iteración (¿un `not_evaluated[]` adicional por fichero omitido?, ¿un canal `skipped[]` espejo del de `graph build`?, ¿error duro como `status`?).
- **Resolución sugerida / versión objetivo:** **track A (honestidad — familia 040)**, la misma clase que 040 cerró a nivel de validador, aquí a nivel de fichero de entrada omitido. Propagar los `skipped` de `map_bible` a `validate`: como mínimo, surfacearlos (un canal `skipped[]` o una entrada en `not_evaluated[]` con el motivo), para que `not_evaluated: []` no mienta. Decidir en `/speckit-plan` si `validate` debe además degradar el verde (alineándose con la negativa de `status`) o solo informar. Cerrarlo cierra la asimetría `status`↔`validate`.

---

## Deuda aceptada (no se arreglará)

_Ninguna por ahora._
