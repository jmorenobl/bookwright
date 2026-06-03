# Validación

`bookwright validate` corre los validadores activos contra el grafo derivado de
tu biblia y tu manuscrito. La **puerta de CI** (código de salida 1) se calcula
solo sobre las violaciones de severidad `error`: los `warning` heurísticos son
informativos y nunca bloquean.

## Validadores integrados

| Validador | Severidad | Qué detecta |
|-----------|-----------|-------------|
| `character_presence` | `error` (huérfanos) / `warning` (menciones desconocidas) | Un personaje de la biblia que nunca se menciona en el manuscrito (`error`); un nombre propio del manuscrito sin ficha (`warning`). |
| `focalization` | `warning` | Rupturas de la voz narrativa declarada en la constitución (primera persona fuera de diálogo bajo tercera persona; *head-hopping* en tercera limitada). |
| `setting_continuity` | `warning` | Un mismo setting descrito con términos contradictorios (p. ej. «costera» e «interior») en archivos distintos. |
| `temporal` | `error` | Contradicciones en la línea de tiempo: ciclos `follows`/`precedes`, solapamientos imposibles, contención incompatible con un orden estricto, o intervalos numéricos que contradicen una relación declarada. |

Solo `character_presence` (huérfanos) y `temporal` producen `error` y, por
tanto, bloquean. `focalization` y `setting_continuity` son siempre `warning`.

## Activar y desactivar validadores

En `manifest.toml`:

```toml
[validators]
enabled = []          # vacío = todos los integrados activos
disabled = []         # nombres a desactivar
custom = []           # nombres de validadores personalizados
```

## Añadir un validador personalizado

1. Crea un módulo bajo `.bookwright/validators/` que exponga una clase con:
   - `name: str` (identificador único),
   - `severity_default: Severity`,
   - `validate(self, project: ValidationContext, indexer: Indexer) -> list[Violation]`.
2. El método debe ser **determinista** y **no escribir en disco** (Principio de
   validación): examina `project` (constitución, rosters, manuscrito) y el
   `indexer` (grafo ya construido) y devuelve una lista de `Violation`.
3. Declara su `name` en `[validators] custom` del manifiesto.

Consulta [Extender](extending.md) para un ejemplo completo.
