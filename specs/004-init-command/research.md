# Phase 0 — Research: `bookwright init` Command

**Branch**: `004-init-command` | **Date**: 2026-05-29 |
**Plan**: [plan.md](plan.md)

The spec has no `NEEDS CLARIFICATION` markers — the five
`/speckit-clarify` answers recorded in `spec.md` § Clarifications closed
the open questions before planning began. The questions resolved here are
*design choices the implementer needs answers to* before writing code, not
unresolved unknowns from the spec.

Each entry follows the format:

- **Decision** — what was chosen.
- **Rationale** — why, grounded in spec FRs / constitution / design.
- **Alternatives considered** — what else was on the table and why
  rejected.

---

## R1. Author resolution order (FR-016)

**Decision**: Resolve `book.authors` in this exact order, stopping at the
first non-empty hit:

1. `git config --get user.name` (run with the project root as `cwd` so a
   per-repo override wins over the global config; falls back to the global
   when no per-repo entry exists).
2. `$USER` environment variable.
3. Sentinel `"Unknown Author"`, with the one-line stderr warning
   canonicalised in [contracts/init_command.md](../contracts/init_command.md)
   § 5 (Author resolution row) so the user knows what to edit. The text
   is fixed at the contract layer; this research document does not
   re-define it.

The warning is emitted whenever step 3 is reached (per FR-016), regardless
of `--json`. With `--json` the warning still lands on stderr; stdout
remains a single JSON document.

**Rationale**:

- The design (§ 5.2, § 8.1) leaves the precise mechanism to the planner;
  the spec FR-016 names exactly the (git → env → fallback) ordering and
  the stderr-on-fallback requirement.
- Git is the most accurate source of "the human who is going to author
  this book in this repo" — it already encodes per-repo overrides via
  `git config --local`. Running it with `cwd=project_root` for the
  directory-form invocation, or `cwd=Path.cwd()` for `--here`, means a
  user who has a different identity per project gets it without having
  to re-set `$USER`.
- `$USER` is a coarse fallback; it survives in non-git environments (CI
  runners, fresh containers).
- The sentinel string is documented (FR-016 + Edge Cases) so downstream
  consumers can detect it without parsing prose.

**Alternatives considered**:

- **Reverse the order (`$USER` first)**: rejected. `$USER` is set on
  every shell session and would mask any per-repo git override the user
  set deliberately.
- **Read `pwd.getpwuid(os.getuid()).pw_gecos`** (the GECOS comment field):
  rejected. Portability is poor (Windows), the field is often blank, and
  it adds no value over `$USER`.
- **Prompt interactively**: rejected. FR-029 already restricts when
  prompting is allowed; expanding prompts for author detection would push
  every CI run through `--force` or a non-default flag.

---

## R2. Host-locale → `book.language` detection (FR-018)

**Decision**: Use `locale.getlocale()`; if the language part is a valid
ISO 639-1 two-letter code (per the existing iter-2 `ISO_639_1_CODES` set
in `bookwright.core.iso639_1`), use it lower-cased. Otherwise, fall back
silently to `"es"`. Do NOT call `locale.setlocale(...)` (it mutates global
state) and do NOT trust `$LANG` directly (parse via `locale.getlocale()`
which handles both `LC_ALL` and `LANG` precedence).

**Rationale**:

- The iteration-2 `BookBlock.language` validator already rejects anything
  outside `ISO_639_1_CODES` with a Pydantic-friendly error. So the only
  values worth emitting from the detector are codes that will pass that
  validator.
- The design's stated fallback is `"es"`. The user's locale could be
  e.g. `es_ES`, `en_US`, `pt_BR`, etc.; we take only the two-letter prefix
  and check membership in the validator's set.
- "Silent fallback" matches the spec's Edge Case ("Language cannot be
  detected: the manifest is written with `language = 'es'` per the
  design's default") — no warning needed.

**Alternatives considered**:

- **Read `$LANG` directly**: rejected. `LC_ALL` overrides `LANG`;
  re-implementing the precedence rules is what `locale.getlocale()`
  already does.
- **Use `babel.default_locale`**: rejected. Adds a runtime dependency
  (not in Constitution Technical Constraints) for one-line behaviour.
- **Always default to `"es"` regardless**: rejected. The spec lists
  detection as the primary path and the default as the fallback.

---

## R3. `PROJECT_NAME` → directory slug + `book.title` preservation (FR-021)

**Decision**: `book.title` is the raw `PROJECT_NAME` after the FR-021a
validation passes (Unicode preserved, casing preserved, leading/trailing
whitespace stripped). The on-disk directory name is
`slugify(PROJECT_NAME, lowercase=True, separator="-", allow_unicode=False,
regex_pattern=r"[^A-Za-z0-9]+")` from `python-slugify`. The slug is then
re-checked against the FR-021a reserved-name list (so a name that
slugified to `"con"` on Windows still trips). Empty slug after
transliteration → FR-021a `"empty"` rule.

For the `--here` invocation, `book.title` is the current directory's
`basename` (also passed through the FR-021a rules for symmetry — but only
the `empty`, `path-separator`, and reserved-name rules apply; a directory
already on disk is not subject to the length cap).

**Rationale**:

- `python-slugify` is already in the Constitution-locked dependency list;
  no new dependency needed.
- `allow_unicode=False` means accented characters transliterate to ASCII
  (e.g., `á` → `a`, `ñ` → `n`), which keeps the directory name portable
  across filesystems while the manifest's `title` still preserves the
  authoring intent (the spec's Acceptance Scenario 3).
- Re-checking the slug against the reserved-name list closes a
  Windows portability hole: `con-fictions` slugifies to `con-fictions`
  (fine), but a name that slugifies to exactly `con` would be a Windows
  reserved name.

**Alternatives considered**:

- **Roll our own slugifier**: rejected. `python-slugify` handles the
  Unicode normalization step (`unicodedata.normalize("NFKD", ...)`) the
  spec implies and is already paid for.
- **Use the title verbatim as the directory name**: rejected. Files with
  spaces, accents, and uppercase letters in their path are a usability
  hazard across shells and CI runners.
- **Strict ASCII without transliteration**: rejected. A user who supplies
  `"Café-Society"` should get `"cafe-society"` on disk, not be forced to
  rename.

---

## R4. Backup-and-rollback ledger (FR-030)

**Decision**: One in-memory ledger lives for the duration of the command.
Each filesystem mutation goes through one writer (`_init_scaffold.write`)
that:

1. Resolves the absolute target path (and confirms it is inside the
   project root — refuse otherwise).
2. If the target exists, copies it to a per-invocation backup directory
   under `<project_root>/.bookwright/cache/backup/<token>/<rel_path>`
   (where `<token> = secrets.token_hex(6)` per overwrite, and
   `<rel_path> = target.relative_to(project_root)`) via `shutil.copy2`
   (preserves mode + mtime). On copy failure, abort (the FR-030 last
   sentence: "If a backup cannot be created (e.g. permission denied), the
   overwrite MUST NOT proceed").
3. Appends `(target, backup_path or None)` to the ledger.
4. Writes the new bytes via `os.replace(tempfile, target)` so the write
   itself is atomic on POSIX.

On success: the ledger is walked and every `backup_path` is `unlink`-ed.
On any exception: the ledger is walked in reverse — entries with
`backup_path is None` are `unlink`-ed (newly created); entries with a
backup are restored via `shutil.move(backup_path, target)`. For
directory-form invocations where the entire `project_root` was newly
created by this command, an outer `try/except` removes the freshly
created `project_root` after the ledger replay (so a "couldn't even
create the manifest" failure leaves nothing behind, matching SC-005).

Backup files live under `.bookwright/cache/backup/` (which is excluded
from git by the generated `.gitignore` — see spec § Assumptions). This
keeps `git add .` from staging the backups during the initial commit
(FR-022, SC-004). The `<token>` segment also disambiguates parallel
overwrites of the same path.

**Rationale**:

- Per-file backup is the only mechanism that satisfies the spec's
  Session 2026-05-29 clarification (Q4: "best-effort restore … on
  rollback, originals are restored from the backup; on success, the
  backups are deleted"). A whole-directory tarball would also work but
  is heavier and harder to inspect under test.
- `os.replace` is the standard atomic-file primitive; `tomlkit.dump`
  already uses the same pattern (`tempfile + fsync + os.replace`) in
  `Manifest.dump`. Reusing that pattern keeps the on-disk semantics
  consistent.
- `shutil.copy2` preserves mode + mtime so a restored file is
  indistinguishable from the original (the spec's "byte-for-byte
  equivalent" SC-005). It does NOT preserve owner — but in v0 we don't
  run as a process that could change owner, so this is moot.

**Alternatives considered**:

- **Whole-directory snapshot via `shutil.copytree`**: rejected. For
  `--here` over a directory containing hundreds of files we'd duplicate
  the world for every init invocation. Per-file is proportional to what
  the command actually touches.
- **Tarball backup**: rejected. Binary format violates the spirit of
  Principle I (plain-text everywhere a human might inspect). The backup
  files are sibling text/binary copies of what was there; if a rollback
  fails halfway, the user can still read them with `cat`.
- **Atomic via a single-file lockfile**: rejected. Doesn't help with the
  multi-file scaffold — we need per-file restore semantics, not a single
  commit point.

---

## R5. Deprecated-flag handling: `--ai`, `--ai-skills`, `--ai-commands-dir` (FR-003, FR-004)

**Decision**:

- **`--ai <key>`**: declared as a hidden Typer option
  (`typer.Option(None, "--ai", hidden=True, ...)`). When set and
  `--integration` was NOT also set, its value populates `--integration`
  internally and a one-line stderr warning is emitted ("the `--ai` flag
  is deprecated; use `--integration` instead"). When both are set,
  `--integration` wins and the same warning fires once.
- **`--ai-skills` and `--ai-commands-dir`**: NOT declared as Typer
  options. They are caught by a Typer `callback=` on the `init` command
  that inspects `click.get_current_context().args` *before* Typer's
  unknown-option handler runs. Each removed flag matches a hand-rolled
  "removed-flag" error with a fixed message pointing at the modern
  invocation, raises `typer.Exit(2)`, and writes no files. The
  inspection happens at the command-callback boundary, *after* Typer's
  argument parsing but *before* any helper in `commands/init.py` runs
  side-effects.

To enable the pre-callback to see arbitrary unknown flags without Typer
short-circuiting, the `init` Typer command is declared with
`context_settings={"allow_extra_args": True, "ignore_unknown_options":
True}`. The callback then walks `ctx.args` (and `--key=value` forms) and
fires the structured error before any scaffolding begins.

**Rationale**:

- The two removed flags are NOT valid in any current form — declaring
  them as Typer options just to reject them is misleading (Typer
  would auto-render them in `--help` output). Trapping at the context
  layer keeps `--help` clean and concentrates the deprecation logic in
  one place.
- Hidden options are the standard Typer pattern for "still accepted but
  not advertised"; they fit `--ai` exactly.
- The two paths share one ledger of "deprecated/removed flag rules" so
  adding a future entry is a one-line edit (closes the migration-spec
  open question implied by FR-031: deprecation logic in one place).

**Alternatives considered**:

- **Declare the removed flags as Typer options that always error**:
  rejected — pollutes `--help` and tempts future readers to wire them
  back up.
- **Pre-process `sys.argv` before Typer sees it**: rejected — would
  re-implement Typer's argv parsing; the `allow_extra_args +
  ignore_unknown_options` escape hatch is exactly what Typer publishes
  for this case.
- **Defer to a generic "unknown option" Typer handler**: rejected —
  loses the structured "name the modern equivalent" requirement
  (FR-004).

---

## R6. Atomic file writes within the scaffolder (FR-030)

**Decision**: Inside the writer helper, every byte is written to
`tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.",
suffix=".tmp")`, fsync'd, then `os.replace(tmp, target)`. This is exactly
the pattern `Manifest.dump` already uses (iteration 2). The two paths
share no code but share the same primitive, so a future refactor that
hoists the primitive into a `bookwright.core.io` helper would be a single
swap.

**Rationale**:

- Local atomicity (one file goes from "old" to "new" with no torn
  half-state) is the precondition the backup-ledger rollback assumes.
  If a write partially lands and the process dies, the ledger replay
  must be able to either delete the new file (it doesn't exist —
  `os.replace` is atomic) or restore the backup (still on disk under
  its sibling name).
- Reusing the iteration-2 pattern means the same Windows-newline /
  fsync rules apply consistently across the codebase.

**Alternatives considered**:

- **Write directly to the target via `Path.write_text`**: rejected. A
  failure mid-write leaves a half-written file that the backup ledger
  cannot trivially classify as "new" or "overwritten."
- **`flock` the target**: rejected. Doesn't help against process death
  and POSIX file locks are advisory.

---

## R7. Non-interactive detection for `--here` confirm (FR-029)

**Decision**: The interactive-confirmation path runs only when:

1. `--json` is NOT set, AND
2. `sys.stdin.isatty()` is True, AND
3. `sys.stdout.isatty()` is True.

If any condition fails and `--force` was not supplied and the directory is
not empty and `--here` was set, the command refuses with a structured
"non_interactive_here" error pointing the caller at `--force`, exits
non-zero, and writes nothing. The TTY check lives in a single helper
`_init_resolve.is_interactive()` so tests can monkeypatch one symbol.

**Rationale**:

- The Session 2026-05-29 Q1 answer ("Refuse with a dedicated
  non-interactive error; write no files; exit non-zero") is exactly this
  rule.
- Checking both stdin and stdout matches the way standard tools (apt,
  npm) decide whether to prompt: a piped stdin or a redirected stdout
  alike make a prompt useless.
- A single helper makes the test fixture trivial
  (`monkeypatch.setattr("bookwright.commands._init_resolve.is_interactive",
  lambda: False)`).

**Alternatives considered**:

- **Only check stdin**: rejected. A `--here | tee log.txt` pipeline has
  an interactive stdin but no visible stdout; a prompt would be invisible.
- **Always prompt unless `--json`**: rejected. Breaks CI runs that
  legitimately want to scaffold-in-place via `--force` but forgot to
  pass it on the previous attempt — the second attempt would hang.

---

## R8. Git interaction without GitPython (FR-022..FR-025)

**Decision**: A thin `_init_git.py` wrapper exposes three functions:

```python
def git_available() -> bool: ...                    # shutil.which("git") is not None
def is_inside_existing_repo(p: Path) -> bool: ...   # walks parents for .git/
def init_and_commit(root: Path, message: str) -> None: ...
```

`init_and_commit` runs `git init`, `git add .`, then `git commit -m
<message>` (no `--no-verify`, no `--allow-empty`) with `cwd=root`,
`check=True`, and `env` augmented to set `GIT_AUTHOR_NAME` /
`GIT_AUTHOR_EMAIL` / `GIT_COMMITTER_*` from the resolved author + a
documented fallback email (`"author@bookwright.local"`) so the commit
succeeds on a runner with no global git identity (which is the common CI
case). The pre-existing user `git config` is honoured first — the env
vars only fill the gap when `git config user.email` returns empty.

On `subprocess.CalledProcessError`, the error is captured (stderr in the
exception) and re-raised as a structured `GitInitError` carrying the
verbatim git stderr (the spec's "surface the underlying git error
verbatim" edge case under FR-022). The backup ledger rollback then
removes every file the scaffolder created — including any partial
`.git/` directory created by `git init` itself (`.git/` is added to the
ledger as a newly-created entry before `git init` runs).

`--no-git` skips this wrapper entirely (FR-023). `git_available()` False
+ `--no-git` not set → scaffolding succeeds, warning to stderr, no
`.git/` (FR-024). `is_inside_existing_repo(root)` True + `--here` set →
skip the wrapper, scaffolding succeeds, no new init, no automatic commit
(FR-025).

**Rationale**:

- The spec Assumption is explicit: "The initial commit is created using
  the `git` binary on PATH via subprocess. No new runtime dependency on
  a Python git library is introduced." GitPython is therefore excluded
  by spec.
- Setting `GIT_AUTHOR_*` / `GIT_COMMITTER_*` env vars is the lowest-
  invasive way to make the commit work in a CI container that has `git`
  but no global identity. It does NOT write to the host's git config,
  so a developer running the command locally sees no change in
  `~/.gitconfig`.
- Tracking `.git/` in the ledger as a newly-created entry means a git
  failure rolls back cleanly (no orphaned half-init'd repository).

**Alternatives considered**:

- **`pygit2`**: rejected — adds a C-extension runtime dependency for one
  init + one commit, well outside the Constitution-locked dep list.
- **Spec Kit's git extension**: rejected — operational reference only
  (axiom 5 + 6). Bookwright does not run shell scripts and does not
  depend on Spec Kit at runtime.
- **Skip the env-var trick and let `git commit` fail with "please tell
  me who you are"**: rejected — that's a sharp edge in CI for no
  pedagogical value.

---

## R9. Jinja2 rendering from `importlib.resources` (FR-008..FR-011)

**Decision**: One `jinja2.Environment` is constructed per init invocation
with:

```python
Environment(
    loader=PackageLoader("bookwright.resources.project", ""),
    autoescape=False,                # Markdown / TOML, not HTML
    keep_trailing_newline=True,      # round-trip preservation
    undefined=jinja2.StrictUndefined # surface missing context as errors
)
```

The scaffolder walks the resource tree via
`importlib.resources.files("bookwright.resources.project").iterdir()`
(recursively). For each entry:

- If it ends `.j2`, the writer renders it via `env.get_template(rel_path)`
  with `{title, project_slug, author, language, integration_key, ...}`
  context and writes the rendered output to the target without the `.j2`
  suffix.
- Otherwise, the writer copies the bytes verbatim.
- Directory entries map to `target.mkdir(parents=True, exist_ok=True)`.

`StrictUndefined` means a template that references a context key the
scaffolder forgot to populate raises `jinja2.UndefinedError` at render
time (caught by the rollback wrapper, surfaces as a structured
`TemplateRenderError`).

**Rationale**:

- `PackageLoader` is the idiomatic way to point Jinja2 at packaged
  resources; it Just Works with `importlib.resources` under
  `hatchling`'s wheel.
- `keep_trailing_newline=True` matches the iteration-2
  `Manifest.dump` behaviour (newline at EOF) and makes the generated
  files lint-clean (most editors flag missing-newline files).
- `StrictUndefined` is the only sane default for a code-gen pipeline —
  silent stringification of an undefined variable is the bug that ate
  Friday afternoon.

**Alternatives considered**:

- **`str.format_map`**: rejected — no loops, no conditionals, no
  whitespace control. Bible / outline templates in iteration 7 will
  need conditionals.
- **Roll our own template syntax**: rejected — re-implements Jinja2
  badly.
- **`FileSystemLoader` pointing at the unpacked resource dir**:
  rejected — wheel installs serve resources through `importlib.resources`,
  not as actual files; `PackageLoader` handles the indirection.

---

## R10. Source layout: `commands/init.py` + private siblings

**Decision**: `commands/init.py` holds the Typer entry point (`def
run(...)`) and the orchestration top-level function. The five helpers
(`_init_validate.py`, `_init_resolve.py`, `_init_scaffold.py`,
`_init_git.py`, `_init_envelope.py`) are private siblings in the same
package; each is single-purpose and under 200 lines. Names follow the
iteration-2 precedent (`core/_build.py`, `core/_translate.py` — private
helpers with leading underscore).

**Rationale**:

- Principle IV requires one file per CLI subcommand. The subcommand
  *is* `init.py`. The helpers are not subcommands; they are
  implementation detail.
- A subpackage (`commands/init/`) would technically also satisfy the
  principle's intent, but it would change the `from
  bookwright.commands import init` import shape and require an
  `__init__.py` that re-exports `run`. The flat layout matches the
  iteration-1 precedent (`commands/check.py`, `commands/version.py` are
  flat) so a future reader scans the directory and sees every command
  immediately.
- Leading-underscore private modules signal "not part of the public
  surface" without an `__all__` ceremony.

**Alternatives considered**:

- **`commands/init/` subpackage**: rejected as above.
- **One 800-line `init.py`**: rejected — would violate Principle IV's
  500-line ceiling.
- **Helpers under `core/`**: rejected — they are command-specific
  (deprecated-flag handling, JSON envelope shape, init-options record).
  Moving them under `core/` would invert the dependency direction
  (`core/` is consumed by commands, not the other way around).
