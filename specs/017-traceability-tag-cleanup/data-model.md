# Data Model: Traceability Tag Cleanup

This iteration adds no persisted data, no Pydantic model, and no graph
vocabulary. The "entities" below are conceptual — the categories the work
operates over — kept here so `/speckit-tasks` and `/speckit-analyze` have a
stable vocabulary.

## Forbidden traceability tag

A planning-bookkeeping token with **no durable artifact after merge**. Two
families, defined by regex (the single source of truth, shared verbatim by the
sweep, the spec, and the gate):

```
\bT0[0-9]{2}\b      # task ID from tasks.md — T followed by exactly 3 digits
\bUS-?[0-9]+\b      # user-story tag — US-3, US3
\+US[0-9]+          # backlog tag — +US3
```

The target of removal. Lives only in comments/docstrings under `src/`+`tests/`.

## Durable reference

A permitted pointer that survives merge and MUST NOT be altered (FR-007):

- `FR-0xx` / `SC-0xx` — requirement / success criterion in the **owning
  iteration's** `specs/NNN-*/spec.md`.
- `D-x` — a recorded decision in that iteration's `research.md`.
- `bookwright-design.md § N.M` — a section of the global design doc.

The replacement vocabulary. Note these never trip the gate regex (verified —
see research D3).

## Owning iteration

The single iteration whose `src/` (or `tests/`) subtree contains a file
(CONTRIBUTING.md rule 1). Scopes which spec a bare `FR`/`SC`/`D` resolves
against, since numbering restarts per iteration. Used only to validate that an
already-present ref belongs to its file's owner; no number is ever borrowed
across iterations (FR-006).

## Edit class (the transform applied per hit)

A closed set of four — see research.md D1:

| Class | Transform |
|---|---|
| strip-token | delete forbidden token + orphaned punctuation; freeze surrounding durable refs |
| relabel | rewrite a decorative marker/header to a behaviour-descriptive label, ID gone |
| remove | delete a bare bookkeeping parenthetical; keep self-describing prose |
| neutral-prose | rewrite a why-bearing comment to prose with no ID |

**Invariant**: every edit touches only `#` comment text or `"""docstring"""`
text. `git diff` after each file confirms no code/signature/name/assertion
line changed (FR-008, FR-009).

## No-regression gate

An automated check (`tests/meta/test_no_traceability_tags.py`), part of the
suite and CI, that scans `src/`+`tests/` for the forbidden patterns and fails
on any match. State: **green** on the cleaned tree; **red** the moment a tag
reappears. Its full behaviour is specified in
[contracts/no-regression-gate.md](contracts/no-regression-gate.md).
