# Bookwright — Plan de implementación con Spec Kit

> **Documento complementario a:** `bookwright-design.md` (el *cómo* técnico) y
> `bookwright-roadmap.md` (el *qué* y *por qué* a lo largo de versiones).
> **Propósito:** secuencia de iteraciones para el **hito en curso** de Bookwright.
> Cada iteración trae su prompt y el **comando del workflow** listo para ejecutar.
> **Audiencia:** Jorge (o cualquier desarrollador con Spec Kit instalado y
> `bookwright-design.md` en el root del repo).

> **Hito en curso: `v0.5.x` — endurecimiento post-dogfood** (DEBT-009/010). El hito
> `v0.5.0` —validación robusta (issue #1): la **costura de prosa/estructura única** (039)
> y el **resultado tri-valor** (040)— está **cerrado y liberado** (2026-06-22);
> `__version__` es `0.5.0`, `main` está tageado y los cuatro gates verdes. Un **dogfood
> end-to-end** del fixture `tiny-historical` tras la release (2026-06-22, banco
> desechable fuera del repo) destapó dos defectos latentes en `character_presence`,
> registrados en `DEBT.md`: **DEBT-009** (marca el primer término tras la raya de diálogo
> `—`, la *misma clase* de acoplamiento de superficie que issue #1 cerró para los
> marcadores de bloque, pero la costura de 039 no reconoce la raya tipográfica) y
> **DEBT-010** (marca tokens de un setting multi-palabra que *sí* está declarado en la
> bible, porque el cruce solo consulta el roster de personajes). El *qué/por qué* durable
> vive en `bookwright-roadmap.md` § 3.
>
> **Es un track de endurecimiento → un patch por iteración** (plan § 0.3, al estilo de
> `v0.3.x` y `v0.4.x`): **041** cierra DEBT-009 (`v0.5.1`) y **042** cierra DEBT-010
> (`v0.5.2`), cada uno con un delta observable y su entrada de `DEBT.md` borrada **dentro
> del spec**. Las dos iteraciones son **independientes** —041 toca solo la costura
> `io/prose.py`; 042 toca `validation/base.py` + `character_presence.py`—, así que el
> orden es por prioridad (041 primero, es la clase de issue #1), no por dependencia.
>
> El detalle de las iteraciones **001–040** (M0–M5, `v0.3.1`…`v0.3.4`, `v0.4.0`, los
> patches `v0.4.1`…`v0.4.6` y el minor `v0.5.0`) vive en el historial git, en
> `specs/001-…` … `specs/040-…` y en el `CHANGELOG` — **no** aquí. Este documento se
> **vacía del trabajo entregado** al cerrar cada hito; conserva solo el andamiaje
> reutilizable (§ 0 y § 7).
>
> **Qué viene tras `v0.5.x`:** el **horizonte demand-pulled** (`bookwright-roadmap.md`
> § 5 y `DEBT.md`), **sin versión asignada** — juicio semántico en validación
> (movimiento 3 de la issue #1: el path LLM de `bookwright-verify` con el regex como
> pre-filtro; trigger = un heurístico medido como insuficiente), búsqueda vectorial
> (ChromaDB sobre rdflib; trigger = corpus multi-libro/serie o recall estructural
> medido), export a EPUB/PDF/print vía pandoc (trigger = flujo end-to-end probado en
> un libro real), y los dos diferidos G6/G3 (`RelationshipRole`,
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
- **Numeración:** los `specs/` van por `001`…`040`. Este track arranca en **041** y
  continúa la secuencia. Cada iteración es un branch `NNN-<short-name>` con su propio
  `specs/`.

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

## 1+. Iteraciones del track en curso — `v0.5.x` (endurecimiento post-dogfood)

Dos iteraciones **independientes** (041 toca solo la costura `io/prose.py`; 042 toca
`validation/base.py` + `character_presence.py`). Cada una es un **patch** con un delta
observable y se libera por separado (041 → `v0.5.1`, 042 → `v0.5.2`); el orden es por
prioridad (041 primero, cierra la clase de issue #1), no por dependencia. Origen:
**dogfood end-to-end de `tiny-historical` tras `v0.5.0`** (2026-06-22, banco desechable
fuera del repo), registrado en `DEBT.md` (DEBT-009/010). El *qué/por qué* durable está
en `bookwright-roadmap.md` § 3.

### 1. Iteración 041 — La costura de prosa reconoce la raya de diálogo `—` (cierra DEBT-009)

Cierra DEBT-009: `character_presence` marca el primer término tras la **raya de diálogo**
española (`—Esto…` → "Esto" reportado como nombre propio sin entrada en la bible). Es la
*misma clase* que issue #1 cerró para los marcadores de bloque (DEBT-008): un marcador
líder de superficie que el heurístico no "ve". El arreglo vive **solo en la costura
compartida** (`io/prose.py`), no en un stripper local — meterlo en `character_presence`
reintroduciría exactamente la deuda que 039 saldó.

**Necesidad (`SPEC`)** — pega verbatim como `spec`:

```text
Necesidad: en prosa española el diálogo se abre con la raya tipográfica `—` (U+2014; y
a veces la semirraya `–`, U+2013). La costura de prosa única de Bookwright
(`io/prose.py`, iteración 039) normaliza los marcadores de bloque ASCII —encabezado ATX
`#{1,6} `, viñeta/blockquote `[-*+>] `— pero NO reconoce la raya de diálogo. Como
consecuencia, `character_presence` ve `—Esto es el porvenir` con la `—` aún pegada: el
término `Esto` no queda en offset 0, así que la exención de inicio-de-frase no dispara y
`Esto` (un demostrativo, no un nombre propio) se reporta como nombre propio sin entrada
en la bible. En una novela real —mayoritariamente diálogo con raya— esto inunda de
warnings espurios el primer término capitalizado de CADA línea de diálogo (Esto, Sí,
Claro, Nunca…), ahogando los hallazgos reales. Son `warning`, así que no vetan el gate,
pero es exactamente el fallo de superficie que issue #1 quería cerrar de raíz, y la
costura de 039 lo dejó abierto para la raya. Detectado por el dogfood end-to-end de
`tiny-historical` tras `v0.5.0` (DEBT-009 en `DEBT.md`).

Esta iteración cierra DEBT-009 en la COSTURA, no en el validador: `io/prose.py` añade la
raya de diálogo líder (`—`/`–`, tolerando espacio alrededor) al conjunto de marcadores
estructurales que su normalización retira, junto a los marcadores de bloque que ya
maneja. Tras normalizar, el primer término de contenido de la línea de diálogo queda en
offset 0 y hereda la exención de inicio-de-frase YA existente en `character_presence` (el
mismo mecanismo con el que DEBT-008 resolvió el encabezado ATX). En consecuencia NINGÚN
validador se toca: el arreglo es puramente de la capa compartida, lo que prueba que
cierra la CLASE (cualquier validador de prosa se beneficia), no una instancia.

Comportamiento esperado / criterios:
- `character_presence` deja de marcar el primer término tras una raya de diálogo líder:
  `—Esto es el porvenir` no reporta `Esto`. El arreglo vive SOLO en `io/prose.py`; no se
  edita ningún validador (criterio de que la clase se cierra en la costura).
- La raya se trata como un marcador de bloque más: solo la LÍDER (anclada en `^`,
  tolerando whitespace previo) se retira; las rayas internas de un inciso
  (`—dijo Arnela—`) NO se tocan. La semirraya `–` (U+2013) se reconoce igual que la raya
  `—` (U+2014); el guion ASCII `- ` ya lo cubre el marcador de viñeta existente.
- CERO regresión en los fixtures vivos sin tocar oráculos salvo donde HOY exista un falso
  positivo de raya de diálogo: hay que verificarlo EMPÍRICAMENTE corriendo la suite. Si
  algún oráculo contaba un warning espurio de raya, se corrige a la baja (el manuscrito
  del fixture NO se toca), igual que 038 corrigió el conteo `6 → 5` del `Capítulo`
  espurio.
- El locator `relpath:línea` NO cambia: el número de línea sigue saliendo de `enumerate`,
  no del offset del match; la normalización solo afecta al texto escaneado, no a la
  numeración.
- GENERALIZACIÓN demostrada: un fixture/caso nuevo con una mención de personaje fuera de
  roster MID-línea en un párrafo de diálogo (p. ej. `—Pregúntale a Quirón —dijo.`) sigue
  disparando sobre `Quirón`, mientras que el demostrativo líder no dispara — probando que
  solo se neutraliza el marcador líder, no el contenido.
- SIN dependencia nueva (Constitución II): la raya se reconoce con una regex determinista
  anclada (como `_BULLET_MARKER`), NO con un parser de markdown de terceros. Cada archivo
  ≤ 500 líneas. Validadores de prosa sin grafo, `triples=()`, ontología congelada intacta
  (Principio X); el gate (solo `error` rompe CI) y las severidades no cambian.
- Borra la entrada DEBT-009 de `DEBT.md` (git conserva el historial).

Fuera de scope: el roster de cruce incompleto de settings/locations/objects (eso es
DEBT-010 / iteración 042); convertir el heurístico de nombres propios en juicio semántico
(movimiento 3 de issue #1, demand-pulled); cualquier validador que no escanee prosa de
superficie (`factual_anchor`, `temporal`, `narrative_structure`).
```

**Pista para `/speckit-plan` (`PLAN_HINT`)** — pega verbatim como `plan_hint`:

```text
Apóyate en `io/prose.py` (la costura de 039): `_normalize` retira iterativamente los
prefijos de bloque vía `_HEADING_MARKER` (`^#{1,6}\s+`) y `_BULLET_MARKER`
(`^\s*[-*+>]\s+`). Añade un `_DIALOGUE_MARKER` —p. ej. `^\s*[—–]\s*` (raya U+2014 /
semirraya U+2013, espacio opcional alrededor; OJO: la raya suele ir pegada al texto,
`—Esto`, así que el sufijo es `\s*`, no `\s+`)— y aplícalo en `_normalize` dentro del
mismo bucle de stripping, una pasada por marcador (`sub(count=1)`), de modo que solo la
raya LÍDER se retire y las internas queden intactas. NO toques `character_presence`: con
la raya retirada, `_is_sentence_initial(scan, match.start())` ve el primer término en
prefijo vacío y lo exime, igual que el encabezado ATX en DEBT-008. Verifica
empíricamente qué oráculos cambian (`uv run pytest`) y corrige solo los conteos de falsos
positivos de raya (sin tocar manuscritos de fixture). Añade un caso de prosa que pruebe
que una mención MID-línea de diálogo sigue disparando. Diseño § 13. Sin librería de
markdown (Constitución II).
```

**Comando del workflow** (desde `main` limpio):

```bash
SPEC=$(cat <<'EOF'
…  # la Necesidad de 041, verbatim del bloque de arriba
EOF
)
PLAN_HINT=$(cat <<'EOF'
…  # la Pista de 041, verbatim del bloque de arriba
EOF
)
specify workflow run bookwright-quality \
  -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
```

Al verde: mergear a `main` (`Merge iteration 041: …` + `docs(claude): record iteration
041 merged`) y cortar la release `v0.5.1` con `bookwright-release` (§ 0.4, paso 4).

---

### 2. Iteración 042 — `character_presence` cruza contra TODA la bible (cierra DEBT-010)

Cierra DEBT-010: el heurístico de "nombre propio sin entrada en la bible" solo consulta
el roster de PERSONAJES, así que los tokens de un setting/location/object multi-palabra
que SÍ está declarado (p. ej. `Real`, `Fábrica`, `Paños` de "la Real Fábrica de Paños")
se marcan como sin entrada. El mensaje dice literalmente "no bible entry": debe consultar
TODA la bible, no solo `characters/`.

**Necesidad (`SPEC`)** — pega verbatim como `spec`:

```text
Necesidad: el validador `character_presence` tiene dos reglas. La regla de huérfanos
(severidad `error`, protege el gate) verifica que cada PERSONAJE de la bible se mencione
en el manuscrito. La regla de menciones-desconocidas (severidad `warning`) marca todo
nombre propio del manuscrito que "no tiene entrada en la bible" — pero solo cruza contra
el roster de PERSONAJES (`character_names()`). Por eso, un setting declarado como
`bible/settings/la-real-fabrica-de-panos.md` ("la Real Fábrica de Paños") provoca que sus
tokens `Real`, `Fábrica`, `Paños` se reporten como nombres propios «sin entrada en la
bible» — cuando la entrada EXISTE, solo que en `settings/` (o `locations/`, `objects/`)
en vez de `characters/`. El texto del warning es honesto («heuristic — may be a place or
organization»), pero sobre una novela con sus entornos ya declarados el diagnóstico es
engañoso y el ruido alto. Detectado por el dogfood end-to-end de `tiny-historical` tras
`v0.5.0` (DEBT-010 en `DEBT.md`).

Esta iteración cierra DEBT-010: la regla de menciones-desconocidas pasa a suprimir todo
candidato cuyo slug (o cuyos tokens) case con CUALQUIER entidad declarada en la bible
—personajes, settings, locations y objects—, no solo personajes. La regla de huérfanos
(la que rompe el gate) sigue operando EXCLUSIVAMENTE sobre el roster de personajes: un
setting nunca mencionado NO es un huérfano de personaje. El estado `no-evaluado` de
`character_presence` (iteración 040) tampoco cambia.

Comportamiento esperado / criterios:
- `ValidationContext` (`validation/base.py`) gana accesores cacheados `location_names()`
  y `object_names()`, espejo exacto de `setting_names()` (mismo helper genérico
  `_names_of`, mismo patrón `_UNSET`/memo), para las clases GOLEM `NarrativeLocation`
  (G13, `bible/locations/`) y `Object` (G16, `bible/objects/`).
- La regla de menciones-desconocidas de `character_presence` construye su conjunto de
  "slugs conocidos" a partir de la UNIÓN de personajes + settings + locations + objects
  (nombre completo y tokens, como ya hace `_roster_slugs`). Un token que case cualquiera
  de esos rosters deja de reportarse: `Real`/`Fábrica`/`Paños` de "la Real Fábrica de
  Paños" ya no se marcan.
- La regla de huérfanos (`error`) NO cambia: sigue derivando del roster de PERSONAJES
  (`character_names()`). Un setting/location/object declarado pero nunca mencionado NO
  produce error ni warning de huérfano (no es su responsabilidad). Los hallazgos `error`
  existentes salen byte a byte iguales (protege el gate, como 040).
- El guard `NotEvaluated` de 040 NO cambia: `character_presence` sigue siendo
  `no-evaluado` SOLO cuando NO hay prosa Y el roster de personajes está vacío; su motivo
  textual es idéntico. (Settings/locations/objects sin prosa ni personajes siguen sin
  nada que cruzar.)
- CERO regresión funcional: verifícalo EMPÍRICAMENTE (`uv run pytest`). Donde un oráculo
  contara un warning de un setting/location/object ya declarado, se corrige a la baja
  (sin tocar manuscritos ni la bible del fixture). Un nombre propio genuinamente fuera de
  TODA la bible sigue disparando.
- Validador de prosa: el cruce sigue siendo file-based vía `bible()`/`map_bible` (no
  SPARQL), `triples=()`, sin grafo, ontología congelada intacta (Principio X). El gate
  (solo `error` rompe CI) y las severidades no cambian. Cada archivo ≤ 500 líneas.
- Borra la entrada DEBT-010 de `DEBT.md` (git conserva el historial).

Fuera de scope: la raya de diálogo (DEBT-009 / iteración 041); crear un validador de
presencia de entornos/objetos aparte (no hace falta: basta ampliar el roster de cruce);
convertir el heurístico en juicio semántico (movimiento 3 de issue #1, demand-pulled).
```

**Pista para `/speckit-plan` (`PLAN_HINT`)** — pega verbatim como `plan_hint`:

```text
Apóyate en `validation/base.py`: el helper genérico `_names_of(concept_cls)` y el accesor
`setting_names()` (clase `Setting`) son el patrón exacto a replicar para
`location_names()` (clase `NarrativeLocation`) y `object_names()` (clase `Object`), ambas
exportadas desde `bookwright.golem`. En `character_presence.validate()`, hoy
`roster = project.character_names()` alimenta tanto `_orphans` como `_roster_slugs`;
sepáralo: `_orphans` sigue con `character_names()`, pero el conjunto de slugs que
`_unknown_mentions` usa para suprimir se construye sobre la UNIÓN de los cuatro rosters
(reutiliza `_roster_slugs` pasándole la concatenación). NO cambies el guard `NotEvaluated`
(sigue clavado en `not character_names and not files`) ni la firma/forma de `Violation`.
Verifica empíricamente qué oráculos cambian y corrige solo conteos de warnings de
entidades ya declaradas. Diseño § 13. File-based (no SPARQL), sin dependencia nueva.
```

**Comando del workflow** (desde `main` limpio, con 041 ya liberada):

```bash
SPEC=$(cat <<'EOF'
…  # la Necesidad de 042, verbatim del bloque de arriba
EOF
)
PLAN_HINT=$(cat <<'EOF'
…  # la Pista de 042, verbatim del bloque de arriba
EOF
)
specify workflow run bookwright-quality \
  -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
```

Al verde: mergear a `main` (`Merge iteration 042: …` + `docs(claude): record iteration
042 merged`) y cortar la release `v0.5.2` con `bookwright-release` (§ 0.4, paso 4). Tras
la release, **vaciar § 1+ de este plan** (el trabajo entregado vive en git / `specs/` /
`CHANGELOG`) y dejar el roadmap como intención durable.

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
