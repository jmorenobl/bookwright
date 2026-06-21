# Estructura narrativa

La **capa estructural narrativa** (v0.4, diseño § 7) es la respuesta de Bookwright
a la pregunta *¿qué forma tiene la trama, más allá de quién aparece y dónde?* Donde
la biblia modela personajes, settings y eventos, esta capa modela los **beats** de
la historia, las **funciones** que cumplen (en el sentido de Propp) y las
**secuencias** ordenadas que componen — todo desde texto plano en `outline/units/`,
sin tocar la ontología congelada de GOLEM.

Es **opcional y aditiva**: un proyecto sin `outline/units/` construye exactamente el
mismo grafo que antes de v0.4. Y los **vocabularios** (Propp, Greimas) solo tipan
cuando los activas: con `[vocabularies] active = []` el grafo es byte a byte el de
v0.3.

## De `outline/units/` al grafo

Cada archivo `outline/units/*.md` es una **tarjeta de unidad**: una ficha con
front-matter YAML que describe un beat de la trama. Al construir el grafo
(`bookwright graph build`), el ingestor recorre el directorio y, por cada tarjeta
bien formada, materializa:

| Entidad GOLEM | Clase | De dónde sale |
|---|---|---|
| `NarrativeUnit` (G9) | `golem:G9_Narrative_Unit` | una por tarjeta (su `name`). |
| `NarrativeFunction` (G10) | `golem:G10_Narrative_Function` | una por slug **distinto** en `functions:` (deduplicado entre tarjetas). |
| `NarrativeSequence` (G7) | `golem:G7_Narrative_Sequence` | una por `sequence:` distinto; sus miembros son las unidades, ordenadas por `order`. |

La unidad **refiere** (`crm:P67_refers_to`) a cada una de sus funciones y a cada rol
que resuelve; la secuencia enlaza a cada unidad miembro con `dlp:proper-part` en
orden ascendente de `order`. Toda aserción lleva su procedencia `file:line` por el
camino `crm:E13_Attribute_Assignment` de siempre — nada de esto añade una clase a la
ontología congelada (las 17 clases de `golem.ttl` no se tocan).

## El front-matter de una tarjeta de unidad

Las claves reconocidas son `name`, `functions`, `roles`, `sequence` y `order`;
cualquier otra clave es un aviso suave (`unknown_keys`), nunca un error.

```markdown
---
name: "Departure Beat"      # obligatorio — identidad de la unidad (G9)
functions: [departure]      # 0..N funciones (G10); se deduplican por slug
roles: [protagonist, helper]  # 0..N roles que resuelven contra los personajes
sequence: "Quest"           # opcional — la línea narrativa que la unidad integra
order: 2                    # opcional — su posición en esa línea (entero)
---

La partida: la heroína deja el valle acompañada de su ayudante.
```

- **`functions`** — cada nombre se convierte en una `NarrativeFunction`. Dos
  tarjetas que nombran la misma función comparten una sola entidad G10 (dedup por
  slug). Con un vocabulario activo (abajo), el nombre que coincide con un término
  canónico gana un tipado.
- **`roles`** — cada slug se **resuelve** contra los roles que los personajes
  declaran en su `narrative_roles:` (los nodos de rol del paso de la biblia). Un
  slug que ningún personaje juega no acuña nada: queda como una referencia sin
  resolver (la unidad se construye igual) que el validador puede reportar.
- **`sequence` / `order`** — **no** son atributos de la unidad; solo dirigen el
  ensamblado de la `NarrativeSequence`. Una tarjeta sin `sequence` no es miembro de
  ninguna secuencia (es un **beat huérfano**). Un `order` sin `sequence` que lo
  posicione es un aviso suave. Si dos miembros comparten `order`, el slug de la
  unidad desempata; los miembros sin `order` van al final. El orden resultante es
  total y determinista: el mismo corpus produce la misma secuencia byte a byte.

## Consultar la capa por nombre y por orden

Desde la iteración 035 la capa narrativa es **consultable por contenido y por
orden** desde el grafo, sin tocar la ontología congelada:

- **`rdfs:label` en unidades y funciones.** Cada `G9_Narrative_Unit` y cada
  `G10_Narrative_Function` emite **una** `rdfs:label` con su `name` autorado tal cual
  (acentos, mayúsculas y espacios incluidos) — el mismo patrón de una sola etiqueta
  que ya usan `CharacterRole` y los rasgos de personaje. La etiqueta viaja sobre la
  aserción de identidad de la entidad: no añade un `E13` propio. Así, buscar "el beat
  llamado X" deja de ser imposible.
- **`bw:sequenceOrdinal` en cada membresía.** La posición resuelta de cada unidad
  dentro de su `G7_Narrative_Sequence` se materializa como un triple por unidad
  `(?unit bw:sequenceOrdinal "n"^^xsd:integer)`, a un salto SPARQL de la secuencia
  (`?seq dlp:proper-part ?unit`). El ordinal es el **rango contiguo 1..k** del orden
  total que el ensamblado ya define (ascendente por `order`, los sin `order` al final,
  desempate por slug), de modo que es total y sin huecos aunque el `order:` autorado
  tenga huecos, falte o se duplique. RDF no es ordenado, pero ahora SPARQL tiene algo
  por lo que `ORDER BY`. A diferencia de la etiqueta, el ordinal **sí** se reifica con
  su propio `E13` a nivel de fichero (es una propiedad relacional de la membresía, no
  intrínseca a la unidad). `bw:sequenceOrdinal` se declara en
  `resources/vocabularies/sources.ttl`, fuera de `golem.ttl` y de su cierre, igual que
  la familia `bw:reference`.

Encontrar un beat por su nombre (US1):

```sparql
SELECT ?u WHERE {
  ?u a <https://w3id.org/golem/ontology#G9_Narrative_Unit> ;
     <http://www.w3.org/2000/01/rdf-schema#label> "Interdiction Beat" .
}
```

Listar una secuencia en el orden declarado (US2):

```sparql
SELECT ?u ?n WHERE {
  ?s a <https://w3id.org/golem/ontology#G7_Narrative_Sequence> .
  ?s <http://www.ontologydesignpatterns.org/ont/dlp/DOLCE-Lite.owl#proper-part> ?u .
  ?u <https://bookwright.dev/vocab/bw#sequenceOrdinal> ?n .
} ORDER BY ?n
```

## Activar Propp y Greimas

Los **vocabularios controlados** viven empaquetados como Turtle (`propp.ttl` con las
31 funciones de Propp, `greimas.ttl` con los 6 actantes), cada término un individuo
`crm:E55_Type` con etiquetas en español e inglés. Se activan por nombre en el
manifiesto:

```toml
[vocabularies]
active = ["propp", "greimas"]   # ambos; o ["propp"]; o [] para no tipar nada
```

- **Propp** tipa las **funciones narrativas** (G10): al ingerir `outline/units/`,
  cada `NarrativeFunction` cuyo nombre coincide (vía `make_slug`, tolerante a
  mayúsculas/acentos y a la grafía ES o EN) con una etiqueta de `propp.ttl` recibe
  una arista `crm:P2_has_type` hacia ese término. Una función sin coincidencia queda
  sin tipar, en silencio.
- **Greimas** tipa los **roles de personaje** (G11): al ingerir la biblia, cada rol
  de `narrative_roles:` que coincide con un actante de `greimas.ttl` (sujeto, objeto,
  destinador, destinatario, ayudante, oponente) recibe su `crm:P2_has_type`.

La activación es lo **único** que añade los tipados: con `active = []` ambos pasos no
tipan nada y el grafo es idéntico al de antes de la función (garantía de no-regresión
de la iteración 030). El enlace de tipado se reifica por el mismo camino de
procedencia `E13` que cualquier otra aserción; no hay clase ni propiedad nueva en la
ontología.

## El validador `narrative_structure`

`narrative_structure` (iteración 031) es el primer **consumidor** de esta capa: un
validador auto-descubierto, sin LLM y determinista, con severidad `warning` por
defecto (nunca bloquea el gate de CI). Tiene dos reglas:

- **Beat huérfano (regla a).** Una `G9_Narrative_Unit` que no es miembro de ninguna
  `G7_Narrative_Sequence`. Se responde con SPARQL `NOT EXISTS` sobre `dlp:proper-part`
  en el grafo derivado. Útil para detectar un beat que olvidaste enganchar a su línea
  (le falta `sequence`).
- **Rol sin resolver (regla c).** Un `roles:` de una tarjeta de unidad que nombra un
  slug que ningún personaje juega. Se re-emerge de los registros de referencia sin
  resolver que la ingesta de `outline/units/` ya produce, filtrados a las tarjetas de
  unidad. Útil para detectar un rol mal escrito o un personaje que falta en la biblia.

Ambos hallazgos citan su `file:line` por el camino `E13`. Como son `warning`,
`bookwright validate` termina con `failed: false` aunque los reporte: son una guía de
autoría, no un muro.

```toml
[validators]
enabled = []     # vacío = todos los integrados activos (narrative_structure incluido)
disabled = []    # añade "narrative_structure" aquí para silenciarlo
```

## Un ejemplo completo

El fixture `tests/fixtures/tiny-quest/` es el ejemplo trabajado de toda la capa:
Propp activo, seis beats (cinco en una secuencia `"Quest"` ordenada, uno huérfano a
propósito), un rol `dragon` que ningún personaje juega, y un oráculo
(`expected-narrative.md`) que enumera cada hecho. La prueba E2E
`tests/e2e/test_narrative_workflow.py` lo construye y valida de punta a punta.
