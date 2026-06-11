# CLI Contract: `bookwright focus`

The `focus` command group reads, writes, and clears the authored `[focus]` block
in `manifest.toml`. Every subcommand accepts `--json` and, when given, emits
**exactly one** JSON document on stdout and nothing else (Principle IX); human
prose and progress go to stderr.

Sub-app wiring: `commands/focus/` is a `typer.Typer(name="focus",
no_args_is_help=True)`; `show`/`set`/`clear` self-register at import; the root CLI
mounts it via `app.add_typer(focus.app, name="focus")`.

All three subcommands locate the project via `find_project_root()` and load the
manifest via `Manifest.load(...)`; the shared fault rows below apply to each.

## Exit codes (all subcommands)

| Code | Meaning |
|---|---|
| `0` | Success — **including** `show`/`clear` when no `[focus]` exists. |
| `2` | Any error: not a Bookwright project, invalid manifest, or empty `--target`. The error `code` field distinguishes the kind. |

## Shared error envelope

On failure under `--json`, stdout carries the unified envelope
`{"status":"error","code":…,"message":…[,"details":…]}` (owned by
`BookwrightError.to_json()`). Without `--json`, a single
`bookwright: error: <message>` line goes to stderr.

| Condition | `code` | Exit |
|---|---|---|
| Not inside a project (no `manifest.toml`) | `project_not_found` | 2 |
| Manifest invalid (syntax/validation, incl. bad `focus.updated_at`) | `invalid_manifest` | 2 |
| `focus set` with empty/whitespace `--target` | `focus_target_empty` | 2 |

---

## `bookwright focus show [--json]`

Read-only. Displays the current focus.

**Behaviour**

- Block present, human mode: print `target`, `notes`, `updated_at` legibly on
  **stdout**.
- Block present, `--json`: emit
  `{"status":"ok","focus":{"target":"…","notes":"…","updated_at":"YYYY-MM-DD"}}`.
- Block absent, human mode: print `no focus defined` on **stderr**; exit `0`.
- Block absent, `--json`: emit `{"status":"ok","focus":null}`; exit `0`.

**Success JSON (present)**

```json
{"status":"ok","focus":{"target":"arco de Berlín","notes":"cerrar timeline cap-04","updated_at":"2026-06-11"}}
```

**Success JSON (absent)**

```json
{"status":"ok","focus":null}
```

Maps: FR-003, FR-004, FR-005, FR-013.

---

## `bookwright focus set --target <text> [--notes <text>] [--json]`

Create or update the `[focus]` block; preserve all other manifest content;
stamp `updated_at` with today's date.

**Arguments**

| Flag | Type | Required | Notes |
|---|---|---|---|
| `--target` | `str` | yes | Empty/whitespace-only ⇒ `focus_target_empty`, manifest unchanged (FR-008). A non-empty value is stored **verbatim** (not trimmed). |
| `--notes` | `str` (optional) | no | Omitted ⇒ preserve existing notes / `""` on create; `--notes "X"` ⇒ set; `--notes ""` ⇒ clear (FR-007). |
| `--json` | flag | no | Emit the success/error envelope. |

**Behaviour**

- Absent block ⇒ create `[focus]` with `target`, resolved `notes`, and
  `updated_at = today`.
- Present block ⇒ update `target`, apply the partial-`notes` rule, refresh
  `updated_at = today`.
- Writes via `Manifest.set_focus(...)` → `Manifest.dump(..., overwrite=True)`;
  every other block, comment, and ordering round-trips byte-for-byte (FR-009,
  SC-002).
- Human mode: confirmation (e.g. `focus set: target="…", updated_at=…`) on
  **stderr**.

**Success JSON**

```json
{"status":"ok","focus":{"target":"arco de Berlín","notes":"decidir POV","updated_at":"2026-06-11"}}
```

(The echoed `focus` reflects the freshly written block.)

**Empty-target error JSON**

```json
{"status":"error","code":"focus_target_empty","message":"--target must be a non-empty string"}
```

Maps: FR-006, FR-007, FR-008, FR-009, FR-013.

---

## `bookwright focus clear [--json]`

Remove the `[focus]` block; preserve the rest of the manifest.

**Behaviour**

- Block present ⇒ remove `[focus]` (via `Manifest.clear_focus()` →
  `dump(overwrite=True)`); report success.
- Block absent ⇒ no-op, success, clear message that there was nothing to clear
  (FR-010).
- Human mode: `focus cleared` / `no focus to clear` on **stderr**.

**Success JSON (removed)**

```json
{"status":"ok","cleared":true}
```

**Success JSON (no-op)**

```json
{"status":"ok","cleared":false}
```

Maps: FR-009, FR-010, FR-013.

> `cleared` is a boolean discriminator so an agent can tell a real removal from a
> no-op without a second read; both are `status:"ok"`, exit `0`.
