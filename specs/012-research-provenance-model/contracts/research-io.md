# Contract — `io/research.py` public surface

The reader that turns `bible/research/` into provenance entities, mirroring
`io/bible.py`. Consumed only by `commands/graph/build.py` in v0.

## Entry point

```python
def map_research(
    project_root: Path,
    research_dir: Path,          # bible_dir / "research"
    uri_base: str,
    book_language: str,          # manifest.book.language — drives the translation rule
    bible_index: Mapping[str, URIRef],  # slug → URI from the bible pass (bears_on / constrains)
    timeline_uri: URIRef,        # target for `constrains: timeline`
) -> ResearchResult: ...
```

- **Absent/empty `research_dir`** → `ResearchResult` with empty tuples and
  `files_processed == 0`; never raises (FR-015, SC-005).
- **Deterministic order**: files globbed in sorted order; `sources.md` parsed
  before topic files so source references resolve in one pass.

## Result type

```python
@dataclass(frozen=True)
class ResearchResult:
    sources: tuple[Source, ...]
    findings: tuple[Finding, ...]
    anchors: tuple[Anchor, ...]
    files_processed: int

    @property
    def entities(self) -> tuple[GolemEntity, ...]:
        return (*self.sources, *self.findings, *self.anchors)
```

## Errors

```python
class ResearchError(BookwrightError):       # io/errors.py
    """A research file is structurally invalid; the build aborts, no graph written."""
    # carries: relpath, offending value/key, human message; .to_json() envelope
```

Raised (hard, build-aborting — D7) for:

- an out-of-vocabulary `type` or `reliability` value (names the value);
- a missing required Source facet;
- a non-open finding lacking `claim` or `sources`;
- `anchors[].promotes` referencing an unknown finding `id`;
- a translation-rule violation (missing when languages differ; the reader drops a
  translation supplied when they match — not an error);
- malformed YAML front-matter in a research file.

Resolution misses that are **not** hard errors are still surfaced, consistent with
the spec's edge cases:

- `bears_on` / `constrains` naming an entity absent from `bible_index`: the link is
  emitted as declared against a composed URI (the entity may be defined elsewhere);
  *existence/kind verification is the iter-15 `factual_anchor` validator's job*, not
  this reader's (spec edge cases).

## Build integration

`build.py:_build()` calls `map_research(...)` after the bible pass, then:

```python
for entity in research.entities:
    for triple in entity.to_triples():
        engine.add_triple(*triple)
```

before `engine.save(...)`. Research entities are **not** run through
`build_provenance` (they are already E13 reifications). `ResearchError` is caught
in the command body and rendered via the existing error envelope with exit code 2;
the `BuildReport` gains optional `sources` / `findings` / `anchors` counts for the
human and `--json` summaries (existing fields unchanged).
