# Phase 0 Research — Validation System

All decisions below are resolved; no `NEEDS CLARIFICATION` remains. Each entry is
Decision / Rationale / Alternatives considered.

## D1 — What structured data each validator can read (and the indexer gap we close)

**Audit finding.** The merged indexer (iteration 6) is **bible-frontmatter-driven**:
`src/bookwright/io/bible.py` maps `Character` (name, born/died years, features,
narrative_roles), `Setting` (name only), `NarrativeEvent` (**name + participants
only**), `SocialRelationship` (name + participants), plus one CIDOC
`E13_Attribute_Assignment` per derived assertion carrying a `relpath[:line]` source
(`crm:P16_used_specific_object`). `src/bookwright/io/manuscript.py` does **no prose
mining**. So the graph contains **no** `follows`/`temporally-overlaps` edges and no
event dates — exactly the signals the clarified `temporal` validator needs.

**Decision (robustness, user-approved).** Close that gap *deliberately and in a
layered way* so `temporal` works on real projects, not just on fixtures:

1. Extend the **timeline frontmatter** (`bible/timeline.md`) so each event may
   declare an optional `date:` (integer year) and `follows:` (list of event names);
   optionally `overlaps:`.
2. Extend the **`NarrativeEvent` GOLEM model + the indexer mapping** to emit, for
   each event: a year literal (closure-safe modelling — see **D11**) and one
   `TemporalRelations.owl#follows` (resp. `temporally-overlaps`) edge per declared
   relation, with the names resolved through the same slug index used for
   participants. Unresolved references become soft warnings, exactly like
   participants.
3. `temporal` stays a **pure graph consumer**: it queries the graph for event-year
   literals and `follows`/`temporally-overlaps` edges. This keeps the layering
   clean (indexer extracts, validator checks) and matches the clarified spec
   literally.

Each validator's source of truth:

| Validator | Primary source | What it reads |
|---|---|---|
| `temporal` | the graph (`bible/graph.ttl`) | per-event year literal + `follows`/`temporally-overlaps` edges (now emitted by the indexer) |
| `character_presence` | bible + manuscript prose | bible character names vs. regex name matches in `manuscript/**.md` |
| `setting_continuity` | bible + manuscript prose | setting names vs. contradicting descriptor terms in prose |
| `focalization` | constitution + manuscript prose | declared person/focus vs. prose POV signals |

**Rationale.** A `temporal` validator that can only fire on a hand-authored test
graph is false confidence — the test goes green while the feature is inert on every
real project. Closing the gap makes the M3 milestone genuinely deliverable
(SC-001/002 reflect reality). The work is small and contained (a few optional
frontmatter keys + their triple emission), reuses the existing participant
resolution and year-literal patterns, and adds no runtime dependency. It is **not**
the "future preset/extension plumbing" the constitution forbids — it completes a
v0 feature.

**Scope/process note.** This touches GOLEM event modelling and the bible timeline
format, which originate in iterations 5–6. We do it under this branch because
iteration 11's clarified spec *requires* those graph signals; the indexer's not
emitting them is a defect relative to this milestone. `/speckit-analyze` should
confirm the cross-artifact consistency. No constitution amendment is needed (no
new dependency, no principle change); the timeline-format addition is backward
compatible (all new keys optional).

**Test consequence.** `temporal` fixtures now exercise the **real pipeline**: a
`timeline.md` with `date:`/`follows:` keys → `graph build` → `validate`. A clean
fixture (consistent dates/order) and a violation fixture (an earlier-dated event
declared to follow a later one, plus a `follows` cycle) prove end-to-end behaviour,
not a fabricated graph.

**Alternatives considered.**
- *`temporal` reads `timeline.md` frontmatter directly (skip the indexer).* Viable
  and self-contained, but duplicates extraction logic in the validator, diverges
  from the clarified "graph-internal" contract, and leaves the graph impoverished
  for any future consumer. Rejected in favour of the layered approach.
- *Keep graph-only + inert-until-future-indexer + fabricated fixtures.* Rejected:
  the false-confidence path the robustness review flagged.

## D2 — Validator discovery mechanism

**Decision.** Built-ins: `pkgutil.iter_modules(validators.__path__)`, import each
module, and collect every module-level object that satisfies the `Validator`
protocol (has `name: str`, `severity_default: Severity`, callable `validate`).
Custom: for each sorted `*.py` under `<project>/.bookwright/validators/`,
`importlib.util.spec_from_file_location` + execute, then collect protocol-conforming
objects. Names must be unique within each tier; a duplicate name is a load error
surfaced (not silently shadowed).

**Rationale.** Package iteration needs no install step and no `pyproject` plumbing,
is fully deterministic, and keeps the subsystem self-contained — matching the
design's "se autodescubren en `bookwright.validation`." Custom validators are
explicitly file-path loaded (they live outside the installed package).

**Alternatives considered.** `importlib.metadata.entry_points` — rejected for v0:
it would require re-installing the package to register a built-in and adds
distribution coupling that the "extension system" milestone (v0.5) owns. The
user's hint allowed either; module iteration is the simpler, in-scope choice.

## D3 — `character_presence` mention detection (no NER)

**Decision.** Roster = character names from `io.bible.map_bible` (cached on the
context). For each manuscript file, strip nothing structurally; run a
word-boundary, case-sensitive-ish regex per roster name (whole-name and, if the
name is multi-token, also its first token as an alias). Two findings:

- **Orphan bible entry** (scenario 3): a roster name with zero manuscript matches →
  violation located at the character's bible file.
- **Unknown manuscript mention** (scenario 2): a *proper-noun candidate* — a run of
  Capitalized tokens (optionally honorific-prefixed) that is **not** sentence-initial
  and does **not** match any roster name (after slug-normalized comparison) — →
  violation located at `file:line` of the first occurrence. Sentence-initial tokens
  and a small built-in stop-set (e.g. weekday/month/"Capítulo") are excluded to
  curb false positives.

**Severity split (robustness, user-approved).** The two directions carry *different*
severities even though the validator's `severity_default` is `error`:

- **orphan bible entry → `error`.** Fully deterministic and reliable; worth gating CI.
- **unknown manuscript mention → `warning`.** This is the heuristic, false-positive-prone
  direction (it can flag places/organisations as if they were characters). At
  `warning` it surfaces in the report and counts toward the summary, but a false
  positive can **never** fail the build (FR-013 gate is error-only). This stays
  spec-compliant: FR-002 allows per-violation severity, and scenario 2 / SC-001 do
  not pin a severity — they require the finding to be *reported*, which it is.

Duplicate mentions of the same candidate collapse to one finding (dedupe, edge case).

**Rationale.** This is "simple name matching, not advanced entity recognition"
(FR-016) and fully deterministic (SC-003). It satisfies scenarios 2 and 3 and the
user's hint ("expresiones regulares simples sobre menciones por nombre").

**Known limits (documented in code + quickstart).** The unknown-mention direction
can false-positive on places/organizations; mitigations are manifest `disabled`,
`--scope`, and (future v0.5) per-project allow-lists. NER, alias/coreference, and
accent-fold beyond slug normalization are out of scope (spec "Out of Scope").

**Alternatives considered.** Pure orphan-only detection (drop scenario 2) — rejected:
SC-001 requires all four kinds to fire. Marker-based mentions in prose — rejected:
no such convention exists in v0 manuscripts.

## D4 — `setting_continuity` contradiction detection

**Decision.** Setting names from `io.bible.map_bible`. Ship a tiny built-in
**contradiction lexicon**: a tuple of antonym groups (each a frozenset of mutually
exclusive descriptor terms, ES+EN), e.g. `{coastal, costera, inland, interior}`,
`{day, día, night, noche}`, `{north, norte, south, sur}`. For each setting, scan
every manuscript file for the setting name and, within the same line/sentence
window, any lexicon term; record `(setting, term, file:line)`. If one setting is
associated with ≥2 terms from the **same** group across **different files**, emit
one warning per conflicting pair citing both source locations.

**Rationale.** Deterministic, no LLM, minimal data; satisfies scenario 4
(coastal/inland across chapters). Warning severity matches the design table and
the spec's "lean toward warnings to avoid false-positive build failures."

**Alternatives considered.** Free-text diffing of descriptions / embeddings —
rejected (nondeterministic, NER-adjacent, out of scope). Requiring a structured
`nature:` field on settings — rejected: would change the bible format (iteration 6
scope) and still need a contradiction lexicon to compare against prose.

## D5 — `focalization` POV detection

**Decision.** Read `paths.constitution` (default `bible/constitution.md`). Locate
the "Voz narrativa" line; classify declared **person** by keyword regex
(primera/segunda/tercera persona; first/second/third person). If exactly one bible
character name appears on that line, treat it as the **focal** character; otherwise
no focal character is set. Manuscript signals:

- **Person mismatch.** When third person is declared, flag first-person subject
  pronouns (`I`, `we`, `yo`, `nosotros/as`) that occur **outside** quotation marks
  (dialogue is stripped before scanning), citing `file:line`.
- **Head-hopping** (third-person *limited* with a focal character). Flag a sentence
  where a **non-focal** bible character name is adjacent to an interiority verb from
  a small built-in set (`thought/felt/knew/realized/wondered`,
  `pensó/sintió/supo/se dio cuenta`), citing `file:line`. The focal character is
  exempt.

Warning severity. If person cannot be classified, only structural signals that
need no person are skipped (the validator yields nothing rather than guessing).

**Rationale.** Deterministic (fixed pronoun + verb sets, quote stripping),
bible-grounded focal resolution, satisfies scenario 5 (revealing another
character's private thoughts under third-limited). No LLM.

**Alternatives considered.** Sentence-level POV modelling / dependency parsing —
rejected (heavy, nondeterministic-prone, out of scope). Parsing arbitrary
free-prose focal declarations — rejected; the bible-name-on-the-voice-line rule is
the deterministic, recall-conservative choice.

## D6 — Source-location resolution from the graph

**Decision.** `queries.resolve_source(indexer, entity_uri) -> str | None` runs a
SPARQL SELECT for the entity's provenance:
`?a crm:P140_assigned_attribute_to <uri> ; crm:P16_used_specific_object ?source`.
Prefer the most specific (line-bearing) source; fall back to the file-level
identity assignment; `None` if the entity has no provenance.

**Rationale.** Provenance is exactly how iteration 6 records `relpath[:line]`
(`AttributeAssignment` in `golem/modules/inference.py`). This lets the graph-only
`temporal` validator attach a real source location to its findings (FR-002/003).

**Alternatives considered.** Carrying source as a separate triple on the event —
rejected; the provenance record already holds it.

## D7 — Configuration resolution & exit codes

**Decision (active-set resolution).** Let `B` = discovered built-in names, `C` =
discovered custom names.
1. If `custom` non-empty, restrict `C` to listed names.
2. `candidates = B ∪ C`, minus any name in `disabled`.
3. If `enabled` non-empty, intersect `candidates` with `enabled`; else keep all.
4. Any name appearing in `enabled`, `disabled`, or `custom` that is **not** in the
   originally discovered `B ∪ C` set → **unknown-validator error** (FR-007).

**Decision (exit codes).** `0` success (no error-severity violation, no config
error); `1` gate fail (≥1 error-severity violation, computed from the **unfiltered**
set per FR-013); `2` config/usage error (no project, invalid/missing manifest,
unknown validator name, scope matching no content). Mirrors the `graph` command's
`EXIT_CONFIG = 2`.

**Rationale.** Satisfies FR-006 (empty `enabled` = all; `disabled` subtracts;
`custom` governs customs), US3 scenarios 1–4, SC-008, and FR-007. The pre-filter
gate satisfies FR-013/SC-006 — a `--severity`/`--scope` filter can never hide an
error from CI.

**Alternatives considered.** `custom` as mere declaration (folder presence alone
activates) with no allow-list — rejected; FR-006 says the custom list *governs*
project-specific validators, so empty=all / non-empty=allow-list mirrors `enabled`.

## D8 — Determinism

**Decision.** Sort discovery output by validator name; iterate manuscript files via
`sorted(glob)`; sort findings by `(validator, source, message)` before emission;
deduplicate byte-identical findings (edge case "duplicate detection"). No use of
set iteration order, dict insertion order across processes, or wall-clock.

**Rationale.** SC-003 (identical findings every run). Required for CI stability.

## D9 — Failure isolation

**Decision.** The runner wraps each validator's `validate()` in try/except; a
raise becomes a `ValidatorError(validator, message)` in the report's `errors[]`,
and the run continues. A custom file that fails to import or exposes no conforming
validator is skipped with an attributed `errors[]` entry. `errors[]` are surfaced
in both human and JSON output but do **not** affect the gate (only error-severity
*violations* do).

**Rationale.** FR-014 + edge cases ("a validator raises", "malformed custom file").
Keeping loader/runtime problems off the gate matches FR-013's strict wording;
documented as a known v0 trade-off.

**Alternatives considered.** Treat a crashed validator as a synthetic
error-severity violation (gating). Rejected: FR-013 ties the gate strictly to
error-severity violations; conflating crashes with findings would surprise CI.

## D10 — Scope semantics

**Decision.** `--scope PATH` is resolved relative to the project root (absolute
paths must fall under it). A violation matches the scope iff its source's file part
equals the scope file or is contained in the scope directory. Location-less
violations are **omitted** under an active scope (clarification). If the scope path
does not exist or is outside the project, the command reports "scope matched no
content" and exits 2 (edge case), rather than silently succeeding.

**Rationale.** FR-009, US2 scenarios 2–3, and the scope edge cases.

## D11 — Closure-safe modelling of the event date (the `P4_has_time-span` problem)

**Audit finding.** GOLEM's frozen ontology (`resources/schemas/golem-1.1/golem.ttl`)
defines `TemporalRelations.owl#follows`, `precedes`, `temporally-overlaps`, and
`temporal-location` — but **not** `crm:P4_has_time-span` (it appears only in a
comment). The term-closure test (`tests/golem/test_namespaces.py`,
`frozen_terms()`) asserts every emitted class/predicate IRI is present in the
frozen ontology, so emitting `crm:P4_has_time-span` would fail CI.

**Decision.** Model the event year with predicates that **are** frozen, reusing the
proven year-literal pattern already used for character `born`/`died`:

- `event  TR:temporal-location  {event.uri}/time-span` (frozen object property,
  semantically "perdurant → temporal region"), and
- `{event.uri}/time-span  crm:P90_has_value  "1885"^^xsd:gYear`
  (`P90_has_value` = the existing `HAS_VALUE` constant; `gyear_literal()` from
  `golem/modules/feature.py` already formats the literal).

`follows` / `temporally-overlaps` are emitted as direct `event → event` edges using
the frozen `TemporalRelations.owl#` predicates. New predicate constants
(`FOLLOWS`, `TEMPORALLY_OVERLAPS`, the temporal namespace) are added to
`golem/namespaces.py` and to the closure test's checked predicate list (they are in
`frozen_terms()`, so the test passes).

`temporal` reads "the gYear reachable from each event via `temporal-location` →
`P90_has_value`," so it is insensitive to the exact carrier node shape.

**Rationale.** Keeps the indexer's output closure-valid (no GOLEM ontology
amendment, honouring axiom X "rdflib/GOLEM frozen"), reuses existing literal
formatting, and gives `temporal` a real, comparable date per event.

**Alternatives considered.** Add `P4_has_time-span` to the ontology — rejected:
the ontology is a vendored, version-pinned external artifact (commit
`f666128a…`); editing it forks GOLEM and breaks the provenance test. Store the year
as a bare literal on the event via an ad-hoc predicate — rejected: any predicate
not in `frozen_terms()` fails the closure test.
