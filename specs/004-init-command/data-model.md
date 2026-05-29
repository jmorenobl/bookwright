# Phase 1 — Data Model: `bookwright init` Command

**Branch**: `004-init-command` | **Date**: 2026-05-29 |
**Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

This iteration is mostly orchestration: it consumes the iteration-2
`Manifest` model and the iteration-3 `SkillsIntegration` contract, then
writes a tree of plain-text files. Three data structures are nonetheless
worth pinning because they cross the boundary between command-internal
helpers and the persisted on-disk record:

1. **`InitOptionsRecord`** — the persisted `.bookwright/init-options.json`
   envelope. The only new persistent file format this iteration
   introduces. Versioned per FR-034 / the Session 2026-05-29 Q5 answer.
2. **`ResolvedInvocation`** — in-process resolved-options struct passed
   between helpers and serialised into `InitOptionsRecord.options`.
3. **`BackupLedger`** — internal in-memory rollback record (FR-030).

For each structure: fields, validation, lifetime, and the JSON shape it
serializes to (where applicable). Iteration-2 and iteration-3 models
(`Manifest`, `SkillsIntegration`, the integration exception family) are
referenced where consumed but not re-specified.

---

## 1. `InitOptionsRecord`

**Purpose**: Persistent record at `.bookwright/init-options.json`
capturing the exact flags and resolved values that `init` was invoked
with, so later commands (introspection, debug bundles, future re-init
diffs) have a single source of truth (FR-034).

**Shape**: `pydantic.BaseModel` in
`bookwright.commands._init_envelope`. Lives in-process during the
command run and is serialised to disk via
`json.dumps(..., indent=2, sort_keys=False)` (insertion order matches
the schema below — `json.dumps` is stable on Python 3.7+).

| Field                | Type                  | Required | Notes                                                                                                                                |
|----------------------|-----------------------|----------|--------------------------------------------------------------------------------------------------------------------------------------|
| `schema_version`     | `int`                 | yes      | Currently `1`. Readers MUST reject unknown values (Session 2026-05-29 Q5). The reader contract for future iterations is pinned here. |
| `created_at`         | `str` (ISO 8601 UTC)  | yes      | E.g., `"2026-05-29T12:34:56Z"`. Computed from `datetime.now(timezone.utc).isoformat(timespec='seconds') + 'Z'`.                       |
| `bookwright_version` | `str`                 | yes      | The value of `bookwright.__version__` at init time. Captured for forensics, not for behaviour gating.                                |
| `options`            | `ResolvedInvocation`  | yes      | Resolved invocation values (see § 2).                                                                                                |

**Validation rules**:

- `schema_version` MUST equal `1` at write time. Readers (a future
  introspection command, iteration 11) MUST raise a structured error on
  any other integer.
- `created_at` MUST be a UTC timestamp ending in `Z` (no offset).
- `bookwright_version` is treated as opaque text by the writer; PEP 440
  validity is verified separately by `Manifest.build` for
  `cli_version_min`, not here.

**Storage**: written to
`<project_root>/.bookwright/init-options.json` via the same atomic
writer + backup-ledger primitive every other init-time file goes
through. The file is committed in the initial git commit (it is part
of the canonical project record).

**Lifetime**: created once at init time. Subsequent commands in v0 do
not modify it; iteration 11 may add an introspection command that
reads it.

---

## 2. `ResolvedInvocation`

**Purpose**: Capture, in one struct, every resolved value the command
operated on after CLI parsing, name validation, author/language
resolution, and integration option parsing. This is the source of
truth for `InitOptionsRecord.options` and also the input the JSON
envelope (§ 4) serialises on success.

**Shape**: `pydantic.BaseModel` in
`bookwright.commands._init_envelope`.

| Field                  | Type                        | Required | Notes                                                                                                                                                            |
|------------------------|-----------------------------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `mode`                 | `Literal["named", "here"]`  | yes      | Whether the invocation was `bookwright init <NAME>` or `bookwright init --here` (FR-002).                                                                        |
| `project_name`         | `str \| None`               | yes      | Raw `PROJECT_NAME` after FR-021a stripping. `None` when `mode == "here"`.                                                                                        |
| `project_slug`         | `str`                       | yes      | Slugified form (FR-021, R3). For `here` mode it is the slug of the current directory's basename.                                                                 |
| `project_root`         | `str` (absolute POSIX path) | yes      | The directory the command ultimately wrote into. For `named` mode: `Path.cwd() / project_slug`. For `here` mode: `Path.cwd()`.                                   |
| `title`                | `str`                       | yes      | Manifest title — preserves user casing (FR-021).                                                                                                                  |
| `authors`              | `list[str]`                 | yes      | Per R1 resolution. Always non-empty (sentinel `"Unknown Author"` if all sources fail; FR-016).                                                                    |
| `language`             | `str`                       | yes      | ISO 639-1 (per R2). Default `"es"` when detection fails.                                                                                                          |
| `integration_key`      | `str`                       | yes      | One of `list_keys()` (FR-005, FR-007). Default `"claude"`.                                                                                                       |
| `integration_skills_dir` | `str`                     | yes      | Resolved relative-path string. Comes from `integration_cls().resolve_skills_dir(parsed_options)` (iteration 3) — single source of truth (FR-005, FR-013).        |
| `integration_options`  | `dict[str, str \| bool]`    | yes      | Output of `parse_options(raw, integration_cls)`. Empty dict when `--integration-options` was not supplied (FR-020).                                              |
| `no_git`               | `bool`                      | yes      | The `--no-git` flag value (FR-023).                                                                                                                              |
| `force`                | `bool`                      | yes      | The `--force` flag value (FR-026, FR-028 — `--force` does NOT bypass "already initialized").                                                                     |
| `json_output`          | `bool`                      | yes      | The `--json` flag value (FR-032, FR-033).                                                                                                                        |
| `git_status`           | `Literal["initialized", "skipped_by_flag", "skipped_no_binary", "skipped_existing_repo"]` | yes | Records what actually happened at git time (FR-022..FR-025). Populated by `_init_git.init_and_commit` or its skip branches. |
| `deprecated_flags_seen` | `list[str]`                | yes      | Empty unless `--ai` was used (FR-003). Used by the envelope's `warnings` array (§ 4).                                                                            |

**Validation rules**:

- `integration_key` MUST be in `bookwright.integrations.list_keys()` at
  construction time. Pydantic does the membership check via a
  `field_validator`; failure produces an `UnknownIntegrationError`-equivalent
  (the envelope serialises the same `code: "unknown_integration"`).
- `integration_skills_dir` MUST be a relative POSIX path (no leading
  `/`); iteration-3 `setup()` already enforces "inside the project
  root" semantics. The validator is "starts with no `/`, contains no
  `..`."
- `language` is validated against the iteration-2
  `ISO_639_1_CODES` set so a bad locale fallback can never sneak
  through.
- `authors` length ≥ 1 (matches `BookBlock.authors` validator).

**Relationships**:

- `ResolvedInvocation` is the construction input to
  `Manifest.build(title=..., authors=..., integration_key=...,
  integration_skills_dir=..., integration_options=...,
  language=...)`. The manifest is therefore a *derived* view of this
  struct + the iteration-2 defaults.
- `ResolvedInvocation` is the source for
  `InitOptionsRecord.options` (§ 1).
- `ResolvedInvocation` is the source for the success-path JSON
  envelope (§ 4.1).

**Storage**: in-memory during the command; serialised into
`init-options.json` and into the success-path stdout envelope.

---

## 3. `BackupLedger`

**Purpose**: In-memory rollback record (FR-030). Every filesystem
mutation `init` performs is appended here before the bytes hit disk;
on success the ledger is reset; on any exception the ledger is
replayed in reverse to restore the project root to byte-for-byte its
pre-invocation state (SC-005).

**Shape**: simple list of `BackupEntry` dataclass instances in
`bookwright.commands._init_scaffold`.

```python
@dataclass(frozen=True)
class BackupEntry:
    target: Path                    # absolute path that was about to be written
    backup_path: Path | None        # None  → target did not exist (newly created)
                                    # Path  → target existed; sibling backup file
    was_directory: bool             # True  → mkdir entry; False → file write
```

**Validation rules** (enforced by the writer helper, not by the
dataclass itself):

- `target` MUST be inside the project root. The writer refuses any
  path outside (FR-014).
- When `backup_path is not None` it MUST be a sibling of `target`
  under the project root (no `/tmp/` backups — they would violate
  FR-014's "no files outside project root").
- The ledger MUST be append-only during scaffolding. The rollback
  routine consumes it in reverse-iteration order.

**Lifetime**:

- Created at the start of `_init_scaffold.scaffold(...)`.
- Appended to by every `write(...)`, `mkdir(...)`, and the
  `git init` step (which adds a single `BackupEntry(target=root /
  ".git", backup_path=None, was_directory=True)` before invoking
  the wrapper).
- On scaffold success: every `backup_path` is `unlink`-ed; the
  ledger object is discarded.
- On scaffold exception: walked in reverse — `backup_path` entries
  restored via `shutil.move`, newly-created files unlinked,
  newly-created directories removed via `shutil.rmtree`. For
  directory-form invocations (`mode == "named"`), the outermost
  `project_root` directory itself is also removed (see R4 — a
  failure on the very first write should leave nothing behind).

**Storage**: in-memory only. Never serialised. The backup files
themselves are on-disk siblings of their targets and are deleted on
success.

---

## 4. JSON envelope shapes (out-of-band but pinned here)

The envelope shape is contractual (Principle IX) and tested by
subprocess in `tests/commands/test_init_json_envelope.py`. It is fixed
*here* so the contract document
([`contracts/init_command.md`](contracts/init_command.md)) can
reference rather than restate.

### 4.1 Success envelope

Emitted to **stdout** as a single JSON document followed by exactly
one `\n` (matching the iteration-1 `version --json` pattern).

```json
{
  "status": "ok",
  "project_root": "<absolute POSIX path>",
  "project_slug": "mi-libro",
  "mode": "named",
  "integration": {
    "key": "claude",
    "skills_dir": ".claude/skills",
    "options": {}
  },
  "git_status": "initialized",
  "warnings": ["..."],
  "bookwright_version": "0.0.1"
}
```

Field-by-field:

- `status`: literal `"ok"`. Distinguishes success from error.
- `project_root`, `project_slug`, `mode`, `integration.*`,
  `git_status`, `bookwright_version`: mirror the
  `ResolvedInvocation` fields (§ 2). `git_status` is the
  literal-string union.
- `warnings`: array of one-line strings; non-empty only when a
  deprecation (`--ai`), git-not-found, or author-not-detected
  warning fired. Each warning is *also* on stderr per FR-032;
  the JSON copy is for agent consumers that don't read stderr.

`json.dumps(...)` uses `separators=(",", ":")` for the stdout copy
(matches existing `version --json` / `check --json` pattern); the
`init-options.json` on-disk copy uses `indent=2` for human review.

### 4.2 Error envelope

Emitted to **stdout** as a single JSON document followed by `\n`.
The process exits non-zero (specific code per § 5).

```json
{
  "status": "error",
  "code": "<stable error code, snake_case>",
  "message": "<human-readable one-line>",
  "details": { "...": "..." },
  "rolled_back": true,
  "bookwright_version": "0.0.1"
}
```

- `code` is one of the documented codes in
  [`contracts/init_command.md`](contracts/init_command.md) § Error
  codes. For errors that originate in the iteration-3 layer
  (`UnknownIntegrationError`, `UnknownOptionError`,
  `MalformedOptionError`), the code is the iteration-3 `error.code`
  verbatim and `details` is the iteration-3 `error.to_dict()`
  payload minus `code` and `message` (which are hoisted up).
- `rolled_back`: `true` when the failure happened after some bytes
  had been written to disk and the backup-ledger replay completed
  successfully; `false` when the failure happened before any
  filesystem mutation (most validation errors), or when rollback
  itself failed (rare — emitted with a `details.rollback_error`
  field describing the partial state).

### 4.3 Stderr contract under `--json`

Even with `--json` set, warnings still go to stderr (FR-032). Each
warning is one line, prefixed by a stable token so an agent that
wishes to parse them can:

```
bookwright: warning: --ai is deprecated; use --integration
bookwright: warning: git not found on PATH; project created without a repository
bookwright: warning: author could not be resolved from git config or $USER; manifest uses 'Unknown Author'
```

Errors NEVER go to stderr under `--json` — they are emitted as the
JSON envelope on stdout only. (Without `--json`, errors are one
human-readable line on stderr, no stdout output.)

---

## 5. Exit codes

| Code | Meaning                                                         | Triggering FRs            |
|------|-----------------------------------------------------------------|---------------------------|
| `0`  | Success — project scaffolded, manifest written, git initialised (or deliberately skipped). | FR-022, FR-023, FR-024, FR-025 |
| `2`  | CLI usage error: mutual-exclusion violation, removed flag, validation failure. | FR-002, FR-004, FR-007, FR-021a |
| `3`  | "Already initialized" refusal (`--here` inside an existing project, even with `--force`). | FR-028 |
| `4`  | Target-directory conflict (non-empty `--here` without `--force` in non-interactive mode; or non-empty named-mode target without `--force`). | FR-026, FR-029 |
| `5`  | Integration setup or option parsing failed (`UnknownIntegrationError`, `UnknownOptionError`, `MalformedOptionError`, `InvalidOptionDeclarationError`). | FR-006, FR-007 |
| `6`  | Filesystem error after scaffold began; backup-ledger rolled back. The error envelope carries the underlying cause. | FR-030, FR-031 |
| `7`  | Git error: `git init` or `git commit` failed and the user did not pass `--no-git`. The stderr/JSON carries the verbatim git stderr. | FR-022 last clause |

Exit codes are part of the contract and asserted by
`tests/commands/test_init_*.py` for each documented failure mode. The
choice of distinct codes (rather than collapsing everything to `1`)
matches the spec's named edge cases and lets shell-script wrappers
(future iteration 11 fixtures) branch on them without re-parsing the
JSON envelope.
