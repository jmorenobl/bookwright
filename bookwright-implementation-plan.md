# Bookwright — Plan de implementación con Spec Kit

> **Documento complementario a:** `bookwright-design.md` (el *cómo* técnico) y
> `bookwright-roadmap.md` (el *qué* y *por qué* a lo largo de versiones).
> **Propósito:** secuencia de iteraciones para el **hito en curso** de Bookwright.
> Cada iteración trae su prompt y el **comando del workflow** listo para ejecutar.
> **Audiencia:** Jorge (o cualquier desarrollador con Spec Kit instalado y
> `bookwright-design.md` en el root del repo).

> **No hay hito versionado abierto.** La **primera ola del move 3 — juicio semántico en
> validación** está **completa y liberada**: las tres dimensiones del techo de conjunto
> abierto que la issue #1 dejó honestas-pero-en-`not_evaluated` ya **escalan a juicio**
> anclado en el grafo —personaje usado-pero-no-declarado (051, `v0.5.10`, cierra DEBT-013),
> head-hopping bajo 3ª limitada (052, `v0.5.11`), y ruptura de 1ª persona / recall pro-drop
> (honestidad 053 `v0.5.12` + juicio 054 `v0.5.13`, cierra DEBT-021)—. El detalle vive en
> git, `specs/051…054` y `CHANGELOG` — **no** aquí (este documento se vacía del trabajo
> entregado al cerrar cada hito; conserva el andamiaje reutilizable, § 0 y § 7). **DEBT.md
> está vacío.**
>
> **Frente actual: el horizonte demand-pulled** (`bookwright-roadmap.md` § 5), sin versión
> asignada — ninguno arranca como plumbing especulativo, cada uno espera su condición de
> activación: búsqueda vectorial (trigger = corpus multi-libro/serie o recall medido;
> **enchufa en el grounding del move 3**, principio 2 de § 20.6.1), export a EPUB/PDF/print
> (trigger = flujo end-to-end probado), onboarding de un comando / `bookwright doctor`
> (trigger = 2º autor no-técnico real), una **2ª ola del move 3** (trigger = señal real
> perdida medida en autoría genuina, no un sondeo plantado — ver abajo), y los diferidos
> G6/G3 (`RelationshipRole`, `PsychologicalState`).
>
> **4º dogfood (`la-hora-del-eclipse`, banco desechable, 2026-06-25) — verdicto:** la
> primera ola es **sana sobre prosa fresca** — un capítulo en 3ª limitada con tres defectos
> plantados (personaje sin declarar, head-hopping, y ruptura de 1ª persona **pro-drop sin
> «yo» explícito**) los abstiene los tres en el canal `not_evaluated` y `status` emite los
> tres nudges, incluido el 6º eje recién shippeado (054). La señal que el 3er dogfood midió
> perdida **ya no se pierde**. El sondeo además observó tres dimensiones semánticas que la
> capa determinista **no ve ni abstiene** —deriva de tiempo verbal vs. el tiempo declarado,
> contradicción de un rasgo declarado del personaje, y ruptura de una línea roja
> (deus ex machina)—: son **dimensiones sin semilla** (ningún heurístico abstiene → no hay
> `Abstention` → no hay nudge → invisibles, peor que una abstención honesta). **NO se
> promueven a DEBT ni a iteración:** son defectos que yo planté en un fixture, no señal
> real perdida en autoría genuina; la barra de activación del move 3 (§ 20.6.1) exige lo
> segundo. Queda como **observación de dirección** en `bookwright-roadmap.md` § 5, pendiente
> de confirmación por un dogfood real, no como compromiso.

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

> **✅ `v0.5.x`, track de la issue #1: 043–054 liberados (`v0.5.3`–`v0.5.13`, 2026-06-24/25).**
> Honestidad + pulido determinista (043–050: 043 menciones-desconocidas→abstainer · 044 categorías
> de `not_evaluated` + verde alcanzable · 045 head-hopping→`not_evaluated` · 046 `validate` propaga
> `skipped` · 047 vocab Propp/Greimas no fatal · 048 locators · 049 nombre-vs-slug · 050 contrato
> `EvalResult`) **y la primera ola completa del move 3** (051 personaje-usado-pero-no-declarado,
> cierra DEBT-013 · 052 head-hopping bajo 3ª limitada · 053 honestidad de recall de 1ª persona + el
> discriminador `code` · 054 juicio de ruptura de 1ª persona, cierra DEBT-021). Detalle en
> `CHANGELOG`/git/`specs/043…054`. **No relanzar.**

**No queda nada abierto en el track de la issue #1.** Las **tres dimensiones** del techo semántico
de conjunto abierto que el 3er dogfood midió perdidas (`el-año-de-las-casas-vacías`, 2026-06-24) ya
escalan a juicio anclado en el grafo: personaje-sin-declarar (051), head-hopping (052) y ruptura de
1ª persona / recall pro-drop (053 honestidad + 054 juicio). **DEBT-013 y DEBT-021 cerradas; `DEBT.md`
vacío.** El 4º dogfood (`la-hora-del-eclipse`, 2026-06-25) confirmó la ola sana sobre prosa fresca
(los tres defectos abstienen y nudgean, incluido el 6º eje de 054) y dejó una **observación de
dirección** —dimensiones semánticas sin semilla (tiempo verbal, rasgo declarado, línea roja)— en
`bookwright-roadmap.md` § 5, **no** promovida a deuda ni a iteración por ser sondeo plantado, no
señal real perdida (la barra de activación, § 20.6.1, exige lo segundo).

> El frente pasa al **horizonte demand-pulled** (`bookwright-roadmap.md` § 5). Cuando una condición
> de activación se dispare, su iteración es un branch `NNN-<short-name>` con su `specs/`, que **borra
> la(s) entrada(s) de `DEBT.md`** que cierre (§ 0.4). **Pídeme el comando de la que vayas a lanzar y
> lo regenero verificado contra el código vigente** (§ 0.4).

---

## 1.C — Track del move 3 (juicio semántico) — primera ola COMPLETA (registro histórico)

> **Cerrado con `v0.5.13` (2026-06-25).** La primera ola del move 3 entregó sus **tres
> dimensiones** (051–054); el `DEBT.md` de la issue #1 está vacío. Se conserva esta sección como
> registro del diseño-primero que guió la ola; la frontera (§ 20.6.1) y el contrato (§ 20.6.2)
> son canónicos en `bookwright-design.md`, no aquí. Una **2ª ola** sólo arranca con su condición
> de activación (señal real perdida medida en autoría genuina) — horizonte demand-pulled, banner
> arriba y `bookwright-roadmap.md` § 5.

El 2º dogfood **cumplió la condición de activación** del move 3 (un heurístico concreto medido
insuficiente sobre prosa real: 4/4 FP) y el **3er dogfood la reforzó** con señal real **perdida,
no teórica**: sobre prosa literaria fresca, un personaje usado-pero-no-declarado (`Amelia`) y un
head-hopping real quedaron **invisibles**, abstenidos en el mismo gesto que (correctamente)
silencia orgs y topónimos. Fue el **norte del track de validación**. La frontera (§ 20.6.1) y el
**contrato concreto** (§ 20.6.2) quedaron decididos, y la **primera ola completa aterrizó**
(051–054, `v0.5.10`–`v0.5.13`): las tres dimensiones del techo de conjunto abierto.

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
- **Aterrizado — la ola completa (051–054), mismo patrón en las tres:** `validate` abstiene
  (`pending_capability`) → `bookwright-continuity` recoge la `Abstention` del canal `not_evaluated`,
  anclada en el grafo → juzga → reporta; `status` añade un nudge por dimensión. (051,
  personaje-sin-declarar, grounding = roster, cierra DEBT-013; 052, head-hopping, grounding = voz
  declarada + calendario POV + roster, bajo 3ª limitada; 053+054, ruptura de 1ª persona, grounding =
  voz declarada **solo** —es persona gramatical, no identidad—, bajo cualquier 3ª, cierra DEBT-021.)
  El interim honesto del track A (declarar `not_evaluated`, `kind=pending_capability`) sigue siendo
  el fallback correcto y permanente si el path LLM no corre.
- **Observación del 4º dogfood — dimensiones sin semilla (NO activadas).** El contrato del move 3
  sólo escala dimensiones que **ya** tienen un heurístico determinista que abstiene y siembra el
  canal `not_evaluated`. Una dimensión semántica **sin semilla** (deriva de tiempo verbal vs. el
  declarado, contradicción de rasgo declarado, ruptura de línea roja) nunca llega al canal → no hay
  nudge → es invisible. Es una verdad estructural real, pero su urgencia está **sin probar**: salió
  de un sondeo plantado, no de señal real perdida. Queda como dirección en `bookwright-roadmap.md`
  § 5; una 2ª ola (p. ej. un eje de tiempo verbal sembrado al estilo `focalization`) **espera un
  dogfood real que la dispare**, no se adelanta.

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
