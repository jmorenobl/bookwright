# Research: Release Prep — Fixtures, E2E Tests & Documentation

**Branch**: `011-release-prep` | **Date**: 2026-06-03 | **Phase**: 0

This iteration is polish/consolidation: no new runtime feature, no new
command. The open questions are therefore *technical-approach* decisions
about how to author the fixtures, how to drive the real CLI from tests so
the E2E layer counts toward coverage, and how to ship a docs site that
builds with zero warnings without pulling forbidden plumbing. The spec
itself carries no `NEEDS CLARIFICATION` markers (both clarification
questions were answered in Session 2026-06-03), so the work here is
de-risking implementation choices, not resolving requirement ambiguity.

---

## D1 — How E2E tests invoke the CLI (in-process vs subprocess)

**Decision**: Drive the CLI **in-process** via Typer's `CliRunner`
(`typer.testing.CliRunner`) for every assertion that must contribute to
coverage (FR-009). Keep exactly one *subprocess* path — the existing
`tests/test_cli_subprocess.py` style plus the packaged-wheel quickstart —
for the "real `bookwright` on `PATH`" smoke, which by design does **not**
count toward `--cov`.

**Rationale**: `pytest-cov` measures the in-process interpreter. A
subprocess-only E2E suite would exercise the code but report 0% of it as
covered, and FR-009 explicitly requires the E2E tests to *contribute to
the coverage measurement*. `CliRunner` invokes the same Typer `app`
(`bookwright.cli:app`) the console-script entry point uses, so the call
path is faithful while staying in-process. The repo already has both
shapes (`tests/test_cli_subprocess.py`, `tests/test_cli_version.py`), so
this matches established convention.

**Alternatives considered**:
- *All-subprocess (`subprocess.run(["bookwright", ...])`)*: most faithful
  to a user's shell, but invisible to coverage → fails FR-009. Reserved
  for the single packaged-wheel validation.
- *`coverage run --parallel` across subprocesses*: would recover coverage
  from subprocesses but adds CI plumbing and a combine step for marginal
  fidelity gain over `CliRunner`. Rejected as over-engineering for v0.

---

## D2 — Fixture graph: ship `bible/graph.ttl` or rebuild it in tests

**Decision**: Fixtures ship **source only** (manifest, constitution,
bible, outline, manuscript, vocabulary). They do **not** commit
`bible/graph.ttl`. E2E/fixture tests copy the fixture into `tmp_path`
(`shutil.copytree`) and run `bookwright graph build` there, so the graph
is materialized in the throwaway copy, never in the committed tree.

**Rationale**: `bible/graph.ttl` is a derived cache, deterministically
rebuildable from the bible — committing it as canonical state violates
Constitution Principle I (derived caches "MAY exist on disk only if … and
clearly marked as ephemeral"). Building in-place inside the committed
fixture would also dirty the working tree during a test run and risk
order-dependent tests. Copy-to-tmp keeps the committed fixture immutable
and each test hermetic.

**Alternatives considered**:
- *Commit `graph.ttl` and assert against it*: faster tests, but turns a
  derived artifact into source-of-truth (Principle I violation) and makes
  the fixture rot silently if the indexer changes. Rejected.
- *Build in the fixture dir, clean up after*: mutates a committed path
  mid-test; fragile under `-p no:randomly`/parallelism. Rejected.

---

## D3 — Non-fiction fixtures must validate clean (no false positives)

**Decision** (revised after reading the runtime): all three fixtures —
`tiny-novel`, `tiny-essay`, `tiny-memoir` — run the **full** built-in
validator set (`[validators] disabled = []`). No validator is disabled and
no validator code changes. "Clean" is defined against the real gate:
`bookwright validate` exits 0 ⟺ zero **`error`-severity** violations
(`ValidationReport.failed` keys on `error` only — `report.py:49-51`).
Heuristic `warning`-severity findings are permitted and non-gating.

**Rationale**: the earlier plan to disable `character_presence` /
`focalization` on non-fiction was unnecessary masking. Reading the
validators shows the fiction checks are *inert off-genre*:
- `character_presence` splits by severity — an unmentioned bible character
  is an **error**, but an unknown proper-noun mention is only a
  **warning** (`character_presence.py:103`; orphans=error, unknown=warning).
  An essay has an empty roster → zero orphan errors; cited-author surnames
  produce only warnings, which don't gate.
- `focalization` returns no findings unless the constitution declares a
  **third-person** voice (`focalization.py:62-71`); a first-person memoir
  or a declaration-less essay yields nothing.
So both non-fiction fixtures pass the error gate with every validator
active — exercising the *full* set (higher signal) with *less* config.
Critically, disabling was also self-defeating for `tiny-novel`: under a
"zero findings incl. warnings" reading, the novel's own **setting names**
(capitalized, not in the character roster) would trip `character_presence`
warnings, forcing brittle prose contortions. Defining clean = zero errors
removes that coupling entirely, and still requires **no validator code
change** (the spec's explicit constraint).

**Alternatives considered**:
- *Per-fixture `[validators] disabled` to suppress warnings*: masking
  config with no functional need under the error gate; hides which
  validators actually ran and shrinks what the fixtures exercise.
  Rejected as technical debt.
- *Define clean = "zero findings of any severity" (`status == "ok"`)*:
  makes `tiny-novel` couple to the unknown-mention heuristic (its
  settings) and contradicts the engine, whose gate is errors-only.
  Rejected.
- *Add a `genre`-aware auto-disable in validator selection*: new runtime
  behavior, out of scope; needs its own spec. Rejected.

**Verification target**: SC-001 / FR-004 — all three fixtures return
**zero `error`-severity violations** (`bookwright validate` exit 0) in
their shipped state, with every built-in validator active.

---

## D4 — Docs ↔ CLI drift detection (FR-015, edge case)

**Decision**: Add a lightweight **test** that introspects the live Typer
app (`bookwright.cli:app`) for its registered command names and asserts
the docs `commands` section documents exactly that set — neither missing
a shipped command nor documenting a non-existent one. The check compares
the command inventory (`init`, `check`, `version`, `validate`, `graph
build`, `graph query`) against the page/section list under `docs/`. The
introspection MUST descend into registered sub-`Typer` groups so the
inventory contains leaf paths (`graph build`, `graph query`), not the bare
`graph` group, otherwise the comparison reports false drift.

**Rationale**: FR-015 requires documented command names/flags to match the
shipped CLI, and the edge case asks that drift "surface rather than
silently ship". An introspection test is cheap, deterministic, and fails
closed in CI. Full flag-level prose-matching would be a doc-linter project
of its own (out of scope); command-set parity is the high-value, low-cost
guard.

**Alternatives considered**:
- *Parse `--help` output and diff every flag against prose*: high
  maintenance, fuzzy matching, false failures on wording. Deferred.
- *Trust review only*: violates "fail closed" intent of the edge case.

---

## D5 — MkDocs configuration, theme, and the "architecture" page

**Decision**: `mkdocs.yml` at the repo root; theme `material`
(`mkdocs-material`); `docs/` holds the seven page areas (index,
getting-started, architecture, commands, validation, extending, FAQ) as
plain Markdown. The **architecture page is a hand-curated Spanish summary**
that links into `bookwright-design.md` by section (`§ N.M`) rather than
duplicating it; the full design doc ships alongside the repo and is the
canonical long-form reference. `strict: true` in `mkdocs.yml` so any
broken link / missing nav target / orphan page is a **build error**
(satisfies the zero-warnings gate, FR-014/SC-004).

**Rationale**: `material` is the theme named in the spec and the iteration
hint. `strict: true` is how MkDocs turns warnings into a failing build, so
"zero warnings" becomes machine-checkable. A curated summary + section
links keeps the design doc as single source of truth (no wholesale
duplication, FR-013) and avoids any generated-content plugin.

**Alternatives considered**:
- *`mkdocs-gen-files` / `mkdocstrings` to auto-generate the architecture
  page from the design doc or from source docstrings*: adds plugins and a
  generation step whose only payoff is automating a one-page summary; risks
  warnings and pulls doc-tooling complexity. The hint's "resumen
  automático" is satisfied by a small, maintained summary page with
  deterministic section links. Rejected for v0; noted as a post-v0 option.
- *Read the Docs / Sphinx*: not the theme/ecosystem the spec names.

---

## D6 — Where MkDocs + docs deps live (Constitution Principle II)

**Decision**: `mkdocs`, `mkdocs-material` (and any small docs helper) go
into a **dedicated `docs` dependency group** under
`[dependency-groups]` in `pyproject.toml` — **not** in
`[project.dependencies]`. They are dev/build tooling, run via
`uv run --group docs mkdocs build`.

**Rationale**: Constitution Principle II / Technical Constraints bind the
**runtime** dependency list; adding a runtime dependency needs a MINOR
amendment. MkDocs never ships inside the wheel and is never imported by
`src/bookwright/` at runtime, so it is categorically a dev/docs tool (same
class as `mypy`, `ruff`, `pytest`, already in the `dev` group). Putting it
in a `docs` group keeps the runtime contract untouched → **no
constitutional amendment required**.

**Alternatives considered**:
- *Add to `[project.dependencies]`*: would bloat every install of
  `bookwright-cli` with a docs toolchain and would require (and fail
  without) a constitutional amendment. Rejected.
- *Fold into the existing `dev` group*: works, but a separate `docs` group
  lets CI install only what the docs-build job needs. Minor preference.

---

## D7 — Distribution build + isolated-install validation (FR-022, SC-007)

**Decision**: Build the wheel + sdist with `uv build`. Provide a
**scripted manual quickstart** (`quickstart.md` + a `scripts/` helper or
documented steps) that installs the local wheel into an isolated
environment (`pipx install ./dist/bookwright_cli-*.whl`, or `uv tool
install`) and runs the README quickstart. Gate the *buildability* of the
artifact in CI (a `uv build` step) but treat the **isolated-install +
quickstart run** as the documented **manual** acceptance step (SC-003 /
SC-007), optionally wrapped in a `@pytest.mark.manual`/`slow` test that is
deselected by default.

**Rationale**: `uv build` producing a valid wheel/sdist is fast and
deterministic — worth a CI gate (FR-022 first half). A full `pipx`
install into a clean env is network-dependent and slow; the spec and the
iteration plan both frame it as **manual validation with an external
user** ("Validación manual al final con un usuario externo si es
posible"). Encoding it as a documented, repeatable procedure (not a
default-on test) matches that intent and keeps CI hermetic.

**Alternatives considered**:
- *Always-on E2E test that pipx-installs the wheel*: flaky/slow in CI,
  needs network. Made opt-in (`-m manual`) instead.
- *Skip artifact build in CI entirely*: would let packaging regressions
  (e.g. missing `resources/` in the wheel) reach a tag undetected.
  Rejected — keep the `uv build` gate.

---

## D8 — CI: add the docs-build gate

**Decision**: Extend `.github/workflows/tests.yml` with a **docs job**
(or a step on the 3.12 leg) that runs `uv run --group docs mkdocs build
--strict`, and an artifact-build step that runs `uv build`. The existing
`pytest` / `ruff check` / `ruff format --check` / `mypy --strict` matrix
is unchanged.

**Rationale**: FR-021 requires CI to run the test, lint, type, **and
docs-build** gates green on the release branch. `--strict` makes the docs
build fail on any warning (ties to D5/FR-014). Reusing the existing
workflow keeps one source of truth for gates.

**Alternatives considered**:
- *Separate `docs.yml` workflow*: fine, but a single workflow keeps the
  "all gates green" picture in one place for the release branch.

---

## D9 — Fixture authoring: shape that indexes with zero skips

**Decision**: Each fixture mirrors the `bookwright init` scaffold exactly,
with the GOLEM-bearing files authored to the iteration-6 mapper's
recognized frontmatter keys:

- `tiny-novel`: `bible/characters/<slug>.md` ×3 (frontmatter `name` +
  optional `born`/`features`/`narrative_roles`), `bible/settings/<slug>.md`
  ×2 (`name` only), `bible/timeline.md` with an `events:` list of **5**
  items (each `{name, participants:[<character-slug>…]}`),
  `bible/constitution.md` with a narrative-voice declaration matching the
  prose, fully-filled `outline/*`, and **one** draft chapter under
  `manuscript/` mentioning every character by name (so
  `character_presence` finds no orphan).
- `tiny-essay`: 3 chapters under `manuscript/`, **no** `bible/characters/`
  entries, a bibliography document, manifest `type = "essay"` with **all
  validators active** (clean because the fiction checks are inert
  off-genre — revised D3).
- `tiny-memoir`: a single protagonist character (the author),
  autobiographical scenes/chapters that mention the author by name, a
  first-person voice declaration so `focalization` stays silent; manifest
  `type = "memoir"` with **all validators active** (revised D3).

**Rationale**: The iteration-7 molds already encode the exact recognized
keys (`character.md.tmpl`, `setting.md.tmpl`, `timeline.md`), so authoring
to them guarantees `graph build` reports **zero skips / zero
unknown_keys**. The novel's 5-event/3-character/2-setting counts are the
SC-001 assertion targets and the timeline-event source is the
`events:` frontmatter list (`io/bible.py: TIMELINE_TOP_KEYS = {"events"}`).
"Coherent, not rich" (spec Assumptions) keeps the prose minimal while
internally consistent.

**Rationale (size)**: Fixtures omit any materialized `.claude/skills/` /
`.agents/skills/` directory — graph build/query/validate never read them,
and the skills-materialization test generates its own. This keeps fixtures
small and review-friendly (plain text only, Principle I).

---

## Resolved unknowns summary

| ID | Question | Decision |
|----|----------|----------|
| D1 | CLI invocation in E2E | In-process `CliRunner` for coverage; one subprocess smoke |
| D2 | Ship `graph.ttl`? | No — rebuild in `tmp_path` copy |
| D3 | Non-fiction false positives | All validators active; clean = zero *error*-severity (warnings non-gating); no code change |
| D4 | Docs/CLI drift | Introspection (leaf paths incl. `graph build/query`) == documented set |
| D5 | MkDocs + architecture page | `material`, `strict: true`, curated summary linking design § |
| D6 | Docs deps & Principle II | `docs` dependency group, not runtime → no amendment |
| D7 | Isolated-install validation | `uv build` gated in CI; pipx quickstart manual / `-m manual` |
| D8 | CI docs gate | `mkdocs build --strict` + `uv build` added to workflow |
| D9 | Fixture shape | Mirror init scaffold; author to iteration-6 mapper keys |

No `NEEDS CLARIFICATION` remain. No Constitution violations introduced
(see `plan.md` Constitution Check). No runtime dependency added.
