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
# character_unknown_mentions, factual_anchor, focalization, setting_continuity, temporal),
# so its warning count (1) is the project-wide total. It now coincides with the
# factual_anchor-scoped {error:1, warning:1} that `expected-findings.md` pins for the M4
# validator test, but they remain independent oracles; this file records what `status`
# actually emits.
# (Iteration 038 dropped this from 6 to 5: `character_presence` no longer mis-flags
# `Capítulo`, the first word of the manuscript's ATX heading `# Capítulo 1 — El telar
# nuevo`, as a proper noun. Iteration 041 dropped it from 5 to 4: `character_presence`
# no longer mis-flags the first spoken word `Esto` after the leading dialogue dash `—`,
# now stripped at the seam. Iteration 042 dropped it from 4 to 1: `character_presence`
# now cross-checks proper-noun candidates against the UNION of the character, setting,
# location and object rosters, so the three tokens `Real`/`Fábrica`/`Paños` of the
# declared setting "la Real Fábrica de Paños" stop being mis-flagged — only the lone
# `factual_anchor` warning remains. DEBT-010.)
#
# NOTE ON `validation.not_evaluated` (iteration 043, issue #1 track A): the open-set
# unknown-mention rule split out of `character_presence` into the new pure abstainer
# `character_unknown_mentions`, which raises `NotEvaluated` UNCONDITIONALLY. So the
# `not_evaluated` channel always carries it. `validation.counts` is UNCHANGED (the
# abstainer emits no finding; `character_presence` already emitted zero here post-042).
# (Iteration 044, the 043 repair: the entry now carries `kind: pending_capability` — a
# PERMANENT capability-gap that awaits move 3, not an actionable per-project input gap.
# The refined green predicate and the refined `activate_dormant_validators` rule consider
# only `missing_input` entries, so this capability-gap entry no longer fires the dormant
# nudge: `next_actions` went 4 → 3 (the second `bookwright-continuity` was gone;
# `review_continuity`, driven by the `error: 1` count, stays). `validation.counts` is
# byte-identical. DEBT — see § 13.5; this restores the reachable-green contract 043 broke.)
# (Iteration 051, move 3 first slice: a NEW rule `judge_undeclared_characters` — keyed on
# the abstaining SOURCE `character_unknown_mentions`, NOT on the `pending_capability` kind —
# now fires an INFORMATIVE second `bookwright-continuity` nudge pointing at the semantic-
# judgment skill that answers this gap. `next_actions` goes 3 → 4. It does NOT touch green
# (the entry stays `pending_capability`), and `validation.counts` / the `not_evaluated`
# entries stay byte-identical. `activate_dormant_validators` is untouched — still
# `missing_input`-only. DEBT-013 closed; § 20.6.2 first slice LANDED.)
# (Iteration 052, move 3 second slice: a SECOND peer rule `judge_head_hopping` — keyed on
# the abstaining SOURCE `focalization` AND `kind: pending_capability` — now fires a THIRD
# INFORMATIVE `bookwright-continuity` nudge pointing at the head-hopping judgment the skill
# performs over the `focalization` head-hopping abstention. `next_actions` goes 4 → 5. The
# name-only `_JUDGE_SOURCES` frozenset was generalized to a shared `_judges(validator)`
# predicate (validator + `pending_capability`), so `judge_undeclared_characters` stays
# byte-identical. Green, `validation.counts` and the `not_evaluated` entries are byte-
# identical. § 20.6.2 second slice LANDED; DEBT-021 (1st-person pro-drop) stays open.)

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
# runs — the `error: 1` is why `review_continuity` keeps firing. `counts` is unchanged by
# the 043 split (the abstainer emits no finding).
validation:
  counts:
    error: 1
    warning: 1
    info: 0
  # The always-dormant open-set abstainer (iteration 043). Present in BOTH runs. Its
  # `kind` is `pending_capability` (iteration 044): a permanent capability-gap, so it
  # stays VISIBLE here but does NOT fire `activate_dormant_validators` (which now nudges
  # only on `missing_input` gaps) and does NOT deny green for a clean project.
  not_evaluated:
    - validator: character_unknown_mentions
      reason: >-
        open-set proper-noun discovery requires semantic judgment (move 3); the
        deterministic heuristic was measured insufficient on real prose
      kind: pending_capability
    # The head-hopping capability-gap (iteration 045). `tiny-historical` declares
    # «Tercera persona limitada, centrada en Elena Vidal», so `focalization` abstains
    # from the WHOLE run rather than running the near-dormant head-hopping heuristic.
    # Its `kind` is `pending_capability` too: like the open-set abstainer it stays
    # VISIBLE here, does NOT fire `activate_dormant_validators`, and does NOT deny green.
    # Since iteration 052 (move 3 second slice) it DOES fire the peer `judge_head_hopping`
    # nudge — keyed on the SOURCE `focalization` AND `kind: pending_capability` — so
    # `next_actions` grows length 4 → 5 (the third `bookwright-continuity`).
    # `validation.counts` is byte-identical (head-hopping emitted nothing here today).
    # Sorted by validator name (after `character_unknown_mentions`). DEBT-014 (honesty
    # half) closed; DEBT-019 recorded.
    - validator: focalization
      reason: >-
        head-hopping / interiority attribution requires semantic judgment (move 3); the
        deterministic heuristic was measured nearly dormant on real prose
      kind: pending_capability

# The five firing rules, in priority order (research D2 / data-model § 3). `research_queue`
# fires while ANY open question OR anchor gap remains; `review_continuity` fires on the
# `error: 1` count. `activate_dormant_validators` does NOT fire (iteration 044): both
# `not_evaluated` entries are `pending_capability`, and that rule nudges only on
# `missing_input` gaps. BOTH move-3 judge rules fire, each keyed on its abstaining SOURCE +
# `pending_capability` (iteration 052 generalized the keying to `_judges(validator)`):
# `judge_undeclared_characters` (iteration 051, source `character_unknown_mentions`) adds a
# SECOND `bookwright-continuity` after `review_continuity`, and `judge_head_hopping`
# (iteration 052, source `focalization`) adds a THIRD — both informative pointers to the
# semantic-judgment skill. Neither degrades green (both entries are `pending_capability`, not
# `missing_input`); `validation.counts` and the `not_evaluated` entries stay byte-identical.
# The LENGTH stays 5 across both runs (NOT N-1) — only the research-queue prompt/reason
# converge.
next_actions:
  skills:
    - bookwright-research
    - bookwright-verify
    - bookwright-continuity
    - bookwright-continuity
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
   `next_actions` enumera **cinco** workstreams: `bookwright-research`, `bookwright-verify`,
   `bookwright-continuity` (los errores de continuidad), un **segundo**
   `bookwright-continuity` (el *nudge* de juicio de personajes sin declarar, move 3 primera
   rebanada) y un **tercer** `bookwright-continuity` (el *nudge* de juicio de head-hopping,
   move 3 segunda rebanada). El *nudge* de validadores dormidos ya **no** dispara: las
   entradas `not_evaluated` (`character_unknown_mentions`, `focalization`) son ambas
   `kind: pending_capability` (huecos de capacidad permanentes, no accionables para
   `activate_dormant_validators`, que —refinada en la iteración 044— solo dispara ante
   huecos `missing_input`). Pero las dos reglas de juicio de move 3 **sí** disparan, cada
   una anclada a su fuente abstinente más `pending_capability` (la iteración 052 generalizó
   la clave de la frozenset por-nombre a un predicado compartido `_judges(validator)`):
   `judge_undeclared_characters` (iteración 051, fuente `character_unknown_mentions`) y
   `judge_head_hopping` (iteración 052, fuente `focalization`). Son **informativos** —las
   entradas siguen `pending_capability`, así que no deniegan verde— y permanecen
   **visibles** en `not_evaluated` (issue #1 track C: move 3 contesta los huecos que la 044
   dejó visibles).

2. **Tras aplicar la resolución pre-cocinada** (`_resolution/q-libro-de-jornales.md` →
   `bible/research/`, y se elimina `q-libro-de-jornales` de `_index.md`) y reconstruir:
   queda **una** pregunta abierta (`q-origen-telares`). La acción `bookwright-research`
   deja de nombrar la pregunta cerrada y su `reason` baja a *«1 open research question»*;
   **todo lo demás es byte-idéntico** —`focus`, `phase`, `unresolved_anchors`,
   `low_reliability_findings`, `validation` (incluidas las entradas `not_evaluated` de los
   abstainers, con su `kind: pending_capability`), y las acciones `verify`/`continuity` (las
   tres)— y `len(next_actions)` **sigue siendo 5** (agregación por workstream, no `N−1`).

`state.graph` (entidades/triples) se asevera *presente* en cada corrida pero se **excluye**
de la igualdad byte cross-run: cerrar un hallazgo emite triples distintos de forma
legítima (208 → 211), aunque la cuenta de entidades sea net-zero (−1 abierto, +1 cerrado).
