# Implementation Plan: Validation System

**Branch**: `010-validation-system` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-validation-system/spec.md`

## Summary

Add a deterministic validation subsystem and a `bookwright validate` command. A
single `Validator` protocol (name, default severity, `validate(project, indexer)
-> list[Violation]`) is auto-discovered: built-ins by iterating the
`bookwright.validation.validators` package, custom ones by loading `*.py` from
`<project>/.bookwright/validators/`. The manifest's `[validators]` block
(`enabled` / `disabled` / `custom`) selects the active set. Four built-ins ship:
`temporal` (error) reads the graph; `character_presence` (error),
`setting_continuity` (warning), and `focalization` (warning) read the bible,
manuscript prose, and constitution directly. The command renders a grouped human
report (stdout) or a single JSON document under `--json` (Principle IX), supports
`--scope PATH` and `--severity LEVEL` display filters, and signals failure (exit
1) when **any** error-severity violation exists *before* filtering, so a display
filter can never mask the CI gate.

**Robustness decision (see research D1/D11).** The merged indexer emits no temporal
edges, so a graph-only `temporal` validator would be inert on real projects. To
make the feature genuinely work (not just pass fabricated fixtures), this iteration
also closes that gap in a layered way: the `bible/timeline.md` frontmatter gains
optional `date:` / `follows:` keys, and the `NarrativeEvent` model + bible indexer
emit a closure-safe year literal (`temporal-location` → `P90_has_value`/`gYear`) and
`follows`/`temporally-overlaps` edges. `temporal` stays a pure graph consumer.
`character_presence` splits severity: the deterministic orphan-in-bible finding is
`error` (gates CI); the heuristic unknown-mention finding is `warning` (never fails
a build on a false positive).

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II).

**Primary Dependencies**: existing only — `typer`, `rich`, `rdflib`, `pydantic`
v2, `pyyaml` (via `io.bible`). No new runtime dependency; mention/POV detection
uses the stdlib `re`. Discovery uses stdlib `importlib` + `pkgutil` (no
`entry_points` machinery — see research D2).

**Storage**: reads plain-text sources (`bible/`, `manuscript/`, constitution) and
the already-built `bible/graph.ttl`; writes nothing (FR-020). Custom validators
live as `.py` under `<project>/.bookwright/validators/`.

**Testing**: pytest. Per FR/SC, each validator gets one fixture with an injected
violation and one clean fixture; the command gets integration tests for
`--json` / `--scope` / `--severity` / exit-code gating.

**Target Platform**: cross-platform CLI (macOS / Linux; Windows path-safe).

**Project Type**: single project (CLI), `src/bookwright/` + `tests/`.

**Performance Goals**: none formal; graphs are <10k triples and manuscripts are
small. Regex scans are linear in manuscript size.

**Constraints**: deterministic (FR-019, SC-003) — discovery order, file
iteration, and emitted findings MUST be stably sorted; no LLM, no network. One
failing validator MUST NOT abort the run (FR-014). JSON mode: one document on
stdout, prose on stderr (Principle IX).

**Scale/Scope**: 4 built-in validators, 1 command, the discovery/registry layer,
and a report/filter/gate layer. No graph mutation, no auto-fix, no NER.

## Constitution Check

*GATE: re-checked after Phase 1 — still passing.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain text as source of truth | ✅ | Reads md/toml/ttl; emits no canonical store. Custom validators are user `.py` (code, not data). |
| II. Modern Python stack | ✅ | No new dependency. `re`, `importlib`, `pkgutil` are stdlib. |
| III. src-layout | ✅ | `src/bookwright/validation/`, command in `src/bookwright/commands/validate.py`, tests in `tests/`. |
| IV. Modular command surface, ≤500 lines | ✅ | `validate` in its own module; subsystem split across base/registry/report/queries + one file per validator. Every file budgeted <300 lines. |
| V. Plugin-based integrations | ✅ (N/A) | Not an integration. The validator registry follows the same plugin spirit (auto-discovery, no monolithic dispatcher). |
| VI/VII. Agent Skills only / agentskills.io | ✅ (N/A) | Emits no skills. |
| VIII. Test discipline (≥80%) | ✅ | Unit tests for `validation/` (per the pyramid this principle names explicitly); integration tests for the `validate` flow. |
| IX. JSON-over-stdout | ✅ | `--json` → single JSON doc on stdout; human prose/progress on stderr; non-zero exit on gate fail even under `--json`. |
| X. Design axioms | ✅ | rdflib (not Grafeo); deterministic (no LLM); does not reopen any § 16 axiom. |

**No violations → Complexity Tracking is empty.**

### Scope guard (Constitution "Scope & Release Discipline")

This iteration adds the validation subsystem named in design § 13 and plan § 2
(iteration 11). It **also** makes a small, deliberate extension to the timeline
frontmatter + the bible indexer + the `NarrativeEvent` model so the graph carries
the temporal signals the clarified `temporal` validator requires (research D1/D11):
optional `date:` / `follows:` timeline keys → closure-safe year literal +
`follows`/`temporally-overlaps` edges. This is **completing a v0 (M3) feature**, not
the "future preset/extension plumbing" the constitution forbids; all new frontmatter
keys are optional (backward compatible) and no new runtime dependency is added.
Because this crosses into iteration-5/6 territory, `/speckit-analyze` must confirm
cross-artifact consistency. No constitution amendment is required. Everything else a
validator needs (manuscript prose, setting descriptions, declared POV) is read from
source files, not mined into the graph.

## Project Structure

### Documentation (this feature)

```text
specs/010-validation-system/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions D1..D10
├── data-model.md        # Phase 1 — Severity, Violation, ValidationContext, Report, config resolution
├── quickstart.md        # Phase 1 — run validate, configure, add a custom validator
├── contracts/
│   ├── validator-protocol.md   # the Validator protocol, Violation shape, discovery + config rules
│   └── cli-validate.md         # command surface: flags, exit codes, JSON envelope
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── validation/
│   ├── __init__.py            # re-export Severity, Violation, Validator, ValidationContext,
│   │                          #   discover_validators, resolve_active, run_validators
│   ├── base.py                # Severity (str Enum), Violation (frozen dataclass),
│   │                          #   ValidationContext (project accessors), Validator Protocol
│   ├── queries.py             # graph helpers: predicate IRIs (follows/overlaps/time-span),
│   │                          #   resolve_source(indexer, uri) via CIDOC provenance
│   ├── registry.py            # autodiscovery (built-ins via pkgutil; custom via importlib),
│   │                          #   manifest filtering, unknown-name detection, malformed-skip
│   ├── runner.py              # run active validators with per-validator isolation (FR-014)
│   ├── report.py              # ValidationReport: scope/severity filtering, gate, to_json + render
│   └── validators/
│       ├── __init__.py
│       ├── temporal.py            # graph: earlier-dated event follows later; follows cycles
│       ├── character_presence.py  # regex name match: orphan bible entry + unknown manuscript mention
│       ├── setting_continuity.py  # contradiction-lexicon descriptors per setting across files
│       └── focalization.py        # constitution-declared person/focus vs manuscript prose
├── commands/
│   └── validate.py            # Typer command; wires context+engine → runner → report → exit code
└── (indexer-gap closure — research D1/D11; small edits to existing iter-5/6 modules)
    golem/modules/event.py      # NarrativeEvent gains optional date (year) + follows/overlaps refs
    golem/namespaces.py         # add FOLLOWS, TEMPORALLY_OVERLAPS, TR namespace (all in frozen_terms)
    io/bible.py                 # timeline mapper reads date:/follows:/overlaps:, resolves refs via slug index

tests/
└── validation/
    ├── __init__.py
    ├── conftest.py            # project scaffolds + per-validator violation/clean fixtures
    ├── test_base.py           # Severity ordering, Violation shape, context accessors
    ├── test_registry.py       # discovery, enabled/disabled/custom resolution, unknown-name, malformed-skip
    ├── test_report.py         # scope + severity filtering, gate computation
    ├── test_temporal.py       # injected + clean, end-to-end (timeline.md → graph build → validate)
    ├── test_character_presence.py   # orphan(error) + unknown-mention(warning) + clean
    ├── test_setting_continuity.py
    ├── test_focalization.py
    └── test_command.py        # integration: --json contract, --scope, --severity, exit codes, edge cases

# indexer-gap closure — extend existing iter-5/6 test suites (not new files):
tests/golem/test_triples.py      # NarrativeEvent emits temporal-location/gYear + follows edges
tests/golem/test_namespaces.py   # FOLLOWS / TEMPORALLY_OVERLAPS ∈ frozen_terms()
tests/io/test_bible.py           # timeline date:/follows:/overlaps: mapping + unresolved-ref warnings
```

**Structure Decision**: single-project src-layout (Constitution III). The
subsystem is a `validation/` package (sibling of `golem/`, `indexers/`,
`integrations/`); the command is one module under `commands/` registered in
`cli.py` via `app.command("validate")(validate.run)`. Validators live one-per-file
under `validation/validators/` so the package is the auto-discovery root and each
stays well under the 500-line ceiling (Principle IV).

## Phase 0 — Research (see research.md)

Resolved decisions (no open NEEDS CLARIFICATION):

- **D1 — Indexer gap, closed deliberately.** The merged indexer is
  bible-frontmatter-driven (identity + participants + CIDOC `E13` provenance only) —
  **no** `follows`, dates, setting descriptions, or prose mining. Rather than ship an
  inert graph-only `temporal`, this iteration extends `bible/timeline.md`
  (optional `date:`/`follows:`) + the bible indexer + `NarrativeEvent` to emit the
  temporal edges; `temporal` stays a pure graph consumer. `character_presence`,
  `setting_continuity`, `focalization` read source files directly.
- **D2 — Discovery mechanism.** Iterate `bookwright.validation.validators` modules
  with `pkgutil.iter_modules` and collect protocol-conforming instances; custom
  via `importlib.util.spec_from_file_location` over sorted `*.py`. No `entry_points`
  (no reinstall step, deterministic, self-contained).
- **D3 — `character_presence` heuristic + severity split.** Bible roster from
  `io.bible.map_bible`; word-boundary regex per name over manuscript prose. Orphan =
  bible name never matched → **`error`** (deterministic, gates CI). Unknown mention =
  conservative proper-noun candidate not matching any roster name → **`warning`**
  (heuristic; a false positive must never fail a build). No NER; documented limits.
- **D4 — `setting_continuity` heuristic.** Per setting name, scan manuscript for a
  descriptor from a tiny built-in **contradiction lexicon** (antonym groups, e.g.
  coastal/inland). Same setting tagged with two terms from one group across
  different files → warning citing both `file:line`.
- **D5 — `focalization` heuristic.** Parse the constitution "Voz narrativa" line
  for declared person (first/second/third) and, if a bible character name appears
  there, the focal character. Flag (a) first-person pronouns outside dialogue when
  third-person is declared and (b) interiority verbs attached to a **non-focal**
  bible character (head-hopping) under third-person-limited.
- **D6 — Source resolution from the graph.** `resolve_source(indexer, uri)` reads
  the CIDOC provenance edge (`crm:P140_assigned_attribute_to` ←
  `crm:P16_used_specific_object`) to recover the `relpath[:line]` string for a
  graph entity.
- **D7 — Config resolution & exit codes.** `enabled` empty = all built-ins; non-empty
  intersects; `disabled` subtracts; `custom` empty = all discovered customs,
  non-empty allow-lists them; any referenced name absent from the discovered set →
  exit 2. Exit 0 ok, 1 = ≥1 error-severity violation (pre-filter gate), 2 = config/usage.
- **D8 — Determinism.** Stable sort of discovery, file iteration, and emitted
  findings; deduplicate identical findings (edge case).
- **D9 — Failure isolation.** Per-validator try/except in the runner; malformed
  custom load and runtime raises both surface as report `errors[]` (attributed),
  never abort, never gate.
- **D10 — Scope semantics.** Scope resolved under project root; a scope path
  matching no project content → exit 2; location-less violations omitted under an
  active scope (per clarification).
- **D11 — Closure-safe event date.** `crm:P4_has_time-span` is **not** in the frozen
  GOLEM ontology (would fail the term-closure test), so the event year is modelled
  with frozen predicates: `temporal-location` → a time node → `crm:P90_has_value`
  `xsd:gYear` (reusing the character born/died literal pattern). `follows` /
  `temporally-overlaps` are emitted directly (both ∈ `frozen_terms()`).

## Phase 1 — Design & Contracts

- **data-model.md** — `Severity` ordering, `Violation` fields (validator,
  severity, message, source `file[:line]|None`, triples), `ValidationContext`
  (root, manifest, cached bible/manuscript/constitution accessors),
  `ValidatorError`, `ValidationReport` (filter + gate), config-resolution rules.
- **contracts/validator-protocol.md** — the `Validator` protocol, the `Violation`
  contract (FR-001/002/003), and discovery/configuration rules (FR-004..007).
- **contracts/cli-validate.md** — `bookwright validate` flags (`--scope`,
  `--severity`, `--json`), exit codes, and the JSON success/error envelope
  (FR-008..014, Principle IX).
- **quickstart.md** — run a validation, read the report, filter/scope, configure
  `[validators]`, drop in a custom validator.
- **Agent context update** — point the CLAUDE.md SPECKIT marker at this plan.

## Complexity Tracking

> No Constitution Check violations — this section is intentionally empty.
