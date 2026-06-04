# Feature Specification: `factual_anchor` Validator

**Feature Branch**: `014-factual-anchor-validator`

**Created**: 2026-06-04

**Status**: Draft

**Input**: User description: "Necesidad: las anclas de investigación solo sirven si están bien formadas y no chocan con la cronología. Necesitamos un validator de código (determinista, complementario a los chequeos LLM) que audite la integridad de las anclas sobre el grafo. […] Referencia: ver bookwright-design.md § 20.6 y § 13 (Sistema de Validación)."

## Clarifications

### Session 2026-06-04

- Q: When one source is missing several mandatory provenance facets, report per-facet or per-source? → A: One **warning per missing facet** (matches FR-007's singular wording; each gap independently fixable and testable; no extra noise on well-formed sources).
- Q: When a source backing an anchor is missing the reliability rating entirely, how do the provenance-completeness (FR-007) and threshold (FR-008) checks interact? → A: Report it **once** as a missing `reliability` facet (FR-007); the unrated source contributes no rating to FR-008's best-reliability computation. If no supporting source carries any rating, best-of-none fails FR-008's threshold and the anchor is also flagged as below-minimum — but a single source is never double-labelled as both "incomplete" and "under-reliable" for the same missing rating.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Audit the structural integrity of research anchors (Priority: P1)

An author has researched a historically-grounded novel and promoted several
findings to binding **anchors** (facts the manuscript may not contradict). Before
trusting those anchors, they want a fast, deterministic check that each one is
*well-formed*: that it rests on at least one cited source, that the source carries
complete provenance, that its supporting source is reliable enough to bind the
story, and that the narrative element it constrains actually exists. They run
`bookwright validate` and the `factual_anchor` check reports, as **warnings**, any
anchor that is unsourced, under-reliable, provenance-incomplete, or dangling —
without making any judgement about whether the *claim itself* is true.

**Why this priority**: This is the core of the iteration. An anchor that is
malformed is worse than no anchor — it gives false confidence. The structural
audit is the deterministic floor the later semantic LLM check (`bookwright-verify`,
a separate iteration) builds on, and it delivers value entirely on its own.

**Independent Test**: Build the graph for a project that contains a well-formed
anchor, an anchor whose promoted finding has no source, an anchor backed only by a
low-reliability source, and an anchor that constrains an entity absent from the
bible; run `bookwright validate` and confirm exactly the three malformed anchors
are reported as warnings, each naming the offending anchor and reason, and the
well-formed one is silent.

**Acceptance Scenarios**:

1. **Given** an anchor that promotes a finding with no supporting source, **When**
   `bookwright validate` runs, **Then** the `factual_anchor` check emits a
   **warning** that the anchor has no source.
2. **Given** an anchor whose best supporting source has reliability below
   `[research].min_reliability_for_anchor`, **When** validate runs, **Then** a
   **warning** is emitted that the anchor's support is below the configured minimum
   reliability.
3. **Given** an anchor backed by a source missing a mandatory provenance facet
   (e.g. no author, no access date, or no original-language quote), **When**
   validate runs, **Then** a **warning** is emitted naming the missing facet.
4. **Given** an anchor whose constrained narrative entity does not resolve to an
   entity present in the graph, **When** validate runs, **Then** a **warning** is
   emitted that the anchor constrains a missing narrative entity.
5. **Given** a fully well-formed anchor (sourced, reliable enough, complete
   provenance, resolving to a real entity), **When** validate runs, **Then** the
   `factual_anchor` check produces **no** violation for it.

---

### User Story 2 - Catch anchors that clash with the timeline (Priority: P2)

An author has pinned a researched fact to a date — "the regulation that licensed
private detectives in Spain existed from 1957" — and attached it as an anchor with
a time-span constraining a timeline event. If the event the anchor constrains is
placed by the timeline in a contradictory period (a real anachronism), the author
wants that surfaced as a hard **error**, not a soft note: it breaks the story's
factual spine. They run `bookwright validate` and a chronological clash between an
anchor's time-span and the event it constrains is reported as an error, reusing the
same interval reasoning that already powers the temporal validator.

**Why this priority**: Anachronism is the one anchor problem the design rates as a
hard failure (error), because it is a concrete, deterministic contradiction the
graph already contains. It is high value but rides below the structural audit
because it only applies to the subset of anchors that carry a time-span.

**Independent Test**: Build a graph with a timeline event dated to one period and
an anchor whose time-span is disjoint from / contradicts that event's interval;
confirm `bookwright validate` reports an **error** for the anachronism. Add a second
anchor whose time-span is consistent with its event and confirm it produces no
error.

**Acceptance Scenarios**:

1. **Given** an anchor with a time-span constraining a timeline event whose interval
   contradicts that time-span, **When** validate runs, **Then** an **error** is
   emitted reporting the anachronism, with the implicated triples.
2. **Given** an anchor with a time-span that is chronologically consistent with the
   event it constrains, **When** validate runs, **Then** **no** anachronism error is
   emitted.
3. **Given** an anchor that carries a time-span but constrains a target with no
   comparable temporal interval (e.g. a character), **When** validate runs, **Then**
   **no** anachronism error is emitted (nothing to contradict — no false positive).
4. **Given** `bookwright validate --severity error`, **When** anchors have both
   structural warnings and an anachronism, **Then** only the anachronism error is
   reported and the structural warnings are suppressed (existing severity gate).

---

### User Story 3 - Zero-config discovery and cost-free on non-research projects (Priority: P3)

A project lead expects validation to "just work": the new check should appear in
`bookwright validate` without any wiring, obey the existing `[validators]`
enable/disable controls, and impose no cost on projects that don't do research. A
novel with no `bible/research/` directory, or one that has switched
`[research].enabled = false`, should see zero anchor violations — the check is inert
when there is nothing to audit.

**Why this priority**: Frictionless adoption and "you pay only if you use it" are
required by the project's scope discipline, but they are a property of how the check
plugs in rather than what it detects, so this lands last.

**Independent Test**: On a freshly `init`-ed project with no research, run
`bookwright validate` and confirm `factual_anchor` runs and emits zero violations;
disable it via `[validators].disabled` and confirm it no longer appears; set
`[research].enabled = false` on a project that *does* have anchors and confirm the
check emits zero violations.

**Acceptance Scenarios**:

1. **Given** a project with no `bible/research/` (no anchors), **When** validate
   runs, **Then** `factual_anchor` produces zero violations and the run succeeds.
2. **Given** a manifest that lists `factual_anchor` under `[validators].disabled`,
   **When** validate runs, **Then** the check does not run.
3. **Given** a manifest with `[validators].enabled` naming a set that includes
   `factual_anchor`, **When** validate runs, **Then** the check runs (and others not
   listed do not), via the existing selection mechanism.
4. **Given** `[research].enabled = false` on a project that contains anchors,
   **When** validate runs, **Then** `factual_anchor` is inert and emits zero
   violations.

---

### Edge Cases

- **Anchor promoting an open finding**: an open finding carries no claim or source,
  so the anchor that promotes it is reported as unsourced (US1 scenario 1).
- **Multiple supporting sources of mixed reliability**: the anchor is judged by its
  **best** (highest) supporting reliability — `alta` > `media` > `baja` — mirroring
  "minimum reliability to promote a finding"; a single high-reliability source
  satisfies the threshold even alongside weaker ones.
- **Anchor with only a `begin` or only an `end` year** (open-ended time-span): the
  anachronism check applies to the bound that is present; an absent bound is simply
  not compared.
- **Anchor constraining the timeline as a whole** (rather than one event): its
  time-span is checked against the timeline's events / overall bounds, reusing the
  temporal interval model.
- **Source language equals the book language**: no translation is expected, so a
  missing translation is **not** flagged; when the languages differ, a missing
  translation is part of incomplete provenance (US1 scenario 3).
- **Graph built by an older reader or hand-edited** so that a source backing an
  anchor is provenance-incomplete: still flagged (the audit does not assume the
  build-time reader already rejected it — defense in depth).
- **BCE / multi-format years** in time-spans: handled by reusing the temporal
  validator's year parsing, so anachronism detection behaves identically to the
  existing timeline checks.
- **Anchor whose narrative target was dropped at build time** because it did not
  resolve in the bible: surfaces in the graph as an anchor with no resolved
  constraint, which the check reports as a missing-entity warning (US1 scenario 4).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a validator named `factual_anchor` that
  conforms to the existing Validator Protocol (a `name`, a `severity_default`, and a
  `validate(project, indexer) -> list[Violation]` method that returns an empty list
  when there are no problems).
- **FR-002**: The validator's `severity_default` MUST be **warning**: structural
  problems are reported as warnings and only hard anachronisms are reported as
  errors (design § 13.2, § 20.6).
- **FR-003**: The validator MUST be deterministic and side-effect-free — it MUST NOT
  write to disk, fetch anything over the network, mutate the graph, or invoke an LLM
  — consistent with the Validator contract.
- **FR-004**: The validator MUST be auto-discovered as a built-in by the existing
  validator registry (no hand-registration and no new discovery mechanism) and MUST
  be subject to the existing `[validators].enabled` / `[validators].disabled`
  selection rules.
- **FR-005**: `bookwright validate` MUST include the validator with the existing
  `--json`, `--scope`, and `--severity` behaviors unchanged; the validator only
  produces `Violation`s and relies on the runner/report for filtering and output.
- **FR-006**: For each anchor, when the finding it promotes is backed by no source,
  the validator MUST emit a **warning** that the anchor has no source.
- **FR-007**: For each source backing an anchor, when that source is missing any
  mandatory provenance facet — reference, author, original language, source type,
  reliability, reliability justification, access date, original-language quote, and
  a translation when the source's language differs from the book's — the validator
  MUST emit **one warning per missing facet**, each naming the specific facet. A
  source missing several facets therefore yields several distinct warnings.
- **FR-008**: For each anchor, when the **best** (highest) reliability among its
  supporting sources is below `[research].min_reliability_for_anchor`, the validator
  MUST emit a **warning**. Reliability is ordered `alta` > `media` > `baja`. A
  supporting source that carries **no** reliability rating contributes no value to
  the best-reliability computation (its missing rating is reported only as a
  provenance-incomplete facet under FR-007, never additionally as "under-reliable").
  When **no** supporting source carries any rating, the best reliability is treated
  as below any threshold and the anchor is flagged.
- **FR-009**: For each anchor, the finding it promotes and the narrative entity it
  constrains MUST exist in the graph; an anchor whose constrained narrative entity
  does not resolve to an entity present in the graph (including one whose constraint
  link was dropped at build time because the target was absent) MUST be reported as
  a **warning**.
- **FR-010**: When an anchor carries a time-span (a `begin` and/or `end` year) and
  constrains a narrative event (or the timeline) whose own interval contradicts that
  time-span, the validator MUST emit an **error** reporting the anachronism. A
  contradiction is the same disjoint-range / inconsistent-ordering condition the
  temporal validator detects between two intervals.
- **FR-011**: The anachronism check MUST **reuse** the temporal validator's interval
  model and contradiction logic rather than re-implementing interval reasoning;
  there must be one source of truth for "two intervals contradict."
- **FR-012**: When an anchor carries a time-span but the constrained target has no
  comparable temporal interval (e.g. a character or setting), the validator MUST NOT
  emit an anachronism violation for it (no false positives on legitimately
  non-temporal anchors).
- **FR-013**: Each emitted `Violation` MUST identify the offending anchor in its
  message and carry the implicated triples where applicable; it SHOULD carry the
  originating research-file location (path, with line when the graph records one) so
  `--scope` filtering and report grouping behave as for the other validators, and
  MAY be location-less when no location is recorded (as the temporal validator
  already is for some findings).
- **FR-014**: The validator MUST read `[research].enabled` and
  `[research].min_reliability_for_anchor` from the project manifest (via the
  validation context), applying the documented defaults when the block is absent.
- **FR-015**: When `[research].enabled = false`, the validator MUST be inert and emit
  zero violations even if anchors exist in the graph.
- **FR-016**: On a project with no anchors (no `bible/research/`, or research present
  but with no promoted anchors), the validator MUST emit zero violations.
- **FR-017**: The validator MUST check only **structural** integrity, never semantic
  truth: it MUST NOT judge whether a claim is factually correct or whether the
  manuscript contradicts a researched fact (that is the separate `bookwright-verify`
  LLM check), and it MUST NOT attempt any auto-fix — it reports only.

### Key Entities *(include if feature involves data)*

- **`factual_anchor` validator**: the new built-in deterministic check; carries a
  `name`, a `warning` `severity_default`, and the `validate` method; reports
  `Violation`s and never mutates anything.
- **Anchor** *(graph entity from iteration 012, not redefined here)*: the audited
  subject — a binding constraint that *promotes* a finding, *constrains* a narrative
  entity (or the timeline), and optionally carries a `begin`/`end` time-span.
- **Finding / Source** *(graph entities from iteration 012)*: a finding records a
  claim supported by sources; a source carries the provenance facets and the
  reliability rating the audit inspects.
- **`[research]` manifest block** *(from iteration 013)*: supplies `enabled` (the
  inert switch) and `min_reliability_for_anchor` (the reliability threshold).
- **`Violation` / `Severity`** *(from the validation system)*: the existing report
  unit the validator emits, carrying `validator`, `severity`, `message`, `source`,
  and implicated `triples`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a project containing an unsourced anchor, an under-reliable anchor,
  and a provenance-incomplete anchor, all three are flagged as warnings and a fully
  well-formed anchor produces zero violations — 100 % of malformed anchors detected,
  0 false positives on the well-formed one.
- **SC-002**: An anchor whose time-span contradicts the interval of the event it
  constrains is reported as an **error**; a chronologically-consistent anchor and a
  time-spanned anchor constraining a non-temporal target both produce **no** error.
- **SC-003**: An anchor whose constrained narrative entity is absent from the graph
  is reported as a warning — verifiable on a hand-built graph without inspecting
  implementation.
- **SC-004**: On a project with no research, the validator runs and emits zero
  violations; with `[research].enabled = false` it emits zero violations even when
  anchors exist.
- **SC-005**: The validator participates in `bookwright validate` indistinguishably
  from the existing validators: it honors `--json` (its violations appear in the JSON
  document), `--scope` (filtering by path narrows its violations), and `--severity`
  (e.g. `--severity error` keeps the anachronism error and drops the structural
  warnings), and obeys `[validators].enabled` / `disabled`.
- **SC-006**: The project's single-sourced coverage gate stays green (≥ 80 %,
  `fail_under = 80`; Constitution VIII), and the new validator module is exercised by
  a unit suite covering each violation kind (unsourced, under-reliable,
  provenance-incomplete, missing entity, anachronism) and the clean / inert / no-
  research cases.

## Assumptions

- **Reliability scale and threshold**: reliability is the controlled scale `alta` /
  `media` / `baja` (design § 20.3), ordered `alta` > `media` > `baja`; the threshold
  comes from `[research].min_reliability_for_anchor` (default `"media"`, iteration
  13). An anchor satisfies the threshold when its best supporting source meets or
  exceeds it.
- **Reasoning surface**: the validator reasons over the **built graph** through the
  existing indexer seam plus the manifest exposed by the validation context, exactly
  as `temporal` and `character_presence` do; it does not re-parse research files
  itself, re-fetch sources, or call any model. The graph is the derived cache the
  validator audits.
- **Unresolved constraints**: an anchor whose intended narrative target did not
  resolve in the bible appears in the graph with no resolved constraint (the
  iteration-12 reader drops the link to a build-time warning); the validator treats
  that state as the "constrains a missing entity" warning (FR-009).
- **Anachronism semantics**: a "hard anachronism" is a definite interval
  contradiction (disjoint year ranges, or an ordering inconsistency) between the
  anchor's time-span and the constrained event's/timeline's interval, decided by the
  same rules the temporal validator already applies between two event intervals
  (FR-011). When no comparable interval exists, no temporal violation is produced.
- **Default activation**: `factual_anchor` ships as a built-in, so under the default
  `[validators]` configuration it runs automatically; it is a harmless no-op on
  projects without research (FR-016) and can be turned off via
  `[validators].disabled`.
- **Provenance-completeness facets** are those the iteration-12 `Source` model
  requires (reference, author, original language, type, reliability, reliability
  justification, access date, original-language quote, plus translation when the
  source language differs from the book language). The build-time reader normally
  enforces these, so the validator's facet check is defense-in-depth for hand-edited
  or older graphs (FR-007).
- **Scope discipline**: this is M4 / v0.2 work (design § 20.6). It deliberately does
  **not** implement the semantic `bookwright-verify` LLM check (a later iteration),
  any auto-fix, or vector search (v0.3); and it adds no GOLEM ontology classes
  (Constitution X) — it only reads the `bw:`/CIDOC triples iteration 12 already
  emits.

## Dependencies

- **Iteration 010 (validation system)**: the `Validator` Protocol, `Violation` /
  `Severity`, `ValidationContext`, the registry's built-in auto-discovery and
  `[validators]` resolution, the `validate` runner/report (`--json` / `--scope` /
  `--severity`), and the `temporal` validator plus its interval/query helpers reused
  for anachronism detection. Must be on `main` (it is).
- **Iteration 012 (research provenance model)**: the `Source` / `Finding` / `Anchor`
  graph entities, their `bw:` predicates and time-span shape, and `sources.ttl` —
  the anchors this validator audits. Must be on `main` (it is).
- **Iteration 013 (research skill + `[research]` block)**: the `[research]` manifest
  block exposing `enabled` and `min_reliability_for_anchor` that this validator
  reads. Must be on `main` (it is).
- **Iteration 006 (graph indexer)**: `bookwright graph build` produces the
  `graph.ttl` derived cache the validator queries.
