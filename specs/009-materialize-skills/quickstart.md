# Quickstart: Materialize commands as Agent Skills (iteration 9)

## What this iteration delivers

`bookwright init` now produces **ready-to-invoke Agent Skills**: one
`<skills_dir>/<command>/SKILL.md` per source command, each agentskills.io-compliant,
with cited `references/` copied alongside. Re-running `init` never overwrites a skill
you edited.

## Try it (Claude integration)

```bash
uv run bookwright init --title "My Novel" --integration claude   # in an empty dir
ls .claude/skills/                       # one dir per command
cat .claude/skills/bookwright-constitution/SKILL.md
ls .claude/skills/bookwright-bible/references/   # cited refs copied per-skill
```

Each `SKILL.md` has frontmatter:

```yaml
---
name: bookwright-constitution        # == parent directory
description: |-                      # authoritative bilingual triggers, < 1024 chars
  Define la constitución narrativa … / Build the book's narrative constitution …
license: Apache-2.0
metadata:
  author: bookwright
  version: 0.0.1                      # == installed CLI version
---
```

…and a body that is the source body with every `{ARGS}` replaced by `$ARGUMENTS` and
inline `bookwright graph build --json` calls intact. No `!`shell`` injection, no
`.bookwright/scripts/` wrappers.

## Generic integration / re-targeted dir

```bash
uv run bookwright init --title X --integration generic                       # .agents/skills/
uv run bookwright init --title X --integration generic --skills-dir .cursor/skills
```

Output is standard-only (identical bodies, different `skills_dir`).

## Idempotency

Materialization is idempotent **per `SKILL.md`**: an existing skill file is never
overwritten (your edits survive), while a deleted skill is regenerated in full.

Note that `bookwright init` is single-shot per project — re-running it on a project
that already has `.bookwright/` returns `{"code": "already_initialized"}` and writes
nothing. The idempotency guard takes effect whenever materialization runs **again** —
e.g. after de-initializing (removing `.bookwright/`) and re-running `init`, or a future
re-scaffold/sync:

```bash
uv run bookwright init my-novel                # materializes skills
$EDITOR my-novel/.claude/skills/bookwright-bible/SKILL.md   # tweak a step
rm -rf my-novel/.claude/skills/bookwright-draft/            # delete one
rm -rf my-novel/.bookwright/                   # de-initialize so init will run again
uv run bookwright init my-novel --force        # bible edit preserved; only bookwright-draft regenerated
```

## Run the tests

```bash
uv run pytest tests/integrations/test_materialize.py \
              tests/integrations/test_skill_lint.py \
              tests/integrations/test_materialize_idempotent.py \
              tests/integrations/test_setup_materialize.py -q
uv run pytest tests/commands/init/ -q          # E2E: every generated SKILL.md lints clean
uv run ruff check && uv run ruff format --check && uv run mypy --strict src tests
```

## Failure you should see (hard abort)

If a generated skill would violate the spec (e.g. an over-cap description), `init`
aborts that integration with a structured error and leaves **no** invalid `SKILL.md`
on disk:

```json
{"code": "skill_lint_failed", "skill": "bookwright-bible",
 "rule": "description_too_long", "detail": "len=1102 ≥ 1024"}
```

## Where the code lives

- `src/bookwright/integrations/base.py` — `SkillsIntegration` contract + one shared
  `setup()` (no subclass overrides).
- `src/bookwright/integrations/materialize.py` — `generate_skill_md`, roster iteration,
  body transform, frontmatter render, reference copy.
- `src/bookwright/integrations/lint.py` — `lint_skill_md`, `approx_tokens`.
- `src/bookwright/integrations/descriptions.py` — `SKILL_DESCRIPTIONS` + `get_description`.
- `src/bookwright/integrations/{claude,generic}/__init__.py` — class vars only.
- `src/bookwright/io/fs.py` — `FileLedger` protocol + `NullLedger` + `BackupLedger` +
  `mkdir_tracked`/`write_bytes_atomic` (extracted from `init/scaffold.py`); `setup()`
  records every materialized path here so a failed `init` rolls them back.
- `src/bookwright/resources/commands/` — read-only source roster (iteration 8).
