# Validación

`bookwright validate` corre los validadores activos contra el grafo derivado de
tu biblia y tu manuscrito. La **puerta de CI** (código de salida 1) se calcula
solo sobre las violaciones de severidad `error`: los `warning` heurísticos son
informativos y nunca bloquean.

Esta página es la **referencia**: qué validador comprueba qué, y cómo se
configuran. Para aprender a *leer e interpretar* la salida —las tres respuestas
posibles, la definición de verde, cómo despertar un validador dormido— ve a la
guía [Interpretar la validación](guides/interpret-validation.md).

## Validadores integrados

Son **seis**, todos deterministas (sin LLM, sin red), descubiertos
automáticamente:

| Validador | Severidad | Qué detecta |
|-----------|-----------|-------------|
| `character_presence` | `error` (huérfanos) / `warning` (menciones desconocidas) | Un personaje de la biblia que nunca se menciona en el manuscrito (`error`); un nombre propio del manuscrito sin ficha (`warning`). |
| `focalization` | `warning` | Rupturas de la voz narrativa declarada en la constitución (primera persona fuera de diálogo bajo tercera persona; *head-hopping* en tercera limitada). |
| `setting_continuity` | `warning` | Un mismo setting descrito con términos contradictorios (p. ej. «costera» e «interior») en archivos distintos. |
| `temporal` | `error` | Contradicciones en la línea de tiempo: ciclos `follows`/`precedes`, solapamientos imposibles, contención incompatible con un orden estricto, o intervalos numéricos que contradicen una relación declarada. |
| `factual_anchor` | `warning` (defectos estructurales) / `error` (anacronismo) | Integridad de los anclajes de investigación: un anclaje sin fuente, una fuente a la que le falta una faceta de procedencia obligatoria, una fiabilidad de respaldo por debajo de `[research] min_reliability_for_anchor`, o un hallazgo/entidad ausente del grafo (`warning`); y un choque cronológico entre el lapso temporal del anclaje y el intervalo del evento (o la línea de tiempo) que restringe (`error`). Es inerte cuando `[research].enabled = false` o no hay anclajes. |
| `narrative_structure` | `warning` | Continuidad de la [capa narrativa](concepts/narrative-structure.md): una unidad `G9` que no pertenece a ninguna secuencia `G7` (beat huérfano) y un rol citado por una unidad que no resuelve a ningún personaje de la biblia (rol sin resolver). |

Solo `character_presence` (huérfanos), `temporal` y el anacronismo de
`factual_anchor` producen `error` y, por tanto, bloquean. `focalization`,
`setting_continuity`, `narrative_structure` y los defectos estructurales de
`factual_anchor` son siempre `warning`.

## Tres resultados: evaluado, con hallazgos, no evaluado

Cada validador devuelve, por corrida, un veredicto de **tres valores**, no dos:

- **evaluado, sin hallazgos** — miró y está limpio.
- **evaluado, con hallazgos** — miró y reportó `warning`/`error`.
- **no evaluado** — *no pudo* mirar, y lo declara con un motivo (manuscrito vacío,
  voz narrativa sin declarar, sin constitución…).

Los «no evaluados» viajan en su propio canal `not_evaluated[]`, **distinto** de
`errors[]` (un fallo del validador) y de las violaciones. **No bloquean**, pero
tampoco cuentan como verde: un resultado vacío ya no se confunde con un visto
bueno. La definición canónica de verde es, por tanto,
`status == "ok" AND not_evaluated == []`. Lo trata a fondo la guía
[Interpretar la validación](guides/interpret-validation.md); su forma exacta en
JSON está en la referencia de [`bookwright validate`](commands/validate.md).

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
