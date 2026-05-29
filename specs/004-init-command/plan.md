# Implementation Plan: `bookwright init` Command

**Branch**: `004-init-command` | **Date**: 2026-05-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-init-command/spec.md`

## Summary

Deliver `bookwright init` — the first user-facing command. It produces, in
one invocation, the full project tree from
[bookwright-design.md § 7](../../bookwright-design.md) (manifest, manuscript,
bible, outline, `.bookwright/` metadata, and the chosen integration's skills
directory), then makes exactly one git commit titled
`Initial commit from bookwright init`. It consumes — but does not duplicate —
the iteration-2 `Manifest.build/dump` API and the iteration-3
`bookwright.integrations.{get, parse_options, SkillsIntegration.setup}`
surface.

Technical approach (grounded in `bookwright-design.md` § 5.2 + § 7, the
iteration-4 prompt in `bookwright-implementation-plan.md` § Iteración 4, and
the iteration-3 contract in
[`../003-integration-architecture/contracts/integrations_api.md`](../003-integration-architecture/contracts/integrations_api.md)):

- **One Typer subcommand module: `src/bookwright/commands/init.py`** —
  registers with `app.command("init")`, owns flag parsing, deprecation
  handling, JSON envelope serialization, and the top-level orchestration
  (`validate → resolve → scaffold → setup integration → git init+commit →
  emit`). Stays under the Principle IV 500-line ceiling by delegating to
  private helpers in the same package (`commands/_init_*.py`).
- **Templates ship as packaged resources** under
  `src/bookwright/resources/project/` and are loaded via
  `importlib.resources.files("bookwright.resources.project")`. A small
  template walker enumerates every entry in the tree and renders it: files
  ending `.j2` go through Jinja2 (`Environment(autoescape=False,
  keep_trailing_newline=True)`), everything else is byte-copied. Bible
  templates in this iteration are minimal placeholders (heading + a "see
  iteration 7" note) per the spec's assumption; the full versions land in
  iteration 7 without touching the walker.
- **`Manifest.build(...)` is the only way the manifest is produced** —
  `init` calls it with the resolved `title`, `authors`, `integration_key`,
  `integration_skills_dir`, and `integration_options`, then `Manifest.dump`s
  it. No alternative path. This is the iteration-2 contract surface.
- **The chosen integration's `setup()` runs after the rest of the tree is
  on disk** so a rollback-after-setup-failure path can still delete the
  marker via the same backup ledger that covers every other write.
  `parse_options(raw, integration_cls)` (iteration 3) is the only source of
  parsed integration options; `init` never re-parses.
- **Atomic-or-nothing on disk via a backup ledger** (FR-030). Every write
  goes through one writer that, before any byte hits the target,
  appends `(target_path, prior_state)` to an in-memory ledger:
  `prior_state` is `None` for "did not exist", or a path to a backup copy
  for "existed and is about to be overwritten under `--force`/`--here`".
  On success the backups are deleted; on any exception the ledger is
  replayed in reverse (created files unlinked, overwritten files restored).
  Backup creation that fails (e.g., permission denied) aborts before any
  byte is overwritten (FR-030 last sentence).
- **Git via `subprocess.run`** (per the planning hint and the spec's
  Assumption that the `git` binary on `$PATH` is the only mechanism — no
  new runtime dependency like GitPython). A wrapper checks `git --version`
  for availability; if missing and `--no-git` was not passed, scaffolding
  proceeds and a stderr warning is emitted (FR-024). If `--no-git` was
  passed, git is never invoked at all (FR-023). When `--here` lands inside
  an existing `.git/`, the wrapper short-circuits — no new init, no commit
  (FR-025).
- **Non-interactive detection (FR-029)**: `(sys.stdin.isatty() and
  sys.stdout.isatty())` AND `--json` not set. When non-interactive, the
  `--here` confirm prompt is replaced by a refusal. The TTY check is in one
  helper so tests can monkeypatch.
- **Deprecated-flag handling at the Typer layer**: `--ai <key>` is a hidden
  Typer option that, when present, is forwarded into `--integration`
  semantics and emits a one-line stderr warning (FR-003). `--ai-skills`
  and `--ai-commands-dir` are NOT declared as Typer options at all —
  they're trapped by a pre-callback that inspects `click.get_current_context().args`
  (Typer surfaces the underlying click context) so unknown-option errors
  become structured "removed flag" errors with a pointer to the modern
  invocation (FR-004). The pre-callback fires before any filesystem
  side-effect (FR-031 + the SC-005 "byte-for-byte unchanged on failure"
  guarantee).
- **`--json` is contract-tested via subprocess**, mirroring the existing
  `tests/test_cli_subprocess.py` pattern. The envelope shape is pinned in
  [`contracts/init_command.md`](contracts/init_command.md) and asserted by
  parametrized tests over success / each failure mode. Warnings still go to
  stderr even with `--json` set (FR-032).
- **Tests are end-to-end with `tmp_path`**, one file per User Story plus
  one file per cross-cutting concern. Each test invokes the Typer
  subcommand via `CliRunner` (in-process; cheap; what 95 % of the suite
  uses) and a small number of subprocess tests pin the stdout-purity
  contract (Principle IX, the same pattern already in place for `version`
  and `check`). The git binary is assumed available in CI; tests that hit
  git skip on `shutil.which("git") is None` so they survive minimal
  developer environments.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution Principle II, Technical
Constraints).

**Primary Dependencies**:

- Runtime: `typer` (CLI surface — already in iter 1), `rich` (progress on
  stderr — already in iter 1), `jinja2` (template rendering — already
  declared but unused until this iteration), `python-slugify` (PROJECT_NAME
  → directory slug — already declared but unused until this iteration),
  `tomlkit` (transitive via `Manifest.dump`), `pydantic` v2 (transitive via
  `Manifest`), and stdlib `subprocess`, `shutil`, `locale`, `importlib.resources`,
  `tempfile`, `json`, `sys`, `os`. **No new runtime dependency.**
- Dev / test: `pytest` + `pytest-cov` (already declared). No new dev
  dependency.

**Storage**: Plain-text only. Every artifact this command writes is
Markdown, TOML, JSON, Turtle, or an empty placeholder. The
`.bookwright-skills-placeholder` marker comes from iteration 3 unchanged.

**Testing**: `pytest`. Fixtures: `tmp_path` for E2E scaffold scenarios; the
existing `runner: CliRunner` fixture from `tests/conftest.py` for in-process
invocation; a `git_available` fixture that skips when `shutil.which("git")
is None`; a `non_interactive_io` monkeypatch fixture that forces the
`isatty()` check to return `False`. The `.bookwright/init-options.json`
output is the canonical fixture against which subsequent iterations'
introspection commands will diff (so its schema is pinned by contract, not
by golden-file comparison).

**Target Platform**: macOS + Linux developer CLIs (Python 3.11+). Windows
filesystem semantics are NOT in v0 scope; the Windows-reserved-name check
in FR-021a is enforced for portability of the manifest, not because v0
runs on Windows.

**Project Type**: CLI / library (single project, `src/` layout, per
Constitution Principle III). This iteration adds one Typer subcommand and
one resource subpackage.

**Performance Goals**: SC-001 sets the budget — "under 30 seconds wall-clock
on a typical laptop, including the initial git commit." The expected cost
breakdown is dominated by `git init` + one `git commit` (≈ 100 ms each on
SSD), with everything else (manifest build, ≈ 20 template writes,
integration `setup()`) well under 1 s.

**Constraints**:

- No new runtime dependency (Constitution Principle II).
- The command MUST NOT create any files outside the project root (FR-014).
  The backup ledger and any temp files live inside the project root (or its
  parent during the initial mkdir, for the directory-form invocation).
- The command MUST be atomic-or-nothing: on any error after the first byte
  is written, the target directory is byte-for-byte equivalent to its
  pre-invocation state (FR-030, SC-005). Verified by a parametrized test
  that snapshots a `dirhash`-equivalent (sorted (path, sha256) tuple list)
  pre and post for every documented failure mode.
- The command MUST emit a single JSON document on stdout when `--json` is
  set and nothing else; human progress goes to stderr (Principle IX,
  FR-032, FR-033). Verified by subprocess tests (the existing
  `tests/test_cli_subprocess.py` pattern).
- `.bookwright/init-options.json` MUST be a versioned envelope per FR-034
  and the spec's Session 2026-05-29 clarification: `{schema_version: 1,
  created_at: ISO 8601 UTC, bookwright_version: str, options: {...}}`.
  Consumers MUST reject unknown `schema_version`.
- `Manifest.build(...)` is the only producer of the manifest; `Manifest.dump`
  is the only writer. The init command does not re-implement TOML
  serialization (FR-015 → FR-021 land on the iteration-2 model, not on
  iteration 4 code).
- The chosen integration's `setup()` is the only producer of the skills
  directory and its marker (FR-013). `init` calls it once per invocation
  and never re-implements directory layout per integration.

**Scale/Scope**: One Typer subcommand, ≈ 20 packaged template files, two
bundled Turtle vocabularies (`propp.ttl`, `greimas.ttl`) — minimal stubs in
this iteration (full files land alongside iter 10 validation work). Test
slice target: ≥ 95 % line coverage on `src/bookwright/commands/init.py`
and its `_init_*` helpers; the global CI gate (Principle VIII, ≥ 80 %)
remains the merge gate.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Plain Text as Source of Truth (NON-NEGOTIABLE) | ✅ | Every file written is Markdown, TOML, JSON, Turtle, or empty placeholder. The two Turtle vocabularies (`propp.ttl`, `greimas.ttl`) are plain text. No binary stores. |
| II. Modern Python Stack | ✅ | No new runtime dependency. `typer`, `rich`, `jinja2`, `python-slugify`, `tomlkit`, `pydantic` are already locked in the Technical Constraints. Git is invoked via `subprocess.run` against the host's `git` binary — no Python git library is added (per spec Assumption + planning hint). |
| III. src-layout | ✅ | New code lives under `src/bookwright/commands/init.py` (+ private `_init_*.py` helpers) and `src/bookwright/resources/project/`. Tests under `tests/commands/`. No production code outside `src/bookwright/`. |
| IV. Modular Command Surface | ✅ | One file per subcommand. `init.py` registers itself with the Typer app and stays ≤ 500 lines by delegating to private helpers (same layout iteration 2 used for `core/_build.py` and `core/_translate.py`). Each helper is ≤ 500 lines. |
| V. Plugin-Based Integrations | ✅ | `init` consumes `bookwright.integrations.{get, parse_options, SkillsIntegration.setup}` exactly. No `AGENT_CONFIG`-style branching by integration key inside the command. The command does not import `ClaudeIntegration` or `GenericIntegration` by name — it uses the registry. |
| VI. Agent Skills Only — No Legacy Commands (NON-NEGOTIABLE) | ✅ | The only path that writes under the skills directory is `SkillsIntegration.setup()` (iteration 3), which writes one marker file. `init` writes nothing to `.claude/commands/`, `.agents/commands/`, or any analogous legacy directory. FR-004 explicitly rejects `--ai-commands-dir` so users cannot ask for one. |
| VII. agentskills.io Standard Compliance | ✅ | No `SKILL.md` is generated in this iteration (full materialization is iteration 9). The marker written by `setup()` is not a `SKILL.md` and is exempt from the standard. |
| VIII. Test Discipline (NON-NEGOTIABLE) | ✅ | Every FR cluster maps to at least one test in `tests/commands/`. End-to-end `tmp_path` scenarios cover the three primary user stories. Subprocess tests pin Principle-IX stdout purity. Atomic-rollback is verified by pre/post directory snapshots for every documented failure mode (FR-030, SC-005). Slice target ≥ 95 % on `bookwright.commands.init` + helpers; global CI gate ≥ 80 % unchanged. |
| IX. JSON-over-stdout CLI Contract | ✅ | `--json` causes the command to emit exactly one JSON document on stdout (FR-032). Human-readable progress is `rich` to stderr (FR-033). Subprocess tests assert the stdout/stderr split for success and for each named failure mode (`FR-002`, `FR-004`, `FR-007`, `FR-026`, `FR-028`, `FR-029`, `FR-030`, `FR-031`). |
| X. Design Document Axioms | ✅ | The project tree follows § 7 exactly. The two v0 integrations (`claude`, `generic`) are the only options exposed (axiom 7, design § 16.7). `.agents/skills/` is the generic default (axiom 8). Spec Kit is operational reference only — no runtime coupling, no shell-script fallback (axioms 5, 6). |

**Out-of-scope confirmations (Scope & Release Discipline)**:

- No preset system (FR-001 omits `--preset` entirely; the design's `--preset`
  flag is explicitly reserved for v0.2 — design § 5.2).
- No `GrafeoIndexer`. `manifest.indexer` defaults to `"rdflib"` via the
  iteration-2 template; no code path in `init` references Grafeo.
- No integrations beyond `claude` / `generic`. `--integration <unknown>`
  fails with the structured `UnknownIntegrationError` from iteration 3
  (FR-007).
- No extension system, no presets layer in `.bookwright/templates/`.
  `init` populates `.bookwright/templates/` with only the
  iteration-current "core" stubs; iteration 7 fills it.
- No EPUB / PDF export. No `bookwright export` subcommand introduced.

**Gate decision**: PASS, no Complexity Tracking entries required. The
iteration adds no new runtime dependency and introduces no architectural
exception.

**Post-design re-check (after Phase 1 artifacts)**:

| Principle | Re-check | Notes |
|---|---|---|
| All | ✅ | Phase 1 artifacts (`research.md`, `data-model.md`, `contracts/init_command.md`, `quickstart.md`) introduce no new dependencies, no new modules beyond those listed in Project Structure below, and no behaviours beyond the FRs / Acceptance Scenarios in `spec.md`. The init-options envelope schema in `contracts/init_command.md` is the single source of truth for FR-034 — no other artifact restates it. |

## Project Structure

### Documentation (this feature)

```text
specs/004-init-command/
├── plan.md                       # This file (/speckit-plan command output)
├── research.md                   # Phase 0 output (/speckit-plan command)
├── data-model.md                 # Phase 1 output (/speckit-plan command)
├── quickstart.md                 # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── init_command.md           # Phase 1 output (CLI signature + JSON envelopes + init-options schema)
├── checklists/                   # existing (from /speckit-specify + /speckit-clarify)
└── tasks.md                      # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/
├── __init__.py                       # (iter 1)
├── __main__.py                       # (iter 1)
├── cli.py                            # (iter 1) — edit: app.command("init")(init.run)
├── commands/                         # (iter 1)
│   ├── __init__.py                   # (iter 1) — untouched
│   ├── check.py                      # (iter 1) — untouched
│   ├── version.py                    # (iter 1) — untouched
│   ├── init.py                       # NEW — Typer entry + orchestration
│   ├── _init_validate.py             # NEW — PROJECT_NAME validation (FR-021a)
│   ├── _init_resolve.py              # NEW — author / language / slug resolution (FR-016, FR-018, FR-021)
│   ├── _init_scaffold.py             # NEW — template walker + backup ledger (FR-008..FR-014, FR-030)
│   ├── _init_git.py                  # NEW — subprocess wrapper (FR-022..FR-025)
│   └── _init_envelope.py             # NEW — success/error JSON envelopes + init-options.json writer (FR-032..FR-034)
├── core/                             # (iter 2) — untouched
│   └── …
├── integrations/                     # (iter 3) — untouched
│   └── …
└── resources/
    ├── __init__.py                   # (iter 2)
    ├── templates/                    # (iter 2)
    │   ├── __init__.py
    │   ├── manifest.template.toml    # (iter 2) — untouched
    │   └── project/                  # NEW — packaged project tree
    │       ├── __init__.py
    │       ├── README.md.j2          # {{ title }}, {{ project_slug }}, {{ author }}
    │       ├── .gitignore            # literal (entries per § 7.1)
    │       ├── manuscript/
    │       │   └── .gitkeep
    │       ├── bible/
    │       │   ├── constitution.md.j2   # minimal placeholder; full version → iter 7
    │       │   ├── characters/.gitkeep
    │       │   ├── settings/.gitkeep
    │       │   ├── timeline.md          # placeholder
    │       │   ├── relationships.md     # placeholder
    │       │   ├── pov-structure.md     # placeholder
    │       │   ├── themes.md            # placeholder
    │       │   ├── glossary.md          # placeholder
    │       │   ├── research.md          # placeholder
    │       │   └── subplots.md          # placeholder
    │       ├── outline/
    │       │   ├── arcs.md              # placeholder
    │       │   ├── structure.md         # placeholder
    │       │   ├── synopsis.md          # placeholder
    │       │   └── scenes.md            # placeholder
    │       └── .bookwright/
    │           ├── schema/.gitkeep      # iter 5 lands golem.ttl here
    │           ├── vocabularies/        # copied from resources/vocabularies/ at scaffold time
    │           ├── templates/.gitkeep   # iter 7 fills overrides/, etc.
    │           └── cache/.gitkeep       # gitignored (.bookwright/cache/ entry)
    └── vocabularies/                 # NEW — bundled v0 vocabularies (stubs)
        ├── __init__.py
        ├── propp.ttl                 # minimal stub: prefixes + empty class list
        └── greimas.ttl               # minimal stub: prefixes + empty class list

tests/
├── conftest.py                       # (iter 1)
├── test_cli_*.py                     # (iter 1) — untouched
├── test_smoke_import.py              # (iter 1)
├── core/                             # (iter 2) — untouched
├── integrations/                     # (iter 3) — untouched
└── commands/                         # NEW
    ├── __init__.py
    ├── conftest.py                   # shared fixtures: scaffold_in_tmp, git_available, non_interactive
    ├── test_init_default.py          # US1 — `bookwright init mi-libro`
    ├── test_init_here.py             # US2 — `--here`, confirm prompt, --force, already-initialized refusal
    ├── test_init_integrations.py     # US3 — claude / generic / generic+override / unknown / invalid options
    ├── test_init_no_git.py           # US4 — --no-git + git-not-installed warning
    ├── test_init_deprecated_flags.py # US5 — --ai / --ai-skills / --ai-commands-dir
    ├── test_init_validation.py       # FR-021a — name-rule grid
    ├── test_init_rollback.py         # FR-030, SC-005 — directory snapshot pre/post for each failure
    ├── test_init_options_record.py   # FR-034 — schema_version envelope shape (success + every failure)
    ├── test_init_json_envelope.py    # FR-032/33 — subprocess: stdout pure JSON, stderr non-empty on warning
    └── test_init_non_interactive.py  # FR-029 — --here in non-empty + non-TTY refuses
```

**Structure Decision**:

- **One Typer subcommand module** (`commands/init.py`) per Principle IV.
  The five private `_init_*.py` siblings are not subcommands — they are
  the same `commands.init` namespace decomposed for the 500-line ceiling,
  mirroring the iteration-2 `core/_build.py` + `core/_translate.py`
  pattern. No module crosses the ceiling; each is single-purpose.
- **Templates ship as a packaged resource subtree**
  (`src/bookwright/resources/project/`) so iteration 7 can replace the
  bible / outline content without touching the scaffolder. The
  `Jinja2 → byte-copy` walker is the only consumer of the subtree and
  does not enumerate filenames — it walks the resource tree it sees at
  runtime. `.j2` suffix triggers Jinja2; everything else is copied as is.
  Empty directories are kept via `.gitkeep` placeholders, matching the
  design's "directory exists with the expected layout" promise (FR-009,
  FR-010 second clause).
- **Vocabularies live under `resources/vocabularies/`** (NOT inside
  `resources/project/`) so iteration 10 (validation) can index them
  directly from the package without re-reading them through the project
  tree. The scaffolder copies them into the generated
  `.bookwright/vocabularies/` at init time; they are then the project's
  copies and users can edit them. v0 ships minimal Turtle stubs (prefix
  block + one class declaration each); the full vocabularies land
  alongside iteration 10's validators.
- **The integration's skills directory is NOT in the packaged template
  tree.** It is produced by `SkillsIntegration.setup()` (iteration 3),
  called after the rest of the tree is on disk. Both the directory path
  and the marker file are owned by the integration class, exactly as the
  iteration-3 contract requires.
- **Tests mirror sources** (`tests/commands/` mirrors
  `src/bookwright/commands/`). One file per user story plus one file per
  cross-cutting concern (validation grid, rollback grid, init-options
  envelope, JSON envelope subprocess pin, non-interactive refusal).
  In-process Typer invocation via `CliRunner` is the default; subprocess
  invocation is used only for the JSON-stdout-purity tests (Principle IX),
  matching the existing iteration-1 `tests/test_cli_subprocess.py` pattern.

## Complexity Tracking

> No Constitution Check violations. This iteration introduces no
> architectural exception, no new runtime dependency, and no constitutional
> amendment. The table is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| _none_    | _n/a_      | _n/a_                                |
