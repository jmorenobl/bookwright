---
# Pre-baked resolution for the open question `q-libro-de-jornales` (iteration 023,
# FR-005 / research D3/D4). This file lives in a TOP-LEVEL `_resolution/` directory,
# OUTSIDE bible/ · manuscript/ · outline/, so the project loader never reads it: the
# first `bookwright status` over the committed fixture still sees TWO open questions.
#
# The E2E (`tests/e2e/test_orchestration_workflow.py`) copies this file into
# `bible/research/` on its tmp_path copy and drops `q-libro-de-jornales` from
# `_index.md` open_questions, then rebuilds — closing exactly that one question while
# leaving every other derived fact byte-identical (state convergence, research D2).
#
# Invariants this file MUST satisfy so convergence holds:
#   * ONE closed answering Finding (NOT a `q-…` id, NOT flagged open) → does not
#     re-enter open_questions.
#   * `bears_on` resolves to a real bible entity ("La Real Fábrica de Paños") → no
#     ResearchWarning, no unresolved-target noise.
#   * `sources` names only the already-registered `alta` source "Memoria de la Real
#     Fábrica de Paños" → adds no low-reliability finding.
#   * NO `anchors:` block → adds no AnchorGap, no factual_anchor change.
#   * Ships no derived graph, no materialized skill, no pending-sentinel → committed-tree
#     invariants hold.
findings:
  - id: libro-de-jornales-hallado
    claim: "El libro de jornales de la Real Fábrica se conserva en el Archivo Municipal y data la huelga en 1851."
    asserted_by: author
    bears_on: "La Real Fábrica de Paños"
    sources: ["Memoria de la Real Fábrica de Paños"]
---

# El libro de jornales, hallado

Respuesta a la pregunta abierta *¿Se conserva el libro de jornales de la fábrica que
permita datar la huelga?* (`q-libro-de-jornales`). El libro de jornales de la Real
Fábrica de Paños se conserva en el Archivo Municipal: sus asientos sitúan la huelga en
**1851**, en consonancia con la fundación de la fábrica. El hallazgo descansa sobre la
*Memoria de la Real Fábrica de Paños* (fiabilidad `alta`), de modo que cierra la
pregunta sin introducir ningún *anchor* nuevo ni rebajar la fiabilidad del corpus.
