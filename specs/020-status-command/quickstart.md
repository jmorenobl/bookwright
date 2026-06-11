# Quickstart — validating `bookwright status` (iteration 020)

Runnable scenarios proving the feature end-to-end. Shapes and exit codes are
normative in [contracts/cli-status.md](contracts/cli-status.md); state model
in [data-model.md](data-model.md).

## Prerequisites

```bash
uv sync                      # deps + dev group
uv run pytest tests/status tests/commands/test_status.py tests/commands/test_status_errors.py
```

All four gates must stay green:

```bash
uv run ruff check && uv run ruff format --check
uv run mypy --strict
uv run pytest                # ≥ 80 % coverage enforced
```

## Scenario 1 — facts + next actions on a known-state project (US1, US2)

Use the research E2E fixture (`tests/fixtures/tiny-historical`, iteration
016), which carries open questions, anchors, and validation findings. From a
scratch copy:

```bash
cp -r tests/fixtures/tiny-historical /tmp/qs-status && cd /tmp/qs-status
uv run bookwright status --json | python -m json.tool
```

**Expected**: exit 0; one JSON document with `status:"ok"`; `state.phase`
echoing `manifest.toml`'s `book.status`; `open_questions` /
`unresolved_anchors` / `low_reliability_findings` each carrying matching
`count` and `items` (authored ids + relpaths, never URIs);
`validation.counts` per severity; `next_actions` containing the
`bookwright-research` recommendation whose reason cites the queue count.

## Scenario 2 — determinism: byte-identical repeat (US3, SC-002)

```bash
uv run bookwright status --json > /tmp/run1.json
cp .bookwright/cache/status.json /tmp/cache1.json
uv run bookwright status --json > /tmp/run2.json
cmp /tmp/run1.json /tmp/run2.json          # identical
cmp /tmp/run1.json /tmp/cache1.json        # stdout ≡ cache
cmp /tmp/cache1.json .bookwright/cache/status.json
```

**Expected**: all three `cmp`s silent (byte-identical), even though
`bible/graph.ttl` was refreshed (its minted URIs may differ — that cache is
exempt from byte-identity).

## Scenario 3 — agreement with the owning tools (SC-003)

```bash
uv run bookwright status --json > /tmp/st.json
uv run bookwright validate --json > /tmp/val.json || true   # validate may gate-exit 1
uv run bookwright focus show --json > /tmp/focus.json
```

**Expected**: `state.validation.counts` equals validate's `by_severity`;
top-level `focus` equals `focus show`'s `focus`.

## Scenario 4 — healthy project ⇒ empty/minimal actions (US2, edge case)

On a fixture with no open questions, no violations, and a `[focus]` block
(e.g. `tiny-novel` after `bookwright focus set --target …`):

```bash
uv run bookwright status --json
```

**Expected**: exit 0; `next_actions` is `[]` (or, without focus set, exactly
the `bookwright focus set` recommendation).

## Scenario 5 — v0.2-era / degraded projects (FR-013, SC-006)

```bash
# no [focus], no bible/research/ — must still succeed
cp -r tests/fixtures/tiny-novel /tmp/qs-v02 && cd /tmp/qs-v02
uv run bookwright status --json
```

**Expected**: exit 0; `focus` is `null`; research facts all
`{"count":0,"items":[]}`; at most one bootstrap action. With the bible
emptied out, `graph.available`/`entities` reflect the absence and the report
still exits 0.

## Scenario 6 — failure envelopes (US3-AS3, clarification #3)

```bash
cd /tmp && uv run bookwright status --json; echo "exit=$?"
# expected: {"status":"error","code":"no_project",...} and exit=2
```

On a corpus with malformed research YAML: same `ResearchError` envelope and
exit 2 as `graph build`. On a corpus with a skipped bible file (broken
front-matter): `code:"skipped_sources"`, exit 4, previous
`.bookwright/cache/status.json` (if any) untouched.

## Scenario 7 — corpus untouched (SC-007)

```bash
find bible manuscript -type f -name '*.md' -exec md5 {} + > /tmp/before.txt
uv run bookwright status --json > /dev/null
find bible manuscript -type f -name '*.md' -exec md5 {} + > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt       # empty: only graph.ttl + status.json changed
```

## Scenario 8 — rule table in isolation (SC-005)

```bash
uv run pytest tests/status/test_rules.py -q
```

**Expected**: every rule in `RULES` is exercised by a synthetic
`StatusState` with no graph, no disk, no project — exact actions, exact
order, repeat-call equality.
