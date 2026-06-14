# Bookwright — Plan de implementación con Spec Kit

> **Documento complementario a:** `bookwright-design.md` (el *cómo* técnico) y
> `bookwright-roadmap.md` (el *qué* y *por qué* a lo largo de versiones).
> **Propósito:** secuencia de iteraciones para el **hito en curso** de Bookwright,
> el tramo de **endurecimiento v0.3.x** (cancelar deuda técnica, robustez, cerrar
> atajos de v0). Cada iteración tiene un prompt listo para invocar
> `/speckit-specify`.
> **Audiencia:** Jorge (o cualquier desarrollador con Spec Kit instalado y
> `bookwright-design.md` en el root del repo).

> **Nota sobre versiones anteriores de este plan:** las iteraciones 1–23
> (hitos M0–M5, releases `v0.1.0`, `v0.2.0` y `v0.3.0`) ya están **completadas y
> mergeadas en `main`**. Su detalle vive ahora en el historial git, en
> `specs/001-…` … `specs/023-…` y en el `CHANGELOG`. Este documento se ha vaciado
> de ellas a propósito: solo describe el trabajo **por hacer**. El registro de lo
> hecho es `CLAUDE.md` (tabla de iteraciones) y los `specs/` por iteración; la
> intención de largo plazo es `bookwright-roadmap.md`.

---

## 0. Estado y cómo usar este documento

### 0.1 Punto de partida

- `v0.1.0` (M0–M3, iter. 1–11), `v0.2.0` (M4, iter. 12–18) y `v0.3.0` (M5,
  iter. 19–23) están en `main`: paquete real en `src/bookwright/`, suite de
  tests, docs y gates verdes. `v0.3.0` está tageada (2026-06-13).
- El repo ya está inicializado con Spec Kit (`.specify/`, `.claude/skills/speckit-*`)
  y tiene su constitución ratificada (`.specify/memory/constitution.md`).
- **No hay que re-bootstrapear ni recrear la constitución.** Este tramo construye
  sobre el código existente y **no reabre ningún axioma** de `bookwright-design.md`
  § 16.

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
- **Cada iteración entrega un delta observable** y se libera como un **patch**
  (`v0.3.1`, `v0.3.2`, …). El plumbing interno (p. ej. un refactor que habilita
  una feature) **viaja dentro del patch que habilita**, nunca como release de
  cero cambios visibles (disciplina de scope de la constitución).

### 0.3 Numeración

Los `specs/` van por `001`…`023`. Este tramo **arranca en 024** y continúa la
secuencia. Cada iteración es un branch `NNN-<short-name>` con su propio `specs/`.

---

## 1. El hito: endurecimiento v0.3.x

### 1.1 El problema

Antes de avanzar a funcionalidad nueva (la capa estructural narrativa de v0.4)
conviene **solidificar la base**: saldar la deuda técnica que quedó como atajos de v0,
hacer **explícito** lo que hoy está implícito, y robustecer el sistema actual.
Construir sobre cimientos firmes en vez de sobre atajos no documentados.

La deuda dominante: **la ontología congelada modela 13 conceptos narrativos, pero
solo ~6 son alcanzables desde texto autoral.** El resto está modelado, registrado
en `CONCEPTS`, cubierto por el test de clausura (SC-003)… y **muerto de cara al
autor** porque ningún builder lo alimenta (`io/bible.py` solo construye Character,
Setting, NarrativeEvent y SocialRelationship, más NarrativeRole/CharacterFeature
inline bajo personaje). Síntoma observado en uso real: una investigación con
`bears_on:`/`constrains:` a una localización queda como *soft-miss*
(`ResearchWarning`) porque `bible/locations/` **no se procesa en absoluto**.

Siete conceptos huérfanos: **NarrativeLocation (G13), Object (G16),
PsychologicalState (G3), RelationshipRole (G6), NarrativeUnit (G9),
NarrativeFunction (G10), NarrativeSequence (G7)**. Locations es solo el primero
que duele.

### 1.2 El principio rector del tramo

> **Ningún concepto modelado sin un camino desde texto autoral o una nota de
> diferimiento explícita; ningún directorio del scaffold que el motor ignore sin
> decirlo.**

Es decir: eliminar el **silencio** entre "modelado" y "alimentado". Para cada
clase del cierre, o hay builder, o hay una nota de diferimiento (razón + versión
objetivo) respaldada por un **test que asevera que el conjunto de clases huérfanas
es exactamente el conjunto intencionadamente diferido**. Cada patch que cablea una
clase la **saca** del set diferido y el test obliga a actualizar el contrato — la
deuda deja de pudrirse en silencio.

Esto respeta las restricciones duras: cablear un concepto **no toca la ontología**
(la clase ya existe en `CLASS_IRI`; falta el builder — Constitución X a salvo),
Principio I (texto plano fuente de verdad), Principio IX (`--json`), Principio IV
(≤ 500 líneas, un subcomando por módulo), Principio VIII (cobertura ≥ 80 %).

### 1.3 Encaje en el roadmap

Este tramo **toma la línea `v0.3.x`** (patches sucesivos). Lo que **no** entra
aquí y pasa a **v0.4**: la capa estructural narrativa Propp/Greimas (G7/G9/G10) y
la ingesta de `outline/`, porque son un subsistema con modelo e ingesta nuevos, no
un fix. La búsqueda vectorial y el export pasan al **horizonte demand-pulled** (sin
versión asignada; se activan por condición concreta, no por número de versión —
ver `bookwright-roadmap.md` § 4). Siguen
descartados (decisión de owner): presets, GrafeoIndexer/Grafeo, multi-integración
más allá de `claude`/`generic`, extension system. Ver `bookwright-roadmap.md`.

### 1.4 El doc de diseño

El diseño canónico de los conceptos vive en `bookwright-design.md` § 4.2
(conceptos GOLEM y sus URI) y § 7.2 (decisión de ingesta de localizaciones G13).
Si durante la implementación algo del diseño no encaja con la realidad técnica,
actualiza `bookwright-design.md` **antes** de divergir el código (nota 4.3), y
registra el cambio en `CHANGELOG` bajo "Design decisions revised during
implementation".

---

## 2. Mapa de iteraciones

| # | Título | Release | Depende de | Tipo |
|---|---|---|---|---|
| 024 | Honestidad del cierre: guarda de paridad de ingesta + notas de diferimiento | v0.3.1 | — | Robustez / contrato |
| 025 | Indexar localizaciones (`G13_Narrative_Location`) + split de `bible.py` | v0.3.2 | 024 | Cablear concepto |
| 026 | Indexar objetos (`G16_Object`): builder + scaffold `bible/objects/` + skill | v0.3.3 | 024, 025 | Cablear concepto |
| 027 | Limpieza: sobre JSON único + G6/G3 diferidos a v0.4 + rename unresolved-reference | v0.3.4 | 024 | Limpieza / decisión |

Las iteraciones se ejecutan en orden. **024 va primero a propósito**, aunque
locations sea lo que más pica: establece el *contrato* (qué está vivo, qué está
diferido y por qué) contra el que se miden 025–027. Cada vez que 025/026 cablean
una clase, esta sale del set diferido de 024 y el test lo obliga a registrar.

Estimación: medio día a dos días de agente + revisión humana por iteración.

> **Nota:** 027 es la iteración de cierre "blanda". Si durante `/speckit-tasks`
> crece, divide la limpieza del sobre JSON (mecánica) de la decisión G6/G3
> (diseño) en dos specs/patches.

---

## 3. Iteraciones detalladas

### Iteración 024 — Honestidad del cierre: guarda de paridad de ingesta + notas de diferimiento

**Objetivo:** hacer **visible y congelada** la deuda de conceptos huérfanos, sin
cablear ninguno todavía. Establecer el contrato "qué concepto está vivo, qué está
diferido y por qué" con un test que impida que se pudra en silencio.

**Prompt:**

````
/speckit-specify

Necesidad: la ontología congelada modela 13 conceptos narrativos (registrados en CONCEPTS y cubiertos por el test de clausura), pero solo ~6 son alcanzables desde texto autoral; los otros 7 están modelados pero ningún builder los alimenta — están "muertos de cara al autor" sin que nada lo declare. Ese silencio entre "modelado" y "alimentado" es la deuda. Antes de cablear conceptos uno a uno, queremos un contrato explícito: para cada concepto del cierre, o hay un camino desde texto autoral, o hay una nota de diferimiento (razón + versión objetivo), respaldada por un test que asevere que el conjunto de huérfanos es exactamente el conjunto intencionadamente diferido.

Comportamiento esperado:

- Se introduce un registro estático de DIFERIMIENTO: para cada concepto de CONCEPTS hoy no alcanzable desde texto autoral (NarrativeLocation G13, Object G16, PsychologicalState G3, RelationshipRole G6, NarrativeUnit G9, NarrativeFunction G10, NarrativeSequence G7), una entrada con su razón breve y su versión objetivo (p. ej. G13/G16 → v0.3.x; G9/G10/G7 → v0.4; G6/G3 → "por decidir"). El registro es texto/código plano, unit-testeable.
- Un test de paridad de ingesta asevera, de forma determinista, que el conjunto de conceptos que NO se materializan desde una fixture de ejercicio (los huérfanos reales) es EXACTAMENTE el conjunto declarado como diferido. Si alguien añade un builder (un concepto deja de ser huérfano) sin sacarlo del registro de diferidos, el test falla y obliga a actualizar el contrato. Y al revés: declarar diferido algo que sí se ingiere también falla.
- El "está vivo" se comprueba contra la realidad, no contra una lista a mano: construir el grafo de una fixture que ejerza todos los caminos de ingesta vigentes y observar qué rdf:type de CLASS_IRI aparecen.
- Se documenta explícitamente, por escrito, que outline/ y manuscript/ son author-only en v0.3: el scaffold los crea pero el motor no los ingiere (decisión legítima de v0, hoy no declarada). Una nota en el código del lector de manuscrito y/o en docs, no un cambio de comportamiento.

Determinismo:

- El test de paridad es una función pura del corpus de la fixture y del registro de diferidos: misma entrada, mismo veredicto.

Fuera de scope:

- Cablear cualquier concepto huérfano (iteraciones 025+).
- Tocar la ontología congelada o añadir clases/propiedades (Principio X): no se añade nada al cierre.
- Cualquier ingesta nueva de outline/ o manuscript/ (eso es v0.4): aquí solo se DOCUMENTA que hoy no se ingieren.

Referencia: ver bookwright-roadmap.md § 3 (paridad de ingesta), bookwright-design.md § 4.2 (conceptos GOLEM y URI). Principio I (texto plano), Principio X (ontología congelada), Principio VIII (testeable). Precedente de test de clausura: el SC-003 de la iteración 5 (test_namespaces).
````

**Pista para `/speckit-plan`:** *"Modela el registro de diferimiento como una
estructura estática (un dict `concept -> (reason, target_version)`) en su propio
módulo, junto a `golem/__init__.py` (donde vive `CONCEPTS`) o en
`golem/namespaces.py`. El test de paridad va en `tests/golem/`: usa una fixture
existente que ejerza todos los caminos (characters/settings/timeline/relationships
+ narrative_roles/features), construye el grafo con `RdflibIndexer`, recoge los
`rdf:type` ∈ `CLASS_IRI.values()` presentes, y deriva `huérfanos = CONCEPTS −
observados − {inline-only}`; asevera `huérfanos == set(registro_diferidos)`. La
nota author-only de outline/manuscript va como docstring en `io/manuscript.py`
(que ya dice 'v0 does no prose mining') extendido a outline, y/o una línea en
`docs/`. No toques `golem/` salvo el registro nuevo."*

**Criterio de aceptación:** existe un registro de diferimiento con razón y versión
para los 7 conceptos huérfanos; el test de paridad pasa y falla si se añade un
builder sin actualizar el registro (verificado invirtiéndolo en el propio test o
con un caso negativo); `outline/`/`manuscript/` documentados como author-only; el
cierre de la ontología no cambia (test de clausura verde); `ruff`,
`mypy --strict` y `pytest` verdes; cobertura > 85 % en el código nuevo.

---

### Iteración 025 — Indexar localizaciones (`G13_Narrative_Location`) + split de `bible.py`

**Objetivo:** cerrar el atajo de v0 cableando la clase G13 ya existente a un
*builder* de `bible/locations/`, sacándola del registro de diferidos. Como
`io/bible.py` está en el límite de 500 líneas, **el split del módulo viaja dentro
de este patch** (es el plumbing que habilita la feature, no una release aparte).

**Prompt:**

```
/speckit-specify

Necesidad: hoy bible/locations/*.md no se procesa en absoluto (atajo de v0): el command bookwright-bible instruye escribir cada localización sin frontmatter ingerido y el mapper no tiene builder para locations/. La clase G13_Narrative_Location ya está reservada y modelada en el código (modelo NarrativeLocation en golem/modules/setting.py, en el cierre congelado CLASS_IRI, registrada en CONCEPTS, con cross-ref `setting` vía dlp:generic-location). Queremos que las localizaciones entren al grafo como entidades de primera clase, de modo que una investigación con bears_on:/constrains: a una localización resuelva en vez de quedar como soft-miss; y sacar G13 del registro de diferidos de la iteración 024.

Comportamiento esperado:

- map_bible procesa bible/locations/*.md como directorio uno-entidad-por-fichero (espejo de settings/), construyendo entidades NarrativeLocation a partir de su frontmatter.
- El frontmatter de una localización admite `name` (cadena obligatoria) y `setting` (opcional, nombre de un setting hermano). Cuando `setting` está presente, se resuelve contra el índice de settings y emite el cross-ref dlp:generic-location (location → su setting); si no resuelve, es un soft-miss coherente con el contrato existente del mapper (no un crash).
- El command source bookwright-bible se actualiza: las localizaciones pasan a llevar frontmatter `name:` (+ `setting:` opcional) además de sus secciones sensoriales en prosa. Se re-materializa como SKILL.md por el pipeline existente, en claude y generic, con triggers bilingües preservados.
- Compatibilidad: una localización antigua sin frontmatter (estilo v0) se trata como fichero no ingerible (skip elegante, como hoy hace el mapper con frontmatter inservible), nunca un crash. Un proyecto sin bible/locations/ sigue funcionando igual.
- El registro de diferidos de la iteración 024 deja de incluir G13; el test de paridad de ingesta sigue verde con G13 ahora "vivo".

Validaciones:

- name es cadena obligatoria; setting, si está, es cadena.
- Colisión de slug entre localizaciones se rechaza igual que en characters/settings.

Refactor que acompaña (mismo patch, sin cambio de comportamiento):

- io/bible.py está en el límite de 500 líneas (Principio IV). Antes o junto con el builder de locations, extrae parte del módulo (p. ej. los builders concretos y/o la maquinaria de DirectorySpec) a un módulo hermano, dejando map_bible legible y por debajo del límite. El refactor no cambia ninguna salida observable; los tests existentes de bible lo cubren.

Fuera de scope:

- Cualquier clase o propiedad nueva en la ontología (Principio X): G13 ya existe, no se añade nada.
- Cambiar el validador factual_anchor o el comportamiento de research más allá de que los enlaces a localizaciones ahora resuelvan.
- Atributos de localización más allá de identidad + setting (v0 de la clase es identity-only, igual que Setting).

Referencia: ver bookwright-design.md § 7.2 (decisión de ingesta G13), § 4.2 y § 4.5 (G13 como concepto y su URI), § 20 (research / soft-miss). Principio I (texto plano), Principio X (ontología congelada), Principio IV (≤ 500 líneas). Precedente de builder: el de settings/ en io/bible.py.
```

**Pista para `/speckit-plan`:** *"Primero el split: extrae de `io/bible.py` los
builders concretos (`_build_character`, `_build_event`, los coercers) y/o las
dataclasses `_DirSpec`/`_CollectionSpec` a un módulo hermano (p. ej.
`io/_bible_builders.py`), dejando `map_bible` y el cableado de specs en
`bible.py` < 500 líneas; los tests existentes garantizan que no cambia nada.
Luego añade una `_DirSpec` para `locations/` espejando la de `settings/`, con un
builder que construya `NarrativeLocation` y resuelva el cross-ref `setting`
contra el índice de settings (mismo patrón de resolución de nombres). No toques
`golem/`: la clase, el cross-ref y el registro en `CONCEPTS` ya existen. Edita
`resources/commands/bookwright-bible.md` para dar frontmatter a las
localizaciones y re-materializa vía el pipeline de la iteración 9. Saca G13 del
registro de diferidos de la 024. Actualiza `bookwright-design.md` § 7.2 retirando
el atajo. Tests: round-trip con y sin `setting`, resolución del cross-ref,
soft-miss cuando el setting no existe, fichero sin frontmatter tratado como skip,
colisión de slug; el test de paridad de la 024 sigue verde con G13 vivo."*

**Criterio de aceptación:** una `bible/locations/<slug>.md` con `name:` (y
`setting:`) se materializa en el grafo como `G13_Narrative_Location` con su triple
`dlp:generic-location`; una investigación con `bears_on:` a esa localización
resuelve (sin `ResearchWarning`); una localización sin frontmatter se omite sin
crash; `io/bible.py` queda por debajo de 500 líneas; el cierre congelado no cambia
(test de clausura verde); el test de paridad (024) sigue verde con G13 fuera de
diferidos; `ruff`, `mypy --strict` y `pytest` verdes; cobertura > 85 % en el
código nuevo.

---

### Iteración 026 — Indexar objetos (`G16_Object`): builder + scaffold + skill

**Objetivo:** cablear la clase G16 (identity-only, espejo de settings/), que hoy
ni siquiera tiene directorio en el scaffold ni mención en la skill de biblia.

**Prompt:**

```
/speckit-specify

Necesidad: la clase G16_Object está modelada (modelo Object en golem/modules/character.py, identity-only, en CLASS_IRI y CONCEPTS) pero es huérfana: no hay builder, no existe bible/objects/ en el scaffold, y bookwright-bible no menciona objetos. Los objetos del mundo narrativo (un arma, una reliquia, un documento) no pueden ser blanco de investigación ni de cross-refs. Queremos cablearlos como entidades de primera clase, espejo de settings/, y sacar G16 del registro de diferidos.

Comportamiento esperado:

- map_bible procesa bible/objects/*.md como directorio uno-entidad-por-fichero (espejo de settings/), construyendo entidades Object a partir de su frontmatter `name` (cadena obligatoria). v0 de la clase es identity-only, igual que Setting.
- El scaffold de proyecto (resources/project/) incluye bible/objects/ con su material de arranque, igual que bible/settings/ y bible/locations/.
- El command source bookwright-bible se actualiza para instruir la creación de fichas de objeto con frontmatter `name:`. Se re-materializa como SKILL.md por el pipeline existente, en claude y generic, triggers bilingües preservados.
- Compatibilidad: ausencia de bible/objects/ no afecta a nada; fichero sin frontmatter se omite sin crash; colisión de slug se rechaza como en characters/settings.
- El registro de diferidos (024) deja de incluir G16; el test de paridad sigue verde con G16 vivo.

Validaciones:

- name es cadena obligatoria; colisión de slug rechazada.

Fuera de scope:

- Atributos de objeto más allá de identidad (identity-only en v0).
- Clases o propiedades nuevas en la ontología (Principio X): G16 ya existe.
- Cross-refs de objeto (p. ej. objeto → personaje portador): fuera de este patch.

Referencia: ver bookwright-design.md § 4.2 (G16 como concepto y su URI). Principio I, Principio X. Precedente directo: el builder de settings/ en io/bible.py y, recién hecho, el de locations/ (iteración 025).
```

**Pista para `/speckit-plan`:** *"Añade una `_DirSpec` para `objects/`
espejando la de `settings/` (identity-only, `SETTING_KEYS`-equivalente con solo
`name`). Reutiliza el módulo de builders ya extraído en 025. Añade
`bible/objects/` al scaffold en `resources/project/` con su `.tmpl`/material
mínimo, y edita `resources/commands/bookwright-bible.md` para instruir objetos.
Re-materializa vía el pipeline de la iteración 9. Saca G16 del registro de
diferidos. Tests: round-trip de un objeto, ausencia del directorio, fichero sin
frontmatter omitido, colisión de slug; el test de paridad (024) verde con G16
vivo; el test del scaffold incluye bible/objects/."*

**Criterio de aceptación:** una `bible/objects/<slug>.md` con `name:` se
materializa como `G16_Object`; el scaffold de `bookwright init` incluye
`bible/objects/`; un objeto sin frontmatter se omite sin crash; el cierre no
cambia; el test de paridad (024) verde con G16 fuera de diferidos; gates verdes;
cobertura > 85 % en el código nuevo.

---

### Iteración 027 — Limpieza: sobre JSON único + decisión G6/G3 + rename unresolved-reference

**Objetivo:** saldar la deuda menor de consistencia del sobre JSON de éxito y
**tomar una decisión explícita** sobre los dos conceptos huérfanos "medios"
(RelationshipRole G6, PsychologicalState G3). **Decisión tomada en `/speckit-clarify`:
ambos se confirman diferidos a `v0.4`** (razón: "requires a typed roles/states model
with attributes and an authoring surface"); ninguno se cablea, porque cada uno tiene
un cross-ref obligatorio y sin superficie autoral un nodo identity-only sería
degenerado. Se suma un tercer cabo, **deferido explícitamente por la iteración 025**:
renombrar el tipo de aviso `UnresolvedParticipant` → `UnresolvedReference` (tipo +
clave `--json` + prosa stderr), eliminando el desajuste modelo↔wire. Con esto el tramo
v0.3.x cierra en 027.

**Prompt:**

```
/speckit-specify

Necesidad: quedan dos cabos del tramo de endurecimiento. (1) El sobre JSON de éxito se single-sourcea en ok_payload() (iteración 020), pero check/focus/graph siguen construyendo el dict {"status":"ok",...} a mano — deuda de consistencia documentada como "out of 020's scope". (2) Dos conceptos huérfanos "medios" siguen sin decisión: RelationshipRole (G6) y PsychologicalState (G3); el registro de diferidos (024) los marca "por decidir". Hay que resolver ambos cabos para cerrar el tramo con el contrato de paridad limpio.

Comportamiento esperado:

- Sobre JSON: check, focus y graph enrutan su documento de éxito por ok_payload()/emit_json en vez de construir el dict a mano, sin cambiar la salida observable (mismos bytes). Un test asevera que ninguna salida cambia.
- Decisión G6/G3: para cada uno, o (a) se cablea un builder mínimo identity-only si encaja sin tocar la ontología y sin inflar bible.py, sacándolo de diferidos; o (b) se confirma su diferimiento con una razón concreta y una versión objetivo en el registro de la 024 (p. ej. "requiere modelo de roles/estados con atributos → v0.4"). La decisión se documenta; el registro queda sin entradas "por decidir".
- Tras esta iteración, el registro de diferidos solo contiene conceptos con razón y versión objetivo firmes (sin "por decidir"), y el tramo v0.3.x cierra.

Fuera de scope:

- La capa estructural narrativa (G9/G10/G7) e ingesta de outline/: es v0.4, no se toca aquí salvo para confirmar su diferimiento en el registro.
- Refactors del sobre JSON más allá de check/focus/graph.

Referencia: ver bookwright-roadmap.md § 3, _envelope.py (ok_payload, nota "out of 020's scope"), el registro de diferidos de la iteración 024, bookwright-design.md § 4.2 (G6/G3). Principio IX (--json).
```

**Pista para `/speckit-plan`:** *"Sobre JSON de éxito: en `commands/focus/*` y
`commands/graph/query.py` reemplaza los dicts `{"status":"ok",...}` por
`ok_payload(**fields)` + `emit_json`, exactamente como ya hace `status`
(iteración 020). `check.py` **no** se envuelve en `ok_payload`: su sobre es
`{"ok": <bool>, "checks": [...]}` sin clave top-level `status` — single-sourcear
solo donde no cambie ningún byte; los dicts por-check `{"name",...,"status"}` son
sub-objetos de dominio, no el sobre. `graph build` **ya** serializa por el
`to_json()` de su report object: confirmar, no tocar. Un test de regresión
captura los bytes actuales de `check` / `focus` show·set·clear / `graph query` /
`graph build` y asevera idénticos tras el cambio. Para G6/G3 **la decisión ya
está tomada (clarify): confirmar diferimiento de ambos, NO cablear** — edita
`golem/deferrals.py` cambiando las entradas de `RelationshipRole` (G6) y
`PsychologicalState` (G3) de `"undecided"` a `target_version` `"v0.4"` con razón
'requires a typed roles/states model with attributes and an authoring surface';
ambos siguen observados como huérfanos. Actualiza `EXPECTED_VERSIONS` (y, si
aplica, los pines reachable-set/orphan-set) en
`tests/golem/test_ingestion_parity.py`; el set de huérfanos NO cambia, solo el
mapping de versión. Elimina el literal `"undecided"` del contrato del registro.
Rename unresolved-reference (User Story 3, deferido por la 025): en
`io/report.py` renombra el tipo `UnresolvedParticipant` → `UnresolvedReference`
(campos `{path,entity,name}` intactos, docstring generalizado a cualquier
referencia sin resolver: `participants:` o `setting:`). Renombra la clave `--json`
`unresolved_participants` → `unresolved_references` en `graph build` conservando
su POSICIÓN en el sobre; nuevo golden baseline solo para esa clave (todo lo demás
byte-idéntico). En `commands/graph/build.py` el resumen stderr pasa a 'N
unresolved reference(s)'. Actualiza `docs/commands/graph-build.md`. Grep final:
ningún `UnresolvedParticipant` ni `unresolved_participants` en `src/` ni `docs/`."*

**Criterio de aceptación:** `focus`/`graph query` emiten su éxito vía
`ok_payload`/`emit_json` y `check`/`graph build` quedan confirmados single-sourced,
todos con salida byte-idéntica salvo la única clave renombrada `unresolved_references`
(test de regresión verde con nuevo golden para esa clave); G6 y G3 quedan **diferidos a
v0.4** con razón firme (fuera de "por decidir", siguen huérfanos, test de paridad
verde); el registro de diferidos no tiene entradas "undecided"; no queda ningún
`UnresolvedParticipant`/`unresolved_participants` en `src/` ni `docs/` y
`docs/commands/graph-build.md` nombra la clave nueva; gates verdes; cobertura > 85 %
en el código nuevo.

---

## 4. Notas operativas

### 4.1 Manejo de spec rechazadas

Si tras `/speckit-analyze` aparecen issues de consistencia entre spec/plan/tasks,
vuelve a `/speckit-clarify` o edita `spec.md` directamente, regenera plan y tasks,
y vuelve a analizar. No fuerces `/speckit-implement` con análisis con errores.

### 4.2 Iteraciones que se complican

Si una iteración crece más de lo previsto durante `/speckit-tasks` (más de ~10
tareas), divídela en dos specs/patches. En este tramo, la **027** (sobre JSON +
decisión G6/G3) es la candidata más probable a split: separa la limpieza mecánica
del sobre de la decisión de diseño de G6/G3.

### 4.3 Cambios en el documento de diseño

El diseño es la fuente de verdad técnica. Si durante la implementación algo del
diseño no encaja con la realidad técnica, actualiza `bookwright-design.md`
**antes** de divergir el código, y registra el cambio en `CHANGELOG` bajo "Design
decisions revised during implementation". Las decisiones de § 16 son inmutables.

### 4.4 Cuándo pedir ayuda al humano

Spec Kit genera bien spec/plan/tasks pero puede divagar en decisiones de diseño
no triviales (p. ej. cablear o no G6/G3). Cuando dudes, ejecuta `/speckit-clarify`
o intervén manualmente; redirige al doc de diseño / roadmap.

### 4.5 Después de v0.3.x

Tras cerrar este tramo, el roadmap que se mantiene es **v0.4 — la capa estructural
narrativa** (Propp/Greimas: G9/G10/G7) y la **ingesta de `outline/`**, que cierran
la paridad de ingesta. La **búsqueda vectorial** (ChromaDB sobre rdflib,
desacoplada) y el **export** (EPUB/PDF/print vía pandoc) pasan al **horizonte
demand-pulled**: sin versión asignada, se activan por condición concreta (ver
`bookwright-roadmap.md` § 4). Cuando llegue el momento, vaciar este plan
de lo entregado y redactarlo para el siguiente hito, manteniendo
`bookwright-roadmap.md` como la intención durable. Quedan descartados: presets,
GrafeoIndexer/Grafeo, multi-integración y extension system; ver
`bookwright-design.md` § 15.5.

---

**Fin del plan.**
