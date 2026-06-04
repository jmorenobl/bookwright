---
# The single source of truth for what this fixture's planted defects are. The E2E
# test (tests/e2e/test_research_workflow.py) loads this front-matter once and asserts
# against it — counts and anchor identifiers are NEVER hard-coded in the test.
#
# Identifiers are STABLE `constrains`-target slugs, not anchor/finding URIs: Finding
# and Anchor mint random uuid7 URIs, so the only deterministic handle on an anchor is
# the bible entity it constrains. The test resolves each finding's anchor → constrains
# target through the graph and matches it here.

# What the DETERMINISTIC validator (factual_anchor) must report on this fixture.
factual_anchor:
  expected_counts:                  # exact counts from `validate --json`, scoped to factual_anchor
    error: 1
    warning: 1
  # Defect #1 (R3 warning): the under-reliable anchor — backed only by the `baja`
  # "Hoja suelta sin firma" under the `media` floor. It constrains this setting.
  warning_anchor: el-almacen-viejo
  # Defect #2 (R5 error): the time-span-anachronistic anchor — span 1920-1925
  # constraining the 1851 dated event. It constrains this timeline event.
  error_anchor: la-inauguracion-de-la-fabrica

# What the MANUAL verify step (bookwright-verify LLM skill) should flag.
verify:
  manuscript_file: manuscript/01-el-telar-nuevo.md
  # Defect #3 (prose anachronism): the dated anchor the prose contradicts — the
  # founding anchor (date 1851) constraining this setting.
  contradicted_anchor: la-real-fabrica-de-panos
  prose_anachronism: >-
    Tomás Arnela atiende una llamada de teléfono en 1851, décadas antes de que el
    teléfono existiera; contradice el año 1851 fijado por el anchor de fundación.
---

# Hallazgos esperados — `tiny-historical`

Este proyecto es un ejemplo *deliberadamente imperfecto*: construye y se parsea sin
errores, pero contiene exactamente **tres** defectos plantados, en **dos** capas de
verificación. Esta es su declaración documentada (FR-012). No se versiona ningún
informe literal del modelo de lenguaje: rotaría y no puede comprobarse en CI; el test
automatizado comprueba las **precondiciones** del paso de verificación, no la salida
del modelo.

## Capa determinista — el validador `factual_anchor`

1. **Una advertencia (R3, infrasostenida).** El *anchor* que asciende el hallazgo
   `rumor-incendio` se apoya únicamente en la *Hoja suelta sin firma*, de fiabilidad
   `baja`, por debajo del mínimo `media` exigido en `manifest.toml`. Parsea sin
   problemas (el lector no veta la promoción), pero `factual_anchor` lo marca como
   advertencia. Constriñe el entorno **El almacén viejo**.

2. **Un error (R5, anacronismo).** El *anchor* que asciende `traslado-maquinaria`
   constriñe el evento datado **La inauguración de la fábrica** (1851) con un
   intervalo de `1920-1925`. Los rangos de años son disjuntos, así que `factual_anchor`
   lo marca como error y la validación falla (la puerta de error se dispara).

El resto de los *anchors* está limpio: bien sostenidos en fuentes `media`/`alta`,
con hallazgo y entidad presentes y, cuando son temporales, con intervalos
consistentes. Por eso `validate --json` reporta **exactamente** `{error: 1, warning: 1}`
para `factual_anchor`.

## Capa de juicio — la skill `bookwright-verify` (manual)

3. **Anacronismo en la prosa.** En `manuscript/01-el-telar-nuevo.md`, Tomás Arnela
   **atiende una llamada de teléfono en 1851**, décadas antes de que el teléfono se
   inventara. La prosa contradice el año `1851` que fija el *anchor* de fundación
   (`fundacion-fabrica`, que constriñe **La Real Fábrica de Paños**). Este defecto no
   lo detecta ningún validador determinista: lo señala la skill `bookwright-verify`
   leyendo el manuscrito contra los *anchors* del grafo. El test solo comprueba que
   ese paso *puede* ejecutarse (los *anchors* son consultables y la skill se
   materializa), no la respuesta del modelo.
