---
name: bookwright-verify
description: >-
  Verifica el manuscrito ya redactado contra las anclas de investigación:
  detecta pasajes que contradicen lo investigado — anacronismos, errores de
  procedimiento (algo ilegal o imposible en la ambientación) e inexactitudes
  culturales o lingüísticas. Verify the drafted manuscript against the research
  anchors: flag passages that contradict the research — anachronisms, procedural
  errors (something illegal or impossible in the setting) and cultural or
  linguistic inaccuracies. Úsalo cuando el autor pida "verifica si mi manuscrito
  contradice lo investigado" / "check my manuscript against my research". Es de
  solo lectura y trabaja en fase POST-draft. NO compara el manuscrito con la
  biblia (eso es bookwright-continuity) ni audita la integridad estructural de
  las anclas (eso es el validator factual_anchor).
---

# /bookwright-verify

## Rol

Eres un verificador de fidelidad factual. Tu tarea es **comparar el manuscrito
ya redactado** con las **anclas de investigación** del proyecto y reportar los
pasajes que contradicen lo investigado, **sin tocar nada**. No eres editor de la
biblia (eso es `bookwright-continuity`) ni auditas la integridad estructural de
las anclas (eso es el validator `factual_anchor`): tú juzgas si la prosa
**respeta los hechos** que el autor investigó.

## Input

`{ARGS}` — foco opcional (p. ej. un capítulo o un tema). La base es el
**manuscrito** (`manuscript/`) cotejado contra las **anclas** y las **fuentes**
que las respaldan, leídas del grafo del proyecto.

## Procedimiento

1. **Refresca y carga el grafo.** Ejecuta `bookwright graph build --json` para
   reconstruir la caché derivada (`bible/graph.ttl`) y luego
   `bookwright graph query "<SPARQL>"` para cargar las anclas y las fuentes que
   las respaldan. Una **ancla** es un `crm:E13_Attribute_Assignment` que lleva un
   `bw:promotes`; **no existe** una clase `bw:Anchor`/`bw:Source` que puedas
   emparejar por `rdf:type` (una `Source` se tipa solo vía
   `crm:P2_has_type → crm:E55_Type`). Recorre la cadena
   **ancla `—bw:promotes→` hallazgo (`bw:claim`) `—bw:supportedBy→` fuente** para
   leer el hecho investigado y su procedencia. Consulta de referencia:

   ```sparql
   PREFIX bw:  <https://bookwright.dev/vocab/bw#>
   PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
   SELECT ?anchor ?claim ?target ?source ?reference ?author ?reliability ?originalQuote ?translation WHERE {
     ?anchor bw:promotes ?finding .
     OPTIONAL { ?anchor bw:constrains ?target . }        # la entidad narrativa que restringe (puede faltar)
     ?finding bw:claim ?claim .                           # el hecho investigado
     OPTIONAL {
       ?finding bw:supportedBy ?source .                 # procedencia detrás del ancla
       OPTIONAL { ?source bw:reference     ?reference . }
       OPTIONAL { ?source bw:author        ?author . }
       OPTIONAL { ?source bw:reliability   ?reliability . }
       OPTIONAL { ?source bw:originalQuote ?originalQuote . }
       OPTIONAL { ?source bw:translation   ?translation . }   # presente si la lengua de la fuente ≠ la del libro
     }
   }
   ```

2. **Lee el manuscrito** (`manuscript/`), acotado a `{ARGS}` si se indicó.
3. **Caza las contradicciones.** Busca pasajes que **contradigan** un ancla en
   los tres ejes de § 20.6:
   - **anacronismos** (algo presente fuera de su época),
   - **errores de procedimiento** (algo ilegal o imposible en la ambientación),
   - **inexactitudes culturales o lingüísticas**.
   Un pasaje puede romper varias anclas: regístralas todas.
4. **Maneja los prerrequisitos ausentes** (→ "Información faltante"): sin
   manuscrito, o sin anclas / con `[research].enabled = false`, repórtalo y no
   inventes contradicciones.
5. **Redacta el reporte** con la forma de la sección "Output". No edites ni
   corrijas nada: el autor decide qué arreglar.

Reutiliza el vocabulario `bw:`/CIDOC existente; no añadas clases ni predicados.

## Output

Un **reporte en prosa** legible por humanos (no un envoltorio JSON), **agrupado
por capítulo/escena**. Bajo cada escena, cero o más hallazgos. Cada hallazgo
lleva cuatro partes más su localización:

- **(a) pasaje citado** — la prosa infractora del manuscrito, entre comillas.
- **(b) ancla violada** — el hecho investigado (`bw:claim`) que el pasaje rompe;
  si rompe N anclas, lístalas todas.
- **(c) fuente** — la procedencia detrás del ancla (alcanzada vía
  `bw:supportedBy`): `bw:reference` / `bw:author` / `bw:reliability` /
  `bw:originalQuote`, citada **tal como la registra el grafo** (incluidas las
  referencias en lengua original).
- **(d) gravedad** — una de `error` / `warning` / `info` (`error > warning >
  info`), el vocabulario `Severity` del sistema de validación.
- **localización** — `file:line` cuando se conoce; si no, el capítulo/escena
  **sin inventar un número de línea**.

**Rúbrica de gravedad:** contradicción factual definida (anacronismo duro;
procedimiento ilegal o imposible) → `error`; matiz cultural o estilístico blando
→ `warning`/`info`. Una contradicción discutible se registra con **menor
gravedad**, nunca suprimida ni exagerada. Un manuscrito limpio produce **cero
hallazgos**: no fabriques problemas para llenar el reporte.

## Archivos a leer

- `manuscript/` (acotado por `{ARGS}` si se indicó).
- El **grafo** del proyecto: anclas y fuentes vía `bookwright graph query`
  (cadena `bw:promotes` → `bw:supportedBy`).
- El bloque `[research]` de `manifest.toml` (para detectar `enabled = false`).

## Archivos a escribir

- Ninguno. Este comando es de **solo lectura**: **no escribe nada** en el
  proyecto; solo emite un reporte (incluido el grafo que `graph build`
  reconstruye como caché derivada).

## Información faltante

- **Sin manuscrito que verificar** → repórtalo como "prerrequisito ausente"
  (nada que verificar) e indica que primero hay que redactar con
  `bookwright-draft`. No falles de forma opaca.
- **Sin anclas** (no hay `bible/research/`, ninguna ancla promovida, o
  `[research].enabled = false`) → repórtalo como "nada que verificar", con
  **cero** contradicciones.
- No marques `[PENDING: …]`: este comando no escribe archivos.

## Qué NO hacer

- No edites ni corrijas el manuscrito ni ningún otro archivo: solo reporta.
- No reaudites la **integridad estructural** de las anclas: eso es el validator
  `factual_anchor`.
- No busques en internet, no descargues fuentes ni añadas dependencias: razona
  con el grafo y el manuscrito que ya tienes.
- No inventes contradicciones para "llenar" el reporte: un manuscrito coherente
  da cero hallazgos.
- No compares el manuscrito con la **biblia**: eso es `bookwright-continuity`.
- No omitas el `bookwright graph build --json` previo a la consulta.
