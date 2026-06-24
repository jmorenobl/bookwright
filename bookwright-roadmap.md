# Bookwright — Roadmap

> **Documento durable de intención.** A diferencia del plan de implementación
> (`bookwright-implementation-plan.md`), que se **vacía** de lo entregado en
> cada hito, este roadmap **persiste**: guarda el *qué* y el *por qué* a lo
> largo de las versiones, para no perder el rumbo cuando el plan se reescribe.
>
> **Es una guía, no un compromiso.** El plan real se decide iteración a
> iteración; el owner cambia de opinión cuando la realidad lo aconseja. Este
> documento existe para recordar la intención, no para atarla. Si una decisión
> de aquí se contradice con el plan vigente, manda el plan (y conviene
> actualizar esto).

> **Complementa a:** `bookwright-design.md` (el *cómo* técnico, citado por
> sección) y `bookwright-implementation-plan.md` (el *qué* concreto del hito en
> curso, con prompts `/speckit-specify`). Los tres roles no se solapan:
>
> | Documento | Rol | Vida útil |
> |---|---|---|
> | `bookwright-design.md` | *Cómo* funciona técnicamente (§ citados, axiomas § 16) | Estable, casi congelado |
> | `bookwright-roadmap.md` (este) | *Qué* y *por qué* a lo largo de versiones | Durable — no se vacía |
> | `bookwright-implementation-plan.md` | Iteraciones concretas del hito actual | Efímero — se vacía cada hito |

---

## 1. Dónde estamos

El tramo de endurecimiento **`v0.3.x` está cerrado** (`v0.3.4` tageada
2026-06-15), **v0.4 — la capa estructural narrativa — está entregada**
(iteraciones 028–032; `v0.4.0` al cierre, iteración 032) y el **tramo de
endurecimiento post-dogfooding `v0.4.x`** (iteraciones 033–038, patches
`v0.4.1`…`v0.4.6`) está **cerrado** (`v0.4.6` tageada 2026-06-22). **`v0.5.0` —
validación robusta** (issue #1) **está entregada** (2026-06-22, iteraciones
039+040), y sus dos primeros patches también (`v0.5.1`/`v0.5.2`, iteraciones
041/042). Un **segundo dogfooding** (`sombra-en-el-puerto`, novela negra,
2026-06-23) reencuadró el norte: lo que queda no son tres parches de costura más,
sino **una decisión de fondo** sobre dónde acaba el heurístico determinista (§ 3).
Ese track —honestidad + pulido determinista (`v0.5.3`–`v0.5.8`, iteraciones 043–049)—
**está entregado** (2026-06-24); el **move 3** (juicio semántico) queda como **dirección
activada, diseño-primero** (§ 5), con dos deudas cerrables (DEBT-019/020) antes de él. Lo
entregado hasta hoy:

- **`v0.1.0`** (M0–M3) — el toolkit v0: manifiesto, modelo GOLEM sobre `rdflib`,
  los 10 commands de autoría materializados como Agent Skills, validación.
- **`v0.2.0`** (M4) — investigación y verificación: modelo de procedencia
  (Source/Finding/Anchor), `bookwright-research`, validador `factual_anchor`,
  `bookwright-verify`.
- **`v0.3.0`** (M5) — orquestación: el bloque autoral `[focus]`, el comando
  derivado `bookwright status` con `next_actions` deterministas, y las skills
  consumiéndolo.
- **`v0.3.1`…`v0.3.4`** (endurecimiento v0.3.x) — paridad de ingesta explícita:
  guarda + registro de diferidos (024), localizaciones G13 (025) y objetos G16
  (026) cableadas, y cierre de limpieza con G6/G3 diferidos a posterior (027).
- **`v0.4.0`** (capa estructural narrativa) — **v0.4 entregada**: ingesta de
  `outline/units/` en unidades (G9) y funciones (G10) narrativas (028) y ensamblado
  de secuencias (G7) (029), los vocabularios Propp/Greimas como `E55_Type` con
  tipado vía `[vocabularies] active` (030), el validador `narrative_structure`
  (031), y el cierre E2E + docs + diferidos honestos + release (032). Cierra la
  paridad de ingesta; G6/G3 quedan en el horizonte demand-pulled.
- **`v0.4.1`…`v0.4.6`** (endurecimiento post-dogfooding v0.4.x) — un dogfooding real
  (libro de punta a punta, 2026-06-21) destapó hallazgos accionables, saldados como
  un patch cada uno: parámetro `NarrativeRole` muerto fuera (033, DEBT-001), y el
  tramo de la **issue #1** —`focalization` tolera la declaración de voz prefijada con
  markdown (034, DEBT-004), `rdfs:label` + orden de secuencia consultable (035,
  DEBT-005), mensajes de error de fuentes accionables (036, DEBT-006), `focalization`
  trata el placeholder `[PENDING]` de voz como "sin declaración" (037, DEBT-007) y
  `character_presence` ignora la primera palabra de un encabezado markdown (038,
  DEBT-008). Las cinco son **parches por instancia** de una misma clase de defecto
  (§ 3); cerrarla de raíz fue el cometido de `v0.5.0`.
- **`v0.5.0`** (validación robusta, issue #1) — cierre de la *clase* de raíz: la
  **costura de prosa/estructura única** (`io/prose.py`, 039, cierra el acoplamiento
  de superficie) y el **resultado tri-valor** `evaluado` / `no-evaluado(motivo)`
  (040, cierra la falsa confianza). Minor: 039+040 acumularon en `main` y se
  liberaron una sola vez (estilo M4→`v0.2.0`).
- **`v0.5.1`/`v0.5.2`** (endurecimiento post-`v0.5.0`) — primer dogfood de `v0.5.0`
  (`tiny-historical`): la costura strippea la raya de diálogo `—`/`–`/`―` (041,
  DEBT-009), y la regla de menciones-desconocidas cruza contra la **unión** de
  rosters character/setting/location/object (042, DEBT-010).
- **`v0.5.3`…`v0.5.8`** (track issue #1 tras el 2º dogfood, iteraciones 043–049) —
  **honestidad + pulido determinista, entregado**. *Track A (honestidad):*
  `character_presence` partido en regla de huérfanos + abstainer
  `character_unknown_mentions`, con `not_evaluated` categorizado por `kind`
  (`missing_input`/`pending_capability`) y verde alcanzable de nuevo (043+044→`v0.5.3`);
  head-hopping de `focalization`→`not_evaluated` (045→`v0.5.4`); `validate` propaga los
  `skipped` de ingestión (046→`v0.5.5`). *Track B (pulido determinista):* vocab
  Propp/Greimas no reconocido → `warning` no fatal enumerado (047→`v0.5.6`); locators
  resolubles en los graph-consumers (048→`v0.5.7`); identificador de unidad unificado en
  `narrative_structure` (049→`v0.5.8`). Cerró DEBT-009…018 salvo DEBT-013 (diferida al
  move 3); abrió DEBT-019 (contrato de evaluación parcial) y DEBT-020 (identidad git en
  `init`).

Todo en `main`, con suite de tests, docs y los cuatro gates (`ruff`,
`ruff format`, `mypy --strict`, `pytest` ≥ 80 %) verdes.

---

## 2. La línea de versiones

```
v0.3.x  ──  endurecimiento: cancelar deuda, robustez, cerrar atajos de v0   ✅ cerrado (v0.3.4)
v0.4    ──  capa estructural narrativa (Propp/Greimas: G7/G9/G10)            ✅ entregada (v0.4.0)
            + ingesta de outline/  — cierra la paridad de ingesta
v0.4.x  ──  endurecimiento post-dogfooding (issue #1, instancia a instancia)  ✅ cerrado (v0.4.6)
v0.5.0  ──  validación robusta: cerrar la CLASE del defecto de superficie     ✅ entregada (v0.5.0)
            (costura única + estado tri-valor; verde = evaluado).  issue #1.
v0.5.x  ──  honestidad de validación + pulido determinista (043–049)        ✅ entregado (v0.5.8)
            conjunto ABIERTO declara no-evaluado (familia 040); locators,
            vocab, mensajes.  issue #1, 2º dogfood.  Restan DEBT-019/020.
──── el move 3 ASCIENDE de demand-pulled-sin-disparador a dirección ACTIVADA ────
juicio    ─  escalado semántico (voz/focalización/menciones-desconocidas) vía el  ← AQUÍ
semántico    path LLM de bookwright-verify, con el regex como pre-filtro. Condición  (diseño-1º)
   (norte)   CUMPLIDA por el 2º dogfood (heurístico medido 100% ruido sobre prosa
             real). Es el norte del track de validación; necesita diseño propio
             (determinismo en el gate de CI) antes de spec — no es un sprint ciego.
vectores  ─  ChromaDB sobre rdflib, tras el Indexer Protocol. Activar SI:
             corpus multi-libro/serie, O recall estructural medido como
             insuficiente en una skill concreta. Hasta entonces: no se implementa.
export    ─  EPUB / PDF / print vía pandoc. Activar cuando el flujo completo se
             haya probado en un libro real y el cuello de botella sea sacarlo.
```

**Por qué v0.4 es solo la capa narrativa.** v0.4 completa la **tesis estructural**
del proyecto —los conceptos narrativos modelados-sin-alimentar que quedan
(G7/G9/G10)— y la ingesta de `outline/`. Es determinista, citable por SPARQL,
núcleo. Lo que **no** entra es la búsqueda vectorial: es un subsistema blando
(embeddings, recall sobre prosa) sin un consumidor que hoy sufra por su ausencia,
y mezclarlo con la capa estructural trataría como pares dos cosas de naturaleza
opuesta. Por eso pasa al **horizonte demand-pulled** (§ 5): buena idea sin
disparador presente, con condición de activación explícita en vez de número de
versión. El export sale del mismo molde —su `v1.0` estaba **pre-asignado** sin
haberse ganado; el número 1.0 se gana cuando el flujo de punta a punta esté
probado, no se reparte por adelantado—. Es el mismo espíritu del registro de
diferidos de la iteración 024, llevado del nivel de *concepto de ontología* al de
*subsistema*.

**Por qué un tramo de endurecimiento antes de v0.4.** Antes de añadir
funcionalidad nueva conviene **solidificar la base**: saldar la deuda técnica
acumulada como atajos de v0, hacer explícito lo que hoy está implícito, y
robustecer el sistema actual. Cada versión `v0.3.x` es un **patch**: una
iteración Spec Kit que deja la herramienta funcional y entrega **un delta
observable** (no se libera un patch sin cambio visible; el plumbing interno viaja
dentro del patch que habilita, nunca como release de cero cambios — disciplina de
scope de la constitución).

---

## 3. El norte actual: honestidad de validación + el move 3 activado (issue #1, 2º dogfood)

`v0.5.0` (entregada) cerró las **dos caras** de la clase que el dogfooding de
v0.4.x destapó: la **costura única** (`io/prose.py`, 039) mató el acoplamiento a la
prosa de superficie, y el **resultado tri-valor** (`evaluado` /
`no-evaluado(motivo)`, 040) mató la falsa confianza del `[]`-que-no-distingue
"limpio" de "no pude mirar". El gate sigue clavado solo en `error`; **verde =
`status ok` Y `not_evaluated == []`**. Eso es historia cerrada (detalle en
`CHANGELOG` / `specs/039`,`040`).

Un **segundo dogfooding** —`sombra-en-el-puerto`, novela negra con diálogo denso,
2026-06-23— corrió sobre `v0.5.2` y dio el dato que **reencuadra lo que queda**: la
regla de menciones-desconocidas de `character_presence` (`warning`) produjo **4
falsos positivos, 0 señal real** sobre prosa real. No es un parche más; es la
prueba empírica de que esa regla pide la decisión de fondo de la issue #1.

### El reencuadre: una regla, no "la validación"

`character_presence` mezcla **dos reglas de naturaleza opuesta**, y esa distinción
es la que ordena las 8 deudas del dogfood:

- **Huérfanos** (`error`, el gate). ¿Toda CHARACTER del bible aparece en la prosa?
  Es **conjunto cerrado**: buscas nombres *conocidos*. Determinista, sin NER, sin
  costura — sólido, se queda intacto.
- **Menciones-desconocidas** (`warning`). ¿Todo token capitalizado de la prosa
  tiene entrada en el bible? Es **conjunto abierto**: *descubrir desconocidos*. Eso
  **es** el problema de NER/juicio semántico, y tiene un techo de precisión que
  **ninguna costura ni roster nuevo sube**. Aquí vive TODO lo frágil (`_CANDIDATE`,
  `_is_sentence_initial`, los rosters), y los 4 FP del dogfood.

El error de fondo del estado actual: dos heurísticos deterministas
—menciones-desconocidas y el head-hopping de `focalization`— **fingen** hacer un
trabajo semántico. Echarles más listas cerradas (un 5º roster) o más stripping de
superficie (043/044) es perseguir un conjunto abierto con listas cerradas: no
converge nunca.

### La decisión (issue #1, 2º dogfood)

1. **El heurístico de conjunto abierto deja de fingir.** En vez de inundar ruido
   (menciones-desconocidas: 4/4 FP) o dormir en verde (head-hopping: falso
   negativo, familia 040), **declaran `not_evaluated`** con motivo preciso
   («descubrimiento/juicio de conjunto abierto: requiere juicio semántico, move 3»).
   No es un parche: es la aplicación honesta del canal que 040 ya construyó, y es el
   comportamiento terminal **permanente** (aun con el move 3, si el path LLM está
   offline, `not_evaluated` es el fallback correcto). Mata el ruido y la falsa
   confianza a la vez.
2. **El move 3 se activa** (§ 5). La condición del roadmap (un heurístico concreto
   *medido* como insuficiente sobre prosa real) está **cumplida**: 4/4 FP, no "mejor
   validación" en abstracto. Deja de ser demand-pulled-sin-disparador y pasa a ser
   el **norte del track de validación**. Es la única cura de raíz del conjunto
   abierto: el path LLM distingue «Naviera = organización» / «Las = artículo» /
   «Elena = personaje sin declarar», restaurando la **señal real** (un personaje
   usado pero no declarado) sin el ruido.
3. **DEBT-016 (vocab Propp/Greimas), otra familia, se cierra barata e
   independiente.** Hoy un término no-Propp (`functions: [intimidacion]`) entra **en
   silencio** como nodo sin tipo, mientras el vocab de research (`type`/`reliability`)
   rechaza enumerando (DEBT-006). El silencio es lo único claramente malo. Resolución:
   **cerrado para *tipar*, abierto para *autorar*** — un `warning` **no fatal** en
   `graph build` que enumere los términos válidos (simetría con DEBT-006, atrapa el
   typo), pero el nodo se ingiere sin tipo (no prohíbe etiquetas propias, no aborta).
   El principio que lo hace consistente con el rechazo fatal de DEBT-006: **fatal ⇔
   un valor inválido rompe lógica downstream** (un `reliability` inválido rompería el
   gate de `factual_anchor`; un `P2_has_type` ausente es metadato descriptivo y no
   rompe nada).

### Reparto de las 8 deudas del 2º dogfood

| Track | Deudas | Naturaleza |
|---|---|---|
| **A — honestidad** (consecuencia de 040) | menciones-desconocidas→`not_evaluated` (subsume DEBT-011/012, y el *síntoma* de 013), head-hopping→`not_evaluated` (DEBT-014), `validate` propaga `skipped` (DEBT-018) | cerrar la mentira `[]`/dormido |
| **B — pulido determinista** | locators de graph-consumers (DEBT-015, cerrada iter 048), vocab build-warning (DEBT-016, cerrada iter 047), mensaje nombre-vs-slug (DEBT-017, cerrada iter 049) | cerrado/estructural, real, barato |
| **C — move 3** (norte activado, § 5) | conjunto abierto entero: DEBT-013 (orgs), techo de DEBT-014 | juicio semántico, diseño propio |
| **Descartado** | 043/044 como parches de costura; 5º roster «organización» | parchear conjunto abierto con listas cerradas |

**Por qué se descartan 043/044 (los parches de comilla-líder y cuerpo-de-título).**
Ambos solo des-ruidan la regla de menciones-desconocidas — verificado: tocan solo
`_is_sentence_initial`, que solo alimenta esa regla. Si la regla pasa a
`not_evaluated` por defecto, pulir sus FP de superficie es trabajo muerto. La
costura `io/prose.py` se queda (es buena arquitectura para los validadores
deterministas); solo dejamos de alimentar con ella el heurístico abierto. DEBT-011/012
quedan **subsumidas**, no resueltas por instancia.

**Alineado con los principios.** Honestidad (track A) y pulido determinista (track
B) son shippables ya, deterministas y de raíz; no tocan la ontología congelada
(validadores de prosa, `triples=()`, Principio X). El move 3 (track C) es el norte,
pero **necesita diseño propio antes de spec** — tiene una tensión real: todo el
proyecto es disciplina de test determinista y un LLM en el gate de CI es
no-determinista (§ 5, design § 20.6). No es un sprint ciego.

---

## 4. El norte de v0.3.x→v0.4: paridad de ingesta (histórico — cerrado)

> Cerrado con `v0.4.0`. Se conserva como registro de la intención que guió
> `v0.3.x`/`v0.4`; ya no es el norte vigente (ese es § 3).

La deuda dominante descubierta en revisión: **la ontología congelada modela 13
conceptos narrativos, pero solo ~6 son alcanzables desde texto autoral.** El
resto está modelado, registrado en `CONCEPTS`, cubierto por el test de clausura
(SC-003)… y **muerto de cara al autor** porque ningún builder lo alimenta. El
*soft-miss* de investigación a localizaciones fue el primer síntoma visible.

Estado por concepto (clase GOLEM → ¿llega desde texto autoral?):

| Concepto | Clase | ¿Vivo? | Cómo entra (o por qué no) |
|---|---|---|---|
| Character | G1 | ✅ | `bible/characters/*.md` |
| Setting | G12 | ✅ | `bible/settings/*.md` |
| NarrativeEvent | G5 | ✅ | `bible/timeline.md` |
| SocialRelationship | G4 | ✅ | `bible/relationships.md` |
| NarrativeRole | G11 | ✅ | inline vía `narrative_roles:` de personaje |
| CharacterFeature | G17 | ✅ | inline vía `features:`/`born`/`died` |
| **NarrativeLocation** | **G13** | ❌ | `bible/locations/` existe en scaffold y la skill lo escribe, pero **nada lo ingiere** |
| **Object** | **G16** | ❌ | sin builder, sin `bible/objects/`, sin skill |
| **PsychologicalState** | **G3** | ❌ | sin builder |
| **RelationshipRole** | **G6** | ❌ | las relaciones son identidad + participantes, sin roles tipados |
| **NarrativeUnit** | **G9** | ❌ | capa estructural narrativa, sin ingesta |
| **NarrativeFunction** | **G10** | ❌ | capa estructural narrativa, sin ingesta |
| **NarrativeSequence** | **G7** | ❌ | capa estructural narrativa, sin ingesta |

**Siete conceptos huérfanos.** El objetivo de v0.3.x no es necesariamente
cablearlos todos, sino **eliminar el silencio entre "modelado" y "alimentado"**:
para cada clase del cierre, o hay un camino desde texto autoral, o hay una **nota
de diferimiento explícita** (con razón y versión objetivo), respaldada por un test
que asevera *"el conjunto de clases huérfanas es exactamente el conjunto
intencionadamente diferido"*. Así la deuda deja de pudrirse en silencio: cada vez
que un patch cablea una clase, esta **sale** del set diferido y el test obliga a
actualizar el contrato.

Reparto previsto (puede cambiar):

- **Baratas (espejo de `settings/`, identity-only)** → se cablean en v0.3.x:
  NarrativeLocation (G13), Object (G16).
- **Medias** → decidir en v0.3.x (cablear o diferir formal): RelationshipRole
  (G6), PsychologicalState (G3).
- **Capa estructural narrativa (Propp/Greimas)** → **v0.4**: NarrativeUnit (G9),
  NarrativeFunction (G10), NarrativeSequence (G7). Es un subsistema con modelo e
  ingesta de `outline/` nuevos, no un fix; no cabe en un patch.

Deuda menor que acompaña al tramo: unificar el sobre JSON de éxito
(`ok_payload`, hoy con dicts a mano en `check`/`focus`/`graph`) y hacer
**explícito por escrito** que `outline/` y `manuscript/` son author-only en v0.3
(el scaffold los crea pero el motor no los ingiere — decisión legítima de v0, hoy
no documentada como tal).

---

## 5. Más allá: el horizonte demand-pulled

**Horizonte sin versión asignada (demand-pulled).** Buenas ideas sin disparador
presente. No se cancelan, pero **no se implementan hasta que su condición se
cumpla** — y entonces se les asigna número de versión. Es el patrón del registro
de diferidos (iteración 024) a escala de subsistema:

- **Juicio semántico en validación** (movimiento 3 de la issue #1) — **CONDICIÓN
  CUMPLIDA, dirección ACTIVADA** (ya no es demand-pulled-sin-disparador). Escalar a
  juicio literario los validadores que lo exigen —menciones-desconocidas (orgs,
  topónimos, vocativos, personajes sin declarar), voz/focalización, continuidad
  temporal— reusando el path LLM existente (`bookwright-verify`, iteración 015), con
  el heurístico regex como **pre-filtro barato** que acota candidatos, no como
  veredicto final. Algunos juicios (¿esta prosa rompe de verdad la focalización
  limitada? ¿«Naviera» es organización o personaje sin declarar?) son
  irreductiblemente semánticos: ninguna costura ni roster nuevo los resuelve.
  **Condición de activación — cumplida (2026-06-23):** el 2º dogfood
  (`sombra-en-el-puerto`) midió la regla de menciones-desconocidas como **100%
  ruido** sobre prosa real (4 FP, 0 señal); ese es el disparador concreto que el
  roadmap exigía, no "mejor validación" en abstracto. **La pasada de diseño ya está
  hecha** (2026-06-24): los cuatro principios que fijan la frontera determinismo/LLM
  viven en `bookwright-design.md` § 20.6.1 — (1) la frontera es el *sustrato* (grafo
  determinista vs. prosa LLM), no la dificultad; (2) LLM-primero **anclado en el
  grafo** (grounding, donde enchufa la búsqueda vectorial de abajo); (3) el
  determinismo añade confianza o ahorra coste pero **nunca suprime** un candidato; (4)
  separar *juicio* (LLM, informativo, no rompe CI) de *gate* (determinista o veredictos
  LLM cacheados). Lo que falta es la spec que los aterrice. El interim honesto ya está:
  el heurístico declara `not_evaluated` (track A, § 3), no finge; el move 3 restaura la
  señal que ese `not_evaluated` deja pendiente. **Corroborado por el 3er dogfood
  (`el-año-de-las-casas-vacías`, novela literaria multi-POV, 2026-06-24):** sobre prosa
  fresca de un género distinto (3ª limitada multi-voz), la abstención honesta del track A
  funciona sin ruido, pero el hueco semántico **muerde con señal real perdida, no
  teórica** — un personaje usado-pero-no-declarado (`Amelia`, 4 menciones, sin ficha) y un
  head-hopping real (interioridad de Irene en el capítulo focalizado en Teo) quedan
  **invisibles**, abstenidos en el mismo gesto que (correctamente) silencia orgs y
  topónimos. Es decir: la única respuesta determinista honesta (abstener) no puede separar
  ruido de señal; sólo el juicio semántico lo hace. El 3er dogfood **confirma el move 3
  como la próxima roca** sobre onboarding (que no aportó muro nuevo: el flujo
  `init→autoría→graph→validate→status` fue sin fricción; la fricción documentada es la
  cadena externa, condición de activación aún no disparada).
- **Búsqueda vectorial.** ChromaDB (o equivalente) **sobre `rdflib`**, desacoplada
  del grafo, detrás del `Indexer` Protocol. Sin Grafeo (cancelado). Su valor real
  es la capa RAG (lo que las skills recuperan como contexto) y la detección
  *sugerida* de incoherencias de prosa que SPARQL no ve por estructurales — no
  "mejor búsqueda" en abstracto. **Condición de activación:** existe un corpus real
  multi-libro/serie, **o** se mide que la recuperación estructural falla en recall
  en una skill concreta. Hasta entonces no hay consumidor que sufra su ausencia, y
  añadirla sería plumbing especulativo (disciplina de scope, § 6).
- **Export.** EPUB / PDF / print vía `pandoc`. El texto plano canónico ya es la
  fuente; el export es una proyección más, como el grafo. **Condición de
  activación:** el flujo de punta a punta se ha probado en un libro real y el
  cuello de botella pasa a ser sacarlo. El número `1.0` se **gana** cuando ese
  flujo completo está probado; no se pre-asigna al export por adelantado.
- **Onboarding de un comando para autores no-técnicos.** Bootstrap idempotente
  ejecutable desde URL (patrón Astral: `irm https://…/install.ps1 | iex` /
  `curl … | sh`), un script por SO (`.ps1` Windows, `.sh` Mac/Linux), que
  **detecta y solo instala lo que falte**: `uv` (que a su vez trae Python), la
  CLI (`uv tool install`/`upgrade bookwright-cli`), el agente de IA (Claude Code
  ya tiene instalador nativo sin Node/npm; Codex tiene binario sin Node — la vía
  npm es evitable) y `git` (vía `winget` en Windows con fallback a git-scm.com).
  Principio: el script **orquesta** instaladores oficiales auto-actualizables,
  **no empaqueta ni fija versiones** propias (menos mantenimiento, update gratis).
  **Reparto deliberado con git:** el bootstrap solo instala herramientas (no
  interactivo — `irm | iex` ocupa el stdin, los prompts se rompen) y **no toca la
  identidad de git**; configurar `user.name`/`user.email` (local del repo, nunca
  global a ciegas) y el primer commit son responsabilidad de `bookwright init` /
  un futuro `bookwright doctor`, donde la interactividad sí funciona (ver DEBT —
  identidad git en `init`). **Condición de activación:** un segundo autor
  no-técnico real lo necesita (caso fundacional 2026-06-23: amigo psicólogo en
  Windows tuvo que instalar Python+Node+npm+permisos+Codex+git a mano — "ni de
  broma lo habría hecho solo"). Lo barato y sin código (una página
  «Instalación» en `docs/` con los 3 one-liners modernos) se puede adelantar; el
  script y el `doctor` son la forma plena. Descartado por ahora: binario único
  PyInstaller (pesado, sin cross-compile, y no resuelve agente ni git) y GUI/app
  de escritorio (es otro producto).

> **Resuelto (iteración 033).** La «decisión estructural sobre `NarrativeRole`
> (DEBT-001)» ya está tomada: el concepto de nivel superior `NarrativeRole` se
> **eliminó** de `CONCEPTS` —`CharacterRole` es la única encarnación de
> `G11_Narrative_Role` que se quiere— y el contrato de paridad de ingesta se
> endureció para nombrar como fallo cualquier concepto cuya IRI la mate solo un
> carrier fuera de `CONCEPTS`. La clase RDF `G11_Narrative_Role` sigue congelada.

---

## 6. Principios de qué entra y qué sale

- **Texto plano fuente de verdad** (Principio I). Todo lo derivado —grafo,
  `status.json`, futuros índices vectoriales, export— es caché reconstruible,
  nunca fuente.
- **Ontología congelada** (Constitución X). El cierre de 17 clases (`CLASS_IRI`)
  y `golem.ttl` no ganan clases. Cablear un concepto huérfano **no** toca la
  ontología: la clase ya existe; falta el builder. Vocabulario nuevo va en
  `.ttl` separados.
- **Agent Skills, nunca legacy commands** (Principio VI). Multi-integración
  limitada a `claude` y `generic`.
- **Disciplina de scope.** No se implementa plumbing cuya única justificación sea
  "future X". Un patch = un delta observable.

### Cancelados (decisión de owner — no se implementarán)

Presets / paquetes de género (la resolución de templates es 2 capas:
overrides → core) · `GrafeoIndexer` / motor Grafeo · multi-integración más allá
de `claude` / `generic` · sistema de extensiones. Ver `bookwright-design.md`
§ 15.5 y § 20.12.

---

## 7. Cómo evoluciona este documento

Cuando un hito se cierra y libera, el **plan** se vacía de lo entregado y se
rellena con el siguiente tramo; este **roadmap** se actualiza solo en su tabla de
estado (§ 1) y, si la intención de largo plazo cambió, en las secciones que
toque. El **design** se actualiza *antes* de divergir el código, nunca después.
```
