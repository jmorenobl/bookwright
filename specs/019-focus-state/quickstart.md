# Quickstart: Authored focus state

End-to-end walkthrough of the `bookwright focus` commands. Assumes a Bookwright
project (a directory with `manifest.toml`).

## 1. Record what you're working on

```console
$ bookwright focus set --target "arco de Berlín" --notes "cerrar la timeline del cap-04"
focus set: target="arco de Berlín", updated_at=2026-06-11
```

This creates a `[focus]` block in `manifest.toml`:

```toml
[focus]
target = "arco de Berlín"
notes = "cerrar la timeline del cap-04"
updated_at = "2026-06-11"
```

Every other block, comment, and the ordering in `manifest.toml` is preserved
byte-for-byte.

## 2. Read it back

```console
$ bookwright focus show
target:     arco de Berlín
notes:      cerrar la timeline del cap-04
updated_at: 2026-06-11
```

For tooling, ask for JSON (exactly one document on stdout):

```console
$ bookwright focus show --json
{"status":"ok","focus":{"target":"arco de Berlín","notes":"cerrar la timeline del cap-04","updated_at":"2026-06-11"}}
```

## 3. Update only the target (keep the notes)

Omitting `--notes` preserves the existing notes; `target` and `updated_at`
refresh:

```console
$ bookwright focus set --target "arco de París"
$ bookwright focus show --json
{"status":"ok","focus":{"target":"arco de París","notes":"cerrar la timeline del cap-04","updated_at":"2026-06-11"}}
```

To clear the notes explicitly, pass an empty string:

```console
$ bookwright focus set --target "arco de París" --notes ""
$ bookwright focus show --json
{"status":"ok","focus":{"target":"arco de París","notes":"","updated_at":"2026-06-11"}}
```

## 4. Clear the focus

```console
$ bookwright focus clear
focus cleared
$ bookwright focus show --json
{"status":"ok","focus":null}
```

Clearing when there is no focus is a successful no-op:

```console
$ bookwright focus clear --json
{"status":"ok","cleared":false}
```

## Error cases

Empty `--target` is rejected and the manifest is left unchanged:

```console
$ bookwright focus set --target "   "
bookwright: error: --target must be a non-empty string
$ echo $?
2
```

```console
$ bookwright focus set --target "" --json
{"status":"error","code":"focus_target_empty","message":"--target must be a non-empty string"}
```

Running outside a project, or against an invalid manifest, fails with the same
clear errors every other manifest-reading command produces
(`project_not_found` / `invalid_manifest`, exit 2). A manifest whose
`[focus].updated_at` is not a valid `YYYY-MM-DD` date surfaces as a normal
`invalid_manifest` validation error — never a crash.

## Acceptance check (maps to the spec)

| Step | Spec coverage |
|---|---|
| 1 | US1 / FR-006, FR-009 |
| 2 | US2 / FR-003, FR-004 |
| 3 | FR-007 (partial notes) |
| 4 | US3 / FR-005, FR-010 |
| Error cases | FR-008, FR-011, FR-013 |
