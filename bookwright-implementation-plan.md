# Bookwright — Plan de implementación con Spec Kit

> **Documento complementario a:** `bookwright-design.md` (el *cómo* técnico) y
> `bookwright-roadmap.md` (el *qué* y *por qué* a lo largo de versiones).
> **Propósito:** secuencia de iteraciones para el **hito en curso** de Bookwright,
> **v0.4 — la capa estructural narrativa** (Propp/Greimas: G9/G10/G7) y la
> **ingesta de `outline/`**, que cierran la paridad de ingesta. Cada iteración
> tiene un prompt listo para invocar `/speckit-specify`.
> **Audiencia:** Jorge (o cualquier desarrollador con Spec Kit instalado y
> `bookwright-design.md` en el root del repo).

> **Nota sobre versiones anteriores de este plan:** las iteraciones 1–27
> (hitos M0–M5, releases `v0.1.0`, `v0.2.0`, `v0.3.0` y el tramo de
> endurecimiento `v0.3.1`…`v0.3.4`) ya están **completadas y mergeadas en
> `main`**. Su detalle vive ahora en el historial git, en `specs/001-…` …
> `specs/027-…` y en el `CHANGELOG`. Este documento se ha vaciado de ellas a
> propósito: solo describe el trabajo **por hacer** (v0.4). El registro de lo
> hecho es `CLAUDE.md` (tabla de iteraciones) y los `specs/` por iteración; la
> intención de largo plazo es `bookwright-roadmap.md`.

---

## 0. Estado y cómo usar este documento

### 0.1 Punto de partida

- `v0.1.0` (M0–M3, iter. 1–11), `v0.2.0` (M4, iter. 12–18), `v0.3.0` (M5,
  iter. 19–23) y el tramo de endurecimiento `v0.3.1`…`v0.3.4` (iter. 24–27)
  están en `main`: paquete real en `src/bookwright/`, suite de tests, docs y
  gates verdes. `v0.3.4` está tageada (2026-06-15). **El tramo v0.3.x está
  cerrado.**
- El repo ya está inicializado con Spec Kit (`.specify/`, `.claude/skills/speckit-*`)
  y tiene su constitución ratificada (`.specify/memory/constitution.md`, v1.4.0).
- **No hay que re-bootstrapear ni recrear la constitución.** Este hito construye
  sobre el código existente y **no reabre ningún axioma** de `bookwright-design.md`
  § 16.
- El **registro de diferidos** (`src/bookwright/golem/deferrals.py`, iteración 024)
  y su **test de paridad de ingesta** (`tests/golem/test_ingestion_parity.py`) ya
  existen y son el **contrato** de este hito: hoy declaran cinco conceptos
  huérfanos — `NarrativeUnit` (G9), `NarrativeFunction` (G10), `NarrativeSequence`
  (G7), `RelationshipRole` (G6) y `PsychologicalState` (G3). v0.4 saca los **tres
  primeros** del registro; G6/G3 siguen diferidos.

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

Los `specs/` van por `001`…`027`. Este hito **arranca en 028** y continúa la
secuencia. Cada iteración es un branch `NNN-<short-name>` con su propio `specs/`.

---

## 1. El hito: v0.4 — capa estructural narrativa

### 1.1 El problema

La paridad de ingesta del tramo v0.3.x cerró los conceptos "baratos" (G13
localizaciones, G16 objetos) y dejó por escrito el contrato de diferimiento. Lo
que queda para **cerrar la paridad de ingesta del todo** es el último gran trozo:
la **capa estructural narrativa** de GOLEM, modelada pero sin alimentar.

Tres clases del cierre congelado siguen muertas de cara al autor:

| Concepto | Clase | Modelo (ya existe) | Por qué está huérfana |
|---|---|---|---|
| **NarrativeUnit** | G9 | `golem/modules/narrative.py` (cross-refs a functions y roles vía `crm:P67_refers_to`) | ningún builder; `outline/` no se ingiere |
| **NarrativeFunction** | G10 | `golem/modules/narrative.py` (identity-only) | ningún builder |
| **NarrativeSequence** | G7 | `golem/modules/narrative.py` (`dlp:proper-part` ordenado por unidad) | ningún builder |

Los modelos Pydantic, sus URIs (`narrative-unit`, `narrative-function`,
`narrative-sequence`, design § 4.5) y sus cross-refs **ya están en el código**;
falta el **camino desde texto autoral**. El `NarrativeRole` (G11) hermano **sí**
está vivo (se materializa inline desde `narrative_roles:` de personaje), así que
las unidades lo referencian por nombre, igual que una localización referencia su
setting.

A esto se suma la deuda de fondo: `outline/` existe en el scaffold (`arcs.md`,
`structure.md`, `synopsis.md`, `scenes.md`), la skill `bookwright-outline` lo
escribe, **pero el motor no ingiere nada de él** (declarado author-only en la
iteración 024). v0.4 abre la primera vía de ingesta de `outline/`.

### 1.2 El principio rector del hito

> **La capa estructural narrativa entra al grafo de forma determinista, citable
> por SPARQL, desde una superficie autoral estructurada — sin LLM en el
> indexador (Principio I) y sin tocar la ontología congelada (Principio X).**

Decisiones de diseño tomadas para este hito (owner, antes de specificar):

- **Superficie autoral: `outline/units/*.md`, una entidad por fichero**, espejo
  exacto del patrón ya probado en `bible/settings/`, `bible/locations/` (iter. 025)
  y `bible/objects/` (iter. 026). Reutiliza `io/_bible_builders.py`, la maquinaria
  `_DirSpec` y el guard de paridad. Es el camino de menor riesgo y máxima
  consistencia. El frontmatter de una unidad lleva `name` (obligatorio),
  `functions` (lista opcional), `roles` (lista opcional) y, para secuencias,
  `sequence` + `order`. El cuerpo en prosa (la descripción del *beat*) queda para
  el humano. `arcs.md`/`structure.md`/`synopsis.md` siguen siendo prosa
  author-only; **solo `outline/units/` se ingiere**.
- **Funciones (G10) inline desde la unidad**, igual que `narrative_roles:` de
  personaje materializa `NarrativeRole`: cada nombre en `functions:` materializa
  un `NarrativeFunction` identity-only (dedupe por slug entre unidades) y el
  cross-ref `unit → function` (`crm:P67_refers_to`, ya en el modelo).
- **Roles (G11) por resolución de nombre** contra el índice de roles existente
  (los creados inline por personajes); si un nombre no resuelve es un *soft-miss*
  coherente con el contrato del mapper (`UnresolvedReference`, iter. 027), nunca
  un crash.
- **Secuencias (G7) unit-driven**: una unidad declara su `sequence:` y su
  `order:`; cada secuencia se ensambla a partir de las unidades que la referencian,
  ordenadas por `order:`, emitiendo `dlp:proper-part` por miembro en orden (ya en
  el modelo). (Alternativa considerada y descartada por más verbosa: un directorio
  `outline/sequences/` que liste miembros.)

Esto respeta las restricciones duras: cablear estos conceptos **no toca la
ontología** (las clases ya existen en `CLASS_IRI`; faltan los builders —
Constitución X a salvo), Principio I (texto plano fuente de verdad), Principio IX
(`--json`), Principio IV (≤ 500 líneas, un subcomando por módulo), Principio VIII
(cobertura ≥ 80 %).

### 1.3 Qué NO entra en v0.4

- **RelationshipRole (G6) y PsychologicalState (G3)** siguen diferidos. El
  registro (`deferrals.py`) los marca "requieren un modelo tipado de roles/estados
  con atributos y una superficie autoral" — un subsistema distinto de la capa
  estructural narrativa, no un fix que quepa aquí. v0.4 los deja en el registro;
  la iteración de cierre (032) **re-apunta su `target_version` de `"v0.4"` a un
  hito posterior** para que el contrato no afirme que se entregan en este hito.
- **Búsqueda vectorial y export** quedan en el **horizonte demand-pulled** (sin
  versión asignada, se activan por condición concreta — `bookwright-roadmap.md`
  § 4). No se implementa plumbing especulativo para ellos.
- Siguen descartados (decisión de owner): presets, GrafeoIndexer/Grafeo,
  multi-integración más allá de `claude`/`generic`, extension system. Ver
  `bookwright-roadmap.md` § 5.

### 1.4 El doc de diseño

El diseño canónico de los conceptos vive en `bookwright-design.md` § 4.2
(módulo Narrative y sus clases), § 4.4 (vocabularios controlados Propp/Greimas
vía `E55_Type`), § 4.5 (segmentos de URI de G9/G10/G7) y § 7 (estructura de
`outline/`). La iteración 024 documentó `outline/` como author-only; v0.4 **abre
ese punto** y debe **enmendar esa nota** (queda parcialmente ingerido: `units/`
sí, el resto prosa). Si durante la implementación algo del diseño no encaja con la
realidad técnica, actualiza `bookwright-design.md` **antes** de divergir el código
(nota 4.3) y registra el cambio en `CHANGELOG` bajo "Design decisions revised
during implementation".

---

## 2. Mapa de iteraciones

| # | Título | Depende de | Tipo |
|---|---|---|---|
| 028 | Ingestar unidades (G9) + funciones (G10) desde `outline/units/` | — | Cablear concepto |
| 029 | Ingestar secuencias narrativas (G7) | 028 | Cablear concepto |
| 030 | Vocabularios Propp/Greimas como `E55_Type` + referencias | 028, 029 | Semántica controlada |
| 031 | Validador de continuidad estructural narrativa | 028, 029 | Validación / consumidor SPARQL |
| 032 | Cierre v0.4: E2E + docs + re-target G6/G3 + `v0.4.0` | 028–031 | Release prep |

Las iteraciones se ejecutan en orden. **028 va primero** porque establece la
superficie de ingesta (`outline/units/`) y el builder base que reutilizan 029–031;
cada vez que 028/029 cablean una clase, esta sale del set diferido del registro
(024) y el test de paridad obliga a actualizar el contrato.

Estimación: medio día a dos días de agente + revisión humana por iteración. La
release va al final, una sola vez (`v0.4.0`).

> **Nota:** 030 y 031 son las candidatas a crecer. Si `/speckit-tasks` infla 030,
> separa el flesh-out de `propp.ttl`/`greimas.ttl` del cableado del tagging
> `E55_Type`. Si 031 crece, el validador puede partirse por tipo de incoherencia.

---

## 3. Iteraciones detalladas

### Iteración 028 — Ingestar unidades (G9) + funciones (G10) desde `outline/units/`

**Objetivo:** abrir la ingesta de `outline/` cableando las clases G9 y G10 ya
existentes a un builder de `outline/units/`, espejo de los directorios de la
biblia, y sacarlas del registro de diferidos.

**Prompt:**

````
/speckit-specify

Necesidad: la ontología congelada modela una capa estructural narrativa (NarrativeUnit G9, NarrativeFunction G10, NarrativeSequence G7) cuyos modelos Pydantic, URIs y cross-refs ya existen en golem/modules/narrative.py, pero ningún builder los alimenta: outline/ no se ingiere en absoluto (declarado author-only en la iteración 024). Queremos abrir la ingesta de outline cableando las unidades narrativas y sus funciones como entidades de primera clase, de modo que la estructura de la trama sea citable por SPARQL, y sacar G9 y G10 del registro de diferidos.

Comportamiento esperado:

- map_bible (o su análogo de outline) procesa outline/units/*.md como directorio uno-entidad-por-fichero (espejo de bible/settings|locations|objects), construyendo entidades NarrativeUnit a partir de su frontmatter.
- El frontmatter de una unidad admite `name` (cadena obligatoria), `functions` (lista de cadenas, opcional) y `roles` (lista de cadenas, opcional). El cuerpo en prosa (descripción del beat) no se ingiere: es para el humano.
- Cada nombre en `functions:` materializa una entidad NarrativeFunction identity-only, deduplicada por slug entre todas las unidades (igual que `narrative_roles:` de personaje materializa NarrativeRole inline). Se emite el cross-ref unit → function (crm:P67_refers_to, ya en el modelo NarrativeUnit).
- Cada nombre en `roles:` se resuelve contra el índice de NarrativeRole existente (los creados inline por personajes); si resuelve, se emite el cross-ref unit → role (crm:P67_refers_to). Si no resuelve, es un soft-miss coherente con el contrato del mapper (UnresolvedReference), nunca un crash.
- El command source bookwright-outline se actualiza: además de la prosa de arcs/structure/synopsis, instruye crear una ficha por unidad narrativa en outline/units/ con frontmatter name/functions/roles. Se re-materializa como SKILL.md por el pipeline existente, en claude y generic, con triggers bilingües preservados.
- El scaffold de proyecto (resources/project/outline/) incluye outline/units/ con su material de arranque, igual que bible/settings/.
- Compatibilidad: una unidad sin frontmatter se trata como fichero no ingerible (skip elegante, como hoy con frontmatter inservible), nunca un crash. Un proyecto sin outline/units/ sigue funcionando igual.
- El registro de diferidos (deferrals.py, iteración 024) deja de incluir NarrativeUnit y NarrativeFunction; el test de paridad de ingesta sigue verde con G9 y G10 ahora "vivos".
- Se enmienda la nota author-only de la iteración 024: outline/ pasa a estar parcialmente ingerido (units/ sí; arcs/structure/synopsis siguen siendo prosa author-only).

Validaciones:

- name es cadena obligatoria; functions y roles, si están, son listas de cadenas.
- Colisión de slug entre unidades se rechaza igual que en characters/settings.

Fuera de scope:

- Secuencias narrativas (G7): iteración 029.
- Tagging E55_Type a vocabularios Propp/Greimas: iteración 030.
- Validadores nuevos sobre la estructura narrativa: iteración 031.
- Cualquier clase o propiedad nueva en la ontología (Principio X): G9/G10 ya existen.
- Atributos de unidad más allá de name/functions/roles; ingesta de arcs/structure/synopsis.

Referencia: ver bookwright-design.md § 4.2 (módulo Narrative), § 4.5 (URIs narrative-unit/narrative-function), § 7 (estructura de outline/). Principio I (texto plano), Principio X (ontología congelada), Principio IV (≤ 500 líneas). Precedente directo: los builders de settings/locations/objects en io/_bible_builders.py (iter. 025–026) y la materialización inline de NarrativeRole desde personaje.
````

**Pista para `/speckit-plan`:** *"Reutiliza la maquinaria `_DirSpec` y los
builders de `io/_bible_builders.py` (extraídos en iter. 025). Añade una `_DirSpec`
para `outline/units/` espejando la de `settings/`, con un builder que construya
`NarrativeUnit`: `name` obligatorio; por cada nombre en `functions:` crea/dedup un
`NarrativeFunction` identity-only por slug y enlaza el cross-ref `functions`; por
cada nombre en `roles:` resuelve contra el índice de `NarrativeRole` (mismo patrón
de resolución de nombres que location→setting) y enlaza el cross-ref `roles`, con
soft-miss `UnresolvedReference` si no resuelve. Decide dónde vive el cableado de
outline: si `map_bible` ya recorre directorios genéricos, añade `outline/units/`
como otra `_DirSpec`; si no, un módulo hermano `io/outline.py` análogo a
`bible.py`, manteniendo ambos < 500 líneas. No toques `golem/`: clases, cross-refs
y registro en `CONCEPTS` ya existen. Edita `resources/commands/bookwright-outline.md`
y re-materializa vía el pipeline de la iteración 9. Añade `outline/units/` al
scaffold en `resources/project/outline/`. Quita `NarrativeUnit` y
`NarrativeFunction` de `deferrals.py` y actualiza `EXPECTED_VERSIONS`/los pines de
huérfanos en `tests/golem/test_ingestion_parity.py`. Enmienda la nota author-only
(docstring de outline / docs). Tests: round-trip de una unidad con functions y
roles, dedupe de funciones entre unidades, resolución de roles contra personajes,
soft-miss cuando un rol no existe, fichero sin frontmatter omitido, colisión de
slug, ausencia del directorio; el test de paridad verde con G9/G10 vivos; el test
del scaffold incluye outline/units/."*

**Criterio de aceptación:** una `outline/units/<slug>.md` con `name:`,
`functions:` y `roles:` se materializa en el grafo como `G9_Narrative_Unit` con sus
`NarrativeFunction` (G10) y sus cross-refs `crm:P67_refers_to`; un rol no resuelto
queda como soft-miss (sin crash); una unidad sin frontmatter se omite; el scaffold
de `bookwright init` incluye `outline/units/`; el cierre congelado no cambia (test
de clausura verde); el registro de diferidos pierde G9 y G10 y el test de paridad
sigue verde; la nota author-only de outline queda enmendada; `ruff`,
`mypy --strict` y `pytest` verdes; cobertura > 85 % en el código nuevo.

---

### Iteración 029 — Ingestar secuencias narrativas (G7)

**Objetivo:** cablear la clase G7 ensamblando secuencias ordenadas a partir de las
unidades que las referencian, sacándola del registro de diferidos. Con esto la
capa estructural narrativa queda completa (solo G6/G3 siguen diferidos).

**Prompt:**

```
/speckit-specify

Necesidad: tras cablear unidades (G9) y funciones (G10) desde outline/units/, falta la última clase de la capa estructural narrativa: NarrativeSequence (G7). Su modelo ya existe (golem/modules/narrative.py: emite dlp:proper-part por unidad miembro en el orden declarado). Queremos que las secuencias narrativas (fabula/syuzhet, líneas de trama) entren al grafo, de modo que el orden de los beats sea citable por SPARQL, y sacar G7 del registro de diferidos. Tras esto la capa estructural narrativa queda completa.

Comportamiento esperado:

- El frontmatter de una unidad (outline/units/*.md) admite, además de name/functions/roles, dos claves opcionales: `sequence` (cadena, nombre de la secuencia a la que pertenece la unidad) y `order` (entero, su posición en esa secuencia).
- Cada secuencia se ensambla a partir de las unidades que la referencian por nombre: se materializa una entidad NarrativeSequence identity-only (dedup por slug), y se emiten sus triples dlp:proper-part hacia las unidades miembro, en el orden dado por `order:` (ascendente). El orden es la tupla del builder; RDF es desordenado (igual que el contrato existente de NarrativeSequence).
- Una unidad con `sequence:` pero sin `order:` se ubica al final de forma determinista (p. ej. tras las que sí tienen order, en orden de slug) — o se rechaza con un mensaje claro; decidir en clarify. Una unidad sin `sequence:` simplemente no pertenece a ninguna secuencia.
- El command source bookwright-outline se actualiza para instruir las claves sequence/order al crear unidades. Se re-materializa como SKILL.md por el pipeline existente, en claude y generic, triggers bilingües preservados.
- Compatibilidad: un proyecto sin ninguna unidad con `sequence:` no produce secuencias y sigue funcionando igual.
- El registro de diferidos deja de incluir NarrativeSequence; el test de paridad sigue verde con G7 vivo. Tras esta iteración el registro solo contiene G6 (RelationshipRole) y G3 (PsychologicalState).

Validaciones:

- sequence, si está, es cadena; order, si está, es entero.
- order duplicado dentro de una misma secuencia: decidir en clarify (rechazo vs. desempate determinista por slug). Slug de secuencia colisionando con otra entidad de tipo distinto no colapsa (segmento de URI distinto, design § 4.5).

Fuera de scope:

- Un directorio outline/sequences/ separado (se descartó la opción dir-driven a favor de unit-driven).
- Tagging E55_Type a Propp/Greimas (iteración 030) y validadores (iteración 031).
- Clases o propiedades nuevas en la ontología (Principio X): G7 ya existe.

Referencia: ver bookwright-design.md § 4.2 (módulo Narrative, fabula/syuzhet), § 4.5 (URI narrative-sequence). Principio I, Principio X, Principio IV. Precedente: el builder de unidades de la iteración 028 y el contrato dlp:proper-part del modelo NarrativeSequence.
```

**Pista para `/speckit-plan`:** *"Extiende el builder de unidades (iter. 028) para
leer `sequence:` y `order:`. Tras construir todas las unidades, agrupa por nombre
de `sequence:`, ordena cada grupo por `order:` ascendente (con la regla de
desempate confirmada en clarify), y por cada grupo materializa un
`NarrativeSequence` (dedup por slug) con su cross-ref `units` (`dlp:proper-part`)
en orden. El ensamblaje de secuencias es un segundo paso sobre el conjunto de
unidades ya construido, no por-fichero. No toques `golem/`: `NarrativeSequence` y
su cross-ref `units` ya existen. Quita `NarrativeSequence` de `deferrals.py` y
actualiza el test de paridad (ahora solo G6/G3 huérfanos). Edita
`resources/commands/bookwright-outline.md` y re-materializa. Tests: una secuencia
con tres unidades ordenadas (verificar el orden de los `proper-part`), order
duplicado según la regla decidida, unidad sin sequence, secuencia con un solo
miembro, ausencia de secuencias; el test de paridad verde con G7 vivo."*

**Criterio de aceptación:** unidades que declaran `sequence:`/`order:` producen un
`G7_Narrative_Sequence` con sus `dlp:proper-part` en el orden correcto; el registro
de diferidos pierde G7 y queda solo con G6/G3; el cierre no cambia; gates verdes;
cobertura > 85 % en el código nuevo.

---

### Iteración 030 — Vocabularios Propp/Greimas como `E55_Type` + referencias

**Objetivo:** dar a la capa estructural su **semántica Propp/Greimas** real (no
solo unidades genéricas): poblar `propp.ttl`/`greimas.ttl` y enlazar funciones y
roles a sus términos de vocabulario controlado vía `E55_Type`, cuando la
constitución del proyecto los active.

**Prompt:**

```
/speckit-specify

Necesidad: la capa estructural narrativa ya entra al grafo (G9/G10/G7), pero sus funciones y roles son entidades identity-only sin semántica: una función llamada "departure" no se reconoce como la función Proppiana correspondiente. GOLEM provee el patrón E55_Type para enchufar vocabularios controlados sin extender el esquema (design § 4.4). Los TTL propp.ttl y greimas.ttl existen como stubs (una sola clase cada uno). Queremos poblarlos y enlazar funciones/roles a sus términos cuando la constitución del proyecto active Propp o Greimas, dando a v0.4 su payoff "Propp/Greimas" real.

Comportamiento esperado:

- propp.ttl se puebla con las funciones Proppianas como términos E55_Type (su conjunto canónico) y greimas.ttl con los actantes del modelo actancial, como vocabularios controlados — vocabulario nuevo en .ttl separados, NUNCA en la ontología congelada golem.ttl (Constitución X).
- Cuando el proyecto tiene Propp y/o Greimas activos (según la constitución / vocabularios activos del proyecto), una NarrativeFunction o NarrativeRole cuyo nombre (o un campo `type:` explícito) coincide con un término del vocabulario recibe un triple crm:P2_has_type hacia ese término. Si no coincide ningún término, la entidad queda sin tipar (no es error).
- La activación de un vocabulario se lee de donde el proyecto ya la declara (constitución / manifiesto / .bookwright/vocabularies/); no se inventa un mecanismo nuevo si ya existe uno. Determinar en plan/clarify la fuente de activación exacta.
- Las referencias references/propp-functions.md y references/greimas-actants.md (ya citadas por la skill bookwright-outline) se proveen/actualizan para que el autor sepa qué nombres usar.
- Compatibilidad: un proyecto sin Propp/Greimas activos produce funciones/roles sin tipar, exactamente como en la iteración 028 (sin regresión).

Fuera de scope:

- Otros vocabularios (booker-seven-plots, essay-structures): fuera de v0.4.
- Cualquier clase nueva en la ontología congelada (Principio X): los términos viven en propp.ttl/greimas.ttl, no en golem.ttl.
- Validadores que usen el tipado (iteración 031).

Referencia: ver bookwright-design.md § 4.4 (vocabularios controlados E55_Type), § 4.2 (módulo Narrative). Principio I, Principio X. Precedente: sources.ttl (v0.2) como vocabulario .ttl separado y su patrón E55_Type.
```

**Pista para `/speckit-plan`:** *"Puebla `resources/vocabularies/propp.ttl` y
`greimas.ttl` como vocabularios `E55_Type` (un `skos`/`rdfs:label` por término;
sigue el patrón de `sources.ttl`). En el builder de funciones/roles (iter. 028),
tras crear la entidad, si el vocab está activo y el nombre/`type:` resuelve a un
término, emite `crm:P2_has_type <término>`. Lee la activación de la fuente que el
proyecto ya use para vocabularios (verifícalo con codegraph: cómo se cargan hoy
`.bookwright/vocabularies/` y qué declara la constitución). Provee
`resources/commands/references/propp-functions.md` y `greimas-actants.md` si no
existen. No toques `golem.ttl`. Tests: función que matchea un término Propp recibe
el `P2_has_type`, función que no matchea queda sin tipar, proyecto sin Propp activo
no emite tipos, carga/parseo de los TTL poblados."*

**Criterio de aceptación:** con Propp activo, una función cuyo nombre coincide con
un término recibe su `crm:P2_has_type`; sin Propp activo no hay regresión; los TTL
poblados parsean; `golem.ttl` y el cierre congelado no cambian; gates verdes;
cobertura > 85 % en el código nuevo.

---

### Iteración 031 — Validador de continuidad estructural narrativa

**Objetivo:** dar a la capa estructural un **consumidor SPARQL** que pruebe su
citabilidad: un validador de continuidad que detecte incoherencias en la
estructura narrativa, registrado en el sistema de validación existente.

**Prompt:**

```
/speckit-specify

Necesidad: la capa estructural narrativa ya está en el grafo (unidades, funciones, secuencias, tipado Propp/Greimas), pero nada la consume todavía: su valor es ser citable por SPARQL para detectar incoherencias. El sistema de validación (validation/validators/*, runner.py, queries.py, registry.py) corre continuity checks contra el grafo. Queremos añadir un validador de continuidad estructural narrativa que aproveche la nueva capa, demostrando que es citable y útil al autor.

Comportamiento esperado:

- Se añade un validador nuevo, registrado en validation/registry.py como los existentes (character presence, focalization, setting continuity, temporal), que ejerce SPARQL contra la capa estructural y reporta incoherencias como findings con su locator file:line cuando aplique.
- Incoherencias candidatas (afinar en clarify, empezar por las de señal clara): (a) unidad narrativa que no pertenece a ninguna secuencia (beat huérfano); (b) hueco o duplicado en el orden (`order`) de una secuencia; (c) unidad cuyo `roles:` referencia un rol no resuelto (ya soft-miss en ingesta, ahora reportado como continuity finding); (d) secuencia vacía. Elegir un subconjunto coherente; no inventar reglas sin valor autoral.
- El validador respeta el contrato de los demás: se ejecuta vía runner.py, emite findings serializables por el sobre --json existente (Principio IX), y se puede activar/desactivar como el resto.
- Compatibilidad: un proyecto sin capa estructural narrativa (sin outline/units/) no produce findings de este validador y no regresa nada.

Fuera de scope:

- Reglas que requieran inferencia LLM (este validador es SPARQL determinista).
- Cambiar el comportamiento de los validadores existentes.
- Clases/propiedades nuevas en la ontología (Principio X).

Referencia: ver bookwright-design.md § 4.2 (módulo Narrative) y la sección de validación. Principio I, Principio IX (--json). Precedente: los validadores existentes en validation/validators/ y sus queries en queries.py.
```

**Pista para `/speckit-plan`:** *"Añade `validation/validators/narrative_structure.py`
(o nombre análogo) siguiendo la forma de un validador existente (mira
`setting_continuity` con codegraph). Las consultas van en `validation/queries.py`;
regístralo en `validation/registry.py`. Reúsa el patrón de findings con locator
`file:line` (la procedencia ya resuelve campo→`file:line` vía el indexador).
Empieza por 2–3 reglas de señal clara (beat huérfano, secuencia vacía, hueco de
order) confirmadas en clarify. Tests: fixture con una incoherencia de cada tipo
que dispara el finding, fixture limpia que no dispara nada, proyecto sin outline/units/
inerte. Verifica el sobre --json del reporte de validación."*

**Criterio de aceptación:** el validador detecta las incoherencias estructurales
elegidas con su locator y las emite por el reporte `--json`; una estructura limpia
no dispara findings; un proyecto sin la capa es inerte; gates verdes; cobertura
> 85 % en el código nuevo.

---

### Iteración 032 — Cierre v0.4: E2E + docs + re-target G6/G3 + `v0.4.0`

**Objetivo:** cerrar el hito: una fixture E2E que ejerza el flujo completo
`outline/units/` → grafo → validación, un workflow test, documentación, el
re-targeting honesto de G6/G3 en el registro de diferidos, y el bump de versión a
`v0.4.0` con su tag.

**Prompt:**

```
/speckit-specify

Necesidad: la capa estructural narrativa está cableada (G9/G10/G7), tipada (Propp/Greimas) y validada. Falta cerrar el hito v0.4 como se cerraron M4 (v0.2.0) y M5 (v0.3.0): una fixture E2E que demuestre el flujo de punta a punta, un workflow test, docs actualizadas, dejar el contrato de diferidos honesto, y la release.

Comportamiento esperado:

- Una fixture E2E de proyecto con outline/units/ poblado (unidades con functions, roles, sequence/order, con Propp activo) ejerce el flujo completo: ingesta → graph build → validación, y se verifica que las entidades narrativas, sus cross-refs, sus tipos E55_Type y los findings del validador aparecen como se espera.
- Un workflow test recorre el camino autoral análogo a los de M4/M5.
- La documentación (docs/, README) cubre la ingesta de outline/units/, el frontmatter de una unidad, la activación de Propp/Greimas y el validador nuevo, en español (convención de idioma de los docs).
- El registro de diferidos (deferrals.py) queda honesto: G6 (RelationshipRole) y G3 (PsychologicalState) son los únicos diferidos; su target_version se re-apunta de "v0.4" a un hito posterior concreto (decidir el label en clarify; el contrato exige una etiqueta de versión concreta, no un placeholder). El test de paridad sigue verde.
- Bump de versión a v0.4.0 (single-source en __version__), CHANGELOG con la sección v0.4.0 (incluida "Design decisions revised during implementation" si aplica), CLAUDE.md y bookwright-design.md actualizados donde el código divergió.

Fuera de scope:

- Cablear G6/G3 (siguen diferidos).
- Cualquier feature nueva: esta iteración es solo cierre, fixture, docs y release.

Referencia: ver bookwright-roadmap.md § 4 (G6/G3, horizonte demand-pulled), las iteraciones de cierre 016 (M4) y 023 (M5) como precedente, y la skill bookwright-release. Principio VIII (cobertura), Principio I.
```

**Pista para `/speckit-plan`:** *"Modela la fixture E2E sobre las de M4/M5 (mira
con codegraph cómo está montada la de la iteración 023). El workflow test reproduce
el flujo de un autor que estructura la trama. En `deferrals.py` cambia el
`target_version` de `RelationshipRole` y `PsychologicalState` de `"v0.4"` al label
posterior confirmado en clarify (p. ej. `"v0.5"`) y actualiza
`EXPECTED_VERSIONS`/los pines del test de paridad; el set de huérfanos (G6/G3) NO
cambia, solo el mapping de versión. La release la conduce la skill
`bookwright-release` (verificar gates → merge a main → bump `__version__` →
CHANGELOG → CLAUDE.md → design → commit de release → tag anotado `v0.4.0`).
Actualiza también `bookwright-roadmap.md` § 1 (estado: v0.4 entregada) y el marcador
`← AQUÍ` de § 2."*

**Criterio de aceptación:** la fixture E2E y el workflow test pasan ejerciendo el
flujo completo; los docs cubren la nueva ingesta y validación; el registro de
diferidos solo tiene G6/G3 con un target_version posterior firme (sin "v0.4"); el
test de paridad verde; `__version__` y CHANGELOG en `v0.4.0`; `main` tageada
`v0.4.0`; los cuatro gates verdes; cobertura ≥ 80 % global.

---

## 4. Notas operativas

### 4.1 Manejo de spec rechazadas

Si tras `/speckit-analyze` aparecen issues de consistencia entre spec/plan/tasks,
vuelve a `/speckit-clarify` o edita `spec.md` directamente, regenera plan y tasks,
y vuelve a analizar. No fuerces `/speckit-implement` con análisis con errores.

### 4.2 Iteraciones que se complican

Si una iteración crece más de lo previsto durante `/speckit-tasks` (más de ~10
tareas), divídela en dos specs. En este hito, **030** (poblar TTL + cablear
tagging E55_Type) y **031** (validador con varias reglas) son las candidatas más
probables a split.

### 4.3 Cambios en el documento de diseño

El diseño es la fuente de verdad técnica. Si durante la implementación algo del
diseño no encaja con la realidad técnica, actualiza `bookwright-design.md`
**antes** de divergir el código, y registra el cambio en `CHANGELOG` bajo "Design
decisions revised during implementation". Las decisiones de § 16 son inmutables.
La nota author-only de `outline/` (iteración 024) **se enmienda** en la 028.

### 4.4 Cuándo pedir ayuda al humano

Spec Kit genera bien spec/plan/tasks pero puede divagar en decisiones de diseño no
triviales (p. ej. la regla de desempate de `order`, la fuente de activación de
vocabularios, o el subconjunto de reglas del validador). Cuando dudes, ejecuta
`/speckit-clarify` o intervén manualmente; redirige al doc de diseño / roadmap.

### 4.5 Después de v0.4

Con v0.4 la **paridad de ingesta queda cerrada**: todos los conceptos del cierre
o se alimentan desde texto autoral o están diferidos con razón y versión firmes
(solo G6/G3, re-apuntados a un hito posterior). Lo que sigue vivo en el roadmap:

- **RelationshipRole (G6) + PsychologicalState (G3)** — el subsistema de
  roles/estados tipados con atributos y superficie autoral. Candidato a hito
  propio cuando haya demanda.
- **Horizonte demand-pulled (sin versión asignada):** búsqueda vectorial
  (ChromaDB sobre rdflib, desacoplada) y export (EPUB/PDF/print vía pandoc). Se
  activan por condición concreta, no por número de versión (ver
  `bookwright-roadmap.md` § 4). El `1.0` se **gana** cuando el flujo de punta a
  punta esté probado en un libro real; no se pre-asigna.

Cuando llegue el siguiente hito, vacía este plan de lo entregado y redáctalo para
él, manteniendo `bookwright-roadmap.md` como la intención durable. Quedan
descartados: presets, GrafeoIndexer/Grafeo, multi-integración y extension system;
ver `bookwright-design.md` § 15.5.

---

**Fin del plan.**
