# Investigación

El sistema de **investigación con procedencia** (M4 / v0.2) deja que una novela
histórica —o cualquier obra que se apoye en hechos— documente *qué sabe, de dónde lo
sabe y con qué grado de confianza*, y que esa investigación **restrinja** la ficción
de forma verificable. Es **opcional**: un proyecto que no la usa no paga nada por ella
(ver [Inercia](#inercia-cuando-no-se-usa)).

Se enciende con un bloque en `manifest.toml`:

```toml
[research]
enabled = true
source_languages = ["fr", "de"]      # idiomas extranjeros de tus fuentes (ISO 639-1)
min_reliability_for_anchor = "media" # respaldo mínimo para promover un hallazgo a ancla
```

Toda la investigación vive en texto plano bajo `bible/research/`, igual que el resto
de la biblia: `sources.md` (el registro de fuentes), uno o más `<tema>.md` (hallazgos
y anclas) y `_index.md` (preguntas abiertas globales). El grafo derivado es, como
siempre, una caché reconstruible: la verdad está en el Markdown.

## El modelo: Source, Finding, Anchor

Tres conceptos, ninguno de los cuales añade una clase nueva a la ontología GOLEM
(reutilizan `crm:E55_Type` y `crm:E13_Attribute_Assignment`):

- **Source (fuente).** Una referencia del mundo real con **procedencia completa**:
  `name`, `reference`, `author`, `original_language`, `type` (vocabulario controlado:
  `primaria`, `secundaria`, `oficial`, `académica`, `periodística`, `testimonial`),
  `reliability` (`alta` / `media` / `baja`), `reliability_justification`,
  `access_date` y `original_quote`. Si la fuente está en otro idioma que el del libro,
  además lleva `translation`.
- **Finding (hallazgo).** Una afirmación (`claim`) sobre el mundo, sostenida por una o
  más fuentes (`sources`) y, opcionalmente, ligada a una entidad de la biblia
  (`bears_on`). Un **hallazgo abierto** (`open: true`) es una pregunta sin resolver:
  no necesita `claim` ni fuentes.
- **Anchor (ancla).** Un hallazgo **promovido a restricción vinculante**: `promotes` el
  hallazgo, `constrains` una entidad de la biblia (un personaje, un setting, un evento
  de la línea de tiempo, o la `timeline` entera) y, si procede, fija un lapso temporal
  (`date`, o `begin`/`end`). Un ancla es lo que convierte «esto es verdad» en «la
  ficción debe respetarlo».

```yaml
# bible/research/<tema>.md (front-matter)
findings:
  - id: fundacion-fabrica
    claim: "La Real Fábrica de Paños de Arnela abrió sus puertas en 1851."
    bears_on: "La Real Fábrica de Paños"
    sources: ["Memoria de la Real Fábrica de Paños"]
anchors:
  - promotes: fundacion-fabrica
    constrains: "La Real Fábrica de Paños"
    date: 1851
```

## La skill `bookwright-research`

El protocolo de autoría no se rellena a mano: invocas
[`/bookwright-research`](authoring.md) con un tema y la skill **investiga, destila y
documenta** los hallazgos con procedencia bajo `bible/research/`, marcando cuáles son
anclas. Dispara con prompts en español o inglés («investiga \<tema\>», «documenta
\<tema\> con fuentes» / «research \<topic\>», «find sources on \<topic\>»). No verifica
prosa ya escrita (eso es [`bookwright-verify`](authoring.md)) ni puebla fichas de
personajes (eso es [`bookwright-bible`](authoring.md)).

## Verificación en dos capas

Lo investigado se vigila por **dos mecanismos complementarios** que nunca se pisan: uno
lee el **grafo**, el otro lee la **prosa**.

1. **Capa determinista — el validador [`factual_anchor`](../validation.md).** Audita la
   *integridad estructural y cronológica* de las anclas en CI, sin leer una sola línea
   de manuscrito. Sus reglas: ancla sin fuente (R1), fuente con procedencia incompleta
   (R2), respaldo por debajo de `min_reliability_for_anchor` (R3), hallazgo o entidad
   ausente del grafo (R4) y **anacronismo** —el lapso del ancla es disjunto del
   intervalo del evento que restringe— (R5). R1–R4 son `warning`; R5 es `error` y
   bloquea. Es **inerte** si `[research].enabled = false` o no hay anclas.
2. **Capa de juicio — la skill `bookwright-verify`.** Lee el manuscrito **ya redactado**
   contra las anclas y señala lo que un grafo no puede ver: anacronismos en la prosa,
   errores de procedimiento (algo ilegal o imposible en la ambientación) e inexactitudes
   culturales o lingüísticas. Es de solo lectura, **post-draft**, y su juicio es del
   LLM: por eso es un **paso manual documentado**, no una puerta determinista de CI.

La división es deliberada: `factual_anchor` prueba que las anclas son *coherentes entre
sí y con la línea de tiempo*; `bookwright-verify` prueba que la *prosa respeta las
anclas*. Un anacronismo puede existir en una de las dos capas sin la otra.

## Multilingüismo y procedencia

La investigación histórica es multilingüe por naturaleza. Bookwright lo trata como un
invariante de procedencia, no como una nota al pie: una fuente cuyo `original_language`
difiere del idioma del libro **debe** llevar `translation`, y el lector estricto
**aborta la construcción** si falta (o si sobra cuando los idiomas coinciden). La cita
en lengua original (`original_quote`) se conserva siempre, de modo que la afirmación es
trazable hasta las palabras exactas de la fuente. Así, el grafo no solo dice «esto es
verdad», sino «esto lo dice tal fuente, en tal idioma, con esta fiabilidad, accedida en
tal fecha».

## El ejemplo trabajado: `tiny-historical`

El repositorio incluye un proyecto de ejemplo completo en
`tests/fixtures/tiny-historical/` — una novela mínima ambientada en 1851, *El telar de
Arnela*, con un corpus de `bible/research/` enteramente atribuido. Es deliberadamente
**imperfecto**: construye y se parsea sin errores, pero contiene exactamente **tres
defectos plantados** en las dos capas de verificación, declarados en su oráculo
co-localizado `tiny-historical/expected-findings.md`:

| # | Defecto | Capa | Resultado |
|---|---------|------|-----------|
| 1 | Un ancla apoyada solo en una fuente de fiabilidad `baja`, por debajo del mínimo `media`. | `factual_anchor` R3 | `warning` |
| 2 | Un ancla con lapso `1920-1925` que restringe el evento datado en `1851`. | `factual_anchor` R5 | `error` |
| 3 | En la prosa, un personaje **atiende una llamada de teléfono en 1851**, décadas antes de que el teléfono existiera. | `bookwright-verify` | `error` (manual) |

Por eso `bookwright validate` reporta sobre este proyecto **exactamente** un `warning` y
un `error` de `factual_anchor`, mientras que el tercer defecto solo lo señala el paso
manual de `bookwright-verify`. El oráculo es la declaración documentada de esos
hallazgos esperados; **no** se versiona ningún informe literal del modelo (rotaría y no
puede comprobarse en CI), solo las precondiciones del paso de verificación.

## Inercia cuando no se usa

Si un proyecto no tiene `bible/research/`, o si fija `[research].enabled = false`, el
sistema **no emite ningún triple `bw:`** y `factual_anchor` devuelve cero hallazgos: la
validación se comporta exactamente como en v0.1. La investigación es aditiva y
opcional, nunca un coste impuesto.
