---
# Findings and anchors for the central topic: the founding of the factory and the
# arrival of the mechanical looms. Four findings, four anchors.
#
# Clean anchors (no factual_anchor finding):
#   * fundacion-fabrica  → constrains the setting "La Real Fábrica de Paños",
#     date 1851. THIS is the dated anchor the prose anachronism contradicts
#     (verify.contradicted_anchor = la-real-fabrica-de-panos). A setting target
#     carries no interval, so R5 never fires on it.
#   * telar-mecanico     → constrains the character "Elena Vidal", span 1845-1860.
#     A character target carries no interval, so R5 never fires either.
#
# Planted defects (exactly one factual_anchor finding each):
#   * DEFECT #2 (R5 error)   → "traslado-maquinaria" promoted by an anchor that
#     constrains the DATED event "La inauguración de la fábrica" (1851) with a span
#     of 1920-1925 — disjoint year ranges → anachronism error.
#   * DEFECT #1 (R3 warning) → "rumor-incendio" rests only on the `baja` "Hoja
#     suelta sin firma" (< the `media` floor); promoted to an anchor → under-reliable
#     warning. It constrains the setting "El almacén viejo" (present → no R4) and
#     carries no span (→ no R5), so R3 is the only rule it trips.
findings:
  - id: fundacion-fabrica
    claim: "La Real Fábrica de Paños de Arnela abrió sus puertas en 1851."
    asserted_by: author
    bears_on: "La Real Fábrica de Paños"
    sources: ["Memoria de la Real Fábrica de Paños"]

  - id: telar-mecanico
    claim: "Los telares mecánicos llegaron a Arnela a mediados del siglo XIX."
    asserted_by: author
    bears_on: "Elena Vidal"
    sources: ["Rapport sur l'industrie lainière", "Bericht über die Wollweberei"]

  - id: traslado-maquinaria
    claim: "La maquinaria pesada se instaló en la nave principal de la fábrica."
    asserted_by: author
    bears_on: "La Real Fábrica de Paños"
    sources: ["Memoria de la Real Fábrica de Paños"]

  - id: rumor-incendio
    claim: "Un incendio arrasó el almacén viejo antes de levantarse la fábrica."
    asserted_by: author
    bears_on: "El almacén viejo"
    sources: ["Hoja suelta sin firma"]

anchors:
  # Clean: dated 1851, constrains a setting (no interval → no R5), alta source.
  - promotes: fundacion-fabrica
    constrains: "La Real Fábrica de Paños"
    date: 1851

  # Clean: temporal anchor on a character (no interval → no R5), alta+media sources.
  - promotes: telar-mecanico
    constrains: "Elena Vidal"
    begin: 1845
    end: 1860

  # DEFECT #2 (R5 error): constrains the 1851 inauguration event with a 1920-1925
  # span — disjoint → anachronism. The promoted finding is alta-sourced, so R3 stays
  # silent and this anchor trips exactly one rule.
  - promotes: traslado-maquinaria
    constrains: "La inauguración de la fábrica"
    begin: 1920
    end: 1925

  # DEFECT #1 (R3 warning): backed only by the `baja` source, below the `media`
  # floor. Constrains a present setting and carries no span, so R3 is the only rule.
  - promotes: rumor-incendio
    constrains: "El almacén viejo"
---

# El telar y la fábrica

La fundación de la Real Fábrica de Paños (1851) y la llegada de los telares
mecánicos son los dos hechos que sostienen la novela, cada uno respaldado por sus
fuentes. Junto a ellos, este tema conserva a propósito dos defectos didácticos: un
*anchor* que sitúa la maquinaria en los años veinte (anacronismo respecto a la
inauguración de 1851) y un *anchor* que asciende un rumor sostenido solo por una
hoja anónima de fiabilidad baja.
