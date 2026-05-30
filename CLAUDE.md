# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state: pre-implementation

There is **no Python source code in this repo yet**. The implementation has
not started. What exists:

- `bookwright-design.md` (Spanish, ~74 KB) — canonical design spec. Section
  numbering is load-bearing; iteration prompts reference it as
  `bookwright-design.md § N.M`. Section 16 lists axiomatic decisions that
  MUST NOT be reopened.
- `bookwright-implementation-plan.md` (Spanish, ~45 KB) — ordered iteration
  plan. Section 2 has the dependency map; sections 3+ have one
  ready-to-paste `/speckit-specify` prompt per iteration.
- `.specify/memory/constitution.md` — ratified v1.0.0. **Binding** on every
  PR. Three principles are explicitly NON-NEGOTIABLE: plain-text source of
  truth (I), Agent Skills only — no legacy `commands/` directories (VI),
  and test discipline with ≥80 % coverage (VIII).
- `.specify/` — Spec Kit scaffolding (templates, hook config in
  `extensions.yml`, the git extension scripts).
- `.claude/skills/speckit-*` — the 14 Spec Kit slash-command skills that
  drive the workflow.

Implementation lives in the future. Every feature lands through a numbered
iteration from the implementation plan, not as a freehand commit.

## How work is done here

The project is built **with** Spec Kit, **for** narrative authoring. Every
iteration runs this fixed sequence — do not skip steps, do not write code
directly outside this flow:

```
/speckit-specify <iteration prompt from bookwright-implementation-plan.md>
/speckit-clarify          # mandatory; say "no clarifications" to unblock if truly none
/speckit-plan <technical hint, usually a pointer into bookwright-design.md §X.Y>
/speckit-tasks
/speckit-analyze          # cross-artifact consistency check
/speckit-implement
```

Each iteration produces a feature branch `NNN-<short-name>` with its own
`specs/NNN-<short-name>/{spec,plan,tasks}.md`. Merge to `main` only when
tests are green and `/speckit-analyze` reports no issues; subsequent
iterations assume earlier code is on `main`.

The auto-git hooks in `.specify/extensions.yml` will offer to commit
between phases. `before_constitution` and `before_specify` are mandatory
(`optional: false`); the rest are optional prompts.

## Iteration order (do not reorder)

From `bookwright-implementation-plan.md` § 2:

| # | Iteration | Depends on | Milestone |
|---|---|---|---|
| 1 | Bootstrap repo + empty CLI | — | M0 |
| 2 | Manifest model | 1 | M0 |
| 3 | Integration architecture | 1, 2 | M0 |
| 4 | `bookwright init` command | 1, 2, 3 | M0 |
| 5 | GOLEM domain model | 1 | M1 |
| 6 | Graph indexer + `graph` commands | 5 | M1 |
| 7 | Bible / outline / constitution templates | 4 | M2 |
| 8 | Author the 10 source commands | 7 | M2 |
| 9 | Materialize commands as Agent Skills | 3, 8 | M2 |
| 10 | Validation system | 6, 9 | M3 |
| 11 | Fixtures + E2E tests + docs | 1–10 | M3 |

When a `/speckit-specify` prompt references `§ 6`, `§ 11`, `§ 15.1`, etc.,
that's a section in `bookwright-design.md`. Open it.

## Stack the implementation MUST use

Locked by Constitution Principle II and the Technical Constraints section.
Substituting any of these requires a constitutional amendment:

- **Language**: Python 3.11+ only.
- **Package manager / lockfile**: `uv` + committed `uv.lock`.
- **Build backend**: `hatchling`.
- **Runtime deps (minimum set, in this order)**: `typer`, `rich`, `rdflib`,
  `pydantic` (v2), `tomlkit`, `jinja2`, `python-slugify`, `platformdirs`,
  `uuid-utils`. Note: `uuid-utils`, **not** `uuid7` — the plan was already
  re-aligned to this in commit `4debfc9`.
- **Layout**: `src/bookwright/…` for production code, `tests/` at the root.
  No exceptions (Principle III).
- **Per-command modules**: each CLI subcommand in its own file under
  `src/bookwright/commands/<name>.py`, ≤500 lines (Principle IV).
- **Lint / type / test**: `ruff check`, `ruff format --check`,
  `mypy --strict`, `pytest`. All four are CI gates on every push / PR.

Once iteration 1 lands, the canonical commands will be:

```
uv sync                          # install deps into .venv
uv run bookwright <subcommand>   # run the CLI
uv run pytest                    # full test suite
uv run pytest tests/path/to/test_file.py::test_name   # single test
uv run ruff check && uv run ruff format --check
uv run mypy --strict src tests
```

Until iteration 1 merges, none of those commands work — there is no
`pyproject.toml` yet.

## Domain knobs you will encounter

- **Integrations**: only `claude` (writes `.claude/skills/`) and `generic`
  (writes `.agents/skills/` by default) ship in v0. A monolithic
  `AGENT_CONFIG`-style dispatcher is forbidden — use the
  `SkillsIntegration` + `INTEGRATION_REGISTRY` plugin shape (Principle V).
- **Agent Skills, never legacy commands**: the toolkit MUST emit one
  `SKILL.md` per command under the integration's `skills_dir`. Writing to
  `.claude/commands/` or analogous directories is a Principle VI violation
  and will block merge (Principle VII enforces agentskills.io constraints:
  `name` ≤ 64 chars matching its parent directory, `description` ≤ 1024
  chars, valid YAML frontmatter).
- **JSON-over-stdout contract**: any subcommand consumed by an agent
  accepts `--json` and, when set, emits a single JSON document on stdout
  and **only** that. Human prose / progress goes to stderr (Principle IX).
- **Domain model**: GOLEM ontology, serialized as Turtle (RDF). `rdflib`
  in v0; `Grafeo` is deferred to v0.3 and MUST NOT be pulled forward.

## Out of v0 scope — do not implement these

From the Constitution's Scope & Release Discipline section. A PR that adds
plumbing whose only justification is "future X" MUST be rejected:

- Preset / genre-package system → v0.2
- `GrafeoIndexer`, vector search → v0.3
- Integrations beyond `claude` / `generic` (Copilot, Gemini, Cursor-specific)
  → v0.4
- Extension system (distributable validators, pre-commit hooks) → v0.5
- Export to EPUB / PDF / print via pandoc → v1.0

## Language conventions

- The two design documents (`bookwright-design.md`,
  `bookwright-implementation-plan.md`) are written in **Spanish**. Keep
  edits to them in Spanish; the user authored them deliberately in that
  language.
- Source code, identifiers, commit messages, and the constitution itself
  are in **English**.

## Spec Kit specifics worth knowing

- Pinned at `v0.8.16` stable (commit `ffa1a45`). Don't upgrade without a
  reason that's worth chasing template churn.
- Skill names are hyphenated (`speckit-plan`, not `speckit.plan`). The
  `extensions.yml` hook entries still use dot form (`speckit.git.commit`);
  the dispatcher converts dots to hyphens when invoking.
- `.specify/extensions.yml` `auto_execute_hooks: true` is on. Mandatory
  hooks (`before_constitution`, `before_specify`) execute without
  prompting; optional ones (commit hooks) ask first.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
[specs/005-golem-domain-model/plan.md](specs/005-golem-domain-model/plan.md)
<!-- SPECKIT END -->
