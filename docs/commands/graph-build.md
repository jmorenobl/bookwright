# `bookwright graph build`

Lee la biblia, construye el grafo GOLEM con procedencia CIDOC-CRM y lo serializa
en `bible/graph.ttl`.

## Uso

```bash
bookwright graph build
bookwright graph build --json
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--force` | Reconstruye desde cero, ignorando cualquier caché (v0: *no-op*). |
| `--json` | Emite el informe de construcción como un único documento JSON en stdout. |

## Códigos de salida

| Código | Significado |
|--------|-------------|
| 0 | Construcción limpia. |
| 2 | Proyecto/manifiesto/directorio inválido o motor desconocido. |
| 3 | Colisión de *slug* (no se escribe grafo). |
| 4 | Al menos un archivo omitido (el grafo se escribe igualmente). |

El informe incluye `files_processed`, `entities`, `triples`, y las listas
`skipped`, `unknown_keys` y `unresolved_participants`.
