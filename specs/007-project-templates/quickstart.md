# Quickstart: Authoring & Validating a Bookwright Template

Audience: the implementer of iteration 7. This is a "how to author one file and
prove it conforms" walkthrough — no new runtime code, only documents + tests.

## Prerequisites

- Iterations 1–6 on `main` (`uv sync` works; `bookwright init` and
  `bookwright graph build` run).
- `uv run pytest` green before you start.

## 1. Author a skeleton singleton (e.g. `bible/themes.md`)

Edit `src/bookwright/resources/project/bible/themes.md`. Replace the stub with
real Spanish content:

- Section headings in Spanish (`## Registro de motivos`, …).
- An `<!-- -->` HTML-comment guidance block telling the author/agent what to fill.
- A worked example **inside** an HTML comment.
- `[PENDING: <pregunta en español>]` prompts where the agent fills from a brief.
- No frontmatter (themes is not indexed). No stub sentinel.

## 2. Author an indexed document (e.g. `bible/timeline.md`)

```markdown
---
events: []
---

# Línea de tiempo
<!-- Guía: cada evento es { name, participants: [slug-de-personaje, …] }.
     Mantén `events:` vacío hasta que el agente lo rellene. Ejemplo:
events:
  - name: "Caída del puente"
    participants: ["ana-soler", "marco"]
-->
...
```

The fence is on line 1; the only top-level key is `events: []`; the example
lives in the HTML comment so it never indexes (contract C2/C4, F3).

## 3. Author an indexed mold (e.g. `bible/character.md.tmpl`)

Create `src/bookwright/resources/templates/bible/character.md.tmpl`:

```markdown
---
name: "[PENDING: ¿Cómo se llama el personaje?]"
# born: 1980          # año entero — descomenta y rellena, nunca un texto
# died:
features: []
narrative_roles: []
---

# {name}
<!-- Guía para el agente: ... -->
## Rasgos biográficos
...
```

`name` is a string field, so a **quoted** `[PENDING: …]` value is legal (C3):
write `name: "[PENDING: …]"`, never `name: [PENDING: …]` (bare brackets parse as
a YAML list and skip on `_require_name`). `born`/`died` stay **commented or
omitted** — a non-int value there would make the mapper skip the file.
`features`/`narrative_roles` are empty string lists.

## 4. Validate format + round-trip locally

```bash
# YAML + allowed-key + sentinel + render + round-trip suite
uv run pytest tests/resources/ -q

# Manual round-trip: stamp a fresh project and index it
uv run bookwright init /tmp/qt-book --title "QT" --integration generic
uv run bookwright graph build --json --project-root /tmp/qt-book \
  | python -c 'import json,sys; r=json.load(sys.stdin); \
print("skipped", r.get("skipped")); print("unknown_keys", r.get("unknown_keys"))'
# Expect: skipped [] , unknown_keys []  (SC-002)
```

## 5. Prove a filled instance maps to a GOLEM entity (SC-004)

Stamp the character mold into the fresh project, fill it, re-index:

```bash
mkdir -p /tmp/qt-book/bible/characters
# copy character.md.tmpl → bible/characters/ana-soler.md, fill name/born/features
uv run bookwright graph build --json --project-root /tmp/qt-book
# Expect exactly one Character entity with the declared name/born/features
```

## 6. CHANGELOG + finish

- Create `CHANGELOG.md` (repo root): credit `fiction-book-writing` (adaumann,
  MIT), note original Apache-2.0 redaction adapted to GOLEM, record § 6 layout
  supersession (FR-021 / SC-006).
- Re-run the full gate:

```bash
uv run pytest -q
uv run ruff check && uv run ruff format --check
uv run mypy --strict src tests
```

`ruff`/`mypy` apply to the new **test** modules only (the templates are not
Python). All four must pass before merge.

## Done When

- Every `bible/*` and `outline/*` skeleton file is real authored content, zero
  sentinels (SC-001).
- Fresh `init` + `graph build` → zero skips, zero `unknown_keys`, zero
  unresolved participants (SC-002).
- Every authored template parses through the iter-6 reader without raising
  (SC-003).
- A filled character/setting mold → exactly one `Character`/`Setting` (SC-004).
- Every template has ≥1 HTML-comment guidance block and reads as plain Markdown
  (SC-005).
- `CHANGELOG.md` records the credit + § 6 supersession (SC-006).
