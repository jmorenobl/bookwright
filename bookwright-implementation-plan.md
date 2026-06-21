# Bookwright — Plan de implementación con Spec Kit

> **Documento complementario a:** `bookwright-design.md` (el *cómo* técnico) y
> `bookwright-roadmap.md` (el *qué* y *por qué* a lo largo de versiones).
> **Propósito:** secuencia de iteraciones para el **hito en curso** de Bookwright.
> Cada iteración tiene un prompt listo para invocar `/speckit-specify`.
> **Audiencia:** Jorge (o cualquier desarrollador con Spec Kit instalado y
> `bookwright-design.md` en el root del repo).

> **No hay hito en curso.** v0.4 — la capa estructural narrativa (Propp/Greimas
> G7/G9/G10) e ingesta de `outline/` — **está entregada** (`v0.4.0`, 2026-06-21,
> iteraciones 028–032) y con ella **se cierra la paridad de ingesta**. Las
> iteraciones 1–32 (hitos M0–M5, el tramo de endurecimiento `v0.3.1`…`v0.3.4` y
> v0.4) están **completadas y mergeadas en `main`**; su detalle vive en el
> historial git, en `specs/001-…` … `specs/032-…` y en el `CHANGELOG`. Este
> documento se ha vaciado de ellas a propósito. **Lo que sigue es el horizonte
> demand-pulled, sin versión asignada** (búsqueda vectorial, export, y la
> decisión estructural sobre `NarrativeRole` / G6 / G3): no es material de este
> plan —que es por-hito— sino de `bookwright-roadmap.md` § 4 y de `DEBT.md`. Este
> plan se redacta de nuevo cuando un disparador active el siguiente hito con
> número de versión. El registro de lo hecho es `CLAUDE.md` (tabla de iteraciones)
> y los `specs/` por iteración; la intención de largo plazo es
> `bookwright-roadmap.md`.

---

## 0. Estado y cómo usar este documento

### 0.1 Punto de partida

- `v0.1.0` (M0–M3, iter. 1–11), `v0.2.0` (M4, iter. 12–18), `v0.3.0` (M5,
  iter. 19–23), el tramo de endurecimiento `v0.3.1`…`v0.3.4` (iter. 24–27) y
  `v0.4.0` — la capa estructural narrativa (iter. 28–32) — están en `main`:
  paquete real en `src/bookwright/`, suite de tests, docs y gates verdes.
  `v0.4.0` está tageada (2026-06-21). **El hito v0.4 está cerrado y con él la
  paridad de ingesta.**
- El repo ya está inicializado con Spec Kit (`.specify/`, `.claude/skills/speckit-*`)
  y tiene su constitución ratificada (`.specify/memory/constitution.md`, v1.5.0).
- **No hay que re-bootstrapear ni recrear la constitución.** El siguiente hito,
  cuando lo haya, construirá sobre el código existente y **no reabrirá ningún
  axioma** de `bookwright-design.md` § 16.
- El **registro de diferidos** (`src/bookwright/golem/deferrals.py`, iteración 024)
  y su **test de paridad de ingesta** (`tests/golem/test_ingestion_parity.py`)
  siguen siendo el **contrato**: tras v0.4 declaran solo dos conceptos huérfanos
  —`RelationshipRole` (G6) y `PsychologicalState` (G3)—, ambos re-apuntados al
  **horizonte demand-pulled** (sin versión asignada). `NarrativeUnit` (G9),
  `NarrativeFunction` (G10) y `NarrativeSequence` (G7) salieron del registro en
  v0.4.

### 0.2 Convenciones de iteración (siguen vigentes)

Cada iteración sigue el flujo fijo de Spec Kit, sin saltarse pasos:

```
/speckit-specify <prompt de la iteración>    # crea branch NNN-name + spec.md
/speckit-clarify                              # responde preguntas, refina spec
/speckit-plan <pista técnica>                 # genera plan.md con el cómo
/speckit-tasks                                # desglose en tareas
/speckit-analyze                              # cross-artifact check
/speckit-implement                            # ejecuta tareas
```

- **No saltes `/speckit-clarify`.** Si el prompt no genera dudas, di "no hay
  clarificaciones" para desbloquear.
- **En `/speckit-plan` apóyate en el doc de diseño** y en el código ya existente
  (consulta el índice codegraph antes de grepear).
- **Merge a `main` tras cada iteración** (tests verdes, `/speckit-analyze` sin
  issues). Las iteraciones posteriores asumen el código de las previas en `main`.
- **Cada iteración es autocontenida y deja la herramienta funcionando.** Ningún
  branch puede dejar `bookwright` roto a mitad: lo ya mergeado debe seguir pasando
  todos los gates.
- **Cada iteración entrega un delta observable.** A diferencia del tramo v0.3.x
  (donde cada iteración se liberaba como un patch), v0.4 es un **hito minor**: las
  iteraciones 028–032 se acumulan en `main` y se libera **una sola vez** como
  `v0.4.0` en la iteración de cierre (032), igual que M4→`v0.2.0` y M5→`v0.3.0`.
  Aun así cada iteración mantiene la herramienta funcional y aporta un delta
  observable por sí misma.

### 0.3 Numeración

Los `specs/` van por `001`…`032`. El siguiente hito **arrancará en 033** y
continuará la secuencia. Cada iteración es un branch `NNN-<short-name>` con su
propio `specs/`.

---

## 1. v0.4 entregado — patch de cierre `v0.4.1` en curso (iteración 033)

v0.4 (la capa estructural narrativa: Propp/Greimas G7/G9/G10 + ingesta de
`outline/`) está **entregada y cerrada** (`v0.4.0`, 2026-06-21, iteraciones
028–032), y con ella se cierra la **paridad de ingesta**. El detalle de su plan
—el problema, el principio rector, el mapa de dependencias y los prompts
`/speckit-specify` de las iteraciones 028–032— se ha vaciado a propósito (igual
que se vació el de 001–027): vive en el historial git, en `specs/028-…` …
`specs/032-…`, en el `CHANGELOG` (`[0.4.0]`) y en la tabla de iteraciones de
`CLAUDE.md`.

**Hay un patch estructural en curso: `v0.4.1` (iteración 033, § 2)**, que cierra
DEBT-001 — el concepto muerto `NarrativeRole` que evade el registro de diferidos
por colisión de IRI con su carrier `CharacterRole`. Es un patch de un solo delta
observable (un concepto menos, paridad endurecida), sin ontología nueva y con cero
pérdida de información; encaja en el mismo molde que el track de hardening v0.3.x.

Más allá de ese patch **no hay un siguiente hito mayor con número de versión**. Lo
que queda es el **horizonte demand-pulled** (sin versión asignada), que vive en
`bookwright-roadmap.md` § 4 y en `DEBT.md`, no aquí:

- **Búsqueda vectorial** (ChromaDB sobre rdflib, desacoplada) — activa ante un
  corpus real multi-libro/serie o un fallo medido de structural-recall.
- **Export** (EPUB/PDF/print vía pandoc) — activa cuando el flujo de punta a
  punta esté probado en un libro real; el `1.0` se **gana**, no se pre-asigna.
- **RelationshipRole (G6) + PsychologicalState (G3)** — el subsistema de
  roles/estados tipados con superficie autoral propia (siguen en el registro de
  diferidos).

Cuando un disparador active el siguiente hito mayor, se le asigna número de versión
y **este plan se redacta de nuevo** para él (arrancando en `specs/034-…`),
manteniendo `bookwright-roadmap.md` como la intención durable.

---

## 2. Iteración 033 — eliminar `NarrativeRole` muerto + endurecer paridad (`v0.4.1`)

**Problema.** El concepto GOLEM de nivel superior `NarrativeRole`
(`golem/modules/narrative.py`, registrado en `CONCEPTS`) es **código muerto
inalcanzable por diseño**: ningún builder lo instancia y no existe ruta de autoría
que pueda crearlo. La única encarnación real de `golem:G11_Narrative_Role` es el
nodo inlined `CharacterRole` (`golem/modules/feature.py`, fuera de `CONCEPTS`), que
se materializa desde `narrative_roles:` en `bible/characters/*.md`; los `roles:` de
`outline/units/` resuelven por slug contra ese índice de personajes y **nunca
acuñan** (`outline.py` `_resolve_roles`, design § 7.4). Como ambas clases comparten
`CLASS_IRI["NarrativeRole"]`, el test de paridad ve G11 materializado y por eso
`NarrativeRole` **no** aparece en `DEFERRED_CONCEPTS`: un concepto muerto que se
escapa del contrato de diferimiento por colisión de IRI con un carrier (DEBT-001).

**Decisión (dueño, doble-verificada con agente independiente).** Se **elimina**
`NarrativeRole` de `CONCEPTS` — no se le da superficie de autoría. El diseño define
G11 como "rol **de un personaje**" (design línea 1603) y no concibe roles
independientes de personaje; `CharacterRole` ya cubre el 100 % de lo expresable
sobre roles. **Cero pérdida de información**: el grafo emite exactamente los mismos
triples G11 que antes. Darle superficie propia (`outline/roles/*.md`) queda
**rechazado**: fabricaría una capacidad que el diseño no pide e introduciría una
segunda fuente de verdad para G11.

**Prompt:**

````
/speckit-specify

Necesidad: el concepto GOLEM de nivel superior `NarrativeRole` (golem/modules/narrative.py, registrado en CONCEPTS) es código muerto inalcanzable por diseño: ningún builder lo instancia y no existe ninguna ruta de autoría que pueda crearlo. La única encarnación real de la clase RDF golem:G11_Narrative_Role es el nodo inlined `CharacterRole` (golem/modules/feature.py, fuera de CONCEPTS), que se materializa desde `narrative_roles:` en bible/characters/*.md; los `roles:` de outline/units/ resuelven por slug contra ese índice de personajes y nunca acuñan (outline.py `_resolve_roles`, design § 7.4). Como CharacterRole y NarrativeRole comparten CLASS_IRI["NarrativeRole"], el test de paridad de ingestión ve G11 materializado y por eso NarrativeRole NO aparece en DEFERRED_CONCEPTS: un concepto muerto que se escapa del contrato de diferimiento por colisión de IRI con un carrier (DEBT-001). Queremos eliminar `NarrativeRole` de CONCEPTS y endurecer el contrato de paridad para que un concepto muerto que comparta IRI con un carrier no pueda volver a colarse, SIN perder ninguna información: G11 sigue vivo y materializado vía CharacterRole, el diseño define G11 como "rol de un personaje" (design línea 1603) y no concibe roles independientes de personaje, así que no se recorta ninguna capacidad de crear/auditar/verificar libros.

Comportamiento esperado:

- Se elimina la clase NarrativeRole de golem/modules/narrative.py y sus referencias en golem/__init__.py (import, entrada del dict CONCEPTS, __all__). El recuento de conceptos baja de trece a doce.
- CharacterRole (golem/modules/feature.py) sigue siendo la materialización real de G11 y permanece fuera de CONCEPTS; no se toca salvo para confirmarlo.
- deferrals.py ajusta el conteo "thirteen concepts"→"twelve" y su prosa; DEFERRED_CONCEPTS NO cambia (G6/G3 siguen diferidos).
- El test de paridad de ingestión (tests/golem/test_ingestion_parity.py) se endurece para reconocer explícitamente que G11 se materializa vía el carrier CharacterRole (fuera de CONCEPTS), cerrando por construcción el agujero de DEBT-001; el set de conceptos alcanzables baja en uno y sigue verde.
- Se arreglan los asserts sobre NarrativeRole en tests/golem/test_namespaces.py, test_triples.py y test_uri.py en consecuencia.
- Se borra la entrada DEBT-001 de DEBT.md (git conserva el historial).

Validaciones / no-regresión:

- `uv run pytest` sigue verde: el grafo emite exactamente los mismos triples G11 que antes (la prueba que verifica la materialización de G11 vía CharacterRole sigue pasando).
- Los cuatro gates (ruff check, ruff format --check, mypy --strict, pytest ≥80%) pasan.

Fuera de scope (decisión del dueño, NO reabrir en clarify):

- Darle a NarrativeRole una superficie de autoría propia (outline/roles/*.md): rechazado.
- Tocar los diferidos G6 (RelationshipRole) / G3 (PsychologicalState).
- Cualquier cambio en la ontología congelada: la clase RDF golem:G11_Narrative_Role y golem.ttl NO cambian (Principio X).

Referencia: bookwright-design.md § 7.4 (los roles no acuñan, resuelven contra roles de personaje) y línea 1603 (G11 = rol de un personaje). DEBT-001 en DEBT.md. Principio I (texto plano), Principio X (ontología congelada), Principio IV (≤ 500 líneas).
````

**Pista para `/speckit-plan`:** *"Iteración estructural de limpieza, sin ontología
nueva (Principio X: `golem:G11_Narrative_Role` y `golem.ttl` no cambian). Elimina la
clase `NarrativeRole` de `src/bookwright/golem/modules/narrative.py` y sus
referencias en `src/bookwright/golem/__init__.py` (import, entrada del dict
`CONCEPTS`, `__all__`). `CharacterRole` (`src/bookwright/golem/modules/feature.py`)
ya define `golem_class = CLASS_IRI["NarrativeRole"]` y es la materialización real de
G11 — no la toques salvo para confirmar que sigue fuera de `CONCEPTS`. Actualiza el
conteo `"thirteen concepts"`→`"twelve"` y la prosa de
`src/bookwright/golem/deferrals.py` (`DEFERRED_CONCEPTS` no cambia: G6/G3 siguen).
Endurece `tests/golem/test_ingestion_parity.py`: el set de conceptos alcanzables
baja en uno y el test debe reconocer explícitamente que G11 se materializa vía el
carrier `CharacterRole` (fuera de `CONCEPTS`), de modo que el agujero de DEBT-001
quede cerrado por construcción; arregla en consecuencia los asserts sobre
`NarrativeRole` en `tests/golem/test_namespaces.py`, `test_triples.py` y
`test_uri.py`. Apóyate en design § 7.4 y la línea 1603. Borra la entrada DEBT-001 de
`DEBT.md`. Verifica que `uv run pytest` sigue verde (mismos triples G11) y que los
cuatro gates pasan."*

---

## 4. Notas operativas

### 4.1 Manejo de spec rechazadas

Si tras `/speckit-analyze` aparecen issues de consistencia entre spec/plan/tasks,
vuelve a `/speckit-clarify` o edita `spec.md` directamente, regenera plan y tasks,
y vuelve a analizar. No fuerces `/speckit-implement` con análisis con errores.

### 4.2 Iteraciones que se complican

Si una iteración crece más de lo previsto durante `/speckit-tasks` (más de ~10
tareas), divídela en dos specs. Buenas candidatas a split: las que pueblan un
vocabulario *y* lo cablean a la vez, o un validador con varias reglas
independientes.

### 4.3 Cambios en el documento de diseño

El diseño es la fuente de verdad técnica. Si durante la implementación algo del
diseño no encaja con la realidad técnica, actualiza `bookwright-design.md`
**antes** de divergir el código, y registra el cambio en `CHANGELOG` bajo "Design
decisions revised during implementation". Las decisiones de § 16 son inmutables.

### 4.4 Cuándo pedir ayuda al humano

Spec Kit genera bien spec/plan/tasks pero puede divagar en decisiones de diseño no
triviales (p. ej. la regla de desempate de `order`, la fuente de activación de
vocabularios, o el subconjunto de reglas del validador). Cuando dudes, ejecuta
`/speckit-clarify` o intervén manualmente; redirige al doc de diseño / roadmap.

### 4.5 El siguiente hito

El único trabajo versionado en curso es el patch de cierre `v0.4.1` (iteración 033,
§ 2). El horizonte demand-pulled vive en `bookwright-roadmap.md` § 4 y en `DEBT.md`.
Cuando un disparador active el siguiente hito mayor, asígnale número de versión,
**vacía y redacta de nuevo este plan** para él (arrancando en `specs/034-…`), y
mantén `bookwright-roadmap.md` como la intención durable. Quedan descartados: presets, GrafeoIndexer/Grafeo,
multi-integración y extension system; ver `bookwright-design.md` § 15.5.

---

**Fin del plan.**
