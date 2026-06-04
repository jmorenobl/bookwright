# Quickstart: `bookwright-research` Skill + `bible/research/`

A manual end-to-end walkthrough proving the three slices. Assumes
`uv sync` and iteration 13 (`io/research.py`, provenance entities, `sources.ttl`)
on `main`.

## 1. Scaffold ships the research system (US3, FR-014)

```bash
uv run bookwright init --json my-novel   # or run interactively
cd my-novel
ls bible/research/        # → _index.md  sources.md   (NO bible/research.md)
```

Expected: `bible/research/_index.md` and `bible/research/sources.md` exist,
rendered from `resources/project/bible/research/`; the legacy single
`bible/research.md` is gone.

## 2. The `[research]` block is written with defaults + comments (US2, FR-014a)

```bash
grep -A4 '^\[research\]' manifest.toml
```

Expected:

```toml
[research]
enabled = true
source_languages = []
min_reliability_for_anchor = "media"
```

…each line preceded by its explanatory comment. Round-trip safety:

```bash
uv run python -c "from bookwright.core import Manifest; m=Manifest.load('manifest.toml'); m.dump('manifest.toml', overwrite=True)"
grep -c 'research system is active' manifest.toml   # comment survived → 1
```

Loading a manifest **without** the block still works (defaults applied):

```bash
uv run python - <<'PY'
from bookwright.core import Manifest
# (point at a fixture manifest that omits [research])
m = Manifest.load("tests/.../no_research.toml")
assert m.research.enabled is True
assert m.research.source_languages == []
assert m.research.min_reliability_for_anchor == "media"
print("defaults OK")
PY
```

A bad value is rejected naming the field:

```bash
# [research] min_reliability_for_anchor = "altísima"  → ManifestValidationError
#   naming research.min_reliability_for_anchor (FR-013)
```

## 3. The skill materializes and lints (US1, FR-001..FR-004, SC-001)

```bash
ls .claude/skills/bookwright-research/      # SKILL.md (+ references/research-format.md)
ls .agents/skills/bookwright-research/ 2>/dev/null || true   # if generic was chosen
```

Expected: a `SKILL.md` whose front-matter `name` is `bookwright-research`,
`description` ≤ 1024 chars with ES+EN triggers, passing `lint_skill_md`. Confirm
the reference came along:

```bash
test -f .claude/skills/bookwright-research/references/research-format.md && echo "reference copied"
```

## 4. Run the protocol, then build the graph (US1, FR-005..FR-006, FR-018, SC-003)

Inside an agent session: `/bookwright-research "logística de la Wehrmacht en 1943"`.
The agent follows the seven steps and writes:

- `bible/research/logistica-de-la-wehrmacht-en-1943.md` (findings + anchors)
- updated `bible/research/sources.md` (provenance, with original-language quotes
  and translations where the source language ≠ `es`)
- updated `bible/research/_index.md` (topic map + remaining open questions)

then runs the final step:

```bash
uv run bookwright graph build --json
```

Expected JSON report includes non-zero `sources`/`findings`/`anchors`, zero
`ResearchError` (the build succeeds), and any unresolved `bears_on`/`constrains`
surfaces only as a soft `research_warnings` entry.

## 5. Verify provenance, conflicts, anchors, and the reliability floor

- **Provenance complete (SC-004)**: every finding's sources carry
  `original_quote`; foreign-language sources carry `translation`.
- **Conflicts preserved (SC-005)**: a nationally-divergent topic yields two
  findings, each with its own source — no merge.
- **Anchor reaches the graph (SC-003)**:

  ```bash
  uv run bookwright graph query --json \
    'SELECT ?a ?e WHERE { ?a a ?t ; <https://…/constrains> ?e }'
  # → ≥1 anchor constraining a named narrative entity
  ```

- **Reliability floor (FR-015, SC-006)**: a finding whose best source is `baja`
  while `min_reliability_for_anchor = "media"` appears as a finding but **not**
  as an anchor — 0 such promotions.

## 6. Bible & clarify wiring (FR-009, FR-010)

- `/bookwright-bible` creates `bible/research/_index.md` (not `bible/research.md`).
- `/bookwright-clarify` lists the open research questions from
  `bible/research/_index.md`.

## Done when

All four CI gates pass (`ruff check`, `ruff format --check`, `mypy --strict`,
`pytest` ≥ 80 %, > 85 % on new code per SC-007), the generated skill passes
`lint_skill_md` in both integrations, and the SC-009 description-mirror gate is
green for `bookwright-research`.
