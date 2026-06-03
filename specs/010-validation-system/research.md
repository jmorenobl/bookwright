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
   declare an optional `begin:` / `end:` year (plus a `date:` shorthand for a
   single-year point interval) and any of the five qualitative relation keys
   (`follows:` / `precedes:` / `overlaps:` / `includes:` / `included_in:`, each a
   list of event names).
2. Extend the **`NarrativeEvent` GOLEM model + the indexer mapping** to emit, for
   each event: a closure-safe **time interval** (begin/end boundaries — see **D11**)
   and one `TemporalRelations.owl#` edge per declared qualitative relation, with the
   referenced names resolved through the same slug index used for participants.
   Unresolved references become soft warnings, exactly like participants.
3. `temporal` stays a **pure graph consumer**: it queries the graph for each event's
   begin/end boundaries and the five relation edges (D12). This keeps the layering
   clean (indexer extracts, validator checks) and matches the clarified spec
   literally.

Each validator's source of truth:

| Validator | Primary source | What it reads |
|---|---|---|
| `temporal` | the graph (`bible/graph.ttl`) | per-event begin/end interval boundaries + the five `follows`/`precedes`/`overlaps`/`includes`/`included-in` edges (now emitted by the indexer) |
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
`timeline.md` with `begin:`/`end:` and relation keys → `graph build` → `validate`. A
clean fixture (consistent intervals/order) and violation fixtures covering each of
FR-015's four rules — (a) a `follows` cycle, (b) a pair both ordered and overlapping,
(c) containment conflicting with strict order, (d) numeric begin/end contradicting a
declared relation — plus an open-interval (begin-only) fixture prove end-to-end
behaviour, not a fabricated graph.

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

**Cross-tier collision (built-in wins).** A custom validator whose `name` equals a
built-in's is **not** allowed to override the built-in: the built-in wins, the custom
is skipped with an attributed `ValidatorError(phase="load")` ("custom validator name
'<n>' collides with a built-in; rename it"), and the run continues. Silent override
of an integrated coherence check by project code would erode the determinism
guarantee (FR-019) and surprise CI, so it is reported, never absorbed. This reuses
the same non-fatal "skip with attributed message" path as a malformed custom file.

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
  curb false positives. **Pinned heuristic (so the warning is deterministically
  testable, T021):** a candidate token matches
  `\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\b` (length ≥ 3, accents included), is preceded in the
  sentence by a non-terminal token (i.e. not the first word after `.`/`!`/`?`/
  newline), is not in the built-in stop-set, and does not slug-match any roster name;
  contiguous capitalized tokens (optionally honorific-prefixed) coalesce into one
  candidate. Intentionally conservative — it may miss or over-report, which is
  exactly why the finding is a `warning`, never a gate.

**Severity split (robustness, user-approved).** The two directions carry *different*
severities even though the validator's `severity_default` is `error`:

- **orphan bible entry → `error`.** Fully deterministic and reliable; worth gating CI.
- **unknown manuscript mention → `warning`.** This is the heuristic, false-positive-prone
  direction (it can flag places/organisations as if they were characters). At
  `warning` it surfaces in the report and counts toward the summary, but a false
  positive can **never** fail the build (FR-013 gate is error-only). This stays
  spec-compliant: FR-002 allows per-violation severity, and scenario 2 / SC-001 do
  not pin a severity — they require the finding to be *reported*, which it is.

**Collapse per name (edge case "not multiplied per mention").** Each distinct
unknown candidate name produces **exactly one** unrecognised-mention finding however
many times it occurs; the cited source is the lowest `relpath:line` (first occurrence
in deterministic file/line order). This is stronger than identical-`Violation` dedup
(D8): N mentions of one unknown name on N different lines are N *distinct* findings,
so the validator MUST collapse them by name before emission — otherwise one
missing-from-bible name would flood the report.

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
the declaration line under **either** label (case-insensitive) — the Spanish "Voz
narrativa" **or** the English "Narrative voice" — so an English-authored constitution
is not silently ignored (the project is bilingual by constitution). Classify declared
**person** by keyword regex (primera/segunda/tercera persona; first/second/third
person). If exactly one bible character name appears on that line, treat it as the
**focal** character; otherwise no focal character is set. Manuscript signals:

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

`B` and `C` are **disjoint by construction**: any custom whose name collides with a
built-in was dropped at discovery (D2, built-in wins), so `B ∪ C` has no shadowing
ambiguity and `resolve_active` never has to break a tie.

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

**Decision.** Sort discovery output by validator (module) name; iterate manuscript
files via `sorted(glob)` on the posix relpath; deduplicate byte-identical findings
(edge case "duplicate detection"), **then** sort the surviving findings by the
explicit **total order key** `(validator, _RANK[severity] descending, source or "",
message, triples)` before emission. This key is fully specified — not "stable sort"
left to chance — so `violations[]` is **byte-identical across runs, processes, and
platforms** (SC-003), independent of `dict` insertion order or filesystem order. No
use of set iteration order, dict insertion order across processes, or wall-clock.

**Rationale.** SC-003 (identical findings every run) and SC-004 (a parseable,
shape-stable document) both demand a deterministic, named ordering — a merely
"stable" sort without a pinned key is platform-fragile. Required for CI stability.

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

**Two distinct outcomes — do not conflate.** `empty_scope` (exit 2) is *only* for a
scope path that is **absent or outside the project** (a typo / wrong path — a usage
error). A scope that **resolves to an existing in-project path** but happens to
contain no violations is **not** an error: it exits **0** with an empty report. Both
branches are tested (T032) so a future refactor cannot turn a valid, clean scope into
a false exit 2.

**Rationale.** FR-009, US2 scenarios 2–3, and the scope edge cases.

## D11 — Closure-safe interval-based temporal model (the `P4_has_time-span` problem)

**Audit finding.** The merged indexer emits no temporal signal at all (D1), and the
obvious CIDOC way to attach a date — `crm:P4_has_time-span` and the boundary
predicates `P82a`/`P82b`/`P81`/`P79`/`P80` — is **not** in the vendored frozen
ontology (`resources/schemas/golem-1.1/golem.ttl`): `P4_has_time-span` appears only
in a comment, the others not at all. The term-closure test
(`tests/golem/test_namespaces.py`, `frozen_terms()`) asserts every emitted
class/predicate IRI is a member of the frozen set, so emitting any of them fails CI
and would force a GOLEM fork (axiom X violation, design § 16). Verified against the
ontology on 2026-06-02: every term the model below uses **is** in `frozen_terms()`;
`P4_has_time-span` **is not** (script in the plan's Phase 0 notes).

**Decision (multi-year interval model, all terms frozen).** An event carries a time
**interval** (not a bare year), so it can span several years and support open
intervals (begin-only / end-only). The interval is assembled entirely from frozen
GOLEM / DOLCE-Lite / CIDOC predicates, reusing the proven `Dimension` + `gyear_literal`
year-literal pattern (character `born`/`died`) and the `P2_has_type`-to-shared-`E55_Type`
qualification pattern (biographical feature `birth`/`death`):

| Triple | Frozen term used | Purpose |
|---|---|---|
| `event  CSM:duration  {event}/time-span` | `CommonSenseMapping.owl#duration` (⊑ `TR:temporal-location`, range `time-interval`) | event → its interval; being a sub-property of `temporal-location` it **entails** the spec's "links via `temporal-location`", but is semantically tighter ("event *has duration* this interval") |
| `{event}/time-span  rdf:type  dlp:time-interval` | `DOLCE-Lite.owl#time-interval` | the interval node |
| `{event}/time-span  TR:temporal-location  {event}/time-span/begin` (and `…/end`) | `TR:temporal-location` | interval → up to two child **boundary** nodes; an open interval emits only the boundary it knows |
| `{event}/time-span/begin  rdf:type  dlp:time-interval` | `DOLCE-Lite.owl#time-interval` | each boundary is itself a (degenerate) interval |
| `{event}/time-span/begin  crm:P2_has_type  {uri_base}type/begin` | `crm:P2_has_type` → shared `E55_Type` | **self-labels** the boundary as begin / end — makes open intervals unambiguous |
| `{event}/time-span/begin  crm:P43_has_dimension  {…/begin}/dimension` → `crm:P90_has_value "1885"^^xsd:gYear` | `crm:P43_has_dimension`, `E54_Dimension`, `crm:P90_has_value`, `xsd:gYear` | the boundary's year, via the **exact** `Dimension`/`gyear_literal()` carrier already used for `born`/`died` |

The five **qualitative relations** are emitted as direct `event → event` edges using
the frozen `TemporalRelations.owl#` predicates: `TR:follows`, `TR:precedes`,
`TR:temporally-overlaps`, `TR:temporally-includes`, `TR:temporally-included-in`. New
constants (`FOLLOWS`, `PRECEDES`, `TEMPORALLY_OVERLAPS`, `TEMPORALLY_INCLUDES`,
`TEMPORALLY_INCLUDED_IN`, `TEMPORAL_LOCATION`, `DURATION`, the `TR`/`CSM` namespaces,
and `CLASS_IRI["TimeInterval"] = dlp:time-interval`) are added to `golem/namespaces.py`;
the closure test covers them automatically because each is in `frozen_terms()`.

`temporal` stays a **pure graph consumer**: per event it reads "the `gYear` reachable
from the boundary tagged `type/begin` (resp. `type/end`)" — insensitive to whether
`P90_has_value` sits directly on the boundary or (as here) on its `Dimension`, and to
the exact interval-node shape — plus the five relation edges. This keeps the indexer
as the sole extractor and matches the clarified spec literally.

**Rationale.** Closure-valid (no ontology amendment, honouring axiom X and not
reopening § 16); reuses three existing patterns verbatim (`Dimension`,
`gyear_literal()`, `P2_has_type`→`E55_Type`); supports multi-year and open intervals;
and gives the validator everything FR-015's four contradiction rules (a–d) need —
numeric begin/end boundaries **and** the qualitative relation network.

**Alternatives considered.**
- *`crm:P4_has_time-span` + CIDOC `P82a/P82b` begin/end-of-the-begin literals* — the
  textbook CIDOC modelling, rejected: none of those predicates is in `frozen_terms()`;
  emitting them fails closure and forks the vendored ontology (commit `f666128a…`).
- *A single bare-year literal per event (the prior D11 draft).* Rejected: cannot
  represent a multi-year span or an open interval, and FR-015(d) needs distinct
  begin/end numbers to contradict `includes` / strict-order claims.
- *Untyped begin/end via two ad-hoc predicates on the event.* Rejected: any predicate
  outside `frozen_terms()` fails the closure test; `P2_has_type`-labelled boundaries
  give the same expressiveness with only frozen terms.

## D12 — `temporal` validator: the four contradiction rules over the interval graph

**Decision.** `temporal` loads, for every `NarrativeEvent` in the graph, `(begin, end)`
(either may be `None` — open or absent interval) and the five relation edges, then
emits one `error`-severity `Violation` per detected contradiction (FR-015, uniform
error severity per the 2026-06-02 clarification). The four rules:

- **(a) Order cycle.** Treat `precedes` as the inverse of `follows` and fold both into
  one directed "strict-order" graph (`A follows B` ⇒ edge `B→A` "B before A"); a cycle
  (incl. a 2-cycle `A follows B` ∧ `B follows A`) is a contradiction. Detected by DFS
  with a recursion stack over events sorted by URI (determinism, D8).
- **(b) Order ∧ overlap on one pair.** A pair `(A,B)` asserted **both** a strict order
  (`follows`/`precedes`, either direction) **and** `temporally-overlaps` — mutually
  exclusive claims.
- **(c) Containment vs. strict order.** `A temporally-includes B` (or `B
  temporally-included-in A`) while the same pair also carries `follows`/`precedes` —
  containment and strict succession cannot both hold.
- **(d) Numbers contradict a relation.** Only when both intervals have the needed
  numeric boundaries: `A follows B` but `A.end < B.begin` (A wholly before B, yet
  claims to come after); symmetrically for `precedes`; and `A includes B` whose numbers
  do **not** satisfy `A.begin ≤ B.begin ∧ B.end ≤ A.end`.

Each `Violation` carries a message naming both events and the offending relation/years,
`triples` = the implicated relation edge(s), and `source` resolved from the graph
(D6); cyclic and pairwise findings are graph-wide (`source=None` when no single line
applies). Identical findings are deduplicated (D8). The validator never consults
document order (FR-015) and never reads files directly — it is a pure graph consumer.

**Rationale.** Covers all four FR-015 rules with deterministic graph/number checks
(no LLM, FR-019); uniform `error` matches the clarified default severity; reading
boundaries through the "reachable gYear" abstraction keeps it decoupled from D11's
exact carrier shape.

**Alternatives considered.** Inferring missing relations from numbers (e.g. deriving
`follows` from `A.begin > B.end`) — rejected: the spec asks the validator to detect
*contradictions between declared signals*, not to synthesise an ordering; inferring
edges would invent findings and hurt determinism's intelligibility.

## D13 — Test-discipline: four spec edge cases that need dedicated coverage (Principle VIII)

**Audit finding.** Four behaviours named in the spec's Edge Cases / FRs are currently
covered only incidentally by the per-validator and `--json` tests. Principle VIII
(test discipline, ≥80 %) makes them **explicit, dedicated tests**, each pinned to its
source clause so a regression is caught at the responsible seam:

| # | Behaviour | Spec anchor | Test home | Assertion |
|---|---|---|---|---|
| 1 | **Runner deduplicates identical violations** | Edge "Duplicate detection"; FR-019/SC-003; D8 | `tests/validation/test_runner.py` | a validator that returns the *same* `Violation` twice (and two validators that independently surface the byte-identical finding) collapses to exactly **one** entry in `report.violations`; order is stable |
| 2 | **Project with no `graph.ttl`** | Edge "No graph yet / empty project"; cli-validate behaviour step 2 | `tests/validation/test_command.py` | running in a project that never ran `graph build` exits **0**, reports **zero** graph-sourced (`temporal`) findings, and does **not** error — the indexer loads empty, file-based validators still run |
| 3 | **Composed `--scope` + `--severity`** | Edge "Conflicting severity filter and scope"; FR-009+FR-010; SC-005 | `tests/validation/test_report.py` (+ one command-level integration) | with both filters active the reported set is exactly the **intersection** (scope ∧ severity-threshold); a violation failing *either* is excluded; the **gate/exit code is unchanged** by either filter (FR-013) |
| 4 | **FR-020 — a run writes nothing** | FR-020; "Out of Scope" (no auto-fix) | `tests/validation/test_command.py` | snapshot the project tree (set of paths + mtimes/hashes) before a full `validate` run (human **and** `--json`) and assert it is **byte-identical** afterwards — no file created, modified, or deleted anywhere under the project root |

**Rationale.** These four are the spec's load-bearing guarantees that are easy to
regress silently (a dedupe that stops triggering, an empty-graph crash, a filter that
leaks across the gate, an accidental cache/temp write). Pinning each to a named test
makes the Principle VIII coverage *meaningful*, not just a line-count threshold.

**Alternatives considered.** Folding them into the existing broad `test_command.py`
`--json` test — rejected: a single mega-test hides which guarantee broke and tends to
assert too little about each. One focused test per behaviour keeps failures legible.
