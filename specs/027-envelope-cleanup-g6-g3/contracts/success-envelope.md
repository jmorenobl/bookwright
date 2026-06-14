# Contract: success-envelope byte-identity (US1, FR-001…FR-007)

The interface under contract is the **stdout** of each `--json` command in scope.
The guarantee is byte-level: same keys, same values, same key order, same compact
separators (`,`/`:`), same single trailing `\n`. Exit codes unchanged.

## Encoding (single-sourced in `commands/_envelope.py`)

```
render_json(payload) == json.dumps(payload, separators=(",", ":")) + "\n"
ok_payload(**fields) == {"status": "ok", **fields}   # status first, fields in call order
emit_json(payload)   == sys.stdout.write(render_json(payload))
```

## In-scope commands and their pinned stdout shape

| Command | stdout (one JSON doc + `\n`) | Built via |
|---|---|---|
| `check --json` (all deps OK) | `{"ok":true,"checks":[{"name":"python_version","status":"ok","detail":"<v>"},{"name":"dependency:typer","status":"ok"}, …]}` | hand dict (kept) |
| `focus show --json` (set) | `{"status":"ok","focus":{"target":…,"notes":…,"updated_at":…}}` | `ok_payload(focus=…)` |
| `focus show --json` (none) | `{"status":"ok","focus":null}` | `ok_payload(focus=None)` |
| `focus set --json` | `{"status":"ok","focus":{"target":…,"notes":…,"updated_at":…}}` | `ok_payload(focus=…)` |
| `focus clear --json` | `{"status":"ok","cleared":true\|false}` | `ok_payload(cleared=…)` |
| `graph query --json` | `{"status":"ok","results":[…],"count":N}` | `ok_payload(results=…, count=…)` |
| `graph build --json` | `{"status":"ok","files_processed":…,"entities":…,"triples":…,"skipped":[…],"unknown_keys":[…],"unresolved_references":[…],"sources":…,"findings":…,"anchors":…,"research_warnings":[…],"graph_path":…}` | `BuildReport.to_json()` |

## Acceptance (machine-checked, `tests/commands/test_success_envelopes.py`)

1. For each command above, captured stdout **bytes** equal the pinned baseline.
2. `check`'s document has **no** top-level `status` key (it stays `{"ok",…}`).
3. Exit codes: `check` 0 (all OK) / 1 (any fail); `focus *` 0; `graph query` 0;
   `graph build` 0 (clean) / 4 (skips) — unchanged from current.
4. `graph build`'s only changed byte vs. the pre-027 document is the key
   `unresolved_participants` → `unresolved_references` at the same position
   (US3 carve-out; everything else identical).

## Out of contract

`init`, `integration`, `validate`, `version`, `status` (not touched). The
error-envelope path (`BookwrightError.to_json()` / `emit_error`) is unchanged.
