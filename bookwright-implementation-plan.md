# Bookwright — Plan de implementación con Spec Kit

> **Documento complementario a:** `bookwright-design.md`.
> **Propósito:** secuencia de iteraciones para el **siguiente hito** de Bookwright,
> M5 — Orquestación de contexto (el "hilo conductor"). Cada iteración tiene un
> prompt listo para invocar `/speckit-specify`.
> **Audiencia:** Jorge (o cualquier desarrollador con Spec Kit instalado y
> `bookwright-design.md` en el root del repo).

> **Nota sobre versiones anteriores de este plan:** las iteraciones 1–18
> (hitos M0–M4, releases `v0.1.0` y `v0.2.0`) ya están **completadas y mergeadas
> en `main`**. Su detalle vive ahora en el historial git, en `specs/001-…` … `specs/018-…`
> y en el `CHANGELOG`. Este documento se ha vaciado de ellas a propósito: solo
> describe el trabajo **por hacer**. El registro de lo hecho es `CLAUDE.md`
> (tabla de iteraciones) y los `specs/` por iteración.

---

## 0. Estado y cómo usar este documento

### 0.1 Punto de partida

- `v0.1.0` (M0–M3, iteraciones 1–12) y `v0.2.0` (M4, iteraciones 13–18) están en
  `main`: paquete real en `src/bookwright/`, suite de tests, docs y gates verdes.
- El repo ya está inicializado con Spec Kit (`.specify/`, `.claude/skills/speckit-*`)
  y tiene su constitución ratificada (`.specify/memory/constitution.md`, v1.3.0).
- **No hay que re-bootstrapear ni recrear la constitución.** Este hito construye
  sobre el código existente.

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
  branch de este hito puede dejar `bookwright` roto a mitad: si una iteración
  no se llega a completar, lo ya mergeado debe seguir pasando todos los gates.

### 0.3 Numeración

Los `specs/` van por `001`…`018`. Este hito **arranca en 019** y continúa la
secuencia. Cada iteración es un branch `NNN-<short-name>` con su propio `specs/`.

---

## 1. El hito: M5 — Orquestación de contexto (v0.3.0)

### 1.1 El problema

Spec Kit "sabe qué planificar" cuando ejecutas `/speckit-plan` porque tiene una
**máquina de estados con un puntero al estado actual**: el branch `NNN-name` +
el directorio `specs/NNN/` responden a "¿dónde estoy y qué he decidido?", y cada
comando lee los artefactos previos y escribe el siguiente. La intención se
declara **una vez** (`/speckit-specify "…"`) y queda persistida.

Bookwright hoy no tiene ese hilo. Sus skills (`bookwright-research`,
`bookwright-verify`, los 10 commands…) son herramientas *à la carte*: leen el
corpus en texto plano, pero **no hay un puntero de foco** ("qué estoy trabajando
ahora") ni un artefacto que cada skill consulte para orientarse. Síntoma
observado en uso real: en una sesión nueva, `bookwright-research` no tenía de
dónde inferir qué investigar y **preguntó el tema en blanco** — algo que en Spec
Kit no pasa porque el `spec.md` ya está ahí.

Y escribir un libro **no es lineal** (saltas entre biblia, redacción,
investigación, validación, verificación). Eso hace el hilo conductor *más*
necesario, no menos: como no hay una secuencia fija "después de X viene Y", el
"qué hacer ahora" hay que **computarlo desde el estado**, no cablearlo.

### 1.2 El diseño (tres capas, separadas a propósito)

```
CLI  bookwright status   →  hechos derivados + acción sugerida   [DETERMINISTA, testeable]
Skill (el LLM lo lee)    →  prioriza, redacta, investiga         [NO determinista, fuera del CLI]
```

1. **Estado autoral — el foco/intención.** Pequeño, lo escribe el autor, vive en
   **texto plano canónico** (un bloque `[focus]` en `manifest.toml`): qué se
   trabaja ahora + hilos/decisiones pendientes. Es la "bitácora" mínima. No se
   computa.

2. **Estado derivado — el "qué falta / qué sigue".** **Computado**, no escrito a
   mano: anclas sin fuentes suficientes, preguntas de investigación abiertas,
   hallazgos de baja fiabilidad, violaciones de validación. Es una **función
   pura** del grafo (SPARQL), igual de determinista que `bookwright validate` —
   que ya es estado derivado. Se cachea en `.bookwright/cache/status.json` (como
   `graph.ttl`: **caché derivada, reconstruible, nunca fuente de verdad**,
   Principio I). Encima, una **tabla de reglas estática** hecho→acción produce
   `next_actions`: skill recomendada + prompt listo para pegar. Determinista y
   unit-testeable.

3. **Juicio — la skill (LLM).** Priorizar, redactar con matiz, **hacer la
   investigación**. Lo único no determinista, y por eso vive *por encima* de la
   frontera del CLI.

**Principio rector:** *El estado se computa, nunca se inventa; el juicio vive en
las skills, no en el CLI. La verdad sigue en texto plano; `status.json` es una
proyección efímera.*

Esto respeta las restricciones duras: Principio I (texto plano fuente de verdad;
`status.json` es caché), Principio IX (`--json` sobre stdout, prosa a stderr),
Principio X (**ontología congelada**: `status` solo consulta SPARQL, no añade
clases GOLEM), Principio VIII (la parte determinista —hechos y `next_actions`— es
testeable; el juicio queda fuera del gate).

### 1.3 Encaje en el roadmap

Este hito **toma el hueco de `v0.3.0`**. La búsqueda vectorial (antes prevista
como v0.3) se desplaza a **v0.4**, y el export a **v1.0**. Es una decisión de
roadmap visible y reversible: si se prefiere mantener vectores en v0.3, basta con
renumerar el release de este hito (el plan no cambia). Siguen descartados
(decisión de owner): presets, GrafeoIndexer/Grafeo, multi-integración más allá de
`claude`/`generic`, extension system.

### 1.4 El doc de diseño

El diseño canónico de este hito **ya está consolidado en `bookwright-design.md`
§ 21** (Orquestación de contexto), ratificado como extensión que no reabre ningún
axioma de § 16. Los prompts de abajo lo citan como referencia durable, junto con
§ 8 (manifiesto, para `[focus]`), § 13 (validación, reutilizada por `status`) y
§ 20 (investigación, de donde sale la cola `bw:open`/anclas). Si durante la
implementación algo de § 21 no encaja con la realidad técnica, actualiza el diseño
**antes** de divergir el código (nota 4.3).

---

## 2. Mapa de iteraciones

| # | Título | Depende de | Hito |
|---|---|---|---|
| 019 | Estado de foco autoral: bloque `[focus]` + `bookwright focus` | 2 | M5 |
| 020 | `bookwright status`: motor de estado derivado + `next_actions` | 6, 11, 13, 15, 019 | M5 |
| 021 | `bookwright-research` consume anclas / preguntas abiertas | 14, 020 | M5 |
| 022 | Skills leen `status` al iniciar + bloque "Próximos pasos" | 9, 020, 021 | M5 |
| 023 | Fixture E2E del bucle, workflow test, docs y release v0.3.0 | 019–022 | M5 |

Las iteraciones se ejecutan en orden: cada una depende de artefactos de las
previas. 019 (autoral) y 020 (derivado) son los cimientos; 021 resuelve el dolor
concreto observado; 022 cierra el bucle en toda la suite de skills; 023 lo prueba
de extremo a extremo, lo documenta y libera `v0.3.0`.

Estimación: medio día a dos días de agente + revisión humana por iteración;
~1–1.5 semanas el hito completo.

---

## 3. Iteraciones detalladas

### Iteración 019 — Estado de foco autoral: bloque `[focus]` + `bookwright focus`

**Objetivo:** dar al proyecto un puntero de foco persistente y editable —el hilo
conductor en su versión mínima— en texto plano canónico, sin tocar nada del flujo
existente.

**Prompt:**

```
/speckit-specify

Necesidad: un proyecto Bookwright no tiene hoy ningún sitio donde quede registrado "qué estoy trabajando ahora" ni los hilos o decisiones pendientes. Al abrir una sesión nueva, esa intención se pierde y las skills no tienen de dónde orientarse. Necesitamos un estado de foco pequeño, escrito por el autor, persistido en texto plano canónico, que cualquier skill o comando pueda leer.

Comportamiento esperado:

- El manifest.toml admite un bloque opcional [focus] con: target (texto, qué se trabaja ahora, p. ej. "arco de Berlín" o "cap-04"), notes (texto libre, hilos y decisiones pendientes a modo de bitácora breve) y updated_at (fecha ISO 8601, que el CLI fija automáticamente al escribir).
- `bookwright focus show` muestra el foco actual de forma legible; con --json emite el bloque como JSON. Si no hay bloque [focus], indica con claridad "sin foco definido" (y un --json equivalente), sin error.
- `bookwright focus set --target "<texto>" [--notes "<texto>"]` crea o actualiza el bloque, fija updated_at a la fecha actual, y preserva el resto del manifest (comentarios y formato incluidos).
- `bookwright focus clear` elimina el bloque [focus] del manifest.
- El bloque es enteramente opcional: su ausencia no afecta a ningún otro comando (graph, validate, init…). Un proyecto v0.2 existente sigue funcionando igual.

Validaciones:

- target y notes son cadenas; se rechaza target vacío en `focus set`.
- updated_at se valida como fecha ISO al cargar; un valor inválido produce un error de manifest claro (no un crash).

Fuera de scope:

- El estado DERIVADO (anclas, validación, etc.) y el comando `bookwright status`: iteración 020.
- Las recomendaciones de siguiente paso (next_actions): iteración 020.
- Que las skills lean o escriban el foco: iteraciones 021–022.
- Un historial append-only / bitácora con versiones: fuera de este hito (sería over-engineering; el foco actual + notes basta para el bucle).

Referencia: ver bookwright-design.md § 8 (spec del manifest.toml) — el bloque [focus] lo extiende; documentarlo allí. Principio I (texto plano), Principio IX (--json).
```

**Pista para `/speckit-plan`:** *"Extiende el modelo de `src/bookwright/core/manifest.py` (iteración 2) con un submodelo `FocusBlock` opcional, round-tripeado con tomlkit para preservar comentarios. Crea `src/bookwright/commands/focus.py` (un módulo por subcomando, Principio IV) con `show`/`set`/`clear`; errores subclase de `BookwrightError` (iteración 018); `--json` con el sobre estándar. `updated_at` con `datetime.date.today().isoformat()`. Tests: round-trip set→show, preservación de comentarios del manifest, ausencia del bloque, validación de fecha, casos negativos (target vacío)."*

**Criterio de aceptación:** `bookwright focus set --target "X"` seguido de `focus show --json` devuelve el foco con `updated_at` de hoy; los comentarios del `manifest.toml` se preservan; un proyecto sin `[focus]` responde "sin foco definido" sin error; `ruff`, `mypy --strict` y `pytest` verdes; cobertura > 85 % en el código nuevo.

---

### Iteración 020 — `bookwright status`: motor de estado derivado + `next_actions`

**Objetivo:** computar de forma determinista el estado del proyecto (qué falta) y
las acciones recomendadas (qué sigue) a partir del grafo, y exponerlo por CLI con
`--json`. Es el corazón del hito.

**Prompt:**

````
/speckit-specify

Necesidad: el autor (y cada skill) necesita saber, sin re-derivarlo a mano, en qué estado está el proyecto y qué conviene hacer a continuación. Toda esa información ya existe estructuralmente en el grafo y en los validators; falta un comando que la agregue de forma determinista y proponga el siguiente paso. Por ejemplo, las anclas sin fuentes suficientes SON la cola de investigación; hoy nadie la consume.

Comportamiento esperado:

- `bookwright status` computa el estado derivado del proyecto a partir del grafo (graph.ttl), reconstruyéndolo o refrescándolo si está obsoleto (reutilizando `bookwright graph build`, igual que validate). NO añade clases GOLEM: es exclusivamente agregación SPARQL sobre el esquema congelado.
- Reporta HECHOS derivados, entre ellos: la fase del proyecto (manifest.status) y un eco del foco (bloque [focus] de iteración 019); preguntas de investigación abiertas y anclas sin fuente suficiente; hallazgos por debajo de research.min_reliability_for_anchor; un resumen de validación (conteos por severidad, reutilizando el runner de validators y factual_anchor de iteraciones 11 y 15).
- Computa next_actions: una tabla de reglas ESTÁTICA mapea cada predicado de estado a una acción recomendada (skill a invocar + prompt listo para pegar + una razón breve / prioridad). Por ejemplo: "hay N anclas sin resolver" → recomendar bookwright-research con un prompt que las lista; "hay hallazgos de baja fiabilidad" → bookwright-verify; "hay violaciones de continuidad" → revisar la biblia; "no hay foco definido" → `bookwright focus set`. La tabla es determinista y unit-testeable: dado un estado, produce siempre las mismas acciones.
- Con --json emite un único documento JSON de éxito por stdout: { "status": "ok", "focus": {...}, "state": { ...hechos... }, "next_actions": [ { "skill": ..., "prompt": ..., "reason": ... } ] }. La prosa legible va a stderr (o a stdout en modo humano sin --json).
- Cachea el reporte computado en .bookwright/cache/status.json (gitignored), regenerándolo en cada ejecución. La caché es un artefacto derivado, nunca fuente de verdad.
- Es inerte y elegante cuando falta información: sin grafo construible o sin investigación, reporta lo que puede y deja next_actions vacío o con una única acción ("construye el grafo" / "define un foco"). Un proyecto v0.2 sin [focus] ni bible/research/ no falla.

Determinismo:

- Mismo corpus de entrada → mismos hechos y mismas next_actions, byte a byte. Sin juicio, sin LLM, sin red.

Fuera de scope:

- Que las skills consuman este comando (iteraciones 021–022).
- Cualquier juicio o priorización "inteligente" más allá de la tabla de reglas (eso vive en las skills, no en el CLI).
- Nuevas clases o propiedades en la ontología (Principio X).
- Mutar el grafo o el manuscrito.

Referencia: ver bookwright-design.md § 21 (orquestación: § 21.4 estado derivado, § 21.5 next_actions, § 21.6 contrato JSON), § 13 (validación) y § 20 (investigación / anclas: hallazgos `bw:open`, anclas `bw:promotes`/`bw:constrains`). Reutiliza el runner de validators (iteración 11) y factual_anchor (iteración 15). Principios I, IX, X.
````

**Pista para `/speckit-plan`:** *"Crea `src/bookwright/commands/status.py` (un módulo). Reutiliza `RdflibIndexer` y el runner de validación; NO dupliques SPARQL — añade las consultas de agregación junto a `validation/queries.py` o en un módulo `status/queries.py`. Modela `next_actions` como una función pura `state -> list[Action]` con una tabla de reglas estática, en su propio módulo, **unit-testeable sin grafo**. Define un helper para el sobre JSON de éxito (extendiendo el contrato `--json`); errores vía `BookwrightError`. Escribe la caché en `.bookwright/cache/status.json`. Tests: fixtures con estado conocido (N anclas sin resolver, una violación) → asevera hechos + next_actions exactos; fixture limpia → next_actions vacío/mínimo; test de la tabla de reglas aislada."*

**Criterio de aceptación:** sobre una fixture con anclas sin resolver y una violación de validación, `bookwright status --json` reporta ambos y sugiere `bookwright-research`/`bookwright-verify` con prompts concretos; sobre la fixture limpia, `next_actions` es vacío o mínimo; `.bookwright/cache/status.json` se escribe y está gitignored; salida determinista (misma entrada → `next_actions` idénticas); cobertura > 85 % en el código nuevo; gates verdes.

---

### Iteración 021 — `bookwright-research` consume anclas / preguntas abiertas

**Objetivo:** resolver el dolor concreto observado —que la skill de investigación
preguntara el tema en blanco— haciéndola tirar de la cola estructural (anclas sin
resolver, preguntas abiertas) que ya computa `status`, sin perder la entrada
top-down explícita.

**Prompt:**

```
/speckit-specify

Necesidad: cuando el autor invoca la skill de investigación sin un tema explícito, hoy esta pregunta "¿qué investigamos?" en blanco, aunque el proyecto ya contiene preguntas de investigación abiertas y anclas sin fuente suficiente. Esa cola es justamente lo que `bookwright status` (iteración 020) computa. La skill debe consumirla (entrada bottom-up) y ofrecerla como punto de partida, manteniendo la entrada top-down (tema explícito) cuando el autor sí lo da.

Comportamiento esperado:

- El command source bookwright-research se actualiza: si se invoca SIN tema explícito, primero ejecuta `bookwright status --json`, extrae las preguntas de investigación abiertas y las anclas sin fuente suficiente, y las presenta como cola de investigación para que el autor elija ("investiga estas N" o "un tema nuevo").
- Si se invoca CON un tema explícito, se comporta como hasta ahora (top-down), sin consultar status como paso obligatorio.
- Si `status` no devuelve elementos abiertos (proyecto sin investigación pendiente), la skill cae con elegancia al comportamiento actual (preguntar el tema). Nunca se rompe ni se bloquea.
- Los triggers en español e inglés se preservan.
- Se re-materializa como SKILL.md por el pipeline existente (iteración 9), en las integraciones claude y generic.

Fuera de scope:

- Cambiar el comando `bookwright status` (iteración 020, ya cerrado).
- Conectar el resto de skills con status (iteración 022).
- El motor de búsqueda: lo aporta el agente; la skill instruye, no implementa fetch.

Referencia: ver bookwright-design.md § 20.4 y § 20.7 (protocolo de investigación), el comando `bookwright status` (iteración 020) y § 11 (materialización a skills).
```

**Pista para `/speckit-plan`:** *"Edita solo `resources/commands/bookwright-research.md` (prosa/protocolo): añade un primer paso condicional que, sin tema, invoca `bookwright status --json` y parsea las preguntas abiertas/anclas; con tema, salta ese paso. Reutiliza la materialización a SKILL.md de la iteración 9 (no dupliques el pipeline). Mantén el trigger bilingüe y el cuerpo < 5000 tokens. Tests: el SKILL.md regenerado valida contra agentskills.io en ambas integraciones; un test de contrato que asevera que el cuerpo referencia `bookwright status`."*

**Criterio de aceptación:** `bookwright init` genera un `bookwright-research` válido en ambas integraciones; con anclas/preguntas abiertas presentes, la skill las presenta como cola en vez de preguntar en blanco; sin elementos abiertos, cae a preguntar el tema; trigger bilingüe; gates verdes.

---

### Iteración 022 — Skills leen `status` al iniciar + bloque "Próximos pasos"

**Objetivo:** cerrar el bucle en toda la suite de skills: cada una se orienta con
`status` al empezar y termina proponiendo el siguiente paso (`next_actions`), de
modo que el autor siempre tenga un hilo que seguir entre sesiones.

**Prompt:**

```
/speckit-specify

Necesidad: el hilo conductor solo funciona si las skills lo usan. Cada skill debería orientarse al empezar (foco actual + qué falta) consultando `bookwright status`, y terminar proponiendo el siguiente paso concreto, en vez de dejar al autor sin saber qué hacer después. Hoy las skills no consultan estado ni recomiendan continuación.

Comportamiento esperado:

- Cada command source de la suite (los 10 de v0.1 + bookwright-research y bookwright-verify de v0.2) gana: (al inicio) un paso para consultar `bookwright status --json` y orientarse con el foco y los elementos abiertos; (al final) una sección "Próximos pasos" que muestra las next_actions relevantes con sus prompts listos para pegar.
- Donde tenga sentido tras una transición de fase (p. ej. terminar la biblia), la skill actualiza el foco con `bookwright focus set` (iteración 019). Es opcional y solo donde aporte.
- La integración claude, con contexto dinámico, puede inyectar el estado vía !`bookwright status --json`; la generic lo instruye como paso explícito a ejecutar (respetando las convenciones de la iteración 9). 
- La re-materialización es idempotente y aplica a ambas integraciones. Los triggers bilingües se preservan.
- El sistema es inerte si status no aporta nada: las skills siguen funcionando igual que hoy en un proyecto sin foco ni investigación.

Fuera de scope:

- El fixture E2E, los tests de flujo, la documentación y el release (iteración 023).
- Cambiar la lógica de `status` o `focus`.

Referencia: ver bookwright-design.md § 11 (materialización, contexto dinámico), § 21 (orquestación), y los comandos `bookwright status` (020) y `bookwright focus` (019).
```

**Pista para `/speckit-plan`:** *"Aplica un patrón de edición compartido a `resources/commands/*.md`. Para no inflar cada cuerpo (límite ~5000 tokens) ni duplicar el boilerplate 'consulta status', considera un snippet/archivo de referencia común que el materializador inyecte, o una sección breve estandarizada. Reutiliza la materialización de la iteración 9; mantén el trigger bilingüe. Tests: cada SKILL.md regenerado sigue siendo válido contra agentskills.io y por debajo del límite de tokens; un smoke que comprueba la presencia de la sección 'Próximos pasos' y de la consulta a status."*

**Criterio de aceptación:** tras `bookwright init`, todas las skills materializan con la consulta a `status` y la sección "Próximos pasos", todas válidas y bajo el límite de tokens; un smoke manual muestra una skill terminando con un prompt de siguiente paso concreto; el sistema sigue funcionando con estado vacío; gates verdes.

---

### Iteración 023 — Fixture E2E del bucle, workflow test, docs y release v0.3.0

**Objetivo:** probar el bucle de orquestación de extremo a extremo, documentarlo
y liberar `v0.3.0`, cerrando el hito M5.

**Prompt:**

```
/speckit-specify

Necesidad: antes de release v0.3.0 necesitamos una fixture que ejercite el bucle de orquestación, tests E2E del flujo foco→status→siguiente paso, y documentación del nuevo sistema.

Comportamiento esperado:

Fixture:

- Una fixture (extendiendo una existente, p. ej. tiny-historical o tiny-novel) con un bloque [focus] relleno y preguntas de investigación abiertas / anclas sin fuente suficiente, de modo que `bookwright status` tenga algo concreto que reportar y recomendar.

Tests E2E:

- test_orchestration_workflow.py recorre: init → `bookwright focus set` → `bookwright graph build` → `bookwright status` (asevera hechos + next_actions deterministas) → resolver una pregunta abierta (simulada con contenido pre-horneado en la fixture) → `bookwright status` de nuevo (muestra el progreso: una acción menos). Los pasos de juicio (LLM) se simulan con contenido fijo de la fixture; las aserciones son sobre la salida determinista de status.
- Verificar que un proyecto SIN [focus] y SIN bible/research/ sigue funcionando igual (el sistema es inerte si no se usa).

Documentación:

- Página docs/orchestration.md (MkDocs): el modelo del hilo conductor (foco autoral vs estado derivado vs juicio), `bookwright status` y `next_actions`, el bucle de trabajo, y cómo las skills lo usan.
- Actualizar docs/commands con `bookwright status` y `bookwright focus`.
- CHANGELOG.md: entrada v0.3.0 con la orquestación de contexto.

Calidad final:

- pytest > 80% global (manteniendo el umbral), > 85% en el código nuevo del hito.
- ruff, mypy --strict, pre-commit, CI verdes. mkdocs build sin warnings.

Fuera de scope:

- Búsqueda vectorial (ahora v0.4) y export (v1.0).

Referencia: ver bookwright-design.md § 20 y § 21 (orquestación); las iteraciones 12 y 17 como precedente de fixture/E2E/docs/release.
```

**Pista para `/speckit-plan`:** *"La fixture es trabajo creativo pero corto y coherente; el estado abierto debe ser inequívoco para tests deterministas. Los tests E2E usan la fixture como input, igual que las iteraciones 12 y 17. Las aserciones recaen sobre la salida JSON determinista de `bookwright status` (hechos y next_actions), no sobre pasos LLM. Docs integradas en el sitio MkDocs material existente. Verifica explícitamente la inercia cuando no hay [focus] ni bible/research/."*

**Criterio de aceptación:** el flujo E2E de orquestación pasa; las aserciones sobre `status` son deterministas; `mkdocs build` limpio; `CHANGELOG` con entrada `v0.3.0`; release `v0.3.0` listo para publicar. Nota de roadmap: la búsqueda vectorial pasa a v0.4.

---

## 4. Notas operativas

### 4.1 Manejo de spec rechazadas

Si tras `/speckit-analyze` aparecen issues de consistencia entre spec/plan/tasks,
vuelve a `/speckit-clarify` o edita `spec.md` directamente, regenera plan y tasks,
y vuelve a analizar. No fuerces `/speckit-implement` con análisis con errores.

### 4.2 Iteraciones que se complican

Si una iteración crece más de lo previsto durante `/speckit-tasks` (más de ~10
tareas), divídela en dos specs. En este hito, la **020** (status: hechos +
tabla de reglas) y la **022** (re-cablear todas las skills) son las candidatas
más probables a split.

### 4.3 Cambios en el documento de diseño

El diseño es la fuente de verdad y la sección canónica de este hito ya existe
(`bookwright-design.md` § 21, en español). Si durante la implementación algo del
diseño no encaja con la realidad técnica, actualiza `bookwright-design.md`
**antes** de divergir el código, y registra el cambio en `CHANGELOG` bajo "Design
decisions revised during implementation".

### 4.4 Cuándo pedir ayuda al humano

Spec Kit genera bien spec/plan/tasks pero puede divagar en decisiones de diseño
no triviales. Cuando dudes, ejecuta `/speckit-clarify` o intervén manualmente.
Las decisiones de § 16 del doc de diseño son inmutables; si el agente las
cuestiona, redirígelo al doc.

### 4.5 Después de v0.3.0

Tras este hito, el roadmap que se mantiene es: **v0.4 — búsqueda vectorial**
(ChromaDB sobre rdflib, desacoplada, sin Grafeo), y **v1.0 — export** (EPUB/PDF/
print vía pandoc). Cuando llegue el momento, redactar un plan equivalente a éste,
también versionado, vaciando este de lo ya entregado. Quedan descartados (no se
implementarán): presets, GrafeoIndexer/Grafeo, multi-integración y extension
system; ver `bookwright-design.md` § 15.5.

Además hay **una iteración suelta pendiente** (no pertenece a M5, se ejecuta
tras mergear v0.3.0): indexar localizaciones (G13) — ver § 5.

---

## 5. Iteración suelta (post-v0.3, fuera de M5)

> Esta sección **no** forma parte del hito M5. Es una iteración de
> mantenimiento autocontenida, estilo 017/018, capturada el **2026-06-07** y
> ejecutable **una vez v0.3.0 esté mergeado**. No depende de 019–023 ni ellas
> de ella. Numerarla a continuación de los `specs/` existentes al arrancarla.

### Iteración suelta — Indexar localizaciones (`G13_Narrative_Location`)

**Origen:** en uso real, una investigación con `bears_on:`/`constrains:`
apuntando a una localización (p. ej. "Roncesvalles", "Alto del Perdón") no
resuelve y queda como *soft-miss* (`ResearchWarning`). Eso es comportamiento
esperado del indexador, **no** un bug — pero la causa de fondo es que
`bible/locations/*.md` **no se procesa en absoluto** en v0 (atajo, no decisión
de diseño). La clase `G13_Narrative_Location` está **ya reservada y modelada**:
existe en el cierre congelado `CLASS_IRI`, tiene modelo `NarrativeLocation` en
`golem/modules/setting.py` (con cross-ref `setting` vía `dlp:generic-location`)
y está registrada en `CONCEPTS`. Solo falta el *builder* que la alimente. Ver
`bookwright-design.md` § 7.2 (decisión).

**Objetivo:** cerrar el atajo de v0 cableando la clase G13 ya existente a un
*builder* de `bible/locations/`, sin tocar la ontología congelada (Principio X
a salvo) ni requerir enmienda constitucional.

**Prompt:**

```
/speckit-specify

Necesidad: hoy bible/locations/*.md no se procesa en absoluto (atajo de v0): el command bookwright-bible instruye escribir cada localización sin frontmatter ingerido y el mapper no tiene builder para locations/. La clase G13_Narrative_Location ya está reservada y modelada en el código (modelo NarrativeLocation en golem/modules/setting.py, en el cierre congelado CLASS_IRI, registrada en CONCEPTS, con cross-ref `setting` vía dlp:generic-location). Queremos que las localizaciones entren al grafo como entidades de primera clase, de modo que una investigación con bears_on:/constrains: a una localización resuelva en vez de quedar como soft-miss.

Comportamiento esperado:

- map_bible procesa bible/locations/*.md como directorio uno-entidad-por-fichero (espejo de settings/), construyendo entidades NarrativeLocation a partir de su frontmatter.
- El frontmatter de una localización admite `name` (cadena obligatoria) y `setting` (opcional, nombre de un setting hermano). Cuando `setting` está presente, se resuelve contra el índice de settings y emite el cross-ref dlp:generic-location (location → su setting); si no resuelve, es un soft-miss coherente con el contrato existente del mapper (no un crash).
- El command source bookwright-bible se actualiza: las localizaciones pasan a llevar frontmatter `name:` (+ `setting:` opcional) además de sus secciones sensoriales en prosa. Se re-materializa como SKILL.md por el pipeline existente, en claude y generic, con triggers bilingües preservados.
- Compatibilidad: una localización antigua sin frontmatter (estilo v0) se trata como fichero no ingerible (skip elegante, como hoy hace el mapper con frontmatter inservible), nunca un crash. Un proyecto sin bible/locations/ sigue funcionando igual.

Validaciones:

- name es cadena obligatoria; setting, si está, es cadena.
- Colisión de slug entre localizaciones se rechaza igual que en characters/settings.

Fuera de scope:

- Cualquier clase o propiedad nueva en la ontología (Principio X): G13 ya existe, no se añade nada.
- Cambiar el validador factual_anchor o el comportamiento de research más allá de que los enlaces a localizaciones ahora resuelvan.
- Atributos de localización más allá de identidad + setting (v0 de la clase es identity-only, igual que Setting).

Referencia: ver bookwright-design.md § 7.2 (decisión de ingesta G13), § 4.2 y § 4.5 (G13 como concepto y su URI), § 20 (research / soft-miss). Principio I (texto plano), Principio X (ontología congelada). Precedente de builder: el de settings/ en io/bible.py.
```

**Pista para `/speckit-plan`:** *"Añade una `DirectorySpec` para `locations/`
en `io/bible.py` espejando la de `settings/`, con un builder que construya
`NarrativeLocation` y resuelva el cross-ref `setting` contra el índice de
settings ya disponible en el mapper (mismo patrón que la resolución de nombres
existente). No toques `golem/` salvo lo estrictamente necesario: la clase, el
cross-ref y el registro en `CONCEPTS` ya existen. Edita
`resources/commands/bookwright-bible.md` para dar frontmatter a las
localizaciones y re-materializa vía el pipeline de la iteración 9. Actualiza
`bookwright-design.md` § 7.2 retirando el atajo. Tests: round-trip de una
localización con y sin `setting`, resolución del cross-ref, soft-miss cuando el
setting no existe, fichero sin frontmatter tratado como skip, colisión de
slug."*

**Criterio de aceptación:** una `bible/locations/<slug>.md` con `name:` (y
`setting:`) se materializa en el grafo como `G13_Narrative_Location` con su
triple `dlp:generic-location`; una investigación con `bears_on:` a esa
localización resuelve (sin `ResearchWarning`); una localización sin frontmatter
se omite sin crash; el cierre congelado de la ontología no cambia (test de
clausura verde); `ruff`, `mypy --strict` y `pytest` verdes; cobertura > 85 % en
el código nuevo.

---

**Fin del plan.**
