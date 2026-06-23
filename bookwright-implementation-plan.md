# Bookwright — Plan de implementación con Spec Kit

> **Documento complementario a:** `bookwright-design.md` (el *cómo* técnico) y
> `bookwright-roadmap.md` (el *qué* y *por qué* a lo largo de versiones).
> **Propósito:** secuencia de iteraciones para el **hito en curso** de Bookwright.
> Cada iteración trae su prompt y el **comando del workflow** listo para ejecutar.
> **Audiencia:** Jorge (o cualquier desarrollador con Spec Kit instalado y
> `bookwright-design.md` en el root del repo).

> **Hito en curso: `v0.5.x` — endurecimiento post-dogfood** (DEBT-011/012). El hito
> `v0.5.0` —validación robusta (issue #1): la **costura de prosa/estructura única** (039)
> y el **resultado tri-valor** (040)— está **cerrado y liberado** (2026-06-22). Sus dos
> primeros patches de endurecimiento también: **041** cerró DEBT-009 (la raya de diálogo
> `—`, en la costura `io/prose.py`) → `v0.5.1`, y **042** cerró DEBT-010 (`character_presence`
> cruza contra la unión de rosters character/setting/location/object) → `v0.5.2`
> (2026-06-22). Ambas mergeadas y tageadas, los cuatro gates verdes. Su detalle vive en git
> (`specs/041-…`, `specs/042-…`) y en el `CHANGELOG` — **no** aquí.
>
> Un **segundo dogfood end-to-end** sobre `v0.5.2` —`sombra-en-el-puerto`, una **novela
> negra** con diálogo denso en dos estilos (raya `—` y comilla angular `«»`), 2026-06-23,
> banco desechable fuera del repo— destapó tres falsos positivos más de `character_presence`,
> registrados en `DEBT.md`. Confirmó que las correcciones previas funcionan (las líneas de
> diálogo con raya y la primera palabra del encabezado YA no disparan), y aisló lo que queda:
> **DEBT-011** (primer término tras una **comilla-líder de apertura** `«`/`"`/`'` — la misma
> costura de 039/041, otro marcador; `«Inspectora`, `«Las` espurios), **DEBT-012** (el **cuerpo
> de un encabezado** se escanea como prosa pasada la primera palabra; `# Capítulo 1 — Marea
> baja` dispara sobre `Marea`) y **DEBT-013** (**nombres de organización** off-roster; `Naviera`
> de "la Naviera Salas" — límite *semántico* del heurístico, no de superficie).
>
> **Es un track de endurecimiento → un patch por iteración** (plan § 0.3): **043** cierra
> DEBT-011 (`v0.5.3`, gemela de 041 — solo costura `io/prose.py`) y **044** cierra DEBT-012
> (`v0.5.4` — política de no-prosa para el cuerpo del encabezado). Son **independientes** (orden
> por prioridad: 043 primero, es la clase de issue #1 ya registrada). **DEBT-013 NO entra
> como iteración**: su arreglo no vive en la costura, exige una decisión de diseño previa
> (5ª clase de roster «organización» **vs.** el movimiento 3 / juicio semántico) que es
> materia de la **issue #1**, no un patch listo. El *qué/por qué* durable vive en
> `bookwright-roadmap.md` § 3.
>
> El detalle de las iteraciones **001–042** (M0–M5, `v0.3.1`…`v0.3.4`, `v0.4.0`, los
> patches `v0.4.1`…`v0.4.6`, el minor `v0.5.0` y los patches `v0.5.1`/`v0.5.2`) vive en el
> historial git, en `specs/001-…` … `specs/042-…` y en el `CHANGELOG` — **no** aquí. Este
> documento se **vacía del trabajo entregado** al cerrar cada hito; conserva solo el
> andamiaje reutilizable (§ 0 y § 7).
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

## 1+. Iteraciones del track en curso — `v0.5.x` (endurecimiento post-dogfood)

Dos iteraciones **independientes** (043 toca solo la costura `io/prose.py`; 044 toca
`character_presence.py` —y quizá la costura— para tratar el cuerpo del encabezado como
no-prosa). Cada una es un **patch** con un delta observable y se libera por separado
(043 → `v0.5.3`, 044 → `v0.5.4`); el orden es por prioridad (043 primero, cierra la clase
de issue #1 ya registrada como DEBT-011), no por dependencia. Origen: **segundo dogfood
end-to-end —`sombra-en-el-puerto`, novela negra— sobre `v0.5.2`** (2026-06-23, banco
desechable fuera del repo), registrado en `DEBT.md` (DEBT-011/012). El *qué/por qué*
durable está en `bookwright-roadmap.md` § 3.

> **DEBT-013 (nombres de organización, `Naviera`) NO está aquí a propósito.** Su arreglo
> no vive en la costura: exige una **decisión de diseño** previa —una 5ª clase de roster
> «organización» (amplía la ingestión, roza el Principio X) **vs.** diferirlo al juicio
> semántico (movimiento 3 de issue #1)— que es materia de la **issue #1**, no un patch
> listo. Queda registrado en `DEBT.md` como pendiente de esa decisión; no se promueve a
> iteración hasta resolverla.

### 1. Iteración 043 — La costura de prosa reconoce la comilla-líder de apertura `«`/`"`/`'` (cierra DEBT-011)

Cierra DEBT-011: `character_presence` marca el primer término tras una **comilla de
apertura líder** (`«Inspectora` → "Inspectora", `«Las` → "Las" reportados como nombre
propio sin entrada en la bible). Es la **misma clase y la misma costura** que 041 cerró
para la raya de diálogo — otro marcador líder de superficie que la normalización de 039
aún no retira. El arreglo vive **solo en la costura compartida** (`io/prose.py`), no en un
stripper local — meterlo en `character_presence` reintroduciría la deuda que 039 saldó.
Confirmado empíricamente por el dogfood `sombra-en-el-puerto`: `«Las` es especialmente
elocuente —`Las` es un artículo, no un nombre propio; solo se marca por el desplazamiento
de offset que mete la `«`, prueba de que el fallo es de superficie y no de léxico.

El `SPEC` (Necesidad) y el `PLAN_HINT` (Pista para `/speckit-plan`) van **rellenos
verbatim** dentro del comando de copia-pega de abajo (fuente única, sin duplicar).

**Comando del workflow** (desde `main` limpio) — **copia-pega completo en la terminal**:

```bash
SPEC=$(cat <<'EOF'
Necesidad: en prosa española y de muchas otras tradiciones el diálogo o la cita se abren
con una comilla de apertura LÍDER pegada al texto: la angular `«` (U+00AB), la tipográfica
`"` (U+201C) o la simple `'` (U+2018), y a veces la recta ASCII `"`/`'`. La costura de
prosa única de Bookwright (`io/prose.py`, iteración 039) ya normaliza los marcadores de
bloque ASCII (encabezado ATX, viñeta/blockquote) y —tras 041— las rayas de diálogo
`—`/`–`/`―`, pero NO reconoce estas comillas de apertura. Como consecuencia,
`character_presence` ve `«Inspectora —dijo él` con la `«` aún pegada: el término
`Inspectora` no queda en offset 0, así que la exención de inicio-de-frase no dispara y se
reporta como nombre propio sin entrada en la bible. Lo mismo con `«Las malas noticias…`:
`Las` —un ARTÍCULO, ni siquiera un nombre propio— se marca solo por el desplazamiento de
offset que introduce la `«`. En una novela con diálogo entrecomillado esto inunda de
warnings espurios el primer término de cada línea citada, ahogando los hallazgos reales.
Son `warning`, así que no vetan el gate, pero es exactamente el fallo de superficie que
issue #1 quería cerrar de raíz, y la costura de 039/041 lo dejó abierto para la comilla.
Detectado y confirmado empíricamente por el dogfood end-to-end `sombra-en-el-puerto`
(novela negra) sobre `v0.5.2` (DEBT-011 en `DEBT.md`).

Esta iteración cierra DEBT-011 en la COSTURA, no en el validador, exactamente como 041
hizo con la raya: `io/prose.py` añade la comilla de apertura líder al conjunto de
marcadores estructurales que su normalización retira. Tras normalizar, el primer término
de contenido de la línea citada queda en offset 0 y hereda la exención de inicio-de-frase
YA existente en `character_presence`. En consecuencia NINGÚN validador se toca: el arreglo
es puramente de la capa compartida, lo que prueba que cierra la CLASE (cualquier validador
de prosa se beneficia), no una instancia.

Comportamiento esperado / criterios:
- `character_presence` deja de marcar el primer término tras una comilla de apertura
  líder: `«Inspectora —dijo él` no reporta `Inspectora`; `«Las malas noticias` no reporta
  `Las`. El arreglo vive SOLO en `io/prose.py`; no se edita ningún validador (criterio de
  que la clase se cierra en la costura).
- Solo se retira la comilla de apertura LÍDER (anclada en `^`, tolerando whitespace
  previo, sufijo `\s*` porque suele ir pegada: `«Las`). El conjunto cubre `«` (U+00AB),
  `"` (U+201C), `'` (U+2018) y las rectas ASCII `"`/`'`. La comilla de CIERRE (`»`/`"`/`'`)
  y cualquier comilla a mitad de línea (contenido citado interno) NO se tocan.
- Interacción con `¿`/`¡`: si la línea es `«¿Quién…` la apertura líder se retira y el
  signo de apertura de interrogación/exclamación —que `_SENTENCE_END` ya trata— sigue
  cubriendo el inicio de frase; verifícalo con un caso explícito.
- CERO regresión en los fixtures vivos sin tocar oráculos salvo donde HOY exista un falso
  positivo de comilla líder: verifícalo EMPÍRICAMENTE corriendo la suite. Si algún oráculo
  contaba un warning espurio de comilla, se corrige a la baja (el manuscrito del fixture
  NO se toca), igual que 041 corrigió `5 → 4` y 038 `6 → 5`.
- El locator `relpath:línea` NO cambia: el número de línea sigue saliendo de `enumerate`,
  no del offset del match; la normalización solo afecta al texto escaneado.
- GENERALIZACIÓN demostrada: un caso con una mención de personaje fuera de roster
  MID-línea dentro de una cita (p. ej. `«Pregúntale a Quirón», dijo.`) sigue disparando
  sobre `Quirón`, mientras que el término líder no dispara — probando que solo se
  neutraliza el marcador líder, no el contenido citado.
- SIN dependencia nueva (Constitución II): la comilla se reconoce con una regex
  determinista anclada (como `_DIALOGUE_MARKER`/`_BULLET_MARKER`), NO con un parser de
  markdown de terceros. Cada archivo ≤ 500 líneas. Validadores de prosa sin grafo,
  `triples=()`, ontología congelada intacta (Principio X); el gate (solo `error` rompe CI)
  y las severidades no cambian.
- Borra la entrada DEBT-011 de `DEBT.md` (git conserva el historial).

Fuera de scope: el cuerpo del encabezado escaneado como prosa (eso es DEBT-012 / iteración
044); los nombres de organización off-roster (DEBT-013, pendiente de decisión de diseño);
convertir el heurístico de nombres propios en juicio semántico (movimiento 3 de issue #1,
demand-pulled); cualquier validador que no escanee prosa de superficie.
EOF
)
PLAN_HINT=$(cat <<'EOF'
Apóyate en `io/prose.py` (la costura de 039/041): `_normalize` retira iterativamente los
prefijos vía `_HEADING_MARKER` (`^#{1,6}\s+`), `_BULLET_MARKER` (`^\s*[-*+>]\s+`) y —tras
041— `_DIALOGUE_MARKER` (`^\s*[—–―]\s*`). Añade un `_OPENING_QUOTE_MARKER` análogo —p. ej.
`^\s*[«"'""]\s*` (comilla angular U+00AB, tipográficas U+201C/U+2018, rectas ASCII; sufijo
`\s*` porque la comilla va pegada al texto, `«Las`)— y aplícalo en `_normalize` dentro del
mismo bucle de stripping, una pasada por marcador (`sub(count=1)`), de modo que solo la
comilla de APERTURA líder se retire y las de cierre / internas queden intactas. NO toques
`character_presence`: con la comilla retirada, `_is_sentence_initial(scan, match.start())`
ve el primer término en prefijo vacío y lo exime, igual que la raya en DEBT-009 y el
encabezado ATX en DEBT-008. Verifica empíricamente qué oráculos cambian (`uv run pytest`)
y corrige solo conteos de falsos positivos de comilla (sin tocar manuscritos de fixture).
Añade casos de prosa: una cita con mención MID-línea que siga disparando, y `«¿Quién…`
para la interacción con `¿`. Diseño § 13. Sin librería de markdown (Constitución II).
EOF
)
specify workflow run bookwright-quality \
  -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
```

Al verde: mergear a `main` (`Merge iteration 043: …` + `docs(claude): record iteration
043 merged`) y cortar la release `v0.5.3` con `bookwright-release` (§ 0.4, paso 4).

---

### 2. Iteración 044 — `character_presence` trata el cuerpo del encabezado como no-prosa (cierra DEBT-012)

Cierra DEBT-012: DEBT-008 retira el marcador ATX y exime solo la PRIMERA palabra del
encabezado, pero el RESTO del título se sigue escaneando como prosa. Así, una palabra
capitalizada tras la raya interna de un título (`# Capítulo 1 — Marea baja` → `Marea`) se
reporta como nombre propio sin entrada en la bible. Un título de capítulo es texto
editorial, no prosa narrativa: sus nombres propios son estilísticos y los personajes
reales del capítulo se mencionan igual en el cuerpo. Detectado por el dogfood
`sombra-en-el-puerto` sobre `v0.5.2` (DEBT-012 en `DEBT.md`).

El `SPEC` (Necesidad) y el `PLAN_HINT` (Pista para `/speckit-plan`) van **rellenos
verbatim** dentro del comando de copia-pega de abajo (fuente única, sin duplicar).

**Comando del workflow** (desde `main` limpio, con 043 ya liberada) — **copia-pega
completo en la terminal**:

```bash
SPEC=$(cat <<'EOF'
Necesidad: el validador `character_presence`, en su regla de menciones-desconocidas,
escanea cada línea del manuscrito en busca de nombres propios sin entrada en la bible.
DEBT-008 (iteración 038) añadió que se retire el marcador ATX líder de un encabezado
(`#{1,6} `) para que su PRIMERA palabra caiga en offset 0 y herede la exención de
inicio-de-frase: por eso `# Capítulo 1 — Marea baja` ya no marca `Capítulo`. Pero el RESTO
del título se sigue escaneando como prosa, así que `Marea` —segunda mayúscula del título,
tras la raya interna `—`— se reporta como nombre propio sin entrada en la bible. Un título
de capítulo NO es prosa narrativa: es texto editorial cuyas mayúsculas son estilísticas
(un personaje real del capítulo aparece igual en el cuerpo y allí se cruza con el roster).
Reportar nombres propios del título es ruido sistemático en toda novela con subtítulos de
capítulo. Detectado por el dogfood end-to-end `sombra-en-el-puerto` sobre `v0.5.2`
(DEBT-012 en `DEBT.md`).

Esta iteración cierra DEBT-012: una línea de encabezado (la que hoy reconoce el marcador
ATX) se trata como NO-PROSA para la regla de menciones-desconocidas — se exime el título
ENTERO del heurístico de nombres propios, no solo su primera palabra. La regla de
huérfanos (`error`) y el guard `NotEvaluated` (iteración 040) NO cambian.

Comportamiento esperado / criterios:
- `character_presence` deja de reportar CUALQUIER nombre propio que aparezca dentro de una
  línea de encabezado: `# Capítulo 1 — Marea baja` no reporta `Marea` (ni ningún otro
  término del título). El cuerpo de prosa normal se sigue escaneando igual.
- La detección de "esto es un encabezado" reutiliza el reconocimiento ATX que YA existe
  (el mismo `^#{1,6}\s+` de DEBT-008 / la costura), sin un segundo reconocedor divergente.
  Decidir en plan si la exención se expresa en la costura (`io/prose.py` señala/!devuelve
  la línea como encabezado) o como política anclada en `character_presence` que salta la
  línea entera; lo que NO se hace es seguir escaneando el título palabra a palabra.
- La regla de huérfanos (`error`) NO cambia: un personaje cuya ÚNICA mención estuviera en
  un título es un caso degenerado que el cuerpo real siempre cubre; los hallazgos `error`
  existentes salen byte a byte iguales (protege el gate, como 040/042).
- El guard `NotEvaluated` de 040 NO cambia: el motivo textual y la condición
  (`not roster and not files`) son idénticos.
- CERO regresión funcional: verifícalo EMPÍRICAMENTE (`uv run pytest`). Donde un oráculo
  contara un warning de un término dentro de un título, se corrige a la baja (sin tocar
  manuscritos ni bible de fixture). Un nombre propio fuera de roster en PROSA NORMAL (no
  en un título) sigue disparando.
- El locator `relpath:línea` NO cambia para los hallazgos que sí disparan; la numeración
  sigue saliendo de `enumerate`.
- Validador de prosa: file-based, `triples=()`, sin grafo, ontología congelada intacta
  (Principio X). El gate y las severidades no cambian. SIN dependencia nueva (Constitución
  II); regex determinista, NO parser de markdown. Cada archivo ≤ 500 líneas.
- Borra la entrada DEBT-012 de `DEBT.md` (git conserva el historial).

Fuera de scope: la comilla de apertura líder (DEBT-011 / iteración 043); los nombres de
organización off-roster (DEBT-013, pendiente de decisión de diseño); reconocer encabezados
Setext (`====`/`----` en la línea siguiente) o encabezados indentados —si aparecen en un
dogfood futuro serán su propia entrada—; convertir el heurístico en juicio semántico
(movimiento 3 de issue #1, demand-pulled).
EOF
)
PLAN_HINT=$(cat <<'EOF'
Apóyate en el reconocimiento de encabezado que YA existe: `_HEADING_MARKER` (`^#{1,6}\s+`)
en `io/prose.py` (DEBT-008/039) y su uso en `character_presence._unknown_mentions`, donde
hoy `_HEADING_MARKER.sub("", line, count=1)` retira el marcador pero deja el cuerpo para
escanear. El cambio mínimo: si la línea casa `_HEADING_MARKER`, SALTAR la línea entera en
la regla de menciones-desconocidas (no escanear ningún token del título), en vez de
recortar solo el marcador. Evalúa en `/speckit-plan` si conviene que la costura exponga
"esta línea es encabezado" (un predicado reutilizable) en lugar de duplicar el regex en el
validador — preferible si algún otro validador de prosa querrá la misma política. NO toques
la regla de huérfanos ni el guard `NotEvaluated`. Verifica empíricamente qué oráculos
cambian y corrige solo conteos de warnings dentro de títulos. Añade un caso: un encabezado
con un nombre propio fuera de roster (`# La caída de Elena`) NO dispara, pero el mismo
`Elena` en PROSA fuera de roster sí. Diseño § 13. Sin librería de markdown.
EOF
)
specify workflow run bookwright-quality \
  -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
```

Al verde: mergear a `main` (`Merge iteration 044: …` + `docs(claude): record iteration
044 merged`) y cortar la release `v0.5.4` con `bookwright-release` (§ 0.4, paso 4). Tras
la release, si DEBT-013 sigue sin decisión de diseño y no hay más deuda abierta del track,
**vaciar § 1+ de este plan** (el trabajo entregado vive en git / `specs/` / `CHANGELOG`) y
dejar el roadmap como intención durable.

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
