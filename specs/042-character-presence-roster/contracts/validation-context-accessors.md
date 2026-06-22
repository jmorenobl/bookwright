# Contract: `ValidationContext` roster accessors + union cross-check

The CLI surface is unchanged; the contracts here are the **internal seams** this iteration
adds/relies on. They are exercised by the synthetic-project tests (FR-015) and the
`tiny-historical` E2E (FR-012).

## C1 — `ValidationContext.location_names()`

```python
def location_names(self) -> tuple[tuple[str, str], ...]: ...
```

- **Returns**: sorted `(name, bible_relpath)` pairs for every bible entity that is an
  instance of `NarrativeLocation` (mapped from `bible/locations/`, G13).
- **Empty**: returns `()` when `bible/locations/` is absent or empty.
- **Memoized**: computed once per `ValidationContext` via a private `_UNSET`-sentinel field;
  shares the cached `bible()` map (no extra disk read).
- **Mirror invariant**: byte-for-byte the `setting_names()` body with `Setting` →
  `NarrativeLocation`; resolved through the existing `_names_of(concept_cls)` — no new helper.

## C2 — `ValidationContext.object_names()`

```python
def object_names(self) -> tuple[tuple[str, str], ...]: ...
```

- Identical to C1 with `NarrativeLocation` → `Object` (mapped from `bible/objects/`, G16).

## C3 — Union suppression in `character_presence`

- The unknown-mention rule's suppression set is built from
  `character_names() + setting_names() + location_names() + object_names()` via the
  unchanged `_roster_slugs`.
- A proper-noun candidate whose slug (full name **or** any token) is in that union MUST NOT
  be reported (FR-003). Specifically `Real`, `Fábrica`, `Paños` (tokens of the declared
  setting "la Real Fábrica de Paños") MUST stop being reported.
- A candidate whose slug is in **none** of the four rosters (and not stopped/sentence-initial)
  MUST still be reported as exactly one `warning` citing its first occurrence (FR-005).
- The `_orphans` (`error`) rule MUST keep deriving from `character_names()` only (FR-004).
- The `NotEvaluated` guard and reason string MUST be unchanged (FR-007).
- The `Violation` shape and `triples=()` MUST be unchanged (FR-005/FR-008/FR-009).

## C4 — `write_project` test-scaffold extension (test contract)

```python
def write_project(root, *, ..., settings=(), locations=(), objects=(), ...) -> Path: ...
```

- `locations` / `objects` are name iterables; each writes one
  `bible/<locations|objects>/<slug>.md` card (`---\nname: "<name>"\n---\n`), byte-for-byte
  mirroring the existing `settings` knob.
- Both default to `()`, so every existing caller builds a byte-identical project (FR-011).

## Out of contract

- No `--json` envelope, report, `status`, or `next_actions` shape changes — only which
  warnings are emitted on a project with declared environments.
- No GOLEM class, `.ttl`, or graph-build contract changes (FR-010).
