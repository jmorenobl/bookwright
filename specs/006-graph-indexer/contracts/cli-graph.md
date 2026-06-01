# Contract — `bookwright graph` CLI

Two read-only subcommands. Both honor Principle IX: under `--json`, **exactly one
JSON document on stdout and nothing else**; all human prose/progress on stderr;
non-zero exit on error even with `--json`.

JSON is single-line: `json.dumps(payload, separators=(",", ":")) + "\n"`.

---

## `bookwright graph build [--force] [--json]`

Reads the current project's bible, builds the graph, writes `bible/graph.ttl`
(path from `manifest.toml > [paths] graph`).

| Flag | Default | Effect |
|---|---|---|
| `--force` | False | Rebuild from scratch, ignoring any cache. (v0 always full-rebuilds; accepted for forward-compat.) |
| `--json` | False | Emit the build report as one JSON doc on stdout. |

### Success (stdout, `--json`)
```json
{"status":"ok","files_processed":6,"entities":10,"triples":48,"skipped":[],"unknown_keys":[],"unresolved_participants":[],"graph_path":"bible/graph.ttl"}
```
Human form (stderr): one summary line per metric. `unknown_keys` and
`unresolved_participants` (FR-019) are soft warnings — populated when present but
never changing the exit code.

### Completed with skipped files (FR-013, exit code **4**)
```json
{"status":"ok","files_processed":6,"entities":9,"triples":44,"skipped":[{"path":"bible/characters/broken.md","reason":"invalid frontmatter: ..."}],"unknown_keys":[],"unresolved_participants":[],"graph_path":"bible/graph.ttl"}
```
`status` stays `"ok"` (valid files were processed) but a non-empty `skipped`
array + exit 4 distinguish it from a clean build.

### Errors (exit non-zero, no partial graph)
| Code | Exit | When |
|---|---|---|
| `not_a_project` | 2 | No `manifest.toml` in cwd/ancestors. |
| `missing_directory` | 2 | `bible/` or `manuscript/` absent (names which). |
| `unknown_indexer` | 2 | Manifest names an unregistered engine (lists available). |
| `slug_collision` | 3 | Two entities of one type share an identifier (names id + both paths). |

Error doc shape (`--json`):
```json
{"status":"error","code":"slug_collision","message":"...","details":{"identifier":"...","sources":["...","..."]}}
```

---

## `bookwright graph query "<SPARQL>" [--json]`

Loads `bible/graph.ttl` and runs the SPARQL query.

### Success (stdout, `--json`) — FR-004
```json
{"status":"ok","results":[{"c":"https://example.org/my-novel/character/aparici"}],"count":1}
```
- Empty match → `{"status":"ok","results":[],"count":0}`, exit 0 (FR-016).
- Human form (no `--json`): a `rich` table of rows on stdout; progress on stderr.

### Errors (exit non-zero)
| Code | Exit | When |
|---|---|---|
| `not_a_project` | 2 | No `manifest.toml`. |
| `graph_not_built` | 2 | `bible/graph.ttl` missing → "run `graph build` first". |
| `unknown_indexer` | 2 | Manifest names an unregistered engine. |
| `invalid_query` | 3 | Malformed SPARQL; **no partial rows** emitted. |

Error doc shape (`--json`): `{"status":"error","code":"invalid_query","message":"..."}`.

---

## Wiring
`commands/graph/__init__.py` exposes a Typer sub-app registered in `cli.py` via
`app.add_typer(graph.app, name="graph")`. `build` and `query` live in their own
modules (Principle IV).
