# Preguntas frecuentes

## ¿Bookwright escribe mi libro por mí?

No. Bookwright estructura el proceso: tú destilas tus ideas en documentos
canónicos y el agente escribe a partir de *ellos*. El control narrativo es tuyo;
el toolkit garantiza trazabilidad y continuidad.

## ¿Dónde vive mi libro?

En texto plano dentro del proyecto: `bible/` (constitución, personajes, settings,
línea de tiempo), `outline/` (sinopsis, estructura, arcos, escenas) y
`manuscript/`. Todo *diffable* en git.

## ¿Tengo que usar Claude?

No. v0 entrega dos integraciones: `claude` (`.claude/skills/`) y `generic`
(`.agents/skills/`, para cualquier agente compatible con
[agentskills.io](https://agentskills.io)). Cambia entre ellas con
[`bookwright integration use`](commands/integration-use.md).

## ¿Debo versionar `bible/graph.ttl`?

No. Es una caché derivada, reconstruible con `bookwright graph build`. Bookwright
lo trata como efímero (Principio I). Añádelo a `.gitignore`.

## `validate` reporta *warnings* — ¿está mal mi libro?

No necesariamente. Los `warning` son heurísticos (menciones de nombres propios
sin ficha, posibles rupturas de voz) y **no bloquean**. Solo las violaciones de
severidad `error` (personajes huérfanos, contradicciones temporales) hacen fallar
la validación. Ver [Validación](validation.md).

## ¿Cómo consulto el grafo?

Con SPARQL: `bookwright graph query "<consulta>" --json`. El prefijo `golem:` ya
está vinculado. Ver
[`bookwright graph query`](commands/graph-query.md).

## ¿Cómo contribuyo al toolkit?

Lee `CONTRIBUTING.md` en la raíz del repositorio y la página
[Extender](extending.md).
