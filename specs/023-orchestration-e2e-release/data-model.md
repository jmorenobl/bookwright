# Phase 1 Data Model: Orchestration loop fixture, E2E, docs, release

This iteration adds **no `src/` domain model**. The "entities" here are the
fixture artifacts, the oracle schema, and the precise shape of the two `status`
JSON documents the E2E compares. The runtime models they exercise are the merged
iteration-020 records ([`StatusState`, `GraphFacts`, `OpenQuestion`, `AnchorGap`,
`LowReliabilityFinding`, `ValidationSummary`](../../src/bookwright/status/model.py)
and [`Action`](../../src/bookwright/status/rules.py)).

---

## 1. Extended `tiny-historical` fixture

### 1.1 `manifest.toml` — added `[focus]` block (FR-002)

A fully-populated block, appended after `[book]` (or anywhere valid). Required
fields per [`FocusBlock`](../../src/bookwright/core/_focus_block.py):

| Field | Value (illustrative) | Constraint |
|---|---|---|
| `target` | `"Cerrar la investigación del libro de jornales para datar la huelga"` | non-empty string |
| `notes` | `"Pendiente: confirmar si se conserva el libro de jornales (q-libro-de-jornales)."` | string (may be empty) |
| `updated_at` | `2026-06-13` | TOML date or `YYYY-MM-DD` string |

The committed block makes US1 ("a reader inspects `manifest.toml`") true. The E2E
**re-stamps** it via `bookwright focus set` (US2 scenario 1), which is idempotent
for the asserted fields (`target` is what the test passes; `updated_at` becomes
the run date, identical across both `status` runs — D6).

> **FR-006 check.** Adding `[focus]` does not touch `[research]`/`[validators]`,
> so `test_disabled_research_block_is_inert`'s `enabled = true → false` string
> replace and every M4 build/validate assertion are unaffected.

### 1.2 `bible/research/_index.md` — unchanged (the pinned open-question set)

Stays exactly as committed: `open_questions: [q-libro-de-jornales,
q-origen-telares]` (FR-003 "pin the exact set, not assume it adds the only one").
These map to two `open_only=True` findings with `file = bible/research/_index.md`.

### 1.3 `_resolution/q-libro-de-jornales.md` — the pre-baked answering Finding (FR-005, D3/D4)

A new file in a **top-level `_resolution/` directory** (outside the corpus dirs,
so build #1 never reads it). Front-matter declares one **closed** Finding, no
anchor:

```yaml
findings:
  - id: libro-de-jornales-hallado          # a closed answering finding (NOT q-…, NOT open)
    claim: "El libro de jornales de la Real Fábrica se conserva en el Archivo Municipal y data la huelga en 1851."
    asserted_by: author
    bears_on: "La Real Fábrica de Paños"   # resolves in the bible → no ResearchWarning
    sources: ["Memoria de la Real Fábrica de Paños"]   # existing `alta` source → not low-reliability
# NO `anchors:` block → adds no AnchorGap, no factual_anchor finding
```

Invariants this file MUST satisfy (so D2 convergence holds):
- references only an **already-registered** `media`/`alta` source (no new low-reliability finding);
- declares **no anchor** (no new `unresolved_anchors`, no `factual_anchor` change);
- `bears_on` resolves in the bible (no `ResearchWarning`, no unresolved-target noise);
- is **not** flagged `open` (does not re-enter `open_questions`).

### 1.4 `expected-status.md` — the orchestration oracle (FR-004, D5)

New co-located oracle, front-matter loaded once. Illustrative schema:

```yaml
focus:
  target: "Cerrar la investigación del libro de jornales para datar la huelga"
open_questions:
  ids: [q-libro-de-jornales, q-origen-telares]   # exact set, sorted (file,id)
  file: bible/research/_index.md
resolution:
  resolved_id: q-libro-de-jornales               # the id the two-part edit closes
  answering_file: _resolution/q-libro-de-jornales.md
  remaining_id: q-origen-telares
unresolved_anchors:
  - promotes: rumor-incendio
    constrains: "El almacén viejo"
    problems: [under_reliable]
low_reliability_findings:
  - id: rumor-incendio
    best_reliability: baja
validation:
  counts: {error: 1, warning: 1, info: 0}
next_actions:
  skills: [bookwright-research, bookwright-verify, bookwright-continuity]   # the firing rules, in order
```

The test reads identifiers/counts from here — never hard-codes them (FR-008).

---

## 2. The two `status --json` documents (the comparison subject)

Shape per [contracts/cli-status.md](../020-status-derived-state/) /
`ok_payload`: `{"status":"ok","focus":…,"state":…,"next_actions":[…]}`.

### 2.1 First `status` (before resolution) — asserted facts (FR-008)

| Field | Expected (from oracle) |
|---|---|
| `focus` | non-null; `focus.target` == the target the test set |
| `state.phase` | `"drafting"` (manifest `[book].status`) |
| `state.graph.available` | `true`; `entities`/`triples` present (ints ≥ 0) |
| `state.open_questions` | `count == 2`; ids `[q-libro-de-jornales, q-origen-telares]` |
| `state.unresolved_anchors` | `count == 1`; `rumor-incendio → "El almacén viejo"`, `problems == ["under_reliable"]` |
| `state.low_reliability_findings` | `count == 1`; `rumor-incendio`, `best_reliability == "baja"` |
| `state.validation.counts` | `{error:1, warning:1, info:0}` |
| `next_actions` | exactly 3, skills in order `research_queue` (`bookwright-research`), `verify_findings` (`bookwright-verify`), `review_continuity` (`bookwright-continuity`); each entry has `skill`, `reason`, `prompt` |
| `next_actions[research_queue].prompt` | contains both `q-libro-de-jornales` and `q-origen-telares` |

### 2.2 Second `status` (after resolution) — convergence (FR-009)

| Field | Expectation |
|---|---|
| `state.open_questions` | `count == 1`; `[q-origen-telares]`; `q-libro-de-jornales` **absent** |
| `next_actions[research_queue].prompt` | no longer contains `q-libro-de-jornales`; still contains `q-origen-telares` |
| `next_actions[research_queue].reason` | reflects new count (`"1 open research question …"`) |
| `next_actions` **length** | still 3 (workstream aggregation — NOT N−1) |
| `state.graph` | `available == true`, counts present — **excluded from cross-run equality** (D2) |
| `focus`, `state.phase`, `state.unresolved_anchors`, `state.low_reliability_findings`, `state.validation`, `next_actions[verify_findings]`, `next_actions[review_continuity]` | **byte-for-byte identical** to the first run |

---

## 3. Rule-table firing (why exactly these 3 actions)

Derived from [rules.py](../../src/bookwright/status/rules.py) `RULES` order, given
the extended fixture's state:

| Rule | `applies`? | Why |
|---|---|---|
| `bootstrap_graph` | ✗ | graph available, entities > 0 |
| `research_queue` | ✓ | 2 open questions (→1) + 1 anchor gap → fires both runs |
| `verify_findings` | ✓ | `rumor-incendio` below `media` floor → fires both runs (unchanged) |
| `review_continuity` | ✓ | `validation.counts.error == 1 > 0` → fires both runs (unchanged) |
| `define_focus` | ✗ | `[focus]` present → `focus_defined == true` |

Resolution touches only `research_queue` (its prompt + reason) and `open_questions`;
`verify_findings` and `review_continuity` are byte-identical across runs.

---

## 4. Cross-run comparison sets (the convergence contract, D2)

The E2E partitions the two documents into three sets:

- **Δ-expected (must change):** `state.open_questions`; `next_actions[research_queue].prompt`
  and `.reason`; `state.graph` (telemetry, asserted present-not-equal).
- **Invariant (must be byte-identical):** `focus`; `state.phase`;
  `state.unresolved_anchors`; `state.low_reliability_findings`;
  `state.validation`; `next_actions[verify_findings]`; `next_actions[review_continuity]`;
  and `next_actions[research_queue].skill`.
- **Structural:** `status == "ok"`; `len(next_actions) == 3` in both runs.

---

## 5. Test entities (`tests/e2e/test_orchestration_workflow.py`)

| Helper / fixture | Role (mirrors 016) |
|---|---|
| `_load_oracle()` + `oracle` fixture | parse `expected-status.md` front-matter once (committed source) |
| `historical` fixture | `copy_fixture("tiny-historical", tmp_path)` + `monkeypatch.chdir` |
| `_status(cli)` | run `status --json`, assert exit 0, return parsed payload |
| `_apply_resolution(project, oracle)` | copy `_resolution/<answering_file>` → `bible/research/`; drop `resolved_id` from `_index.md` `open_questions` |
| `_research_action(payload)` | locate the `next_actions` entry whose `skill == "bookwright-research"` |
| inertness/degraded tests | reuse `tiny-novel` via `copy_fixture` (D7) |

No new production types; the test imports `app`, `copy_fixture`, `FIXTURES_DIR`,
`parse_frontmatter` — the exact 016 import set.
