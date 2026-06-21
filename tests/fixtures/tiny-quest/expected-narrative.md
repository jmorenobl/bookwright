---
# Oracle for the `tiny-quest` fixture (iteration 032).
#
# This YAML front-matter is the SINGLE SOURCE OF TRUTH for every fact the E2E
# workflow test (tests/e2e/test_narrative_workflow.py) asserts — no count or
# identifier is hard-coded in the test. Every value below was taken from a real
# `graph build` + `validate` of the committed fixture (the contract's
# "Determinism" rule), not hand-guessed. The body (after the front-matter) is a
# Spanish explanation for a human reader; the test never reads it.
#
# Conventions: slug lists (`units.slugs`, each `roles_resolved` value) are SORTED
# — the test compares them as sets. `sequence.members` is ORDERED ascending by the
# cards' `order` key — the test compares it as an exact list.

# --- Build-time graph facts (asserted in workflow Group A) ---------------------
units:                         # G9 NarrativeUnit — one per unit card
  count: 6
  slugs:
    - departure-beat
    - interdiction-beat
    - omen-beat
    - return-beat
    - struggle-beat
    - villainy-beat

functions:                     # G10 NarrativeFunction — one per distinct function slug
  count: 6
  typed:                       # function slug -> matched Propp term (with Propp active)
    departure: departure
    interdiction: interdiction
    return: return
    struggle: struggle
    victory: victory
    villainy: villainy

sequence:                      # G7 NarrativeSequence — exactly one, the "Quest" line
  name: "Quest"
  members:                     # ordered ascending by `order` (1..5); omen-beat absent
    - interdiction-beat
    - departure-beat
    - villainy-beat
    - struggle-beat
    - return-beat

roles_resolved:                # unit slug -> resolved character-role slugs (sorted)
  interdiction-beat: [protagonist]
  departure-beat: [helper, protagonist]
  villainy-beat: [villain]
  struggle-beat: [protagonist, villain]
  return-beat: [protagonist]
  # omen-beat is absent: its only role (`dragon`) resolves to no character → no edge.

# --- Validate-time findings (asserted in workflow Group B) — EXACT set ---------
narrative_structure:
  orphan_beats:                # Rule a: G9 units in no G7 sequence
    - unit: omen-beat          # the unit slug, as it appears in the message
      source: "outline/units/06-omen.md:3"
  unresolved_roles:            # Rule c: roles: slug resolving to no character role
    - unit: "Omen Beat"        # the UnresolvedReference.entity (the unit's `name`)
      role: dragon
      source: "outline/units/06-omen.md:3"
  counts:                      # scoped to validator == "narrative_structure"
    warning: 2                 # 1 orphan beat + 1 unresolved role
    error: 0                   # the validator is warning-only (iteration 031)
---

# `tiny-quest` — la estructura esperada

Este oráculo describe, hecho por hecho, lo que produce construir y validar el
proyecto `tiny-quest`. La prueba E2E lo carga una sola vez y comprueba el grafo
derivado y los hallazgos del validador contra estos valores; ningún número vive
en el código de la prueba.

## Lo que construye el grafo (Grupo A)

Las seis tarjetas de `outline/units/` producen **seis** `G9_Narrative_Unit`. Sus
funciones nombradas se deduplican por slug en **seis** `G10_Narrative_Function`
distintas — `interdiction`, `departure`, `villainy`, `struggle`, `victory`,
`return` — y, como el manifiesto activa Propp (`[vocabularies] active =
["propp"]`), cada una se tipa contra su término `crm:E55_Type` homónimo mediante
`crm:P2_has_type`.

Las cinco tarjetas que declaran `sequence: "Quest"` se ensamblan en **una**
`G7_Narrative_Sequence` llamada `Quest`, con sus miembros ordenados por `order`
(1..5): `interdiction-beat`, `departure-beat`, `villainy-beat`, `struggle-beat`,
`return-beat`. Cada `roles:` que nombra un rol que un personaje juega
(`protagonist`, `villain`, `helper`) resuelve a una arista unidad→rol.

## Lo que reporta el validador (Grupo B)

`06-omen.md` es la única tarjeta sin `sequence`, así que `omen-beat` no es miembro
de ninguna secuencia: es el **beat huérfano** (regla a). Y cita el rol `dragon`,
que ningún personaje juega: es el **rol sin resolver** (regla c). Son exactamente
**dos** avisos (`warning`), cero errores — el validador no bloquea el gate, de
modo que `validate` termina con `failed: false`.

## La no-regresión sin vocabulario (Grupo C)

Si se vacía `[vocabularies] active` y se reconstruye, desaparecen todas las aristas
`crm:P2_has_type` (el mapa `functions.typed` queda ausente del grafo) mientras que
todo lo demás —unidades, conteo de funciones, secuencia y miembros, aristas de
rol— queda byte a byte idéntico. La activación del vocabulario es lo único que
añade los tipados (garantía de la iteración 030).
