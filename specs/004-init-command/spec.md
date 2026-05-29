# Feature Specification: `bookwright init` Command

**Feature Branch**: `004-init-command`

**Created**: 2026-05-29

**Status**: Draft

**Input**: User description: see the `/speckit-specify` brief preserved in `bookwright-implementation-plan.md` § 3, Iteración 4. Reference: `bookwright-design.md` § 5.2 (flags) and § 7 (generated project structure).

## Clarifications

### Session 2026-05-29

- Q: How should `--here` in a non-empty directory (no `--force`) behave when interactive confirmation is impossible (i.e. `--json` is set, or stdin/stdout is not a TTY)? → A: Refuse with a dedicated non-interactive error; write no files; exit non-zero.
- Q: What are the validation rules for raw `PROJECT_NAME` (before slugification)? → A: Permissive Unicode (accents allowed); reject empty, path separators (`/`, `\`), `.`/`..`, leading dot, length > 100 characters, and host-OS reserved names.
- Q: How is the value of `--integration-options` tokenized before it is forwarded to the integration's option parser? → A: POSIX shell-style tokenization (`shlex.split`-equivalent); quoted values with spaces and standard shell escapes are supported; the resulting list is forwarded `argv`-style to the integration.
- Q: When `--force` or `--here` overwrites a pre-existing file and a later scaffolding step fails, must the original file be restored? → A: Yes — best-effort restore. Each pre-existing file is backed up before being overwritten; on rollback, originals are restored from the backup; on success, the backups are deleted.
- Q: What schema does `.bookwright/init-options.json` use? → A: Versioned envelope. Top-level object with `schema_version` (integer, currently `1`), `created_at` (ISO 8601 UTC timestamp), `bookwright_version` (string), and `options` (object of resolved invocation values). Readers MUST reject unknown `schema_version` values.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scaffold a new book project in one command (Priority: P1)

An author who has installed Bookwright wants to start a new book. From any directory they run a single command, give the project a name, and end up with a complete, ready-to-edit project tree on disk: a manifest, empty manuscript area, full bible/outline templates, the Bookwright metadata directory, the AI integration wired in for Claude Code, and a clean git repository whose first commit contains every generated file.

**Why this priority**: This is the canonical entry point to the entire Bookwright workflow. Until this works there is no project to operate on, so every subsequent command (graph, validate, the authoring skills) has nothing to bind to. It is also the user's first impression of the tool — the "two minutes to a working project" promise that justifies the rest of the design.

**Independent Test**: From an empty parent directory, run the init command with only a project name. Confirm that (a) the named directory was created, (b) it contains every file and subdirectory enumerated in § 7 of the design doc, (c) the manifest is valid TOML with all mandatory fields populated, (d) the Claude integration's skills directory exists with the expected layout, and (e) `git log` inside the new directory shows exactly one commit with the prescribed message and every generated file staged.

**Acceptance Scenarios**:

1. **Given** the current directory has no entry named `mi-libro` and git is installed, **When** the author runs `bookwright init mi-libro`, **Then** a directory `mi-libro/` is created containing `manifest.toml`, `README.md`, `.gitignore`, an empty `manuscript/`, a populated `bible/` (with `constitution.md`, empty `characters/` and `settings/`, and the other bible documents listed in § 7), a populated `outline/`, a `.bookwright/` metadata directory, and a `.claude/skills/` directory; and `git log` shows exactly one commit titled `Initial commit from bookwright init` with every generated file staged.
2. **Given** the new project just created, **When** the author opens `manifest.toml`, **Then** all mandatory fields are filled with sensible defaults (title derived from the project name, author resolved from environment/git config, type `novel`, language detected or `es`, status `idea`, integration `claude`, skills_dir `.claude/skills`).
3. **Given** the user passes a project name that includes spaces or uppercase, **When** the command derives the on-disk directory and the manifest `title`, **Then** the directory uses a slugified form and the manifest preserves the original casing as `title`.

---

### User Story 2 - Initialize in the current directory (Priority: P1)

An author already inside an empty (or near-empty) working directory — for example one they just created with `mkdir`, or one a publisher seeded with a single license file — wants to turn it into a Bookwright project in place, without nesting a new subdirectory inside it.

**Why this priority**: This is the second supported entry path called out by name in the design (§ 5.2). It also covers the common case of bootstrapping inside an existing git repository or a directory provided by an editor. Without it, users have to create+move files manually.

**Independent Test**: Create a clean temp directory, `cd` into it, run the init command with `--here`. Verify the same artifacts appear directly in the current directory (no nested project folder), and that git is initialized in this same directory.

**Acceptance Scenarios**:

1. **Given** the current directory is empty, **When** the author runs `bookwright init --here`, **Then** the project structure is written directly into the current directory (not into a subdirectory) and git is initialized at the same level.
2. **Given** the current directory contains unrelated files but no `.bookwright/`, **When** the author runs `bookwright init --here`, **Then** the command asks for confirmation before writing; if the author confirms, the project files are added alongside the existing files; if they decline, nothing is written.
3. **Given** the same non-empty directory, **When** the author runs `bookwright init --here --force`, **Then** the command proceeds without prompting; the manifest and other generated files are written, overwriting any name collisions.
4. **Given** the current directory already contains a `.bookwright/` directory, **When** the author runs `bookwright init --here` (with or without `--force`), **Then** the command refuses with an "already initialized" error and writes nothing.
5. **Given** a positional project name is also supplied alongside `--here`, **When** the command is parsed, **Then** it rejects the combination with an error explaining that the two options are mutually exclusive.

---

### User Story 3 - Choose a different AI integration (Priority: P2)

An author who uses an editor or assistant other than Claude Code (Codex CLI, Cursor, VS Code Copilot, etc.) wants the project to install its skills for that environment instead. They also occasionally want to override where those skills land — for example, the Cursor users on the team keep skills under `.cursor/skills`.

**Why this priority**: The plugin shape is constitutionally required (Principle V) and the two v0 integrations must both work. Without this, the project is implicitly Claude-only and breaks the "Generic" promise. It is P2 rather than P1 because the default (Claude) is the most common path and gets users to a working project; switching integrations is the next-most-important variant.

**Independent Test**: Run the init command three times in separate temp directories — once with `--integration generic`, once with `--integration generic --integration-options="--skills-dir .cursor/skills"`, and once with an invalid integration name — and confirm the generated skills layout, the recorded manifest values, and the error path respectively.

**Acceptance Scenarios**:

1. **Given** an empty parent directory, **When** the author runs `bookwright init mi-libro --integration generic`, **Then** the generated project contains a `.agents/skills/` directory (not `.claude/skills/`) populated by the Generic integration, and `manifest.toml` records `integration.key = "generic"` and `integration.skills_dir = ".agents/skills"`.
2. **Given** the same parent directory, **When** the author runs `bookwright init mi-libro --integration generic --integration-options="--skills-dir .cursor/skills"`, **Then** the generated project contains `.cursor/skills/` (and no `.agents/skills/`), and the manifest records `skills_dir = ".cursor/skills"` plus the override under `integration.options`.
3. **Given** any directory, **When** the author runs `bookwright init mi-libro --integration unknown`, **Then** the command fails with an error that names the unknown integration and lists the available integration keys (`claude`, `generic`), and writes no files.
4. **Given** the user passes `--integration-options` whose contents are not valid for the chosen integration (unknown flag, malformed value), **When** the command runs, **Then** it fails with an error that quotes the offending option and names the integration it was sent to, and writes no files.

---

### User Story 4 - Skip git initialization (Priority: P2)

An author wants to scaffold a project inside an existing monorepo or inside a directory that is already a git repository, and does not want a nested git repo or an extra commit interfering with their existing workflow.

**Why this priority**: A user-facing escape hatch that the design lists explicitly. It is P2 because it is a deliberate, narrower choice that does not affect the most common first-run experience but does affect users who would otherwise be blocked.

**Independent Test**: Run the init command with `--no-git` in a clean parent directory and verify the project files are written but no `.git/` directory exists, no commit is created, and the success report explicitly notes that git was skipped.

**Acceptance Scenarios**:

1. **Given** a clean parent directory, **When** the author runs `bookwright init mi-libro --no-git`, **Then** the project structure is created, no `.git/` directory exists, no commit is made, and the command reports success while explicitly noting that git initialization was skipped.
2. **Given** that git is not installed on the machine (or not on the PATH) and the user did *not* pass `--no-git`, **When** the command runs, **Then** it writes the project structure, emits a warning that git was not detected, and reports success without creating a repository or commit.

---

### User Story 5 - Migrate from deprecated flags (Priority: P3)

A user (or a script) carries forward muscle memory or copy/paste from older Spec Kit–style projects: they call init with `--ai claude` (an old name for the integration choice) or with flags that no longer exist (`--ai-skills`, `--ai-commands-dir`). The user needs to learn the new flag without being stranded.

**Why this priority**: This is migration ergonomics: it does not unlock new functionality but it materially reduces support friction for users coming from earlier tooling. It is bounded — only the three flags called out in the brief need to be handled.

**Independent Test**: Run the init command once with `--ai claude` (must succeed with a warning), once with `--ai-skills`, and once with `--ai-commands-dir` (both must fail with a pointer to the modern equivalent). Capture stderr in each case and confirm the warning/error wording.

**Acceptance Scenarios**:

1. **Given** an empty parent directory, **When** the author runs `bookwright init mi-libro --ai claude`, **Then** the command behaves exactly like `--integration claude` (creates the same project), emits a stderr warning that `--ai` is deprecated and the user should switch to `--integration`, and still exits with a success status.
2. **Given** the author runs the command with `--ai-skills` (with or without a value), **When** the command parses arguments, **Then** it fails with a non-zero exit code, writes no files, and the error message explains that `--ai-skills` is no longer accepted because Agent Skills is now the only output mode and points at the current invocation form.
3. **Given** the author runs the command with `--ai-commands-dir <path>`, **When** the command parses arguments, **Then** it fails with a non-zero exit code, writes no files, and the error message explains that the directory is now controlled by the chosen integration (and, for Generic, by `--integration-options="--skills-dir <path>"`).

---

### Edge Cases

- **Target directory exists and is non-empty** (no `--here`, no `--force`): the command fails before writing anything, with an error that names the directory and explains the two ways forward (`--force` to overwrite, `--here` to initialize in place).
- **Target directory exists and is empty**: the command proceeds and reuses the directory. No prompt.
- **Target directory exists and `--force` is passed**: the command proceeds, overwrites name collisions in the project root, and does not delete unrelated pre-existing files.
- **`--here` inside an already-initialized Bookwright project** (i.e. `.bookwright/` exists): the command refuses and writes nothing, even with `--force` — `--force` does not override "already initialized".
- **Both `PROJECT_NAME` and `--here` supplied**: rejected as mutually exclusive.
- **Neither `PROJECT_NAME` nor `--here` supplied**: rejected with a usage error pointing at both options.
- **Project name fails validation**: rejected with an error that quotes the offending name and lists the rules. A `PROJECT_NAME` is invalid if it is empty, contains a path separator (`/` or `\`), is exactly `.` or `..`, starts with `.`, exceeds 100 characters, or matches a host-OS reserved name (e.g. on Windows: `CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9`). Unicode characters, including accented letters such as `á`, `ñ`, `ü`, are accepted in the raw `PROJECT_NAME`; the on-disk directory is derived via slugification (see FR-021).
- **No write permission on the target path**: fails with a clear "permission denied" message naming the path; nothing is partially written.
- **Disk write fails partway through scaffolding**: the command must either complete fully or leave the target directory byte-for-byte equivalent to its pre-invocation state. A half-written project is not an acceptable end state. Under `--force`/`--here`, any pre-existing file that the command was about to overwrite MUST be backed up before the overwrite; on rollback, those backups are restored over the partial writes; on success, the backups are deleted. Files newly created by the command (no prior version) MUST be deleted on rollback.
- **Author cannot be resolved** (no `$USER`, no `git config user.name`): the manifest is still written; the `authors` field is set to a documented sentinel (e.g. `["Unknown Author"]`) and a stderr note tells the user to update it.
- **Language cannot be detected**: the manifest is written with `language = "es"` per the design's default.
- **`--no-git` is passed in a directory that already contains a `.git/`**: the command does not touch the existing repository, does not initialize a new one, and does not create a commit. The user's existing git state is preserved.
- **Git is installed but the initial commit fails** (e.g. global git hook rejects it): the command surfaces the underlying git error verbatim, rolls back to the pre-invocation state per FR-030 (any partial `.git/` created by `git init` is removed, every scaffolded file is unlinked, and any pre-existing file overwritten under `--force`/`--here` is restored from backup), and exits non-zero so the user can recover.
- **`--json` is requested**: the success report on stdout is a single JSON document describing the result; warnings (deprecation, git-not-found, author-not-detected, etc.) still go to stderr.
- **`--here` in a non-empty directory under non-interactive conditions** (i.e. `--json` is set, or stdin/stdout is not a TTY): the command does not prompt and does not silently overwrite. It refuses with an error pointing the caller at `--force`, writes nothing, and exits non-zero.

## Requirements *(mandatory)*

### Functional Requirements

#### Invocation and flags

- **FR-001**: The command MUST be invokable as `bookwright init [PROJECT_NAME]` and MUST accept the flags `--here`, `--force`, `--no-git`, `--integration <key>`, `--integration-options <string>`, and `--json`, with the semantics defined in `bookwright-design.md` § 5.2.
- **FR-002**: The command MUST treat `PROJECT_NAME` and `--here` as mutually exclusive and MUST require exactly one of them.
- **FR-003**: The command MUST accept `--ai <key>` as a deprecated hidden alias for `--integration <key>`, emit a deprecation warning to stderr when it is used, and otherwise behave identically.
- **FR-004**: The command MUST reject `--ai-skills` and `--ai-commands-dir` with a non-zero exit code and an error message that names the modern equivalent (`--integration` or `--integration-options="--skills-dir ..."`). It MUST NOT write any files when this happens.
- **FR-005**: The command MUST default `--integration` to `claude` and MUST default the integration's skills directory according to the design's per-integration table (`claude` → `.claude/skills`, `generic` → `.agents/skills`).
- **FR-006**: When `--integration-options` is supplied, the command MUST tokenize its value using POSIX shell-style rules (`shlex.split`-equivalent: whitespace separates tokens, single and double quotes group tokens, standard backslash escapes apply) and forward the resulting `argv`-style list to the chosen integration's option parser. If tokenization fails (e.g. unbalanced quotes), or parsing fails, or the option is not declared by that integration, the command MUST fail with an error that quotes the offending option (or, for tokenization errors, the original raw value) and writes no files.
- **FR-007**: When `--integration <unknown>` is supplied, the command MUST fail with an error that lists the available integration keys and writes no files.

#### Project structure

- **FR-008**: The command MUST produce, in the project root, the files `manifest.toml`, `README.md`, and `.gitignore`, each populated from packaged templates.
- **FR-009**: The command MUST produce an empty `manuscript/` directory that is preserved in git via a `.gitkeep` (or equivalent) placeholder.
- **FR-010**: The command MUST produce a populated `bible/` directory containing at minimum: `constitution.md` (the unfilled template), empty `characters/` and `settings/` subdirectories, and the other bible documents enumerated in § 7 of the design (`timeline.md`, `relationships.md`, `themes.md`, `glossary.md`, `research.md`, `subplots.md`, and a `pov-structure.md` placeholder). Bible templates in this iteration MAY be minimal placeholders; the full versions land in iteration 7.
- **FR-011**: The command MUST produce a populated `outline/` directory containing at minimum the documents enumerated in § 7 (`arcs.md`, `structure.md`, `synopsis.md`, `scenes.md`).
- **FR-012**: The command MUST produce a `.bookwright/` directory containing `init-options.json`, `schema/`, `vocabularies/` (with at least `propp.ttl` and `greimas.ttl`), `templates/`, and `cache/` — with `cache/` (and only `cache/` from within `.bookwright/`) excluded from git via the generated `.gitignore`.
- **FR-013**: The command MUST install the chosen integration's skills directory under the path defined by that integration (default `.claude/skills/` for `claude`, default `.agents/skills/` for `generic`, or the override path supplied via `--integration-options`). In this iteration the contents MAY be placeholders; full skill materialization lands in iteration 9.
- **FR-014**: The command MUST NOT create any files outside the project root.

#### Manifest contents

- **FR-015**: The generated `manifest.toml` MUST be valid TOML and MUST populate all mandatory fields defined in `bookwright-design.md` § 8.1.
- **FR-016**: The manifest's `book.authors` field MUST be populated by resolving, in order: (a) `git config user.name` in the relevant scope, (b) the `$USER` environment variable, (c) a documented fallback value. The actual mechanism used MUST be reported in stderr when fallback (c) is reached.
- **FR-017**: The manifest's `book.type` MUST default to `novel`.
- **FR-018**: The manifest's `book.language` MUST default to a value detected from the host locale when available, and to `es` otherwise.
- **FR-019**: The manifest's `book.status` MUST default to `idea`.
- **FR-020**: The manifest's `[integration]` section MUST reflect the chosen integration key, the resolved skills directory, and the options that were applied. When `--integration-options` was not supplied, `integration.options` MUST be an empty inline table.
- **FR-021**: The manifest's `book.title` MUST be derived from the supplied `PROJECT_NAME` (preserving the user's casing/spacing) for the directory-form invocation, and from the current directory's basename for the `--here` invocation. The on-disk project directory name, in the directory-form invocation, MUST be a filesystem-safe slug of the supplied name.
- **FR-021a**: The command MUST validate `PROJECT_NAME` before any filesystem work and MUST reject it with a non-zero exit and no files written when any of the following hold: it is empty, it contains a path separator (`/` or `\`), it is exactly `.` or `..`, it starts with `.`, it exceeds 100 characters, or it matches a host-OS reserved name (e.g. on Windows: `CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9`). Leading and trailing ASCII whitespace MUST be stripped before the rules apply (so `"  mi-libro  "` is accepted as `"mi-libro"`; a value consisting entirely of whitespace trips the `empty` rule). Unicode characters, including accented Latin letters, MUST be accepted; the slug derivation in FR-021 is responsible for normalising them for the on-disk directory.

#### Git initialization

- **FR-022**: Unless `--no-git` is supplied, the command MUST initialize a git repository at the project root and create exactly one commit titled `Initial commit from bookwright init`, with every generated non-ignored file staged. Files generated under paths covered by the project's `.gitignore` (notably `.bookwright/cache/` per the Assumptions list — including any `.gitkeep` placeholder shipped to keep that directory present, and any backup files written under `.bookwright/cache/backup/` during a `--force`/`--here` run) are deliberately NOT staged; the initial commit's tree matches `git ls-files`, not the full on-disk scaffold.
- **FR-023**: When `--no-git` is supplied, the command MUST NOT run any git operations and MUST NOT create a `.git/` directory.
- **FR-024**: When git is not available on the host and `--no-git` was not supplied, the command MUST still produce the project structure, MUST emit a warning to stderr explaining that git was not detected, and MUST report success.
- **FR-025**: When `--here` is used inside a directory that already contains a `.git/`, the command MUST leave the existing repository untouched (no new init, no automatic commit on the user's repository).

#### Idempotency, safety, and failure modes

- **FR-026**: When the positional `PROJECT_NAME` resolves to an existing directory that is non-empty, the command MUST refuse to proceed unless `--force` is supplied; the error message MUST name the directory and mention both `--force` and `--here` as alternatives.
- **FR-027**: When the positional `PROJECT_NAME` resolves to an existing directory that is empty, the command MUST proceed without prompting.
- **FR-028**: When `--here` is used in a directory that already contains a `.bookwright/`, the command MUST refuse with an "already initialized" error, even if `--force` is supplied.
- **FR-029**: When `--here` is used in a non-empty directory without `--force`, the command MUST ask for interactive confirmation before writing; a negative answer MUST leave the directory untouched. If the run is non-interactive (`--json` is supplied, or stdin/stdout is not a TTY), the command MUST NOT prompt: it MUST refuse with a dedicated error explaining that non-interactive `--here` in a non-empty directory requires `--force`, exit non-zero, and write no files.
- **FR-030**: If any failure occurs after scaffolding has begun, the command MUST roll back so that the target directory is byte-for-byte equivalent to its pre-invocation state. Files newly created by the command (no prior version on disk) MUST be deleted. Pre-existing files MUST NOT be deleted. Pre-existing files that the command overwrote under `--force` or `--here` MUST be restored from a backup taken immediately before the overwrite; on successful completion the backups MUST be deleted. If a backup cannot be created (e.g. permission denied), the overwrite MUST NOT proceed and the command MUST fail before touching that file.
- **FR-031**: The command MUST exit non-zero on any of the above error conditions. In default (non-`--json`) mode the command MUST emit a single, human-readable error line on stderr identifying the failure cause and MUST NOT write to stdout. Under `--json` (FR-032) the failure is surfaced as the structured error envelope on stdout instead; stderr remains reserved for the warning lines documented in the contract and MUST NOT carry a duplicate error line.

#### Output contract

- **FR-032**: When `--json` is supplied, the command MUST write a single JSON document to stdout describing the result (at minimum: status, project root, chosen integration, skills directory, git status) and MUST NOT write any other content to stdout. Human progress messages and warnings MUST go to stderr.
- **FR-033**: When `--json` is not supplied, the command MAY use a rich human-readable progress display on stderr, but stdout MUST remain quiet (or limited to a final success line) so it can still be redirected without contaminating logs.
- **FR-034**: Regardless of `--json`, the command MUST record the exact options it was invoked with in `.bookwright/init-options.json` so later commands can introspect them. The file MUST be a JSON object with the following top-level keys: `schema_version` (integer, set to `1` in this iteration), `created_at` (ISO 8601 UTC timestamp of when the record was written), `bookwright_version` (the package version string at init time), and `options` (an object capturing the resolved invocation: project name or `--here` mode, integration key, resolved skills directory, integration options, and the boolean flags `--no-git`, `--force`, `--json`). Consumers of this file MUST validate `schema_version` and reject unknown values.

### Key Entities *(include if feature involves data)*

- **Project**: the on-disk directory tree produced by `bookwright init`. Identified by its root path. Contains a manifest, a manuscript area, a bible, an outline, a Bookwright metadata directory, and exactly one integration installation. There is one project per root.
- **Manifest**: the `manifest.toml` file at the project root. Captures the project's identity (title, type, language, authors, status), the active vocabularies, the active validators, and the chosen integration. Mandatory fields are enumerated in `bookwright-design.md` § 8.1.
- **Integration**: a named adapter that knows where and how to install Agent Skills for a given AI environment. In v0 there are exactly two: `claude` (default skills directory `.claude/skills/`) and `generic` (default skills directory `.agents/skills/`, overridable). Each integration declares its own option schema; `bookwright init` does not interpret integration options itself.
- **Init Options Record**: the persisted record at `.bookwright/init-options.json` capturing the exact flags and resolved values used at init time, for later introspection by other commands. Versioned envelope (see FR-034): `schema_version` (integer, currently `1`), `created_at` (ISO 8601 UTC), `bookwright_version` (string), and `options` (object of resolved invocation values). Readers MUST reject unknown `schema_version`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time user who has Bookwright installed can produce a complete, valid project in under 30 seconds of wall-clock time on a typical laptop, including the initial git commit. The 30 s figure is a UX target for typical developer hardware; CI enforces a more generous regression guard-rail (60 s) on the US1 happy path so a flaky shared runner does not red the suite while still catching catastrophic regressions (a misplaced `time.sleep`, a runaway git hook, etc.).
- **SC-002**: 100% of the files and directories listed in `bookwright-design.md` § 7 are present in the generated project after a default-flag run, with zero extra top-level files.
- **SC-003**: The generated `manifest.toml` parses without error against the manifest model defined in iteration 2, with every mandatory field populated, in 100% of runs across the supported flag combinations.
- **SC-004**: After a default-flag run, `git log` inside the project shows exactly one commit titled `Initial commit from bookwright init`, with zero unstaged or untracked files, in 100% of runs where git is available.
- **SC-005**: Running the command in any documented failure mode (target directory non-empty without `--force`, `--here` inside an initialized project, unknown integration, removed flags, invalid integration options) leaves the target directory byte-for-byte unchanged from its pre-invocation state in 100% of runs.
- **SC-006**: When invoked with `--json`, the command emits a single valid JSON document on stdout and zero non-JSON bytes on stdout, in 100% of runs (success and failure alike).
- **SC-007**: Using `--ai claude` produces the same on-disk result as `--integration claude` and a single deprecation warning on stderr; using `--ai-skills` or `--ai-commands-dir` produces a non-zero exit and an error that names the modern equivalent — verified by automated test coverage for each of the three flags.
- **SC-008**: Switching `--integration` from `claude` to `generic` (with or without `--integration-options="--skills-dir <path>"`) changes only the integration installation directory and the `[integration]` block of the manifest; the rest of the generated tree is identical.

## Assumptions

- The Manifest model from iteration 2 and the Integration plugin architecture from iteration 3 (with the `claude` and `generic` integrations already registered) are available on `main` when this iteration starts. This iteration consumes those APIs; it does not reimplement them.
- Bible and outline templates may be minimal placeholders in this iteration. The fully fleshed-out versions land in iteration 7; this spec only requires that the files exist with the names listed in § 7.
- Agent Skills materialization is a placeholder in this iteration. Iteration 9 replaces the placeholder contents with real `SKILL.md` files generated from the source commands. This spec only requires that the chosen integration's skills directory exists with the expected layout.
- The minimum bundled vocabularies for `.bookwright/vocabularies/` are `propp.ttl` and `greimas.ttl`. Additional vocabularies listed in the design's resources catalog can be added later without requiring a spec change here.
- "Language detected from locale" means a best-effort read of the host environment (e.g. the locale environment variables) and falls back silently to `es` per the design.
- "Slugified project name" means a lowercase, filesystem-safe form following the same conventions Bookwright already uses for URI generation; the precise transformation is left to the planning phase.
- The `.gitignore` template entries are: `.bookwright/cache/`, `*.pyc`, `__pycache__/`, `.venv/`, `.env`, per § 7.1 of the design. Additional entries can be added during planning if needed but should not surprise the user.
- The initial commit is created using the `git` binary on PATH via subprocess (per the planning hint in `bookwright-implementation-plan.md` § Iteración 4). No new runtime dependency on a Python git library is introduced by this iteration. The commit's author name is the value resolved by FR-016. The commit's author email is the user's `git config user.email` when set; otherwise a documented fallback (`author@bookwright.local`) is supplied via `GIT_AUTHOR_EMAIL`/`GIT_COMMITTER_EMAIL` env vars purely to let `git commit` succeed on hosts without a global git identity (typical CI containers). The fallback is never written to the user's git config and never reaches the manifest's `book.authors` field.
- This iteration introduces no new top-level CLI surface beyond `bookwright init`; it does not modify the surface of any other subcommand.
