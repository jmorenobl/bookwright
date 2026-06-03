# Contract — `bible/research/` plain-text format

The author-facing contract for the research source-of-truth. `io/research.py`
parses exactly this; anything else is ignored (prose) or rejected (malformed
front-matter). Stable across iteration 012; iteration 14 adds the *templates* that
scaffold these files and the `[research]` manifest block — neither changes this
format.

## Directory

```
bible/
└── research/
    ├── _index.md       # optional — topic map + global open questions
    ├── sources.md      # optional — consolidated Source registry
    └── <topic>.md      # zero or more — findings + anchors for one topic
```

- A project with **no** `bible/research/` directory, or an empty one, is valid and
  produces zero research triples (FR-015).
- File type is determined by **name**: `_index.md` and `sources.md` are reserved;
  every other `*.md` is a topic file.

## Front-matter: `sources.md`

Top-level key `sources:` — a list of mappings. Each Source requires **all** of:

| Key | Type | Notes |
|---|---|---|
| `name` | string | unique within the project; slugged to the URI token |
| `reference` | string | bibliographic reference or URL |
| `author` | string | |
| `original_language` | string | ISO 639-1 code |
| `type` | enum | `primaria` \| `secundaria` \| `oficial` \| `académica` \| `periodística` \| `testimonial` |
| `reliability` | enum | `alta` \| `media` \| `baja` |
| `reliability_justification` | string | non-empty |
| `access_date` | date | `YYYY-MM-DD` |
| `original_quote` | string | quote in the source's original language |
| `translation` | string | **required iff** `original_language` ≠ book language; **forbidden/ignored** when equal |

An out-of-enum `type`/`reliability`, a missing required key, or a translation-rule
violation **aborts the build** with a value-naming error (FR-016) — research files
are validated strictly, not soft-skipped.

## Front-matter: `<topic>.md`

Two optional top-level lists.

### `findings:` — list of mappings

| Key | Type | Req. | Notes |
|---|---|---|---|
| `id` | string | ✓ | unique within the file; referenced by `anchors[].promotes` |
| `open` | bool | – | `true` ⇒ an unresolved question; `claim`/`sources`/`bears_on` all optional |
| `claim` | string | ✓ unless `open` | the real-world assertion |
| `asserted_by` | string | – | defaults to `author` |
| `bears_on` | string | – | a narrative entity name (character/setting/event), resolved against the bible |
| `sources` | list[string] | ✓ unless `open` | Source `name`s; ≥ 1 for a non-open finding |

### `anchors:` — list of mappings

| Key | Type | Req. | Notes |
|---|---|---|---|
| `promotes` | string | ✓ | an `id` of a finding declared in the same file |
| `constrains` | string | ✓ | a narrative entity name, or the literal `timeline` |
| `begin` | int (year) | – | time-span start |
| `end` | int (year) | – | time-span end |
| `date` | int (year) | – | single-year shorthand (`begin == end`); mutually exclusive with `begin`/`end` |

## Front-matter: `_index.md`

Optional `open_questions:` — a list of finding mappings (same shape as a
`findings:` item with `open: true`); each becomes an open `Finding`. The rest of
the file is a human-readable topic map (ignored by the parser).

## Resolution & error summary

- Names in `bears_on` / `constrains` resolve against the **bible** `entity_index`
  (`make_slug(name)` → URI for characters, settings and events — research D11).
  `timeline` resolves to the well-known untyped `{uri_base}timeline` IRI (research D10).
- `sources` / `promotes` resolve against the in-project source registry and the
  in-file finding ids, respectively.
- **Soft (build continues, exit unchanged)**: a `bears_on` / `constrains` target name
  absent from the bible `entity_index` (not `timeline`) — the link is skipped and
  reported as a build warning (D12); existence/kind checks are iter-15's.
- **Hard (build aborts, no graph written, exit 2)**: invalid vocabulary value;
  missing required Source facet; non-open finding without `claim`/`sources`;
  `promotes` → unknown finding id; translation-rule violation; malformed YAML.
