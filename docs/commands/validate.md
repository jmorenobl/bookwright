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
`violations[]`, `errors[]`, `not_evaluated[]` y un `summary` con el desglose
`by_severity` y la lista `ran` de validadores ejecutados. La prosa humana va a
stderr (Principio IX).

```json
{
  "status": "violations",
  "failed": true,
  "violations": [
    {"validator": "character_presence", "severity": "error",
     "message": "character 'Tobías' is defined in the bible but never mentioned in the manuscript",
     "source": "bible/characters/tobias.md", "triples": []}
  ],
  "errors": [],
  "not_evaluated": [
    {"validator": "focalization",
     "reason": "the narrative-voice declaration is still unanswered ([PENDING])",
     "kind": "missing_input"}
  ],
  "summary": {"ran": ["character_presence", "..."], "total": 1, "reported": 1,
              "by_severity": {"error": 1, "warning": 0, "info": 0}}
}
```

Los tres canales son **distintos** y no se solapan:

- **`violations[]`** — hallazgos de continuidad, cada uno con `validator`,
  `severity`, `message`, `source` (`archivo:línea`) y `triples`.
- **`errors[]`** — fallos del **propio validador** (excepciones), no del canon.
- **`not_evaluated[]`** — validadores que **no pudieron evaluar**, cada uno con su
  `validator`, un `reason` y un `kind` (`missing_input` o `pending_capability`).
  Aditivo; **no bloquea**. Una entrada `missing_input` (faltó una entrada tuya)
  significa que el verde no es completo; una `pending_capability` (límite permanente
  del enfoque) no lo deniega. El predicado de verde es, por tanto,
  `status == "ok" AND ninguna entrada de not_evaluated tiene kind == "missing_input"`.

Ver [Validación](../validation.md) para el catálogo de validadores y
[Interpretar la validación](../guides/interpret-validation.md) para leer la salida.
