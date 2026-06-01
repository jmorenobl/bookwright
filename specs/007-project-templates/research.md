# Phase 0 Research: Bible / Outline / Constitution Templates

The spec arrived fully clarified (Session 2026-06-01: prose language + worked
examples in HTML comments). No `NEEDS CLARIFICATION` markers remain in Technical
Context. Research therefore resolves the *mechanical* unknowns — the exact iter-4
walker and iter-6 parser behaviors the templates must satisfy — by reading the
shipped code rather than guessing. Each decision below is grounded in a specific
source file already on `main`.

## R1 — How the iter-4 walker decides `.md` vs `.j2` vs `.tmpl`

**Decision**: Skeleton singletons under `resources/project/` use `.md`
(byte-copied verbatim) or `.j2` (Jinja2-rendered, suffix stripped). Molds use
`.tmpl` and live **only** under `resources/templates/`, never under `project/`.

**Rationale**: `render_resource_tree` walks `bookwright.resources.project`; for
each file `_target_relpath` strips a trailing `.j2` and everything else is
`write_bytes_atomic`-copied byte-for-byte
([scaffold.py](../../src/bookwright/commands/init/scaffold.py#L255-L295)). A
`*.tmpl` placed under `project/` would be copied literally into the new project
(spec edge "init walker semantics") — wrong. `.j2` files are rendered through a
single `jinja2.Environment(undefined=StrictUndefined)`.

**Alternatives considered**: Putting molds under `project/bible/` with a
runtime skip-list — rejected: requires editing iter-4 copy logic (FR-023) and
adds branching the walker deliberately avoids.

## R2 — Which Jinja2 variables a `.j2` skeleton file may reference

**Decision**: Only `title`, `project_slug`, `author`, `language`,
`integration_key`. Any other `{{ var }}` aborts `init`.

**Rationale**: `run_scaffold_steps` builds `template_context` with exactly those
five keys
([scaffold.py](../../src/bookwright/commands/init/scaffold.py#L332-L338)) and the
environment uses `StrictUndefined`, so an undefined reference raises at render
time. The two `.j2` files this iteration touches (`constitution.md.j2`,
`README.md.j2`) must restrict themselves to this set. `constitution.md.j2`
already uses `{{ title }}`; design § 9.2's `{{ book.title }}` is **not**
available — map it to `{{ title }}`.

**Alternatives considered**: Extending the context with `subtitle`/`genre` —
rejected: changing the context is an iter-4 modification (FR-023) and out of
scope.

## R3 — Exact frontmatter the iter-6 mapper recognizes (the parser contract)

**Decision**: Honor these and nothing else for the four indexed concepts:

| Concept | Location | Top-level keys | Value typing rules |
|---|---|---|---|
| Character | `bible/characters/*.md` | `{name, born, died, features, narrative_roles}` | `name` non-empty str (required); `born`/`died` **int or omitted** (bool & non-int rejected); `features`/`narrative_roles` **list of str or omitted** |
| Setting | `bible/settings/*.md` | `{name}` | `name` non-empty str |
| Timeline | `bible/timeline.md` | `{events}` — **only this key** | `events` a list of mappings; each item `name` (str) + optional `participants` (list of character-slug strs) |
| Relationships | `bible/relationships.md` | `{relationships}` — **only this key** | each item `name` + optional `participants` |

**Rationale**: From
[bible.py](../../src/bookwright/io/bible.py#L35-L39): `CHARACTER_KEYS`,
`SETTING_KEYS`, `ITEM_KEYS`, `TIMELINE_TOP_KEYS`, `RELATIONSHIPS_TOP_KEYS`.
`_coerce_year` rejects `bool` and any non-`int`
([bible.py](../../src/bookwright/io/bible.py#L240-L245)); `_coerce_str_list`
requires a list of `str`
([bible.py](../../src/bookwright/io/bible.py#L248-L253)).
`_record_unknown_keys` runs against the **top-level** keys for collections
([bible.py](../../src/bookwright/io/bible.py#L293)), so a stray top-level key in
`timeline.md` (e.g. a stub heading promoted into frontmatter, or a second key)
yields an `unknown_keys` warning — therefore the shipped frontmatter must be
**exactly** `events: []` / `relationships: []`.

**Alternatives considered**: Shipping `born: [PENDING: …]` so the author sees
the prompt in the field — **rejected**, fatal: `_coerce_year` raises
`InvalidFrontmatterError`, the file is skipped (SC-002 fails). Typed-field
prompts must live in prose/HTML comments only (spec edge "Placeholder vs machine
fields"). Age must be expressed as `born`/`died` years or prose, never a
non-int frontmatter value (FR-012).

## R4 — How an empty collection round-trips to zero entities, zero warnings

**Decision**: Ship `events: []` (and `relationships: []`) as the sole frontmatter
key; put every worked example **inside HTML comments** in the body.

**Rationale**: `_map_collection` reads `metadata.get(container, [])`; an empty
list iterates zero times → zero entities, and with only the recognized top key
present `_record_unknown_keys` adds nothing
([bible.py](../../src/bookwright/io/bible.py#L285-L306)). HTML comments are not
YAML and not body entities, so an example `- name: …` inside `<!-- -->` never
indexes and never trips the sentinel sweep (FR-018, Clarification Q2).

**Alternatives considered**: A commented-out `# events:` YAML key — rejected:
brittle (one un-commenting mistake re-introduces a malformed list) and the
example is more legible as a full HTML-comment block in the body.

## R5 — Frontmatter fence shape the reader requires

**Decision**: First line of the file is exactly `---`; a matching closing `---`
follows; YAML between is `yaml.safe_load`-able.

**Rationale**: `parse_frontmatter` only treats a file as having frontmatter when
`lines[0].strip() == "---"` and a later `---` closes it
([frontmatter.py](../../src/bookwright/io/frontmatter.py#L37-L61)); otherwise the
whole file is body with `{}` metadata. So `timeline.md`/`relationships.md` (and
the character/setting molds) must open with the fence on line 1 — no leading
blank line, no leading `#` heading before the fence.

**Alternatives considered**: None — this is a hard reader invariant.

## R6 — Where molds live and how they are named

**Decision**: `resources/templates/<dest-subdir>/<concept>.md.tmpl`:
`templates/bible/{character,setting,location}.md.tmpl`,
`templates/manuscript/chapter.md.tmpl`, `templates/scenes/scene.md.tmpl`.
`manifest.template.toml` stays at `templates/` root (verify-only).

**Rationale**: FR-012/013/014/015/016 dictate the per-concept destination
prefixes; mirroring the destination subdir keeps the command authoring (iter
8–9) a trivial path join. Molds are read directly in v0 (no `resolve_template()`,
FR-024); they are **not** under `project/`, so the iter-4 walker never stamps
them into a project (spec edge).

**Alternatives considered**: A flat `templates/` dir — rejected: loses the
destination hint and risks name collisions (e.g. a future `manuscript` vs `bible`
`notes.md.tmpl`).

## R7 — Constitution structure source

**Decision**: Author `constitution.md.j2` from design § 9.2's seven sections —
Voz y registro, Pacto con el lector, Pacto histórico-ficcional (marked
optional), Líneas rojas, Invariantes de coherencia, Vocabularios activos, Notas
para el agente — each with `[PENDING: <pregunta>]` prompts and HTML-comment
guidance (FR-001). Title via `{{ title }}` (R2).

**Rationale**: § 9.2 is the canonical template; § 9.1/9.3 frame it as
non-optional input to every downstream command, so the prompts must be
answerable from a brief. The agent command `/bookwright-constitution`
(design § 10.1 step 5) explicitly writes `[PENDING]` with a clarifying
question — the template must pre-seed those slots.

**Alternatives considered**: Inventing extra sections — rejected: § 9.2 is the
agreed contract and the indexer/validators key off it.

## R8 — Preset inventory adoption (design § 17.2) and attribution

**Decision**: Adopt the document inventory § 17.2 enumerates — synopsis
(short+long), themes with motif registry, locations with sensory anchors,
glossary, research, subplots, pov-structure — as **original Spanish prose
adapted to GOLEM**, not copied text. Credit `fiction-book-writing`
(adaumann, MIT) in `CHANGELOG.md`; state Bookwright's redaction is original
(Apache-2.0) and adapted to GOLEM; note the § 6 layout supersession (FR-021).

**Rationale**: § 17.2 already lists exactly what to adopt and confirms the
preset's MIT license permits structural reuse with attribution. Studying the
inventory from the design doc is sufficient; fetching the repo is optional and
never a build/runtime dependency (spec Assumptions). No verbatim text → no
sentinel risk and clean license posture.

**Alternatives considered**: Vendoring the preset's Markdown — rejected: pulls
non-GOLEM structure, risks verbatim copy, and adds a dependency the project
explicitly avoids.

## R9 — Validation strategy under the coverage exception (SC-007)

**Decision**: Five pytest modules under `tests/resources/` (see plan structure)
that exercise the *contract*, not line counts: sentinel sweep, frontmatter-YAML
+ allowed-key lint, full `map_bible` round-trip on a freshly-`init`-ed temp
project, a filled-instance fixture asserting mold→entity, and a StrictUndefined
render of every `.j2`. These reuse `bookwright.io` and the iter-4
`render_resource_tree`, so the tests assert against the *real* contracts, not a
re-implementation.

**Rationale**: Constitution VIII's intent — "assertions are themselves
asserted" — is met by testing the parser-visible and human-visible contracts;
line coverage over prose measures nothing (plan Complexity Tracking, SC-007).

**Alternatives considered**: Manual inspection only — rejected: SC-002/003/004
are machine-checkable and regressions (a future stub, a stray key) must fail CI,
not a human eyeball.
