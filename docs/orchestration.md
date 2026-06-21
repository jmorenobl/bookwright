# Orquestación

El **hilo conductor** (M5 / v0.3, diseño § 21) es la respuesta de Bookwright a una
pregunta que toda obra larga acaba planteando: *¿en qué trabajo ahora y qué debería
hacer a continuación?* En vez de un TODO escrito a mano que envejece en silencio, el
hilo conductor se compone de tres capas que nunca se pisan —una **autorada**, una
**derivada** y una de **juicio**— de modo que el plan de trabajo es siempre
reconstruible desde el texto plano y verificable en CI.

Es **opcional y aditivo**: un proyecto que no define foco ni investigación se comporta
exactamente como en v0.2 (ver [Inercia](#inercia-cuando-no-se-usa)).

## Las tres capas

1. **Capa autorada — el bloque `[focus]` (§ 21.2).** Lo que *tú* declaras que estás
   trabajando ahora: un `target` corto, unas `notes` opcionales y un `updated_at` que
   la CLI sella sola. Vive en `manifest.toml`, en texto plano, y se gestiona con
   [`bookwright focus set`](commands/focus-set.md),
   [`focus show`](commands/focus-show.md) y [`focus clear`](commands/focus-clear.md).
   Es intención humana: ningún proceso la infiere ni la sobreescribe.

2. **Capa derivada — `bookwright status` (§ 21.4).** El **estado calculado** del
   proyecto, reconstruido desde el corpus en cada ejecución (la recomputación *es* el
   mecanismo de frescura). Agrega los hechos —fase, foco, preguntas de investigación
   abiertas, anclas sin soporte suficiente, hallazgos de baja fiabilidad y el resumen
   de validación— y de ellos deriva, mediante una tabla de reglas pura, las
   `next_actions`. Sin LLM y sin red: el mismo corpus produce **bytes idénticos**.

3. **Capa de juicio — las skills (§ 21.2).** El trabajo que un proceso determinista no
   puede hacer: investigar un tema, verificar la prosa contra las anclas, redactar.
   Lo hacen las Agent Skills (`bookwright-research`, `bookwright-verify`,
   `bookwright-continuity`, `bookwright-bible`), cada una invocada por la acción que
   `status` recomienda. Son las cuatro skills a las que enruta el bucle de orquestación;
   el catálogo completo de skills de autoría está en [Autoría](authoring.md). El juicio
   del modelo vive aquí, nunca en las capas autorada o derivada.

La separación es deliberada (diseño § 16, axioma): el plan no es un texto que se pudre,
sino una **función** del corpus. Borra `bible/graph.ttl`, vuelve a construir y obtienes
el mismo estado. Ese es el motivo por el que el TODO escrito a mano queda descartado.

## Qué reporta `status` y cómo derivan las acciones

[`bookwright status`](commands/status.md) emite, bajo `--json`, un único documento:

```json
{"status":"ok","focus":{…},"state":{"phase":"drafting","graph":{…},
 "open_questions":{…},"unresolved_anchors":{…},"low_reliability_findings":{…},
 "validation":{…}},"next_actions":[…]}
```

Cada `next_action` lleva el **skill** a invocar, un **prompt** listo para pegar y la
**razón** que la dispara. La lista sale de una tabla de reglas estática cuyo orden *es*
el orden de prioridad (§ 21.5). Las reglas recomiendan **por workstream, no por
elemento**: una sola acción `bookwright-research` agrupa *todas* las preguntas abiertas
*y* todas las anclas sin soporte.

| Orden | Regla | Dispara | Skill |
|-------|-------|---------|-------|
| ① | grafo vacío o indisponible | no hay nada que razonar todavía (suprime el resto) | `bookwright-bible` |
| ② | hay preguntas abiertas ∪ anclas sin resolver | cola de investigación pendiente | `bookwright-research` |
| ③ | hay hallazgos de baja fiabilidad | respaldo por debajo del umbral del proyecto | `bookwright-verify` |
| ④ | hay errores de validación | continuidad rota en biblia/manuscrito | `bookwright-continuity` |
| ⑤ | no hay bloque `[focus]` | falta declarar el hilo conductor | `bookwright focus set` |

Como ② agrupa por workstream, **cerrar una pregunta no acorta la lista**: mientras
quede *cualquier* pregunta abierta o *cualquier* ancla sin soporte, `bookwright-research`
sigue disparando. Lo que cambia es su `prompt` (deja de nombrar lo resuelto) y su
`reason` (refleja la cuenta nueva). El resto del informe permanece **byte a byte
idéntico** — eso es lo que el ejemplo de trabajo prueba como *convergencia de estado*.

## El bucle de trabajo

El hilo conductor se recorre en un ciclo corto:

1. **`focus`** — declara en qué trabajas (`bookwright focus set --target "…"`).
2. **`status`** — pregunta a Bookwright qué hacer a continuación (`bookwright status`).
3. **Actúa** — invoca el skill que recomienda la primera `next_action`, con su prompt.
4. **Repite** — cada acción edita el texto plano; el siguiente `status` recalcula el
   estado y propone el paso siguiente.

El proyecto de ejemplo `tests/fixtures/tiny-historical/` materializa este bucle: define
un `[focus]`, deja dos preguntas abiertas en `bible/research/_index.md` y trae una
resolución pre-cocinada en `_resolution/`. Su oráculo co-localizado
`expected-status.md` enumera, de forma exacta y verificable, lo que `status` reporta
antes y después de cerrar una pregunta. La prueba E2E
`tests/e2e/test_orchestration_workflow.py` recorre `focus → build → status → resolver →
build → status` y asevera la convergencia descrita arriba.

## Las skills consumen `status` al arrancar

Las skills de autoría **empiezan leyendo `status`**: antes de
investigar o redactar, una skill consulta el estado derivado para situarse en el foco
actual y en la cola de trabajo pendiente, en lugar de pedirte que se lo expliques. Así,
la capa de juicio se ancla en la capa derivada —y esta, en el texto plano— cerrando el
hilo conductor sin que ninguna capa invada a otra. El estado nunca se duplica a mano: se
lee de la única fuente que lo calcula.

## Inercia cuando no se usa

Un proyecto sin bloque `[focus]` y sin `bible/research/` se comporta como en v0.2:
`bookwright status` sale con código 0, reporta `focus: null`, hechos de investigación
vacíos y, a lo sumo, las acciones de arranque genéricas (① o ⑤); `build` y `validate`
no cambian. Y si faltan los prerrequisitos de construcción, `status` **degrada con
elegancia** —informa `graph.available: false`— en vez de fallar. La orquestación es una
capa que se enciende sola al usarla, nunca un coste impuesto.
