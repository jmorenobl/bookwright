# `bookwright graph query`

Carga `bible/graph.ttl` y ejecuta una consulta SPARQL. Solo lectura. El prefijo
`golem:` ya está vinculado.

## Uso

```bash
bookwright graph query "SELECT ?c WHERE { ?c a golem:G1_Character }"
bookwright graph query "SELECT (COUNT(?e) AS ?n) WHERE { ?e a golem:G5_Narrative_Event }" --json
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--json` | Emite los resultados como un único documento JSON en stdout: `{"status":"ok","results":[...],"count":N}`. |

## Códigos de salida

| Código | Significado |
|--------|-------------|
| 0 | Consulta correcta (incluso con cero resultados). |
| 2 | Proyecto/grafo ausente o motor desconocido. |
| 3 | SPARQL malformado (sin filas parciales). |

Construye el grafo primero con
[`bookwright graph build`](graph-build.md).
