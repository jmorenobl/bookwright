# Arquitectura

Esta página es un resumen curado. La especificación de diseño completa vive en
`bookwright-design.md`, en la raíz del repositorio; su numeración de secciones
es *load-bearing* y se cita aquí como `bookwright-design.md § N.M`. Esta página
**enlaza y resume**, no duplica.

## Capas

![Capas de bookwright en orden de dependencia: CLI (typer), commands/ con envelopes --json, una banda con validation/ · integrations/ · indexers/, golem/ sobre rdflib, core/ con el manifiesto, y errors.py como base sin dependencias](https://raw.githubusercontent.com/jmorenobl/bookwright/main/assets/layers.svg)

| Capa | Responsabilidad | Referencia de diseño |
|------|-----------------|----------------------|
| CLI (`typer`) | Superficie de comandos, envoltura JSON (Principio IX) | `bookwright-design.md § 11` |
| Manifiesto (`pydantic` + `tomlkit`) | Fuente de verdad del proyecto; *round-trip* con comentarios | `bookwright-design.md § 4` |
| GOLEM (`rdflib`) | Modelo de dominio narrativo serializado en Turtle | `bookwright-design.md § 5` |
| Indexer | Construcción y consulta SPARQL del grafo | `bookwright-design.md § 6` |
| Integraciones | Materialización de *Agent Skills* (`claude`, `generic`) | `bookwright-design.md § 9` |
| Validación | Chequeos de continuidad sobre el grafo | `bookwright-design.md § 13` |

## Principios no negociables

Recogidos en la constitución del proyecto
(`.specify/memory/constitution.md`) y resumidos en `bookwright-design.md § 16`
(decisiones axiomáticas que no se reabren):

- **Texto plano como fuente de verdad** (Principio I): el grafo `bible/graph.ttl`
  es una caché derivada, reconstruible; nunca la fuente.
- **Solo Agent Skills** (Principios VI/VII): cada comando se materializa como un
  `SKILL.md` conforme a [agentskills.io](https://agentskills.io); nunca se
  escribe en directorios `commands/` heredados.
- **Integraciones como plugins** (Principio V): el registro
  `INTEGRATION_REGISTRY` + `SkillsIntegration`, sin despachador monolítico.

## Flujo de datos

![Flujo de datos: bible/*.md y manuscript/*.md (texto plano) → map_bible → entidades GOLEM → indexer → graph.ttl (caché RDF derivada) → bookwright validate](https://raw.githubusercontent.com/jmorenobl/bookwright/main/assets/dataflow.svg)

Para el detalle de la ontología GOLEM y la procedencia CIDOC-CRM de cada
aserción derivada, consulta `bookwright-design.md § 5` y `§ 6`.
