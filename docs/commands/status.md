# `bookwright status`

Calcula el **estado derivado** del proyecto y las **próximas acciones**
deterministas (diseño § 21.4–21.6). Reconstruye el grafo desde el corpus en
cada ejecución — la recomputación *es* el mecanismo de frescura — refrescando
de paso la caché derivada `bible/graph.ttl`, agrega los hechos (fase, foco,
preguntas de investigación abiertas, anclas sin soporte suficiente, hallazgos
de baja fiabilidad y el resumen de validación) y los pasa por una tabla de
reglas estática y pura que produce `next_actions`: para cada recomendación, el
skill a invocar, un prompt listo para pegar y la razón que la dispara.

Sin LLM y sin red: el mismo corpus produce **bytes idénticos** en cada
ejecución. Los elementos del informe se identifican por claves estables del
corpus (ids autorados, rutas relativas, textos de claim) — nunca por URIs
acuñadas.

## Uso

```bash
bookwright status
bookwright status --json
```

```console
$ bookwright status
phase: drafting
focus: (none)
graph: 21 entities, 208 triples
open questions (2):
  - q-libro-de-jornales (bible/research/_index.md)
  - q-origen-telares (bible/research/_index.md)
...
next actions:
  1. [bookwright-research] 2 open research questions and 1 unresolved anchor
     prompt: Work through the research queue. ...
```

Con `--json`, exactamente un documento en stdout:

```json
{"status":"ok","focus":null,"state":{"phase":"drafting","graph":{"available":true,"entities":21,"triples":208},"open_questions":{"count":2,"items":[…]},"unresolved_anchors":{"count":1,"items":[…]},"low_reliability_findings":{"count":1,"items":[…]},"validation":{"counts":{"error":1,"warning":6,"info":0},"ran":[…]}},"next_actions":[…]}
```

Cada hecho con lista de elementos lleva siempre `count` **y** `items`;
`next_actions` puede ser `[]` — la respuesta válida de un proyecto sano y con
foco definido.

## Caché de estado

Toda ejecución con éxito (en ambos modos) regenera
`.bookwright/cache/status.json` con los **mismos bytes** que el documento
`--json` — una serialización, dos destinos. Es una salida de solo escritura:
nunca se vuelve a leer, y un fallo deja intacta la caché anterior.

## La tabla de reglas

En orden de prioridad fijo: ① grafo vacío/indisponible → arrancar la biblia
(`bookwright-bible`; suprime el resto); ② preguntas abiertas ∪ anclas sin
resolver → `bookwright-research`; ③ hallazgos de baja fiabilidad →
`bookwright-verify`; ④ errores de validación → `bookwright-continuity`
(con puntero a `bookwright validate`); ⑤ sin `[focus]` →
`bookwright focus set`.

## Degradación elegante

La información **ausente** nunca es un error: un proyecto v0.2 (sin `[focus]`,
sin `bible/research/`) sale con 0 y hechos de investigación vacíos; un proyecto
sin nada que indexar informa `graph.available: false` y, como mucho, la acción
de arranque. La información **corrupta** falla exactamente como `graph build`
sobre el mismo corpus.

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--json` | Emite el informe como un único documento JSON en stdout: `{"status":"ok","focus":…,"state":…,"next_actions":…}`. La prosa va a stderr. |

## Códigos de salida

| Código | Significado |
|--------|-------------|
| 0 | Informe calculado — por muy insano que esté el estado, incluidos los estados degradados por ausencia. |
| 2 | No es un proyecto (`no_project`), manifiesto inválido (`invalid_manifest`), motor desconocido (`unknown_indexer`) o corpus de investigación malformado (`invalid_research`). |
| 3 | Colisión de slugs en la biblia (`slug_collision`). |
| 4 | ≥ 1 fichero de la biblia omitido por front-matter inutilizable (`skipped_sources`, con `details` por fichero) — un informe de hechos sobre un corpus parcial sería mentira. |

Los fallos emiten el sobre de error unificado
(`{"status":"error","code":…,"message":…}`) bajo `--json`.
