<!--
Sync Impact Report
==================
Version change: 1.2.0 → 1.3.0
Bump rationale: MINOR — materially expanded guidance in Principle VIII (Test
Discipline). The principle enumerated an end-to-end author workflow
(`init → constitution → bible → outline → scenes → draft`) as if every leg were
an executable CLI command. The authoring legs (`constitution`, `bible`,
`outline`, `scenes`, `draft`) ship as Agent Skills — LLM-driven `SKILL.md`
prompts (Principles VI, X), not CLI commands — so they cannot be driven by an
automated end-to-end CLI test. This amendment clarifies that their E2E
verification is satisfied by agentskills.io materialization compliance
(Principle VII), while the executable surface is exercised through the real
CLI. The coverage bar (≥ 80%) and CI gates are unchanged; no workflow step is
exempted. Surfaced by /speckit-analyze on iteration 011-release-prep
(finding C1): the prior wording forced an inline reinterpretation in plan.md,
which this amendment moves into the binding document.

Principles: VIII reworded (clarification + expanded guidance); I–VII, IX, X
unchanged (no renames, no additions, no removals).

Propagation:
- ✅ Principle VIII text updated in place.
- ✅ .specify/templates/*.md — no change required (no template restates the VIII
  workflow; the plan-template Constitution Check is generic).
- ✅ bookwright-design.md — no change required: line 62 maps the conceptual
  Spec-Kit↔Bookwright flow (not the E2E test mandate) and § 15 ("Tests E2E de
  cada command sobre fixtures") already matches the clarified split; no axiom in
  § 16 is reopened (Principle X), so no design change accompanies this.
- ✅ specs/011-release-prep/plan.md — the "Note on Principle VIII" now cites this
  clarified principle instead of reinterpreting it; the gate reference is bumped
  to v1.3.0.
- ✅ .claude/skills/speckit-*/ — no change required.

History:
- 1.0.0 (2026-05-28): initial ratification (Principles I–X, Technical
  Constraints, Scope & Release Discipline, Governance).
- 1.1.0 (2026-05-28): added `packaging` to the runtime dependency list
  (FR-012, iteration 002-manifest-model; PEP 440 ordering of `cli_version_min`).
- 1.2.0 (2026-06-01): added `pyyaml` (runtime dependency list).
- 1.3.0 (2026-06-03): clarified Principle VIII E2E verification for Agent-Skill
  authoring legs (iteration 011-release-prep, finding C1).
-->

# Bookwright Constitution

Bookwright is a Python toolkit that applies Spec-Driven Development to book
production (novels, essays, memoirs). This constitution defines the
non-negotiable rules that govern every command, integration, skill, validator,
and release. The exhaustive design rationale lives in
[bookwright-design.md](../../bookwright-design.md); when this document and the
design document agree, follow either. When they disagree, this constitution
wins until amended.

## Core Principles

### I. Plain Text as Source of Truth (NON-NEGOTIABLE)

Every artifact that a human author or a downstream tool may need to read,
diff, or recover MUST be Markdown, TOML, or Turtle (RDF). Binary stores,
opaque caches, and embedded databases (SQLite, LevelDB, binary JSON, pickled
indices) are forbidden as canonical storage. Derived caches MAY exist on
disk only if they are deterministically rebuildable from the plain-text
sources and clearly marked as ephemeral.

Rationale: authors must be able to audit, version, and survive the toolkit's
disappearance. Git diffability is a load-bearing feature, not an aesthetic
preference.

### II. Modern Python Stack

The implementation language is Python 3.11+. The required toolchain is:
Typer for the CLI surface, Pydantic v2 for domain models, rdflib for graph
work, Jinja2 for template rendering, hatchling as the build backend, uv as
the package manager and lockfile producer, ruff for lint/format, and mypy in
strict mode for type-checking. Introducing an additional runtime dependency
requires an amendment to the dependency list in the Technical Constraints
section below.

Rationale: a small, opinionated stack is enforceable; an open one is not.

### III. src-layout

All production code MUST live under `src/bookwright/`. All automated tests
MUST live under `tests/`. No production module may be imported from outside
`src/bookwright/`, and no test may live alongside production code. No
exceptions.

Rationale: src-layout makes accidental editable-install shadowing impossible
and keeps packaging behavior identical between local development and PyPI
installs.

### IV. Modular Command Surface

Each CLI subcommand MUST live in its own module under
`src/bookwright/commands/<name>.py` and register itself with the Typer app.
No source file (production or test) may exceed 500 lines; a file approaching
the limit MUST be decomposed before the limit is reached, not after.
Monolithic `cli.py` files that inline subcommand bodies are prohibited.

Rationale: per-command isolation keeps blast radius small, makes tests
addressable, and prevents the slow drift toward a god-module.

### V. Plugin-Based Integrations

Integrations MUST be implemented as subclasses of `SkillsIntegration`
registered in `INTEGRATION_REGISTRY`. The v0 registry ships exactly two
entries — `claude` (writes `.claude/skills/`) and `generic` (writes
`.agents/skills/` by default, configurable via `--skills-dir`). A monolithic
`AGENT_CONFIG`-style dispatcher is explicitly forbidden, even as a
transitional step.

Rationale: Spec Kit already paid the cost of unwinding a monolithic agent
config (issue github/spec-kit#1924). Bookwright starts on the post-refactor
side of that line.

### VI. Agent Skills Only — No Legacy Commands (NON-NEGOTIABLE)

Bookwright MUST emit Agent Skills (`<skills_dir>/<name>/SKILL.md`) and
nothing else. Writing to `.claude/commands/`, `.agents/commands/`, or any
analogous "slash-command-only" directory is prohibited in every integration.
A single SKILL.md per command is the only supported delivery format.

Rationale: Agent Skills give us progressive disclosure, cross-agent
portability (Claude Code, Codex, Cursor, Copilot, Gemini, ...), and
structural validation against an open standard. Legacy command directories
give us none of those.

### VII. agentskills.io Standard Compliance

Every generated `SKILL.md` MUST satisfy the agentskills.io specification:
valid YAML frontmatter; `name` < 64 characters and exactly matching the
parent directory name; `description` < 1024 characters; body content
optimized for the three-tier progressive-disclosure model (metadata →
instructions → resources). Long reference material MUST be offloaded to
`references/` rather than inlined to keep the SKILL.md body within the
standard's working budget. Skill generation MUST fail loudly (non-zero exit,
JSON error on stdout) when a generated skill would violate any of these
constraints — silent truncation or auto-fixing is forbidden.

Rationale: compliance is what makes Bookwright projects portable across the
25+ agents that consume the standard. A skill that "almost" complies is a
liability.

### VIII. Test Discipline (NON-NEGOTIABLE)

Tests are mandatory, not optional. v0 MUST hold a minimum of 80% line
coverage across `src/bookwright/`. The test pyramid is enforced: unit tests
for `core/`, `golem/`, `integrations/`, and `validation/`; integration tests
for command flows (`init`, `graph build`, `validate`); end-to-end tests for
the full author workflow (`init → constitution → bible → outline → scenes →
draft`) against the `tiny-novel/` fixture. Because the authoring legs of that
workflow (`constitution`, `bible`, `outline`, `scenes`, `draft`) ship as Agent
Skills — LLM-driven `SKILL.md` prompts (Principles VI, X), not executable CLI
commands — their end-to-end verification is satisfied by **agentskills.io
materialization compliance** (every authoring skill is generated and passes the
shipped `lint_skill_md` gate, Principle VII), while the executable surface
(`init → graph build → graph query → validate`) is exercised end-to-end through
the real CLI. This split is the only sound verification mode given the
skill/CLI boundary; it neither lowers the coverage bar nor exempts any workflow
step. CI MUST run pytest, ruff, and mypy strict on every push and pull request;
a red bar blocks merge.

Rationale: a documented domain model and a graph validator only earn trust
when their assertions are themselves asserted.

### IX. JSON-over-stdout CLI Contract

Any CLI command whose output is meant to be consumed by an AI agent MUST
accept a `--json` flag and, when set, emit a single well-formed JSON
document on stdout and nothing else. Human-readable progress, warnings, and
diagnostics MUST go to stderr. Mixing JSON and human prose on stdout is a
contract violation and MUST fail tests. Exit codes MUST be non-zero on
error even when `--json` is set; the JSON body carries the structured error
detail.

Rationale: the SKILL.md ↔ CLI boundary is the only stable contract between
Bookwright and the agent. Polluting stdout breaks every downstream parser.

### X. Design Document Axioms

Section 16 of [bookwright-design.md](../../bookwright-design.md) enumerates
decisions that are closed: Python over Rust/TypeScript; rdflib over Grafeo
in v0; GOLEM as the ontology; plain text over binary stores; Spec Kit as
operational reference without runtime coupling; no shell scripts; Agent
Skills only; `.agents/skills/` as the generic default; Bookwright as a
standalone toolkit (not a Spec Kit preset or extension); plugin-based
integrations from day one. These MUST NOT be reopened in spec, plan, or
task discussions. Reopening one requires a constitutional amendment AND a
matching update to design Section 16, in the same change.

Rationale: agents and contributors waste cycles relitigating settled
decisions. Naming the axioms eliminates that loop.

## Technical Constraints

The following are binding constraints on the v0 implementation. Changes
require a MINOR (additions) or MAJOR (removals / incompatible swaps)
constitutional bump.

- **Language**: Python 3.11+ only. No support for 3.10 or earlier.
- **Runtime dependencies (minimum set)**: `jinja2`, `packaging`,
  `platformdirs`, `pydantic` (v2), `python-slugify`, `pyyaml`, `rdflib`,
  `rich`, `tomlkit`, `typer`, `uuid-utils`. Adding to this list requires a
  MINOR amendment; removing or swapping requires a MAJOR amendment.
- **Build backend**: `hatchling`. **Lockfile**: `uv.lock` committed to the
  repository.
- **Distribution**: PyPI package name `bookwright-cli`. Release tags follow
  semver `v0.X.Y`.
- **CI**: GitHub Actions matrix runs `pytest`, `ruff check`, `ruff format
  --check`, and `mypy --strict` on every push and pull request. All four
  MUST pass before merge.

## Scope & Release Discipline

The v0 line ships exactly the M0–M3 milestones described in design § 15.
The following capabilities are deliberately deferred and MUST NOT be pulled
into v0 scope:

- **Preset system** (genre packages, template overlays) — v0.2.
- **`GrafeoIndexer`** and vector search — v0.3.
- **Multi-integration beyond `claude` and `generic`** (Copilot, Gemini,
  Cursor-specific, etc.) — v0.4.
- **Extension system** (distributable validators, pre-commit hooks) — v0.5.
- **Export to EPUB / PDF / print** (pandoc pipeline) — v1.0.

A pull request that introduces any of the deferred capabilities, or that
adds plumbing whose only justification is "future preset support", MUST be
rejected at review or split out into a post-v0 branch. Speculative
generality is treated as a violation of this constitution.

## Governance

This constitution supersedes all other internal practice documents,
including in-line code conventions and per-feature design notes. When a
spec, plan, or task conflicts with this document, the constitution wins and
the conflicting artifact MUST be amended.

**Amendment procedure**: Amendments are proposed in a dedicated pull request
that updates `.specify/memory/constitution.md`, bumps the version line,
updates the Sync Impact Report at the top of this file, and propagates any
required changes to `.specify/templates/*.md` and (when applicable)
[bookwright-design.md](../../bookwright-design.md) § 16. The PR description
MUST state the bump type (MAJOR / MINOR / PATCH) and its rationale.

**Versioning policy**: Semantic versioning applied to this document.
- **MAJOR**: backward-incompatible removal or redefinition of a principle,
  removal of a runtime dependency, or change to the agentskills.io
  compliance contract.
- **MINOR**: new principle, new section, materially expanded guidance, or
  addition to the runtime dependency list.
- **PATCH**: clarifications, typo fixes, rewording without semantic change.

**Compliance review**: every pull request MUST be reviewed against the
principles above. `/speckit-plan` and `/speckit-analyze` runs use this file
as the Constitution Check gate; violations surfaced there block merge until
either the code is fixed or the constitution is amended through the
procedure above. The CI pipeline (Principle VIII) is the automated half of
this gate; human review covers the rest.

**Version**: 1.3.0 | **Ratified**: 2026-05-28 | **Last Amended**: 2026-06-03
