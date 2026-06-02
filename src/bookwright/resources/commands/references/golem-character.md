# GOLEM — El personaje (`G1_Character`)

Referencia de dominio para escribir y leer las fichas de personaje
(`bible/characters/<slug>.md`). El indexador las ingiere como instancias de
`G1_Character` del modelo GOLEM. Consúltala desde `bookwright-bible` (al estampar
las fichas) y desde `bookwright-draft` (para mantener la voz constante).

## Lo platónico vs. lo narrativo

GOLEM distingue dos planos del personaje:

- **El personaje platónico** (`G0_Character-Stoff`): la identidad estable y
  reconocible que persiste a través de toda la obra y, en teoría, a través de
  distintas versiones de la historia. Es "quién es" con independencia de la
  escena: su nombre, su biografía, su voz.
- **El personaje narrativo** (manifestaciones en `G5_Narrative_Event` y estados
  `G3_Psychological_State`): cómo aparece y cambia en momentos concretos de la
  trama. Es "cómo está aquí y ahora".

La ficha de `bible/characters/` captura sobre todo el plano **platónico**
(identidad estable). La evolución por escena vive en el manuscrito, en
`timeline.md` (eventos) y en los arcos del outline. No metas en la ficha datos
que solo son ciertos en un capítulo concreto: márcalos donde correspondan.

## Contrato del frontmatter

El frontmatter de una ficha de personaje admite **únicamente** estas claves de
nivel superior; cualquier otra genera un aviso del indexador:

```yaml
name: "Ana Soler"          # cadena obligatoria
born: 1990                 # año entero, o se omite la línea
died: 2031                 # año entero, o se omite si sigue viva
features: ["zurda", "cicatriz en la ceja"]   # lista de cadenas
narrative_roles: ["protagonista", "heroína"] # lista de cadenas
```

- **`name`** — obligatoria, cadena no vacía. Si falta el dato, escribe el
  marcador **entre comillas**: `name: "[PENDING: ¿Cómo se llama?]"` (sin
  comillas, los corchetes se parsean como lista y la ficha se descarta — ver
  `references/pending-protocol.md`).
- **`born` / `died`** — año entero o **omitidas**. Nunca un texto ni un
  `[PENDING]`: un valor no entero hace que el indexador descarte el archivo. La
  edad se deriva de `born`/`died` o se cuenta en prosa, jamás como cadena en el
  frontmatter.
- **`features`** — rasgos distintivos estables (físicos o de carácter), lista de
  cadenas.
- **`narrative_roles`** — etiquetas de función narrativa (protagonista,
  antagonista, aliado, mentor…), lista de cadenas. Conectan con los vocabularios
  de Propp/Greimas si la constitución los activó.

## El slug

El *slug* de un personaje se deriva de su `name` (p. ej. `name: "Ana Soler"` →
`ana-soler`), **no** del nombre del archivo. Nombra cada
`bible/characters/<slug>.md` con ese mismo slug para que las referencias desde
`timeline.md` y `relationships.md` (que listan slugs en `participants`)
resuelvan correctamente.

## Secciones de cuerpo (de la plantilla)

La ficha estampada trae secciones en prosa que **no** se indexan pero anclan al
personaje: rasgos biográficos, rasgos psicológicos, rasgos físicos, rol
narrativo, un diálogo de muestra (clave para la voz) y patrones de lenguaje
corporal. Rellénalas con material del brief; marca `[PENDING: …]` lo que falte.
