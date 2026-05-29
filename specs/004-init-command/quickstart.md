# Quickstart: `bookwright init`

**Branch**: `004-init-command` | **Date**: 2026-05-29 |
**Plan**: [plan.md](plan.md) | **Contract**: [contracts/init_command.md](contracts/init_command.md)

This iteration ships the first user-facing command. Unlike iteration 3 —
which was a library iteration with no CLI surface — this quickstart is for
**end users** scaffolding a new book project, plus a short coda for
implementers exercising the test suite.

If you are upgrading from an earlier internal build, jump to the
[Migration notes](#migration-notes) section.

---

## Prerequisites

- Python 3.11+.
- `uv` installed (`pipx install uv` or `brew install uv`).
- `git` on `$PATH` if you want the automatic initial commit. Bookwright
  works without git but will warn (see [`--no-git` / no git on PATH](#no-git--no-git-on-path)).
- The Bookwright CLI installed in editable mode:

  ```bash
  git checkout 004-init-command
  uv sync
  ```

  Verify the install:

  ```bash
  uv run bookwright check
  uv run bookwright version
  ```

  Both come from earlier iterations and should report all-green before
  trying `init`.

---

## 1. Scaffold a new project (default path)

```bash
uv run bookwright init mi-libro
```

What this does:

- Creates `./mi-libro/` (`mi-libro` is the slugified directory name).
- Writes `manifest.toml` with:
  - `book.title = "mi-libro"` (preserves your casing — pass
    `"Mi Libro"` and the title is `"Mi Libro"`, the directory is still
    `mi-libro/`).
  - `book.authors` resolved from `git config user.name`, falling back
    to `$USER`, falling back to `"Unknown Author"` (with a stderr
    warning if the fallback ran).
  - `book.language` detected from your host locale, falling back to
    `"es"`.
  - `book.type = "novel"`, `book.status = "idea"`.
  - `integration.key = "claude"` with `integration.skills_dir =
    ".claude/skills"` (the default integration in v0).
- Populates `bible/`, `outline/`, `manuscript/` (empty placeholder),
  and `.bookwright/` with the iteration-current templates.
- Installs the Claude integration's skills directory at
  `.claude/skills/` with the iteration-3 placeholder marker (real
  `SKILL.md` files land in iteration 9).
- Initialises git and creates exactly one commit titled
  `Initial commit from bookwright init` with every generated file
  staged.

Confirm:

```bash
cd mi-libro
ls
# bible/  manuscript/  outline/  .bookwright/  .claude/  .gitignore  README.md  manifest.toml

git log --oneline
# <hash> Initial commit from bookwright init

git status
# nothing to commit, working tree clean
```

---

## 2. Scaffold in the current directory

When you've already `mkdir`'d the project (or your publisher seeded a
directory for you), use `--here`:

```bash
mkdir mi-libro && cd mi-libro
uv run bookwright init --here
```

`book.title` is taken from the current directory's basename. Everything
else behaves identically to § 1.

**If the directory is non-empty**, `--here` prompts:

```text
bookwright: directory '/abs/path' is not empty. Overwrite name collisions? [y/N]
```

- Answer `y` to proceed (and any pre-existing file with a colliding
  name is backed up before being overwritten — see § 6).
- Answer `N` (or anything not starting with `y`/`Y`) to abort. Nothing
  is written.
- If you pre-set `--force`, the prompt is skipped.
- If stdin/stdout is not a TTY, or `--json` is set, the prompt is
  refused entirely — pass `--force` to proceed non-interactively.

**If the directory already contains `.bookwright/`**, the command
refuses — `--force` does NOT override this. Use a different directory
or remove `.bookwright/` deliberately.

---

## 3. Choose a different integration

Default is Claude Code. To target a different agent, pass
`--integration generic`:

```bash
uv run bookwright init mi-libro --integration generic
# → skills land in .agents/skills/
```

To override where `generic` writes its skills (Cursor convention,
say):

```bash
uv run bookwright init mi-libro \
  --integration generic \
  --integration-options="--skills-dir .cursor/skills"
# → skills land in .cursor/skills/
```

The `--integration-options` string is tokenised with POSIX shell rules
(quoted values with spaces are fine), then forwarded to the
integration's option parser. Unknown flags fail loudly:

```bash
uv run bookwright init mi-libro --integration generic \
  --integration-options="--cursor-dir .cursor/skills"
# bookwright: error: unknown option --cursor-dir for integration 'generic'; valid: [--skills-dir]
# (exit 5)
```

An unknown integration key fails with the list of valid keys:

```bash
uv run bookwright init mi-libro --integration copilot
# bookwright: error: unknown integration: 'copilot'; valid: [claude, generic]
# (exit 5)
```

---

## 4. `--no-git` / no git on PATH

To deliberately skip git (e.g., scaffolding inside an existing
monorepo):

```bash
uv run bookwright init mi-libro --no-git
```

No `.git/` is created, no commit is made, and the success report
explicitly notes git was skipped.

If `git` is not on `$PATH` and you didn't pass `--no-git`, scaffolding
still completes successfully, you get a stderr warning, and no
repository is created:

```bash
uv run bookwright init mi-libro
# bookwright: warning: git not found on PATH; project created without a repository
# (exit 0)
```

If `--here` lands inside an existing repository (a `.git/` somewhere up
the tree), Bookwright leaves that repository untouched and emits a
warning:

```bash
cd existing-monorepo/books/
uv run bookwright init --here
# bookwright: warning: existing .git/ detected; skipped git init and commit
```

---

## 5. JSON output for agent consumers

Pass `--json` to get a single structured document on stdout. Useful when
an agent invokes `init` and needs to parse the result:

```bash
uv run bookwright init mi-libro --json
```

```json
{"status":"ok","project_root":"/abs/path/mi-libro","project_slug":"mi-libro","mode":"named","integration":{"key":"claude","skills_dir":".claude/skills","options":{}},"git_status":"initialized","warnings":[],"bookwright_version":"0.0.1"}
```

The exact envelope shape (success + every error case) is pinned in
[contracts/init_command.md](contracts/init_command.md).

Warnings still go to stderr under `--json`; the JSON copy in the
`warnings` array is for agents that don't read stderr.

---

## 6. Failure modes (what they look like, what to do)

| You ran                                                | You see (stderr, no `--json`)                                                                  | Exit | Fix                                                                                 |
|--------------------------------------------------------|------------------------------------------------------------------------------------------------|------|-------------------------------------------------------------------------------------|
| `bookwright init` (no name, no `--here`)               | `error: must specify PROJECT_NAME or --here, not both`                                         | 2    | Pass one of the two.                                                                |
| `bookwright init mi-libro --here`                      | `error: PROJECT_NAME and --here are mutually exclusive`                                        | 2    | Drop one of them.                                                                   |
| `bookwright init './..'`                               | `error: invalid project name '../'; rule: path_separator`                                      | 2    | Pick a portable name (no `/` `\` `.` `..`, no leading dot, ≤ 100 chars).             |
| `bookwright init mi-libro --ai-skills`                 | `error: --ai-skills is no longer accepted; Agent Skills is now the only output mode`           | 2    | Drop the flag (Bookwright only writes Agent Skills).                                |
| `bookwright init mi-libro --ai-commands-dir x`         | `error: --ai-commands-dir is no longer accepted; for generic, use --integration-options="--skills-dir <path>"` | 2 | Use the modern form.                                                                |
| `bookwright init mi-libro --integration copilot`       | `error: unknown integration: 'copilot'; valid: [claude, generic]`                              | 5    | Pick a valid integration key.                                                       |
| `bookwright init existing-non-empty-dir`               | `error: directory 'existing-non-empty-dir' is not empty; use --force to overwrite or --here to initialise in place` | 4 | Pass `--force` or `--here`, or pick a different name.                               |
| `bookwright init --here` inside `.bookwright/`-bearing dir | `error: directory '/abs/path' is already a Bookwright project (found .bookwright/)`            | 3    | Pick a different directory or remove `.bookwright/`.                                |
| `bookwright init --here` in non-TTY non-empty dir      | `error: --here in a non-empty directory requires --force in non-interactive runs`              | 4    | Pass `--force`.                                                                     |
| `--ai claude` (deprecated)                             | `warning: --ai is deprecated; use --integration instead` (and the command succeeds)            | 0    | Migrate to `--integration`.                                                          |

For every failure case, **the target directory is byte-for-byte
unchanged from its pre-invocation state** — every pre-existing file is
restored from a sibling backup if it was about to be overwritten, and
every newly created file is removed. The success/failure rollback story
is verified by the test grid in `tests/commands/test_init_rollback.py`.

---

## Migration notes

Coming from an earlier internal build that used the Spec-Kit-style
flag set:

| Old flag                                   | New form                                                              |
|--------------------------------------------|-----------------------------------------------------------------------|
| `bookwright init … --ai claude`            | `bookwright init … --integration claude` (the old form still works with a deprecation warning) |
| `bookwright init … --ai-skills`            | (removed; Agent Skills is the only output mode — drop the flag)        |
| `bookwright init … --ai-commands-dir x`    | `bookwright init … --integration-options="--skills-dir x"` (only for `generic`) |

---

## For implementers

```bash
git checkout 004-init-command
uv sync
uv run pytest tests/commands/ -v
```

The test suite includes:

- `test_init_default.py` — US1 default path (named mode, Claude).
- `test_init_here.py` — US2 `--here` matrix (empty / non-empty +
  prompt / non-empty + `--force` / `.bookwright/` refusal / `--here`
  with `PROJECT_NAME` mutex).
- `test_init_integrations.py` — US3 (claude / generic / generic +
  override / unknown key / invalid options).
- `test_init_no_git.py` — US4 (`--no-git` + git-not-found warning).
- `test_init_deprecated_flags.py` — US5 (`--ai` warning, `--ai-skills`
  / `--ai-commands-dir` removal).
- `test_init_validation.py` — FR-021a name-rule grid.
- `test_init_rollback.py` — FR-030 atomic-or-nothing grid (one
  parametrized case per documented failure mode).
- `test_init_options_record.py` — FR-034 envelope shape across every
  CLI flag combination the user-story tests exercise.
- `test_init_json_envelope.py` — subprocess pin: stdout pure JSON,
  stderr only warnings (Principle IX).
- `test_init_non_interactive.py` — FR-029 refusal under
  non-TTY + `--here` + non-empty.

Run a single test:

```bash
uv run pytest tests/commands/test_init_rollback.py::test_target_unchanged_on_unknown_integration -v
```

The full quality gate before opening a PR:

```bash
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy --strict src tests
```

All four must be green. CI runs the same matrix on every push.

---

## What this iteration deliberately does NOT do

- **Render the bible / outline templates fully.** They are minimal
  placeholders in this iteration. Iteration 7 (`bookwright-design.md`
  § 9 onward) lands the full templates. The scaffolder walks the
  resource tree by shape, not by enumerated filename, so iteration 7
  swaps content without touching the walker.
- **Materialize per-command `SKILL.md` files.** The integration's
  `setup()` writes only the placeholder marker (iteration 3 contract).
  Iteration 9 swaps the placeholder for real `SKILL.md` files.
- **Run validators on the freshly scaffolded project.** Iteration 10
  introduces the validator engine and the `bookwright validate`
  subcommand.
- **Support `--preset`, `--script`, or any other v0.2+ flag from design
  § 5.2.** They are explicitly out of v0 scope.
