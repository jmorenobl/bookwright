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
`v0.4.1`…`v0.4.6`) está **cerrado** (`v0.4.6` tageada 2026-06-22). El siguiente
hito es **`v0.5.0` — validación robusta** (§ 3), que cierra la *clase* de defecto
de superficie de los validadores (issue #1); tras él, el horizonte
**demand-pulled** sin versión asignada (§ 5). Lo entregado hasta hoy:

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
  (§ 3); cerrarla de raíz es el cometido de `v0.5.0`.

Todo en `main`, con suite de tests, docs y los cuatro gates (`ruff`,
`ruff format`, `mypy --strict`, `pytest` ≥ 80 %) verdes.

---

## 2. La línea de versiones

```
v0.3.x  ──  endurecimiento: cancelar deuda, robustez, cerrar atajos de v0   ✅ cerrado (v0.3.4)
v0.4    ──  capa estructural narrativa (Propp/Greimas: G7/G9/G10)            ✅ entregada (v0.4.0)
            + ingesta de outline/  — cierra la paridad de ingesta
v0.4.x  ──  endurecimiento post-dogfooding (issue #1, instancia a instancia)  ✅ cerrado (v0.4.6)
v0.5.0  ──  validación robusta: cerrar la CLASE del defecto de superficie     ← AQUÍ
            (costura única + estado tri-valor; verde = evaluado).  issue #1.
──── horizonte sin versión asignada (demand-pulled, con condición de activación) ────
juicio    ─  escalado semántico (voz/focalización/temporal) vía el path LLM de
semántico    bookwright-verify, con el regex como pre-filtro. Activar cuando un
             validador concreto pida juicio literario que el heurístico no da.
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

## 3. El norte actual: `v0.5.0` — validación robusta (issue #1)

El dogfooding de v0.4.x destapó **una clase de defecto, no tres bugs**. Cinco
parches (`v0.4.2`…`v0.4.6`) saldaron instancias sueltas de un mismo patrón
recurrente; la **issue #1** lo nombró y decidió **cerrar la clase de raíz** en vez
de seguir jugando al whack-a-mole. `v0.5.0` es ese cierre. Es un **minor** (no un
patch v0.4.x): introduce arquitectura nueva —una costura compartida y un contrato
de resultado tri-valor—, así que las iteraciones **acumulan en `main`** y se
liberan **una sola vez** al cierre, al estilo de M4→`v0.2.0` (plan § 0.3).

La clase tiene **dos caras**:

- **A — acoplamiento a la prosa de superficie.** Cada validador que escanea
  manuscrito/constitución reimplementa por su cuenta "cómo ver más allá del
  markdown que la propia herramienta emite": `character_presence` strippea el
  encabezado ATX (`# `, DEBT-008), `focalization` strippea viñeta + énfasis +
  placeholder (`- **Voz narrativa**`, `[PENDING: …]`, DEBT-004/007), y
  `setting_continuity` re-escanea `splitlines()` crudo. Cada formato markdown nuevo
  (un epígrafe, un `> blockquote`) vuelve a abrir la grieta en el siguiente
  validador. Un topo por iteración.
- **B — falsa confianza.** `validate()` devuelve `list[Violation]`, y `[]` es
  **indistinguible** entre "evaluado y limpio" y "no pude mirar". DEBT-004 fue,
  literalmente, un validador **dormido y verde**. Para una herramienta de autoría el
  peor fallo no es el falso positivo (ruido), es la **falsa confianza**.

**Lo que entrega `v0.5.0`** (dos iteraciones, cierran A y B; movimientos 1 y 2 de
la issue):

- **Costura de prosa/estructura única** (iter 039, cierra A). Una sola capa
  markdown-aware en `io/` —vecina de `frontmatter.py`, que ya lleva tracking de
  líneas— que **todos** los validadores de prosa consumen: clasifica cada línea
  (encabezado / viñeta / blockquote / énfasis / placeholder `[PENDING]` / prosa) y
  expone la vista normalizada **una vez**, con los números de línea preservados
  (el locator `relpath:línea` no cambia). Los tres validadores se reescriben sobre
  ella y sus strippers locales (`_HEADING_MARKER`, `_BULLET`, `_LEAD_EMPHASIS`,
  `_CLOSE_EMPHASIS`, `_PENDING_ONLY`, `_normalize_declaration_line`) **se borran**.
  Cero regresión en los fixtures vivos; un fixture nuevo de la *siguiente* superficie
  (`> blockquote`/epígrafe) prueba que la costura generaliza sin tocar validador.
  **Sin dependencia nueva** (Constitución II): es un clasificador determinista de
  bloques sobre las primitivas regex existentes, **no** un AST de markdown.
- **Resultado tri-valor** (iter 040, cierra B). El contrato del validador pasa de
  "lista de hallazgos" a **`evaluado` / `con-hallazgos` / `no-evaluado(motivo)`**.
  Los retornos-tempranos-`[]` de hoy (focalización sin declaración parseable o con
  voz aún en `[PENDING]`; manuscrito vacío) se vuelven `no-evaluado` con motivo. El
  runner, el report, el sobre `--json`, `bookwright status` y las skills exponen el
  tercer estado, de modo que **verde = evaluado**. El gate (solo `error` rompe CI) y
  la forma de `Violation` no cambian; el estado es **aditivo**. La detección de
  placeholder de la costura (iter 039) alimenta aquí el motivo "declaración sin
  responder", uniendo ambas caras.

**Alineado con los principios.** Es Principio I llevado a la validación: los
validadores dejan de acoplar a la **prosa de superficie** y consumen la
**estructura ya clasificada**. No toca la ontología congelada (validadores de
prosa, `triples=()`, Principio X). La decisión § 13.1 del diseño (el Protocol
`validate`) se actualiza **antes** de divergir el código (plan § 7.3).

**Lo que NO entra** (movimiento 3 de la issue, → horizonte demand-pulled, § 5): el
**escalado a juicio semántico** de los validadores que lo exigen (voz,
focalización, continuidad temporal) reusando el path LLM de `bookwright-verify`
(iter 015), con el regex como **pre-filtro barato**, no como veredicto. La propia
issue lo deja como **dirección roadmap-level**, no como patch: se activa cuando un
validador concreto pida juicio literario que el heurístico determinista no da, no
antes (sería plumbing especulativo).

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

- **Juicio semántico en validación** (movimiento 3 de la issue #1). Escalar a juicio
  literario los validadores que lo exigen —voz, focalización, continuidad
  temporal— reusando el path LLM existente (`bookwright-verify`, iteración 015), con
  el heurístico regex como **pre-filtro barato** que acota candidatos, no como
  veredicto final. `v0.5.0` cierra el acoplamiento de superficie y la falsa confianza
  (§ 3), pero **no** convierte el heurístico en juicio; algunos juicios (¿esta prosa
  rompe de verdad la focalización limitada?) son irreductiblemente semánticos.
  **Condición de activación:** un validador concreto cuyo heurístico determinista se
  mida como insuficiente (demasiados falsos positivos/negativos sobre prosa real), no
  "mejor validación" en abstracto. Hasta entonces, plumbing especulativo
  (disciplina de scope, § 6).
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
