# GOLEM — Eventos y línea de tiempo (`G5_Narrative_Event` vs. `G3_Psychological_State`)

Referencia de dominio para `bible/timeline.md`. La consultan `bookwright-bible`
(al poblar la cronología) y `bookwright-continuity` (al verificar la coherencia
temporal del manuscrito frente a la biblia).

## Evento vs. estado psicológico

GOLEM separa dos cosas que es fácil confundir:

- **`G5_Narrative_Event`** — un **hecho** discreto que ocurre en la historia y
  hace avanzar la trama: "la caída del puente de Ardía", "el pacto en la torre".
  Tiene participantes y ocupa un punto (o tramo) en la cronología. Es lo que se
  registra en `timeline.md`.
- **`G3_Psychological_State`** — el **estado interior** de un personaje en un
  momento dado: "Ana, paralizada por la culpa tras el pacto". No es un hecho del
  mundo, es una condición de la mente. **No** va en `timeline.md`: vive en la
  ficha del personaje (rasgos psicológicos), en los arcos del outline y en el
  manuscrito.

Regla práctica al poblar la cronología: si la frase responde a "¿qué **pasó**?",
es un evento → `timeline.md`. Si responde a "¿cómo **se sentía** alguien?", es un
estado → ficha/arco, no la cronología.

## Contrato del contenedor `timeline.md`

`bible/timeline.md` es un archivo **contenedor indexado**. Su frontmatter lleva
una única clave de nivel superior, `events:`, una lista de mapas en **orden
cronológico interno** de la historia:

```yaml
events:
  - name: "Caída del puente de Ardía"
    participants: ["ana-soler", "marco-vega"]
  - name: "Pacto en la torre"
    participants: ["ana-soler"]
```

- `name` — obligatorio, cadena no vacía; nombra el hecho.
- `participants` — opcional; lista de *slugs* de personaje. Cada slug debe
  corresponder a un `bible/characters/<slug>.md` real o aparecerá como referencia
  sin resolver.
- El **orden de la lista** refleja el orden cronológico interno (no
  necesariamente el orden de narración, que puede saltar).
- **Mantén `events:` como única clave de nivel superior** del frontmatter; otra
  clave dispara un aviso del indexador.
- El cuerpo en prosa ("notas de cronología") ancla el marco temporal global
  (época, duración, saltos); no se indexa.

## Cronología interna vs. orden de narración

`timeline.md` ordena los hechos según ocurren **dentro** del mundo de la obra.
El orden en que el lector los descubre (analepsis, estructura no lineal) se
decide en `outline/structure.md`. No fuerces el orden de narración sobre la
cronología: son dos ejes distintos y `bookwright-continuity` los compara por
separado.
