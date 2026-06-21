# Bookwright — Plan de implementación con Spec Kit

> **Documento complementario a:** `bookwright-design.md` (el *cómo* técnico) y
> `bookwright-roadmap.md` (el *qué* y *por qué* a lo largo de versiones).
> **Propósito:** secuencia de iteraciones para el **hito en curso** de Bookwright.
> Cada iteración trae su prompt y el **comando del workflow** listo para ejecutar.
> **Audiencia:** Jorge (o cualquier desarrollador con Spec Kit instalado y
> `bookwright-design.md` en el root del repo).

> **Hito en curso: track de endurecimiento post-dogfooding `v0.4.x`** (iteraciones
> **034–036**). Salió de un **ejercicio de dogfooding** sobre un libro real
> ("El Cerco de Almenara", 49 ficheros / 90 entidades / 1550 triples, 2026-06-21)
> que destapó tres hallazgos concretos —un bug de validador, un gap de recall medido
> y fricción de mensajes de error— hoy registrados como **DEBT-004/005/006** en
> `DEBT.md`. Cada iteración cierra una entrada de deuda y corta su **patch** propio
> (`v0.4.2`, `v0.4.3`, `v0.4.4`). No es trabajo especulativo: un bug, un gap *medido*
> y UX — todos pasan la disciplina de scope. Las iteraciones 1–33 (M0–M5, el tramo
> `v0.3.1`…`v0.3.4`, `v0.4.0` y el patch `v0.4.1`) están **mergeadas en `main`**; su
> detalle vive en el historial git, en `specs/001-…` … `specs/033-…` y en el
> `CHANGELOG`. El horizonte demand-pulled (búsqueda vectorial, export, G6/G3) sigue
> en `bookwright-roadmap.md` § 4, **no** aquí.

---

## 0. Estado y cómo usar este documento

### 0.1 Punto de partida

- Todo hasta `v0.4.1` está en `main` (tageado, 2026-06-21): paquete real en
  `src/bookwright/`, suite de tests, docs y los cuatro gates verdes. La iteración
  033 (eliminación de `NarrativeRole` muerto + endurecimiento de paridad) cerró
  `v0.4.1`; con v0.4 la **paridad de ingesta** quedó alcanzada.
- El repo ya está inicializado con Spec Kit (`.specify/`, `.claude/skills/speckit-*`)
  y su constitución ratificada (`.specify/memory/constitution.md`, v1.5.0). **No** se
  re-bootstrapea ni se reabre ningún axioma de `bookwright-design.md` § 16.
- El **registro de diferidos** (`src/bookwright/golem/deferrals.py`) y su **test de
  paridad** (`tests/golem/test_ingestion_parity.py`) declaran hoy solo dos conceptos
  huérfanos —`RelationshipRole` (G6) y `PsychologicalState` (G3)—, ambos en el
  horizonte demand-pulled. Ninguna iteración de este track los toca.
- **Origen del track:** el dogfooding (§ 1). El proyecto de prueba vive en
  `/tmp/bookwright-dogfood/` (desechable, fuera del repo) y sirve de banco para
  reproducir cada hallazgo.

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

En este track lo ejecutamos **empaquetado** como el workflow headless
`bookwright-quality` (§ 0.5), no paso a paso a mano. El flujo manual de arriba queda
como referencia de lo que el workflow corre por dentro.

- **No se salta `/speckit-clarify`.** Cada spec trae el "Fuera de scope" cerrado para
  que `clarify` no se atasque ni derive la decisión.
- **En `/speckit-plan` apóyate en el diseño** y el código existente (consulta el
  índice codegraph antes de grepear).
- **Cada iteración es autocontenida y deja la herramienta funcional.** Ningún branch
  puede dejar `bookwright` rojo a mitad: lo ya mergeado sigue pasando los gates.
- **Cada iteración entrega un delta observable** y **cierra su entrada de DEBT.md**
  (cancelación de deuda, § 0.5).

### 0.3 Numeración

Los `specs/` van por `001`…`033`. Este track arranca en **034** y continúa la
secuencia (034, 035, 036). Cada iteración es un branch `NNN-<short-name>` con su
propio `specs/`.

### 0.4 Versionado de este track — **un patch por iteración**

Decisión: cada iteración corta su propio **patch** (`v0.4.2`, `v0.4.3`, `v0.4.4`), al
estilo del tramo de endurecimiento `v0.3.x` (donde 024–027 se liberaron como
`v0.3.1`…`v0.3.4`) y del patch `v0.4.1`. Razón: los tres hallazgos son
**independientes** y cada uno tiene **un delta observable distinto** (un validador que
despierta; consultas por label/orden habilitadas; mensajes de error accionables), así
que acumularlos en un único minor escondería deltas que merecen su línea de
`CHANGELOG`. No es un hito minor (no abre una capa nueva): es endurecimiento, y el
endurecimiento aquí ships en patches.

### 0.5 Ciclo de cierre de cada iteración

El workflow `bookwright-quality` corre headless y termina con árbol **limpio** en la
branch `NNN-<short-name>`: **no** mergea, **no** versiona, **no** taggea. Por eso cada
iteración tiene un **cierre manual** fijo, idéntico al de 033:

1. **Lanzar el workflow** con el comando de la sección de la iteración (desde `main`
   limpio; el paso `specify` crea la branch). La **cancelación de deuda va dentro del
   spec** (cada spec instruye *"borra DEBT-00N de DEBT.md"* en su comportamiento
   esperado), así que el propio workflow la ejecuta como parte de `implement`.
2. **Verificar** en la branch: los cuatro gates verdes (`finalize` los re-corre) y que
   `DEBT-00N` ya **no** está en `DEBT.md` (git conserva el historial).
3. **Mergear a `main`** replicando el patrón de 033: un commit `Merge iteration NNN: …`
   con `--no-ff` + un commit `docs(claude): record iteration NNN merged` que voltea la
   fila de la tabla de `CLAUDE.md` y la prosa de estado.
4. **Cortar el patch** con la skill `bookwright-release` (`vX.Y.Z`): bump de
   `__version__`, sección de `CHANGELOG`, edición de estado en `CLAUDE.md`/diseño si
   procede, commit de release y tag anotado.

> **Comando del workflow (forma).** Carga los prompts en variables con heredoc
> *entrecomillado* (`<<'EOF'`) para que zsh **no** expanda backticks / `$` / `§`, y
> pásalos como `-i key=value`. Cada iteración de abajo trae su `SPEC` y `PLAN_HINT`
> ya rellenos:
>
> ```bash
> SPEC=$(cat <<'EOF'
> …            # la Necesidad de la iteración, verbatim
> EOF
> )
> PLAN_HINT=$(cat <<'EOF'
> …            # la Pista para /speckit-plan, verbatim
> EOF
> )
> specify workflow run bookwright-quality \
>   -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
> ```
>
> Sigue el run con `specify workflow status`; reintenta un paso fallido con
> `specify workflow resume <run_id>`. **Refresca `SPEC`/`PLAN_HINT` por iteración**:
> un prompt heredado de la corrida anterior es un fallo real (precedente histórico) que
> corrompe el audit-trail.

---

## 1. Origen — el ejercicio de dogfooding (2026-06-21)

Con `v0.4.1` cerrada y la deuda a cero, el siguiente paso de valor no era plumbing
especulativo (lo prohíbe la disciplina de scope) sino **usar la herramienta sobre un
libro real** para que la fricción aflorara. Se autoró "El Cerco de Almenara"
(fantasía histórica, ~10 personajes, settings/localizaciones/objetos, ~20 unidades
narrativas en 3 secuencias con Propp+Greimas activos, research con fuentes/findings/
anchors, timeline y 6 capítulos de manuscrito multi-POV) y se corrió el bucle
`graph build → validate → status → graph query`. Resultado: 49 ficheros, 90
entidades, 1550 triples; los 6 validadores corren; los defectos plantados disparan.
**Los tres hallazgos accionables** (priorizados por valor):

| Pri | Hallazgo | Iteración | Patch | Deuda |
|---|---|---|---|---|
| P0 | `focalization` se autodesactiva con el formato de su propia plantilla (bug de correctitud) | 034 | `v0.4.2` | DEBT-004 |
| P1 | G9 sin `rdfs:label` + `order:` no materializado (gap de recall **medido**) | 035 | `v0.4.3` | DEBT-005 |
| P2 | mensajes de error de research que ciegan al autor (F1 `type`, F2 `access_date`) | 036 | `v0.4.4` | DEBT-006 |

**Mapa de dependencias:** las tres son **independientes**; se ordenan por valor (bug →
gap medido → UX), no por dependencia técnica. Pueden correrse en cualquier orden;
este plan las da 034→035→036.

**Triggers demand-pulled (no se activan en este track):** la **búsqueda vectorial**
no se justifica aún — el dogfooding encontró el paso previo más barato (los labels de
DEBT-005); su trigger real es un corpus multi-libro. El **export** queda *cerca*: el
flujo end-to-end está probado y converge, pero el roadmap pide cerrar antes las
trampas silenciosas (este track lo hace). Ambos siguen en `bookwright-roadmap.md` § 4.

---

## 2. Iteración 034 — `focalization` tolera prefijos markdown (`v0.4.2`, DEBT-004)

**Problema.** El regex de declaración de voz de `focalization`
(`validators/focalization.py:24`) exige la etiqueta al inicio de línea
(`^\s*(?:voz narrativa|narrative voice)\s*:`), pero la plantilla de constitución del
scaffold emite `- **Voz narrativa**: …` (viñeta + negrita markdown), que **no
matchea**. Sin declaración parseable, el validador devuelve cero findings **en
silencio**: queda desactivado para cualquier autor que rellene la constitución tal
como se genera. Verificado: el fixture `tiny-historical` usa ese mismo formato, así
que el validador está dormido también ahí. Es un bug de correctitud / acoplamiento
frágil plantilla↔parser.

**Comando del workflow:**

```bash
SPEC=$(cat <<'EOF'
Necesidad: el validador `focalization` no reconoce la declaración de voz narrativa cuando viene con prefijos markdown, que es justo el formato que la plantilla de constitución del scaffold genera. El regex `_DECLARATION` (src/bookwright/validation/validators/focalization.py) exige la etiqueta al inicio de línea (`^\s*(?:voz narrativa|narrative voice)\s*:`), pero la plantilla emite `- **Voz narrativa**: …` (viñeta + negrita markdown) y NO matchea; sin declaración parseable el validador devuelve cero findings EN SILENCIO y queda desactivado para cualquier autor que rellene la constitución tal como se genera (verificado: el fixture tiny-historical usa ese mismo formato y deja focalization dormido). Queremos que `focalization` tolere los prefijos markdown habituales delante de la etiqueta "Voz narrativa"/"Narrative voice", de modo que la declaración del scaffold se lea y el validador despierte, sin cambiar ninguna otra regla del validador.

Comportamiento esperado:

- El parser tolera viñetas (`-`, `*`, `+`, `>`) y marcadores de énfasis markdown (`*`, `**`, `_`) alrededor de la etiqueta antes de los dos puntos; `- **Voz narrativa**: Tercera persona limitada, centrada en X` se parsea con persona=tercera, limitada, focal=X.
- Sin declaración parseable sigue siendo cero findings (el edge case intacto).
- Un test usa el formato EXACTO del scaffold (src/bookwright/resources/project/bible/constitution.md) y verifica que focalization ya produce findings; se ata plantilla↔parser para que no vuelvan a divergir.
- Si algún fixture (tiny-historical u otro) cambia de comportamiento al despertar focalization, se reconcilia su oracle/expectativa de forma honesta.
- Se borra la entrada DEBT-004 de DEBT.md (git conserva el historial).

Validaciones / no-regresión:

- `uv run pytest` verde; los cuatro gates (ruff check, ruff format --check, mypy --strict, pytest ≥80%) pasan.

Fuera de scope (NO reabrir en clarify):

- Cambiar otras reglas de focalization o sus heurísticas de pronombre/interioridad.
- Tocar la ontología congelada (Principio X): no hay cambio de grafo, es un validador sobre prosa.
- Los demás hallazgos del dogfooding (DEBT-005/006): son sus propias iteraciones.

Referencia: src/bookwright/validation/validators/focalization.py (_DECLARATION); src/bookwright/resources/project/bible/constitution.md. DEBT-004 en DEBT.md. Principio VIII (test discipline).
EOF
)
PLAN_HINT=$(cat <<'EOF'
En `src/bookwright/validation/validators/focalization.py`, amplía `_DECLARATION` para tolerar prefijos markdown antes de la etiqueta — viñetas (`[-*+>]`), espacios y marcadores de énfasis (`*`/`**`/`_`) alrededor de "Voz narrativa"/"Narrative voice" — o, más robusto, normaliza la línea (strip de viñetas y `*_`) antes de aplicar el patrón. No toques las otras reglas (pronombre primera persona, interioridad/head-hopping). Añade un test que lea el formato EXACTO de `src/bookwright/resources/project/bible/constitution.md` (o un fixture que lo replique) y verifique que focalization produce findings, atando plantilla↔parser. Revisa si tiny-historical (cuya constitución usa el mismo formato con viñeta+negrita) cambia al despertar el validador y reconcilia su oracle. Sin clases nuevas (Principio X): es un validador sobre prosa, no toca el grafo. Borra la entrada DEBT-004 de DEBT.md. Verifica `uv run pytest` y los cuatro gates.
EOF
)
specify workflow run bookwright-quality \
  -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
```

**Cierre:** ciclo § 0.5 → merge + `record iteration 034` + `bookwright-release` →
`v0.4.2`. DEBT-004 ya borrada por el workflow; verifícalo.

---

## 3. Iteración 035 — G9 con `rdfs:label` + orden de secuencia consultable (`v0.4.3`, DEBT-005)

**Problema.** La capa narrativa no es consultable por contenido ni por orden. (a) Las
`G9_Narrative_Unit` no emiten `rdfs:label`: su nombre humano vive **solo** en el slug
de la URI, así que ninguna consulta SPARQL por nombre/contenido de beat es posible.
(b) El `order:` declarado se consume al ensamblar la secuencia y **no se materializa**
(`narrative.py:67-68`: "RDF is unordered; the ordering is the caller's tuple order"),
así que SPARQL no puede recuperar el orden de los beats. Medido en dogfooding: las
sondas "lista las funciones en orden de la secuencia X" y "beats sobre <tema>" fallan
estructuralmente. Es el **prerequisito** antes de evaluar búsqueda vectorial.

> **Nota de riesgo (para `/speckit-plan`):** materializar el orden bajo RDF (no
> ordenado) sin clase de ontología nueva es la decisión no trivial de esta iteración
> (§ 4.4 de notas operativas). Si `/speckit-tasks` la infla por encima de ~10 tareas,
> es candidata legítima a split (labels en una, orden en otra).

**Comando del workflow:**

```bash
SPEC=$(cat <<'EOF'
Necesidad: la capa narrativa no es consultable por contenido ni por orden, lo que se midió en el dogfooding. (a) Las G9_Narrative_Unit no emiten `rdfs:label`: su nombre humano (`name`) vive SOLO en el slug de la URI, así que ninguna consulta SPARQL por nombre/contenido de beat es posible. (b) El `order:` declarado en las units se consume al ensamblar la secuencia y NO se materializa como triple (RDF no es ordenado; ver narrative.py: "RDF is unordered; the ordering is the caller's tuple order"), así que SPARQL no puede recuperar el orden de los beats de una secuencia. Queremos materializar (a) `rdfs:label` en las unidades narrativas (y, con el mismo patrón, en las funciones narrativas si encaja) con su `name` autorado, y (b) un ordinal CONSULTABLE de la membresía de secuencia que refleje el `order:` declarado, de modo que el orden de los beats sea recuperable por SPARQL — cerrando el gap de recall medido y habilitando consultas por nombre y por orden. Este es el prerequisito antes de cualquier evaluación de búsqueda vectorial (horizonte demand-pulled); la búsqueda vectorial NO entra aquí.

Comportamiento esperado:

- Cada G9_Narrative_Unit emite `rdfs:label` con su `name`, siguiendo el mismo patrón de dos triples que CharacterRole / E55_Type ya usan. Idem G10_Narrative_Function si aplica el mismo patrón.
- La membresía de secuencia (`dlp:proper-part`) gana un ordinal CONSULTABLE que refleja el `order:` declarado de cada unit dentro de su NarrativeSequence — SIN introducir una clase de ontología nueva (Principio X): usar rdfs:label y un mecanismo de orden (p.ej. reificar la membresía con un índice entero, o un predicado de orden permitido) que no exija clase nueva.
- Una consulta SPARQL puede (i) encontrar una unit por su label y (ii) listar las units de una secuencia EN SU ORDEN declarado. Se incluyen ambas consultas como prueba.
- Procedencia: el label/orden se reifican por el path E13 existente cuando corresponda, como el resto de aserciones GOLEM.
- Se borra la entrada DEBT-005 de DEBT.md (git conserva el historial).

Validaciones / no-regresión:

- El resto del grafo sigue emitiendo los mismos triples; los validadores existentes (incluido narrative_structure, que cita units) siguen verdes.
- `uv run pytest` verde y los cuatro gates pasan.

Fuera de scope (NO reabrir en clarify):

- Búsqueda vectorial (ChromaDB): es el horizonte demand-pulled, no este track.
- Cualquier clase o propiedad NUEVA en golem.ttl (Principio X): usar rdfs:label y un mecanismo de orden que no requiera clase nueva.
- Cambiar el formato de autoría de las units (name/functions/roles/sequence/order intactos).
- Los demás hallazgos del dogfooding (DEBT-004/006).

Referencia: src/bookwright/golem/modules/narrative.py (NarrativeUnit, NarrativeSequence; FR-015 "in declared order"); bookwright-design.md § 7.4. Patrón de tipado de CharacterRole / E55_Type para los dos triples de label. DEBT-005 en DEBT.md. Principio X (ontología congelada), Principio I (texto plano).
EOF
)
PLAN_HINT=$(cat <<'EOF'
Dos piezas en `src/bookwright/golem/modules/narrative.py`. (1) Labels: emite `rdfs:label` en `NarrativeUnit` (y `NarrativeFunction`) con su `name`, siguiendo el patrón de dos triples de CharacterRole / E55_Type (no inventes mecanismo nuevo). (2) Orden — el reto real, bajo RDF no-ordenado, SIN clase de ontología nueva (Principio X): elige entre reificar cada membresía `dlp:proper-part` con un nodo intermedio que lleve un índice entero (más triples, plenamente consultable) o emitir un predicado de orden por unit dentro de la secuencia usando un predicado existente/permitido; justifica la elección contra Principio X en /speckit-plan. Mantén la procedencia E13 donde aplique y la no-regresión del resto del grafo (narrative_structure y demás validadores verdes). Verifica con dos consultas SPARQL: una que encuentre una unit por label, otra que liste las units de una secuencia en orden. Apóyate en narrative.py y design § 7.4. Si /speckit-tasks pasa de ~10 tareas, considera split (labels / orden). Borra la entrada DEBT-005 de DEBT.md. `uv run pytest` y los cuatro gates verdes.
EOF
)
specify workflow run bookwright-quality \
  -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
```

**Cierre:** ciclo § 0.5 → merge + `record iteration 035` + `bookwright-release` →
`v0.4.3`. DEBT-005 ya borrada por el workflow; verifícalo.

---

## 4. Iteración 036 — mensajes de error de research accionables (`v0.4.4`, DEBT-006)

**Problema.** El dogfooding sobre un libro real expuso mensajes de error que ciegan al
autor. (F1) cuando una fuente declara un `type` fuera del vocabulario cerrado, el
error nombra el valor inválido pero **no enumera los aceptados**, obligando a iterar a
ciegas. (F2) cuando `access_date` se escribe entrecomillado (string en vez de fecha
YAML), el error `Input should be a valid date` **no nombra qué fuente** de la lista
falló ni que la causa son las comillas. (Footgun relacionado: un typo de
clase/predicado en `graph query` devuelve resultado vacío indistinguible de "no hay
datos" — se documenta, no es un fix de mensaje localizado.)

**Comando del workflow:**

```bash
SPEC=$(cat <<'EOF'
Necesidad: el dogfooding sobre un libro real expuso mensajes de error en la carga de fuentes de research que ciegan al autor. (F1) cuando una fuente de `bible/research/sources.md` declara un `type` fuera del vocabulario cerrado (primaria|secundaria|oficial|académica|periodística|testimonial), el error nombra el valor inválido pero NO enumera los valores aceptados, obligando a iterar a ciegas. (F2) cuando `access_date` se escribe entrecomillado (string en vez de fecha YAML nativa), el error "Input should be a valid date" NO nombra QUÉ fuente de la lista falló ni que la causa son las comillas, dejando al autor sin saber qué fila arreglar. Queremos que ambos errores sean accionables: enumerar el vocabulario válido de `type`, e incluir el identificador de la fuente (su `name`, o el índice 1-based si no hay name) en los errores por-fuente, de modo que un autor sepa exactamente qué arreglar y dónde.

Comportamiento esperado:

- El error de `type` inválido lista los valores aceptados del vocabulario cerrado.
- Los errores de carga de una fuente individual anteponen el identificador de la fuente (su `name` si está, o el índice 1-based en la lista `sources:`) para localizar la fila en sources.md.
- El footgun de SPARQL (un typo de clase/predicado en `graph query` devuelve vacío sin aviso) se DOCUMENTA (no se arregla con un mensaje localizado): una nota breve en la doc/ayuda de `graph query` o en docs, advirtiendo que un IRI inexistente devuelve cero filas, no un error.
- Cobertura de test para ambos mensajes mejorados (F1 y F2).
- Se borra la entrada DEBT-006 de DEBT.md (git conserva el historial).

Validaciones / no-regresión:

- `uv run pytest` verde y los cuatro gates pasan.
- El envelope JSON de error unificado (Principio IX, iteraciones 018/027) NO se rediseña: solo mejora el `message`/`details`, manteniendo el contrato `{status, code, message[, details]}`.

Fuera de scope (NO reabrir en clarify):

- Rediseñar el envelope JSON de error o el esquema de fuentes.
- "Arreglar" el footgun de SPARQL con validación de IRIs (consulta arbitraria): solo se documenta.
- Los demás hallazgos del dogfooding (DEBT-004/005).

Referencia: el loader/modelo de fuentes de research (p.ej. src/bookwright/io/research.py + el modelo Pydantic Source y su vocabulario de `type`). El envelope de error en errors.py (Principio IX). DEBT-006 en DEBT.md.
EOF
)
PLAN_HINT=$(cat <<'EOF'
Localiza dónde se valida/parsea la lista `sources:` (probablemente `src/bookwright/io/research.py` + el modelo Pydantic `Source` y el enum/literal de `type`). Para F1: captura el error de `type` inválido (ValueError/enum de pydantic) y reescribe el `message` para ENUMERAR los miembros válidos del vocabulario cerrado. Para F2: envuelve la validación por-fuente para anteponer el `name` (o el índice 1-based en la lista) al error de pydantic, de modo que el autor sepa qué fuente falló. Mantén el envelope `{status, code, message[, details]}` (Principio IX, errors.py) — solo mejora el texto, no rediseñes el contrato. Para el footgun de SPARQL, añade una nota breve en la ayuda de `graph query` o en docs (un IRI inexistente devuelve cero filas, no un error); no añadas validación de IRIs sobre consulta arbitraria. Tests que disparen ambos errores y comprueben el texto mejorado. Borra la entrada DEBT-006 de DEBT.md. `uv run pytest` y los cuatro gates verdes.
EOF
)
specify workflow run bookwright-quality \
  -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
```

**Cierre:** ciclo § 0.5 → merge + `record iteration 036` + `bookwright-release` →
`v0.4.4`. DEBT-006 ya borrada por el workflow; verifícalo. Con las tres entradas
cerradas, `DEBT.md` vuelve a quedar vacío y el track `v0.4.x` post-dogfooding termina.

---

## 5. Notas operativas

### 5.1 Manejo de spec rechazadas

Si tras `/speckit-analyze` aparecen issues de consistencia entre spec/plan/tasks,
vuelve a `/speckit-clarify` o edita `spec.md` directamente, regenera plan y tasks, y
vuelve a analizar. No fuerces `/speckit-implement` con análisis con errores. (En el
workflow headless, el paso `analyze-resolve` lo hace solo contra la constitución.)

### 5.2 Iteraciones que se complican

Si una iteración crece más de lo previsto durante `/speckit-tasks` (más de ~10
tareas), divídela en dos specs. En este track, la candidata clara a split es la **035**
(labels + orden): si el mecanismo de orden bajo RDF se complica, sepáralo de los
labels.

### 5.3 Cambios en el documento de diseño

El diseño es la fuente de verdad técnica. Si durante la implementación algo del diseño
no encaja con la realidad técnica, actualiza `bookwright-design.md` **antes** de
divergir el código, y registra el cambio en `CHANGELOG` bajo "Design decisions revised
during implementation". Las decisiones de § 16 son inmutables.

### 5.4 Cuándo pedir ayuda al humano

Spec Kit genera bien spec/plan/tasks pero puede divagar en decisiones de diseño no
triviales — en este track, **el mecanismo de orden consultable de la 035** es la
decisión sensible (cómo materializar orden bajo RDF sin clase nueva). Cuando dudes,
ejecuta `/speckit-clarify` o intervén manualmente; redirige al diseño / roadmap.

### 5.5 Tras este track

Cuando 034–036 estén mergeadas y liberadas (`v0.4.2`…`v0.4.4`) y `DEBT.md` vacío, no
hay siguiente hito con número de versión asignado: vuelve el **horizonte
demand-pulled** (`bookwright-roadmap.md` § 4 y `DEBT.md`) — búsqueda vectorial (ahora
desbloqueada por los labels de 035, pero con trigger real = corpus multi-libro),
export (cerca: el flujo end-to-end ya converge), y G6/G3. Cuando un disparador active
el siguiente hito, asígnale versión, **vacía y redacta de nuevo este plan** (arrancando
en `specs/037-…`) y mantén `bookwright-roadmap.md` como la intención durable. Quedan
descartados: presets, GrafeoIndexer/Grafeo, multi-integración y extension system; ver
`bookwright-design.md` § 15.5.

---

**Fin del plan.**
