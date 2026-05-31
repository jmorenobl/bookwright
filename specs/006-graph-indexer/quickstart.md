# Quickstart — Graph indexer + `graph` commands

End-to-end walkthrough exercising the iteration-6 deliverables. Assumes
iterations 1–5 are present and the Gate II `pyyaml` amendment has landed.

## 0. A project with bible content

```bash
uv run bookwright init my-novel --integration claude
cd my-novel
```

Add a character (`bible/characters/aparici.md`):
```markdown
---
name: "Manuel de Aparici"
born: 1828
died: 1900
features:
  - "ingeniero químico"
narrative_roles:
  - protagonist
---
Manuel funda Destilerías Ayelo...
```

Add events (`bible/timeline.md`):
```markdown
---
events:
  - name: "Fundación de Destilerías Ayelo"
    participants: ["Manuel de Aparici"]
---
```

## 1. Build the graph (US1)

```bash
uv run bookwright graph build
# stderr: processed 2 files, 4 entities, NN triples → bible/graph.ttl
uv run bookwright graph build --json
# stdout: {"status":"ok","files_processed":2,"entities":4,"triples":NN,"skipped":[],"unknown_keys":[],"graph_path":"bible/graph.ttl"}
```

`bible/graph.ttl` parses as Turtle and uses short prefixes (`golem:`, `crm:`,
`dlp:`, `rdfs:`, `xsd:`).

## 2. Query the graph (US2)

```bash
# Who are the characters?
uv run bookwright graph query "SELECT ?c WHERE { ?c a golem:G1_Character }" --json
# {"status":"ok","results":[{"c":".../character/manuel-de-aparici"}],"count":1}

# Characters born before 1850 (R1 makes this answerable):
uv run bookwright graph query '
  SELECT ?c ?y WHERE {
    ?c a golem:G1_Character ; golem:GP0_has_feature ?f .
    ?f crm:P2_has_type <…/type/birth> ; crm:P43_has_dimension/crm:P90_has_value ?y .
    FILTER(?y < "1850"^^xsd:gYear)
  }'

# Protagonists:
uv run bookwright graph query "SELECT ?c WHERE { ?c dlp:plays ?r . ?r a golem:G11_Narrative_Role }"
```

Empty match → `{"status":"ok","results":[],"count":0}`, exit 0.
Invalid SPARQL → `{"status":"error","code":"invalid_query",...}`, exit 3.

## 3. Provenance (US3)

```bash
uv run bookwright graph query "
  SELECT ?src WHERE {
    ?a a crm:E13_Attribute_Assignment ;
       crm:P140_assigned_attribute_to <…/character/manuel-de-aparici> ;
       crm:P16_used_specific_object ?src }"
# → "bible/characters/aparici.md" (or "...:N" with a line locator)
```

## 4. Pluggable engine (US4)

```bash
# default rdflib (no key) works; an unknown engine fails clearly:
#   manifest.toml → [bookwright] indexer = "nope"
uv run bookwright graph build --json
# {"status":"error","code":"unknown_indexer","message":"unknown indexer 'nope'; available: rdflib"}
```

## 5. Fault tolerance (US5)

```bash
# missing bible/ or manuscript/ → fails before writing, exit 2
# one malformed file among valid ones → build completes, lists it, exit 4
# slug collision → exit 3, names the id + both files, no graph written
```

## Test commands
```bash
uv run pytest tests/golem tests/indexers tests/io tests/commands/graph
uv run ruff check && uv run ruff format --check
uv run mypy --strict src tests
```
