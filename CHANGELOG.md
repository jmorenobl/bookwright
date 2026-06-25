# Changelog

All notable changes to Bookwright are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project aims to follow semantic versioning.

## [0.5.12] — 2026-06-25

Iteration **053** — issue #1 **track C** (move 3, semantic judgment): the third
move-3 dimension, **first half (honesty)** — the same split head-hopping took,
honesty (045/050) before judgment (052). Today `focalization` runs
`_first_person_breaks` over a **closed** explicit-pronoun set
(`yo`/`nosotros`/…/`i`/`we`) under a third-person voice and is **silent** about
everything that set cannot see — Spanish pro-drop verbal morphology (`Caminé`,
`Me senté`), an **open** set no regex captures without reopening issue #1's
whack-a-mole (**DEBT-021**). That silence is the `[]`-means-clean lie at the
sub-check level. This patch closes it: `focalization` declares the recall
ceiling **honestly** with a `pending_capability` abstention under **both**
third-person branches, while the explicit-pronoun `warning`s stay
**byte-identical**. The forced contract plumbing — an additive optional `code`
discriminator on the abstention types — rides inside the patch that needs it,
exactly as iteration 044 added `kind`. **No** first-person nudge yet (that, plus
DEBT-021's closure, is iteration 054); **no** gate, **no** skill change, the 044
green predicate **byte-identical**, no `error` born, **no `DEBT.md` entry
removed** (DEBT-021's honesty half landed; its judgment half stays open).

### Added

- **Optional `code` discriminator** (`src/bookwright/validation/base.py`) — both
  `Abstention` (returned) and `NotEvaluatedResult` (recorded) gain
  `code: str | None = None`, a short, stable per-dimension tag
  (`"first_person_recall"`, `"head_hopping"`, `"undeclared_characters"`)
  serialized **additively** in `NotEvaluatedResult.to_json` (`code: null` for a
  raised abstention), precisely as iteration 044 added `kind`. The raised
  `NotEvaluated` **exception** does not gain `code` (the discriminator is of
  *returned* abstentions); `not_evaluated_sort_key` stays `(validator, reason)`
  (`code` is **not** a sort term — the two `focalization` reasons already differ,
  so the order is total).
- **First-person-recall honesty** (`validators/focalization.py`) — a new
  `_FIRST_PERSON_RECALL_PENDING` reason and an
  `Abstention(…, pending_capability, code="first_person_recall")` emitted under
  **both** third-person branches (under limited-third it joins the existing
  head-hopping abstention in the same partial `EvalResult`; the non-limited bare
  `list` return is now wrapped in an `EvalResult` to carry it). The
  first-person-recall ceiling is now **visible** in `not_evaluated[]` instead of
  silently absent.

### Changed

- **`status` nudges key on `(validator, code)`** (`src/bookwright/status/rules.py`)
  — the iteration-052 `_judges(validator)` predicate is generalized to
  `_judges(validator, code)` (`… AND r.code == code`), because `focalization` now
  emits **two** `pending_capability` abstentions. `judge_head_hopping` re-points
  to `(focalization, head_hopping)` and `judge_undeclared_characters` to
  `(character_unknown_mentions, undeclared_characters)` — now **precise**: the
  head-hop nudge never mis-fires on the new recall abstention, and no first-person
  nudge exists yet (iteration 054).
- **`character_unknown_mentions` converted form (b)→(c)**
  (`validators/character_unknown_mentions.py`) — from a raised `NotEvaluated`
  (which cannot carry a `code`) to a returned
  `EvalResult([], [Abstention(…, code="undeclared_characters")])`, so the
  code-keyed nudge can match it. Observationally additive (only the `code` key
  changes from `null`); the reason, kind, and nudge behaviour are unchanged.
- The `focalization` runner stamps `code` through its **single** `_record`
  naming point (form (c) passes `abstention.code`, the raised path defaults
  `None`) — no second naming authority. `bookwright-design.md` §§ 13.4/13.5/20.6
  record the contract (`not_evaluated` gains `code`) and the move-3 honesty/
  judgment split; **DEBT-021** is updated (honesty landed; judgment → 054), not
  removed. `validation/report.py` (the green predicate) and `_first_person_breaks`
  / the `_FIRST_PERSON` regex are **byte-identical**.

## [0.5.11] — 2026-06-25

Iteration **052** — issue #1 **track C** (move 3, semantic judgment): the
**second vertical slice**, the same pattern as 051 with only the judged
dimension changed. Corroborated by the **third dogfood**
(`el-año-de-las-casas-vacías`, third-person limited): a **real head-hop** — the
interiority of `Irene` inside a chapter focalized on `Teo` — was left
**invisible**, because `focalization` honestly abstains under limited-third
(`Abstention(_HEAD_HOPPING_PENDING, pending_capability)`, iteration 050) rather
than fake the judgment. This slice closes that gap with semantic judgment: the
LLM verdict is an **Agent Skill** (the CLI stays deterministic, **no** LLM
dependency), the `not_evaluated` channel **is** the contract (each
`pending_capability` abstention is a judgment task the skill answers), and the
verdict is **informative — not a gate** (no `error` is born from an LLM; the
044 green predicate is **byte-identical**). The third and last move-3 dimension
(the pro-drop first-person recall, **DEBT-021**) stays open — head-hopping
carries no debt of its own, so **no `DEBT.md` entry is removed** this slice.

### Added

- **`bookwright-continuity` fifth axis** — «head-hopping / saltos de punto de
  vista / focalización rota» in `## Procedimiento` + `## Output`
  (`src/bookwright/resources/commands/bookwright-continuity.md`). It reads the
  declared narrative voice (`bible/constitution.md`) and proceeds **only** under
  third-person *limited* (omniscient / first-person → nothing), reads the focal
  POV per chapter from the prose **POV calendar** (`bible/pov-structure.md`,
  "Calendario de POV" — newly added to "Archivos a leer"), and the person
  roster, then judges per chapter whether the prose attributes **interiority**
  to a non-focal POV character — reporting each head-hop as one more continuity
  deviation (the manuscript quote + "interiority of *X* under the POV of *Y* in
  *<chapter>*" + a suggestion). When the calendar is absent / `[PENDING]` it
  **reports the grounding gap and does not guess** (mirroring how `focalization`
  treats a `[PENDING]` voice, iteration 037). The widened bilingual
  `description` is mirrored verbatim into
  `SKILL_DESCRIPTIONS["bookwright-continuity"]` (`integrations/descriptions.py`).
- **`judge_head_hopping` status rule** (`src/bookwright/status/rules.py`) — a
  second **green-preserving** `next_action` pointing the author to
  `bookwright-continuity` when `focalization` abstains on head-hopping. It is
  keyed via the new shared `_judges(validator)` predicate, which requires
  `validator == … AND kind is pending_capability` — so it fires on the
  head-hopping `pending_capability` gap but **not** on `focalization`'s
  `missing_input` gap (covered by `activate_dormant_validators`). It sits after
  `judge_undeclared_characters`, before `define_focus`; the two move-3 nudges
  can co-fire.

### Changed

- **`_JUDGE_SOURCES` frozenset removed** (`src/bookwright/status/rules.py`) — the
  iteration-051 name-only keying is generalized to the `_judges(validator)`
  predicate. `judge_undeclared_characters` adopts it **byte-identically**
  (`character_unknown_mentions` always abstains `pending_capability`), while the
  new predicate also expresses what name-only keying could not: `focalization`
  emits **both** abstention kinds, and only the `pending_capability` one is a
  judgment the skill answers.
- `bookwright-design.md` § 20.6.2 marks the move-3 **second slice landed**;
  § 13.5 reframed. No `DEBT.md` entry removed (**DEBT-021 stays open**);
  `focalization` and all of `validation/` are untouched; the green predicate and
  the error-only CI gate are byte-identical.

## [0.5.10] — 2026-06-24

Iteration **051** — issue #1 **track C** (move 3, semantic judgment): the
**first vertical slice**. Activated and corroborated by the **third dogfood**
(`el-año-de-las-casas-vacías`, a literary multi-POV novel in third-person
limited): on real prose the honest open-set abstention (track A) silences the
noise (organizations, toponyms) **and** the signal (a character used but never
declared — `Amelia`, four mentions, no bible sheet — left **invisible**) in the
**same** gesture; only semantic judgment separates them. The move-3 frontier
(`bookwright-design.md` § 20.6.1) and concrete contract (§ 20.6.2) are now
landed: the LLM judgment is an **Agent Skill** (the CLI stays deterministic,
**no** LLM dependency), the `not_evaluated` channel **is** the contract between
the deterministic and semantic layers (each `pending_capability` abstention is a
judgment task the skill answers), and the verdict is **informative — not a
gate** (the gate stays the deterministic `validate`; no `error` is born from an
LLM). This slice covers the **undeclared-character** dimension and **closes
DEBT-013** — the organization-vs-undeclared-person distinction it asked for is
exactly what the skill now makes, with no fifth roster. The other two move-3
dimensions (head-hopping and the pro-drop first-person recall, DEBT-021) follow
the same pattern in later slices.

### Added

- **`bookwright-continuity` fourth axis** — «menciones de conjunto abierto /
  personajes sin declarar» in `## Procedimiento` + `## Output`
  (`src/bookwright/resources/commands/bookwright-continuity.md`). It reads the
  person roster from the `bible/characters/*.md` `name:` fields (**not** the
  graph — `G1_Character` carries no `rdfs:label`, so the authored name lives in
  the sheet and the URI slug), scans the manuscript for proper nouns, and judges
  *a person used in the prose but absent from the bible* (e.g. `Amelia`) versus
  an organization / place-name / vocative / title-word, reporting each as one
  more continuity deviation (the manuscript quote + "no entry in
  `bible/characters/`" + a suggestion). The grounding restores the real signal
  without the heuristic's noise.
- **`judge_undeclared_characters` status rule** (`src/bookwright/status/rules.py`)
  — a **green-preserving** `next_action` pointing the author to
  `bookwright-continuity` when `character_unknown_mentions` abstains. It is keyed
  on the abstaining **source** validator, not the `pending_capability` kind, so
  `focalization`'s head-hopping abstention does **not** fire it. This restores
  the discoverability nudge iteration 044 had to remove (the judgment is now
  actionable: the author can run the skill).
- The roster-from-sheets grounding documented in
  `resources/commands/references/golem-character.md`; the widened `description`
  mirrored verbatim into `SKILL_DESCRIPTIONS["bookwright-continuity"]`
  (`integrations/descriptions.py`).

### Changed

- **DEBT-013 closed** and removed from `DEBT.md` — the undeclared-person /
  organization distinction is now delivered by the continuity axis (its
  resolution criterion was "closes when move 3 lands"; this is that landing).
- `bookwright-design.md` § 20.6.2 marks the move-3 **first slice landed**; § 13.5
  reframed to record the skill layer answering the `not_evaluated` channel.

No new CLI surface, no new runtime dependency, no ontology change, no new
validator (the move-3 judgment is the **skill** layer, not Python in
`validation/`), and no LLM in the CLI. The deterministic
`character_unknown_mentions` abstainer is **unchanged**, the 044 green predicate
is **byte-identical**, and the error-only CI gate is untouched.

## [0.5.9] — 2026-06-24

Iteration **050** — issue #1 **track A** (evaluation honesty), closing
**DEBT-019**. The validator contract had been **all-or-nothing**: `validate()`
either returned `list[Violation]` **or** raised `NotEvaluated(reason, kind)` —
a validator could not deterministically check one dimension **and** declare
`not_evaluated` on another in the same run. Iteration 045 hit that wall: under
a third-person-**limited** voice, `focalization` raised
`NotEvaluated(pending_capability)` for head-hopping **before** reaching its
first-person-break check, so the still-working deterministic break check
**stopped running for every focalized project** — a real, suite-**invisible**
coverage regression (DEBT-019; the three focalized fixtures exercise no
first-person break, so nothing went red). This patch introduces a **general
partial-evaluation contract** — a **third** return shape — so a validator can
emit findings **and** abstentions together. `focalization` is its first and
only consumer: under limited-third it now **runs** `_first_person_breaks`
**and** declares the head-hopping `pending_capability` abstention in the same
run. The contract is observationally conservative: `EvalResult([],
[Abstention(r, k)])` is byte-identical on the wire to `raise NotEvaluated(r,
k)`, so the three focalized fixtures stay byte-identical and only a focalized
project that **actually has** a first-person break sees a new (already-correct)
`warning`. No new CLI surface, no new runtime dependency, no ontology change;
the 044 green predicate, the `NotEvaluatedKind` enum, the `not_evaluated[]`
serialization, and the error-only CI gate are **consumed unchanged**.

### Added

- **`Abstention(reason, kind=missing_input)`** and **`EvalResult(violations,
  not_evaluated)`** (`src/bookwright/validation/base.py`) — both frozen
  dataclasses. `Abstention` is the returned-not-raised sibling of
  `NotEvaluated`, carrying **only** `(reason, kind)`; the validator never names
  itself. `EvalResult` is the form-(c) carrier. Both added to `__all__` and
  re-exported from `validation/__init__.py` alongside the widened Protocol.
- **`_record(name, reason, kind)`** (`validation/runner.py`) — the **single**
  name-stamping authority, shared by both the raised total abstention (form
  (b)) and each returned partial abstention (form (c)). The stamping authority
  does not fork (FR-002).
- **Runner-level form-(c) tests** (`tests/validation/test_runner.py`) — a
  synthetic `_Partial` validator proves the general three-shape contract
  **decoupled** from `focalization`; `_PartialEmpty`/`_SkipEmptyTwin` pin the
  observational-equivalence invariant (comparing serialized `to_json()`);
  `_PartialDup` proves form-(c) findings flow through the shared dedup.

### Changed

- **`Validator` Protocol** (`validation/base.py`) — `validate` return widened
  `list[Violation]` → `list[Violation] | EvalResult`. Back-compat preserved: a
  bare-list validator still satisfies the Protocol under `mypy --strict`.
- **`run_validators`** (`validation/runner.py`) — normalizes all three shapes:
  a bare list and a raised `NotEvaluated` exactly as before; an `EvalResult`
  routes its `violations` into the existing dedup + `sort_key` and each
  `Abstention` into `not_evaluated[]` via `_record`. `RunResult` stays the
  4-tuple; both consumers (`commands/validate.py`, `status/queries.py`) are
  untouched.
- **`focalization`** (`validation/validators/focalization.py`) — at the one
  limited-third site, returns `EvalResult(self._first_person_breaks(...),
  [Abstention(_HEAD_HOPPING_PENDING, pending_capability)])` instead of raising.
  The four `missing_input` raises, the omniscient `list` path, the first-person
  `[]` path, `_first_person_breaks`, and `_HEAD_HOPPING_PENDING` are untouched;
  the validator stays prose-only (`triples=()`).
- **Oracles** (`tests/validation/test_focalization.py`) — a new both-at-once
  case asserts exactly one `warning` citing the marker **and** one
  `pending_capability` head-hop entry in the same `EvalResult`; the
  limited-third ES/EN tests are retargeted from `pytest.raises(NotEvaluated)` to
  the `EvalResult` shape; the English break test now asserts the break **fires**
  (the inverse of what iteration 045 asserted — DEBT-019 made concrete).
- **Contract before code** — `bookwright-design.md` § 13.1 (third return shape),
  § 13.2 / § 13.5 / § 20.6.1 (focalization now runs the deterministic
  first-person check **and** abstains on head-hopping under limited-third — the
  determinism↔LLM frontier realized at sub-check level).

### Removed

- **DEBT-019** (the all-or-nothing contract suppressing `focalization`'s
  deterministic first-person-break check under limited-third) — resolved and
  removed from `DEBT.md`; the track-A index line reconciled to cite iteration
  050 as its closure.

## [0.5.8] — 2026-06-24

Iteration **049** — issue #1 **track B** (determinism / polish), closing
**DEBT-017**. The `narrative_structure` validator named the **same** entity
kind — a `G9_Narrative_Unit` — **two** ways: the orphan-beat rule
(`_orphan_beats`) printed the opaque URI slug
(`'el-recuerdo-de-la-primera-marea'`) while the unresolved-role rule
(`_unresolved_roles`) printed the human authored name (`'La fechoría en el
muelle'`). This patch **unifies both onto the human authored name, alone** (no
parenthetical slug — name-plus-slug was rejected: it would change the
unresolved rule's name-only output and re-introduce the opaque id the
`relpath:line` locator already supersedes, the iteration-048 track-B
precedent). The name rides the **already-loaded derived graph**: each `G9`
emits `(uri, rdfs:label, name)` since iteration 035, so `load_orphan_units`
carries the label alongside the URI via an `OPTIONAL` clause — **no** outline
cross-reference, **no** rebuild, **no** lossy slug reconstruction. Both rules
render through **one shared formatting point** (`_unit_identifier(name, slug)`,
mirroring iteration 048's `anchor_handle`) so the two surfaces cannot drift;
the slug survives only as the impossible-by-construction fallback (FR-004). The
single observable delta is the orphan-beat rule's printed identifier (slug →
human name); finding **count, severity, `relpath:line` locator, and the
gate/exit-code contract are unchanged** on every fixture. No new CLI surface,
no new runtime dependency, no ontology change, no new validator/finding/severity
— pure hardening.

### Changed

- **`load_orphan_units`** (`src/bookwright/validation/queries.py`) — return type
  widened `list[str]` → `list[tuple[str, str | None]]`; the orphan query gains
  `OPTIONAL { ?unit rdfs:label ?label }` and sorts by the unique URI so the
  output stays byte-stable. The sole caller is `_orphan_beats` (grep-verified).
- **`narrative_structure`** (`validation/validators/narrative_structure.py`) —
  new module-level `_unit_identifier(name, slug) -> str` (`name if name else
  slug`), the **single** place a `G9` unit is named in a finding message. Both
  `_orphan_beats` (now passing the graph `rdfs:label`, was the slug) and
  `_unresolved_roles` (passing `ref.entity`, byte-identical output) render
  through it. A dead multi-label dedup branch was removed (iteration 035 emits
  exactly one `rdfs:label` per `G9`, so it was unreachable).
- **Oracles** — `test_narrative_structure.py` flips the orphan oracle slug →
  `"Orphan Beat"`; a new test pins the FR-004 slug fallback when the graph
  carries no label; `tiny-quest/expected-narrative.md` flips `omen-beat` →
  `"Omen Beat"`; `test_command.py`'s JSON-envelope orphan oracle flips (the one
  other oracle that moved, found empirically).
- **Contract before code** — `bookwright-design.md` § 13 (validator table)
  records both rules naming the unit by its human authored name;
  `bookwright-roadmap.md` track-B line reconciled (DEBT-017 closed in iteration
  049).

### Removed

- **DEBT-017** (the inconsistent unit identifier across `narrative_structure`'s
  two rules) — resolved and removed from `DEBT.md`; its track-B index
  cross-reference struck through.

## [0.5.7] — 2026-06-24

Iteration **048** — issue #1 **track B** (determinism / polish), closing
**DEBT-015**. The two **graph-consumer** validators emitted unactionable
findings — `factual_anchor` named each defective anchor by its opaque uuid7 URI
with `source: null`, and `temporal` rules (a) cycle, (b) order-vs-overlap and
(c) containment-vs-order also emitted `source: null` while only rule (d) numeric
resolved a locator — whereas the prose validators always give `relpath:line` +
a readable handle. This patch makes both consumers resolve a real locator and a
legible identifier, in **two independent halves**. **`temporal`**: rules a/b/c
adopt rule (d)'s `resolve_source` over a **deterministically-chosen** implicated
event — the carried triple's subject for b/c, the lexicographically smallest
event URI of the strongly-connected component for (a) — so all four rules now
resolve to `bible/timeline.md:<line>` uniformly. **`factual_anchor`**: every
violation now resolves `source` to the anchor's authored
`bible/research/<topic>.md` (via `AnchorIdentity.relpath`, **not**
`resolve_source(anchor.uri)` — an anchor *is* the reified `E13`, so nothing
points at it) and names the anchor by its authored handle (`promotes ->
constrains`) through the **same shared point** (`anchor_handle`) that
`bookwright status` already uses, so the two surfaces can never diverge. The
load-bearing design call (research D1): anchors are `MintedEntity` (uuid7,
re-minted every build) and `validate` reads the *persisted* `graph.ttl` from a
prior `graph build`, so a URI join against the disk graph would miss for **every**
anchor; `factual_anchor` therefore resolves over an **in-process-built,
non-persisting** research corpus (a memoized `ValidationContext.anchor_corpus()`)
and joins by URI within that single build — exactly as `status` does. No new CLI
surface, no new runtime dependency, no ontology change, no new
validator/finding/severity, and the gate/exit-code contract is unchanged
(findings differ only in their `source`/message identifiers) — pure hardening.

### Added

- **`ValidationContext.anchor_corpus()`** (`src/bookwright/validation/base.py`)
  — a memoized, **non-persisting** accessor returning `(engine, anchor_identities)`
  from one in-process `map_research` pass (reusing the memoized `outline()`
  `MapResult`), so an anchor's uuid7 URI and its `AnchorIdentity` come from the
  same build and join coherently. The validator never writes: the corpus calls
  no `engine.save`. A `set_anchor_corpus()` injection seam lets hand-built
  fixtures supply the corpus directly.
- **`anchor_handle(promotes, constrains)`** (`io/_research_identity.py`,
  re-exported from `io/research.py`) — the **single** spelling of an anchor's
  author-facing handle (`promotes -> constrains`, or `promotes` alone when no
  target), called by **both** `commands/status._anchor_line` and
  `factual_anchor`, so the two surfaces name the same anchor byte-identically.
- Oracles — a defective-anchor unit asserts `source == bible/research/<topic>.md`
  (not null) + an authored-handle message with no uuid7 tail; a cross-surface
  test asserts `factual_anchor` and `status` name/locate the same anchor
  identically; the FR-010 join-miss floor still emits (uuid7 label + `source=None`);
  `temporal` a/b/c resolve to the timeline file and are byte-stable across two
  builds; the E2E `test_research_workflow.py` covers the real `graph build` →
  `validate` path (non-null source, no uuid7) and that `validate` never rewrites
  the derived graph.

### Changed

- **`temporal` rules a/b/c** (`validation/validators/temporal.py`) — now resolve
  `source` via `resolve_source` over a deterministically-chosen implicated event
  instead of emitting `source=None`.
- **`factual_anchor`** (`validation/validators/factual_anchor.py`) — resolves
  each violation's `source` to the anchor's research file and names it by the
  shared authored handle; the uuid7/`None` fallback is retained only as a
  defensive floor on an identity join miss.
- **Shared graph-feeding extracted** — `io/bible.feed_graph` is now the single
  triple-assembly both the persisted `graph build` (`commands/_graph`) and the
  in-process validation corpus route through, so the two graphs cannot drift.
- **Contract before code** — `bookwright-design.md` § 13.2 (validator table) and
  § 20.6 record both graph-consumers as resolvable, with the file-only-anchor vs
  `:line`-event granularity stated as **by design**; `bookwright-roadmap.md`
  track-B line reconciled (DEBT-015 closed in iteration 048).

### Removed

- **DEBT-015** (the unactionable locators/identifiers of the graph-consumer
  validators) — resolved and removed from `DEBT.md`; its track-B index
  cross-reference struck through.

## [0.5.6] — 2026-06-24

Iteration **047** — issue #1 **track B** (determinism / polish), closing
**DEBT-016**. With a closed narrative vocabulary active (`[vocabularies] active`,
e.g. `propp`), `graph build` types each authored term — a match gets a
`crm:P2_has_type` edge — but a **non-match was minted as an untyped node in
silence**: no warning, no finding, inconsistent with research (§ 20), which
**rejects** an unknown `type`/`reliability` *fatally* with an enumerated message.
This patch closes that asymmetry **for typing while leaving authoring open**: an
unrecognized Propp `functions:` / Greimas `narrative_roles:` term now emits a
**non-fatal** `graph build` warning enumerating the valid terms of the active
vocabulary; the node is still ingested **unchanged** (untyped, no
`crm:P2_has_type`), and the build **neither aborts nor changes its exit code**.
The governing principle (design § 4.4): **fatal ⇔ an invalid value breaks
downstream logic** — `reliability` poisons the `factual_anchor` gate (fatal); an
absent `P2_has_type` is descriptive metadata that gates nothing (warn only). The
warning rides a new soft channel (`untyped_vocab_terms`), sibling of
`unknown_keys`/`unresolved_references` — additive to the success envelope, never
referenced in `exit_code`. No new CLI verb, no new runtime dependency, no
ontology change (the frozen `golem.ttl`/`propp.ttl`/`greimas.ttl` are untouched),
no new validator and no `Severity` change — pure hardening.

### Added

- **`untyped_vocab_terms` soft channel** (`047`) — `UntypedVocabTerm{path, field,
  term, vocabulary}` (`src/bookwright/io/report.py`), carried by
  `MapResult.untyped_vocab_terms` and copied verbatim into
  `BuildReport.untyped_vocab_terms` (additive `to_json()` key, **not** referenced
  in `exit_code`, default `()` so vocabulary-free builds stay byte-identical).
  Populated at the **two** silent `resolve()→None`-then-mint typing sites — Propp
  `functions:` in `io/outline.py:_mint_functions` (deduped project-wide via
  `functions_index` ⇒ warned once) and Greimas `narrative_roles:` in
  `io/_bible_builders.py:_build_character` (an `else:` on the typing loop, guarded
  by an `EmptySlugError` pre-filter so a blank role mints no node and no warning,
  and deduped per character by slug so a repeated label warns once).
- **`VocabularyIndex.terms`** (`io/vocabularies.py`) — the sorted, deduplicated
  set of every `rdfs:label` (ES + EN), collected in `_index_turtle`; the
  human-render valid-term enumeration is **derived** from it at render time
  (`commands/graph/build.py`, one `valid <vocab> terms: …` line per distinct
  vocabulary), never denormalized into the structured record. Sorting makes the
  enumeration byte-stable regardless of the label store's incidental order.
- Oracles (`tests/commands/graph/test_untyped_vocab.py`,
  `tests/io/test_vocabularies.py`) — Propp typo → one envelope entry (valid term
  untyped → none, bad node lacks `P2_has_type`, exit 0); the human render lists
  the valid terms; Greimas bad role → one `narrative_roles`/`greimas` entry;
  blank role → no warning; a repeated bad role warns once; vocabulary-free build
  → empty channel, byte-identical to pre-feature; two builds byte-identical;
  `terms` sorted / unique / bilingual / stable.

### Changed

- **Contract before code** — `bookwright-design.md` § 4.4 gained the fatal-vs-warning
  principle paragraph and § 13.5 move-3 item 3 was reconciled (planned → delivered
  in iteration 047), ahead of the code diverging. `io/bible.py` threads `relpath`
  + `ctx.result` into `_build_character` via the existing lambda so the Greimas
  site can record warnings.

### Removed

- **DEBT-016** (the silent untyped-mint of unrecognized vocabulary terms) —
  resolved and removed from `DEBT.md`; its track-B index cross-reference struck
  through.

## [0.5.5] — 2026-06-23

Iteration **046** — the **input-file twin of 040/043** (issue #1, track A —
honesty). The 2nd dogfood (`sombra-en-el-puerto`) found that when a bible file
has unusable front-matter (broken YAML), `map_bible` **omits** it
(`MapResult.skipped`) so that entity never enters the graph — and `validate`, the
CI gate, then ran over the **partial corpus silently**: `not_evaluated: []` read
as "everything evaluated" when a whole file had been excluded (DEBT-018, the exact
`[]`-lies-as-clean hole iteration 040 set out to erase, here at the **input-file**
level rather than the validator level). Meanwhile `status` already hard-refused the
same project (`code=skipped_sources`, exit 4) — a `status`↔`validate` asymmetry.
This patch closes it on the `validate` side: after `run_validators(...)`,
`validate` reads the **same memoized** `map_bible` the validators already triggered
(`project.bible().skipped` — no graph rebuild, safe/empty on a missing bible dir)
and merges one `NotEvaluated` entry per skipped file into the **existing**
`not_evaluated[]` channel (040/044) — no new `skipped[]` channel. The entry carries
`validator="ingestion"` (one shared sentinel for the non-validator origin) and
`kind=missing_input`, so the **unchanged** 044 green predicate **degrades green**
automatically. The gate/exit code is untouched (a skip is no `Violation`, so
`report.failed` is identical for the same findings). This release only **consumes**
the 040/044 machinery — the green predicate, `NotEvaluatedKind`/`NotEvaluatedResult`
model, the `not_evaluated[]` serialization and `_KIND_LABEL` render, and `status`
are all unchanged. No new CLI surface, no new runtime dependency, no ontology
change, no validator module touched — pure hardening.

### Added

- **`ingestion` pseudo-source in `not_evaluated[]`** (`046`,
  `src/bookwright/commands/validate.py`, 147 → 167 lines) — each
  `project.bible().skipped` entry becomes a
  `NotEvaluatedResult("ingestion", "bible file '<path>' skipped (unusable
  front-matter): <reason>", NotEvaluatedKind.missing_input)`, merged into the
  existing channel and re-sorted with the shared total-order key. Visible on both
  surfaces (`--json` and the human report's `ingestion [input gap]: …` line);
  `status` still refuses the same project independently — no shared third channel,
  no `status` edit.
- 7 tests (`tests/commands/test_validate_skipped.py`) — surface + degrade-green,
  exit-code parity with the no-skip run, two-skip determinism, both-surfaces
  visibility, `status`↔`validate` agreement, and no-skip byte-identity (the
  tri-valued `_EXPECTED_GAPS` E2E oracle is unchanged).

### Changed

- **`not_evaluated[]` sort promoted to a total order** (`046`,
  `src/bookwright/validation/runner.py`, 82 → 95 lines) — from the partial
  `lambda r: r.validator` (safe only while each validator emitted ≤ 1 entry) to
  `not_evaluated_sort_key → (validator, reason)`, defined **once** (added to
  `__all__`) and imported by both sort sites (runner + the `validate` skip-merge)
  so multi-skip runs (all sharing `validator="ingestion"`) stay byte-identical via
  the unique-path `reason` tie-break. Skip-free runs are unaffected — validator
  names are already unique, so no existing fixture reorders.
- **Contract before code** — `bookwright-design.md` § 13.4 gained the `ingestion`
  pseudo-source paragraph and § 13.5 move-1 was reconciled (skips are now surfaced
  by `validate`, degrading green — not only refused by `status`), ahead of the code
  diverging.

### Removed

- **DEBT-018** (the silent partial-corpus validation, `status`↔`validate`
  asymmetry) — resolved and removed from `DEBT.md`; its track-A cross-reference
  reconciled to past tense. **DEBT-019** (the all-or-nothing `NotEvaluated`
  contract) stays recorded, untouched.

## [0.5.4] — 2026-06-23

Iteration **045** — the **head-hopping twin of 043** (issue #1, track A —
honesty). The 2nd dogfood (`sombra-en-el-puerto`) measured `focalization`'s
deterministic head-hopping check (interiority verbs attributed to a non-focal
bible character under a declared third-person-**limited** voice) as **practically
dormant**: it fires only when a character's **full** bible name sits on the **same
physical line** as the interiority verb, while real prose names characters by
first name / epithet across lines (DEBT-014, a near-total false negative). A
head-hop heuristic without semantic judgment has a precision ceiling, so — exactly
as 043 did with the open-set unknown-mention rule — the rule **stops faking**:
under a parseable limited-third voice the validator now raises `NotEvaluated(…,
kind=pending_capability)` for the **whole run** instead of running the near-null
heuristic, surfacing the permanent gap through the iteration-040 `not_evaluated[]`
channel. The deterministic heuristic is **deleted**, not parked. This release only
**consumes** the 044 machinery — the green predicate, `NotEvaluatedKind`, the
`not_evaluated[]` serialization, the `status` nudge and `_KIND_LABEL` render are
all unchanged. The validator stays a single prose validator (`triples=()`), the
frozen ontology is untouched (Principle X), and no runtime dependency is added.

### Changed

- **`focalization` abstains on head-hopping** (`045`,
  `src/bookwright/validation/validators/focalization.py`, 190 → 159 lines) — under
  a declared third-person-limited / focalized voice, `validate()` raises
  `NotEvaluated("head-hopping / interiority attribution requires semantic judgment
  (move 3); the deterministic heuristic was measured nearly dormant on real
  prose", kind=NotEvaluatedKind.pending_capability)` instead of running the
  deterministic check. A declared third-person **non-limited** voice still runs
  `_first_person_breaks` and stays `evaluated`; a first-person voice still
  evaluates with no findings; the four input-conditional abstentions (no
  constitution, no declared voice, `[PENDING]` placeholder, no grammatical person)
  stay `kind=missing_input` with byte-identical reasons (the 037 `_PENDING_ONLY`
  guard is preserved verbatim).
- **Contract before code** — `bookwright-design.md` § 13.2 (the validator row) and
  § 13.5 now state the whole-validator limited-third abstention plainly, ahead of
  the code diverging.
- **Oracles** — the per-fixture `not_evaluated[]` expectation now carries a
  `focalization` `pending_capability` entry for the third-limited fixtures
  (`tiny-historical`, `tiny-novel`, `tiny-quest`); first-person fixtures
  (`tiny-memoir`, `tiny-essay`) gain none. `tiny-historical` counts stay
  `{error:1, warning:1, info:0}` and its `next_actions` length stays 3 (the
  head-hopping rule emitted nothing on it, so no warning drops).

### Removed

- The dormant head-hopping heuristic and its now-dead support — `_head_hopping`,
  the `_INTERIORITY` matcher, the `_Declaration.focal` field, the focal-name
  computation in `_parse_declaration` (its `character_names` argument is dropped),
  and the orphaned `character_names` computation in `validate` — grep-confirmed to
  have zero external consumers (mirrors 043 deleting its heuristic rather than
  parking it for move 3).
- **DEBT-014** (the dormant head-hopping false negative) — resolved and removed
  from `DEBT.md`.

### Known regression (recorded, not dropped)

- **DEBT-019** — `NotEvaluated` is all-or-nothing, so a limited-third declaration
  abstains the **whole** `focalization` run: the still-working deterministic
  first-person-break check no longer runs for limited-third projects (it still
  runs under non-limited third). The honest fix is a partial-evaluation contract
  or move 3, both 040/044-scale and out of this iteration's scope.

## [0.5.3] — 2026-06-23

Iterations **043 + 044**, released together — the **issue #1 second-dogfood
decision** (track A — honesty). A second end-to-end dogfood (`sombra-en-el-puerto`,
a noir novel) measured `character_presence`'s unknown-mention `warning` rule as
**100 % noise** (4 false positives, 0 real signal) on real prose: telling
«Naviera = organization» / «Las = article» / «Elena = undeclared character» apart
is an **open-set** discovery a capitalization heuristic cannot do soundly — it is
the move-3 (semantic-judgment) case, not a surface bug fixable by another seam
patch or roster. So the open-set heuristic **stops faking**, and the move 3 (LLM
semantic judgment) graduates from a demand-pulled idea to an **activated
direction** (its activation condition — a concrete heuristic measured insufficient
on real prose — is now met), pending its own design pass on determinism in the CI
gate. The prose validators stay graph-free (`triples=()`), the frozen ontology is
untouched (Principle X), no new runtime dependency, and the CI gate (only `error`
fails it) is unchanged.

### Added

- **`character_unknown_mentions` validator** (043,
  `src/bookwright/validation/validators/character_unknown_mentions.py`) — the
  open-set proper-noun rule, made honest: a **pure abstainer** that raises
  `NotEvaluated` unconditionally (reading no project state), surfacing through the
  iteration-040 `not_evaluated[]` channel. The real signal it cannot deliver
  deterministically is the job of move 3.
- **`NotEvaluatedKind` (StrEnum)** (044, `src/bookwright/validation/base.py`) —
  `missing_input` (default — an input-conditional gap the author can fix, e.g. a
  missing voice declaration or empty manuscript) and `pending_capability` (a
  permanent, project-independent gap awaiting move 3). `NotEvaluated`/
  `NotEvaluatedResult` gain a `kind`; the runner stamps it; it is serialized
  additively as `"kind"` in `--json` and `bookwright status`.
- **Automated clean-fixture green guards** (044) — tests asserting `tiny-novel`/
  `tiny-memoir` read green and fire no dormant-validator nudge: the regression
  guard 043 lacked (CI had no test asserting green on a clean fixture).

### Changed

- **`character_presence` split into two auto-discovered validators** (043):
  `character_presence` keeps its name and **only** the orphan rule (`error`,
  byte-identical findings, the `not roster and not files` `NotEvaluated` guard
  preserved — the CI gate is untouched); the unknown-mention rule moves to the new
  abstainer. The entire deterministic heuristic (`_CANDIDATE`, `_is_sentence_initial`,
  `_roster_slugs`, `_unknown_mentions`, the iteration-042 union-roster build) is
  **deleted**, not parked — `character_presence.py` shrank ~223 → 72 lines.
- **Dead-code sweep** (043): the now-zero-consumer iteration-042 accessors
  `ValidationContext.location_names()` / `object_names()` (and their cached fields)
  and the `conftest` `locations=` / `objects=` test knobs are removed.
  `setting_names()` / `settings=` are retained (still consumed by
  `setting_continuity`). **Iteration 043 thus supersedes 042**, whose union-roster
  delta lived entirely inside the deleted unknown-mention path.
- **Refined green predicate** (044): a run is green/clean iff `status == "ok"` AND
  **no `not_evaluated` entry has `kind == "missing_input"`**. A `pending_capability`
  entry stays listed (visible) but no longer denies green — so a flawless project
  reads green again, while the permanent move-3 gap remains surfaced. Documented in
  `bookwright-design.md` § 13.4/§ 13.5.
- **`status` dormant-validator nudge filters on `missing_input`** (044,
  `src/bookwright/status/rules.py`): the `bookwright-continuity` nudge fires only
  for actionable input-conditional gaps; the always-dormant abstainer no longer
  nudges every project. The 043-added `_REMEDIES["character_unknown_mentions"]`
  clause is removed.

### Removed

- **DEBT-011 and DEBT-012** (the leading opening-quote marker and the heading-body
  scan) — **subsumed**, not patched per-instance: both were false positives of the
  unknown-mention rule, which now declares `not_evaluated` instead of emitting
  `warning`. The `io/prose.py` seam is retained for the deterministic validators;
  the per-instance seam patches planned as the old 043/044 are discarded.

## [0.5.2] — 2026-06-22

The second patch of the **v0.5.x post-dogfooding track** (iteration 042),
closing **DEBT-010** — a defect the `tiny-historical` dogfood surfaced, again a
direct continuation of the issue #1 doctrine. The `character_presence` validator
has two rules split by severity: an orphan rule (`error`, protects the gate —
every bible CHARACTER must be mentioned in the prose) and an unknown-mention
rule (`warning` — a prose proper noun with no bible entry). The unknown-mention
rule cross-checked proper-noun candidates against the CHARACTER roster **only**,
so the capitalized tokens of a declared multi-word environment — `Real`,
`Fábrica`, `Paños` of the bible setting "la Real Fábrica de Paños" under
`bible/settings/` — each fired a spurious "no bible entry" `warning`, even
though the entry exists (just under `settings/`, not `characters/`). Per the
issue #1 per-class, no-NER doctrine, the fix widens the rule's known-names set
to the **union** of the character, setting, location and object rosters — **no
validator heuristic is reworked** and **no new disk read is added** (the rosters
ride the already-cached `bible()` map). The `error` orphan gate keeps deriving
from the character roster alone, and the iteration-040 `not-evaluated` guard is
byte-stable. No new CLI surface, no new runtime dependency, no ontology change
(the prose validators stay graph-free, `triples=()`, Principle X) and the CI
gate is unchanged — pure hardening.

### Added

- **Two cached roster accessors on `ValidationContext`**
  (`src/bookwright/validation/base.py`): `location_names()` (GOLEM class
  `NarrativeLocation`, G13, `bible/locations/`) and `object_names()` (GOLEM class
  `Object`, G16, `bible/objects/`), each a byte-for-byte mirror of the existing
  `setting_names()` — the same generic `_names_of(concept_cls)` helper and
  `_UNSET`-sentinel memoization, no new helper.
- **`locations=` / `objects=` knobs on the synthetic-project test builder**
  (`tests/validation/conftest.py`'s `write_project`), mirroring the existing
  `settings=` knob byte-for-byte (both default `()`), so the location/object
  union arms and both new accessors are proven by synthetic projects rather than
  by editing a pinned E2E fixture.

### Changed

- **The `character_presence` unknown-mention rule now suppresses against the
  union of all four bible rosters**
  (`src/bookwright/validation/validators/character_presence.py`): the slug set
  `_unknown_mentions` consumes is built from
  `character_names() + setting_names() + location_names() + object_names()`
  passed once through the unchanged module-level `_roster_slugs`. `_orphans`
  still feeds from `character_names()` alone (the `error` gate untouched), and
  the `NotEvaluated` guard stays clavado on `not roster and not files`
  (character roster only) with the identical reason string. The `Violation`
  shape, `triples=()`, and frozen ontology are untouched.
- **The `tiny-historical` E2E oracle** (`tests/fixtures/tiny-historical/expected-status.md`):
  `validation.counts.warning 4 → 1` — the three setting tokens
  `Real`/`Fábrica`/`Paños` stop being mis-flagged, leaving only the independent
  `factual_anchor` warning; `error` stays `1`. The fixture manuscript and bible
  are untouched (oracle-only shift, the same shape iteration 041 did `5 → 4` and
  038 did `6 → 5`).
- **`DEBT.md`**: the **DEBT-010** entry is removed (resolved). DEBT-011 (the
  genuinely-distinct paired leading-quote markers `«`/`"`/`'`) remains recorded
  for a future iteration — explicitly out of scope here.

## [0.5.1] — 2026-06-22

The first patch of the **v0.5.x post-dogfooding track** (iteration 041),
closing **DEBT-009** — a defect the `tiny-historical` dogfood surfaced and the
direct continuation of the issue #1 doctrine v0.5.0 established. In Spanish
prose a line of dialogue opens with the typographic em dash `—` (U+2014; the en
dash `–` U+2013 and the historical horizontal bar `―` U+2015 are variants),
glued to the first spoken word (`—Esto es el porvenir`). The single prose seam
(`src/bookwright/io/prose.py`, iteration 039) normalized ASCII block markers
(headings, bullets, blockquotes) but **not** the dialogue dash, so
`character_presence` saw `Esto` at a non-zero offset, `_is_sentence_initial`
returned `False`, and the demonstrative was reported as an unbound proper noun —
one spurious `warning` on the first capitalized word of **every** dialogue line,
drowning the real findings. Per the issue #1 doctrine, the class is closed at
the **seam**, never the validator: the fix is one branch in `io/prose.py`'s
existing normalization loop and **no validator file is touched**. No new CLI
surface, no new runtime dependency, no ontology change (the prose validators
stay graph-free, `triples=()`, Principle X) and the CI gate is unchanged — pure
hardening.

### Added

- **A leading-dialogue-dash recognizer in the prose seam**
  (`src/bookwright/io/prose.py`): a new `_DIALOGUE_MARKER`
  (`^\s*[—–―]\s*` — em `—` U+2014, en `–` U+2013, and horizontal bar `―` U+2015,
  all three a single glued, unpaired dash class) joins the heading and
  bullet/blockquote strippers as a third `elif` branch in the existing iterative
  `_normalize` loop (`sub(count=1)`, one pass per marker). The trailing `\s*`
  (not `\s+`, unlike the bullet marker) is load-bearing because Spanish glues the
  dash to the spoken word; a leading typographic dash is unambiguous, so no
  bullet-vs-emphasis guard is needed. Only the **leading** dash is a block
  prefix — internal incise dashes (`—dijo Arnela—`) are content and survive. The
  first spoken word then lands at offset 0 and inherits `character_presence`'s
  existing sentence-initial exemption — the same mechanism iteration 038 (ATX
  headings, DEBT-008) used. No validator file is edited.

### Changed

- `tests/fixtures/tiny-historical/expected-status.md`: the pinned project-wide
  `validation.counts.warning` drops `5 → 4` (the spurious `Esto` flag on the
  first dialogue line is gone), the fixture manuscript untouched — exactly as
  iteration 038 dropped `6 → 5`. `tiny-novel`/`tiny-memoir` carry leading-dash
  dialogue too but their tests assert only `error == 0` (warnings tolerated, no
  pinned count), so they needed no edit.
- `DEBT.md`: the **DEBT-009** entry is removed (git keeps the history). The
  audit recorded **DEBT-011** — the leading paired-quote markers
  (`«`/`"`/`'`), a genuinely distinct *paired* (open…close) design with mid-line
  content and `¿¡`/`_SENTENCE_END` overlap — as a separate future iteration; the
  horizontal bar `―` U+2015, being the same glued dash class **and** design as
  `—`/`–`, was swept here rather than deferred.

## [0.5.0] — 2026-06-22

The **validation-robustness** minor (issue #1), shipping **two** iterations at
once — 039 (single prose/structure seam) and 040 (tri-valued validator result) —
released together at the close of the milestone, the M4→`v0.2.0` /
M5→`v0.3.0` pattern. The v0.4.x post-dogfooding track had patched DEBT-004,
DEBT-007, and DEBT-008 one instance at a time, but the dogfooding made plain they
were **one class** of defect, not three bugs: every prose validator was
re-implementing how to "see past the markdown the tool itself emits," and `[]`
from a validator could not be told apart from "evaluated and clean." Issue #1
decided to close the class at the root rather than keep playing whack-a-mole.
This release closes both facets. No new CLI subcommand and no new runtime
dependency; the `--json` envelope grows **additively** (a new `not_evaluated[]`
array) and the CI gate is unchanged — only `error`-severity findings gate, as
before. The frozen ontology is untouched (Principle X); the prose validators stay
graph-free and LLM-free (`triples=()`).

### Added

- **Single Markdown-aware prose/structure seam** (iteration 039,
  `src/bookwright/io/prose.py`): a generic view that splits a Markdown source into
  lines, classifies block-level prefixes (heading marker, blockquote/bullet),
  and exposes a *normalized view* every prose validator consumes instead of
  re-scanning raw text. It knows only about block-level Markdown — never a
  validator's domain labels. Cached `ValidationContext` accessors
  (`constitution_view()` / `manuscript_view()`) memoize the parse so the three
  prose validators share one pass. This closes the **surface-coupling class**
  behind DEBT-004/007/008 at the root: the per-validator strippers
  (`character_presence`'s `_HEADING_MARKER`, `focalization`'s bullet/emphasis and
  `_PENDING_ONLY` handling, `setting_continuity`'s own scan) are deleted and
  rebuilt on the shared seam.
- **Tri-valued validator result** (iteration 040,
  `src/bookwright/validation/base.py`): a validator's per-run verdict is now
  `evaluated` (with or without findings) vs `not-evaluated(reason)`, so an empty
  result can no longer read as a clean pass when it meant "had nothing to look
  at" — the exact false-confidence bug that kept `focalization` asleep-and-green
  for the whole v0.4 line (DEBT-004). A validator signals not-evaluated by
  **raising a dedicated `NotEvaluated(reason)`** (a plain `Exception`, not a
  `BookwrightError`); the runner — already the per-validator isolation boundary —
  catches it in a clause *before* its generic `except Exception` and records a
  `NotEvaluatedResult(validator, reason)`. `Validator.validate` keeps its return
  type `list[Violation]` **unchanged** — no dual-shape return, no return-type
  sniffing — so a custom validator returning a bare list keeps working as
  evaluated.
- **A `not_evaluated[]` channel** threaded additively through the stack: the
  runner's `RunResult` gains a 4th element (`not_evaluated`, sorted by name); the
  `validate --json` envelope gains a `not_evaluated[]` array (sibling of
  `violations`/`errors`) plus a human "not evaluated:" report section;
  `status`'s `ValidationSummary` gains `not_evaluated` under `state.validation`; a
  new pure `activate_dormant_validators` rule names the remedy in `next_actions`;
  and `resources/commands/bookwright-research.md` lists the raw not-evaluated
  facts at startup. **GREEN is now the single documented predicate
  `status == "ok" AND not_evaluated == []`.**

### Changed

- **The three prose validators are rewritten on the shared seam** (iteration 039,
  `character_presence.py`, `focalization.py`, `setting_continuity.py`): same
  observable findings, but the markdown-normalization logic lives once in `io/`
  instead of being duplicated and drifting per validator.
- **Three validators migrate their "could-not-look" early returns to
  `NotEvaluated`** (iteration 040): `focalization` routes all four early
  "no usable voice" paths to distinct reasons — no constitution, no parseable
  declaration, `[PENDING]` placeholder, and no grammatical person resolved (a
  usable first/third person stays evaluated); `setting_continuity` is
  not-evaluated when the manuscript is empty; `character_presence` is
  not-evaluated **only** when *both* inputs are empty (no prose **and** an empty
  roster) — an empty manuscript with a non-empty roster stays **evaluated** and
  still emits its `error`-level orphan findings byte-for-byte, the rule that keeps
  the gate honest. `temporal` and `factual_anchor` only conform to the
  backward-compatible contract. Every migrated trigger fires only on inputs that
  already returned `[]`, so there are **zero** existing finding-oracle edits.
- **`bookwright-design.md § 13.1`** updated (Spanish) to the tri-valued contract
  before the code diverged.

### Removed

- The per-validator markdown strippers, folded into the `io/prose.py` seam
  (iteration 039) — the surface-coupling class is closed at the root, not patched
  instance-by-instance.

## [0.4.6] — 2026-06-22

Fifth patch of the **v0.4.x post-dogfooding hardening track** (iteration 038) —
pure hardening that makes the `character_presence` validator stop flagging the
first word of a markdown heading as an unknown proper noun, closing DEBT-008.
The proper-noun heuristic exempts a capitalized word that opens a line or follows
sentence-ending punctuation as grammatical, but did not recognize ATX heading
syntax: the first word of `# Capítulo 1` is preceded by the `# ` marker, so
`_is_sentence_initial` saw a non-empty, non-terminal prefix and reported
`proper noun 'Capítulo' appears in the manuscript but has no bible entry` on
every chapter heading — a manuscript that named no off-roster character was told
it had unbound proper nouns. The fix strips a single leading ATX marker before
the heuristic runs, so the heading's first content word lands at offset 0 and is
exempted by the **existing** empty-prefix branch — no new exemption rule. The
rest of the line is analyzed unchanged, so a real out-of-roster name later in the
title (`Elena` in `# La caída de Elena`) still fires. No new CLI surface, no new
runtime dependency, no ontology change, and no `--json` envelope change — pure
hardening on a prose validator (`triples=()`, the frozen ontology untouched,
Principle X).

The `_HEADING_MARKER` recognizer stays local to `character_presence.py` (no
speculative shared markdown-stripping utility), mirroring iteration 037's local
`_PENDING_ONLY`. The marker is anchored at `^` with no leading whitespace, so
`#Capítulo` (no space), seven-or-more `#`, and indented heading-like lines are
out of scope and behave exactly as before. The `relpath:line` locator is
unchanged: `lineno` comes from `enumerate`, never the match offset.

### Changed

- **`character_presence` no longer mis-flags a markdown heading's first word**
  (`src/bookwright/validation/validators/character_presence.py`): a module-level
  `_HEADING_MARKER = re.compile(r"^#{1,6}\s+")` and a `scan = _HEADING_MARKER.sub(
  "", line, count=1)` step in `_unknown_mentions` strip a single leading ATX
  marker before `_CANDIDATE.finditer(scan)` and `_is_sentence_initial(scan, …)`
  run, so the heading-initial word inherits the existing sentence-initial
  exemption. The inverse (bible→manuscript, `error`) direction, the pinned
  `_STOP_WORDS`, per-name collapsing, and the `warning` severity are untouched.
- **`tests/fixtures/tiny-historical/expected-status.md`**: the project-wide
  `warning` count drops `6 → 5`. Its manuscript opens with
  `# Capítulo 1 — El telar nuevo`, and the oracle had baked the spurious
  `Capítulo` flag into its expected output; correcting the validator removes the
  false positive, so the oracle is brought into line (the fixture manuscript is
  not edited).

### Removed

- **DEBT-008** removed from `DEBT.md` (the "Deuda abierta" section returns to
  `_Ninguna por ahora._`) — the v0.4.x post-dogfooding hardening track is
  complete, with no open debt.

## [0.4.5] — 2026-06-21

Fourth patch of the **v0.4.x post-dogfooding hardening track** (iteration 037) —
pure hardening that makes the `focalization` validator treat an unanswered
`[PENDING: …]` narrative-voice placeholder as *no declaration*, closing DEBT-007.
A fresh `bookwright init` constitution carries the prompt
`- **Voz narrativa**: [PENDING: …(primera/tercera persona, omnisciente/limitada)?]`.
That placeholder *text* literally contains "tercera persona" and "limitada", so
`_parse_declaration` parsed it as a real declaration (`person="third",
limited=True`) and the first interiority verb in the manuscript flooded
head-hopping warnings against every character — a project that had answered
*nothing* was told its prose was broken. The fix routes a body that is *solely* an
unanswered `[PENDING]` token into the validator's existing "no declaration → zero
findings" path, so the check stays dormant until the author actually declares a
voice, then wakes exactly as before. No new CLI surface, no new runtime
dependency, no ontology change, and no `--json` envelope change — pure hardening
on a prose validator (`triples=()`, the frozen ontology untouched, Principle X).

The constitution template is deliberately **not** reworded — suppressing the
mis-parse at the parser keeps the `[PENDING: …]` author prompt useful instead of
papering over one template's wording. The recognizer stays local to
`focalization.py` (no speculative shared `[PENDING]` utility);
`references/pending-protocol.md` remains the prose source of truth it mirrors.

### Changed

- **`focalization` no longer mis-reads an unanswered voice placeholder as a
  declaration** (`src/bookwright/validation/validators/focalization.py`): a
  module-level `_PENDING_ONLY = re.compile(r"(?i)^\s*\[pending\b[^\]]*\]\s*$")`
  recognizes a body that is *solely* an unanswered `[PENDING: …]` token, and a
  one-line guard in `_parse_declaration` (after the body is extracted) returns
  `None` for it — reusing the existing no-declaration path. The full `^…$` anchor
  means real text *before or after* the token keeps the body a real declaration
  (FR-002); the check runs on the already markdown-normalized body (iteration
  034), so the bullet/emphasis scaffold form is recognized; recognition is
  case-insensitive and label-agnostic (ES/EN). No other focalization rule
  changed — first-person, interiority/head-hopping, markdown tolerance and focal
  resolution are byte-identical (FR-006).



Third patch of the **v0.4.x post-dogfooding hardening track** (iteration 036) —
pure hardening that makes research-source load errors actionable, closing the last
dogfooding finding (DEBT-006). The dogfooding run hit two blinding error shapes:
an out-of-vocabulary `type:` (or `reliability:`) rejected the value without naming
the accepted alternatives, and a per-source fault (a quoted `access_date`, a
duplicate name) named neither which source in the `sources:` list had failed. This
release enumerates the closed vocabulary in the message and prefixes every
per-source error with a single locator (the source's quoted `name`, or its 1-based
`#index` when the name is absent or unsluggable), with the underlying reason
preserved. No new CLI surface, no new runtime dependency, no ontology change, and
the `--json` error envelope is **byte-unchanged** (`code=invalid_research`,
`details={relpath, value}`) — only the human-readable `message` improves
(Principle IX). The SPARQL empty-result footgun (a query over a misspelled IRI
returns zero rows, not an error) is **documented, not "fixed"** — arbitrary-query
IRI validation is explicitly out of scope.

This release also folds in the **relicense to EUPL-1.2** and the licensing-accuracy
corrections that had accumulated on `main` since `v0.4.3` (previously the
`[Unreleased]` section), so they ship under a tagged version.

### Changed

- **Research-source load errors are now actionable**
  (`src/bookwright/io/research.py`): `_reject_unknown_vocab` enumerates the
  accepted members of the closed vocabulary in the message — `unknown source type
  'x' in <relpath>; one of: primaria, secundaria, oficial, académica,
  periodística, testimonial` and the `reliability` twin (`one of: alta, media,
  baja`). The list is derived from the imported `SOURCE_TYPE_IRI`/`RELIABILITY_IRI`
  maps in declaration order, so it can never drift from the real vocabulary. Each
  per-source fault is wrapped once with a `source '<name>': …` / `source #<n>: …`
  locator prefix (1-based), so the author knows which `sources:` entry failed; the
  duplicate-name and translation-rule messages were de-duplicated so no source is
  named twice (the duplicate retains its `slug` as the semantic subject).
- **Relicensed from Apache-2.0 to EUPL-1.2.** Bookwright is now distributed under
  the European Union Public Licence v. 1.2. `LICENSE` carries the official,
  verbatim EUPL 1.2 text in Spanish and English (Spanish first); `pyproject.toml`
  declares `license = "EUPL-1.2"`; `NOTICE`, the READMEs, the materialized-skill
  default (`DEFAULT_SKILL_LICENSE`) and the design doc were updated to match.
  Third-party licence mentions are unchanged (Spec Kit = MIT, agentskills =
  Apache-2.0).

### Added

- **SPARQL empty-result note** (`src/bookwright/commands/graph/query.py`,
  `docs/commands/graph-query.md`): the `graph query` command help (English) and
  the docs page (Spanish) now warn that a query referencing a non-existent or
  misspelled IRI returns an empty result set, not an error — surfacing the footgun
  without adding IRI validation to arbitrary queries.

### Fixed

- **Licensing-accuracy corrections** surfaced during the relicense audit: the
  redistributed GOLEM ontology was mislabelled Apache-2.0 — it is actually **CC
  BY 4.0** (declared via `dcterms:license` in the ontology itself; the upstream
  repo ships no `LICENSE`), now corrected in `bookwright-design.md` and attributed
  in `NOTICE`. A broken attribution URL in this changelog now points to the real
  preset repo (`adaumann/speckit-preset-fiction-book-writing`).

## [0.4.3] — 2026-06-21

Second patch of the **v0.4.x post-dogfooding hardening track** (iteration 035) —
pure hardening that makes the v0.4 narrative-structure layer queryable by content
and by order. The dogfooding run measured two structural-recall gaps: a
`G9_Narrative_Unit` carried no `rdfs:label`, so its human name lived only in the
URI slug and no SPARQL query could find a beat by name; and a sequence's declared
`order:` was consumed at assembly and never materialized, so under unordered RDF
no query could walk a `G7_Narrative_Sequence` in author order (DEBT-005). This
release emits a single `rdfs:label` on every unit and function (reusing the
`CharacterRole`/`CharacterFeature` one-triple shape, riding the identity
assertion — no new provenance node), and materializes each member's resolved
position as a per-unit `bw:sequenceOrdinal` triple (`xsd:integer`, 1-based
contiguous rank over the already-sorted members, so it is total and gap-free
under missing/duplicate/absent `order:`). No new CLI surface and no new runtime
dependency. The GOLEM ontology stays **frozen** — `bw:sequenceOrdinal` is
declared in `resources/vocabularies/sources.ttl` (the `bw:reference` home),
outside `golem.ttl`/`CLASS_IRI` and the `test_namespaces.py` closure (Principle
X); the graph remains a derived cache reconstructible from the plain-text source
(Principle I).

### Added

- **`G9`/`G10` `rdfs:label` emission**
  (`src/bookwright/golem/modules/narrative.py`): `NarrativeUnit.to_triples()` and
  `NarrativeFunction.to_triples()` each yield one `(uri, rdfs:label,
  Literal(name))` carrying the authored name verbatim (accents/casing preserved),
  so beats and functions are name-queryable. The function is minted once per slug,
  so exactly one label triple exists even when several fiches name it.
- **`bw:sequenceOrdinal` queryable order**
  (`src/bookwright/golem/modules/narrative.py`,
  `src/bookwright/golem/namespaces.py`): `NarrativeSequence.to_triples()` emits a
  per-member `(unit, bw:sequenceOrdinal, Literal(rank, xsd:integer))` triple, and
  `derived_assertions()` reifies each ordinal as its own file-level
  `crm:E13_Attribute_Assignment` (target = unit, attribute = sequence, keyed to
  `order`). A single SPARQL `ORDER BY ?n` now recovers the declared order from the
  graph alone.
- **`bw:sequenceOrdinal` vocabulary declaration**
  (`src/bookwright/resources/vocabularies/sources.ttl`): declared as an
  `rdf:Property` with `rdfs:label`/`rdfs:comment`, outside the frozen GOLEM
  closure.
- **Two demonstrative SPARQL queries as tests**
  (`tests/golem/test_narrative_label_order.py`): Q1 resolves a unit by its
  `rdfs:label`; Q2 lists a sequence's members in declared order via the ordinal,
  proving the query isolates one sequence line. The E2E
  `tests/e2e/test_narrative_workflow.py` `_ordered_members` is rewritten to read
  member order from the graph by `ORDER BY` — overturning its prior "the graph
  carries no member ordinal" assumption — and a new test asserts every unit/
  function label against the `tiny-quest` oracle.

### Changed

- **Term-closure test exempts the one new `bw:` term**
  (`tests/golem/test_triples.py`): the frozen-ontology closure check now exempts
  `bw:sequenceOrdinal` specifically — *not* the whole `bw:` namespace — so any
  other stray `bw:` emission still fails the gate. The `test_namespaces.py`
  closure list is **unmodified** and `golem.ttl`/`CLASS_IRI` are untouched.

### Removed

- **DEBT-005 entry** (`DEBT.md`): the narrative-recall gap is closed and removed
  (git keeps the history); the dogfooding-intro count drops to one entry and
  DEBT-006's cross-reference is repointed to "the narrative-recall gap of
  iteration 035".

## [0.4.2] — 2026-06-21

First patch of the **v0.4.x post-dogfooding hardening track** (iteration 034) —
pure hardening that wakes a validator the toolkit's own scaffold had been
silently disabling. The `focalization` validator anchored its narrative-voice
declaration pattern at line start, so it never matched the
`- **Voz narrativa**: …` shape that `constitution.md.j2` itself emits — leaving
the check dormant on every voice-bearing fixture and on every real project
scaffolded by `bookwright init` (DEBT-004, surfaced by the 2026-06-21 dogfooding
run). This release normalizes the candidate line before matching — stripping one
line-leading bullet/blockquote marker and the emphasis markers around the label —
so the scaffold shape parses byte-identically to the bare form. No new CLI
surface, no new runtime dependency, and the GOLEM ontology stays **frozen** —
this is a prose validator that emits `triples=()` and touches no graph.

### Changed

- **`focalization` tolerates markdown-prefixed voice declarations**
  (`src/bookwright/validation/validators/focalization.py`): a new
  `_normalize_declaration_line` helper strips, per candidate line and each
  independently (no balance guard), one line-leading bullet/blockquote marker
  (`-`/`*`/`+`/`>` + whitespace), then a leading emphasis run, then an emphasis
  run anchored between the label and its colon (`*`/`**`/`_`). The
  person/limited/focal body-extraction is untouched, so `- **Voz narrativa**:
  Tercera persona limitada, centrada en Elena Vidal.` now parses to the same
  `_Declaration(person="third", limited=True, focal="Elena Vidal")` as the bare
  form. The validator is now awake on the scaffold shape (ES + EN).

### Added

- **Template↔parser anti-drift binding test**
  (`tests/validation/test_focalization.py`): a test reads the live
  `constitution.md.j2` voice line and asserts the parser accepts it, so the
  scaffold and the validator can never again silently diverge; plus
  marker-by-marker recognition coverage and the no-false-positive edge cases
  (no declaration / `[PENDING:…]` / mid-sentence label). Suite reconciliation
  confirmed every fixture oracle stays honest: the awakened validator yields
  **0 findings** on `tiny-historical`'s clean third-person prose, so its
  project-wide `validation.counts` stays `{error:1, warning:6}` — read from the
  awake validator, not back-fitted.

### Removed

- **DEBT-004 entry** (`DEBT.md`): the silently-disabled-validator debt is closed
  and removed (git keeps the history); the intro count drops `tres → dos` and
  DEBT-006's cross-reference is repointed from `DEBT-004/005` to `DEBT-005`.

## [0.4.1] — 2026-06-21

First patch on the **v0.4 line** (iteration 033) — pure hardening that removes a
dead concept and closes the structural loophole that let it hide. The top-level
`NarrativeRole` Python concept was unreachable: `G11_Narrative_Role` is
materialized solely by the character-scoped `CharacterRole` carrier (the design
defines G11 as *a character's role*, `bookwright-design.md` line 1603), so the
standalone concept minted nothing yet still counted toward the registry. This
release deletes it and hardens the ingestion-parity contract so a dead concept
that shares a carrier's class IRI can never again be silently counted reachable
(DEBT-001, closed). No new CLI surface, no new runtime dependency, and the GOLEM
ontology stays **frozen** — the 17-class closure is untouched (now 12 concept +
5 carrier IRIs), `golem.ttl` and `golem:G11_Narrative_Role` unchanged, and the
graph emits byte-identical triples.

### Removed

- **Dead `NarrativeRole` concept** (`src/bookwright/golem/modules/narrative.py`
  and its import / `CONCEPTS` entry / `__all__` entry in
  `src/bookwright/golem/__init__.py`): the unreachable standalone concept is
  deleted, dropping `CONCEPTS` from **13 → 12** and the parity reachable set from
  **11 → 10**. G11 continues to be materialized — with identical triples — by the
  `CharacterRole` carrier, which was never in `CONCEPTS`.

### Changed

- **Ingestion-parity contract hardened against carrier-IRI collision**
  (`tests/golem/test_ingestion_parity.py`): `NarrativeRole` joins `CARRIER_NAMES`
  (→ 5), `EXPECTED_REACHABLE` drops to 10, and a new pure `carrier_iri_collisions`
  invariant plus a drift simulation assert that no `CONCEPTS` member may share a
  class IRI with a carrier-only entry — closing the DEBT-001 loophole by
  construction.
- **G11 triple/URI coverage relocated onto the real carrier** (`test_triples.py`,
  `test_uri.py`, `test_namespaces.py`): coverage that referenced the deleted
  concept now exercises `CharacterRole`; `test_namespaces.py` reclassifies the
  G11 IRI from the concept bucket to the carrier bucket (`12 + 5 == 17`), so the
  closure count is preserved, not lowered.
- **Stale "thirteen concepts" counts swept** to "twelve" across live source and
  tests (`golem/__init__.py`, `golem/deferrals.py`, the parity test, the
  `parity-exercise/manifest.toml` header, the `CharacterRole` docstring);
  released `CHANGELOG.md` history is left intact (Principle I).
- **DEBT-001 retired** (`DEBT.md`, `bookwright-roadmap.md` §4): the ledger entry
  is removed and the roadmap decision reconciled to *Resuelto (iteración 033)*.
  The G6/G3 deferrals are untouched.

## [0.4.0] — 2026-06-21

The **narrative-structure layer** (iterations 028–032), shipped once as a minor
release at the close of the milestone — like M4→`v0.2.0` and M5→`v0.3.0`, the
five iterations accumulated on `main` and carry no per-iteration patch tag. This
release brings Propp/Greimas narrative structure (the modelled-but-unfed
`G7`/`G9`/`G10` closure) alive end to end: `outline/units/*.md` now ingests, the
graph assembles narrative sequences from it, the Propp/Greimas vocabularies type
the result, and a new continuity validator consumes the layer. With it the
**ingestion-parity north star is reached** — every authorable concept now has an
ingestion path. No new runtime dependency, and the GOLEM ontology stays
**frozen** (the 17-class closure is untouched; the `G7`/`G9`/`G10`/`G11` classes
already existed — only their ingestion and typing paths are new).

### Added

- **`outline/units/*.md` ingestion → `G9_Narrative_Unit` + `G10_Narrative_Function`**
  (iteration 028, `bookwright-design.md § 7.4`): outline beats now map into the
  graph as narrative units carrying their narrative function, the third ingested
  mirror of the `bible/` pattern after locations (G13) and objects (G16). Takes
  `G9`/`G10` out of the deferral registry's observed-orphan set.
- **`G7_Narrative_Sequence` assembly** (iteration 029): units' optional
  `sequence`/`order` front-matter keys assemble into ordered narrative sequences
  via `dlp:proper-part`, completing the `G7`/`G9`/`G10` ingestion closure.
- **Propp/Greimas vocabularies as `crm:E55_Type`** (iteration 030,
  `resources/vocabularies/propp.ttl` + `greimas.ttl`): 31 Propp functions and 6
  Greimas actants with ES+EN labels. When the manifest's new `[vocabularies]
  active` list turns a vocabulary on, narrative functions (G10) and character
  roles (G11) are typed via `crm:P2_has_type`, the link reified through the
  existing `E13` provenance path — with zero regression when no vocabulary is
  active.
- **`narrative_structure` validator** (iteration 031,
  `src/bookwright/validation/validators/narrative_structure.py`): the first
  *consumer* of the layer — an auto-discovered, `warning`-default, LLM-free check
  with two rules: **orphan beat** (a `G9` unit in no `G7` sequence, via SPARQL
  `NOT EXISTS` over `dlp:proper-part`) and **unresolved role** (re-surfaced from
  outline ingestion's `UnresolvedReference` records). Both findings are cited via
  the existing `E13` provenance path; no ontology change.
- **Narrative-structure E2E + docs** (iteration 032): a source-only
  `tests/fixtures/tiny-quest/` fixture with a co-located oracle (Propp active, a
  deliberate orphan beat and unresolved role), the build→validate E2E
  `tests/e2e/test_narrative_workflow.py`, and the Spanish
  `docs/narrative-structure.md`.

### Changed

- **`ValidationContext.outline()` accessor** (iteration 031): a new cached
  accessor exposes outline ingestion's `UnresolvedReference` records to the
  validation layer, so the `narrative_structure` validator can re-surface
  unresolved roles without re-parsing.
- **G6/G3 deferral re-targeted to `demand-pulled`** (iteration 032,
  `src/bookwright/golem/deferrals.py`, the ingestion-parity parity test's
  `EXPECTED_VERSIONS`, and `DEBT.md`): `RelationshipRole` (G6) and
  `PsychologicalState` (G3), previously stamped target `"v0.4"`, are honestly
  re-pointed at the first-class `"demand-pulled"` sentinel — they ship when an
  activation condition is met, not on a pre-assigned version. The two remain
  observed as orphans by the ingestion-parity build.

## [0.3.4] — 2026-06-15

Fourth and **closing** patch of the **v0.3.x hardening track** (iteration 027).
It ties off the three loose ends the track left behind: the success-envelope
single-sourcing deferred "out of 020's scope", the two "undecided" orphan
verdicts the iteration-024 deferral registry still carried, and the
`UnresolvedParticipant` misnomer iteration 025 explicitly deferred to here.
After this patch the deferral registry holds **zero** `"undecided"` entries,
no `focus`/`graph` command hand-builds a `{"status": "ok", …}` literal, and no
`UnresolvedParticipant` symbol survives in `src/` or `docs/`. No new CLI
surface, no new runtime dependency, no ontology change — pure hardening, with
one **deliberate** public-contract byte change (see *Changed*).

### Added

- **Success-envelope regression suite**
  (`tests/commands/test_success_envelopes.py`): pins the exact stdout bytes of
  every command in the cleanup's scope (`check`, `focus` show/set/clear, `graph
  query`, `graph build`) so any future single-byte drift in a success document
  fails CI.

### Changed

- **Success documents single-sourced** (`src/bookwright/commands/focus/{show,set_,clear}.py`,
  `src/bookwright/commands/graph/query.py`, `src/bookwright/commands/_envelope.py`):
  the `focus` and `graph query` commands now build their success envelope through
  the shared `ok_payload()` helper + `emit_json` instead of a hand-rolled
  `{"status": "ok", …}` dict. Output is **byte-identical** to before — same keys,
  order, compact separators, and trailing newline. `check`'s intentional
  `{"ok": <bool>, "checks": […]}` envelope (no top-level `status`) is left exactly
  as-is.
- **G6/G3 deferral confirmed** (`src/bookwright/golem/deferrals.py`):
  `RelationshipRole` (G6) and `PsychologicalState` (G3), previously stamped
  `"undecided"`, are now firmly deferred to **`v0.4`** with the reason "requires a
  typed roles/states model with attributes and an authoring surface". Neither is
  wired (each carries a mandatory cross-ref and has no `bible/` authoring surface,
  so an identity-only node would be semantically degenerate); both stay observed as
  orphans by the ingestion-parity build. The registry now contains **no**
  `"undecided"` verdict — every remaining entry names a firm reason and a concrete
  target version.
- **`UnresolvedParticipant` → `UnresolvedReference`** (`src/bookwright/io/report.py`,
  `src/bookwright/commands/graph/build.py`, `docs/commands/graph-build.md`): the
  `graph build` soft-warning type — reused since iteration 025 to also surface an
  unresolvable location `setting:`, not just an unmatched `participants:` member —
  is renamed to describe what it actually reports. **This renames the public
  `graph build --json` key `unresolved_participants` → `unresolved_references`** (a
  deliberate `0.x` maintainer-facing contract change): the key's position, its
  `{path, entity, name}` item shape, and every other byte of the envelope are
  unchanged; only that one key string and a new pinned golden baseline differ. The
  stderr summary now reads "N unresolved reference(s)".



Third patch of the **v0.3.x hardening track** (iteration 026). It wires the
second orphaned GOLEM concept into the ingestion pipeline: `bible/objects/*.md`
files — narrative-world objects (a weapon, a relic, a document), ignored
entirely in v0 — now become first-class `G16_Object` nodes, a faithful mirror of
how `bible/settings/` already feeds `G12_Setting`. This shrinks the deferral
registry from six orphans to five and turns the ingestion-parity guard's
reachable set from seven fed concepts to eight. No new CLI surface, no new
runtime dependency, no ontology change (G16 already exists in the frozen
closure, identity-only) — pure hardening.

### Added

- **Object ingestion** (`src/bookwright/io/_bible_builders.py`,
  `src/bookwright/io/bible.py`): the bible mapper now processes
  `bible/objects/*.md` as a one-entity-per-file directory (a sixth `_DirSpec` in
  the existing data-driven loop). Each file builds an `Object` (G16) from `name:`
  front-matter — the identity source, required — exactly as `Setting` does. The
  v0 class is identity-only. Absence of `bible/objects/` changes nothing; a file
  without front-matter is skipped without crashing; a slug collision is rejected
  as in characters/settings.
- **Project scaffold** (`src/bookwright/resources/project/bible/objects/`): the
  `bookwright init` tree now includes `bible/objects/` alongside `settings/` and
  `locations/`.

### Changed

- **`Object` removed from the deferral registry**
  (`src/bookwright/golem/deferrals.py`, 6 → 5 entries); the ingestion-parity test
  (`tests/golem/test_ingestion_parity.py`) now pins eight reachable concepts.
- **`/bookwright-bible` source command** teaches authoring each object as
  `bible/objects/<slug>.md` with `name:` (required) front-matter. The skill
  re-materializes for both `claude` and `generic` integrations with its bilingual
  (ES/EN) triggers preserved.
- Recorded G16 as wired in `bookwright-design.md` § 7.3 and added `bible/objects/`
  to the project-tree diagram (no axiom reopened).

## [0.3.2] — 2026-06-14

Second patch of the **v0.3.x hardening track** (iteration 025). It wires the
first orphaned GOLEM concept into the ingestion pipeline: `bible/locations/*.md`
files — ignored entirely in v0 — now become first-class
`G13_Narrative_Location` nodes, mirroring how `bible/settings/` already feeds
`G12_Setting`. This shrinks the deferral registry from seven orphans to six and
turns the ingestion-parity guard's reachable set from six fed concepts to seven.
No new CLI surface, no new runtime dependency, no ontology change (G13 and
`dlp:generic-location` already exist in the frozen closure) — pure hardening.

### Added

- **Location ingestion** (`src/bookwright/io/_bible_builders.py`,
  `src/bookwright/io/bible.py`): the bible mapper now processes
  `bible/locations/*.md` as a one-entity-per-file directory. Each file builds a
  `NarrativeLocation` (G13) from `name:` front-matter (identity source) plus an
  optional `setting:` that resolves against the sibling settings index and emits
  the already-modelled `dlp:generic-location` cross-ref. An unresolvable
  `setting:` is surfaced through the existing `unresolved_participants` channel
  (no new warning category); the node is still built, the build never aborts.
  Built locations feed the research target index, so a `bears_on:` / `constrains:`
  link to a location now resolves instead of degrading to a soft-miss.

### Changed

- **`io/bible.py` split** (behavior-preserving): the concrete builders, coercers,
  resolution helpers, and the context/result dataclasses moved to the new sibling
  module `src/bookwright/io/_bible_builders.py`, bringing `bible.py` back under the
  500-line Principle IV ceiling (it was exactly at 500). `bible.py` re-exports the
  moved public names, so every `from bookwright.io.bible import …` keeps resolving;
  the existing mapper tests pass unchanged.
- **`NarrativeLocation` removed from the deferral registry**
  (`src/bookwright/golem/deferrals.py`, 7 → 6 entries); the ingestion-parity test
  (`tests/golem/test_ingestion_parity.py`) now pins seven reachable concepts.
- **`/bookwright-bible` source command** teaches authoring each concrete location
  as `bible/locations/<slug>.md` with `name:` (required) and `setting:` (optional)
  front-matter; the "no se indexa en v0" shortcut wording is retired. The skill
  re-materializes for both `claude` and `generic` integrations with its bilingual
  (ES/EN) triggers preserved.
- Recorded G13 as wired in `bookwright-design.md` § 7.2 (the v0 shortcut text is
  retired; no axiom reopened).

## [0.3.1] — 2026-06-13

First patch of the **v0.3.x hardening track** (iteration 024). It makes
*ingestion parity* — the gap between GOLEM concepts that are **modelled** (a
frozen class with a `CLASS_IRI` entry) and those actually **fed** from authored
`bible/*.md` — an explicit, tested contract instead of tribal knowledge. Of the
thirteen `CONCEPTS`, seven have no ingestion path today; this release names them
and guards the set so it can only shrink deliberately. No new CLI surface, no new
runtime dependency, no ontology change — pure hardening.

### Added

- **Deferral registry** (`src/bookwright/golem/deferrals.py`): `DEFERRED_CONCEPTS`,
  a pure-data map of the seven orphaned concepts (`NarrativeLocation`, `Object`,
  `NarrativeUnit`, `NarrativeFunction`, `NarrativeSequence`, `RelationshipRole`,
  `PsychologicalState`) to a `DeferralNote` recording *why* each is unfed and its
  `target_version` (`v0.3.x`, `v0.4`, or `undecided`). The module imports only
  `typing` — no I/O, no `CONCEPTS` import — so the gap is recorded independently of
  the code that fills it.
- **Ingestion-parity guard** (`tests/golem/test_ingestion_parity.py`): derives the
  orphan set from a *real* pipeline build over the new `parity-exercise` fixture and
  asserts it equals exactly `DEFERRED_CONCEPTS`'s keys. Wiring a concept later
  (iteration 025+) means **removing its registry entry**; the test stays green only
  if the registry no longer claims it deferred. Backed by the
  `parity-exercise` bible/manuscript fixture exercising every fed concept.

### Changed

- Documented the parity contract in `docs/authoring.md`; the `manuscript.py`
  reader gained a clarifying docstring (no behavior change).

## [0.3.0] — 2026-06-13

Context-orchestration milestone (M5, design § 21). This release adds the
**hilo conductor** — a three-layer work thread that answers "what am I working on
and what should I do next?" without a hand-written TODO that rots. The layers never
overlap: an **authored** `[focus]` block (your declared intent), a **derived**
`bookwright status` (the project state recomputed from the corpus, with
deterministic `next_actions`), and the **judgment** of the Agent Skills each action
invokes. Like the rest of Bookwright, the plan is a *function* of the plain text:
delete the graph, rebuild, get the same state. The system is **inert** for projects
that don't use it: no `[focus]` and no `bible/research/` means identical v0.2.0
behavior. This entry consolidates iterations 19–23.

### Added

- **Authored focus** (iteration 19): the optional `[focus]` manifest block
  (`target`, `notes`, CLI-stamped `updated_at`) and the `bookwright focus
  set`/`show`/`clear` commands. Plain-text authored state (Principle I); `focus
  set` preserves the rest of the manifest byte-for-byte (comments and order
  included).
- **`bookwright status`** (iteration 20): the derived-state command. Rebuilds the
  graph from the corpus on every run (recomputation *is* the freshness mechanism),
  aggregates the facts (phase, focus, open research questions, under-supported
  anchors, low-reliability findings, validation summary), and maps them through a
  pure, ordered rule table into `next_actions` — each carrying the skill to invoke,
  a paste-ready prompt, and the reason it fired. No LLM, no network: the same corpus
  yields byte-identical output. The rules recommend **per workstream, not per item**,
  so resolving one open question does not shorten the list — only its prompt/reason
  converge.
- **Status-consuming skills** (iterations 21–22): the authoring skills now read
  `bookwright status` at start, anchoring the judgment layer in the derived state
  rather than asking the author to restate it.
- **Orchestration fixture, E2E & docs** (iteration 23): the `tiny-historical`
  fixture extended into a worked orchestration example (a populated `[focus]`, a
  co-located `expected-status.md` oracle, and a pre-baked `_resolution/` answering
  finding outside the corpus dirs); `tests/e2e/test_orchestration_workflow.py`,
  which walks `focus → build → status → resolve → build → status` and asserts
  deterministic **state convergence** plus the inertness/degraded paths; and the
  Spanish `docs/orchestration.md` page wired into the nav. The M4
  `factual_anchor` expectations stay byte-stable (FR-006).

## [0.2.0] — 2026-06-05

Research & verification milestone (M4). This release adds a provenance-backed
research system on top of the v0.1.0 narrative graph: authors can record
external **Sources**, the **Findings** drawn from them, and the **Anchors** that
bind manuscript claims to evidence — all in plain text, all reconstructible into
the graph. Two new Agent Skills drive the loop, a new validator guards anchor
integrity, and an LLM-driven fidelity check flags claims the manuscript can't
support. The system is **inert** for projects that don't use it: no `[research]`
block or `bible/research/` means identical v0.1.0 behavior. This entry
consolidates iterations 12–18.

### Added

- **Research provenance model** (iteration 12): `Source`, `Finding`, and
  `Anchor` GOLEM-adjacent entities serialized through a new `sources.ttl`
  vocabulary (the frozen GOLEM ontology is untouched — Constitution X), with an
  `io/research.py` reader analogous to `bible.py` that maps `bible/research/*.md`
  into entities with `file:line` provenance.
- **`bookwright-research` Agent Skill** + **`[research]` manifest block**
  (iteration 13): the author-facing loop for gathering sources and recording
  findings, plus the `bible/research/` scaffold stamped by `init`. Triggers on
  both ES and EN prompts.
- **`factual_anchor` validator** (iteration 14): a continuity check that flags
  malformed anchors and time-span anachronisms against the graph, wired into the
  same error-only CI gate as the v0.1.0 validators.
- **`bookwright-verify` Agent Skill** (iteration 15): a post-draft LLM fidelity
  check that reads the manuscript against its anchored evidence and reports
  claims the sources don't support.
- **End-to-end research coverage & docs** (iteration 16): the `tiny-historical`
  fixture (a documented mini-novel with real anchors and a deliberate
  anachronism), `tests/e2e/test_research_workflow.py` exercising
  build → query → validate → verify, the Spanish `docs/research.md` page, and
  CHANGELOG/release metadata for this milestone.

### Changed

- **Unified error envelope** (iteration 18): every serializable error across the
  eight origins (`core`, `golem`, `io`, `indexers`, `validation`,
  `commands.validate`, `integrations`, `commands.init`) now subclasses the single
  `BookwrightError` base in `errors.py`, which owns the one canonical `--json`
  envelope (`{status, code, message[, details]}`) and its single `to_json()`.
  Per-class serializers were removed; the base imports nothing from other layers,
  so it sits below them with no cycle (Principle IX).

### Removed

- **Forbidden traceability tags** (iteration 17): purged all `T0xx` task IDs and
  `US-x`/`+USx` user-story tags from `src/` and `tests/` (~57 occurrences across
  ~40 files), converting each to a durable `FR`/`SC`/`D` or `bookwright-design.md
  § N.M` reference or to neutral prose. Added a non-regression test gate
  (`tests/meta/test_no_traceability_tags.py`) that fails CI if any reappear.
  Comments/docstrings only — no logic, signature, or behavior changes.

## [0.1.0] — 2026-06-03

First public release. Bookwright is a spec-driven authoring toolkit that turns a
small set of canonical plain-text documents into a validatable narrative graph.
This entry consolidates iterations 1–11.

### Added

- **CLI** (`typer` + `rich`, Python 3.11+): `bookwright init` (project
  scaffolding with conflict matrix, rollback ledger, and optional git init),
  `bookwright check`, `bookwright version`, `bookwright validate`,
  `bookwright graph build`, `bookwright graph query` (SPARQL over the GOLEM
  graph), and `bookwright integration use` (switch a project's active agent
  integration). Every agent-facing command accepts `--json` and emits a single
  JSON document on stdout (Principle IX).
- **GOLEM domain model** (`rdflib`): characters, settings, narrative events with
  temporal intervals and the five qualitative temporal relations, social
  relationships, and CIDOC-CRM provenance for every derived assertion, serialized
  to Turtle.
- **Graph indexer**: maps the project bible to GOLEM entities and answers SPARQL
  queries with the `golem:` prefix bound.
- **Bible / outline / constitution templates**: the Spanish narrative skeleton
  stamped by `init`, plus re-instanceable molds for the authoring commands.
- **10 authoring commands** materialized as agentskills.io-compliant Agent Skills
  (`bookwright-constitution`, `-bible`, `-outline`, `-synopsis`, `-scenes`,
  `-draft`, `-clarify`, `-analyze`, `-checklist`, `-continuity`).
- **Integrations**: `claude` (`.claude/skills/`) and `generic` (`.agents/skills/`)
  via a plugin registry — no monolithic dispatcher (Principle V).
- **Validation system**: four built-in validators — `character_presence`,
  `focalization`, `setting_continuity`, `temporal` — with an error-only CI gate.
- **Release layer (this iteration)**: three fully-valid fixture projects
  (`tiny-novel`, `tiny-essay`, `tiny-memoir`) under `tests/fixtures/`; an
  in-process E2E suite (`tests/e2e/`) covering the full workflow, skills
  materialization, the integration swap, and docs↔CLI drift; a Spanish MkDocs
  (`material`) documentation site that builds `--strict`; and finalized release
  metadata.

### Changed

- The integration swap is performed by the dedicated `bookwright integration use`
  command. The original plan (re-init with `init --here --force`) was incompatible
  with `init`'s ratified guard that refuses to re-initialize an existing project
  (`.bookwright/` present), so the swap is its own intention-revealing command;
  `init` is unchanged.
- The coverage gate threshold is single-sourced in `[tool.coverage.report]`
  (`fail_under = 80`, `precision = 2`) so it fails closed with no round-up.

### Added — Bible / Outline / Constitution templates

- Authored the real narrative skeleton stamped by `bookwright init`: the
  `bible/` documents (constitution, timeline, relationships, themes, glossary,
  research, subplots, POV structure) and the `outline/` documents (synopsis,
  structure, arcs, scenes), replacing the iteration-4 placeholder stubs. Each is
  Spanish literary-technical prose with HTML-comment craft guidance, worked
  examples inside comments, and `[PENDING: …]` prompts in author-fill sections.
- Authored the re-instanceable molds under `resources/templates/`
  (`character`, `setting`, `location`, `chapter`, `scene`) for the upcoming
  authoring commands (iterations 8–9). The `character` and `setting` molds carry
  frontmatter aligned exactly to the iteration-6 GOLEM mapper's recognized keys,
  so a fresh project indexes with zero skips and zero `unknown_keys`.
- Added a `tests/resources/` format / round-trip validation suite (sentinel
  sweep, frontmatter-contract round-trip via `map_bible`, filled-instance →
  GOLEM entity, Jinja2 `StrictUndefined` render, mold-structure and
  authoring-guidance lint).

### Attribution

- The template **structure** (the document inventory: short + long synopsis,
  themes with a motif registry, locations with sensory anchors, glossary,
  research, subplots, POV structure) is inspired by the
  [`fiction-book-writing`](https://github.com/adaumann/speckit-preset-fiction-book-writing)
  preset by **adaumann** (MIT-licensed), whose license permits structural reuse
  with attribution. Bookwright's redaction is **original** prose under
  **EUPL-1.2**, rewritten in Spanish and adapted to the **GOLEM** narrative
  model — no verbatim preset text is included.

### Changed — supersedes design § 6

- This iteration **supersedes** `bookwright-design.md` § 6's single unified
  `resources/templates/*.tmpl` layout with a four-layer `resolve_template()`
  resolver, in favor of a **lifecycle split**: stamped-once skeleton singletons
  live under `resources/project/` (rendered/byte-copied by the iteration-4
  walker) and re-instanceable molds live under `resources/templates/` (stamped
  many times by commands). The § 6 resolver only ever existed to serve presets
  (v0.2) and extensions (v0.5), which are out of v0 scope; building it now would
  be forbidden plumbing. § 6 is structural guidance, not a § 16 axiom, so the
  divergence is recorded here rather than litigated as a constitutional
  amendment.
