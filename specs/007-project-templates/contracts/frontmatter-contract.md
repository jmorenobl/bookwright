# Contract: Frontmatter ↔ iter-6 Mapper

**Direction**: templates → consumer. The templates are the *producers*; the
already-shipped iter-6 reader/mapper is the *consumer* whose behavior is frozen
(FR-023). This contract states what the templates MUST emit so the consumer stays
quiet. Authoritative source:
[`src/bookwright/io/bible.py`](../../../src/bookwright/io/bible.py) and
[`src/bookwright/io/frontmatter.py`](../../../src/bookwright/io/frontmatter.py).

## C1. Fence

- The file's **first line** is exactly `---` (no leading blank line, no heading
  before it) and a later line is exactly `---`. Otherwise the reader treats the
  whole file as body with empty metadata (`parse_frontmatter`), silently
  dropping any intended frontmatter.
- The block between fences MUST be `yaml.safe_load`-able. A `yaml.YAMLError` →
  the mapper records a `malformed YAML frontmatter` **skip** (`_safe_parse`).

## C2. Recognized keys (allowed sets)

| Concept | Location | Allowed top-level keys |
|---|---|---|
| Character | `bible/characters/*.md` | `name`, `born`, `died`, `features`, `narrative_roles` |
| Setting | `bible/settings/*.md` | `name` |
| Timeline | `bible/timeline.md` | `events` |
| Relationships | `bible/relationships.md` | `relationships` |

Any top-level key outside the set for that location → one `unknown_keys`
warning (`_record_unknown_keys`). **SC-002 requires zero**, so shipped files
carry only allowed keys. For `timeline.md`/`relationships.md` this means the
frontmatter is *exactly* `events: []` / `relationships: []` and nothing else.

## C3. Value typing (hard — violation = skip, not warning)

- `name`: non-empty `str`, required where the concept needs it (`_require_name`).
  A `[PENDING: …]` prompt is a legal *string* value **only when quoted** —
  `name: "[PENDING: …]"`. A bare `name: [PENDING: …]` is parsed by YAML as a
  *list* (`[{'PENDING': '…'}]`), not a string, and skips on `_require_name`.
- `born`, `died`: `int` or omitted/`null`. `bool` and any non-`int` raise
  `InvalidFrontmatterError` → file skipped (`_coerce_year`). **Never** a
  `[PENDING: …]` string or a textual age.
- `features`, `narrative_roles`: `list[str]` or omitted/`null`. A non-list or a
  list with a non-str item raises → skip (`_coerce_str_list`).
- `events` / `relationships`: a `list`; each item a mapping with `name` (str)
  and optional `participants` (`list[str]` of character slugs). A non-list
  container, or a non-mapping item, → skip; a non-list `participants` →
  `unresolved_participants` warning (the event/relationship still builds).

## C4. Empty-collection guarantee

`events: []` and `relationships: []` iterate zero times → zero entities, zero
`unknown_keys`, zero `unresolved_participants` on a freshly-`init`-ed project.
This is the SC-002 round-trip target.

## C5. Filled-instance guarantee

A `character.md.tmpl` stamped into `bible/characters/<slug>.md` and filled with
`name` (+ optional `born`/`died` ints, `features`/`narrative_roles` str lists)
maps to **exactly one** `Character` carrying those attributes; `setting.md.tmpl`
→ exactly one `Setting` (SC-004). The mold's own frontmatter ships with `born`/
`died` omitted (or in an HTML-comment example), never as a typed-field
placeholder string (C3).

## C6. Verification

`tests/resources/test_frontmatter_contract.py` (round-trip every shipped file via
`parse_frontmatter` and a full `map_bible` over a freshly-rendered temp project,
asserting `skipped == []`, `unknown_keys == []`, `unresolved_participants == []`)
and `test_filled_instance_maps.py` (C5). These import the real iter-6 modules —
no re-implementation.
