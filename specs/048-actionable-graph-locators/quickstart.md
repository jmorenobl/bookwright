# Quickstart — Actionable locators for graph-consumer validators

Runnable validation scenarios proving DEBT-015 is closed. Details live in
[`contracts/graph-consumer-locators.md`](./contracts/graph-consumer-locators.md)
and [`data-model.md`](./data-model.md); this is the run/verify guide.

## Prerequisites

```bash
uv sync
```

## Scenario A — `temporal` rules a/b/c point to the timeline file (US2)

A `bible/timeline.md` with a follows/precedes **cycle** (rule a), an ordered+
overlapping **pair** (rule b), and a containment-vs-order **conflict** (rule c).

```bash
uv run pytest tests/validation/test_temporal.py -q
```

**Expected**: each of the rule (a)/(b)/(c) `temporal` violations carries a `source`
that resolves to `bible/timeline.md` (a line-bearing `bible/timeline.md:<line>`,
exactly as rule (d) already produces), not `null`. A two-build assertion shows the
`source` is byte-identical across builds (FR-002).

## Scenario B — a defective research anchor points to its file + authored name (US1)

A research project with one under-reliable / unsourced anchor (e.g. promoting
`paginas-arrancadas`, constraining `El cuaderno de bitácora`, authored in
`bible/research/puerto.md`).

```bash
uv run pytest tests/validation/test_factual_anchor.py -q
```

**Expected**: the `factual_anchor` violation carries
`source == "bible/research/puerto.md"` (not `null`) and a message naming the anchor
by its authored handle `paginas-arrancadas -> El cuaderno de bitácora` (the
`promotes` id alone when no `constrains` target), **never** the uuid7 URI tail.

## Scenario C — `factual_anchor` and `status` agree (US1 / SC-003)

```bash
uv run pytest tests/validation/test_factual_anchor.py -k agreement -q
```

**Expected**: for the same anchor, the `factual_anchor` finding and the `status`
`anchor_gaps` entry name and locate it **identically** (same handle, same file) —
both resolved through the shared `anchor_handle` helper, so they cannot diverge.

## Scenario D — end-to-end through the real CLI (production path)

```bash
uv run pytest tests/e2e/test_research_workflow.py -q
```

**Expected**: after a real `graph build` → `validate --json` over the committed
`tiny-historical` fixture, the `factual_anchor` findings carry a non-`null`
`bible/research/<topic>.md` `source` and a uuid7-free, handle-based message —
proving the in-process corpus resolution works across the build→validate process
boundary (research D1), not only in the hand-built unit harness.

## Full gate

```bash
uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest
```

**Expected**: all four gates green; the finding **count / severity / gate outcome**
on every existing fixture is unchanged from before the iteration (SC-005) — only
`source` and message identifiers differ.
