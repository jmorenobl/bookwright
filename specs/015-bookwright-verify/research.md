# Phase 0 — Research: `bookwright-verify` Skill

The spec's two open questions were closed in its Clarifications session
(2026-06-04): the report uses the validation system's three-level
`error`/`warning`/`info` `Severity` vocabulary, and the skill **builds then
queries** the graph. This document records the design decisions (D1..D8) that turn
the requirements into an authored command source plus a coherent, gate-passing
roster edit.

## D1 — No new Python logic; the iteration-9 pipeline carries the whole feature

**Decision**: Add `bookwright-verify` as a packaged command-source `.md` only. Do
not write a verifier module, a new CLI verb, or any integration code.

**Rationale**: `integrations/materialize.py::iter_command_sources()` enumerates
*every* `*.md` at the top of `bookwright.resources/commands` and `generate_skill_md`
turns each into `<skills_dir>/<name>/SKILL.md` for both integrations — substituting
only `{ARGS}`, copying cited `references/`, routing the description through
`get_description`, and linting the result. `bookwright init` calls this for the
whole roster with no per-command branching. So the moment `bookwright-verify.md`
exists in the tree, `init` materializes a valid skill in `.claude/skills/` and
`.agents/skills/` (FR-002, FR-017, SC-001) for free. This mirrors how iteration 013
added `bookwright-research` (also a pure source-file + roster addition).

**Alternatives considered**: a `bookwright verify` CLI subcommand that runs the
check — rejected: the check "requires judgement, not code" (the entire premise of
US1 and design § 20.6); a deterministic CLI verb is iteration 014's `factual_anchor`
validator, which this skill is explicitly the *complement* to (FR-012). A separate
materialization path for "graph-consuming skills" — rejected: `bookwright-continuity`
already consumes the graph through the same generic pipeline; no second path exists
or is warranted (Constitution V, no parallel pipeline — FR-002).

## D2 — The four manual roster sites (and exactly how each gate fails if missed)

**Decision**: Updating the command inventory means editing **four** hand-maintained
roster sites; two further sites are auto-derived and need no edit.

| Site | Kind | Edit needed | Gate that fails if missed |
|---|---|---|---|
| `integrations/descriptions.py::SKILL_DESCRIPTIONS` | hand dict | **+1 entry** | `test_descriptions.test_all_roster_keys_present` (after _ROSTER bumped) + materializer's `get_description` would silently fall back to the source frontmatter — works, but the SC-009 equality gate still requires the dict entry |
| `tests/integrations/test_descriptions.py::_ROSTER` | hand tuple | **+1 name** | `test_all_roster_keys_present`, `test_get_description_returns_table_value_when_keyed`, `test_v0_equality_gate_mirrors_source_frontmatter` |
| `tests/integrations/test_materialize.py::_ROSTER` | hand set | **+1 name** | `test_iter_command_sources_is_exactly_the_roster` |
| `tests/resources/helpers.py::EXPECTED_COMMANDS` + `REPORT_ONLY_COMMANDS` | hand tuples | **+1 name each** | `test_command_frontmatter.test_exactly_the_expected_commands_exist`; and absence from `REPORT_ONLY_COMMANDS` means `test_command_body.test_report_only_states_no_writes` never asserts the "no escribe nada" guard for verify |
| `materialize.py::iter_command_sources` | glob | **none** | n/a — picks up the file automatically |
| `test_setup_materialize.py::_ROSTER`, `test_e2e_materialize.py::_ROSTER` | derived from `iter_command_sources()` | **none** | n/a — extend automatically |

**Rationale**: Three rosters are literal copies of the command list rather than
derived from `iter_command_sources()`. That redundancy is deliberate in the existing
code (each is the *expectation* its gate checks the live tree against), so the right
move is to update them, not to refactor them into a single source in this iteration
(that would be scope creep). Enumerating them here so `/speckit-tasks` emits a task
per site and `/speckit-analyze` can confirm completeness.

**Alternatives considered**: deriving all rosters from `iter_command_sources()` to
delete the duplication — rejected as out-of-scope refactoring of working code under
test; the iteration is a command addition, not a roster-architecture change.

## D3 — One authoritative bilingual `description`, drafted once

**Decision**: Draft the `description` string once and use it byte-identically in
both the source frontmatter and `SKILL_DESCRIPTIONS["bookwright-verify"]`. Working
draft (final wording fixed at implement time, but this satisfies every gate):

> Verifica el manuscrito ya redactado contra las anclas de investigación: detecta
> pasajes que contradicen lo investigado — anacronismos, errores de procedimiento
> (algo ilegal o imposible en la ambientación) e inexactitudes culturales o
> lingüísticas. Verify the drafted manuscript against the research anchors: flag
> passages that contradict the research — anachronisms, procedural errors (something
> illegal or impossible in the setting) and cultural or linguistic inaccuracies.
> Úsalo cuando el autor pida "verifica si mi manuscrito contradice lo investigado" /
> "check my manuscript against my research". Es de solo lectura y trabaja en fase
> POST-draft. NO compara el manuscrito con la biblia (eso es bookwright-continuity)
> ni audita la integridad estructural de las anclas (eso es el validator
> factual_anchor).

**Rationale**: It is bilingual (ES + EN triggers, satisfying
`test_command_activation.test_description_is_bilingual` and SC-006), names the
canonical ES and EN prompts from FR-004/SC-006, contains `post-draft` (FR-011), is
read-only-flagged, and explicitly repels its two siblings — `bookwright-continuity`
(verify vs the bible — FR-013) and the `factual_anchor` validator (semantic vs
structural — FR-012). It is ~720 characters, comfortably under the 1024 cap
(FR-003). Keeping it identical in both places is what the SC-009 equality gate
(`test_v0_equality_gate_mirrors_source_frontmatter`) requires.

**Alternatives considered**: a shorter description omitting the sibling repulsion —
rejected: FR-012/FR-013 require the body and trigger surface to disambiguate verify
from both continuity and factual_anchor so the agent invokes the right command.

## D4 — Build then query the graph (clarification-driven), inline in the body

**Decision**: The body instructs the agent to run `bookwright graph build` first
(refresh the derived cache) and then `bookwright graph query <SPARQL>` to load
anchors and their sources, exactly as `bookwright-continuity` builds before
consuming the graph.

**Rationale**: FR-005 mandates the SPARQL surface; the clarification resolved that
`graph query` only works against a built graph, so building first guarantees the
query never hits a stale or missing `bible/graph.ttl` (Constitution I — the graph is
a derived cache, always rebuildable). Writing the CLI call inline matches the
`bookwright-continuity` precedent that `test_command_body.test_graph_build_is_inline`
pins; **this plan extends that test to also assert the inline build for
`bookwright-verify`** (the test already parametrizes `bookwright-constitution` and
`bookwright-continuity`, so verify becomes the **third** entry). Note the precedent is
narrower than it looks: `bookwright-continuity` runs `graph build --json` and consumes
that JSON directly — it does **not** run a separate `bookwright graph query`. So
`bookwright-verify` is the **first** command source whose body authors an explicit
`graph query <SPARQL>` step. The build-first/read-only/report-only shape is the
continuity precedent; the `graph query` step is new, which is exactly why D5 pins the
correct selection rule rather than leaning on a non-existent class match.

**Alternatives considered**: reading `bible/research/*.md` by hand — rejected:
FR-005 fixes the read surface to the graph (SPARQL over the `bw:`/CIDOC triples), and
re-parsing the research files would duplicate the indexer and miss promotion/anchor
resolution. Querying without building — rejected by the clarification (stale/missing
graph risk).

## D5 — The SPARQL the body cites: anchors via `bw:promotes`, not a `bw:Anchor` class

**Decision**: The body instructs a `graph query` that selects **anchors** as the
`crm:E13_Attribute_Assignment` nodes carrying a `bw:promotes` edge, and traverses
`anchor —bw:promotes→ finding —bw:supportedBy→ source` to read each finding's
`bw:claim` and each source's provenance facets, so every reported contradiction can
cite its source. There is **no** `bw:Anchor`/`bw:Source` `rdf:type` to match on.

**Why the obvious form is wrong (verified against the model)**: In
`golem/modules/provenance.py`, `Source.to_triples()` emits **no** `rdf:type` at all —
a source is typed only via `crm:P2_has_type → crm:E55_Type` (research D2 of iteration
012). `Anchor` *and* `Finding` both reify on `crm:E13_Attribute_Assignment` (the same
`CLASS_IRI["AttributeAssignment"]`), so a class match cannot tell them apart. The one
predicate unique to an anchor is `bw:promotes` (a finding never carries it). Querying
`?a a bw:Anchor` / `?s a bw:Source` returns **zero rows** — confirmed empirically by
building the chain through the real classes and the `RdflibIndexer` and running both
forms — which would make the skill silently report "nothing to verify", defeating
SC-002/SC-003. The `bw:` namespace (`https://bookwright.dev/vocab/bw#`) holds
*predicates and controlled-vocabulary individuals*, not these classes.

**Verified reference query** (prefixes `bw:`/`crm:`/`golem:` are bound by
`graph query` via `bind_prefixes`; this exact query returned the full chain in a
real built graph):

```sparql
PREFIX bw:  <https://bookwright.dev/vocab/bw#>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
SELECT ?anchor ?claim ?target ?source ?reference ?author ?reliability ?originalQuote ?translation WHERE {
  ?anchor bw:promotes ?finding .
  OPTIONAL { ?anchor bw:constrains ?target . }      # the narrative entity it binds (may be absent)
  ?finding bw:claim ?claim .                          # the researched fact
  OPTIONAL {
    ?finding bw:supportedBy ?source .                # provenance behind the anchor
    OPTIONAL { ?source bw:reference     ?reference . }
    OPTIONAL { ?source bw:author        ?author . }
    OPTIONAL { ?source bw:reliability   ?reliability . }    # an E55 individual (bw:reliability/alta…)
    OPTIONAL { ?source bw:originalQuote ?originalQuote . }
    OPTIONAL { ?source bw:translation   ?translation . }    # emitted iff source language ≠ book language
  }
}
```

**Rationale**: FR-007 requires every finding to cite (b) the violated anchor and
(c) the source behind it; the anchor→finding→source provenance link is the
iteration-012 model. The skill consumes that chain from the graph rather than
redefining it (Key Entities note: Anchor/Source are iteration-012 entities, not
redefined here).

**Alternatives considered**: pinning the exact SPARQL string verbatim in the body as
load-bearing — the body may include it as a worked example, but the *contract* is the
selection rule (`bw:promotes` discriminates anchors; sources are reached via
`bw:supportedBy`), which is stable even if the agent adjusts the projection. Matching
a `bw:Anchor`/`bw:Source` class — rejected: no such class exists (see above).

## D6 — Report shape: chapter/scene grouping, four-part findings, severity rubric

**Decision**: The "Output" section specifies a human-readable report grouped by
chapter/scene, each contradiction carrying (a) the quoted manuscript passage, (b)
the violated anchor, (c) the anchor's source, (d) a severity from
`error`/`warning`/`info`, and a `file:line` reference where the location is known.
Severity rubric: definite/factual contradictions (hard anachronism;
illegal/impossible procedure) → `error`; soft cultural/stylistic nuances →
`warning`/`info`.

**Rationale**: This is FR-007, FR-008, and US2 verbatim. Reusing the validation
system's `Severity` vocabulary (per the clarification) makes the two § 20.6 layers
(`factual_anchor` deterministic + this skill) report gravity in one shared scale so
the author can triage across them. The report is prose, not a JSON envelope (FR-009)
— consistent with `bookwright-continuity`.

**Alternatives considered**: a custom severity scale (e.g. high/med/low) — rejected
by the clarification in favour of the shared enum.

## D7 — Two absent-prerequisite branches, never an opaque failure

**Decision**: The "Información faltante" section instructs: if there is **no
manuscript**, report an absent prerequisite and point to `bookwright-draft`; if
there are **no anchors** (no `bible/research/`, no promoted anchors, or
`[research].enabled = false`), report that there is nothing to verify and produce no
contradictions.

**Rationale**: FR-015, FR-016, US1 scenarios 4–5, SC-007, and the
`bookwright-continuity` "prerrequisito ausente" pattern. Because the command writes
nothing, it does not use the `[PENDING: …]` marker protocol (that is for generative
commands), matching how continuity's "Información faltante" is phrased.

**Alternatives considered**: failing/exiting non-zero on missing prerequisites —
rejected: the skill is an LLM prompt, not a CLI verb; "report it, don't fail
opaquely" is the established pattern.

## D8 — Docs and the historical fixture are iteration 17, not here

**Decision**: Do not touch `docs/authoring.md`, create `docs/research.md`, or add a
`tiny-historical/` fixture and an E2E `test_research_workflow.py` in this iteration.

**Rationale**: The implementation plan assigns the historical fixture, the
research-workflow E2E, and the documentation page explicitly to **iteration 17**
(bookwright-implementation-plan.md § "Iteración 17"). Iteration 013
(`bookwright-research`) likewise did not add itself to `docs/authoring.md`'s command
tables, confirming docs are deferred to 17. Pulling them in now would violate Scope &
Release Discipline. The skill's behavioural acceptance against a real anachronism is
the manual run in this iteration's quickstart and the iteration-17 E2E.

**Alternatives considered**: adding a `bookwright-verify` row to
`docs/authoring.md` now for symmetry — rejected to stay consistent with how research
was handled and to keep the iteration to its declared scope; iteration 17 owns the
docs sweep that adds both research and verify.
