# CLI Contract — `bookwright status`

Binding contract for the verb added in iteration 020. Shapes referenced from
[data-model.md](../data-model.md); error envelope per iteration 018
(Principle IX).

## Invocation

```
bookwright status [--json]
```

- Registered in `cli.py` as `app.command("status")(status.run)` — one module,
  `src/bookwright/commands/status.py` (Constitution IV).
- No other flags in this iteration. No arguments.
- Read-only over the corpus (SC-007): the only writes are the derived
  `bible/graph.ttl` refresh and `.bookwright/cache/status.json`.

## Channel discipline (Principle IX)

| Mode | stdout | stderr |
|---|---|---|
| `--json`, success | exactly one JSON document (below), nothing else | optional human progress/prose |
| `--json`, failure | exactly one iteration-018 error envelope, nothing else | optional prose |
| human, success | the readable report (FR-011) | progress/warnings |
| human, failure | nothing | `bookwright: error: <message>` |

## Success document (exit 0)

```json
{
  "status": "ok",
  "focus": {"target": "…", "notes": "…", "updated_at": "YYYY-MM-DD"},
  "state": {
    "phase": "drafting",
    "graph": {"available": true, "entities": 12, "triples": 240},
    "open_questions": {"count": 2, "items": [
      {"id": "q-mercury", "text": "How was mercury handled in 1880s labs?", "file": "bible/research/_index.md"}
    ]},
    "unresolved_anchors": {"count": 1, "items": [
      {"promotes": "rel-001", "constrains": "timeline", "file": "bible/research/medicine.md", "problems": ["under_reliable"]}
    ]},
    "low_reliability_findings": {"count": 1, "items": [
      {"id": "rel-001", "best_reliability": "baja", "file": "bible/research/medicine.md"}
    ]},
    "validation": {"counts": {"error": 1, "warning": 3, "info": 0}, "ran": ["character_presence", "factual_anchor", "focalization", "setting_continuity", "temporal"]}
  },
  "next_actions": [
    {"skill": "bookwright-research", "prompt": "…fixed English template listing the queue…", "reason": "2 open research questions and 1 unresolved anchor"}
  ]
}
```

(Values illustrative; key set and shapes normative.)

- `focus` is `null` when no `[focus]` block exists (matches
  `focus show --json`).
- Every item-list fact carries **both** `count` and `items` (FR-011a), items
  ordered by corpus-stable keys (data-model §2). `count == len(items)`
  always.
- `next_actions` may be `[]` — a healthy project's valid answer (FR-015 edge
  case). Each action always carries all three keys (SC-004).
- Encoding: `json.dumps(payload, separators=(",", ":")) + "\n"` — identical
  bytes to the cache file.
- Determinism: same corpus ⇒ byte-identical document (SC-002). No minted
  URIs, no timestamps, no environment data.

## Cache side effect (every successful run, both modes)

`.bookwright/cache/status.json` is (re)written with the byte-identical
success document. Directory created if missing. Never read back (FR-012).
On failure the previous cache file, if any, is left untouched.

## Exit codes & error envelopes

| Exit | Condition | Envelope `code` |
|---|---|---|
| 0 | report computed — regardless of how unhealthy the state is (FR-015); includes degraded/absent-information states (FR-013) | — |
| 2 | not a project | `no_project` |
| 2 | manifest unparseable/invalid | `invalid_manifest` |
| 2 | unknown indexer engine | `invalid_manifest` |
| 2 | malformed research corpus (`ResearchError`) | the error's own code |
| 3 | bible slug collision (`SlugCollisionError`) | the error's own code |
| 4 | ≥ 1 bible file skipped by the build (malformed front-matter — corrupt corpus, research.md D4) | `skipped_sources`, `details` lists `{path, reason}` per skipped file |

All envelopes are produced by `BookwrightError.to_json()` subclasses — never
hand-rolled dicts. Exit parity with `graph build` on the same corpus is
normative for rows 2–4 (clarification #3), **except** missing build
prerequisites (absent `bible/` dir or manuscript), which degrade to a
successful exit-0 report with `graph.available == false` (FR-013,
research.md D5) instead of `graph build`'s exit 2.

## Degraded-state guarantees (FR-013, SC-006)

- v0.2-era project (no `[focus]`, no `bible/research/`): exit 0; `focus`
  `null`; research facts all `{"count": 0, "items": []}`; at most one
  bootstrap action.
- Nothing to build the graph from: exit 0; `graph.available` `false`;
  `next_actions` empty or a single bootstrap action.

## Conformance tests (minimum)

1. `--json` stdout parses as a single JSON document; nothing else on stdout
   (US3-AS1).
2. Double run on unchanged corpus: stdout bytes and cache bytes identical
   across runs and to each other (US3-AS4, SC-002).
3. Known-state fixture (N open questions, unresolved anchors, 1 validation
   error): exact facts and exact `next_actions` (US1, US2).
4. Clean fixture: `next_actions == []` or single minimal action; exit 0.
5. Each error row above: correct envelope code + exit, one document on
   stdout under `--json`.
6. SC-003 parity: validation counts equal `bookwright validate --json` run
   after `status`; focus equals `focus show --json`.
7. SC-007: corpus files byte-identical before/after a run.
