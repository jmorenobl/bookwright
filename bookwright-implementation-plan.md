# Bookwright — Plan de implementación con Spec Kit

> **Documento complementario a:** `bookwright-design.md` (el *cómo* técnico) y
> `bookwright-roadmap.md` (el *qué* y *por qué* a lo largo de versiones).
> **Propósito:** secuencia de iteraciones para el **hito en curso** de Bookwright.
> Cada iteración trae su prompt y el **comando del workflow** listo para ejecutar.
> **Audiencia:** Jorge (o cualquier desarrollador con Spec Kit instalado y
> `bookwright-design.md` en el root del repo).

> **Hito en curso: `v0.5.x` — honestidad de validación + pulido determinista** (decisión
> de la issue #1 tras el 2º dogfood). El minor `v0.5.0` —validación robusta: la **costura
> de prosa/estructura única** (039) y el **resultado tri-valor** (040)— está **cerrado y
> liberado** (2026-06-22), igual que sus patches `v0.5.1` (041, raya de diálogo, DEBT-009)
> y `v0.5.2` (042, unión de rosters, DEBT-010). Detalle en git (`specs/039-…042-…`) y
> `CHANGELOG` — **no** aquí.
>
> Un **2º dogfood end-to-end** —`sombra-en-el-puerto`, novela negra, 2026-06-23, banco
> desechable fuera del repo— corrió sobre `v0.5.2` y **reencuadró el norte**. No son tres
> parches de costura más: la regla de menciones-desconocidas de `character_presence`
> (`warning`) midió **4 falsos positivos, 0 señal real** sobre prosa real, y la **issue #1**
> tomó la decisión de fondo (transcrita a `bookwright-roadmap.md` § 3 / `bookwright-design.md`
> § 13.5 — la issue no es el registro):
>
> 1. **El heurístico de *conjunto abierto* deja de fingir.** La regla de
>    menciones-desconocidas y el head-hopping de `focalization` —dos heurísticos
>    deterministas haciendo un trabajo semántico— dejan de emitir por defecto y declaran
>    **`not_evaluated`** (el canal de 040). Es la aplicación honesta de 040, no un parche.
> 2. **El move 3 (juicio semántico) se ACTIVA** como norte del track de validación (su
>    condición —heurístico medido insuficiente sobre prosa real— está cumplida). Restaura
>    la señal real (personaje usado sin declarar) que el `not_evaluated` deja pendiente.
>    Necesita **diseño propio antes de spec** (determinismo en el gate de CI) — no es una
>    iteración lista; vive como dirección (§ 1.C / `design` § 20.6).
> 3. **Pulido determinista** independiente: vocab cerrado consistente (DEBT-016), locators
>    de graph-consumers (DEBT-015), mensajes (DEBT-017).
>
> **Descartado:** las viejas 043/044 (parches de costura para la comilla-líder y el cuerpo
> de título) — solo des-ruidaban la regla que ahora pasa a `not_evaluated`; pulir los FP de
> una regla apagada es trabajo muerto. DEBT-011/012 quedan **subsumidas**. También el 5º
> roster «organización» (DEBT-013, resuelto (b) → move 3).
>
> **El track se reparte en tres** (`DEBT.md` lleva el mapeo deuda→track):
> **A — honestidad** (`not_evaluated`; cierra la mentira, familia 040),
> **B — pulido determinista** (real, barato), y
> **C — move 3** (norte activado, diseño-primero). A y B son **un patch por iteración**
> (§ 0.3); C es dirección hasta que su diseño cuaje.
>
> El detalle de **001–042** (M0–M5 … `v0.5.2`) vive en git, `specs/` y `CHANGELOG` — **no**
> aquí. Este documento se **vacía del trabajo entregado** al cerrar cada hito; conserva el
> andamiaje reutilizable (§ 0 y § 7).
>
> **Qué viene tras `v0.5.x`:** el move 3 (track C, cuando su diseño esté), y el resto del
> **horizonte demand-pulled** (`bookwright-roadmap.md` § 5) sin versión asignada — búsqueda
> vectorial (trigger = corpus multi-libro/serie o recall medido), export a EPUB/PDF/print
> (trigger = flujo end-to-end probado), y los diferidos G6/G3 (`RelationshipRole`,
> `PsychologicalState`). Ninguno arranca como plumbing especulativo.

---

## 0. Estado y cómo usar este documento

### 0.1 Punto de partida (al abrir un hito nuevo)

Antes de redactar las iteraciones de un hito nuevo, fija el punto de partida:

- Verifica que `main` esté limpio y tageado en la última release, con los cuatro
  gates verdes (`uv run ruff check && uv run ruff format --check`, `uv run mypy
  --strict`, `uv run pytest`).
- El repo ya está inicializado con Spec Kit (`.specify/`, `.claude/skills/speckit-*`)
  y su constitución ratificada (`.specify/memory/constitution.md`). **No** se
  re-bootstrapea ni se reabre ningún axioma de `bookwright-design.md` § 16.
- El **registro de diferidos** (`src/bookwright/golem/deferrals.py`) y su **test de
  paridad** (`tests/golem/test_ingestion_parity.py`) declaran los conceptos
  modelados-pero-no-alimentados. Hoy solo dos, ambos demand-pulled: `RelationshipRole`
  (G6) y `PsychologicalState` (G3). Un hito que alimente uno debe sacarlo de ahí.
- Si el hito nace de un **dogfooding** o de deuda registrada, enlaza el origen
  (`DEBT.md`, una issue de `design`/`discussion`, o un banco de pruebas desechable
  fuera del repo) en § 1 antes de redactar las iteraciones.

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
- **Numeración:** los `specs/` van por `001`…`042`. La continuación de este track arranca
  en **043** y sigue la secuencia. Cada iteración es un branch `NNN-<short-name>` con su
  propio `specs/`.

### 0.3 Versionado — patch vs. minor

Decide por hito, no por iteración:

- **Endurecimiento** (cancelar deuda, cerrar atajos, sin abrir capa nueva) → **un
  patch por iteración** con un delta observable cada uno, al estilo de `v0.3.x`
  (024–027 → `v0.3.1`…`v0.3.4`) y `v0.4.x` (034–038 → `v0.4.2`…`v0.4.6`). Acumular
  hallazgos independientes en un único minor escondería deltas que merecen su línea
  de `CHANGELOG`.
- **Capa nueva** (un sistema modelado que cobra vida) → las iteraciones **acumulan en
  `main`** y se liberan **una sola vez** como **minor** al cierre, al estilo de
  M4→`v0.2.0`, M5→`v0.3.0` y v0.4→`v0.4.0`.

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
> pásalos como `-i key=value`. Cada iteración de § 1+ trae su `SPEC` y `PLAN_HINT`
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

## 1+. Estado del track `v0.5.x` y lo que queda

> **✅ `v0.5.x` ENTREGADO ENTERO (043–049, releases `v0.5.3`–`v0.5.8`, 2026-06-24).** Los dos
> tracks de la issue #1 (2º dogfood) están cerrados: **track A — honestidad** (043
> menciones-desconocidas→abstainer · 044 categorías de `not_evaluated` + verde alcanzable · 045
> head-hopping de `focalization`→`not_evaluated` · 046 `validate` propaga `skipped`) y **track B —
> pulido determinista** (047 vocab Propp/Greimas no fatal · 048 locators de graph-consumers · 049
> nombre-vs-slug). Detalle en `CHANGELOG`/git/`specs/043…049`. **Los bloques § 1.A/§ 1.B de abajo
> (043–049) son referencia histórica — NO relanzar.**

**Lo que queda abierto.** Dos deudas cerrables (orden recomendado abajo) y el **move 3** (§ 1.C —
dirección activada, diseño-primero). Cerradas las dos deudas, el único registro abierto será
DEBT-013, conscientemente diferida al move 3 (= "cero deuda" en este proyecto).

- **DEBT-020 — `bookwright init` no debe petar el primer commit sin identidad git.** Papercut de
  onboarding (sensible para el escritor no-técnico). Patch corto, shippable (`v0.5.9`). Deck-clear
  barato, primero.
- **DEBT-019 — contrato de evaluación PARCIAL** (un validador emite hallazgos Y declara
  `not_evaluated` solo de lo que no pudo). El contrato todo-o-nada obligó a la 045 a abstener
  `focalization` ENTERO, perdiendo su comprobación determinista de ruptura de 1ª persona;
  recupérala. Determinista (familia 040/044) y **prerrequisito que des-riesga el move 3**.
  Sustantivo (`v0.5.10`).

> Cada iteración es un branch `NNN-<short-name>` con su `specs/`, un patch con delta observable,
> que **borra su entrada de `DEBT.md`** al cerrarse (§ 0.4). **Pídeme el comando de la que vayas a
> lanzar y lo regenero verificado contra el código vigente** — no copies un sketch a ciegas (es
> donde se colaron los descuidos que la revisión de mitad de track pilló).

---

## 1.A — Track de honestidad (familia 040) — ✅ ENTREGADO (histórico, no relanzar)

> **✅ 043 y 044 están RELEASED como `v0.5.3`** (2026-06-23: mergeadas a `main` con
> `48bb8a0`, release `f62922a`, tag `v0.5.3`). Sus bloques `SPEC`/comando se conservan abajo
> **solo como referencia histórica — NO relanzar** (re-ejecutar el workflow re-crearía la
> branch sobre trabajo ya entregado). El detalle vivo está en git / `CHANGELOG`. **El frente
> vivo del track A es la iteración 045.**

### 1. Iteración 043 — La regla de menciones-desconocidas declara `not_evaluated` (cierra el ruido de conjunto abierto; subsume DEBT-011/012/013-síntoma) — ✅ RELEASED v0.5.3

`character_presence` mezcla **dos reglas de naturaleza opuesta**: la de **huérfanos**
(`error`, el gate — ¿toda CHARACTER del bible se menciona en la prosa? conjunto **cerrado**,
determinista, sólida) y la de **menciones-desconocidas** (`warning` — ¿todo token
capitalizado tiene entrada en el bible? conjunto **abierto**, descubrir desconocidos: el
problema de NER sin NER). El 2º dogfood (`sombra-en-el-puerto`) midió la segunda como **4
falsos positivos, 0 señal real** sobre prosa real. Ninguna costura ni roster nuevo sube ese
techo: es irreductiblemente semántico (move 3). La iteración 040 dio el canal exacto para
esto —`not_evaluated`, «evaluado vs. no pude mirar»—. Esta iteración lo usa: la regla de
menciones-desconocidas **deja de emitir `warning` por defecto** y declara `not_evaluated`
con motivo; la regla de huérfanos (`error`, el gate) queda **intacta**.

El `SPEC` (Necesidad) y el `PLAN_HINT` (Pista para `/speckit-plan`) van **rellenos verbatim**
dentro del comando de copia-pega de abajo (fuente única, sin duplicar).

**Comando del workflow** (desde `main` limpio) — **copia-pega completo en la terminal**:

```bash
SPEC=$(cat <<'EOF'
Necesidad: el validador `character_presence` tiene DOS reglas de naturaleza opuesta. (1) La
regla de HUÉRFANOS (severidad `error`, la que protege el gate de CI): ¿toda CHARACTER del
bible se menciona en el manuscrito? Es CONJUNTO CERRADO —busca nombres CONOCIDOS del roster
en la prosa—, determinista, sin NER, y es sólida. (2) La regla de MENCIONES-DESCONOCIDAS
(severidad `warning`): ¿todo token capitalizado de la prosa tiene entrada en el bible? Es
CONJUNTO ABIERTO —descubrir desconocidos—, que es el problema de NER sin NER. El segundo
dogfood end-to-end (`sombra-en-el-puerto`, novela negra, 2026-06-23, banco desechable fuera
del repo) midió la regla (2) como 4 FALSOS POSITIVOS, 0 SEÑAL REAL sobre prosa real:
`«Inspectora`, `«Las` (un ARTÍCULO), `Marea` (palabra de un título), `Naviera` (cabeza de
"la Naviera Salas", una organización). Tres son fallo de superficie, uno es semántico, pero
TODOS comparten la causa raíz: distinguir «nombre propio sin declarar» de «organización /
topónimo / artículo desplazado / palabra de título» es irreductiblemente semántico para un
heurístico de mayúsculas. Ninguna costura (la comilla líder) ni roster nuevo (organizaciones)
sube ese techo: es perseguir un conjunto abierto con listas cerradas. La iteración 040 ya
construyó el canal correcto para "no pude evaluar de forma fiable": `NotEvaluated` →
`not_evaluated[]`. La decisión de la issue #1 (2º dogfood; transcrita a
`bookwright-roadmap.md` § 3 y `bookwright-design.md` § 13.5): la regla de
menciones-desconocidas DEJA DE FINGIR.

Esta iteración: la regla de menciones-desconocidas deja de emitir `warning` por defecto y
DECLARA `not_evaluated` con motivo «descubrimiento de nombres propios de conjunto abierto:
requiere juicio semántico (move 3); heurístico determinista medido insuficiente sobre prosa
real». La regla de HUÉRFANOS (`error`) queda INTACTA byte a byte: sigue evaluándose y
emitiendo sus hallazgos. Como `NotEvaluated` (040) es por-validador (se lanza y aborta toda
la evaluación de ese validador, perdiendo los huérfanos), el camino correcto es SEPARAR las
dos reglas en dos validadores: uno de huérfanos (`error`, siempre evaluado, protege el gate)
y uno de menciones-desconocidas (que declara `not_evaluated`). El registro de validadores los
auto-descubre a ambos; cada uno es atómicamente evaluado/no-evaluado, que es justo lo que 040
quería.

Comportamiento esperado / criterios:
- La dimensión de menciones-desconocidas NO emite `warning` por defecto sobre ningún
  manuscrito: en su lugar aparece UNA entrada en `not_evaluated[]` con el validador y el
  motivo de conjunto abierto. Verifícalo sobre `tiny-historical`: los 4 (en realidad 1 tras
  042; ver oráculo) warnings de menciones-desconocidas desaparecen y surge la entrada
  `not_evaluated`.
- La regla de HUÉRFANOS (`error`) sigue evaluándose y emitiendo sus hallazgos BYTE A BYTE
  iguales: un personaje del bible nunca mencionado sigue siendo un `error` que veta el gate.
  El gate (solo `error` rompe CI) NO cambia. Esto es innegociable (protege el gate, como
  040/042).
- La separación en dos validadores (o el mecanismo que el plan elija) deja cada validador
  ATÓMICAMENTE evaluado/no-evaluado: el de huérfanos SIEMPRE evaluado (salvo su guard
  `NotEvaluated` existente `not roster and not files`, que se conserva idéntico, FR-007 de
  042); el de menciones-desconocidas declara `not_evaluated` por la razón de conjunto abierto.
- El motivo de `not_evaluated` es legible y apunta al move 3, de modo que `verde = status ok
  Y not_evaluated == []` (040) refleje honestamente que el descubrimiento de conjunto abierto
  es un hueco CONOCIDO, no algo silenciosamente ausente.
- `bookwright status` y el report humano (los canales que 040 cableó) muestran el tercer
  estado; el sobre `--json` lleva la entrada en `not_evaluated[]`. Sin canal nuevo: reusa el
  de 040.
- Oráculos: `tiny-historical/expected-status.md` se corrige (el `warning` de
  menciones-desconocidas se va; aparece la entrada `not_evaluated`; `error` sin cambios), sin
  tocar el manuscrito/bible del fixture, como 042 hizo `4 → 1` y 041 `5 → 4`. Los fixtures que
  solo asertan `error == 0` no se tocan. Verifícalo EMPÍRICAMENTE (`uv run pytest`).
- La costura `io/prose.py` NO se toca ni se borra (sigue sirviendo a los validadores
  deterministas). NO se añade la comilla-líder (DEBT-011) ni se exime el cuerpo del título
  (DEBT-012): esos FP desaparecen porque la regla entera pasa a `not_evaluated`, no porque se
  des-ruiden. Borra las entradas DEBT-011 y DEBT-012 de `DEBT.md` (subsumidas).
- Validador de prosa: `triples=()`, sin grafo, ontología congelada intacta (Principio X). SIN
  dependencia nueva (Constitución II). Cada archivo ≤ 500 líneas.

Fuera de scope: el head-hopping de `focalization` (DEBT-014 / iteración 045, misma clase,
su propio patch); `validate` propagando `skipped` (DEBT-018 / iteración 046); el move 3 en sí
(el evaluador LLM que REEMPLAZARÁ este `not_evaluated` por hallazgos reales — track C, diseño
propio); un modo opt-in determinista de la regla (descartado por disciplina de scope; sería
aditivo si algún día se pide).
EOF
)
PLAN_HINT=$(cat <<'EOF'
Apóyate en `src/bookwright/validation/validators/character_presence.py` (las dos reglas YA
viven en métodos separados: `_orphans` → `error`, `_unknown_mentions` → `warning`) y en el
contrato tri-valor de 040 (`NotEvaluated` en `validation/base.py`, capturado por el runner
ANTES de su `except` genérico y anotado en `not_evaluated[]`). La forma recomendada: SEPARAR
en dos validadores —p. ej. `character_presence` (huérfanos, `error`, conserva su guard
`NotEvaluated` actual `not roster and not files`) y un nuevo `character_unknown_mentions` que
`raise NotEvaluated("open-set proper-noun discovery requires semantic judgment (move 3); …")`—
ambos auto-descubiertos por `registry.py`. Así cada validador es atómicamente
evaluado/no-evaluado (lo que 040 quería) sin perder los huérfanos. Verifica en `registry.py`
cómo se auto-registran y replica el patrón. NO toques `io/prose.py` ni la regla de huérfanos.
Corre `uv run pytest` para ver qué oráculos cambian: `tiny-historical/expected-status.md`
pierde el `warning` de menciones-desconocidas y gana una entrada `not_evaluated` (no toques el
manuscrito). Mira cómo 040 testeó el canal `not_evaluated[]` y reúsalo. Diseño § 13.5. Sin
librería externa (Constitución II).
EOF
)
specify workflow run bookwright-quality \
  -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
```

**043 está implementada y verde** en la branch `043-character-presence-split` (4 gates verdes,
97.55% cobertura), pero **NO se mergea ni se libera sola**: dejó el predicado verde de 040
inalcanzable en todo proyecto (efecto colateral, no defecto). La iteración **044** se apila
sobre esta misma branch y lo corrige; **043+044 se mergean juntas y se liberan como una sola
`v0.5.3`** (ver cierre de 044). Mantener `main` semánticamente redondo de una.

---

### 2. Iteración 044 — `not_evaluated` distingue capability-gap permanente de input-gap; el verde vuelve a ser alcanzable — ✅ RELEASED v0.5.3

**El refinamiento de 040 que 043 hizo necesario.** 043 hizo honesto el heurístico de conjunto
abierto (`character_unknown_mentions` declara `NotEvaluated` **incondicionalmente**). Correcto,
pero con un efecto colateral en el contrato de 040: como ese abstainer está SIEMPRE dormido,
(1) el predicado verde (`status == ok` Y `not_evaluated == []`, documentado en
`validation/report.py`) es `False` en **todos** los proyectos hasta el move 3 —incluido uno
impecable—, y (2) la regla `_activate_dormant_validators` de `status` dispara un nudge de
`bookwright-continuity` en **todos** los proyectos. Un verde estructuralmente inalcanzable no
informa: si pristino y roto son ambos «no verde», el autor aprende a ignorar el canal
`not_evaluated` —la misma fatiga de alarma que issue #1 quería matar, mudada de canal. La raíz:
hay **dos tipos** de `not_evaluated` y 043 los mezcló en el canal que gobierna el verde.

El `SPEC` (Necesidad) y el `PLAN_HINT` van **rellenos verbatim** en el comando de copia-pega.

**Comando del workflow** — se lanza **DESDE LA BRANCH `043-character-presence-split`** (NO desde
main: 044 se apila sobre 043), con el árbol limpio:

```bash
SPEC=$(cat <<'EOF'
Necesidad: la iteración 043 hizo honesto el heurístico de conjunto abierto — el validador
`character_unknown_mentions` declara `NotEvaluated` INCONDICIONALMENTE (no lee estado del
proyecto). Es correcto, pero tuvo un efecto colateral sobre el contrato tri-valor de la
iteración 040: como ese abstainer está SIEMPRE dormido, (1) el predicado verde de 040
—`status == "ok"` Y `not_evaluated == []`, documentado en `src/bookwright/validation/report.py`—
es `False` en TODOS los proyectos para siempre hasta el move 3, incluido un proyecto impecable;
y (2) la regla `_activate_dormant_validators` de `src/bookwright/status/rules.py` dispara un
nudge de `bookwright-continuity` en TODOS los proyectos (incluido uno limpio). Un verde que
NINGÚN proyecto puede alcanzar jamás no informa: si pristino y roto son ambos "no verde", el
autor aprende a IGNORAR el canal `not_evaluated` — exactamente la fatiga de alarma que la issue
 #1 quería erradicar, mudada del canal `warning` (que 043 vació) al canal `not_evaluated`.

La causa raíz: hay DOS tipos de entrada `not_evaluated`, y 043 los mezcló en el único canal que
gobierna el verde. (a) CONDICIONAL AL INPUT (lo que 040 diseñó): "no pude evaluar TU proyecto
por un input que falta o está roto" — accionable (el autor arregla el input y entonces evalúa),
por-proyecto, transitorio (p. ej. `focalization` sin declaración de voz; manuscrito vacío). (b)
PERMANENTE POR CAPACIDAD (el abstainer de 043): "esto no lo evalúa NINGÚN run determinista;
espera al move 3" — NO accionable por el autor, idéntico en todo proyecto, permanente.

Esta iteración CATEGORIZA las entradas de `not_evaluated` y hace que SOLO las de tipo input
gobiernen el verde y el nudge; las de tipo capability se SIGUEN mostrando (visibilidad: gaps
visibles ≠ silencio, doctrina issue #1) pero no tumban el verde ni piden una acción que el autor
no puede ejecutar. Así un proyecto impecable vuelve a poder estar VERDE, mientras el gap del
move 3 queda registrado y a la vista.

Comportamiento esperado / criterios:
- `NotEvaluated` (y `NotEvaluatedResult`) gana un campo `kind` con dos valores: `missing_input`
  (lo que 040 modeló; DEFAULT, para que TODOS los `raise NotEvaluated(...)` existentes
  —`focalization` sin declaración / `[PENDING]`, el guard `not roster and not files` de
  `character_presence`, manuscrito vacío— conserven su comportamiento byte a byte) y
  `pending_capability` (permanente). `character_unknown_mentions` pasa a `raise
  NotEvaluated(<motivo>, kind="pending_capability")`.
- El predicado verde se REFINA y se re-documenta: GREEN = `status == "ok"` Y no hay entradas
  `not_evaluated` de tipo `missing_input`. Las `pending_capability` NO tumban el verde. Un
  proyecto impecable (sin `error`, sin `warning`, sin input-gaps) vuelve a estar VERDE aunque
  lleve la entrada permanente `character_unknown_mentions: pending_capability`.
- La regla `_activate_dormant_validators` de `status` SOLO nudge-ea por entradas `missing_input`
  (accionables). Las `pending_capability` NO disparan el nudge de `bookwright-continuity` (el
  autor no puede hacer nada: el move 3 no es shippable por él). Se retira el clause
  `_REMEDIES["character_unknown_mentions"]` que 043 añadió (ya no se nudge-ea por él).
- VISIBILIDAD PRESERVADA (innegociable, doctrina issue #1): la entrada `pending_capability`
  SIGUE apareciendo en el sobre `--json` de `not_evaluated[]`, en `bookwright status` y en el
  report humano, etiquetada por su `kind` como limitación conocida pendiente del move 3 — NO se
  oculta (ocultarla reintroduciría el silencio = falsa confianza que 040 mató).
- El sobre `--json` de `not_evaluated[]` y el payload de `status` incluyen `kind` (ADITIVO: el
  shape gana una clave; ningún campo existente cambia de nombre o tipo).
- El GATE no cambia: solo `error` rompe CI; `not_evaluated` de NINGÚN tipo veta. Solo cambian el
  predicado VERDE (informativo) y el nudge de `status`.
- Oráculos (verifícalo EMPÍRICAMENTE con `uv run pytest`): `tiny-historical/expected-status.md`
  — la entrada `not_evaluated` gana `kind: pending_capability`, `next_actions` vuelve de 4 a 3
  (se va el nudge universal), `validation.counts` byte-iguales, `error` sigue 1. Los fixtures
  limpios (`tiny-novel`/`tiny-memoir`) vuelven a VERDE. Ajusta los tests del predicado verde, del
  nudge dormido y de `base`/`runner` que 040 y 043 dejaron.
- Cada archivo ≤ 500 líneas, SIN dependencia nueva (Constitución II), validadores de prosa con
  `triples=()`, ontología congelada intacta (Principio X). Esta iteración NO toca
  `character_presence` (huérfanos) ni `io/prose.py`.

Fuera de scope: el head-hopping de `focalization` (iteración 045); el move 3 en sí (track C); el
canal `errors[]` de validadores que petan (distinto de `not_evaluated`, no se toca).
EOF
)
PLAN_HINT=$(cat <<'EOF'
Apóyate en el contrato de 040 (`src/bookwright/validation/base.py`: `NotEvaluated` línea ~119 y
`NotEvaluatedResult` línea ~135 con su `to_json`) y en el de 043 (`character_unknown_mentions.py`).
Define un `Literal["missing_input", "pending_capability"]` (o un Enum corto); `NotEvaluated.__init__`
gana `kind` con DEFAULT `"missing_input"` (preserva todos los raises existentes); `NotEvaluatedResult`
gana `kind` y lo incluye en `to_json`. El runner (`runner.py:68-69`) estampa `skip.kind` al construir
el `NotEvaluatedResult`. `character_unknown_mentions.validate` pasa `kind="pending_capability"`. El
predicado verde vive en `validation/report.py` (docstring SC-002 ~línea 50 y la lógica "clean"
~línea 116 `if not reported and not self.errors and not self.not_evaluated`) → cámbialo a "no hay
`not_evaluated` de tipo `missing_input`" (filtra por kind). En `status/rules.py`,
`_activate_dormant_validators` (~línea 136) filtra `r.kind == "missing_input"` y quita el clause
`_REMEDIES["character_unknown_mentions"]`. Surfacea `kind` en el render humano de `report.py` (~127)
y en los `to_payload`/`to_json` de `status/model.py` (`ValidationSummary`). Actualiza
`bookwright-design.md` § 13.1/§ 13.4 (el predicado verde refinado) ANTES de divergir el código
(plan § 7.3). Mira cómo 040 testeó el canal `not_evaluated[]` y extiéndelo con el `kind`. Sin
librería externa. Diseño § 13.5.
EOF
)
specify workflow run bookwright-quality \
  -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
```

Al verde: **mergear 043+044 juntas a `main`** en una sola entrada (`Merge iterations 043+044: …`
+ `docs(claude): record iterations 043+044 merged`) y cortar **una sola release `v0.5.3`** con
`bookwright-release` (§ 0.4, paso 4) — main no ve nunca el verde-inalcanzable.

---

### 3. Iteración 045 — `focalization` declara `not_evaluated` cuando su heurístico no puede atribuir interioridad (cierra DEBT-014)

**Misma clase que 043, en el otro validador.** El head-hopping de `focalization` exige el
nombre COMPLETO del bible (`Víctor Salas`) en la MISMA línea física que el verbo de
interioridad; la prosa real nombra por el nombre de pila (`Víctor`) y reparte el párrafo en
varias líneas, así que la regla está **prácticamente dormida** (falso negativo → verde
engañoso, familia 040). La issue #1 confirmó que un head-hop heurístico sin juicio semántico
**tiene techo de precisión**: no se intenta subir el heurístico (mejorar el matching) como
cura. En su lugar, cuando hay una declaración focal pero el heurístico no puede atribuir
interioridad de forma fiable, el validador **declara `not_evaluated`** en vez de dormir en
verde. La detección real —irreductiblemente semántica— es track C (move 3).

- **Necesidad / criterios:** con una declaración de voz parseable (p. ej. "Tercera persona
  limitada, focalizada en X"), `focalization` ya NO devuelve `[]` silencioso cuando su
  heurístico de atribución (nombre completo + misma línea) no es fiable: declara
  `not_evaluated` con motivo «atribución de interioridad / head-hopping: requiere juicio
  semántico (move 3)». Decidir en `/speckit-plan` si la regla de head-hopping pasa ENTERA a
  `not_evaluated` (postura honesta: su precisión actual es ~nula sobre prosa real, como midió
  el dogfood) o si queda un núcleo determinista. Postura recomendada, por coherencia con 043:
  **entera a `not_evaluated`** hasta el move 3. El guard `_PENDING_ONLY` y el de "sin
  declaración" (037) NO cambian: esos ya son `not_evaluated`/"sin declaración" correctos.
- **Pista (`/speckit-plan`):** `validation/validators/focalization.py` (`_head_hopping`,
  `_INTERIORITY`, el matching por nombre completo en `line.raw`). **`kind` (044), CRÍTICO:** el
  nuevo raise del head-hop es un hueco de CAPACIDAD (semántico → move 3), así que usa
  `raise NotEvaluated(<motivo>, kind=NotEvaluatedKind.pending_capability)`. Si se queda con el
  DEFAULT `missing_input`, por el predicado de 044 tumbaría el verde y dispararía el nudge en
  TODO proyecto con voz focal — la regresión que 044 reparó. Los CUATRO raises existentes de
  `focalization` (sin constitución / sin declaración / `[PENDING]`,
  `focalization.py:74/82/167/170`) son input-conditional y se quedan `missing_input` — NO les
  pongas `pending_capability`.
  Verifica oráculos con `uv run pytest`; los fixtures con declaración focal ganan una entrada
  `not_evaluated` de `kind: pending_capability` que —correctamente— NO les rompe el verde.
  Borra DEBT-014 de `DEBT.md` (la mitad de honestidad; el techo de precisión
  lo cierra el track C). Validador de prosa, `triples=()`, ontología congelada intacta.
- **Release:** `v0.5.4`.

---

### 4. Iteración 046 — `validate` propaga los `skipped` de la ingestión (cierra DEBT-018)

**La familia 040 a nivel de fichero de entrada, no de validador.** Un fichero de bible con
front-matter roto se OMITE en `map_bible` (canal `skipped` de `graph build`): ese personaje
desaparece del grafo y de toda validación. `bookwright status` lo trata como bloqueante
(`code=skipped_sources`), pero `bookwright validate` —el gate de CI— procede en silencio
sobre el corpus parcial con `not_evaluated: []`, que se lee como «todo evaluado» cuando un
personaje entero quedó fuera. Es justo el `[]`-miente que 040 quería erradicar.

- **Necesidad / criterios:** `validate` propaga los `skipped` de `map_bible` a su sobre como
  entradas `not_evaluated[]` con **`kind=NotEvaluatedKind.missing_input`** (un fichero omitido
  es input-conditional: el autor arregla el YAML roto), una por fichero omitido con su motivo,
  para que `not_evaluated: []` no mienta. **044 ya resuelve la pregunta del verde:** al ser
  `missing_input`, el predicado refinado de 044 degrada el verde automáticamente, alineándose
  con la negativa dura de `status` — ya no es una decisión abierta. Cierra la asimetría
  `status`↔`validate`. (Alternativa de presentación: un canal `skipped[]` espejo del de `graph
  build`; pero `not_evaluated[]` + `missing_input` reúsa 044 sin canal nuevo.)
- **Pista (`/speckit-plan`):** `commands/validate.py` (ensamblado del `ValidationReport`/sobre)
  vs. `commands/status.py` (que ya rechaza con `code=skipped_sources`, `commands/status.py:82`);
  el canal `skipped` de `map_bible` (`io/bible.py`, `SkippedFile`). Reúsa el `not_evaluated[]`
  de 040 con `kind=missing_input` (044). Borra DEBT-018 de `DEBT.md`.
- **Release:** `v0.5.5`.

---

## 1.B — Track de pulido determinista (cerrado/estructural) — ✅ ENTREGADO (histórico, no relanzar)

Independiente del track A; puede intercalarse. Tres patches, cada uno un delta observable.

### 5. Iteración 047 — vocabulario Propp/Greimas no reconocido: `warning` no fatal enumerado (cierra DEBT-016)

Hoy un `functions: [intimidacion]` (no es una de las 31 funciones de Propp) se ingiere **en
silencio** como `G10_Narrative_Function` sin `crm:P2_has_type`, mientras el vocab de research
(`type`/`reliability`) rechaza enumerando (DEBT-006). Decisión de issue #1: **cerrado para
*tipar*, abierto para *autorar*.**

- **Necesidad / criterios:** con un vocab activo, un `functions:`/`roles:` que no case ningún
  término emite un `warning` **no fatal** en `graph build` enumerando los términos válidos
  (mismo patrón que el loader de research, derivado del vocab en orden de declaración,
  drift-proof); el nodo **se ingiere igual**, sin `P2_has_type`. NO se aborta el build (no
  rompe proyectos con etiquetas propias). NO se introduce severidad `info` nueva. El
  principio: **fatal ⇔ rompe lógica downstream** — documenta por qué research es fatal y esto
  no.
- **Pista (`/speckit-plan`):** `io/vocabularies.py` (tipado por etiqueta) + la ingestión de
  `outline/units/*.md`; mira cómo `_reject_unknown_vocab` de research enumera (DEBT-006/036) y
  replica la enumeración, pero como `warning` no fatal. Borra DEBT-016 de `DEBT.md`.
- **Release:** `v0.5.6`.

### 6. Iteración 048 — locators resolubles en los validadores graph-consumer (cierra DEBT-015)

`factual_anchor` identifica el anchor por su URI uuid7 y emite `source=None`; `temporal`
emite `source=None` en sus reglas a/b (solo la d resuelve `bible/timeline.md`). Inaccionable,
y asimétrico con los validadores de prosa (que siempre dan `relpath:línea`) y con `status`
(que ya reporta el mismo anchor de forma legible).

- **Necesidad / criterios:** (a) `factual_anchor` identifica el anchor por su target/finding
  (el handle determinista que el fixture ya documenta) y resuelve `bible/research/<tema>.md`
  como `source`. (b) `temporal` aplica `resolve_source` también en las reglas a y b.
  Idealmente un helper compartido "resuelve el locator E13 de este sujeto/triple". Severidades
  y gate sin cambios. NADA semántico: el grafo ya lleva la procedencia `file:line` reificada
  en los E13.
- **Pista (`/speckit-plan`):** `validators/factual_anchor.py`, `validators/temporal.py`,
  `validation/queries.py` (`resolve_source`). Borra DEBT-015 de `DEBT.md`.
- **Release:** `v0.5.7`.

### 7. Iteración 049 — `narrative_structure` unifica el identificador de unidad (cierra DEBT-017)

Las dos reglas del validador imprimen identificadores distintos para la misma clase de
entidad: la de rol-sin-resolver el `name` humano, la de beat-huérfano el `slug`. Pulido de
UX, sin impacto funcional; puede ir junto a 048 (ambos son consistencia de mensajes).

- **Necesidad / criterios:** unificar el identificador (preferiblemente el `name` humano, con
  el slug entre paréntesis si hace falta) en las dos reglas. El locator `relpath:línea` ya es
  correcto en ambas; solo cambia qué identificador se imprime.
- **Pista (`/speckit-plan`):** `validators/narrative_structure.py` (las dos reglas). Borra
  DEBT-017 de `DEBT.md`.
- **Release:** `v0.5.8` (o doblada con 048).

---

## 1.C — Track del move 3 (juicio semántico) — dirección activada, NO una iteración lista

El 2º dogfood **cumplió la condición de activación** del move 3 (un heurístico concreto
medido insuficiente sobre prosa real: 4/4 FP). Deja de ser demand-pulled-sin-disparador y es
el **norte del track de validación**. Pero **no se redacta como iteración aún**: tiene una
tensión de diseño real que su spec debe resolver primero.

- **Qué cura:** el conjunto abierto entero que el track A dejó en `not_evaluated` —
  menciones-desconocidas (orgs/topónimos/vocativos/personaje-sin-declarar, DEBT-013 incluida)
  y el head-hopping real (techo de DEBT-014)— escalando a juicio semántico vía el path LLM de
  `bookwright-verify` (iteración 015), con el regex como **pre-filtro barato** (acota
  candidatos), no como veredicto. Restaura la SEÑAL que el `not_evaluated` deja pendiente.
- **La tensión a resolver ANTES de spec (design § 20.6):** todo el proyecto es disciplina de
  test **determinista**, y un LLM en el gate de CI no lo es. El diseño debe decidir: ¿el
  veredicto semántico vive **fuera** del gate (informativo, como `bookwright-verify`/
  `bookwright-continuity` hoy — reporte post-borrador que nunca rompe CI) o **dentro** (con
  golden-runs/caché de veredictos para fijar el no-determinismo)? Coste, operación offline y
  reproducibilidad de tests son parte de la decisión.
- **Siguiente paso (no una spec):** abrir el hilo de diseño (issue `design`, o profundizar
  `bookwright-design.md` § 20.6) que resuelva la tensión de determinismo y fije el contrato;
  recién entonces se redacta la iteración con su `SPEC`/`PLAN_HINT`. Hasta ahí, el interim
  honesto del track A (declarar `not_evaluated`) es el estado correcto y permanente-como-
  fallback.

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
