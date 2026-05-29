# Contract: `bookwright init` CLI

**Branch**: `004-init-command` | **Date**: 2026-05-29 |
**Plan**: [../plan.md](../plan.md) | **Data model**: [../data-model.md](../data-model.md)

This document fixes the external contract of the `init` subcommand: the
exact flag surface, the structured JSON envelope on stdout under
`--json`, the persistent `.bookwright/init-options.json` schema, the
warning lines on stderr, and the exit codes. Iteration 9 (skills
materializer), iteration 11 (E2E fixtures), and future agent integrations
read directly against this surface; any rename, signature change, or
behaviour change after merge is a breaking change.

JSON envelope shapes mirror the corresponding entities pinned in
[../data-model.md](../data-model.md). Where this document and the data
model agree, follow either. Where they disagree, the data model wins
until amended.

---

## 1. CLI surface

```text
bookwright init [PROJECT_NAME]
                [--here]
                [--force]
                [--no-git]
                [--integration KEY]
                [--integration-options STRING]
                [--json]
                [--ai KEY]                  # deprecated hidden alias
```

| Flag                     | Type / shape                          | Default       | Notes                                                                                                              |
|--------------------------|---------------------------------------|---------------|--------------------------------------------------------------------------------------------------------------------|
| `PROJECT_NAME`           | positional `str`                      | —             | Mutex with `--here` (FR-002). Validated per FR-021a before any filesystem work.                                    |
| `--here`                 | `bool`                                | `False`       | Mutex with `PROJECT_NAME`. Scaffolds in `Path.cwd()` (FR-029 governs the confirm-or-refuse path).                  |
| `--force`                | `bool`                                | `False`       | Overwrites name collisions under the project root; backup-ledger restore applies (FR-030).                         |
| `--no-git`               | `bool`                                | `False`       | Skip git init + commit entirely (FR-023).                                                                          |
| `--integration`          | `str`                                 | `"claude"`    | Must be in `bookwright.integrations.list_keys()`; otherwise `UnknownIntegrationError` envelope (FR-007).            |
| `--integration-options`  | `str`                                 | `""`          | POSIX shell-tokenised then forwarded to `bookwright.integrations.parse_options` (FR-006).                          |
| `--json`                 | `bool`                                | `False`       | Stdout becomes a single JSON document; human progress goes to stderr (FR-032, FR-033).                             |
| `--ai`                   | `str`                                 | `None`        | Hidden alias for `--integration`. When set, emits a stderr warning (FR-003).                                       |

Two flags are **not** declared as Typer options and are trapped by a
pre-callback (R5 in research.md):

| Removed flag              | Behaviour                                                                                                          |
|---------------------------|--------------------------------------------------------------------------------------------------------------------|
| `--ai-skills`             | Rejected at parse time with `code: "removed_flag"` envelope pointing at the modern invocation (FR-004).             |
| `--ai-commands-dir`       | Rejected at parse time with `code: "removed_flag"` envelope; for `generic`, the modern path is `--integration-options="--skills-dir <path>"` (FR-004). |

---

## 2. Side effects (in execution order)

1. **Parse + validate flags** — including the deprecated/removed-flag
   pre-callback. Any failure here writes no files and exits non-zero.
2. **Resolve `PROJECT_NAME`** via FR-021a rules; refuse with structured
   error if invalid (`code: "invalid_project_name"`). Compute the slug
   (R3); re-check the slug against the reserved-name list.
3. **Resolve target directory state**: `named` mode → `Path.cwd() /
   slug`; `here` mode → `Path.cwd()`. Apply the conflict matrix:
   - Existing `.bookwright/` at target → refuse (`code:
     "already_initialized"`, exit 3) regardless of `--force`.
   - Non-empty target, no `--force`, `named` mode → refuse (`code:
     "target_not_empty"`, exit 4).
   - Non-empty target, no `--force`, `here` mode, interactive →
     prompt; on negative answer refuse (`code:
     "user_declined_overwrite"`, exit 4) with no files written.
   - Non-empty target, no `--force`, `here` mode, non-interactive →
     refuse (`code: "non_interactive_here"`, exit 4).
4. **Resolve author, language, integration class, parsed integration
   options** — via the helpers in R1, R2, R5 of research.md plus
   `bookwright.integrations.get(...)` + `parse_options(...)`. Errors
   in option parsing surface as the iteration-3 structured exception
   serialised into the envelope (`code` is the iteration-3 code
   verbatim).
5. **Begin backup ledger** (data-model § 3). From this point on every
   filesystem mutation is reversible.
6. **Scaffold project tree** — render every entry under
   `bookwright.resources.project` into the target. Manifest is built
   via `Manifest.build(...)` and written via `Manifest.dump(...)`.
   Vocabularies copied from `bookwright.resources.vocabularies`.
   `.bookwright/init-options.json` is written here using the schema
   in § 4 below.
7. **Run integration `setup()`** — `bookwright.integrations.get(key)().
   setup(project_root, manifest, parsed_options)`. The skills
   directory and marker file are created here (iteration-3
   contract).
8. **Git init + commit** — unless `--no-git`, `git_available() is
   False`, or `is_inside_existing_repo(target)` is `True`. The
   commit subject is exactly `Initial commit from bookwright init`.
9. **Emit envelope** (success-path stdout) and warnings (stderr).
10. **Cleanup** — delete every backup-ledger entry's `backup_path`
    on success; replay the ledger on failure.

---

## 3. JSON envelopes

The shapes pinned in [../data-model.md § 4](../data-model.md) are the
authoritative ones. This section restates them in contract terms with
the field types and the explicit ordering convention.

### 3.1 Success envelope (`status: "ok"`)

```json
{
  "status": "ok",
  "project_root": "/abs/path",
  "project_slug": "mi-libro",
  "mode": "named",
  "integration": {
    "key": "claude",
    "skills_dir": ".claude/skills",
    "options": {}
  },
  "git_status": "initialized",
  "warnings": [],
  "bookwright_version": "0.0.1"
}
```

- `status` ∈ `{"ok"}` — literal.
- `project_root`: absolute POSIX path string.
- `project_slug`: slugified directory name (named mode) or the slug of
  the cwd basename (here mode).
- `mode` ∈ `{"named", "here"}`.
- `integration.key` ∈ `bookwright.integrations.list_keys()`.
- `integration.skills_dir`: project-relative POSIX path.
- `integration.options`: `dict[str, str | bool]` (exact `parse_options`
  return shape).
- `git_status` ∈ `{"initialized", "skipped_by_flag",
  "skipped_no_binary", "skipped_existing_repo"}`.
- `warnings`: array of strings (may be empty). Each entry is the same
  one-line text emitted to stderr (see § 5).
- `bookwright_version`: `bookwright.__version__`.

Encoding: `json.dumps(payload, separators=(",", ":")) + "\n"`. Exactly
one trailing newline. Stderr is silent (no progress) under `--json`,
except for the warning lines documented in § 5.

### 3.2 Error envelope (`status: "error"`)

```json
{
  "status": "error",
  "code": "unknown_integration",
  "message": "unknown integration: 'copilot'; valid: [claude, generic]",
  "details": {
    "value": "copilot",
    "valid": ["claude", "generic"]
  },
  "rolled_back": false,
  "bookwright_version": "0.0.1"
}
```

- `code` is one of the codes in § 4 below.
- `message` is a single line (no embedded `\n`).
- `details` is `{}` when the error carries no extra structure.
- `rolled_back` is `true` only when at least one byte hit disk AND
  the ledger replay completed. `false` otherwise. Includes a
  `details.rollback_error` string field when the ledger replay
  itself failed.

Same encoding as the success envelope. The error envelope is the
ONLY thing on stdout when `--json` is set on a failed run; stderr
remains silent except for the warning lines in § 5.

---

## 4. Error codes (stable identifiers)

| Code                          | Triggering condition                                                                            | Exit | Origin                                       |
|-------------------------------|-------------------------------------------------------------------------------------------------|------|----------------------------------------------|
| `mutually_exclusive`          | Both `PROJECT_NAME` and `--here` supplied (FR-002), or neither.                                  | 2    | init                                         |
| `removed_flag`                | `--ai-skills` or `--ai-commands-dir` present (FR-004).                                           | 2    | init                                         |
| `invalid_project_name`        | FR-021a rule violation (rule in `details.rule`, raw value in `details.value`).                   | 2    | init                                         |
| `unknown_integration`         | `--integration <key>` not in `list_keys()` (FR-007).                                             | 5    | iteration 3 (`UnknownIntegrationError.code`) |
| `unknown_option`              | `--integration-options` contains a flag the integration does not declare (FR-006).               | 5    | iteration 3 (`UnknownOptionError.code`)      |
| `malformed_option`            | `--integration-options` parse failure (missing value, duplicate flag, unbalanced quotes, ...).   | 5    | iteration 3 (`MalformedOptionError.code`)    |
| `invalid_option_declaration`  | The integration's own `options()` is malformed (programming error in iteration 3 surface). No CLI-driven trigger in v0 (both shipped integrations are well-formed); pinned at the iteration-3 layer. `init` only re-raises if a future integration declaration regresses. | 5    | iteration 3                                  |
| `target_not_empty`            | Named mode + target exists + not empty + no `--force` (FR-026).                                  | 4    | init                                         |
| `user_declined_overwrite`     | Interactive `--here` prompt got a negative answer.                                               | 4    | init                                         |
| `non_interactive_here`        | `--here` + non-empty cwd + non-interactive run (FR-029).                                         | 4    | init                                         |
| `already_initialized`         | `.bookwright/` exists at the target, even with `--force` (FR-028).                               | 3    | init                                         |
| `filesystem_error`            | Any `OSError` after scaffold began. Backup-ledger rolled back. `details.errno`, `details.path`. | 6    | init                                         |
| `git_error`                   | `git init` or `git commit` failed and `--no-git` was not set (FR-022 last clause).               | 7    | init                                         |
| `permission_denied`           | Failed to create the target directory or write the first byte for permission reasons.            | 6    | init                                         |

The mapping `error code → exit code` is contractual; consumers MAY
branch on either.

---

## 5. Warning lines (stderr)

Each warning is one line, terminated by `\n`. Prefix is fixed so an
agent that watches stderr can grep. Warnings are emitted regardless of
`--json` (FR-032). On the success path, every warning line emitted to
stderr is ALSO present (verbatim) in the JSON envelope's `warnings`
array. On the failure path, warnings still go to stderr; the error
envelope's payload does not duplicate them.

| Trigger                                                      | Text                                                                                              |
|--------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| `--ai` flag used (FR-003)                                    | `bookwright: warning: --ai is deprecated; use --integration instead`                              |
| `git` binary missing on PATH and `--no-git` not set (FR-024) | `bookwright: warning: git not found on PATH; project created without a repository`                |
| `--here` lands inside an existing `.git/` (FR-025)           | `bookwright: warning: existing .git/ detected; skipped git init and commit`                       |
| Author resolution fell back to sentinel (FR-016 step 3)      | `bookwright: warning: author could not be resolved from git config or $USER; using 'Unknown Author'` |

Adding a new warning is a MINOR contract change (new line type); changing
an existing line's text or prefix is a MAJOR contract change.

---

## 6. Persistent file: `.bookwright/init-options.json`

The on-disk record at `<project_root>/.bookwright/init-options.json`.
Single source of truth for "how was this project initialised."

```json
{
  "schema_version": 1,
  "created_at": "2026-05-29T12:34:56Z",
  "bookwright_version": "0.0.1",
  "options": {
    "mode": "named",
    "project_name": "Mi Libro",
    "project_slug": "mi-libro",
    "project_root": "/abs/path/to/mi-libro",
    "title": "Mi Libro",
    "authors": ["Jorge Moreno"],
    "language": "es",
    "integration_key": "claude",
    "integration_skills_dir": ".claude/skills",
    "integration_options": {},
    "no_git": false,
    "force": false,
    "json_output": false,
    "git_status": "initialized",
    "deprecated_flags_seen": []
  }
}
```

- `schema_version`: MUST equal `1` in this iteration. Future readers
  MUST reject unknown integer values (FR-034 last clause, Session
  2026-05-29 Q5).
- `created_at`: ISO 8601 UTC, suffixed with `Z`, second precision.
- `bookwright_version`: `bookwright.__version__` verbatim.
- `options`: mirror of `ResolvedInvocation` (data-model § 2).

Encoding: `json.dumps(payload, indent=2, sort_keys=False) + "\n"`.

This file is part of the canonical project record and is included in
the initial git commit (so a `git show HEAD --stat` lists it).

---

## 7. Behavioural invariants

These hold across every invocation. Each one is verified mechanically
by a test in `tests/commands/`.

1. **Atomic-or-nothing on disk.** For every documented failure mode,
   the target directory is byte-for-byte equivalent to its
   pre-invocation state. Verified by snapshotting
   `[(rel_path, sha256(bytes)) for rel_path in tree(target)]` pre/post
   the invocation (SC-005, FR-030).
2. **No writes outside the project root.** The backup ledger refuses
   any write whose target is not inside `project_root`. Verified by a
   parametrized test that snapshots `Path.cwd()` siblings before/after
   for `--here` runs (FR-014).
3. **No re-implementation of `Manifest` serialisation.** AST scan of
   `commands/init.py` + helpers MUST show zero `tomlkit.dumps` /
   `tomlkit.parse` calls; the only path that writes TOML is
   `Manifest.dump` (FR-015).
4. **No re-implementation of integration option parsing.** AST scan
   MUST show zero `shlex.split` calls in `commands/`. Token parsing
   for `--integration-options` is solely the iteration-3
   `parse_options` function (FR-006).
5. **`--json` stdout is one JSON document and a trailing newline.**
   Verified by subprocess + `json.loads(result.stdout)` for both
   success and every documented failure mode (Principle IX, FR-032).
6. **Warnings on stderr.** The four warning trigger conditions each
   produce exactly one stderr line; tested by subprocess `result.stderr.splitlines()`.
7. **Exit code per envelope code.** The mapping in § 4 is asserted by
   parametrized tests covering every code.
8. **`init-options.json` round-trips.** Reading the file back as JSON
   and re-parsing into a `pydantic.BaseModel` reconstructs the
   same `ResolvedInvocation` (modulo the `created_at` timestamp) for
   every combination of CLI flags exercised by the user-story tests
   (FR-034).
