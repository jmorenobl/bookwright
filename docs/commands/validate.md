# `bookwright validate`

Corre los validadores activos y reporta las violaciones de continuidad. Sale con
código 1 si hay alguna violación de severidad `error`; los `warning` no bloquean.

## Uso

```bash
bookwright validate
bookwright validate --json
bookwright validate --scope manuscript/ --severity warning
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--scope` | Limita las violaciones reportadas a este archivo o directorio. La puerta (exit 1) se calcula igualmente sobre **todo** el conjunto de errores. |
| `--severity` | Reporta este nivel y superiores (`error` > `warning` > `info`). |
| `--json` | Emite un único documento JSON en stdout y nada más. |

## Salida

Bajo `--json`, el cuerpo es un único documento con `status`, `failed`,
`violations[]`, `errors[]` y un `summary` con el desglose `by_severity`. La prosa
humana va a stderr (Principio IX). Ver [Validación](../validation.md) para el
catálogo de validadores.
