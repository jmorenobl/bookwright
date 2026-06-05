# Feature Specification: Traceability Tag Cleanup

**Feature Branch**: `017-traceability-tag-cleanup`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Cancel the traceability-tag debt that CONTRIBUTING.md forbids: remove every `T0xx` (tasks.md task ID) and `US-x` / `USx` / `+USx` (user-story) tag from `src/` and `tests/`, converting real traceability into the equivalent durable reference (the owning iteration's `FR`/`SC`/`D`, or `bookwright-design.md § N.M`) and decorative markers into behaviour-descriptive labels, touching only comments and docstrings, and add a no-regression gate so the debt stays at zero permanently."

## Clarifications

### Session 2026-06-05

- Q: Where should the no-regression gate (FR-010) live — pytest-only, pytest +
  pre-commit, or a ruff custom rule? → A: A single `pytest` test in the suite
  (no pre-commit hook, no ruff rule). It rides `uv run pytest` and CI per
  Principle VIII, is the minimal deliverable, and fully satisfies FR-010 /
  SC-004; pre-commit wiring is left as a trivial future add, out of scope here.

The need otherwise fully specifies the forbidden tag patterns, the conversion
rules, and the comment-only constraint; remaining choices (exact scan command,
failure-message format) are low-impact implementation details for
`/speckit-plan`. Reasonable defaults are recorded under **Assumptions**.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Zero forbidden tags in source and tests (Priority: P1)

A maintainer searches the codebase for the forbidden planning tags and finds
none. `T0xx` (a `T` followed by exactly three digits) and the user-story tags
`US-x` / `USx` / `+USx` no longer appear anywhere under `src/` or `tests/`,
excluding binaries and `__pycache__`. The historical debt — roughly 57
occurrences across ~48 text files (46 `.py` + 2 `.toml` fixtures) inherited
from iterations 1–14 — is gone.

**Why this priority**: This is the headline outcome. Until the count reaches
zero, the debt the iteration exists to cancel is not cancelled. It is the
smallest slice that delivers the promised value and is independently
verifiable with a single search.

**Independent Test**: Run a recursive search for both forbidden patterns over
`src/` and `tests/` (excluding binaries and `__pycache__`) and confirm zero
matches.

**Acceptance Scenarios**:

1. **Given** the cleaned tree, **When** a maintainer searches `src/` and
   `tests/` for `T` followed by three digits, **Then** zero occurrences are
   reported.
2. **Given** the cleaned tree, **When** a maintainer searches `src/` and
   `tests/` for `US-x`, `USx`, or `+USx`, **Then** zero occurrences are
   reported.
3. **Given** the cleaned tree, **When** the search excludes binaries and
   `__pycache__`, **Then** the result is unaffected because no forbidden tag
   survives in any text file either.

---

### User Story 2 - Real traceability preserved as durable references (Priority: P2)

A reader who relied on a removed tag to navigate from code back to its
*why* can still do so. Where a forbidden tag carried genuine traceability, it
has been replaced by the equivalent durable reference rather than simply
deleted, so the "navigate from code to the planning artifact" capability that
CONTRIBUTING.md values is retained — just expressed in the permitted,
non-stale vocabulary.

**Why this priority**: A bulk deletion would reach zero (US1) but destroy
information. Preserving the durable equivalents is what makes the cleanup a
debt *cancellation* rather than a debt *loss*. It depends on US1's removals
but adds the substantive value.

**Independent Test**: For a sample of files that previously carried a
tag justifying a specific fragment, confirm the comment/docstring now cites a
permitted reference (`FR`/`SC`/`D` of the owning iteration, or
`bookwright-design.md § N.M`) that resolves to the same rationale.

**Acceptance Scenarios**:

1. **Given** a `T0xx` that justified a code fragment and maps to a known
   requirement in the owning iteration's spec, **When** the tag is converted,
   **Then** the comment cites that iteration's `FR`/`SC`/`D` (or a design-doc
   section) and no task ID remains.
2. **Given** a tag that paired with already-present durable refs (e.g.
   `(US2, FR-011..FR-016)` or `... SC-009 (T020)`), **When** it is converted,
   **Then** only the forbidden token is stripped and the existing `FR`/`SC`/`D`
   refs are left byte-for-byte intact.
3. **Given** a forbidden tag with no clear durable equivalent, **When** it is
   converted, **Then** it is rewritten to neutral prose that explains the why
   without citing the task or story ID.
4. **Given** a decorative section marker or docstring header that used an ID
   (e.g. `# --- sources.md (US1) ---` or `"""US4 — Acceptance Scenarios ..."""`),
   **When** it is converted, **Then** it becomes a behaviour-descriptive label
   with no ID.

---

### User Story 3 - Permanent zero via a no-regression gate (Priority: P3)

A contributor accidentally adds a `T0xx` or `US-x` tag to `src/` or `tests/`
in a future change. An automated gate, part of the test suite and CI, fails
and points them at the offending location, so the debt cannot silently
return.

**Why this priority**: Without the gate, the count drifts back up over time
and the one-off cleanup is wasted. It is lowest priority only because the
historical debt (US1/US2) must be cleared first — a gate that fails on day one
because the tree is still dirty is not shippable.

**Independent Test**: With the gate in place and the tree clean, the gate
passes; introduce a `T0xx` or `US-x` into a `src/` or `tests/` file and the
gate fails with a message identifying the file and pattern.

**Acceptance Scenarios**:

1. **Given** the cleaned tree, **When** the suite runs, **Then** the
   no-regression gate passes.
2. **Given** a forbidden tag is reintroduced into a `src/` or `tests/` file,
   **When** the suite runs, **Then** the gate fails and identifies the
   offending file (and ideally line/pattern).
3. **Given** the gate runs in CI on every push/PR, **When** a PR reintroduces
   a forbidden tag, **Then** CI blocks the merge.

---

### Edge Cases

- **Tag with no durable equivalent and no real rationale** (pure bookkeeping
  noise, e.g. a bare `(T013)` that adds nothing): the parenthetical is removed
  outright rather than converted — neutral prose is only required when there
  *is* a why worth keeping.
- **Tag embedded in already-durable text**: only the forbidden token is
  excised; surrounding `FR`/`SC`/`D` refs and `bookwright-design.md §` pointers
  are frozen and must not be renumbered or reworded.
- **A file's owning iteration is ambiguous** (a shared helper touched by
  several iterations): the reference resolves to the iteration whose `src/`
  subtree contains the file; if a tag's original rationale belongs to a
  different iteration with no durable equivalent in the owner, it is rewritten
  to neutral prose rather than borrowing another iteration's numbers.
- **Forbidden tag would appear in a non-comment construct** (test name, string
  literal, assertion): none exist today (verified), but were one to, it would
  fall outside the comment-only mandate and must be surfaced rather than
  silently editing code — the cleanup must not change behaviour to satisfy the
  search.
- **The gate's own source or its allowed-examples documentation**: the gate
  definition must not match itself; pattern definitions are arranged so the
  check does not flag the file that implements it.
- **`bookwright-design.md § N` cited with a literal section number that looks
  like a tag**: design-section pointers and prose like "iteration 9" are
  permitted and must not be touched by either the cleanup or the gate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A recursive search of `src/` and `tests/` for `T` followed by
  exactly three digits MUST return zero occurrences (excluding binaries and
  `__pycache__`).
- **FR-002**: A recursive search of `src/` and `tests/` for `US-x`, `USx`, or
  `+USx` (user-story / backlog tags) MUST return zero occurrences (excluding
  binaries and `__pycache__`).
- **FR-003**: Every forbidden tag that carried genuine traceability (it
  justified a specific fragment) MUST be replaced by the equivalent durable
  reference: the `FR`/`SC`/`D` of the **owning iteration's** spec, or
  `bookwright-design.md § N.M`.
- **FR-004**: When a forbidden tag has no clear durable equivalent, it MUST be
  rewritten to neutral prose that explains the rationale without citing the
  task or story ID; when it carried no rationale at all, it MUST simply be
  removed.
- **FR-005**: Decorative section markers and docstring section headers that
  used a forbidden ID MUST be rewritten to a label describing the behaviour or
  content, with the ID removed.
- **FR-006**: Durable references introduced by the conversion MUST resolve
  relative to the file's **owning iteration** — the iteration whose `src/` or
  `tests/` subtree contains the file — using that iteration's spec numbers, not
  another iteration's.
- **FR-007**: Already-merged `FR`/`SC`/`D` references and existing
  `bookwright-design.md §` pointers MUST NOT be renumbered, reworded, or
  otherwise altered; only the forbidden tags are removed or converted.
- **FR-008**: Changes MUST be confined to comments and docstrings — no changes
  to code logic, function or class signatures, test function names, or
  assertions.
- **FR-009**: Observable behaviour and test coverage MUST be unchanged by the
  cleanup (the same tests pass, exercising the same code paths).
- **FR-010**: A no-regression gate, realised as a single `pytest` test in the
  existing suite (no separate pre-commit hook, no ruff rule), MUST fail
  whenever a `T0xx` or `US-x` (per FR-001/FR-002 patterns) reappears in `src/`
  or `tests/`; because it rides `uv run pytest`, it also runs in CI on every
  push/PR (Principle VIII).
- **FR-011**: The gate MUST NOT report a false positive against permitted
  content: legitimate `FR`/`SC`/`D` refs, `bookwright-design.md §` pointers,
  "iteration N" prose, and the gate's own pattern definitions MUST pass.
- **FR-012**: Artifacts under `specs/` (`spec.md`, `plan.md`, `tasks.md`,
  `research.md`, etc.) MUST NOT be modified by the cleanup and MUST NOT be
  scanned by the gate; task and story IDs are legitimate there.

### Key Entities *(include if feature involves data)*

- **Forbidden traceability tag**: a planning-bookkeeping token with no durable
  artifact after merge — `T0xx` (a tasks.md task ID) or `US-x` / `USx` /
  `+USx` (a user-story / backlog tag). The target of removal.
- **Durable reference**: a permitted pointer that survives merge — `FR-0xx` /
  `SC-0xx` (a requirement / success criterion in the owning iteration's spec),
  `D-x` (a decision in that iteration's `research.md`), or
  `bookwright-design.md § N.M`. The replacement vocabulary.
- **Owning iteration**: the single iteration whose `src/` (or `tests/`) subtree
  a given file belongs to; it scopes which spec a bare `FR`/`SC`/`D` number
  resolves against (numbers restart per iteration).
- **No-regression gate**: an automated check, part of the suite and CI, that
  scans `src/` and `tests/` for the forbidden patterns and fails on any match,
  pinning the debt at zero permanently.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A recursive search for the two forbidden tag families over
  `src/` and `tests/` (excluding binaries and `__pycache__`) returns **0**
  matches — down from the inherited ~57 occurrences across ~48 files (`.py`
  plus two `.toml` fixtures).
- **SC-002**: 100% of removed tags that carried real traceability are
  reachable from the same code via a permitted durable reference (no
  navigational information is lost).
- **SC-003**: The full test suite passes with coverage unchanged — at or above
  the existing ≥ 80% threshold — and no test names or assertions differ from
  before the cleanup (behaviour-preserving).
- **SC-004**: The no-regression gate is green on the cleaned tree and turns red
  within the same suite run when a single forbidden tag is introduced into a
  `src/` or `tests/` file.
- **SC-005**: No file under `specs/` is modified by the cleanup, and no
  existing `FR`/`SC`/`D` number anywhere is renumbered.

## Assumptions

- **Gate mechanism** (decided in Clarifications): the no-regression gate is a
  single `pytest` test riding the existing `uv run pytest` suite and CI gate
  (Principle VIII) — not a separate pre-commit hook and not a ruff custom rule.
  Pre-commit wiring is a deliberate out-of-scope future add.
- **Scan surface**: the gate scans text files under `src/` and `tests/`,
  skipping binaries and `__pycache__`; this includes non-`.py` text such as the
  `.toml` fixtures under `tests/` (two of which carry tags today). `specs/`,
  `docs/`, design docs, and the repo root are out of its scope (their
  task/story IDs are legitimate).
- **Pattern definitions**: `T0xx` means `T` immediately followed by exactly
  three digits; the user-story family covers `US-<n>`, `US<n>`, and `+US<n>`.
  The gate encodes these without flagging permitted `FR`/`SC`/`D`/`§` tokens.
- **No code-construct hits**: a pre-check confirmed no forbidden tag currently
  lives in a test name, assertion, or string literal — every occurrence is in
  a comment or docstring — so the comment-only mandate (FR-008) and the
  reach-zero mandate (FR-001/FR-002) do not conflict.
- **Owning-iteration map**: each `src/`/`tests/` subtree maps to one iteration
  per CONTRIBUTING.md; where the original task's rationale has no durable
  equivalent in the owner, neutral prose (FR-004) is used instead of importing
  another iteration's numbers.
- **Scope**: this is a comments/docstrings-and-one-gate change only; no code
  refactor, no `FR`/`SC`/`D` renumbering, and no edits under `specs/`.
