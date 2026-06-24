# Bookwright — Plan de implementación con Spec Kit

> **Documento complementario a:** `bookwright-design.md` (el *cómo* técnico) y
> `bookwright-roadmap.md` (el *qué* y *por qué* a lo largo de versiones).
> **Propósito:** secuencia de iteraciones para el **hito en curso** de Bookwright.
> Cada iteración trae su prompt y el **comando del workflow** listo para ejecutar.
> **Audiencia:** Jorge (o cualquier desarrollador con Spec Kit instalado y
> `bookwright-design.md` en el root del repo).

> **Hito en curso: el track del move 3 — juicio semántico en validación** (norte
> activado por la issue #1, **reforzado por el 3er dogfood**), que **continúa la cadencia
> `v0.5.x`** (un patch por slice observable, no un minor diferido). La honestidad +
> pulido determinista de la issue #1 (043–050, `v0.5.3`…`v0.5.9`) están **liberados**, y
> la **primera rebanada del move 3 ya aterrizó** (051, `v0.5.10`, 2026-06-24): el detalle
> vive en git, `specs/043…051` y `CHANGELOG` — **no** aquí (este documento se vacía del
> trabajo entregado al cerrar cada hito; conserva el andamiaje reutilizable, § 0 y § 7).
>
> Un **3er dogfood end-to-end** —`el-año-de-las-casas-vacías`, novela literaria multi-POV
> en 3ª persona limitada, 2026-06-24, banco desechable fuera del repo— corrió sobre
> `v0.5.9` para **decidir con evidencia la próxima roca grande**: move 3 vs. onboarding. El
> género se eligió para estresar lo que los dos previos (histórica + negra, ambas 3ª) no
> tocaron: focalización/head-hopping a tope y el path de **ruptura de 1ª persona que la
> iteración 050 (re)activó** y que ningún fixture ejercita. **Veredicto: move 3.** Evidencia
> (registrada en `bookwright-roadmap.md` § 5 y `DEBT.md`):
>
> 1. **El canal de honestidad (track A) es impecable** sobre prosa real: 2 abstenciones,
>    ambas `pending_capability`, cero ruido; el verde es alcanzable y fiable (probado: con
>    los errores plantados arreglados, `failed:false`, exit 0).
> 2. **El hueco semántico MUERDE con señal real perdida, no teórica:** un personaje
>    usado-pero-no-declarado (`Amelia`, 4 menciones, sin ficha) y un head-hopping real
>    quedan **invisibles**, abstenidos en el mismo gesto que (bien) silencia orgs/topónimos.
>    La única respuesta determinista honesta no separa ruido de señal; sólo el juicio
>    semántico lo hace.
> 3. **Onboarding no aportó muro nuevo:** el flujo `init→autoría→graph→validate→status` fue
>    sin fricción; la fricción documentada es la cadena externa (condición de activación aún
>    no disparada). Sigue demand-pulled (`bookwright-roadmap.md` § 5), no adelantado.
>
> **Hallazgo nuevo → DEBT-021 (NO determinista):** el chequeo de ruptura de 1ª persona de
> `focalization` casa el **pronombre sujeto explícito** (`yo`/`nosotros`) —conjunto cerrado,
> sólido— pero "¿esta prosa **está** en 1ª persona?" es conjunto abierto: en español pro-drop
> la forma natural es la **morfología verbal** sin pronombre (`Caminé`, `Me senté`), que
> **ningún** regex captura sin reabrir el whack-a-mole. Es la **misma clase** que el
> head-hopping y las menciones-desconocidas: techo **semántico** → move 3, no un patch.
>
> **El frente es un solo track: C — move 3** (la roca grande, **diseño-primero**: su frontera
> ya está decidida en `design` § 20.6.1, falta la spec que la aterrice). Los tracks A
> (honestidad) y B (pulido determinista) están **cerrados** — el 3er dogfood **no encontró
> nada cheaply-fixable en determinista**: las tres deudas abiertas (DEBT-013 orgs, DEBT-021
> recall 1ª persona, y el head-hopping) son la misma cara del techo de conjunto abierto.
>
> **Qué viene tras el move 3:** el resto del **horizonte demand-pulled**
> (`bookwright-roadmap.md` § 5) sin versión asignada — búsqueda vectorial (trigger = corpus
> multi-libro/serie o recall medido; **enchufa en el grounding del move 3**, principio 2 de
> § 20.6.1), export a EPUB/PDF/print (trigger = flujo end-to-end probado), onboarding de un
> comando / `bookwright doctor` (trigger = 2º autor no-técnico real), y los diferidos G6/G3
> (`RelationshipRole`, `PsychologicalState`). Ninguno arranca como plumbing especulativo.

---

## 0. Estado y cómo usar este documento

### 0.1 Punto de partida (al abrir un hito nuevo)

Antes de redactar las iteraciones de un hito nuevo, fija el punto de partida:

- Verifica que `main` esté limpio y tageado en la última release, con los cuatro
  gates verdes (`uv run ruff check && uv run ruff format --check`, `uv run mypy
  --strict`, `uv run pytest`). **Hoy: `v0.5.9` en `main`, cuatro gates verdes.**
- El repo ya está inicializado con Spec Kit (`.specify/`, `.claude/skills/speckit-*`)
  y su constitución ratificada (`.specify/memory/constitution.md`). **No** se
  re-bootstrapea ni se reabre ningún axioma de `bookwright-design.md` § 16.
- El **registro de diferidos** (`src/bookwright/golem/deferrals.py`) y su **test de
  paridad** (`tests/golem/test_ingestion_parity.py`) declaran los conceptos
  modelados-pero-no-alimentados. Hoy solo dos, ambos demand-pulled: `RelationshipRole`
  (G6) y `PsychologicalState` (G3). Un hito que alimente uno debe sacarlo de ahí.
- Si el hito nace de un **dogfooding** o de deuda registrada, enlaza el origen
  (`DEBT.md`, una issue de `design`/`discussion`, o un banco de pruebas desechable
  fuera del repo) en § 1 antes de redactar las iteraciones. **El frente actual nace del
  3er dogfood (`el-año-de-las-casas-vacías`) → `DEBT.md` (DEBT-021, DEBT-013) y
  `bookwright-roadmap.md` § 5.**

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

Se puede ejecutar **empaquetado** como el workflow headless `bookwright-quality`
(§ 0.4), no paso a paso a mano. El flujo manual de arriba queda como referencia de lo
que el workflow corre por dentro.

- **No se salta `/speckit-clarify`.** Cada spec trae el "Fuera de scope" cerrado para
  que `clarify` no se atasque ni derive la decisión.
- **En `/speckit-plan` apóyate en el diseño** y el código existente (consulta el
  índice codegraph antes de grepear).
- **Cada iteración es autocontenida y deja la herramienta funcional.** Ningún branch
  puede dejar `bookwright` rojo a mitad: lo ya mergeado sigue pasando los gates.
- **Cada iteración entrega un delta observable** y, si cancela deuda, **cierra su
  entrada de `DEBT.md`** (§ 0.4).
- **Numeración:** los `specs/` van por `001`…`050`. La continuación arranca en **051** y
  sigue la secuencia. Cada iteración es un branch `NNN-<short-name>` con su propio
  `specs/`.

### 0.3 Versionado — patch vs. minor

Decide por hito, no por iteración:

- **Endurecimiento** (cancelar deuda, cerrar atajos, sin abrir capa nueva) → **un
  patch por iteración** con un delta observable cada uno, al estilo de `v0.3.x`
  (024–027 → `v0.3.1`…`v0.3.4`), `v0.4.x` (034–038 → `v0.4.2`…`v0.4.6`) y `v0.5.x`
  (041–051 → `v0.5.1`…`v0.5.10`). Acumular hallazgos independientes en un único minor
  escondería deltas que merecen su línea de `CHANGELOG`. **Los slices del move 3 caen aquí:**
  cada uno es un delta observable y útil por sí solo (el primer slice, 051→`v0.5.10`, ya hace
  visible el personaje sin declarar), así que ship como **patch** en la cadencia `v0.5.x`, no
  acumulando hacia un minor.
- **Capa nueva** (un sistema modelado que cobra vida) → las iteraciones **acumulan en
  `main`** y se liberan **una sola vez** como **minor** al cierre, al estilo de
  M4→`v0.2.0`, M5→`v0.3.0` y v0.4→`v0.4.0`. (El move 3 **no** entra aquí: sus slices son
  útiles por separado, así que ship como patches — ver arriba. `v0.6.0`/`1.0` se gana con
  un hito mayor o el flujo end-to-end probado, no se pre-asigna al move 3.)

### 0.4 Ciclo de cierre de cada iteración

El workflow `bookwright-quality` corre headless y termina con árbol **limpio** en la
branch `NNN-<short-name>`: **no** mergea, **no** versiona, **no** taggea. Por eso cada
iteración tiene un **cierre manual** fijo:

1. **Lanzar el workflow** con el comando de la sección de la iteración (desde `main`
   limpio; el paso `specify` crea la branch). Si la iteración cancela deuda, la
   **cancelación va dentro del spec** (cada spec instruye *"borra DEBT-00N de
   DEBT.md"* en su comportamiento esperado), así que el propio workflow la ejecuta
   como parte de `implement`.
2. **Verificar** en la branch: los cuatro gates verdes (`finalize` los re-corre) y,
   si aplica, que `DEBT-00N` ya **no** está en `DEBT.md` (git conserva el historial).
3. **Mergear a `main`** replicando el patrón de la iteración anterior: un commit
   `Merge iteration NNN: …` con `--no-ff` + un commit `docs(claude): record iteration
   NNN merged` que voltea la fila de la tabla de `CLAUDE.md` y la prosa de estado.
4. **Cortar la release** con la skill `bookwright-release` (`vX.Y.Z`): bump de
   `__version__`, sección de `CHANGELOG`, edición de estado en `CLAUDE.md`/diseño si
   procede, commit de release y tag anotado. (En un hito minor, este paso se hace una
   sola vez, al cierre del hito.)

> **Comando del workflow (forma).** Carga los prompts en variables con heredoc
> *entrecomillado* (`<<'EOF'`) para que zsh **no** expanda backticks / `$` / `§`, y
> pásalos como `-i key=value`:
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
> corrompe el audit-trail. **No copies un sketch a ciegas — pídeme el comando de la
> iteración que vayas a lanzar y lo regenero verificado contra el código vigente** (es
> donde se colaron los descuidos que la revisión de mitad del track `v0.5.x` pilló:
> refs a símbolos borrados, `kind` omitido, reglas no listadas).

---

## 1+. Frente actual y lo que queda

> **✅ `v0.5.x`, track de la issue #1: 043–051 liberados (`v0.5.3`–`v0.5.10`, 2026-06-24).**
> Honestidad + pulido determinista (043–050: 043 menciones-desconocidas→abstainer · 044 categorías
> de `not_evaluated` + verde alcanzable · 045 head-hopping→`not_evaluated` · 046 `validate` propaga
> `skipped` · 047 vocab Propp/Greimas no fatal · 048 locators · 049 nombre-vs-slug · 050 contrato
> `EvalResult`) **y la primera rebanada del move 3** (051: `bookwright-continuity` juzga el
> personaje-usado-pero-no-declarado + `status` nudge `judge_undeclared_characters`; cierra DEBT-013).
> Detalle en `CHANGELOG`/git/`specs/043…051`. **No relanzar.**

**Lo que queda abierto** (origen: 3er dogfood `el-año-de-las-casas-vacías`, 2026-06-24): **el move 3
continúa** (§ 1.C). El primer slice (051, personaje-sin-declarar) cerró **DEBT-013** y restauró la
señal que el dogfood midió perdida (`Amelia`); quedan las **otras dos dimensiones**, la **misma cara**
del techo semántico de conjunto abierto:

- **DEBT-021 (recall de ruptura de 1ª persona)** — "¿esta prosa está en 1ª persona?" en español
  pro-drop es morfología verbal, conjunto abierto; ningún regex lo captura sin whack-a-mole. El
  núcleo determinista sólido (`yo`/`nosotros`) se conserva (determinismo añade, no suprime).
- **El head-hopping real** — `focalization` ya **abstiene** de él (`pending_capability`); su
  techo de precisión es el mismo juicio semántico.

Ambas siguen el patrón que **051 ya probó** (la skill responde a la `Abstention` del canal
`not_evaluated`, anclada en el grafo) — cada una es su propio slice/patch en la cadencia `v0.5.x`.

> Cuando el move 3 produzca iteraciones, cada una es un branch `NNN-<short-name>` con su
> `specs/`, que **borra la(s) entrada(s) de `DEBT.md`** que cierra (§ 0.4). **Pídeme el comando
> de la que vayas a lanzar y lo regenero verificado contra el código vigente** (§ 0.4).

---

## 1.C — Track del move 3 (juicio semántico) — la roca grande, diseño-primero

El 2º dogfood **cumplió la condición de activación** del move 3 (un heurístico concreto medido
insuficiente sobre prosa real: 4/4 FP) y el **3er dogfood la reforzó** con señal real **perdida,
no teórica**: sobre prosa literaria fresca, un personaje usado-pero-no-declarado (`Amelia`) y un
head-hopping real quedaron **invisibles**, abstenidos en el mismo gesto que (correctamente)
silencia orgs y topónimos. Es el **norte del track de validación**. La frontera (§ 20.6.1) y el
**contrato concreto** (§ 20.6.2) están decididos, y el **primer slice ya aterrizó** (051,
`v0.5.10`, 2026-06-24): el personaje-usado-pero-no-declarado. Siguen las otras dos dimensiones.

- **Qué cura:** el conjunto abierto entero que el track A dejó honesto-pero-en-`not_evaluated` —
  menciones-desconocidas (orgs/topónimos/vocativos/**personaje-sin-declarar**, DEBT-013 incluida),
  el head-hopping real (techo de precisión cerrado en honestidad por 045/050) y el **recall de
  ruptura de 1ª persona** (DEBT-021: la morfología verbal pro-drop que ningún regex captura)—
  escalando a juicio semántico **anclado en el grafo** (grounding). Las tres son la misma cara
  del techo de conjunto abierto. Restaura la **señal** que el `not_evaluated` deja pendiente, sin
  reintroducir el ruido. Los núcleos deterministas sólidos **se conservan** como confirmación de
  bajo coste (principio 3, determinismo añade): los huérfanos (`error`, el gate), el pronombre
  sujeto explícito (`yo`/`nosotros`) de `focalization`, las relaciones temporales del grafo.
- **La frontera YA está decidida** (issue #1, 2026-06-24; `bookwright-design.md` § 20.6.1, 4
  principios — transcrita, Principio I): (1) la frontera es el **sustrato** (grafo determinista
  vs. prosa LLM), no la dificultad; (2) **LLM-primero anclado en el grafo** (grounding; ahí
  enchufa la búsqueda vectorial del horizonte); (3) el determinismo **añade** confianza o ahorra
  coste pero **nunca suprime** un candidato (mató el "regex pre-filtro → LLM juez"); (4) separar
  **juicio** (LLM, informativo, no rompe CI, estilo `bookwright-verify`) de **gate** (determinista
  o veredictos LLM cacheados/golden-runs). La iteración 050 ya materializó el principio 3 a nivel
  de sub-comprobación (`focalization` corre lo determinista Y abstiene lo semántico en un run).
- **El contrato (decidido, `bookwright-design.md` § 20.6.2):** (1) **superficie** — se **extiende
  `bookwright-continuity`** (su mandato ya es manuscrito-vs-canon, anclado en el grafo), no se añade
  skill nuevo; (2) **el canal `not_evaluated` ES el contrato** entre capas — cada `Abstention`
  (`pending_capability`) que `validate` publica es una tarea de juicio que continuity recoge; (3)
  **grounding** — el roster (personaje-sin-declarar) y la voz declarada (focalización/1ª persona) se
  inyectan como contexto; los núcleos deterministas se conservan; (4) **juicio, NO gate** (en
  cada slice, cadencia `v0.5.x`) — el veredicto es informativo (no rompe CI); el gate sigue siendo
  `validate` determinista; gatear veredictos LLM (golden-runs/caché por hash) queda **diferido** con
  su propia condición.
- **Aterrizado — slice 1 (051, `v0.5.10`): personaje-usado-pero-no-declarado.** Probó la tubería
  entera (`validate` abstiene → `bookwright-continuity` recoge la `Abstention` → juzga anclado en el
  roster → reporta; `status` añade el nudge `judge_undeclared_characters`), con el grounding más
  simple (sólo el roster) y la señal más fuerte del 3er dogfood (`Amelia`). Cerró DEBT-013.
- **Siguiente slice — head-hopping o ruptura de 1ª persona (DEBT-021).** Mismo patrón que 051: la
  skill responde a la `Abstention` correspondiente de `focalization`, anclada en la voz declarada +
  el personaje focal del grafo; veredicto informativo, gate intacto. Es su propio patch en la
  cadencia `v0.5.x`. **Pídeme el `SPEC`/`PLAN_HINT` del siguiente slice y lo regenero verificado
  contra el código vigente** (§ 0.4). El interim honesto del track A (declarar `not_evaluated`,
  `kind=pending_capability`) sigue siendo el fallback correcto y permanente si el path LLM no corre.

---

## 7. Notas operativas

### 7.1 Manejo de spec rechazadas

Si tras `/speckit-analyze` aparecen issues de consistencia entre spec/plan/tasks,
vuelve a `/speckit-clarify` o edita `spec.md` directamente, regenera plan y tasks, y
vuelve a analizar. No fuerces `/speckit-implement` con análisis con errores. (En el
workflow headless, el paso `analyze-resolve` lo hace solo contra la constitución.)

### 7.2 Iteraciones que se complican

Si una iteración crece más de lo previsto durante `/speckit-tasks` (más de ~10
tareas), divídela en dos specs.

### 7.3 Cambios en el documento de diseño

El diseño es la fuente de verdad técnica. Si durante la implementación algo del diseño
no encaja con la realidad técnica, actualiza `bookwright-design.md` **antes** de
divergir el código, y registra el cambio en `CHANGELOG` bajo "Design decisions revised
during implementation". Las decisiones de § 16 son inmutables.

### 7.4 Cuándo pedir ayuda al humano

Spec Kit genera bien spec/plan/tasks pero puede divagar en decisiones de diseño no
triviales. Cuando dudes, ejecuta `/speckit-clarify` o intervén manualmente; redirige
al diseño / roadmap.

---

**Fin del plan.**
