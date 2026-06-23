# Interpretar la validación

`bookwright validate` es tu red de seguridad de continuidad. Esta guía explica
cómo leer su salida, qué significa cada resultado y cómo actuar sobre él. Si solo
quieres la lista de validadores y sus reglas, ve a la
[referencia de Validación](../validation.md).

## Lánzalo

```bash
bookwright validate          # informe legible en tu terminal
bookwright validate --json   # un único documento JSON en stdout (para agentes)
```

El **código de salida** es lo que mira CI: `0` cuando no hay errores, `1` cuando
hay al menos una violación de severidad `error`.

## Los tres resultados posibles

La trampa clásica es pensar que validar es binario —pasa o falla—. Bookwright
distingue **tres** estados, y confundirlos es justo el bug que esta capa previene.

### 1. Evaluado y limpio → verde de verdad

```text
no violations found
```

El validador miró y no encontró nada. Es el resultado que quieres.

### 2. Evaluado con hallazgos → hay algo que mirar

```text
character_presence:
  error: character 'Tobías' is defined in the bible but never mentioned in the
  manuscript — bible/characters/tobias.md
```

Cada hallazgo trae **validador**, **severidad**, **mensaje** y un **localizador**
`archivo:línea`. Dos severidades importan:

- **`error`** — una contradicción dura del canon. **Bloquea** (código de salida 1).
- **`warning`** — una heurística que merece tu atención pero no es seguro que sea
  un fallo (un nombre propio sin ficha, un posible salto de voz). **Nunca bloquea**.

!!! tip "Un warning no es un error tímido"
    Los `warning` son intencionadamente conservadores: prefieren avisarte de algo
    inocuo a callarse algo real. Revísalos, pero no dejes que detengan tu trabajo.
    Si uno te molesta de forma sistemática, puedes
    [desactivar ese validador](../validation.md#activar-y-desactivar-validadores).

### 3. No evaluado → no se pudo mirar

```text
not evaluated:
  character_unknown_mentions [known limitation — no action available yet]: open-set proper-noun discovery requires semantic judgment (move 3); the deterministic heuristic was measured insufficient on real prose
  focalization [input gap]: the narrative-voice declaration is still unanswered ([PENDING])
  setting_continuity [input gap]: the manuscript is empty
```

Esto **no** es un error ni una advertencia, y **no** bloquea. Cada «no evaluado»
lleva una **etiqueta de tipo** entre corchetes, y la distinción importa:

- **`[input gap]`** — el validador no tenía con qué trabajar *en tu proyecto*: no
  había manuscrito, o la constitución no declaraba la voz narrativa, o lo que
  necesitaba aún era un `[PENDING]`. Es **accionable y transitorio**: aporta la
  entrada que falta y el validador despierta. **No es verde** hasta que lo hagas.
- **`[known limitation — no action available yet]`** — un **hueco de capacidad
  permanente**: ningún chequeo determinista puede evaluar eso de forma fiable (hoy,
  `character_unknown_mentions`, el descubrimiento de nombres propios de conjunto
  abierto, que espera el juicio semántico del *move 3*). No hay nada que puedas
  hacer; aparece en *todo* proyecto. Por eso **no impide el verde** ni te pide
  acción — solo se declara, honesto, en lugar de fingir que miró.

La distinción es la razón de ser de esta capa. Antes, un validador sin nada que
mirar devolvía «cero hallazgos», **indistinguible** de «miré y está todo bien». Eso
es *falsa confianza*: tu CI en verde mientras un validador llevaba meses dormido sin
que nadie lo notara. Ahora cada «no evaluado» **se declara, con su motivo y su tipo**.

## La definición de VERDE

!!! success "Tu proyecto está realmente comprobado cuando…"
    ```text
    status == "ok"   Y   ninguna entrada de not_evaluated es de tipo "missing_input"
    ```
    Es decir: cero errores **y** ningún validador dormido *por falta de una entrada
    tuya*. Una entrada `[input gap]` (`missing_input`) sí deniega el verde: tienes
    canon **sin vigilar** y conviene despertar ese validador. Una entrada
    `[known limitation]` (`pending_capability`) **no** deniega el verde — es un límite
    conocido del enfoque, no algo que tú puedas arreglar, así que un proyecto impecable
    se lee verde aunque la lleve siempre.

`bookwright status` reporta lo mismo bajo `state.validation.not_evaluated`, y su
capa de orquestación incluso te propone el remedio como una `next_action` (ver
[Orquestación](../concepts/orchestration.md)).

## Cómo despertar un validador dormido

Cada motivo de «no evaluado» tiene un remedio concreto:

| Validador | Motivo típico | Remedio |
|-----------|---------------|---------|
| `focalization` | La voz narrativa sigue como `[PENDING]` en la constitución | Declárala: `- **Voz narrativa**: Tercera persona limitada…` |
| `focalization` | No hay constitución, o no se pudo parsear una persona gramatical | Crea/corrige `bible/constitution.md` con una voz clara |
| `setting_continuity` | El manuscrito está vacío | Escribe prosa en `manuscript/` |
| `character_presence` | No hay manuscrito **y** la biblia no tiene personajes | Puebla la biblia y/o empieza a redactar |

Tras el remedio, reconstruye y vuelve a validar:

```bash
bookwright graph build && bookwright validate
```

## El flujo de corrección, de principio a fin

El [tutorial](../tutorial/revise.md) lo recorre con un ejemplo real, pero el
patrón es siempre el mismo:

1. **Edita el grafo en su origen** — un hallazgo apunta a un `archivo:línea`. La
   corrección va ahí, en el **texto plano**, nunca en `bible/graph.ttl` (es una
   caché derivada).
2. **`bookwright graph build`** — reconstruye el grafo con tu corrección.
3. **`bookwright validate`** — confirma que el hallazgo desapareció.

Para arreglos guiados por un agente, la skill
[`/bookwright-continuity`](../concepts/authoring.md) lee el informe y corrige cada
error en su fuente.
