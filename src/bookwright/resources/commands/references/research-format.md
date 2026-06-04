# Formato de `bible/research/` — el contrato que el grafo lee

Esta es la referencia de formato para los archivos que escribe
`bookwright-research`. El lector (`bookwright graph build`) es **estricto**: una
violación marcada *fatal* aborta el build con un `ResearchError` y no produce
grafo. Escribe exactamente esta forma; no inventes claves ni valores nuevos.

Orden de proceso (determinista): `sources.md` → cada `<tema>.md` (orden
alfabético) → `_index.md`.

## Vocabularios controlados

- `type` ∈ `{primaria, secundaria, oficial, académica, periodística, testimonial}`
- `reliability` ∈ `{alta, media, baja}`

Un `type` o `reliability` fuera de vocabulario es **fatal** (el error nombra el
valor).

## `sources.md` — el registro de fuentes

Clave de frontmatter `sources:` → una lista de mappings. Por cada fuente:

| Clave | Obligatoria | Tipo | Notas |
|---|---|---|---|
| `name` | ✅ | str | único por *slug* en el archivo (un *slug* duplicado es **fatal**) |
| `reference` | ✅ | str | localizador de la cita (signatura, URL, tomo/folio) |
| `author` | ✅ | str | autor u organismo responsable |
| `original_language` | ✅ | str | código ISO 639-1 (`es`, `de`, `fr`, …) |
| `type` | ✅ | enum | ver vocabulario |
| `reliability` | ✅ | enum | ver vocabulario |
| `reliability_justification` | ✅ | str | no vacío: por qué esa fiabilidad |
| `access_date` | ✅ | fecha | ISO `YYYY-MM-DD` |
| `original_quote` | ✅ | str | cita literal en la lengua original |
| `translation` | condicional | str | **obligatoria si** `original_language` ≠ idioma del libro; **se omite** cuando coinciden |

- Falta una faceta obligatoria → **fatal** (el error nombra la faceta).
- Regla de traducción: una fuente en lengua distinta a la del libro **sin**
  `translation` es **fatal**. Si coinciden, no pongas `translation`.

Ejemplo (libro en `es`, fuente en `de`):

```yaml
---
sources:
  - name: "Kriegstagebuch des OKW, Bd. III"
    reference: "BA-MA RH 2/..., ff. 12-18"
    author: "Oberkommando der Wehrmacht"
    original_language: de
    type: primaria
    reliability: alta
    reliability_justification: "Registro oficial contemporáneo."
    access_date: 2026-06-04
    original_quote: "Die Nachschublage an der Ostfront ..."
    translation: "La situación de abastecimiento en el frente oriental ..."
---
```

## `<tema>.md` — hallazgos y anclas

Frontmatter con `findings:` y `anchors:` (ambas listas, opcionales). El nombre de
archivo es el *slug* del título del tema; conserva el título humano como
`# Encabezado` y como prosa legible en el cuerpo (el cuerpo no se indexa).

### `findings[]`

| Clave | Obligatoria | Tipo | Notas |
|---|---|---|---|
| `id` | ✅ | str | no vacío; único en el archivo; es el blanco de las anclas |
| `claim` | condicional | str | obligatoria salvo que `open: true` |
| `sources` | condicional | list[str] | ≥1 nombre de fuente que **resuelva** en `sources.md`, salvo `open: true` (no resolver es **fatal**) |
| `asserted_by` | ❌ | str | por defecto `"author"` |
| `bears_on` | ❌ | str | nombre de entidad narrativa; si no resuelve, **aviso suave** |
| `open` | ❌ | bool | por defecto `false` |

- Un hallazgo no abierto sin `claim` **o** sin ≥1 fuente que resuelva es **fatal**.
- Cuando las fuentes discrepen, escribe **dos hallazgos**, cada uno con su propia
  fuente; nunca los fundas en uno solo.

### `anchors[]`

| Clave | Obligatoria | Tipo | Notas |
|---|---|---|---|
| `promotes` | ✅ | str | un `id` de hallazgo **de este archivo** (desconocido = **fatal**) |
| `constrains` | ✅ | str | nombre de entidad narrativa, o el literal `"timeline"`; ausente = **fatal**; entidad que no resuelve = **aviso suave** |
| `begin` | ❌ | int | año (solo entero; otra cosa = **fatal**) |
| `end` | ❌ | int | año |
| `date` | ❌ | int | año; **mutuamente excluyente** con `begin`/`end` (combinarlos = **fatal**) |

Promueve a ancla **solo** si la mejor fuente del hallazgo alcanza el umbral
`[research].min_reliability_for_anchor` del manifiesto (`alta` > `media` > `baja`).

```yaml
---
findings:
  - id: f1
    claim: "El ferrocarril de vía estrecha limitaba el tonelaje diario."
    sources: ["Kriegstagebuch des OKW, Bd. III"]
    bears_on: "Wehrmacht"
  - id: q-ruta-suministro
    open: true
anchors:
  - promotes: f1
    constrains: "Wehrmacht"
    begin: 1943
    end: 1943
---
```

## `_index.md` — preguntas abiertas y mapa de temas

Frontmatter con `open_questions:` → una lista mapeada como **hallazgos abiertos**
(`id` obligatorio; `claim`/`sources` opcionales). El cuerpo en prosa (mapa de
temas, lista global de preguntas abiertas) es para humanos y **no se indexa**.

```yaml
---
open_questions:
  - id: q-calibre-via
    claim: "¿Qué ancho de vía tenía el ramal?"
---
# Índice de investigación
## Temas
- [Logística de la Wehrmacht en 1943](logistica-de-la-wehrmacht-en-1943.md)
```

## Suave vs. fatal — resumen

- **Fatal** (`ResearchError`, sin grafo): YAML mal formado; falta una faceta de
  fuente; vocabulario desconocido; nombre de fuente duplicado; hallazgo no abierto
  sin `claim`/fuente; nombre de fuente que no resuelve; ancla que promueve un
  hallazgo desconocido; falta `constrains`; año no entero; `date` junto a
  `begin`/`end`; incumplir la regla de traducción.
- **Suave** (`ResearchWarning`, el grafo se construye igual): un `bears_on` o
  `constrains` que no resuelve en la biblia (se omite la arista; la verificación
  de existencia es trabajo de un validador posterior).
- **Vacío/ausente** `bible/research/` → cero entidades, nunca falla.
