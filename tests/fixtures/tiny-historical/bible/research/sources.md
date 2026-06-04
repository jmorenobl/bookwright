---
# The Source registry for "El telar de Arnela". Every source carries all nine
# required facets; the two foreign-language sources (fr, de) additionally carry a
# `translation` because their `original_language` differs from the book's (es).
#
# Reliability is the spine of defect #1: "Hoja suelta sin firma" is the only `baja`
# source, reserved for the under-reliable anchor (factual_anchor R3). Every other
# source is `media` or `alta`, so every clean anchor rests on adequate support.
sources:
  - name: "Memoria de la Real Fábrica de Paños"
    reference: "Archivo Municipal de Arnela, leg. 12, ff. 3-9"
    author: "Junta de la Real Fábrica de Paños de Arnela"
    original_language: es
    type: oficial
    reliability: alta
    reliability_justification: "Memoria oficial contemporánea de la propia institución."
    access_date: 2026-05-30
    original_quote: "La Real Fábrica de Paños abrió sus puertas el año de 1851."

  - name: "Rapport sur l'industrie lainière"
    reference: "Bibliothèque municipale de Lyon, Fonds local, ms. 312"
    author: "Chambre de commerce de Lyon"
    original_language: fr
    type: secundaria
    reliability: alta
    reliability_justification: "Informe técnico de una cámara de comercio sobre la maquinaria lanera."
    access_date: 2026-05-31
    original_quote: "Les métiers mécaniques se répandirent au milieu du XIXe siècle."
    translation: "Los telares mecánicos se difundieron a mediados del siglo XIX."

  - name: "Bericht über die Wollweberei"
    reference: "Staatsarchiv, Bestand W 4/57, ff. 11-14"
    author: "Königliche Gewerbekammer"
    original_language: de
    type: primaria
    reliability: media
    reliability_justification: "Informe administrativo contemporáneo, aunque parcial en sus cifras."
    access_date: 2026-05-31
    original_quote: "Die mechanischen Webstühle kamen über die Pyrenäen nach Spanien."
    translation: "Los telares mecánicos llegaron a España a través de los Pirineos."

  - name: "Hoja suelta sin firma"
    reference: "Hemeroteca de Arnela, hoja suelta sin signatura"
    author: "Anónimo"
    original_language: es
    type: periodística
    reliability: baja
    reliability_justification: "Hoja anónima sin contraste documental; recoge un rumor de la villa."
    access_date: 2026-06-01
    original_quote: "Dicen que un incendio arrasó el almacén viejo antes de la fábrica."
---

# Registro de fuentes

Cuatro fuentes sostienen la investigación de *El telar de Arnela*: una memoria
oficial española, dos informes extranjeros (francés y alemán, cada uno con su
traducción) y una hoja suelta anónima de fiabilidad baja. La última se conserva en
el registro precisamente para mostrar cómo una afirmación mal sostenida no debe
ascender a *anchor* sin más respaldo.
