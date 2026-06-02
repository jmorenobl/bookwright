# Contract — `bookwright validate`

Runs all active validators over the project and reports the collected violations.
Binding for FR-008..014 and Principle IX. Registered in `cli.py` via
`app.command("validate")(validate.run)`.

## Synopsis

```
bookwright validate [--scope PATH] [--severity LEVEL] [--json]
```

| Option | Type | Default | Meaning |
|---|---|---|---|
| `--scope` | path | none | Limit **reported** violations to those whose source falls within this file or directory (FR-009). |
| `--severity` | `error`\|`warning`\|`info` | `info` | **Threshold**: report this level and above (`error>warning>info`) (FR-010). |
| `--json` | flag | off | Emit one JSON document on stdout and nothing else (FR-011, Principle IX). |

`--scope` and `--severity` affect **displayed output only**. The failure signal is
computed from **all** violations before filtering (FR-013), so a filter can never
hide an error from CI.

## Behaviour

1. Locate project root (`find_project_root`); load `manifest.toml`.
2. Resolve the engine from `manifest.bookwright.indexer`; load
   `manifest.paths.graph` if it exists, else use an empty engine (no error — "no
   graph yet" edge case → zero graph findings).
3. Discover built-in + custom validators; resolve the active set from
   `[validators]` (validator-protocol.md). Unknown name → exit 2.
4. If `--scope` given, resolve it under the root; a path that does not exist or
   lies outside the project → "scope matched no content", exit 2.
5. Run each active validator with per-validator isolation (FR-014); collect
   `violations` (deduped) and `errors`.
6. Render: human (grouped by validator, stdout) or `--json` (one document, stdout).
   Progress/notes go to **stderr**.
7. Exit per the gate.

## Exit codes

| Code | When |
|---|---|
| `0` | No error-severity violation (gate clean). Warnings/info alone still exit 0 (FR-013). |
| `1` | At least one **error-severity** violation in the unfiltered set (gate fail, FR-013/SC-006). |
| `2` | Config/usage error: no project, missing/invalid manifest, unknown validator name (FR-007), or scope matching no content. |

Exit codes are independent of `--json` (Principle IX): a non-zero code is always
set on gate fail / error, with the JSON body carrying the detail.

## JSON success envelope (`--json`)

One line, `json.dumps(payload, separators=(",", ":")) + "\n"` (matching the `graph`
commands). Shape (SC-004 — exactly one entry per **reported** violation):

```json
{
  "status": "violations",
  "failed": true,
  "violations": [
    {"validator":"temporal","severity":"error",
     "message":"event 'B' (1884) is asserted to follow 'A' (1885)",
     "source":"bible/timeline.md:5",
     "triples":[["…#evB","…TemporalRelations.owl#follows","…#evA"]]}
  ],
  "errors": [
    {"validator":".bookwright/validators/broken.py","phase":"load",
     "message":"SyntaxError: invalid syntax (line 3)"}
  ],
  "summary": {
    "ran": ["character_presence","focalization","setting_continuity","temporal"],
    "total": 7, "reported": 1,
    "by_severity": {"error":2,"warning":4,"info":1}
  }
}
```

- `status`: `"ok"` when the reported list is empty, else `"violations"`.
- `failed`: the gate (any error-severity violation pre-filter) — drives exit 1.
- `total`: unfiltered violation count; `reported`: count in `violations[]`.
- `by_severity`: counts over the **unfiltered** set.

## JSON / human error envelope (config & usage failures)

For exit-2 failures, the same single-document discipline applies. JSON:

```json
{"status":"error","code":"unknown_validator","message":"unknown validator(s): foo","details":{"names":["foo"]}}
```

Codes: `no_project`, `invalid_manifest`, `unknown_validator`, `empty_scope`.
Non-`--json` mode writes a single `bookwright: error: <message>` line to stderr.

## Invariants (tested)

- Under `--json`, stdout is exactly one parseable JSON document; **all** human prose
  is on stderr (Principle IX, SC-004).
- `failed` / exit code reflect the **unfiltered** error-severity count regardless of
  `--scope` / `--severity` (FR-013, SC-006).
- Re-running on an unchanged project yields a byte-identical JSON `violations[]`
  ordering (FR-019, SC-003).
- A clean project → `status:"ok"`, `failed:false`, exit 0 (SC-002).
