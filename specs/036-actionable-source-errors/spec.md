# Feature Specification: Actionable research-source error messages

**Feature Branch**: `036-actionable-source-errors`

**Created**: 2026-06-21

**Status**: Draft

**Input**: User description: "Necesidad: el dogfooding sobre un libro real expuso mensajes de error en la carga de fuentes de research que ciegan al autor. (F1) `type` fuera del vocabulario cerrado no enumera los valores aceptados. (F2) `access_date` entrecomillado falla sin nombrar QUÉ fuente. Queremos errores accionables: enumerar el vocabulario válido de `type`, e incluir el identificador de la fuente (su `name`, o el índice 1-based) en los errores por-fuente. El footgun de SPARQL se DOCUMENTA. Borrar DEBT-006."

## User Scenarios & Testing *(mandatory)*

This is a developer-experience (authoring-UX) hardening iteration. The "user" is
a **book author** editing `bible/research/sources.md` by hand and running
`bookwright graph build`. When their source list has a mistake, the build aborts
(the research loader is deliberately strict — research fault model D7) and the
error message is the *only* feedback they get. Today two common mistakes produce
error messages that name the symptom but not enough of the cause or location for
the author to act without trial-and-error. This feature makes those messages
self-sufficient.

### User Story 1 - Out-of-vocabulary `type` tells the author the accepted values (Priority: P1)

An author writes a source with `type: primario` (a near-miss for the accepted
`primaria`) — or any value outside the closed vocabulary. The build aborts. The
author needs to know *which values are accepted* without leaving the terminal,
opening the design doc, or grepping the source.

**Why this priority**: It is the most frequent and most blinding of the two
findings — a closed vocabulary is unknowable from the error alone, so the author
iterates by guessing. Enumerating the legal set turns an open-ended guess into a
one-line fix. Independently shippable and independently valuable.

**Independent Test**: Build a project whose `sources.md` declares a source with
an invalid `type`; assert the emitted error message contains every accepted value
of the closed vocabulary.

**Acceptance Scenarios**:

1. **Given** a `sources.md` with a source whose `type` is not in the closed
   vocabulary, **When** the build runs, **Then** it aborts and the error names
   both the offending value and the complete list of accepted values, in a stable
   order.
2. **Given** a `sources.md` with a source whose `reliability` is not in its closed
   vocabulary, **When** the build runs, **Then** it aborts and the error names both
   the offending value and the complete list of accepted reliability values (the
   identical footgun in the same code path — swept in the same iteration).
3. **Given** a valid `type` and `reliability`, **When** the build runs, **Then**
   no vocabulary error is raised (no regression).

---

### User Story 2 - A per-source load error names which source failed (Priority: P1)

An author writes `access_date: "1937-04-26"` (quoted, so YAML hands the loader a
string instead of a native date). The source model rejects it with "Input should
be a valid date". With several sources in the file, the author cannot tell *which
row* to fix. They need the failing source identified by its `name` — or, when the
mistake is in or before the `name` itself, by its position in the list.

**Why this priority**: Without the identifier the message is unactionable in any
file with more than one source — the author must bisect by deleting rows. Adding
the identifier turns a hunt into a direct edit. Equal-priority with US1 because
both are required to call DEBT-006 closed.

**Independent Test**: Build a project whose `sources.md` has two valid sources and
one with a quoted `access_date`; assert the error names the failing source's
identifier (its `name`) and still carries the underlying validation reason.

**Acceptance Scenarios**:

1. **Given** a source with a `name` that fails validation on another field (e.g.
   a quoted `access_date`), **When** the build runs, **Then** the error prepends
   that source's `name` and preserves the underlying reason (which field + why).
2. **Given** a source with **no** usable `name` that fails to load, **When** the
   build runs, **Then** the error prepends the source's 1-based position in the
   `sources:` list so the author can count to the offending row.
3. **Given** a `sources.md` where every source is valid, **When** the build runs,
   **Then** no per-source error is raised (no regression) and the produced
   entities are unchanged.

---

### User Story 3 - The SPARQL empty-result footgun is documented (Priority: P3)

An author (or a skill) runs `bookwright graph query` with a class or predicate IRI
that contains a typo. The query is syntactically valid, so it succeeds and returns
zero rows — indistinguishable from "the data genuinely has no matches". The author
needs a written warning that an unknown IRI yields an empty result, not an error,
so they know to double-check spelling when a query surprises them with nothing.

**Why this priority**: It is a real trap surfaced by the dogfooding run, but —
unlike F1/F2 — the decision is explicitly to **document, not fix** (validating
arbitrary user IRIs against the graph is out of scope). A short documentation note
fully discharges it.

**Independent Test**: Confirm the `graph query` command help text and/or the
project docs contain a note stating that an unknown/misspelled IRI returns zero
rows rather than an error.

**Acceptance Scenarios**:

1. **Given** the `graph query` command help (or the graph/query documentation),
   **When** an author reads it, **Then** it includes a brief note that a query
   referencing a non-existent IRI returns an empty result set, not an error.

---

### Edge Cases

- **`type` is absent vs. invalid**: a *missing* `type` is already caught earlier
  (missing-required-facet); only a *present but out-of-vocabulary* value reaches
  the enumeration path. The enumeration applies to the out-of-vocabulary case.
- **`name` present but empty/unsluggable**: treated as "no usable `name`" → fall
  back to the 1-based index (consistent with US2 scenario 2).
- **Failure before `name` is read** (e.g. the source mapping is missing `name`
  entirely): the 1-based index is the only available locator and MUST be used.
- **Identifier ordering**: the 1-based index counts sources in the order they
  appear in the `sources:` list (the order the loader processes them).
- **Vocabulary enumeration order**: the accepted values are listed in a stable,
  deterministic order so tests and authors see the same sequence every run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When a source declares a `type` outside the closed vocabulary, the
  loader MUST raise an error whose message names the offending value **and**
  enumerates every accepted `type` value.
- **FR-002**: When a source declares a `reliability` outside the closed
  vocabulary, the loader MUST raise an error whose message names the offending
  value **and** enumerates every accepted `reliability` value (same-class sweep:
  the identical footgun lives in the same code path as FR-001 and is fixed in the
  same pass, not deferred).
- **FR-003**: The enumerated accepted values MUST be the author-facing vocabulary
  values (the accented Spanish keys authors type), emitted in a stable,
  deterministic order.
- **FR-004**: Every error raised while loading an **individual** source MUST be
  prefixed with that source's identifier so the author can locate the failing row.
- **FR-005**: The source identifier MUST be the source's `name` when it is a
  present, non-empty, usable string; otherwise it MUST be the source's 1-based
  position within the `sources:` list.
- **FR-006**: The per-source identifier prefix MUST NOT discard the existing
  diagnostic detail — the underlying reason (which field failed and why, e.g. the
  pydantic "Input should be a valid date" message) MUST remain present in the
  message.
- **FR-007**: The error envelope contract MUST be unchanged: errors keep emitting
  the unified `{status, code, message[, details]}` JSON shape (Principle IX,
  iterations 018/027); only the human-readable `message` (and, where already
  present, `details`) content improves. No new error type, code, or field.
- **FR-008**: The `graph query` command's help text and/or the graph/query
  documentation MUST carry a brief note that a query referencing a non-existent
  (e.g. misspelled) IRI returns an empty result set rather than an error.
- **FR-009**: The DEBT-006 entry MUST be removed from `DEBT.md` (git preserves the
  history; resolved debt is deleted, not archived).
- **FR-010**: Test coverage MUST exercise both improved messages: the enumerated
  `type` (F1) and the source-identified per-source failure (F2).

### Key Entities *(include if feature involves data)*

- **Source**: a research source declared in `bible/research/sources.md`
  front-matter. Relevant facets for this feature: `name` (the human identifier),
  `type` (closed vocabulary), `reliability` (closed vocabulary), `access_date`
  (a date that authors sometimes quote by mistake). Its identity for error
  reporting is its `name`, falling back to its 1-based list position.
- **Closed vocabulary**: a fixed, known set of accepted values for `type` and for
  `reliability`. Enumerating it in errors is the core of F1.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An author who mistypes a `type` value sees every accepted value in
  the error and can correct it on the next attempt without consulting any other
  resource (0 external lookups required).
- **SC-002**: An author with a multi-source `sources.md` and one malformed source
  can identify the exact failing source from the error message alone, without
  deleting or bisecting rows.
- **SC-003**: Both improved messages (F1 and F2) are covered by tests that assert
  the new content (accepted-value enumeration; source identifier).
- **SC-004**: The SPARQL empty-result footgun is discoverable from the product
  itself (command help and/or docs) without reading source code.
- **SC-005**: No regression: `uv run pytest` is green, all four gates pass, the
  error JSON envelope contract is byte-compatible (same `status`/`code`/`details`
  keys), and a fully valid `sources.md` produces identical entities to before.
- **SC-006**: `DEBT.md` no longer lists DEBT-006.

## Assumptions

- **Reliability is in scope alongside `type`.** The user need names `type`
  explicitly, but `reliability` is a second closed vocabulary validated by the
  *same* function with the *same* missing-enumeration footgun. Per the project's
  scope discipline (debt of the same class the iteration touches is swept in full,
  not deferred — DEBT.md preamble), both are fixed in this iteration.
- **"Per-source error" means every error raised while validating/building one
  source** in the sources loop (missing required facet, out-of-vocabulary value,
  model validation failure, empty/unsluggable name, duplicate name, translation
  rule), not only the quoted-`access_date` case. The identifier prefix is applied
  uniformly so the locator behaviour is consistent across all source-level faults.
- **The fix is message content only.** No change to the source schema, the closed
  vocabularies themselves, the strict fault model (a bad source still aborts the
  build), the error codes, or the JSON envelope.
- **The quote-specific hint is not required.** F2's underlying cause is "quoted
  date" but detecting and naming *that specific cause* is fragile; preserving the
  native validation reason (FR-006) plus the source identifier (FR-004/005) is
  sufficient to locate and fix the row. No quote-detection heuristic is added.
- **No SPARQL IRI validation.** The `graph query` footgun is documented (FR-008),
  never "fixed" with IRI existence checking against the graph — explicitly out of
  scope per the user need.
- **Ships as `v0.4.4`** (iteration 036, the third v0.4.x post-dogfooding patch),
  consistent with `bookwright-implementation-plan.md` and the CLAUDE.md roadmap.

## Out of Scope *(explicit — do not reopen in clarify)*

- Redesigning the JSON error envelope or the source schema.
- "Fixing" the SPARQL footgun with IRI validation of arbitrary queries (document
  only).
- The other dogfooding findings (DEBT-004 / DEBT-005 — already closed in 034/035).
