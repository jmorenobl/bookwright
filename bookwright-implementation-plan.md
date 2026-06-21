# Bookwright — Plan de implementación con Spec Kit

> **Documento complementario a:** `bookwright-design.md` (el *cómo* técnico) y
> `bookwright-roadmap.md` (el *qué* y *por qué* a lo largo de versiones).
> **Propósito:** secuencia de iteraciones para el **hito en curso** de Bookwright.
> Cada iteración trae su prompt y el **comando del workflow** listo para ejecutar.
> **Audiencia:** Jorge (o cualquier desarrollador con Spec Kit instalado y
> `bookwright-design.md` en el root del repo).

> **Hito en curso: `v0.5.0` — validación robusta** (issue #1). El último track
> —endurecimiento post-dogfooding `v0.4.x` (iteraciones **034–038**, patches
> `v0.4.2`…`v0.4.6`)— está **cerrado y liberado** (2026-06-22); `__version__` es
> `0.4.6`, `main` está tageado y los cuatro gates verdes. Pero el dogfooding dejó
> claro que DEBT-004/007/008 eran **la misma clase** de defecto parcheada instancia a
> instancia, no tres bugs (issue #1). **`v0.5.0` cierra esa clase de raíz** en dos
> iteraciones (§ 1+): la **costura de prosa/estructura única** (039, cierra el
> acoplamiento de superficie) y el **resultado tri-valor** (040, cierra la falsa
> confianza "verde ≠ evaluado"). El *qué/por qué* durable vive en
> `bookwright-roadmap.md` § 3.
>
> **Es un minor, no un patch** (plan § 0.3): introduce arquitectura nueva (una capa
> compartida en `io/` + un contrato de resultado tri-valor), así que **039 y 040
> acumulan en `main`** y se liberan **una sola vez** como `v0.5.0` al cierre (040),
> al estilo de M4→`v0.2.0`. No se cortan patches `v0.5.x` por iteración.
>
> El detalle de las iteraciones **001–038** (M0–M5, `v0.3.1`…`v0.3.4`, `v0.4.0`, y
> los patches `v0.4.1`…`v0.4.6`) vive en el historial git, en `specs/001-…` …
> `specs/038-…` y en el `CHANGELOG` — **no** aquí. Este documento se **vacía del
> trabajo entregado** al cerrar cada hito; conserva solo el andamiaje reutilizable
> (§ 0 y § 7).
>
> **Qué viene tras `v0.5.0`:** el **horizonte demand-pulled** (`bookwright-roadmap.md`
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
- **Numeración:** los `specs/` van por `001`…`038`. El siguiente hito arranca en
  **039** y continúa la secuencia. Cada iteración es un branch `NNN-<short-name>` con
  su propio `specs/`.

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

## 1+. Iteraciones del hito en curso — `v0.5.0` (validación robusta)

Dos iteraciones, **en orden** (040 depende de 039). Acumulan en `main` sin tag
propio; la release `v0.5.0` se corta **una sola vez** al cierre de 040 (§ 0.3, § 0.4).
Origen: **issue #1** (discusión de diseño, etiqueta `validation`). El *qué/por qué*
durable está en `bookwright-roadmap.md` § 3.

### 1. Iteración 039 — Costura de prosa/estructura única (cierra la clase A)

Cierra el **acoplamiento a la prosa de superficie**: una sola capa markdown-aware que
los validadores consumen, en vez de que cada uno re-strippee el markdown que el propio
andamiaje emite. Subsume y borra los strippers locales de DEBT-004/007/008.

**Necesidad (`SPEC`)** — pega verbatim como `spec`:

```text
Necesidad: los validadores de prosa de Bookwright acoplan a la SUPERFICIE markdown
del manuscrito y la constitución, no a su estructura ya parseada, y cada uno
reimplementa por su cuenta cómo "ver más allá" del markdown que el propio andamiaje
emite. `character_presence` strippea el marcador de encabezado ATX antes de su
heurística de nombres propios (DEBT-008); `focalization` strippea viñeta + énfasis
alrededor de la etiqueta "Voz narrativa" y reconoce el placeholder `[PENDING: …]`
(DEBT-004/007); `setting_continuity` re-escanea `splitlines()` crudo. Es la misma
CLASE de defecto parcheada tres veces (issue #1): el próximo formato markdown nuevo
(un epígrafe, un `> blockquote`) volverá a abrir la grieta en el siguiente validador.

Esta iteración cierra la clase: una COSTURA de prosa/estructura única que todos los
validadores de prosa consumen, en vez de re-escanear el texto crudo. La costura vive
en `io/` (vecina de `frontmatter.py`, que ya lleva tracking de líneas), parsea un
fuente markdown (manuscrito o constitución) en líneas/bloques CLASIFICADOS —encabezado
ATX, viñeta, blockquote, run de énfasis, placeholder `[PENDING: …]`, prosa— con su
número de línea 1-based preservado, y expone una vista normalizada (el texto con los
marcadores estructurales de prefijo retirados) lista para que el heurístico de cada
validador corra sobre ella. `ValidationContext` gana accesor(es) cacheados que
devuelven esa vista (mismo patrón `_UNSET`/memo que `manuscript_files()` /
`constitution_text()`).

Los tres validadores (`character_presence`, `focalization`, `setting_continuity`) se
reescriben sobre la costura y sus normalizadores/strippers locales —`_HEADING_MARKER`
en `character_presence`; `_BULLET`, `_LEAD_EMPHASIS`, `_CLOSE_EMPHASIS`,
`_normalize_declaration_line` y el reconocedor `_PENDING_ONLY` en `focalization`; el
`splitlines()` a pelo de `setting_continuity`— SE BORRAN al quedar subsumidos por la
capa compartida.

Comportamiento esperado / criterios:
- CERO regresión en los fixtures vivos: toda la suite actual sigue verde sin cambiar
  oráculos (la vista normalizada reproduce byte a byte lo que hoy cada stripper
  produce — `# Capítulo 1` sigue exento, `Elena` en `# La caída de Elena` sigue
  disparando, la declaración `- **Voz narrativa**: …` sigue parseándose, el
  `[PENDING: …]`-solo sigue tratándose como no-declaración).
- El locator `relpath:línea` NO cambia: el número de línea sigue saliendo de
  `enumerate`, no del offset del match.
- GENERALIZACIÓN demostrada: un fixture nuevo de la SIGUIENTE superficie —una mención
  de personaje fuera de roster dentro de un `> blockquote` (o un epígrafe), una forma
  que hoy re-abriría la grieta— se maneja correctamente por la costura SIN tocar ningún
  validador, probando que la capa cierra la clase y no una instancia.
- SIN dependencia nueva (Constitución II): la costura es un clasificador determinista
  de bloques/líneas sobre las primitivas regex existentes, NO un parser/AST de markdown
  de terceros. Cada archivo ≤ 500 líneas.
- Validadores de prosa: sin grafo, `triples=()`, ontología congelada intacta
  (Principio X). El gate (solo `error` rompe CI) y las severidades no cambian.

Fuera de scope: el estado tri-valor (eso es la iteración 040); convertir el heurístico
en juicio semántico (movimiento 3 de la issue, demand-pulled); `factual_anchor`,
`temporal` y `narrative_structure`, que operan sobre el grafo/research y no escanean
prosa de superficie, no se tocan.
```

**Pista para `/speckit-plan` (`PLAN_HINT`)** — pega verbatim como `plan_hint`:

```text
Apóyate en `io/frontmatter.py` (precedente de tracking de líneas: parsea YAML
front-matter + body con `key_lines`) y en `validation/base.py:148-257` (el patrón de
accesor cacheado `_UNSET`/memo de `ValidationContext`). Crea un módulo nuevo en `io/`
(p. ej. `io/prose.py`) que, dado un fuente markdown, devuelva un documento parseado:
una lista ordenada de líneas clasificadas (kind ∈ {heading, bullet, blockquote,
emphasis, placeholder, prose}) cada una con su número de línea 1-based y un campo
`normalized` (la línea con su marcador estructural de prefijo retirado — ATX `#{1,6} `,
viñeta/blockquote `[-*+>] `, run de énfasis líder), reproduciendo EXACTAMENTE lo que
hoy strippean `_HEADING_MARKER` / `_BULLET` / `_LEAD_EMPHASIS` / `_CLOSE_EMPHASIS`, más
un predicado `is_placeholder` equivalente a `_PENDING_ONLY` (`^\s*\[pending…\]\s*$`).
`ValidationContext` gana accesores cacheados `manuscript_view()` / `constitution_view()`.
Reescribe `character_presence` para iterar el prose-scan de la vista (sin
`_HEADING_MARKER` local), `focalization` para localizar su declaración sobre las líneas
normalizadas + consultar `is_placeholder`, y `setting_continuity` para escanear las
líneas de la vista. Determinismo y locators intactos. Diseño § 13. Sin librería de
markdown (Constitución II).
```

**Comando del workflow** (desde `main` limpio):

```bash
SPEC=$(cat <<'EOF'
…  # la Necesidad de 039, verbatim del bloque de arriba
EOF
)
PLAN_HINT=$(cat <<'EOF'
…  # la Pista de 039, verbatim del bloque de arriba
EOF
)
specify workflow run bookwright-quality \
  -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
```

Al verde: mergear a `main` con el patrón `Merge iteration 039: …` + `docs(claude):
record iteration 039 merged` (voltea la fila de la tabla y la prosa de estado).
**No** se corta release aquí (acumula para `v0.5.0`).

---

### 2. Iteración 040 — Resultado tri-valor: `evaluado` / `no-evaluado(motivo)` (cierra la clase B)

Cierra la **falsa confianza**: que `[]` deje de leerse igual que "limpio" cuando en
realidad fue "no pude mirar". **Depende de 039** (la detección de placeholder de la
costura alimenta el motivo "voz sin responder"). Cierra el hito → release `v0.5.0`.

**Necesidad (`SPEC`)** — pega verbatim como `spec`:

```text
Necesidad: un validador de Bookwright devuelve `list[Violation]`, y una lista vacía
`[]` es INDISTINGUIBLE entre dos cosas opuestas: "evalué y está limpio" y "no tuve
forma de mirar". Para una herramienta de autoría, la FALSA CONFIANZA es peor fallo que
el ruido: DEBT-004 fue, literalmente, un validador DORMIDO Y VERDE durante todo v0.4
(la declaración de voz no parseaba, así que `focalization` retornaba `[]` y se leía
como "focalización OK"). Hoy `focalization` retorna `[]` cuando no hay constitución, no
hay declaración de voz parseable, o la voz sigue en `[PENDING]`;
`character_presence` / `setting_continuity` retornan `[]` sobre un manuscrito vacío.
Todo eso se pinta verde.

Esta iteración cierra la clase (issue #1, movimiento 2): el resultado de un validador
pasa de "lista de hallazgos" a TRI-VALOR — `evaluado` (con o sin hallazgos) frente a
`no-evaluado(motivo)`. Los retornos-tempranos-`[]` de "no pude mirar" se vuelven
`no-evaluado` con un motivo legible (p. ej. "la constitución no declara voz narrativa",
"la declaración de voz sigue sin responder ([PENDING])", "el manuscrito está vacío").
El runner, el report, el sobre `--json` de `bookwright validate`, `bookwright status`
(y su `next_actions`) y las skills exponen el tercer estado, de modo que VERDE
signifique "evaluado y limpio", no "no se miró".

Comportamiento esperado / criterios:
- El contrato del `Validator` Protocol (`validation/base.py`, diseño § 13.1) crece para
  que un validador declare por corrida si EVALUÓ o NO-EVALUÓ(motivo), ADEMÁS de sus
  `Violation`. Se actualiza `bookwright-design.md § 13.1` ANTES de divergir el código
  (plan § 7.3).
- El estado es ADITIVO y NO rompe el gate: solo los `Violation` de severidad `error`
  siguen rompiendo CI; un `no-evaluado` NO es fallo de gate (no es un hallazgo) pero SÍ
  es visible — nunca se confunde con limpio. La forma de `Violation` y de
  `ValidatorError` (los validadores que PETAN, canal `errors[]`) no cambia; `no-evaluado`
  es un tercer canal distinto de `errors[]` (que es para fallos de carga/ejecución, no
  para el que decide conscientemente no evaluar).
- El sobre `--json` gana un canal para los `no-evaluado` (nombre del validador + motivo),
  hermano de `findings` / `errors`. `bookwright status` lo refleja en el estado derivado
  y, donde aplique, en `next_actions` (p. ej. "declara la voz narrativa en la
  constitución para activar `focalization`"). Las skills que leen `status` al arrancar
  lo muestran.
- Los validadores que hoy retornan `[]` por "no pude mirar" migran al estado nuevo:
  `focalization` (sin constitución / sin declaración parseable / voz en `[PENDING]`,
  reusando la detección de placeholder de la costura de 039), y el manuscrito-vacío de
  `character_presence` / `setting_continuity`. Un validador que evalúa y no encuentra
  nada sigue siendo `evaluado` con cero hallazgos (verde legítimo).
- CERO regresión funcional en los hallazgos existentes: los fixtures que hoy producen
  `Violation` siguen produciéndolos; lo único que cambia es que el "no pude mirar" deja
  de leerse como verde. `mypy --strict` y los cuatro gates verdes.
- Esta iteración CIERRA el hito v0.5.0: tras mergear, se corta la release `v0.5.0` con
  la skill `bookwright-release` (bump `__version__` a `0.5.0`, sección CHANGELOG, edición
  de estado en CLAUDE.md/diseño, commit de release, tag anotado) — una sola vez, por
  ambas iteraciones (039+040).

Fuera de scope: la costura de superficie (iteración 039, precede a esta); el juicio
semántico LLM (movimiento 3 de la issue, demand-pulled); añadir validadores nuevos.
```

**Pista para `/speckit-plan` (`PLAN_HINT`)** — pega verbatim como `plan_hint`:

```text
Apóyate en `validation/base.py` (`Violation`, `ValidatorError`, el `Validator` Protocol,
`ValidationContext`), `validation/runner.py`, el report/sobre de `commands/validate`,
`commands/status`, y las plantillas de skills que leen `status` al arrancar; diseño
§ 13.1. Prefiere un RESULTADO EXPLÍCITO —p. ej. el validador devuelve un pequeño
resultado frozen (`ValidationOutcome` con `evaluated: bool`, `reason: str | None`,
`violations: tuple[Violation, ...]`), o el runner deriva el estado de un señal opt-in
`not_evaluated(reason)`— antes que sobrecargar `Violation`/`Severity` (un `Violation`
centinela de severidad `info` confundiría "no evaluado" con "hallazgo informativo"). El
gate sigue clavado solo en hallazgos `error`. El sobre `--json` gana un array
`not_evaluated[]` (validator, reason) hermano de `findings`/`errors`. Actualiza
`bookwright-design.md § 13.1` antes de tocar el Protocol. Puede pasar de ~10 tareas en
`/speckit-tasks` → si es así, divídela (plan § 7.2).
```

**Comando del workflow** (desde `main` limpio, con 039 ya mergeada):

```bash
SPEC=$(cat <<'EOF'
…  # la Necesidad de 040, verbatim del bloque de arriba
EOF
)
PLAN_HINT=$(cat <<'EOF'
…  # la Pista de 040, verbatim del bloque de arriba
EOF
)
specify workflow run bookwright-quality \
  -i spec="$SPEC" -i plan_hint="$PLAN_HINT" -i integration=claude
```

Al verde: mergear a `main` (`Merge iteration 040: …` + `docs(claude): record iteration
040 merged`) y **cortar `v0.5.0`** con `bookwright-release` (§ 0.4, paso 4 — una sola vez
por el hito minor). Tras la release, **vaciar § 1+ de este plan** (el trabajo entregado
vive en git / `specs/` / `CHANGELOG`) y dejar el roadmap como intención durable.

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
