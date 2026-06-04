# Quickstart — `factual_anchor` Validator

Exercise the validator end-to-end on a research project. Assumes iterations 012/013
are on `main` (the `[research]` block, `bible/research/`, and `graph build`'s
research pass are present).

## 1. A project with research anchors

In a project that has a `bible/research/` directory, author (or already have):

- `bible/research/sources.md` — at least one `Source` with full provenance and a
  reliability of `media` or `alta`.
- `bible/research/<topic>.md` — a finding backed by that source, promoted to an
  anchor that `constrains` a real bible entity (or a timeline event), optionally
  with a `begin`/`end` time-span.

Build the graph (the derived cache the validator reads):

```bash
uv run bookwright graph build
```

## 2. Run validation

```bash
uv run bookwright validate            # human-readable, all validators
uv run bookwright validate --json     # machine contract on stdout
```

`factual_anchor` now appears in `ran[]`. A **well-formed** anchor produces **no**
violation (US1 scenario 5).

## 3. See each violation kind

Introduce one defect at a time and re-run `graph build` + `validate`:

| Defect | Expected finding |
|---|---|
| Promote a finding with **no source** (or an open finding) | **warning**: anchor promotes a finding with no supporting source (R1/FR-006). |
| Drop a mandatory facet from a backing source (e.g. remove `author`) | **warning** naming the missing facet (R2/FR-007) — one per missing facet. |
| Back the anchor only with a `baja`-reliability source while `min_reliability_for_anchor = "media"` | **warning**: backed only by sources below the minimum reliability (R3/FR-008). |
| Constrain an entity not in the bible (link dropped at build) | **warning**: constrains a narrative entity not present in the graph (R4/FR-009). |
| Give the anchor `begin: 1957` and constrain an event the timeline dates to 1950 | **error**: anachronism — disjoint year ranges (R5/FR-010). |

## 4. Verify the inert / zero-cost behavior

```bash
# No research at all → factual_anchor runs and finds nothing:
uv run bookwright validate            # zero factual_anchor violations (FR-016)

# Turn the research system off on a project that DOES have anchors:
#   [research]
#   enabled = false
uv run bookwright validate            # zero factual_anchor violations (FR-015)

# Disable just this check:
#   [validators]
#   disabled = ["factual_anchor"]
uv run bookwright validate            # factual_anchor not in ran[]
```

## 5. Severity gate interaction

```bash
uv run bookwright validate --severity error
```

Only the **anachronism error** survives; the structural **warnings** are suppressed
by the existing severity gate (US2 scenario 4 / SC-005).

## 6. Scope filter interaction

```bash
uv run bookwright validate --scope bible/research
```

`factual_anchor` violations are **location-less** (`source = None`, exactly as the
`temporal` validator already is for some findings), so a `--scope <path>` run reports
**zero** `factual_anchor` violations — scoping is a display filter and the unfiltered
gate still sees every defect (SC-005). Run without `--scope` to see them all.

## What "done" looks like

- `factual_anchor` is discovered with no wiring, honors `[validators]` and
  `[research]`, and is silent on well-formed / non-research projects.
- Every malformed-anchor kind is reported with a message that names the anchor and
  the reason; the anachronism is an `error`, the rest are `warnings`.
- `uv run pytest`, `uv run ruff check`, `uv run mypy --strict` all green; coverage
  stays ≥ 80 %.
