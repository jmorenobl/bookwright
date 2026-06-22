---
# The orchestration oracle for `tiny-historical` (iteration 023, FR-004 / research D5).
#
# The single source of truth for what `bookwright status` reports over this fixture and
# how it converges when the pre-baked resolution closes one open question. The E2E
# (`tests/e2e/test_orchestration_workflow.py`) loads this front-matter ONCE and asserts
# against it — every identifier and count below is read from here, NEVER hard-coded in
# the test (FR-008, the `expected-findings.md` precedent).
#
# A SEPARATE file from `expected-findings.md` on purpose (research D5): that oracle stays
# byte-stable so the M4 research test provably binds an untouched fixture (FR-006).
#
# NOTE ON `validation.counts`: `status` aggregates ALL validators (character_presence,
# factual_anchor, focalization, setting_continuity, temporal), so its warning count
# (1) is the project-wide total. It now coincides with the factual_anchor-scoped
# {error:1, warning:1} that `expected-findings.md` pins for the M4 validator test, but
# they remain independent oracles; this file records what `status` actually emits.
# (Iteration 038 dropped this from 6 to 5: `character_presence` no longer mis-flags
# `Capítulo`, the first word of the manuscript's ATX heading `# Capítulo 1 — El telar
# nuevo`, as a proper noun. Iteration 041 dropped it from 5 to 4: `character_presence`
# no longer mis-flags the first spoken word `Esto` after the leading dialogue dash `—`,
# now stripped at the seam. Iteration 042 dropped it from 4 to 1: `character_presence`
# now cross-checks proper-noun candidates against the UNION of the character, setting,
# location and object rosters, so the three tokens `Real`/`Fábrica`/`Paños` of the
# declared setting "la Real Fábrica de Paños" stop being mis-flagged — only the lone
# `factual_anchor` warning remains. DEBT-010.)

# The authored focus the E2E (re)stamps via `bookwright focus set` at the loop's start.
focus:
  target: "Cerrar la investigación del libro de jornales para datar la huelga"

# A deterministic state fact: equals manifest [book].status, read from here (not hard-coded).
phase: drafting

# The pinned open-question set the first `status` reports (count == 2). Sorted (file, id).
open_questions:
  ids:
    - q-libro-de-jornales
    - q-origen-telares
  file: bible/research/_index.md

# The pre-baked two-part edit the E2E applies to close exactly ONE question (research D3):
# copy `answering_file` into bible/research/, drop `resolved_id` from `_index.md`. After
# rebuild, only `remaining_id` stays open (count == 1) — state convergence (D2).
resolution:
  resolved_id: q-libro-de-jornales
  answering_file: _resolution/q-libro-de-jornales.md
  remaining_id: q-origen-telares

# The permanent under-reliable anchor gap (the `el-almacen-viejo` setting), present and
# byte-identical in BOTH runs — it is why `research_queue` keeps firing after resolution.
unresolved_anchors:
  - promotes: rumor-incendio
    constrains: "El almacén viejo"
    file: bible/research/telar-y-fabrica.md
    problems:
      - under_reliable

# The permanent low-reliability finding (backed only by the `baja` source), present and
# byte-identical in both runs — it is why `verify_findings` keeps firing.
low_reliability_findings:
  - id: rumor-incendio
    best_reliability: baja
    file: bible/research/telar-y-fabrica.md

# The project-wide validation tally `status` reports (all validators), identical in both
# runs — the `error: 1` is why `review_continuity` keeps firing.
validation:
  counts:
    error: 1
    warning: 1
    info: 0

# The three firing rules, in priority order (research D2 / data-model § 3). `research_queue`
# fires while ANY open question OR anchor gap remains, so the LENGTH stays 3 across both
# runs (NOT N-1) — only its prompt/reason converge.
next_actions:
  skills:
    - bookwright-research
    - bookwright-verify
    - bookwright-continuity
---

# Estado esperado — `tiny-historical` (orquestación)

Este oráculo declara, de forma enumerable y co-localizada, lo que `bookwright status`
reporta sobre esta ficción y cómo **converge** cuando se cierra una de sus preguntas
abiertas. Es el ejemplo de trabajo del bucle de orquestación (M5 / iteración 023): un
`[focus]` autoral en `manifest.toml`, dos preguntas abiertas en `bible/research/_index.md`,
un *anchor* infrasostenido permanente y un hallazgo de fiabilidad baja permanente.

## El bucle, en dos fotogramas

1. **Primer `status`.** Dos preguntas abiertas (`q-libro-de-jornales`, `q-origen-telares`),
   un *anchor gap* (`rumor-incendio → El almacén viejo`), un hallazgo de baja fiabilidad
   (`rumor-incendio`) y la cuenta de validación `{error: 1, warning: 1, info: 0}`.
   `next_actions` enumera **tres** workstreams: `bookwright-research`, `bookwright-verify`,
   `bookwright-continuity`.

2. **Tras aplicar la resolución pre-cocinada** (`_resolution/q-libro-de-jornales.md` →
   `bible/research/`, y se elimina `q-libro-de-jornales` de `_index.md`) y reconstruir:
   queda **una** pregunta abierta (`q-origen-telares`). La acción `bookwright-research`
   deja de nombrar la pregunta cerrada y su `reason` baja a *«1 open research question»*;
   **todo lo demás es byte-idéntico** —`focus`, `phase`, `unresolved_anchors`,
   `low_reliability_findings`, `validation`, y las acciones `verify`/`continuity`— y
   `len(next_actions)` **sigue siendo 3** (agregación por workstream, no `N−1`).

`state.graph` (entidades/triples) se asevera *presente* en cada corrida pero se **excluye**
de la igualdad byte cross-run: cerrar un hallazgo emite triples distintos de forma
legítima (208 → 211), aunque la cuenta de entidades sea net-zero (−1 abierto, +1 cerrado).
