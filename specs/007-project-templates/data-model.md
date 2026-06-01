# Phase 1 Data Model: Template Inventory & Frontmatter Schema

This iteration ships no Pydantic/GOLEM types of its own. Its "data model" is
twofold: (1) the **document inventory** — every file authored, its lifecycle,
extension, and governing FR; and (2) the **frontmatter schema** each
indexer-ingested document must present so the iter-6 mapper (§ R3) constructs
the expected GOLEM entity. Both are conformance targets, not new code.

## 1. Document inventory

### 1a. Skeleton singletons — `src/bookwright/resources/project/` (stamped once by `init`)

| File | Ext | FR | Frontmatter | Key authored sections (Spanish prose) |
|---|---|---|---|---|
| `bible/constitution.md.j2` | `.j2` | FR-001 | none | Voz y registro · Pacto con el lector · Pacto histórico-ficcional *(opcional)* · Líneas rojas · Invariantes de coherencia · Vocabularios activos · Notas para el agente |
| `bible/timeline.md` | `.md` | FR-002 | `events: []` (only key) | Per-event shape doc + worked example in HTML comment |
| `bible/relationships.md` | `.md` | FR-003 | `relationships: []` (only key) | Per-relationship shape doc + HTML-comment example |
| `bible/themes.md` | `.md` | FR-004 | none | Registro de motivos · Rastreador de símbolos · Mapa temático por capítulo |
| `bible/glossary.md` | `.md` | FR-005 | none | Registro de términos inventados · Reglas de capitalización · Bitácora de consistencia |
| `bible/research.md` | `.md` | FR-006 | none | Preguntas abiertas · Notas de fuentes · Hallazgos resueltos |
| `bible/subplots.md` | `.md` | FR-007 | none | Beat sheets de subtramas · Puntos de intersección con la trama principal |
| `bible/pov-structure.md` | `.md` | FR-008 | none | Modo narrativo · Calendario de POV · Diferenciación de voz · Mapa de asimetría de información · nota "solo multi-POV" |
| `outline/arcs.md` | `.md` | FR-009 | none | Plantilla de arcos |
| `outline/structure.md` | `.md` | FR-009 | none | Plantilla estructural |
| `outline/scenes.md` | `.md` | FR-009 | none | Plantilla de escenas |
| `outline/synopsis.md` | `.md` | FR-009 | none | Sinopsis corta (250–350 palabras) · Sinopsis larga (1000–2000 palabras) |
| `README.md.j2` | `.j2` | FR-010 | none | Guía breve en español; usa solo `title`/`project_slug`/`author`/`language`/`integration_key` |
| `.gitignore` | — | FR-011 | none | cache, artefactos Python, venv, env — revisar/extender, no regresar |

### 1b. Re-instanceable molds — `src/bookwright/resources/templates/` (stamped many times by commands)

| File | Ext | FR | Frontmatter | Key authored sections (Spanish prose) |
|---|---|---|---|---|
| `bible/character.md.tmpl` | `.tmpl` | FR-012 | ⊆ `{name, born, died, features, narrative_roles}` | Rasgos biográficos · psicológicos · físicos · Rol narrativo · Diálogo de muestra · Patrones de lenguaje corporal |
| `bible/setting.md.tmpl` | `.tmpl` | FR-013 | `{name}` only | Cultura · sistema/era · geografía amplia |
| `bible/location.md.tmpl` | `.tmpl` | FR-014 | none ingested (valid YAML if any; doc as **not indexed in v0**) | Qué se ve · oye · huele · toca · Atmósfera dominante |
| `manuscript/chapter.md.tmpl` | `.tmpl` | FR-015 | none ingested | Estructura de capítulo para borrador |
| `scenes/scene.md.tmpl` | `.tmpl` | FR-016 | none ingested | Estructura de escena para borrador |
| `manifest.template.toml` | `.toml` | FR-025 | n/a | **VERIFY ONLY** — already covers all manifest fields with English comments; do not re-author |

### 1c. Repo-root artifact

| File | FR | Content |
|---|---|---|
| `CHANGELOG.md` | FR-021 | Credit `fiction-book-writing` (adaumann, MIT) as structural inspiration; state Bookwright redaction is original (Apache-2.0), adapted to GOLEM; record that this iteration supersedes design § 6's unified-template layout in favor of the lifecycle split |

## 2. Frontmatter schema (conformance to the iter-6 mapper)

Only the four indexed concepts carry mapper-significant frontmatter. Type rules
are enforced by `_coerce_year` / `_coerce_str_list` / `_require_name` /
`_record_unknown_keys` (§ R3). Violating a typing rule = `invalid_frontmatter`
skip; an extra top-level key = `unknown_keys` warning. Both fail SC-002.

### Character (`bible/characters/*.md`, produced by stamping `character.md.tmpl`)

```yaml
---
name: <str, required, non-empty>          # → Character.name ; a [PENDING] prompt here MUST be quoted: name: "[PENDING: …]"
born: <int year | omit>                   # → Character.born ; NEVER a string/[PENDING]
died: <int year | omit>                   # → Character.died ; NEVER a string/[PENDING]
features: <list[str] | omit>              # → Character.features
narrative_roles: <list[str] | omit>       # → Character.narrative_roles
---
```
Maps to exactly one `Character` (SC-004). "Age" is `born`/`died` or prose only
(FR-012). The shipped **mold** leaves `born`/`died` omitted (or commented), never
a placeholder string.

### Setting (`bible/settings/*.md`, from `setting.md.tmpl`)

```yaml
---
name: <str, required, non-empty>          # → Setting.name ; ONLY ingested key
---
```
Any other key → `unknown_keys`. Maps to one `Setting` (SC-004).

### Timeline (`bible/timeline.md`)

```yaml
---
events: []        # the ONLY top-level key; empty in a fresh project (zero NarrativeEvents)
---
```
Per-event item shape (documented in body + HTML-comment example, never shipped
populated): `{name: <str>, participants: [<character-slug-str>, …]}`. Unresolved
participant slugs surface as `unresolved_participants` warnings — a fresh empty
list yields none (SC-002).

### Relationships (`bible/relationships.md`)

```yaml
---
relationships: []   # the ONLY top-level key; empty in a fresh project
---
```
Per-relationship item shape: `{name: <str>, participants: [<character-slug-str>, …]}`.

### Non-indexed documents

`location.md.tmpl`, `chapter.md.tmpl`, `scene.md.tmpl`, and all other skeleton
docs carry **no** mapper-ingested frontmatter (v0 has no `locations/` handler —
spec edge). If a mold includes frontmatter for human/agent use, it must be valid
YAML (parseable by `parse_frontmatter` without `yaml.YAMLError`) and the template
must not imply it is indexed.

## 3. State / lifecycle transitions

A template moves through these states; the tests assert the invariants:

1. **Authored** (this iteration) — real Spanish content, HTML-comment guidance,
   `[PENDING: …]` prompts; no stub sentinel (FR-022); valid YAML where present.
2. **Stamped** — skeleton via the iter-4 walker (`.j2` rendered with the 5-key
   context / `.md` byte-copied); molds via iter-8/9 commands into `bible/…`,
   `manuscript/…`. A fresh stamp leaves indexed collections empty.
3. **Filled** — author/agent answers `[PENDING]` prompts and adds frontmatter
   values; a filled character/setting now indexes to a GOLEM entity (SC-004).

The only invariant this iteration *owns* is **Authored → still-parseable-when-
Stamped**: every authored file must round-trip through the walker and the
frontmatter reader without error (SC-002/003).
