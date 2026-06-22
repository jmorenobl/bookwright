# Contract: the prose/structure seam (`io/prose.py`)

The public surface the three prose validators (and `ValidationContext`) depend on.
This is the only contract this iteration introduces — there is no CLI/JSON-envelope
change.

## Public surface

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ProseLine:
    number: int       # 1-based source line number
    raw: str          # original line, unmodified
    normalized: str   # leading block prefix(es) stripped (iteratively)

ProseView = tuple[ProseLine, ...]

def prose_view(text: str) -> ProseView: ...
def is_placeholder(body: str) -> bool: ...
```

## Recognizers (private, exact patterns — byte-for-byte parity, FR-004)

```python
_HEADING_MARKER = re.compile(r"^#{1,6}\s+")   # mirrors character_presence._HEADING_MARKER
_BULLET_MARKER  = re.compile(r"^\s*[-*+>]\s+") # mirrors focalization._BULLET
_PENDING_ONLY   = re.compile(r"(?i)^\s*\[pending\b[^\]]*\]\s*$")  # mirrors focalization._PENDING_ONLY
```

Asymmetry is **deliberate** (Clarifications 2026-06-22): heading strict at column 0,
bullet/blockquote tolerant of leading whitespace. Do not unify.

## C1 — `prose_view` splitting

- **C1.1**: `prose_view(text)` returns one `ProseLine` per `text.splitlines()`
  entry, in order, with `number` = its 1-based index.
- **C1.2**: `prose_view("")` → `()`. Whitespace-only or absent input → an empty or
  whitespace `ProseLine` sequence exactly as `splitlines()` yields (no special-case
  dropping of blank lines).
- **C1.3**: `ProseLine.raw` equals the corresponding `splitlines()` element exactly.
- **C1.4**: `ProseLine.number` never derives from a regex match offset (FR-010).

## C2 — `normalized` block-prefix stripping (FR-003, D2)

`normalize(line)` strips one leading block prefix per pass, repeating until none
matches. Each pass: if `_HEADING_MARKER` matches → `sub("", line, count=1)`; elif
`_BULLET_MARKER` matches → `sub("", line, count=1)`; else stop.

| Input | `normalized` | Why |
|-------|-------------|-----|
| `# Capítulo 1` | `Capítulo 1` | heading stripped (count=1) |
| `### Escena` | `Escena` | 3 `#` + space |
| `####### x` | `####### x` | 7 `#` not a heading (out of `{1,6}`) |
| `#Capítulo` | `#Capítulo` | no space after `#` — not a heading |
| `   # text` | `   # text` | heading strict at col 0; indented → unchanged |
| `- Pedro` | `Pedro` | bullet stripped |
| `   - text` | `text` | indented bullet stripped (bullet tolerates `\s*`) |
| `> cita` | `cita` | blockquote stripped |
| `> - text` | `text` | iterative: pass 1 `> `, pass 2 `- ` |
| `* Pedro` | `Pedro` | bullet (`*` + space) |
| `*Pedro*` | `*Pedro*` | emphasis run, no following space — never stripped |
| `**Voz narrativa**:` | `**Voz narrativa**:` | inline emphasis is not a block prefix |
| `` (empty) | `` | no prefix |

- **C2.1 — termination**: a pass that matches neither recognizer exits; every
  stripping pass removes ≥ 1 character, so the loop is finite.
- **C2.2 — emphasis never triggers a pass**: `**`/`*`/`_` are not block prefixes;
  `normalized` never strips them (that is `focalization`'s job, C4 / D4).
- **C2.3 — single-pass on live inputs**: every input the live fixtures exercise
  carries at most one leading block prefix, so the loop runs exactly one pass and
  reproduces the deleted strippers byte-for-byte (FR-004).

## C3 — `is_placeholder` (FR-005, D5)

| Input `body` | Result |
|-------------|--------|
| `[PENDING: …]` | `True` |
| `  [pending algo]  ` | `True` (case-insensitive, surrounding whitespace ok) |
| `[PENDING: x] tercera persona` | `False` (text after the token) |
| `tercera persona [PENDING: x]` | `False` (text before the token) |
| `tercera persona` | `False` |
| `` (empty) | `False` |

Operates on a declaration **body** string, not a line kind. The `^…$` anchor is
load-bearing (a body with real text before *or* after stays a real declaration).

## C4 — `focalization` declaration recognizer (widened, D4)

```python
_DECLARATION = re.compile(
    r"(?i)^\s*(?:\*\*|\*|_)*\s*(?:voz narrativa|narrative voice)"
    r"(?:\*\*|\*|_)*\s*:\s*(?P<body>.+)$"
)
```

Applied to a line's **normalized** form (block bullet already stripped by the seam).

| Normalized line | Matches? | `body` |
|-----------------|---------|--------|
| `Voz narrativa: tercera persona, limitada` | yes | `tercera persona, limitada` |
| `**Voz narrativa**: tercera persona` | yes | `tercera persona` |
| `_Narrative voice_: first person` | yes | `first person` |
| `Voz narrativa : x` (space before colon) | yes | `x` |
| `Algo: x` | no | — |

- **C4.1**: `(?P<body>.+)$` is unchanged from today, so the extracted body — and
  thus parsed person/limited/focal — is byte-identical (D4 parity).
- **C4.2**: `**` precedes `*` in the alternation so the longest emphasis run is
  consumed; the label contains no `*`/`_`, so `(?:…)*` cannot bleed into label/body.

## C5 — `ValidationContext` accessors (FR-006, D6)

- **C5.1**: `manuscript_view()` returns sorted `(relpath, ProseView)` parallel to
  `manuscript_files()`, built from it (no second disk read), memoized.
- **C5.2**: `constitution_view()` returns the constitution's `ProseView`, or `()`
  when `constitution_text()` is `None`. Memoized.
- **C5.3**: Both split each source exactly once per run, shared across validators.

## C6 — Invariants across all consumers

- **C6.1 — locators (FR-010, SC-004)**: every finding's line number is
  `ProseLine.number`; identical to today's `enumerate`-derived numbers.
- **C6.2 — dialogue parity (FR-008c)**: `focalization`'s dialogue / first-person /
  head-hopping scans read `ProseLine.raw`, so the dialogue-prefix exemption
  (`—`/`-`/`>`/quotes) is byte-for-byte unchanged.
- **C6.3 — no validator calls `splitlines()`** (SC-002): line splitting is
  single-sourced in `prose_view`.
- **C6.4 — generalization (FR-011, SC-003)**: a `> blockquote` off-roster mention
  is handled by the seam's existing `[-*+>]` recognizer with **no** validator-code
  change.
- **C6.5 — graph/ontology untouched (FR-013)**: validators stay graph-free,
  LLM-free, `triples=()`; severities and the `error`-only CI gate unchanged.
