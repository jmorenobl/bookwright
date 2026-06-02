# Feature Specification: Validation System

**Feature Branch**: `010-validation-system`

**Created**: 2026-06-02

**Status**: Draft

**Input**: User description: "Necesidad: la calidad de un libro depende de la coherencia interna. Bookwright debe poder detectar automáticamente inconsistencias temporales, presencia de personajes, continuidad de settings y respeto a la focalización declarada. Los validators son código Python que opera sobre el grafo y son deterministas (a diferencia de los chequeos LLM)."

## Clarifications

### Session 2026-06-02

- Q: What signal does the `temporal` validator use to detect timeline contradictions? → A: Graph-internal consistency only — compare declared event dates/time-spans against the ordering relations the indexer extracted (`follows`, `temporally-overlaps`); flag earlier-dated events asserted to follow later-dated ones, plus cycles in `follows`. Document order is not consulted. *(Reconciliation, plan research D11: the declared event year is modelled in the graph with frozen-ontology predicates — `temporal-location` → `crm:P90_has_value` `xsd:gYear` — because `crm:P4_has_time-span`, named in the original answer, is not present in the vendored GOLEM ontology and would fail the term-closure test. The decision is unchanged; only the concrete predicate differs.)*
- Q: When `--severity` filters the reported output, does it also affect the command's failure signal? → A: No — the `--severity` (and `--scope`) filters affect displayed output only. The failure/exit signal is computed from all violations found before filtering, so any error-severity violation fails the run regardless of the display filter.
- Q: With `--scope` active, are location-less (graph-wide) violations reported? → A: No — `--scope` reports only violations whose source falls within the scope; location-less violations (e.g. `follows` cycles, orphaned bible characters) are omitted under scope and surface only in a full unscoped run.
- Q: Is `--severity` an exact-level filter or a threshold? → A: Threshold (this level and above), ordering error > warning > info. `--severity warning` shows warnings and errors; `--severity error` shows only errors; `--severity info` shows everything.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detect internal inconsistencies on demand (Priority: P1)

An author who has drafted several chapters wants to know whether the book holds
together: that the timeline of events is consistent, that every character who
appears in the manuscript is accounted for in the bible, that settings keep the
same described nature across chapters, and that the declared narrative
point-of-view is respected. They run a single command and receive a clear,
human-readable report listing every inconsistency, where it occurs, which rule
it breaks, and why.

**Why this priority**: This is the core value of the feature. Without the
ability to run the validators and read an actionable report, nothing else
matters. It is the minimum viable slice: a writer can find real coherence
problems and act on them.

**Independent Test**: Take a project whose manuscript/bible/constitution contain
known, deliberately injected inconsistencies (one of each kind). Run the
validate command. Confirm the report names each injected problem with its
location, the rule violated, and a human-readable explanation, and that a clean
project produces no findings.

**Acceptance Scenarios**:

1. **Given** a project where event A is dated 1885 and event B is dated 1884 but
   the manuscript orders B after A as a consequence, **When** the author runs
   validation, **Then** a temporal inconsistency is reported with the conflicting
   events and the source location.
2. **Given** a manuscript that names a character ("Aparici") who has no entry in
   the bible, **When** the author runs validation, **Then** a character-presence
   violation is reported identifying the character and the file/line where it
   was mentioned.
3. **Given** a bible character who is never mentioned anywhere in the manuscript,
   **When** the author runs validation, **Then** a character-presence finding is
   reported identifying the orphaned bible entry.
4. **Given** chapter 3 describes a setting as "a coastal city" and chapter 7
   describes the same setting as "an inland city", **When** the author runs
   validation, **Then** a setting-continuity finding is reported (as a warning)
   citing both source locations.
5. **Given** a constitution declaring "third-person limited, focalized on
   Aparici" and a paragraph that reveals another character's private thoughts,
   **When** the author runs validation, **Then** a focalization finding is
   reported (as a warning) with the offending source location.
6. **Given** a fully consistent project, **When** the author runs validation,
   **Then** the report states that no violations were found.

---

### User Story 2 - Machine-readable results for CI and editors (Priority: P2)

An author (or a CI pipeline, or an IDE integration) needs the validation results
in a form a program can consume, and needs to narrow what gets checked or
reported. They request structured output, limit the check to a single file or
directory, and/or filter results down to a chosen severity.

**Why this priority**: Determinism and structured output are what make these
validators useful beyond a one-off human read — they let the results gate a
merge or surface inline in an editor. It builds directly on US1 but is not
required for a writer to get value manually.

**Independent Test**: Run validation with structured-output mode on a project
with mixed-severity findings; confirm the output is a single valid structured
document with one entry per violation. Re-run scoped to one chapter file and
confirm only that file's findings appear. Re-run filtered to a single severity
and confirm only matching findings appear.

**Acceptance Scenarios**:

1. **Given** a project with violations, **When** the author requests
   machine-readable output, **Then** a single structured document is emitted that
   lists every violation with its validator name, severity, message, source
   location, and the implicated graph relationships, and human progress text
   does not pollute that output stream.
2. **Given** the author limits the scope to one chapter file, **When**
   validation runs, **Then** only violations whose source falls within that file
   are reported.
3. **Given** the author limits the scope to a directory, **When** validation
   runs, **Then** only violations whose source falls within that directory are
   reported.
4. **Given** the author filters to error severity, **When** validation runs,
   **Then** warnings and informational findings are excluded from the report.
5. **Given** a run that found at least one error-severity violation, **When**
   the command finishes, **Then** it signals failure in a way a CI pipeline can
   detect; a run with no error-severity violations signals success.

---

### User Story 3 - Configure and extend which validators run (Priority: P3)

A project lead wants control over which checks apply to their book and the
ability to add project-specific rules. They enable or disable built-in
validators in the project manifest and drop custom validator files into a
project folder, where they are discovered and run alongside the built-ins.

**Why this priority**: Configurability and extensibility increase long-term
value but are not needed for the first useful release; the built-ins with
sensible defaults already deliver the core benefit.

**Independent Test**: Disable one built-in validator in the manifest and confirm
its findings no longer appear. Add a trivial custom validator file to the
project's validators folder and confirm its findings appear in a normal run.

**Acceptance Scenarios**:

1. **Given** the manifest lists only a subset of validators as enabled, **When**
   validation runs, **Then** only those validators execute.
2. **Given** the manifest lists no enabled validators, **When** validation runs,
   **Then** all built-in validators execute (empty enabled list means "all").
3. **Given** a validator is listed as disabled in the manifest, **When**
   validation runs, **Then** that validator does not execute even if otherwise
   enabled.
4. **Given** a custom validator file placed in the project's validators folder,
   **When** validation runs, **Then** that validator is discovered, executed, and
   its findings are reported alongside the built-ins.

---

### Edge Cases

- **No graph yet / empty project**: validation runs against an empty or missing
  graph and reports zero violations rather than failing.
- **A validator raises an error**: one failing validator must not abort the
  whole run; its failure is surfaced as a reportable problem while other
  validators still complete.
- **A custom validator file is malformed** (syntax error, doesn't conform to the
  expected validator shape): it is skipped with a clear, attributed message
  rather than crashing the command.
- **Violation without a precise location** (a finding about the graph as a whole,
  not a specific line): the source location may be absent, and the report still
  states clearly what rule was violated and why.
- **Scope path that matches nothing** (file outside the project, typo): the
  command reports that the scope matched no content rather than silently
  succeeding.
- **Conflicting severity filter and scope**: filters compose — only findings that
  satisfy both the scope and the severity filter are reported.
- **An enabled validator name that doesn't exist**: the command reports the
  unknown validator name clearly rather than silently ignoring it.
- **Duplicate detection**: the same underlying inconsistency should be reported
  once, not multiplied per mention.
- **No parsable narrative-voice declaration**: when the constitution contains no
  narrative-voice / point-of-view declaration the focalization validator can
  parse, the validator reports nothing (zero findings) rather than erroring —
  there is no declared rule to violate.

## Requirements *(mandatory)*

### Functional Requirements

#### Validator contract and findings

- **FR-001**: The system MUST define a single validator contract: a validator
  has a stable name, a default severity, and a means of examining the project
  and its derived graph to produce a list of violations (an empty list meaning
  "no problems found").
- **FR-002**: Each violation MUST carry: the name of the validator that produced
  it, a severity (error, warning, or info), a human-readable message explaining
  what rule was broken and why, a source location (file and, when applicable,
  line) or an explicit indication that no specific location applies, and the
  graph relationships implicated in the finding.
- **FR-003**: The system MUST report every violation with enough information for
  the author to locate and understand it without consulting the validator's
  source code: which file, which line where applicable, which rule, and why.

#### Discovery and configuration

- **FR-004**: The system MUST automatically discover the built-in validators
  without requiring each to be registered by hand.
- **FR-005**: The system MUST discover and load user-supplied custom validators
  placed in the project's designated validators folder, running them alongside
  the built-ins.
- **FR-006**: The system MUST read the project manifest to determine which
  validators are active: an explicit enabled list restricts execution to those
  named; an empty enabled list means all built-in validators run; a disabled
  list suppresses named validators; a custom list governs project-specific
  validators.
- **FR-007**: When configuration names a validator that cannot be found, the
  system MUST report the unknown name clearly rather than silently ignoring it.

#### The validate command

- **FR-008**: The system MUST provide a `validate` command that runs all active
  validators over the project and reports the collected violations.
- **FR-009**: The command MUST support limiting the validated scope to a single
  file or a single directory, reporting only violations whose source location
  falls within that scope. Location-less (graph-wide) violations have no source
  to match and MUST be omitted when a scope is active; they are surfaced only in
  a full, unscoped run.
- **FR-010**: The command MUST support filtering reported violations by severity
  using a threshold (the named level and above), with ordering
  error > warning > info. Thus `--severity warning` reports warnings and errors,
  `--severity error` reports only errors, and `--severity info` reports
  everything.
- **FR-011**: The command MUST support a machine-readable output mode that emits
  a single structured document — and only that document — on the program's
  primary output channel, with all human-oriented progress and prose directed
  to the separate diagnostic channel.
- **FR-012**: In its default (human) mode, the command MUST present the results
  in a readable, grouped form suitable for a writer reading a terminal.
- **FR-013**: The command MUST signal overall failure to its caller when any
  error-severity violation is present, and success when none is, so that a CI
  pipeline can gate on it. Warnings and informational findings alone MUST NOT
  cause a failure signal. The `--severity` and `--scope` filters affect the
  displayed output only; the failure signal MUST be computed from all violations
  found before filtering, so a display filter can never mask an error-severity
  violation from the gate.
- **FR-014**: One validator failing to run MUST NOT prevent the others from
  running or prevent results from being reported; the failure itself MUST be
  surfaced.

#### Built-in validators (v0)

- **FR-015**: The system MUST provide a **temporal** validator (default
  severity: error) that detects contradictions in the timeline of events using
  only the graph — never the physical document order of scenes/chapters — over a
  **multi-year interval model**. An event MAY declare a time interval (a begin
  year and/or an end year, so a single event can span several years) and MAY
  declare qualitative temporal relations to other events: `follows` / `precedes`
  (strict order), `temporally-overlaps` (symmetric co-occurrence), and
  `temporally-includes` / `temporally-included-in` (containment). Over this
  relation network the validator MUST flag:
  - (a) **cycles** in the `follows`/`precedes` strict-order relation;
  - (b) an event asserted to **both** strictly order (`follows`/`precedes`)
    **and** `temporally-overlaps` another event (mutually exclusive claims);
  - (c) **containment conflicting with strict order** — A
    `temporally-includes` B while B also `follows`/`precedes` A;
  - (d) when numeric begin/end years are present on the involved intervals, a
    declared relation that **contradicts the numbers** — e.g. an interval that
    ends earlier asserted to `follow` an interval that begins later, or an
    `includes` relation whose interval does not actually contain the other.
  All temporal predicates this validator relies on — `TR:follows`,
  `TR:precedes`, `TR:temporally-overlaps`,
  `TR:temporally-includes` / `TR:temporally-included-in`,
  `TR:temporal-location`, the DOLCE time-interval, and
  `CommonSenseMapping:duration` — already exist in the vendored, frozen GOLEM
  ontology. No ontology amendment is required and design § 16 is not reopened.
- **FR-016**: The system MUST provide a **character_presence** validator that
  cross-checks characters defined in the bible against characters mentioned in
  the manuscript, reporting both manuscript mentions with no bible entry and
  bible entries never mentioned in the manuscript. Mention detection in v0 is
  simple name matching, not advanced entity recognition. Per FR-002 (per-violation
  severity), this validator MUST emit its two finding kinds at **different**
  severities: the deterministic **orphan-in-bible** finding (a bible entry never
  mentioned in the manuscript) at **error** so it gates CI, and the heuristic
  **unrecognised-mention** finding (a manuscript name with no bible entry,
  derived from fuzzy name matching) at **warning** — because a false positive
  from name matching MUST never fail the build.
- **FR-017**: The system MUST provide a **setting_continuity** validator (default
  severity: warning) that detects contradictory descriptions of the same setting
  across different files, citing the conflicting source locations.
- **FR-018**: The system MUST provide a **focalization** validator (default
  severity: warning) that detects passages violating the narrative
  person/point-of-view declared in the project's constitution, citing the
  offending source location.

#### Boundaries

- **FR-019**: The validators MUST be deterministic: the same project state always
  produces the same findings. No validator in this feature may rely on a language
  model or other nondeterministic judgment.
- **FR-020**: The system MUST NOT attempt to automatically fix any violation; it
  only reports.

### Key Entities *(include if feature involves data)*

- **Validator**: A named, deterministic check with a default severity. Examines
  the project and its graph and yields zero or more violations. May be built-in
  or user-supplied.
- **Violation**: A single reported problem — originating validator, severity,
  human-readable message, optional source location (file and line), and the
  implicated graph relationships.
- **Severity**: One of error, warning, or info; governs both how a finding is
  presented and whether it can cause an overall failure signal.
- **Validator configuration**: The manifest-driven settings (enabled, disabled,
  and custom lists) that determine which validators run for a given project.
- **Validation report**: The aggregate result of a run — the set of violations
  after scope and severity filtering — rendered either for a human reader or as a
  single structured document.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a reference project seeded with one deliberately injected
  inconsistency of each of the four kinds, a validation run reports all four,
  each with a correct source location and an explanation of the rule violated.
- **SC-002**: On a fully consistent reference project, a validation run reports
  zero violations and signals success.
- **SC-003**: Re-running validation on an unchanged project produces identical
  findings every time (deterministic).
- **SC-004**: The machine-readable output is a single, parseable structured
  document containing exactly one entry per reported violation, with no
  non-structured text mixed into that output channel.
- **SC-005**: Limiting scope to a single chapter reduces the reported findings to
  only those originating in that chapter; filtering to error severity excludes all
  warnings and informational findings.
- **SC-006**: A run containing at least one error-severity violation signals
  failure to its caller, and a run with only warnings/info signals success,
  allowing a CI pipeline to gate on it without parsing prose.
- **SC-007**: A user can add a custom validator to the project's validators folder
  and see its findings in the next run without modifying any built-in code; a
  malformed custom validator is skipped with an attributed message and does not
  crash the run.
- **SC-008**: Disabling a built-in validator in the manifest removes its findings
  from the report on the next run.

## Assumptions

- **Severity filter semantics**: `--severity X` is a threshold — it reports
  violations at level X and above (error > warning > info), per Clarifications
  2026-06-02. It affects displayed output only, never the failure signal.
- **Default severities**: temporal defaults to error; setting_continuity and
  focalization default to warning, per the design's built-in table (§ 13.2).
  setting_continuity and focalization are heuristic and intentionally lean toward
  warnings to avoid false-positive build failures. character_presence is split
  per finding kind (FR-016, exercising the per-violation severity allowed by
  FR-002): its deterministic orphan-in-bible finding is an error (gates CI) while
  its heuristic unrecognised-mention finding is a warning, so a name-matching
  false positive never fails the build.
- **Empty enabled list means all**: an empty `enabled` list in the manifest
  activates all built-in validators, matching the manifest comment in the design.
- **Mention extraction is name-based**: character_presence uses simple name
  matching in v0; no advanced entity recognition, accent/alias normalization
  beyond basic matching, or coreference resolution is in scope.
- **Custom validators are trusted code**: user-supplied validator files run with
  the same trust as project code; sandboxing untrusted validators is out of scope.
- **Graph is the source of structured truth**: validators read the
  already-built project graph and the project's text/config files; building or
  refreshing the graph is the responsibility of the existing indexer, not this
  feature. **Bounded exception**: so the `temporal` validator has data to
  consume, this feature extends the existing **timeline indexer** to recognise
  optional keys in `bible/timeline.md` (per-event begin/end years → time
  intervals, and qualitative temporal relations → temporal edges in the graph).
  This is a narrow, additive extension of one indexer path; general
  graph-building remains the indexer's responsibility and is otherwise untouched.
- **Relationship to LLM continuity checks**: the deterministic validators here
  are distinct from the LLM-based continuity review available through the
  `bookwright-continuity` authoring command; that command may invoke this
  feature's command, but the LLM checks themselves are out of scope here.

## Out of Scope

- LLM-based or otherwise nondeterministic validators (these exist separately via
  the `bookwright-continuity` authoring command).
- Automatic fixing of any reported violation.
- Advanced natural-language entity recognition, alias/coreference resolution for
  character matching.
- Sandboxing or trust isolation of user-supplied custom validators.
- Building or refreshing the graph index (owned by the indexer feature) — with
  one **bounded exception**: this feature extends the timeline indexer to read
  optional `bible/timeline.md` keys into time intervals and qualitative temporal
  edges, giving the `temporal` validator data to consume (see the "Graph is the
  source of structured truth" assumption). General graph-building stays out of
  scope and remains the indexer's responsibility.
