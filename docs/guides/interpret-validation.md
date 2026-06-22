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
  focalization: the narrative-voice declaration is still unanswered ([PENDING])
  setting_continuity: the manuscript is empty
```

Esto **no** es un error ni una advertencia, y **no** bloquea — pero tampoco es
verde. El validador no tenía con qué trabajar: no había manuscrito, o la
constitución no declaraba la voz narrativa, o la información que necesitaba aún era
un `[PENDING]`.

La distinción es la razón de ser de esta capa. Antes, un validador sin nada que
mirar devolvía «cero hallazgos», **indistinguible** de «miré y está todo bien». Eso
es *falsa confianza*: tu CI en verde mientras un validador llevaba meses dormido sin
que nadie lo notara. Ahora cada «no evaluado» **se declara, con su motivo**.

## La definición de VERDE

!!! success "Tu proyecto está realmente comprobado cuando…"
    ```text
    status == "ok"   Y   not_evaluated == []
    ```
    Es decir: cero errores **y** ningún validador dormido. Un proyecto con
    `not_evaluated` no vacío no está roto, pero tiene canon **sin vigilar** — y
    conviene despertar esos validadores.

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
