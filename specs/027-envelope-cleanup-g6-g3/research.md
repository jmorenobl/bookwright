# Phase 0 Research: envelope cleanup + G6/G3 decision

All major decisions were fixed in the spec (Clarifications + Assumptions); this
file records the *technical* resolutions needed to implement them without
NEEDS CLARIFICATION. No open questions remain.

## D1 — How `ok_payload` is wired today (the pattern to mirror)

**Decision**: Mirror `commands/status.py` exactly. It imports `ok_payload`,
`render_json`, `emit_json` from `._envelope`, builds `payload = ok_payload(**fields)`,
and emits via `emit_json(payload)` (or `render_json` when it also writes a cache).

**Rationale**: `ok_payload(**fields)` returns `{"status": "ok", **fields}`. Python
dict literals and `**`-expansion both preserve insertion order, and `emit_json`
already uses `json.dumps(payload, separators=(",", ":")) + "\n"`. So
`emit_json({"status": "ok", "focus": x})` and
`emit_json(ok_payload(focus=x))` produce **the same bytes** — `"status"` first,
then the passed fields in call order. This is what makes US1 byte-identical by
construction, not by luck.

**Alternatives considered**: Introducing a per-command typed envelope model
(rejected — overkill, risks reordering keys, no caller needs it); leaving the
literals (rejected — that is the debt this iteration closes, SC-002).

## D2 — Byte-identity preservation per migrated call site

**Decision**: For each migrated site, the kwarg order passed to `ok_payload`
MUST match the current literal's key order after `"status"`:

| Command | Current literal | Migrated call |
|---|---|---|
| `focus show` (set) | `{"status":"ok","focus":focus.model_dump()}` | `ok_payload(focus=focus.model_dump())` |
| `focus show` (none) | `{"status":"ok","focus":None}` | `ok_payload(focus=None)` |
| `focus set` | `{"status":"ok","focus":block.model_dump()}` | `ok_payload(focus=block.model_dump())` |
| `focus clear` | `{"status":"ok","cleared":had_focus}` | `ok_payload(cleared=had_focus)` |
| `graph query` | `{"status":"ok","results":rows,"count":len(rows)}` | `ok_payload(results=rows, count=len(rows))` |

`emit_json` wraps each. No `render_json`/cache write is needed (only `status`
writes a cache).

**Rationale**: keyword-argument order is preserved into `**fields`, so the
resulting dict order is identical → identical compact JSON → identical bytes.

**Alternatives**: none — this is the single mechanical mapping.

## D3 — `check.py` deliberately stays outside `ok_payload`

**Decision**: Leave `check.py` building `payload = {"ok": ok, "checks": checks}`
verbatim. Do **not** route it through `ok_payload`.

**Rationale**: `check`'s envelope has no top-level `status` key by design;
`ok_payload` would inject `"status":"ok"` as the first key and change every byte.
The per-check dicts `{"name", "status", "detail?}` are domain sub-objects, not the
Principle-IX envelope, and are left untouched. `check` already emits via
`emit_json`, so its construction is already single-sourced as far as it can be
without changing bytes (FR-003). The regression test still pins its bytes.

**Alternatives**: forcing it through `ok_payload` (rejected — changes bytes,
violates FR-003 and the spec's "byte-identical wins over uniformity" assumption).

## D4 — `graph build` already single-sourced

**Decision**: Confirm `graph build` routes success through
`BuildReport.to_json()` (an object serializer, `io/report.py`) + `emit_json`, not
a hand-built literal. No structural change to its success path; the **only** edit
is the FR-016 key rename inside `to_json()`.

**Rationale**: `build.py` already does `emit_json(report.to_json())`. The
`"status":"ok"` literal living in `to_json()` is the report object's own
serializer (one source for that document); re-routing it through `ok_payload`
would be churn with byte-risk and no benefit. FR-004 only asks us to *confirm and
not regress* this path.

**Alternatives**: rewrite `to_json` to call `ok_payload` (rejected — needless
risk; the report serializer is itself a legitimate single source).

## D5 — Regression test mechanism

**Decision**: Add `tests/commands/test_success_envelopes.py`. Invoke each command
in-process via the existing test pattern (Typer `CliRunner` / the project's
established invocation helper used in `tests/commands/graph/test_*` and
`tests/commands/focus/test_*`), capture **stdout bytes**, and assert each equals a
pinned literal baseline. Run the SAME assertions are part of the suite that runs
before *and* conceptually represents "after"; the pins are captured from current
`main` behavior. Include `check`, `focus show/set/clear`, `graph query`, and
`graph build`.

**Rationale**: golden-bytes pinning is the spec-named mechanism (Assumptions); it
introduces no new framework. Pinning literal expected strings (not "capture then
re-capture") is what actually guards against drift in CI on every later change.

**Implementation notes**:
- Use small fixtures already in `tests/` (the focus tests already set up a
  project with/without a `[focus]` block; the graph tests already build a graph).
- For `graph build`, the pinned baseline carries `unresolved_references` (the new
  name) since the test lands together with the rename; for an unchanged-key proof
  it asserts the FULL document equals the new golden, and a focused assertion that
  the key at its position is `unresolved_references`.
- Assert exit codes alongside bytes (FR-006).

**Alternatives**: snapshot libraries / `syrupy` (rejected — new dependency,
Constitution II); comparing parsed JSON (rejected — would miss key-order and
separator drift, the exact thing US1 guarantees).

## D6 — G6/G3 deferral data edit

**Decision**: In `golem/deferrals.py` set both entries to
`target_version="v0.4"` with `reason="requires a typed roles/states model with
attributes and an authoring surface"`. Remove `"undecided"` from the
`DeferralNote` docstring's enumerated contract (it now lists only the concrete
versions, e.g. `"v0.4"`). Do **not** wire either concept.

**Rationale**: both carry a *mandatory* cross-ref (`RelationshipRole.relationship`,
`PsychologicalState.bearer`) and have no `bible/` authoring surface; an
identity-only node would be semantically degenerate (Edge Cases, Assumptions).
Confirmed deferral keeps the orphan set unchanged and keeps 027 the closing
iteration. This is decided, not open (Clarifications Q3).

**Alternatives**: wiring identity-only (rejected by the spec — degenerate node);
leaving `"undecided"` (rejected — FR-011/SC-003 forbid it after this iteration).

## D7 — Parity-test pin updates

**Decision**: In `tests/golem/test_ingestion_parity.py`:
- `EXPECTED_VERSIONS`: change `RelationshipRole` and `PsychologicalState` from
  `"undecided"` to `"v0.4"`.
- Leave `EXPECTED_REACHABLE` (8) and `ORPHAN_NAMES` (5) **unchanged** — the orphan
  set is identical; only the version mapping moved.
- Add an assertion in `test_registry_well_formed` that **no** entry has
  `target_version == "undecided"` (FR-011 / SC-003), so the eliminated literal can
  never silently return.

**Rationale**: the decision is "confirm deferral", which moves a version label, not
a set membership. The new assertion makes the "zero undecided" invariant a
machine-checked contract rather than a one-time edit.

**Alternatives**: also moving names between reachable/orphan sets (rejected —
nothing is wired, so the sets do not move).

## D8 — Rename scope (the exhaustive `src/` + `docs/` surface)

**Decision**: Full rename across both the Pydantic report type *and* the
intermediate builder dataclass field, so the final grep is clean:

| File | Reference(s) | New |
|---|---|---|
| `io/report.py` | class `UnresolvedParticipant`; `BuildReport.unresolved_participants` field; `to_json()` key `"unresolved_participants"`; class docstring; module docstring | `UnresolvedReference`; `unresolved_references`; `"unresolved_references"`; generalized docstrings |
| `io/_bible_builders.py` | import; `BuildResult.unresolved_participants` field; 3 `.unresolved_participants.append(UnresolvedParticipant(...))` sites; 2 docstrings | renamed type + field |
| `io/bible.py` | module-docstring mention | renamed |
| `commands/_graph.py` | `unresolved_participants=tuple(result.unresolved_participants)` (both sides) | renamed |
| `commands/graph/build.py` | `report.unresolved_participants` access; stderr `"unresolved participant reference(s)"` | `report.unresolved_references`; `"{n} unresolved reference(s)"` |
| `docs/commands/graph-build.md` | the key in the list of soft warnings | `unresolved_references` |

Tests referencing the old names (`tests/io/test_bible.py`,
`tests/commands/graph/test_build.py`, `tests/fixtures/test_fixtures.py`,
`tests/resources/{conftest,test_frontmatter_contract}.py`) are updated to the new
names so the suite stays green. (Tests are outside the FR-019 grep scope — that
scope is `src/` + `docs/` — but must pass.)

**Rationale**: the spec requires zero `UnresolvedParticipant` /
`unresolved_participants` in `src/`+`docs/` (FR-019, SC-007). The intermediate
`BuildResult` field is in `src/`, so it must be renamed too — leaving it would
fail the final grep and re-introduce a name mismatch inside the pipeline.

**Alternatives**: class-only rename (rejected by Clarification Q2 — leaves a
permanent model↔wire mismatch).

## D9 — Key position preservation in `graph build` JSON

**Decision**: In `BuildReport.to_json()` the renamed key keeps its **exact slot**
between `"unknown_keys"` and `"sources"` (current order:
`status, files_processed, entities, triples, skipped, unknown_keys,
unresolved_participants, sources, findings, anchors, research_warnings,
graph_path`). Only the key *string* changes; the surrounding order, the compact
separators, and the trailing newline are untouched (FR-017).

**Rationale**: byte-identity is relaxed solely for the key string (FR-016/FR-017);
a new golden baseline replaces the old for that one key, everything else
byte-stable.

## D10 — CHANGELOG / release framing

**Decision**: The `unresolved_participants` → `unresolved_references` key rename
is a documented public-contract change recorded in the CHANGELOG at release time
(`bookwright-release` skill drives the patch `v0.3.4`). No skill reads the key
from `graph build --json`, so blast radius is `src/`, tests, and one doc page.

**Rationale**: a maintainer/agent-facing JSON key rename is acceptable in a `0.x`
patch when documented (Assumptions). Release mechanics are out of this plan's
scope; this note just records the obligation.
