# Quickstart: validating Propp/Greimas typing

A runnable check that the typing works end to end. Prerequisites: `uv sync`; the
narrative-structure ingestion of 028/029 is on `main`.

## 1. Scaffold a project and activate Propp + Greimas

```bash
uv run bookwright init my-book --json
cd my-book
```

In `manifest.toml`, set the active vocabularies:

```toml
[vocabularies]
active = ["propp", "greimas"]
```

## 2. Author one beat (a Propp function) and one role (a Greimas actant)

```bash
# A character with a Greimas actant role:
mkdir -p bible/characters
cat > bible/characters/hero.md <<'EOF'
---
name: "Hero"
narrative_roles: [sujeto]      # Spanish form of the Greimas "subject" actant
---
EOF

# A unit card naming a Propp function (and one custom, unmatched name):
mkdir -p outline/units
cat > outline/units/opening.md <<'EOF'
---
name: "Opening"
functions: [departure, "my custom beat"]
---
EOF
```

## 3. Build the graph

```bash
uv run bookwright graph build --json
```

## 4. Confirm the typing (and the non-typing)

```bash
# The Propp-matched function carries a P2_has_type to the propp term:
uv run bookwright graph query --json \
  "SELECT ?f ?t WHERE { ?f a <…G10_Narrative_Function> ; <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> ?t }"
```

Expected (verifies the contract):

- The *departure* function is linked by `crm:P2_has_type` to
  `propp#function/departure`, and that term is `a crm:E55_Type`. **(C6)**
- The *"my custom beat"* function has **no** `P2_has_type`. **(C8)**
- The Hero's role node is typed to `greimas#actant/subject` — the Spanish
  `sujeto` resolved to the same term. **(C7/C9)**
- Inspect `bible/graph.ttl`: each typing link has a matching
  `crm:E13_Attribute_Assignment` pointing at the typed entity and the term — no
  bare typing triple. **(C10)**

## 5. Confirm no-regression

Set `active = []`, rebuild, and diff `bible/graph.ttl` against a build at
028/029 — the narrative-function/role triples are unchanged: zero `P2_has_type`,
zero added E13s. **(C12)**

## Automated equivalents

The clauses above are covered by:

- `tests/io/test_vocabularies.py` — C2, C4, C5.
- `tests/io/test_outline.py` (extended) — C6, C7, C8, C10 (function side), C11, C13.
- `tests/io/test_bible.py` / `test_character_roles.py` — C9, C10 (role side), C11.
- `tests/golem/test_triples.py` + `test_derived_assertions.py` — entity emission
  + derived-assertion shape for `type_uri`.
- `tests/resources/test_vocabulary_references.py` — C1, C3, C14 (SC-005).
- An existing 028/029 no-vocab test re-run proves C12/SC-003.

Run the focused set:

```bash
uv run pytest tests/io/test_vocabularies.py tests/io/test_outline.py \
  tests/resources/test_vocabulary_references.py -q
uv run pytest        # full suite + ≥80% coverage gate
uv run ruff check && uv run ruff format --check && uv run mypy --strict
```
