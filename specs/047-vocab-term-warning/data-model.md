# Phase 1 Data Model — Soft warning for unrecognized Propp/Greimas terms

The feature adds **one soft-warning record** and **one enumerator**, riding the
existing `MapResult` → `BuildReport` → render flow. No GOLEM entity, predicate, or
ontology term is added (FR-014, SC-003).

## 1. `UntypedVocabTerm` — the warning record

A frozen Pydantic model in `src/bookwright/io/report.py`, sibling of
`UnknownKey` / `UnresolvedReference` / `ResearchTargetWarning`.

| Field | Type | Meaning |
|---|---|---|
| `path` | `str` | project-relative source file of the offending card |
| `field` | `str` | the frontmatter field the term came from — `"functions"` (Propp) or `"narrative_roles"` (Greimas) |
| `term` | `str` | the offending term **as authored** (original spelling, not the slug) |
| `vocabulary` | `str` | the active vocabulary it failed to type against — `"propp"` or `"greimas"` |

```python
class UntypedVocabTerm(BaseModel):
    """An authored term that, under an active vocabulary, matched no term and so
    minted an untyped node (DEBT-016). Non-fatal: never changes the exit code.
    The valid-term enumeration is render-derived from `vocabulary`, NOT stored here
    (FR-002) — mirroring ResearchTargetWarning, which stores {path,field,name} and
    renders 'not in bible' as derived text."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    field: str
    term: str
    vocabulary: str
```

**Why no enumeration field**: FR-002 bars denormalizing the full valid-term set into
every record; it is derivable from `vocabulary` (D3).

## 2. `MapResult.untyped_vocab_terms` — the accumulator channel

In `src/bookwright/io/_bible_builders.py`, a new field on the `MapResult`
dataclass, exactly like its sibling soft channels:

```python
untyped_vocab_terms: list[UntypedVocabTerm] = field(default_factory=list)
```

Populated at the two typing sites; consumed (copied) by `_graph.py`. Empty whenever
no vocabulary is active or every term typed.

## 3. `BuildReport.untyped_vocab_terms` — the report/envelope channel

In `src/bookwright/io/report.py`, an additive field with a default so existing
output stays byte-stable on a vocabulary-free build:

```python
untyped_vocab_terms: tuple[UntypedVocabTerm, ...] = ()
```

- **`exit_code` unchanged** — only `skipped` drives it; this channel is *not*
  referenced there (FR-004, SC-004).
- **`to_json()` gains one key**: `"untyped_vocab_terms": [w.model_dump() for w in
  self.untyped_vocab_terms]` (the additive envelope contract — see
  `contracts/graph-build-envelope.md`).

## 4. `VocabularyIndex.terms` — the valid-term enumerator

In `src/bookwright/io/vocabularies.py`, a new immutable field on the frozen
`VocabularyIndex`, populated in `_index_turtle`:

| Field | Type | Meaning |
|---|---|---|
| `terms` | `tuple[str, ...]` | every `rdfs:label` of the vocabulary (ES + EN), **deduplicated and sorted** — the human-facing valid-term enumeration |

```python
@dataclass(frozen=True)
class VocabularyIndex:
    _by_slug: dict[str, URIRef]
    terms: tuple[str, ...]          # sorted, unique rdfs:label set (FR-016)
```

Built by collecting `str(label)` for every `(term, rdfs:label)` while indexing, then
`tuple(sorted(set(labels)))`. The sort makes the enumeration byte-stable regardless
of the label store's incidental order (FR-016, SC-008). `resolve()` is unchanged.

## 5. Record lifecycle (where each warning is created)

| Site | Condition | Record emitted |
|---|---|---|
| `outline.py:_mint_functions`, inside `if function is None:` | `ctx.propp is not None and type_uri is None` | `UntypedVocabTerm(path=relpath, field="functions", term=raw, vocabulary="propp")` |
| `_bible_builders.py:_build_character`, in the `if greimas is not None:` loop | `make_slug(label)` succeeds **and** `greimas.resolve(label) is None` | `UntypedVocabTerm(path=relpath, field="narrative_roles", term=label, vocabulary="greimas")` |

Both append to `result.untyped_vocab_terms`. The Propp site emits at first mint
(deduped across cards); the Greimas site emits per unrecognized role label of a
character (unsluggable labels skipped first).

## 6. Determinism contract (FR-016 / SC-008)

- **Entry order** = bible-character sorted-glob order, then outline-unit sorted-glob
  order; within a card, authored YAML list order. No new sort key.
- **Enumeration order** = `VocabularyIndex.terms`, pre-sorted at index build.
- Two identical builds ⇒ byte-identical `untyped_vocab_terms` and rendered
  enumeration.
