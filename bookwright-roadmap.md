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

`v0.3.0` está **entregada y tageada** (2026-06-13): el hito M5 — orquestación de
contexto (el "hilo conductor"), design § 21. Con ella, lo entregado hasta hoy:

- **`v0.1.0`** (M0–M3) — el toolkit v0: manifiesto, modelo GOLEM sobre `rdflib`,
  los 10 commands de autoría materializados como Agent Skills, validación.
- **`v0.2.0`** (M4) — investigación y verificación: modelo de procedencia
  (Source/Finding/Anchor), `bookwright-research`, validador `factual_anchor`,
  `bookwright-verify`.
- **`v0.3.0`** (M5) — orquestación: el bloque autoral `[focus]`, el comando
  derivado `bookwright status` con `next_actions` deterministas, y las skills
  consumiéndolo.

Todo en `main`, con suite de tests, docs y los cuatro gates (`ruff`,
`ruff format`, `mypy --strict`, `pytest` ≥ 80 %) verdes.

---

## 2. La línea de versiones

```
v0.3.x  ──  endurecimiento: cancelar deuda, robustez, cerrar atajos de v0   ← AQUÍ
v0.4    ──  capa estructural narrativa (Propp/Greimas: G7/G9/G10)
            + ingesta de outline/  — cierra la paridad de ingesta
──── horizonte sin versión asignada (demand-pulled, con condición de activación) ────
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
opuesta. Por eso pasa al **horizonte demand-pulled** (§ 4): buena idea sin
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

## 3. El norte de v0.3.x: paridad de ingesta

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

## 4. Más allá: v0.4 y el horizonte demand-pulled

**v0.4 — capa estructural narrativa.** El último gran trozo de "paridad de
ingesta": cablear los conceptos Propp/Greimas modelados-sin-alimentar
(NarrativeUnit G9, NarrativeFunction G10, NarrativeSequence G7) con su modelo e
ingesta de `outline/` nuevos. Es un subsistema, no un fix: no cabe en un patch
v0.3.x. Determinista y citable por SPARQL, encaja como núcleo del proyecto.

**Horizonte sin versión asignada (demand-pulled).** Buenas ideas sin disparador
presente. No se cancelan, pero **no se implementan hasta que su condición se
cumpla** — y entonces se les asigna número de versión. Es el patrón del registro
de diferidos (iteración 024) a escala de subsistema:

- **Búsqueda vectorial.** ChromaDB (o equivalente) **sobre `rdflib`**, desacoplada
  del grafo, detrás del `Indexer` Protocol. Sin Grafeo (cancelado). Su valor real
  es la capa RAG (lo que las skills recuperan como contexto) y la detección
  *sugerida* de incoherencias de prosa que SPARQL no ve por estructurales — no
  "mejor búsqueda" en abstracto. **Condición de activación:** existe un corpus real
  multi-libro/serie, **o** se mide que la recuperación estructural falla en recall
  en una skill concreta. Hasta entonces no hay consumidor que sufra su ausencia, y
  añadirla sería plumbing especulativo (disciplina de scope, § 5).
- **Export.** EPUB / PDF / print vía `pandoc`. El texto plano canónico ya es la
  fuente; el export es una proyección más, como el grafo. **Condición de
  activación:** el flujo de punta a punta se ha probado en un libro real y el
  cuello de botella pasa a ser sacarlo. El número `1.0` se **gana** cuando ese
  flujo completo está probado; no se pre-asigna al export por adelantado.

---

## 5. Principios de qué entra y qué sale

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

## 6. Cómo evoluciona este documento

Cuando un hito se cierra y libera, el **plan** se vacía de lo entregado y se
rellena con el siguiente tramo; este **roadmap** se actualiza solo en su tabla de
estado (§ 1) y, si la intención de largo plazo cambió, en las secciones que
toque. El **design** se actualiza *antes* de divergir el código, nunca después.
```
